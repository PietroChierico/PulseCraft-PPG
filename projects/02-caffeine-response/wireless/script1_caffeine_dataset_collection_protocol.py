# Copyright (c) 2026 Pietro Chierico
# SPDX-License-Identifier: MIT

"""
Script 1 - Caffeine Intake PPG Dataset Collection Protocol

Purpose
-------
Collect real PPG feature rows from a WiFi TCP IR PPG sensor for a caffeine-intake study.
The student selects:
    - Subject ID
    - Session type: Baseline, Coffee +5, +10, +15, +20, or +25 minutes

Protocol per measurement
------------------------
    15 s Stabilization     -> raw PPG is displayed but not saved
    60 s Measurement       -> saved as 10-second feature windows

Every 10-second window is converted into physiological and signal-quality features
and appended to one large CSV file.

Install
-------
pip install numpy scipy pandas pyqtgraph PyQt6

Run
---
python script1_caffeine_dataset_collection_protocol.py

WiFi TCP IR input
-----------------
The script expects real IR data from the ESP32 TCP stream. It supports lines such as:
    123456
    IR:123456
    ir=123456
    millis,red,ir
    12345,80123,90234
It extracts the IR value from each line.
"""
from __future__ import annotations

import csv
import sys
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
from scipy.signal import butter, filtfilt, find_peaks, welch

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import (
    QApplication, QComboBox, QFileDialog, QGridLayout, QHBoxLayout, QLabel,
    QLineEdit, QMainWindow, QMessageBox, QPushButton, QProgressBar,
    QSpinBox, QVBoxLayout, QWidget
)
import pyqtgraph as pg

from ppg_wifi_ir_stream import WiFiPPGClient, parse_ir_value


@dataclass
class PPGConfig:
    tcp_port: int = 3333
    sampling_rate_hz: int = 100
    tcp_connect_timeout_s: float = 5.0
    tcp_lines_per_tick: int = 30
    max_samples: int = 100 * 90
    window_seconds: int = 10
    stabilization_seconds: int = 15
    measurement_seconds: int = 60


CONFIG = PPGConfig()
BASE_DIR = Path(__file__).parent.resolve()
DEFAULT_CSV = BASE_DIR / "caffeine_ppg_big_dataset.csv"
DEFAULT_ESP32_HOST = "192.168.4.1"

SESSION_OPTIONS = [
    ("Baseline", 0),
    ("Coffee +5 min", 5),
    ("Coffee +10 min", 10),
    ("Coffee +15 min", 15),
    ("Coffee +20 min", 20),
    ("Coffee +25 min", 25),
]

CSV_COLUMNS = [
    "measurement_id", "timestamp_iso", "subject_id", "session_label",
    "minutes_after_coffee", "window_index", "window_start_s", "window_end_s",
    "sampling_rate_hz", "bpm", "dominant_bpm", "ibi_mean_s", "ibi_std_s",
    "rmssd_ms", "sdnn_ms", "ppg_amplitude", "signal_power", "noise_power",
    "snr_db", "perfusion_index_proxy", "motion_artifact_proxy", "num_peaks",
]

APPLE_STYLE = """
QMainWindow, QWidget {
    background-color: #0b0f17;
    color: #f5f7fb;
    font-family: -apple-system, BlinkMacSystemFont, Segoe UI;
}
QLabel { color: #f5f7fb; font-size: 14px; }
QLineEdit, QComboBox, QSpinBox {
    background-color: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.20);
    border-radius: 12px;
    padding: 8px;
    color: #f5f7fb;
    selection-background-color: #0071e3;
}
QPushButton {
    background-color: rgba(255,255,255,0.10);
    border: 1px solid rgba(255,255,255,0.18);
    border-radius: 14px;
    padding: 10px 16px;
    color: #f5f7fb;
    font-weight: 700;
}
QPushButton:hover { background-color: rgba(255,255,255,0.18); }
QPushButton:pressed { background-color: rgba(255,255,255,0.26); }
QPushButton#primaryButton {
    background-color: #0071e3;
    border: 1px solid #3f9bff;
}
QPushButton#dangerButton {
    background-color: rgba(255,69,58,0.25);
    border: 1px solid rgba(255,69,58,0.45);
}
QProgressBar {
    border: 1px solid rgba(255,255,255,0.20);
    border-radius: 10px;
    text-align: center;
    background-color: rgba(255,255,255,0.08);
    color: white;
    height: 22px;
}
QProgressBar::chunk { border-radius: 10px; background-color: #36d399; }
"""



