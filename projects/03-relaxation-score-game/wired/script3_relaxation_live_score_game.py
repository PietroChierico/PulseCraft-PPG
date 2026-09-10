# Copyright (c) 2026 Pietro Chierico
# SPDX-License-Identifier: MIT

"""
Script 3 - PPG Live Relaxation Score Game

Purpose
-------
Load the trained model exported by Script 2, stream live PPG data, compute the
same 10-second features, and display a relaxation score from 0 to 100.

Install
-------
pip install pyserial numpy scipy pyqtgraph PyQt6 joblib scikit-learn

Run
---
python script3_relaxation_live_score_game.py
"""
from __future__ import annotations

import math
import re
import sys
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import joblib
import numpy as np

try:
    import serial
    from serial.tools import list_ports
except Exception:
    serial = None
    list_ports = None

try:
    from scipy.signal import find_peaks, welch
except Exception:
    find_peaks = None
    welch = None

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import (
    QApplication, QComboBox, QFileDialog, QGridLayout, QHBoxLayout, QLabel,
    QMainWindow, QPushButton, QProgressBar, QSpinBox, QVBoxLayout, QWidget
)
import pyqtgraph as pg


@dataclass(frozen=True)
class PPGConfig:
    baudrate: int = 115200
    sampling_rate_hz: float = 50.0
    serial_timeout_s: float = 0.02
    serial_lines_per_tick: int = 8
    max_samples: int = 50 * 180
    window_seconds: int = 10


CONFIG = PPGConfig()

FEATURE_COLUMNS = [
    "mean_red", "std_red", "range_red", "rms_red", "mad_red",
    "diff_std", "diff_rms", "signal_energy", "dominant_frequency_hz",
    "spectral_entropy", "peak_count", "mean_peak_distance_s", "pulse_amplitude_mean",
]

APPLE_STYLE = """
QMainWindow, QWidget { background-color: #070b13; color: #f5f7fb; font-family: -apple-system, BlinkMacSystemFont, Segoe UI; }
QLabel { color: #f5f7fb; font-size: 14px; }
QPushButton { background-color: rgba(255,255,255,0.10); border: 1px solid rgba(255,255,255,0.18); border-radius: 15px; padding: 11px 16px; color: #f5f7fb; font-weight: 700; }
QPushButton:hover { background-color: rgba(255,255,255,0.18); }
QPushButton:pressed { background-color: rgba(255,255,255,0.26); }
QComboBox, QSpinBox { background-color: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.20); border-radius: 13px; padding: 8px; color: #f5f7fb; }
QProgressBar { border: 1px solid rgba(255,255,255,0.20); border-radius: 11px; text-align: center; background-color: rgba(255,255,255,0.08); color: white; font-weight: 800; }
QProgressBar::chunk { border-radius: 11px; background-color: #36d399; }
"""


def list_serial_ports() -> list[str]:
    if list_ports is None:
        return []
    return [port.device for port in list_ports.comports()]


def parse_red_value(line: str) -> Optional[float]:
    text = line.strip()
    if not text:
        return None
    numbers = re.findall(r"[-+]?\d*\.\d+|[-+]?\d+", text)
    if not numbers:
        return None
    try:
        return float(numbers[-1])
    except ValueError:
        return None


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


def compute_ppg_features(red_window: np.ndarray, fs: float) -> dict[str, float]:
    red = np.asarray(red_window, dtype=float)
    red = red[np.isfinite(red)]
    if len(red) < 5:
        return {name: 0.0 for name in FEATURE_COLUMNS}
    centered = red - np.mean(red)
    diff = np.diff(red)

    if welch is not None and len(red) >= int(fs * 4):
        freqs, power = welch(centered, fs=fs, nperseg=min(len(red), int(fs * 8)))
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
        prominence = max(1e-9, float(np.std(red) * 0.25))
        peaks, _ = find_peaks(red, distance=min_distance, prominence=prominence)
    else:
        peaks = np.array([], dtype=int)

    peak_count = int(len(peaks))
    mean_peak_distance = float(np.mean(np.diff(peaks)) / fs) if peak_count >= 2 else 0.0
    pulse_amplitude = float(np.mean(red[peaks] - np.percentile(red, 10))) if peak_count >= 1 else 0.0

    return {
        "mean_red": float(np.mean(red)),
        "std_red": float(np.std(red)),
        "range_red": float(np.max(red) - np.min(red)),
        "rms_red": float(math.sqrt(np.mean(red ** 2))),
        "mad_red": float(np.mean(np.abs(red - np.mean(red)))),
        "diff_std": float(np.std(diff)) if len(diff) else 0.0,
        "diff_rms": float(math.sqrt(np.mean(diff ** 2))) if len(diff) else 0.0,
        "signal_energy": float(np.mean(centered ** 2)),
        "dominant_frequency_hz": dominant_frequency,
        "spectral_entropy": entropy,
        "peak_count": float(peak_count),
        "mean_peak_distance_s": mean_peak_distance,
        "pulse_amplitude_mean": pulse_amplitude,
    }


class RelaxationGameWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Demo 3 - Live PPG Relaxation Score Game")
        self.resize(1250, 860)

        self.serial_connection: Optional[serial.Serial] = None if serial is not None else None
        self.streaming = False
        self.model_bundle: dict | None = None
        self.sample_index = 0
        self.last_prediction_sample_index = 0
        self.red_buffer = deque(maxlen=CONFIG.max_samples)
        self.score_history = deque(maxlen=120)

        self._build_ui()
        self._build_timer()

    def _build_ui(self) -> None:
        pg.setConfigOptions(antialias=True, background="#070b13", foreground="#f5f7fb")
        central = QWidget()
        layout = QVBoxLayout(central)
        top = QGridLayout()

        self.port_combo = QComboBox()
        self.refresh_button = QPushButton("Refresh Ports")
        self.connect_button = QPushButton("Connect")
        self.disconnect_button = QPushButton("Disconnect")
        self.load_model_button = QPushButton("Load Model")
        self.reset_game_button = QPushButton("Reset Game")

        self.baudrate_spin = QSpinBox()
        self.baudrate_spin.setRange(9600, 921600)
        self.baudrate_spin.setValue(CONFIG.baudrate)
        self.baudrate_spin.setSingleStep(9600)

        top.addWidget(QLabel("Serial Port"), 0, 0)
        top.addWidget(self.port_combo, 0, 1)
        top.addWidget(self.refresh_button, 0, 2)
        top.addWidget(QLabel("Baudrate"), 1, 0)
        top.addWidget(self.baudrate_spin, 1, 1)

        buttons = QHBoxLayout()
        for button in [self.connect_button, self.disconnect_button, self.load_model_button, self.reset_game_button]:
            buttons.addWidget(button)

        self.title_label = QLabel("Live Relaxation Score Game")
        self.title_label.setStyleSheet("font-size: 32px; font-weight: 900;")
        self.score_label = QLabel("Relaxation Score: -- / 100")
        self.score_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.score_label.setStyleSheet("font-size: 42px; font-weight: 950; background-color: rgba(54,211,153,0.12); border-radius: 26px; padding: 24px;")
        self.state_label = QLabel("State: load model and connect sensor")
        self.state_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.state_label.setStyleSheet("font-size: 22px; font-weight: 800; background-color: rgba(255,255,255,0.075); border-radius: 22px; padding: 18px;")
        self.status_label = QLabel("Status: Waiting")
        self.model_label = QLabel("Model: not loaded")
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)

        cards = QHBoxLayout()
        for label in [self.status_label, self.model_label]:
            label.setStyleSheet("background-color: rgba(255,255,255,0.075); border-radius: 19px; padding: 16px;")
            cards.addWidget(label)

        self.raw_plot = pg.PlotWidget(title="Raw RED PPG Streaming")
        self.raw_plot.setLabel("left", "RED value")
        self.raw_plot.setLabel("bottom", "Time", units="s")
        self.raw_plot.showGrid(x=True, y=True, alpha=0.25)
        self.raw_curve = self.raw_plot.plot([], [], pen=pg.mkPen("#35d7ff", width=2), skipFiniteCheck=True)

        self.score_plot = pg.PlotWidget(title="Relaxation Score History")
        self.score_plot.setLabel("left", "Score")
        self.score_plot.setLabel("bottom", "Prediction window")
        self.score_plot.setYRange(0, 100)
        self.score_plot.showGrid(x=True, y=True, alpha=0.25)
        self.score_curve = self.score_plot.plot([], [], pen=pg.mkPen("#36d399", width=3), skipFiniteCheck=True)

        layout.addWidget(self.title_label)
        layout.addLayout(top)
        layout.addLayout(buttons)
        layout.addWidget(self.score_label)
        layout.addWidget(self.state_label)
        layout.addWidget(self.progress)
        layout.addLayout(cards)
        layout.addWidget(self.raw_plot)
        layout.addWidget(self.score_plot)
        self.setCentralWidget(central)

        self.refresh_ports()
        self.refresh_button.clicked.connect(self.refresh_ports)
        self.connect_button.clicked.connect(self.connect_serial)
        self.disconnect_button.clicked.connect(self.disconnect_serial)
        self.load_model_button.clicked.connect(self.load_model)
        self.reset_game_button.clicked.connect(self.reset_game)

    def _build_timer(self) -> None:
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_loop)
        self.timer.start(30)

    def refresh_ports(self) -> None:
        self.port_combo.clear()
        ports = list_serial_ports()
        self.port_combo.addItems(ports if ports else ["No ports found"])

    def load_model(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Load Relaxation Model", str(Path.home()), "Joblib files (*.joblib)")
        if not path:
            return
        try:
            bundle = joblib.load(path)
            if "pipeline" not in bundle or "features" not in bundle:
                raise ValueError("Invalid model file")
            self.model_bundle = bundle
            self.model_label.setText(f"Model: {Path(path).name}")
            self.status_label.setText("Status: Model loaded")
        except Exception as exc:
            self.model_bundle = None
            self.model_label.setText("Model: load failed")
            self.status_label.setText(f"Status: Model error: {exc}")

    def connect_serial(self) -> None:
        if serial is None:
            self.status_label.setText("Status: pyserial is not installed")
            return
        port = self.port_combo.currentText()
        if port == "No ports found":
            self.status_label.setText("Status: No serial ports found")
            return
        try:
            self.serial_connection = serial.Serial(port=port, baudrate=int(self.baudrate_spin.value()), timeout=CONFIG.serial_timeout_s)
            time.sleep(2.0)
            self.serial_connection.reset_input_buffer()
            self.streaming = True
            self.status_label.setText(f"Status: Connected to {port}")
        except Exception as exc:
            self.serial_connection = None
            self.streaming = False
            self.status_label.setText(f"Status: Connection failed: {exc}")

    def disconnect_serial(self) -> None:
        self.streaming = False
        if self.serial_connection is not None:
            try:
                self.serial_connection.close()
            except Exception:
                pass
        self.serial_connection = None
        self.status_label.setText("Status: Disconnected")

    def reset_game(self) -> None:
        self.score_history.clear()
        self.progress.setValue(0)
        self.score_label.setText("Relaxation Score: -- / 100")
        self.state_label.setText("State: game reset")
        self.update_score_plot()

    def read_serial_data(self) -> None:
        if not self.streaming or self.serial_connection is None or not self.serial_connection.is_open:
            return
        for _ in range(CONFIG.serial_lines_per_tick):
            try:
                line = self.serial_connection.readline().decode("utf-8", errors="ignore")
            except Exception as exc:
                self.streaming = False
                self.status_label.setText(f"Status: Serial read error: {exc}")
                return
            value = parse_red_value(line)
            if value is not None:
                self.red_buffer.append(value)
                self.sample_index += 1

    def update_loop(self) -> None:
        self.read_serial_data()
        self.update_raw_plot()
        self.maybe_predict()

    def update_raw_plot(self) -> None:
        if len(self.red_buffer) < 2:
            return
        visible_samples = int(10 * CONFIG.sampling_rate_hz)
        red = np.array(self.red_buffer, dtype=float)[-visible_samples:]
        x = np.arange(len(red), dtype=float) / CONFIG.sampling_rate_hz
        x = x - x[-1]
        self.raw_curve.setData(x, red)
        self.raw_plot.setXRange(-10, 0, padding=0)

    def maybe_predict(self) -> None:
        if self.model_bundle is None:
            return
        window_samples = int(CONFIG.window_seconds * CONFIG.sampling_rate_hz)
        if len(self.red_buffer) < window_samples:
            percent = int(100 * len(self.red_buffer) / window_samples)
            self.progress.setValue(percent)
            self.state_label.setText("State: collecting enough signal for first score")
            return
        if self.sample_index - self.last_prediction_sample_index < window_samples:
            return

        red_window = np.array(self.red_buffer, dtype=float)[-window_samples:]
        features = compute_ppg_features(red_window, CONFIG.sampling_rate_hz)
        feature_names = list(self.model_bundle["features"])
        row = np.array([[features.get(name, 0.0) for name in feature_names]], dtype=float)
        pipeline = self.model_bundle["pipeline"]

        try:
            score = float(pipeline.predict_proba(row)[0, 1] * 100.0)
        except Exception:
            prediction = int(pipeline.predict(row)[0])
            score = 100.0 if prediction == 1 else 0.0

        self.score_history.append(score)
        self.last_prediction_sample_index = self.sample_index
        self.progress.setValue(int(round(score)))
        self.score_label.setText(f"Relaxation Score: {score:0.1f} / 100")
        if score >= 75:
            state = "Excellent relaxation"
        elif score >= 55:
            state = "Relaxing"
        elif score >= 35:
            state = "Mixed state"
        else:
            state = "Non-relaxed / try slower breathing"
        self.state_label.setText(f"State: {state}")
        self.update_score_plot()

    def update_score_plot(self) -> None:
        values = np.array(self.score_history, dtype=float)
        if len(values) == 0:
            self.score_curve.setData([], [])
            return
        x = np.arange(len(values))
        self.score_curve.setData(x, values)
        self.score_plot.setXRange(max(0, len(values) - 30), max(30, len(values)), padding=0)

    def closeEvent(self, event) -> None:
        self.disconnect_serial()
        event.accept()


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyleSheet(APPLE_STYLE)
    win = RelaxationGameWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
