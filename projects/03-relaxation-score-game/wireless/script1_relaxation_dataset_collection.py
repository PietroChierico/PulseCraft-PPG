# Copyright (c) 2026 Pietro Chierico
# SPDX-License-Identifier: MIT

"""
Script 1 - PPG Relaxation Dataset Collection Protocol

Purpose
-------
Collect labeled PPG feature rows using this fixed relaxation protocol:
    20 s Stabilizing Baseline      -> not saved
    60 s Pre-Relaxation Recording  -> saved as target Pre-Relaxation
    60 s Deep Breathing Technique  -> not saved
    60 s Post-Relaxation Recording -> saved as target Post-Relaxation

Every 10-second IR window is converted into PPG features and appended to memory.
Students can repeat the protocol as Record 1, Record 2, ... as many times as needed.
Use the Export Data button to save the collected rows as CSV.

Input
-----
The ESP32 sends IR PPG data over WiFi TCP.
Default AP mode endpoint: 192.168.4.1 port 3333.
The parser accepts one IR value per line, millis,ir, or millis,red,ir.

Install
-------
pip install numpy scipy pyqtgraph PyQt6

Run
---
python script1_relaxation_dataset_collection.py
"""
from __future__ import annotations

import csv
import math
import sys
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np

try:
    from scipy.signal import find_peaks, welch
except Exception:
    find_peaks = None
    welch = None

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import (
    QApplication, QFileDialog, QGridLayout, QHBoxLayout, QLabel, QLineEdit,
    QMainWindow, QMessageBox, QPushButton, QProgressBar, QSpinBox, QVBoxLayout, QWidget
)
import pyqtgraph as pg

from ppg_wifi_ir_stream import WiFiPPGClient, parse_ir_value


@dataclass(frozen=True)
class PPGConfig:
    tcp_host: str = "192.168.4.1"
    tcp_port: int = 3333
    tcp_connect_timeout_s: float = 5.0
    sampling_rate_hz: float = 100.0
    tcp_lines_per_tick: int = 60
    max_samples: int = 100 * 180
    window_seconds: int = 10


CONFIG = PPGConfig()

FEATURE_COLUMNS = [
    "mean_ir", "std_ir", "range_ir", "rms_ir", "mad_ir",
    "diff_std", "diff_rms", "signal_energy", "dominant_frequency_hz",
    "spectral_entropy", "peak_count", "mean_peak_distance_s", "pulse_amplitude_mean",
]

LEGACY_FEATURE_ALIASES = {
    "mean_red": "mean_ir",
    "std_red": "std_ir",
    "range_red": "range_ir",
    "rms_red": "rms_ir",
    "mad_red": "mad_ir",
}

CSV_COLUMNS = [
    "recording_id", "timestamp_s", "sample_index", "protocol_phase", "target", "window_seconds",
    *FEATURE_COLUMNS,
]

PROTOCOL = [
    ("Stabilizing Baseline", 20, None),
    ("Pre-Relaxation Recording", 60, "Pre-Relaxation"),
    ("Deep Breathing Technique", 60, None),
    ("Post-Relaxation Recording", 60, "Post-Relaxation"),
]

APPLE_STYLE = """
QMainWindow, QWidget { background-color: #070b13; color: #f5f7fb; font-family: -apple-system, BlinkMacSystemFont, Segoe UI; }
QLabel { color: #f5f7fb; font-size: 14px; }
QPushButton { background-color: rgba(255,255,255,0.10); border: 1px solid rgba(255,255,255,0.18); border-radius: 15px; padding: 11px 16px; color: #f5f7fb; font-weight: 700; }
QPushButton:hover { background-color: rgba(255,255,255,0.18); }
QPushButton:pressed { background-color: rgba(255,255,255,0.26); }
QLineEdit, QSpinBox { background-color: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.20); border-radius: 13px; padding: 8px; color: #f5f7fb; }
QProgressBar { border: 1px solid rgba(255,255,255,0.20); border-radius: 11px; text-align: center; background-color: rgba(255,255,255,0.08); color: white; }
QProgressBar::chunk { border-radius: 11px; background-color: #35d7ff; }
"""


def _spectral_entropy(values: np.ndarray) -> float:
    power = np.asarray(values, dtype=float)
    total = float(np.sum(power))
    if total <= 0:
        return 0.0
    p = power / total
    p = p[p > 0]
    if len(p) == 0:
        return 0.0
    return float(-np.sum(p * np.log2(p)) / np.log2(len(p)))