def bandpass_filter(signal: np.ndarray, fs: int, low: float = 0.5, high: float = 5.0) -> np.ndarray:
    signal = np.asarray(signal, dtype=float)
    if len(signal) < fs * 3:
        return signal - np.mean(signal)
    nyq = 0.5 * fs
    b, a = butter(3, [low / nyq, high / nyq], btype="band")
    return filtfilt(b, a, signal)


def compute_ppg_features(ir_window: np.ndarray, fs: int) -> dict[str, float | int]:
    ir = np.asarray(ir_window, dtype=float)
    ir = ir[np.isfinite(ir)]
    if len(ir) < fs * 4:
        raise ValueError("Not enough valid PPG samples in the window.")

    filtered = bandpass_filter(ir, fs)
    peaks, _ = find_peaks(filtered, distance=int(0.35 * fs), prominence=max(np.std(filtered) * 0.35, 1e-9))

    duration_min = len(ir) / fs / 60.0
    bpm = len(peaks) / duration_min if duration_min > 0 else np.nan

    if len(peaks) >= 3:
        ibi = np.diff(peaks) / fs
        ibi_mean = float(np.mean(ibi))
        ibi_std = float(np.std(ibi))
        rmssd = float(np.sqrt(np.mean(np.diff(ibi) ** 2)) * 1000)
        sdnn = float(np.std(ibi) * 1000)
    else:
        ibi_mean = np.nan
        ibi_std = np.nan
        rmssd = np.nan
        sdnn = np.nan

    amplitude = float(np.percentile(filtered, 95) - np.percentile(filtered, 5))
    residual = ir - np.mean(ir) - filtered
    signal_power = float(np.var(filtered))
    noise_power = float(np.var(residual))
    snr = float(10 * np.log10(signal_power / noise_power)) if noise_power > 0 else np.nan

    freqs, psd = welch(filtered, fs=fs, nperseg=min(len(filtered), fs * 8))
    dominant_freq = float(freqs[int(np.argmax(psd))]) if len(freqs) else np.nan
    dominant_bpm = dominant_freq * 60 if np.isfinite(dominant_freq) else np.nan

    dc = float(np.mean(ir))
    perfusion_index_proxy = float((amplitude / abs(dc)) * 100) if dc != 0 else np.nan
    motion_artifact_proxy = float(noise_power / signal_power) if signal_power > 0 else np.nan

    return {
        "bpm": float(bpm),
        "dominant_bpm": float(dominant_bpm),
        "ibi_mean_s": ibi_mean,
        "ibi_std_s": ibi_std,
        "rmssd_ms": rmssd,
        "sdnn_ms": sdnn,
        "ppg_amplitude": amplitude,
        "signal_power": signal_power,
        "noise_power": noise_power,
        "snr_db": snr,
        "perfusion_index_proxy": perfusion_index_proxy,
        "motion_artifact_proxy": motion_artifact_proxy,
        "num_peaks": int(len(peaks)),
    }


class CaffeineCollectionWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Caffeine Intake PPG Dataset Collection")
        self.resize(1280, 860)

        self.wifi_client: Optional[WiFiPPGClient] = None
        self.streaming = False
        self.protocol_running = False
        self.measurement_id = 0
        self.sample_index = 0
        self.measurement_start_sample = 0
        self.last_feature_sample_index = 0
        self.phase = "Idle"
        self.phase_start_time = 0.0
        self.rows: list[dict[str, float | int | str]] = []
        self.ir_buffer = deque(maxlen=CONFIG.max_samples)

        self._build_ui()
        self._build_timer()

    def _card(self, label: QLabel) -> QLabel:
        label.setStyleSheet("background-color: rgba(255,255,255,0.07); border-radius: 18px; padding: 16px;")
        return label

    def _build_ui(self) -> None:
        pg.setConfigOptions(antialias=True, background="#0b0f17", foreground="#f5f7fb")
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setSpacing(16)

        title = QLabel("Caffeine Intake Project · Real WiFi IR PPG Acquisition")
        title.setStyleSheet("font-size: 32px; font-weight: 900; letter-spacing: -1px;")
        subtitle = QLabel("Select a subject and session, stream real RAW IR PPG over WiFi TCP, then save 10-second feature windows into one big CSV.")
        subtitle.setStyleSheet("font-size: 15px; color: #a9b4c7;")

        grid = QGridLayout()
        self.host_edit = QLineEdit(DEFAULT_ESP32_HOST)
        self.host_edit.setPlaceholderText("Example: 192.168.4.1")
        self.connect_button = QPushButton("Connect WiFi")
        self.disconnect_button = QPushButton("Disconnect")
        self.subject_edit = QLineEdit()
        self.subject_edit.setPlaceholderText("Example: S01")
        self.session_combo = QComboBox()
        for label, minutes in SESSION_OPTIONS:
            self.session_combo.addItem(label, minutes)
        self.tcp_port_spin = QSpinBox()
        self.tcp_port_spin.setRange(1, 65535)
        self.tcp_port_spin.setValue(CONFIG.tcp_port)
        self.tcp_port_spin.setSingleStep(1)
        self.fs_spin = QSpinBox()
        self.fs_spin.setRange(25, 500)
        self.fs_spin.setValue(CONFIG.sampling_rate_hz)

        grid.addWidget(QLabel("ESP32 IP / Host"), 0, 0)
        grid.addWidget(self.host_edit, 0, 1, 1, 2)
        grid.addWidget(QLabel("TCP Port"), 0, 3)
        grid.addWidget(self.tcp_port_spin, 0, 4)
        grid.addWidget(QLabel("Sampling Rate Hz"), 0, 5)
        grid.addWidget(self.fs_spin, 0, 6)
        grid.addWidget(QLabel("Subject ID"), 1, 0)
        grid.addWidget(self.subject_edit, 1, 1, 1, 2)
        grid.addWidget(QLabel("Session"), 1, 3)
        grid.addWidget(self.session_combo, 1, 4, 1, 3)

        buttons = QHBoxLayout()
        self.start_button = QPushButton("Start Selected Session")
        self.start_button.setObjectName("primaryButton")
        self.stop_button = QPushButton("Stop")
        self.stop_button.setObjectName("dangerButton")
        self.save_button = QPushButton("Save / Append Big CSV")
        self.clear_button = QPushButton("Clear Unsaved Rows")
        for button in [self.connect_button, self.disconnect_button, self.start_button, self.stop_button, self.save_button, self.clear_button]:
            buttons.addWidget(button)

        self.phase_label = self._card(QLabel("Phase: Idle"))
        self.time_label = self._card(QLabel("Time remaining: --"))
        self.rows_label = self._card(QLabel("Unsaved feature rows: 0"))
        self.status_label = self._card(QLabel("Status: Disconnected"))
        self.live_label = self._card(QLabel("Live BPM: -- · SNR: -- · Amplitude: --"))

        cards = QHBoxLayout()
        for item in [self.phase_label, self.time_label, self.rows_label, self.live_label, self.status_label]:
            cards.addWidget(item)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)

        self.plot = pg.PlotWidget(title="Real-Time RAW IR PPG Stream")
        self.plot.setLabel("left", "RAW IR value")
        self.plot.setLabel("bottom", "Time", units="s")
        self.plot.showGrid(x=True, y=True, alpha=0.25)
        self.curve = self.plot.plot([], [], pen=pg.mkPen("#7ab8ff", width=2), skipFiniteCheck=True)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addLayout(grid)
        layout.addLayout(buttons)
        layout.addLayout(cards)
        layout.addWidget(self.progress)
        layout.addWidget(self.plot)
        self.setCentralWidget(central)

        self.connect_button.clicked.connect(self.connect_wifi)
        self.disconnect_button.clicked.connect(self.disconnect_wifi)
        self.start_button.clicked.connect(self.start_session)
        self.stop_button.clicked.connect(self.stop_session)
        self.save_button.clicked.connect(self.save_csv)
        self.clear_button.clicked.connect(self.clear_rows)

    def _build_timer(self) -> None:
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_loop)
        self.timer.start(30)

    def connect_wifi(self) -> None:
        host = self.host_edit.text().strip()
        port = int(self.tcp_port_spin.value())
        try:
            self.wifi_client = WiFiPPGClient(host, port, connect_timeout_s=CONFIG.tcp_connect_timeout_s)
            self.streaming = True
            self.status_label.setText(f"Status: Connected to {host}:{port}")
        except Exception as exc:
            self.wifi_client = None
            self.streaming = False
            QMessageBox.critical(self, "Connection Error", str(exc))
            self.status_label.setText("Status: WiFi connection failed")

    def disconnect_wifi(self) -> None:
        self.streaming = False
        self.protocol_running = False
        if self.wifi_client is not None:
            try:
                self.wifi_client.close()
            except Exception:
                pass
        self.wifi_client = None
        self.phase_label.setText("Phase: Idle")
        self.status_label.setText("Status: Disconnected")

    def start_session(self) -> None:
        if self.wifi_client is None or not self.wifi_client.connected:
            QMessageBox.information(self, "WiFi Required", "Connect to the ESP32 WiFi TCP IR stream first.")
            return
        subject = self.subject_edit.text().strip()
        if not subject:
            QMessageBox.information(self, "Subject Required", "Enter a Subject ID first.")
            return
        self.measurement_id += 1
        self.phase = "Stabilization"
        self.phase_start_time = time.time()
        self.measurement_start_sample = self.sample_index
        self.last_feature_sample_index = self.sample_index
        self.protocol_running = True
        self.progress.setValue(0)
        self.status_label.setText("Status: Session running")

    def stop_session(self) -> None:
        self.protocol_running = False
        self.phase = "Idle"
        self.phase_label.setText("Phase: Idle")
        self.time_label.setText("Time remaining: --")
        self.progress.setValue(0)
        self.status_label.setText("Status: Session stopped")

    def read_wifi_data(self) -> None:
        if not self.streaming or self.wifi_client is None or not self.wifi_client.connected:
            return
        try:
            lines = self.wifi_client.read_lines(CONFIG.tcp_lines_per_tick)
        except Exception as exc:
            self.streaming = False
            self.protocol_running = False
            self.status_label.setText(f"Status: TCP read error: {exc}")
            return
        for line in lines:
            value = parse_ir_value(line)
            if value is not None:
                self.ir_buffer.append(value)
                self.sample_index += 1

    def update_loop(self) -> None:
        self.read_wifi_data()
        self.update_plot_and_live_features()
        if self.protocol_running:
            self.update_protocol()

    def update_plot_and_live_features(self) -> None:
        fs = int(self.fs_spin.value())
        if len(self.ir_buffer) < 2:
            return
        visible_samples = int(10 * fs)
        ir = np.array(self.ir_buffer, dtype=float)[-visible_samples:]
        x = np.arange(len(ir), dtype=float) / fs
        x = x - x[-1]
        self.curve.setData(x, ir)
        self.plot.setXRange(-10, 0, padding=0)

        if len(ir) >= fs * 10:
            try:
                features = compute_ppg_features(ir[-fs * 10:], fs)
                self.live_label.setText(
                    f"Live BPM: {features['bpm']:.1f} · SNR: {features['snr_db']:.1f} dB · Amplitude: {features['ppg_amplitude']:.1f}"
                )
            except Exception:
                pass

    def update_protocol(self) -> None:
        fs = int(self.fs_spin.value())
        elapsed = time.time() - self.phase_start_time

        if self.phase == "Stabilization":
            duration = CONFIG.stabilization_seconds
            remaining = max(0.0, duration - elapsed)
            self.phase_label.setText("Phase: Stabilization · Not saved")
            self.time_label.setText(f"Time remaining: {remaining:0.1f} s")
            self.progress.setValue(int(100 * min(elapsed / duration, 1.0)))
            if elapsed >= duration:
                self.phase = "Measurement"
                self.phase_start_time = time.time()
                self.measurement_start_sample = self.sample_index
                self.last_feature_sample_index = self.sample_index
                self.progress.setValue(0)
            return

        if self.phase == "Measurement":
            duration = CONFIG.measurement_seconds
            remaining = max(0.0, duration - elapsed)
            label = self.session_combo.currentText()
            self.phase_label.setText(f"Phase: Measurement · {label} · Saved")
            self.time_label.setText(f"Time remaining: {remaining:0.1f} s")
            self.progress.setValue(int(100 * min(elapsed / duration, 1.0)))
            self.maybe_append_feature_row(fs)
            if elapsed >= duration:
                self.protocol_running = False
                self.phase = "Complete"
                self.phase_label.setText("Phase: Complete")
                self.time_label.setText("Time remaining: 0.0 s")
                self.progress.setValue(100)
                self.status_label.setText("Status: Measurement complete. Save CSV or start another session.")

    def maybe_append_feature_row(self, fs: int) -> None:
        window_samples = int(CONFIG.window_seconds * fs)
        if len(self.ir_buffer) < window_samples:
            return
        if self.sample_index - self.last_feature_sample_index < window_samples:
            return

        ir_window = np.array(self.ir_buffer, dtype=float)[-window_samples:]
        try:
            features = compute_ppg_features(ir_window, fs)
        except Exception as exc:
            self.status_label.setText(f"Status: Feature error: {exc}")
            self.last_feature_sample_index = self.sample_index
            return

        session_label = self.session_combo.currentText()
        minutes = int(self.session_combo.currentData())
        subject = self.subject_edit.text().strip()
        window_index = 1 + sum(1 for row in self.rows if row["measurement_id"] == self.measurement_id)
        window_end_s = window_index * CONFIG.window_seconds
        window_start_s = window_end_s - CONFIG.window_seconds

        row = {
            "measurement_id": self.measurement_id,
            "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "subject_id": subject,
            "session_label": session_label,
            "minutes_after_coffee": minutes,
            "window_index": window_index,
            "window_start_s": window_start_s,
            "window_end_s": window_end_s,
            "sampling_rate_hz": fs,
            **features,
        }
        self.rows.append(row)
        self.last_feature_sample_index = self.sample_index
        self.rows_label.setText(f"Unsaved feature rows: {len(self.rows)}")

    def save_csv(self) -> None:
        if not self.rows:
            QMessageBox.information(self, "No Data", "No feature rows have been collected yet.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save or Append Big CSV", str(DEFAULT_CSV), "CSV files (*.csv)")
        if not path:
            return
        path_obj = Path(path)
        file_exists = path_obj.exists()
        try:
            with open(path_obj, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
                if not file_exists:
                    writer.writeheader()
                writer.writerows(self.rows)
            self.status_label.setText(f"Status: Appended {len(self.rows)} rows to {path_obj.name}")
            self.rows.clear()
            self.rows_label.setText("Unsaved feature rows: 0")
        except Exception as exc:
            QMessageBox.critical(self, "Save Error", str(exc))

    def clear_rows(self) -> None:
        self.rows.clear()
        self.rows_label.setText("Unsaved feature rows: 0")
        self.status_label.setText("Status: Unsaved rows cleared")

    def closeEvent(self, event) -> None:
        self.disconnect_wifi()
        event.accept()


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyleSheet(APPLE_STYLE)
    win = CaffeineCollectionWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
