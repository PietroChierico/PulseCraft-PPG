# Copyright (c) 2026 Pietro Chierico
# SPDX-License-Identifier: MIT

"""
Script 3 - Live PPG Resting vs Walking Classification

Purpose
-------
Load the exported model from Script 2, stream raw IR PPG values from WiFi TCP,
compute 10-second PPG noise features, and classify live as Resting or Walking.

Input
-----
The ESP32 sends IR PPG data over WiFi TCP.
Default AP mode endpoint: 192.168.4.1 port 3333.
The parser accepts either one IR value per line, millis,ir, or millis,red,ir.

Install
-------
pip install numpy scipy pyqtgraph PyQt6 scikit-learn joblib

Run
---
python script3_live_classification.py
"""
from __future__ import annotations

import sys
import time
from collections import deque
from pathlib import Path
from typing import Optional

import joblib
import numpy as np
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import (
    QApplication, QFileDialog, QGridLayout, QHBoxLayout, QLabel, QLineEdit,
    QMainWindow, QMessageBox, QPushButton, QSpinBox, QTextEdit, QVBoxLayout, QWidget
)
import pyqtgraph as pg

from ppg_feature_utils import PPGConfig, WiFiPPGClient, compute_ppg_noise_features, parse_ir_value

CONFIG = PPGConfig()

APPLE_STYLE = """
QMainWindow, QWidget { background-color: #0b0f17; color: #f5f7fb; font-family: -apple-system, BlinkMacSystemFont, Segoe UI; }
QLabel { color: #f5f7fb; font-size: 14px; }
QPushButton { background-color: rgba(255,255,255,0.10); border: 1px solid rgba(255,255,255,0.18); border-radius: 14px; padding: 10px 16px; color: #f5f7fb; font-weight: 600; }
QPushButton:hover { background-color: rgba(255,255,255,0.18); }
QLineEdit, QSpinBox, QTextEdit { background-color: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.20); border-radius: 12px; padding: 7px; color: #f5f7fb; }
"""


class LiveClassificationWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Live PPG Resting vs Walking Classification")
        self.resize(1250, 850)
        self.tcp_client: Optional[WiFiPPGClient] = None
        self.streaming = False
        self.sample_index = 0
        self.last_prediction_time = 0.0
        self.ir_buffer = deque(maxlen=CONFIG.max_samples)
        self.prediction_times = deque(maxlen=CONFIG.max_samples)
        self.walking_probabilities = deque(maxlen=CONFIG.max_samples)
        self.model_package: dict | None = None
        self.pipeline = None
        self.feature_names: list[str] = []
        self._build_ui()
        self._build_timer()

    def _build_ui(self) -> None:
        pg.setConfigOptions(antialias=True, background="#0b0f17", foreground="#f5f7fb")
        central = QWidget()
        root = QVBoxLayout(central)
        title = QLabel("Live PPG AI Classification")
        title.setStyleSheet("font-size: 30px; font-weight: 800;")
        root.addWidget(title)

        controls = QGridLayout()
        self.host_edit = QLineEdit(CONFIG.tcp_host)
        self.default_ip_button = QPushButton("Use AP IP")
        self.connect_button = QPushButton("Connect")
        self.disconnect_button = QPushButton("Disconnect")
        self.load_model_button = QPushButton("Load Model")
        self.start_button = QPushButton("Start Stream")
        self.stop_button = QPushButton("Stop Stream")
        self.clear_button = QPushButton("Clear")
        self.tcp_port_spin = QSpinBox()
        self.tcp_port_spin.setRange(1, 65535)
        self.tcp_port_spin.setValue(CONFIG.tcp_port)
        self.tcp_port_spin.setSingleStep(1)
        controls.addWidget(QLabel("ESP32 IP / Host"), 0, 0)
        controls.addWidget(self.host_edit, 0, 1)
        controls.addWidget(self.default_ip_button, 0, 2)
        controls.addWidget(QLabel("TCP Port"), 1, 0)
        controls.addWidget(self.tcp_port_spin, 1, 1)
        root.addLayout(controls)

        buttons = QHBoxLayout()
        for button in [self.load_model_button, self.connect_button, self.disconnect_button, self.start_button, self.stop_button, self.clear_button]:
            buttons.addWidget(button)
        root.addLayout(buttons)

        cards = QHBoxLayout()
        self.prediction_label = QLabel("Prediction: --")
        self.prediction_label.setStyleSheet("font-size: 34px; font-weight: 900; background-color: rgba(255,255,255,0.07); border-radius: 18px; padding: 20px;")
        self.confidence_label = QLabel("Confidence: --")
        self.status_label = QLabel("Status: Load model and connect WiFi")
        for label in [self.prediction_label, self.confidence_label, self.status_label]:
            label.setStyleSheet(label.styleSheet() + " background-color: rgba(255,255,255,0.07); border-radius: 18px; padding: 16px;")
            cards.addWidget(label)
        root.addLayout(cards)

        self.raw_plot = pg.PlotWidget(title="Raw IR PPG Stream")
        self.raw_plot.setLabel("left", "IR value")
        self.raw_plot.setLabel("bottom", "Time", units="s")
        self.raw_plot.showGrid(x=True, y=True, alpha=0.25)
        self.raw_curve = self.raw_plot.plot([], [], pen=pg.mkPen(width=2), skipFiniteCheck=True)

        self.prob_plot = pg.PlotWidget(title="Walking Probability Over Time")
        self.prob_plot.setLabel("left", "P(Walking)")
        self.prob_plot.setLabel("bottom", "Time", units="s")
        self.prob_plot.setYRange(0, 1)
        self.prob_plot.showGrid(x=True, y=True, alpha=0.25)
        self.prob_curve = self.prob_plot.plot([], [], pen=pg.mkPen(width=2), skipFiniteCheck=True)

        self.feature_text = QTextEdit()
        self.feature_text.setReadOnly(True)
        self.feature_text.setMaximumHeight(180)

        root.addWidget(self.raw_plot)
        root.addWidget(self.prob_plot)
        root.addWidget(self.feature_text)
        self.setCentralWidget(central)

        self.default_ip_button.clicked.connect(self.use_access_point_ip)
        self.load_model_button.clicked.connect(self.load_model)
        self.connect_button.clicked.connect(self.connect_wifi)
        self.disconnect_button.clicked.connect(self.disconnect_wifi)
        self.start_button.clicked.connect(self.start_stream)
        self.stop_button.clicked.connect(self.stop_stream)
        self.clear_button.clicked.connect(self.clear_data)

    def _build_timer(self) -> None:
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_loop)
        self.timer.start(30)

    def use_access_point_ip(self) -> None:
        self.host_edit.setText(CONFIG.tcp_host)
        self.tcp_port_spin.setValue(CONFIG.tcp_port)

    def load_model(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Load Exported Model", str(Path.home()), "Joblib files (*.joblib)")
        if not path:
            return
        try:
            package = joblib.load(path)
            self.pipeline = package["pipeline"]
            self.feature_names = list(package["feature_names"])
            self.model_package = package
            self.status_label.setText(f"Status: Model loaded - {Path(path).name}")
            self.feature_text.setText(f"Model features:\n{self.feature_names}")
        except Exception as exc:
            QMessageBox.critical(self, "Model load error", f"Could not load model:\n{exc}")

    def connect_wifi(self) -> None:
        host = self.host_edit.text().strip()
        port = int(self.tcp_port_spin.value())
        try:
            self.disconnect_wifi()
            self.tcp_client = WiFiPPGClient(host=host, port=port, connect_timeout_s=CONFIG.tcp_connect_timeout_s)
            self.status_label.setText(f"Status: Connected to {host}:{port}")
        except Exception as exc:
            self.tcp_client = None
            self.status_label.setText(f"Status: Connection failed: {exc}")

    def disconnect_wifi(self) -> None:
        self.streaming = False
        if self.tcp_client is not None:
            try:
                self.tcp_client.close()
            except Exception:
                pass
        self.tcp_client = None
        self.status_label.setText("Status: Disconnected")

    def start_stream(self) -> None:
        if self.pipeline is None:
            self.status_label.setText("Status: Load a model first")
            return
        if self.tcp_client is None or not self.tcp_client.connected:
            self.status_label.setText("Status: Connect WiFi first")
            return
        self.streaming = True
        self.status_label.setText("Status: Streaming and classifying")

    def stop_stream(self) -> None:
        self.streaming = False
        self.status_label.setText("Status: Stream paused")

    def clear_data(self) -> None:
        self.ir_buffer.clear()
        self.prediction_times.clear()
        self.walking_probabilities.clear()
        self.sample_index = 0
        self.raw_curve.setData([], [])
        self.prob_curve.setData([], [])
        self.prediction_label.setText("Prediction: --")
        self.confidence_label.setText("Confidence: --")
        self.feature_text.clear()

    def read_wifi_data(self) -> None:
        if not self.streaming or self.tcp_client is None or not self.tcp_client.connected:
            return
        try:
            lines = self.tcp_client.read_lines(CONFIG.tcp_lines_per_tick)
        except Exception as exc:
            self.streaming = False
            self.status_label.setText(f"Status: WiFi read error: {exc}")
            return

        for line in lines:
            value = parse_ir_value(line)
            if value is not None:
                self.ir_buffer.append(value)
                self.sample_index += 1

    def update_loop(self) -> None:
        self.read_wifi_data()
        self.update_raw_plot()
        now = time.time()
        if self.streaming and now - self.last_prediction_time >= 1.0:
            self.last_prediction_time = now
            self.update_prediction()

    def update_raw_plot(self) -> None:
        if len(self.ir_buffer) < 2:
            return
        visible_samples = int(10 * CONFIG.sampling_rate_hz)
        ir = np.array(self.ir_buffer, dtype=float)[-visible_samples:]
        x = np.arange(len(ir), dtype=float) / CONFIG.sampling_rate_hz
        x = x - x[-1]
        self.raw_curve.setData(x, ir)
        self.raw_plot.setXRange(-10, 0, padding=0)

    def update_prediction(self) -> None:
        window_samples = int(CONFIG.window_seconds * CONFIG.sampling_rate_hz)
        if self.pipeline is None or len(self.ir_buffer) < window_samples:
            self.prediction_label.setText("Prediction: collecting window...")
            return
        ir_window = np.array(self.ir_buffer, dtype=float)[-window_samples:]
        features = compute_ppg_noise_features(ir_window, CONFIG.sampling_rate_hz)
        X = np.array([[features[name] for name in self.feature_names]], dtype=float)
        prediction = str(self.pipeline.predict(X)[0])

        confidence = None
        walking_probability = 1.0 if prediction == "Walking" else 0.0
        if hasattr(self.pipeline, "predict_proba"):
            probs = self.pipeline.predict_proba(X)[0]
            classes = list(self.pipeline.classes_)
            probability_map = dict(zip(classes, probs))
            walking_probability = float(probability_map.get("Walking", 0.0))
            confidence = float(max(probs))

        self.prediction_times.append(self.sample_index / CONFIG.sampling_rate_hz)
        self.walking_probabilities.append(walking_probability)

        color = "#36d399" if prediction == "Resting" else "#ff5c7a"
        self.prediction_label.setText(f"Prediction: {prediction}")
        self.prediction_label.setStyleSheet(f"font-size: 34px; font-weight: 900; color: {color}; background-color: rgba(255,255,255,0.07); border-radius: 18px; padding: 20px;")
        self.confidence_label.setText("Confidence: --" if confidence is None else f"Confidence: {confidence:.2f}")

        self.update_probability_plot()
        self.feature_text.setText("Current 10-second feature window:\n" + "\n".join(f"{k}: {features[k]:.4f}" for k in self.feature_names))

    def update_probability_plot(self) -> None:
        if len(self.walking_probabilities) < 2:
            return
        t = np.array(self.prediction_times, dtype=float)
        y = np.array(self.walking_probabilities, dtype=float)
        t = t - t[-1]
        self.prob_curve.setData(t, y)
        self.prob_plot.setXRange(-60, 0, padding=0)

    def closeEvent(self, event) -> None:
        self.disconnect_wifi()
        event.accept()


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyleSheet(APPLE_STYLE)
    win = LiveClassificationWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