def compute_ppg_features(ir_window: np.ndarray, fs: float) -> dict[str, float]:
    ir = np.asarray(ir_window, dtype=float)
    ir = ir[np.isfinite(ir)]
    if len(ir) < 5:
        features = {name: 0.0 for name in FEATURE_COLUMNS}
        features.update({legacy: features[current] for legacy, current in LEGACY_FEATURE_ALIASES.items()})
        return features

    centered = ir - np.mean(ir)
    diff = np.diff(ir)

    if welch is not None and len(ir) >= int(fs * 4):
        freqs, power = welch(centered, fs=fs, nperseg=min(len(ir), int(fs * 8)))
        band = (freqs >= 0.05) & (freqs <= 5.0)
        freqs_band = freqs[band]
        power_band = power[band]
        dominant_frequency = float(freqs_band[int(np.argmax(power_band))]) if len(power_band) else 0.0
        entropy = _spectral_entropy(power_band) if len(power_band) else 0.0
    else:
        fft = np.abs(np.fft.rfft(centered)) ** 2
        freqs = np.fft.rfftfreq(len(centered), d=1.0 / fs)
        band = (freqs >= 0.05) & (freqs <= 5.0)
        dominant_frequency = float(freqs[band][int(np.argmax(fft[band]))]) if np.any(band) else 0.0
        entropy = _spectral_entropy(fft[band]) if np.any(band) else 0.0

    if find_peaks is not None:
        min_distance = max(1, int(0.35 * fs))
        prominence = max(1e-9, float(np.std(ir) * 0.25))
        peaks, _ = find_peaks(ir, distance=min_distance, prominence=prominence)
    else:
        peaks = np.array([], dtype=int)

    peak_count = int(len(peaks))
    if peak_count >= 2:
        mean_peak_distance = float(np.mean(np.diff(peaks)) / fs)
    else:
        mean_peak_distance = 0.0

    if peak_count >= 1:
        pulse_amplitude = float(np.mean(ir[peaks] - np.percentile(ir, 10)))
    else:
        pulse_amplitude = 0.0

    features = {
        "mean_ir": float(np.mean(ir)),
        "std_ir": float(np.std(ir)),
        "range_ir": float(np.max(ir) - np.min(ir)),
        "rms_ir": float(math.sqrt(np.mean(ir ** 2))),
        "mad_ir": float(np.mean(np.abs(ir - np.mean(ir)))),
        "diff_std": float(np.std(diff)) if len(diff) else 0.0,
        "diff_rms": float(math.sqrt(np.mean(diff ** 2))) if len(diff) else 0.0,
        "signal_energy": float(np.mean(centered ** 2)),
        "dominant_frequency_hz": dominant_frequency,
        "spectral_entropy": entropy,
        "peak_count": float(peak_count),
        "mean_peak_distance_s": mean_peak_distance,
        "pulse_amplitude_mean": pulse_amplitude,
    }
    features.update({legacy: features[current] for legacy, current in LEGACY_FEATURE_ALIASES.items()})
    return features


class RelaxationDatasetCollectionWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Demo 3 - PPG Relaxation Dataset Collection")
        self.resize(1250, 840)

        self.tcp_client: Optional[WiFiPPGClient] = None
        self.streaming = False
        self.protocol_running = False
        self.recording_id = 0
        self.phase_index = 0
        self.phase_start_time = 0.0
        self.sample_index = 0
        self.last_feature_sample_index = 0
        self.rows: list[dict[str, float | int | str]] = []
        self.ir_buffer = deque(maxlen=CONFIG.max_samples)

        self._build_ui()
        self._build_timer()

    def _build_ui(self) -> None:
        pg.setConfigOptions(antialias=True, background="#070b13", foreground="#f5f7fb")
        central = QWidget()
        layout = QVBoxLayout(central)
        top = QGridLayout()

        self.host_edit = QLineEdit(CONFIG.tcp_host)
        self.default_ip_button = QPushButton("Use AP IP")
        self.connect_button = QPushButton("Connect")
        self.disconnect_button = QPushButton("Disconnect")
        self.start_protocol_button = QPushButton("Start New Relaxation Recording")
        self.stop_protocol_button = QPushButton("Stop Protocol")
        self.export_button = QPushButton("Export Data")
        self.clear_button = QPushButton("Clear Rows")

        self.tcp_port_spin = QSpinBox()
        self.tcp_port_spin.setRange(1, 65535)
        self.tcp_port_spin.setValue(CONFIG.tcp_port)
        self.tcp_port_spin.setSingleStep(1)

        top.addWidget(QLabel("ESP32 IP / Host"), 0, 0)
        top.addWidget(self.host_edit, 0, 1)
        top.addWidget(self.default_ip_button, 0, 2)
        top.addWidget(QLabel("TCP Port"), 1, 0)
        top.addWidget(self.tcp_port_spin, 1, 1)

        buttons = QHBoxLayout()
        for button in [self.connect_button, self.disconnect_button, self.start_protocol_button, self.stop_protocol_button, self.export_button, self.clear_button]:
            buttons.addWidget(button)

        self.title_label = QLabel("Record 0 - Waiting for Relaxation Protocol")
        self.title_label.setStyleSheet("font-size: 31px; font-weight: 900;")
        self.subtitle_label = QLabel("Protocol: baseline stabilization -> pre-relaxation -> deep breathing -> post-relaxation")
        self.subtitle_label.setStyleSheet("font-size: 16px; color: #b7c2d8;")
        self.phase_label = QLabel("Phase: --")
        self.phase_label.setStyleSheet("font-size: 24px; font-weight: 800;")
        self.time_label = QLabel("Time remaining: --")
        self.rows_label = QLabel("Feature rows: 0")
        self.status_label = QLabel("Status: Disconnected")
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)

        cards = QHBoxLayout()
        for label in [self.phase_label, self.time_label, self.rows_label, self.status_label]:
            label.setStyleSheet(label.styleSheet() + " background-color: rgba(255,255,255,0.075); border-radius: 19px; padding: 16px;")
            cards.addWidget(label)

        self.plot = pg.PlotWidget(title="Raw IR PPG Streaming")
        self.plot.setLabel("left", "IR value")
        self.plot.setLabel("bottom", "Time", units="s")
        self.plot.showGrid(x=True, y=True, alpha=0.25)
        self.curve = self.plot.plot([], [], pen=pg.mkPen("#35d7ff", width=2), skipFiniteCheck=True)

        layout.addWidget(self.title_label)
        layout.addWidget(self.subtitle_label)
        layout.addLayout(top)
        layout.addLayout(buttons)
        layout.addLayout(cards)
        layout.addWidget(self.progress)
        layout.addWidget(self.plot)
        self.setCentralWidget(central)

        self.default_ip_button.clicked.connect(self.use_access_point_ip)
        self.connect_button.clicked.connect(self.connect_wifi)
        self.disconnect_button.clicked.connect(self.disconnect_wifi)
        self.start_protocol_button.clicked.connect(self.start_protocol)
        self.stop_protocol_button.clicked.connect(self.stop_protocol)
        self.export_button.clicked.connect(self.export_data)
        self.clear_button.clicked.connect(self.clear_rows)

    def _build_timer(self) -> None:
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_loop)
        self.timer.start(30)

    def use_access_point_ip(self) -> None:
        self.host_edit.setText(CONFIG.tcp_host)
        self.tcp_port_spin.setValue(CONFIG.tcp_port)

    def connect_wifi(self) -> None:
        self.disconnect_wifi(update_status=False)
        host = self.host_edit.text().strip()
        port = int(self.tcp_port_spin.value())
        try:
            self.tcp_client = WiFiPPGClient(
                host=host,
                port=port,
                connect_timeout_s=CONFIG.tcp_connect_timeout_s,
            )
            self.streaming = True
            self.status_label.setText(f"Status: Connected to {host}:{port}")
        except Exception as exc:
            self.tcp_client = None
            self.streaming = False
            self.status_label.setText(f"Status: Connection failed: {exc}")

    def disconnect_wifi(self, update_status: bool = True) -> None:
        self.streaming = False
        self.protocol_running = False
        if self.tcp_client is not None:
            try:
                self.tcp_client.close()
            except Exception:
                pass
        self.tcp_client = None
        if update_status:
            self.status_label.setText("Status: Disconnected")

    def start_protocol(self) -> None:
        if self.tcp_client is None or not self.tcp_client.connected:
            self.status_label.setText("Status: Connect WiFi before starting")
            return
        self.recording_id += 1
        self.phase_index = 0
        self.phase_start_time = time.time()
        self.last_feature_sample_index = self.sample_index
        self.protocol_running = True
        self.title_label.setText(f"Record {self.recording_id} - Relaxation Protocol Running")
        self.status_label.setText("Status: Protocol running")

    def stop_protocol(self) -> None:
        self.protocol_running = False
        self.title_label.setText(f"Record {self.recording_id} - Stopped")
        self.phase_label.setText("Phase: --")
        self.time_label.setText("Time remaining: --")
        self.progress.setValue(0)

    def read_wifi_data(self) -> None:
        if not self.streaming or self.tcp_client is None or not self.tcp_client.connected:
            return
        try:
            lines = self.tcp_client.read_lines(CONFIG.tcp_lines_per_tick)
        except Exception as exc:
            self.streaming = False
            self.protocol_running = False
            self.status_label.setText(f"Status: WiFi TCP read error: {exc}")
            return
        for line in lines:
            value = parse_ir_value(line)
            if value is not None:
                self.ir_buffer.append(value)
                self.sample_index += 1

    def update_loop(self) -> None:
        self.read_wifi_data()
        self.update_plot()
        if self.protocol_running:
            self.update_protocol()

    def update_plot(self) -> None:
        if len(self.ir_buffer) < 2:
            return
        visible_samples = int(10 * CONFIG.sampling_rate_hz)
        ir = np.array(self.ir_buffer, dtype=float)[-visible_samples:]
        x = np.arange(len(ir), dtype=float) / CONFIG.sampling_rate_hz
        x = x - x[-1]
        self.curve.setData(x, ir)
        self.plot.setXRange(-10, 0, padding=0)

    def update_protocol(self) -> None:
        phase_name, phase_duration_s, target = PROTOCOL[self.phase_index]
        elapsed = time.time() - self.phase_start_time
        remaining = max(0.0, phase_duration_s - elapsed)
        save_text = f" - Target {target}" if target else " - Not saved"
        self.phase_label.setText(f"Phase: {phase_name}{save_text}")
        self.time_label.setText(f"Time remaining: {remaining:0.1f} s")
        self.progress.setValue(int(100 * min(elapsed / phase_duration_s, 1.0)))

        if target is not None:
            self.maybe_append_feature_row(phase_name, target)

        if elapsed >= phase_duration_s:
            self.phase_index += 1
            if self.phase_index >= len(PROTOCOL):
                self.protocol_running = False
                self.title_label.setText(f"Record {self.recording_id} - Complete")
                self.phase_label.setText("Phase: Complete")
                self.time_label.setText("Time remaining: 0.0 s")
                self.progress.setValue(100)
                self.status_label.setText("Status: Recording complete. Start another recording or export data.")
            else:
                self.phase_start_time = time.time()
                self.last_feature_sample_index = self.sample_index

    def maybe_append_feature_row(self, phase_name: str, target: str) -> None:
        window_samples = int(CONFIG.window_seconds * CONFIG.sampling_rate_hz)
        if len(self.ir_buffer) < window_samples:
            return
        if self.sample_index - self.last_feature_sample_index < window_samples:
            return
        ir_window = np.array(self.ir_buffer, dtype=float)[-window_samples:]
        features = compute_ppg_features(ir_window, CONFIG.sampling_rate_hz)
        row = {
            "recording_id": self.recording_id,
            "timestamp_s": time.time(),
            "sample_index": self.sample_index,
            "protocol_phase": phase_name,
            "target": target,
            "window_seconds": CONFIG.window_seconds,
        }
        row.update({name: features.get(name, 0.0) for name in FEATURE_COLUMNS})
        self.rows.append(row)
        self.last_feature_sample_index = self.sample_index
        self.rows_label.setText(f"Feature rows: {len(self.rows)}")

    def export_data(self) -> None:
        if not self.rows:
            QMessageBox.information(self, "No data", "No feature rows have been collected yet.")
            return
        default_name = f"ppg_relaxation_ir_dataset_{int(time.time())}.csv"
        path, _ = QFileDialog.getSaveFileName(self, "Export Relaxation Dataset CSV", str(Path.home() / default_name), "CSV files (*.csv)")
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
                writer.writeheader()
                writer.writerows(self.rows)
            self.status_label.setText(f"Status: Exported data to {path}")
        except Exception as exc:
            QMessageBox.critical(self, "Export error", f"Could not export CSV:\n{exc}")

    def clear_rows(self) -> None:
        self.rows.clear()
        self.rows_label.setText("Feature rows: 0")
        self.status_label.setText("Status: Rows cleared")

    def closeEvent(self, event) -> None:
        self.disconnect_wifi()
        event.accept()


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyleSheet(APPLE_STYLE)
    win = RelaxationDatasetCollectionWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
