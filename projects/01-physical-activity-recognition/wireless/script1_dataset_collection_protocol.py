# Copyright (c) 2026 Pietro Chierico
# SPDX-License-Identifier: MIT

"""
Script 1 - PPG Dataset Collection Protocol

Purpose
-------
Collect labeled PPG feature rows using this fixed protocol:
    20 s Stabilizing Data   -> not saved
    60 s Resting            -> saved as target Resting
    10 s Pause              -> not saved
    60 s Walking            -> saved as target Walking

Every 10-second IR window is converted into PPG noise features and appended to CSV.
Students can repeat the protocol as Record 1, Record 2, ... as many times as needed.

Input
-----
The ESP32 sends IR PPG data over WiFi TCP.
Default AP mode endpoint: 192.168.4.1 port 3333.
The parser accepts either one IR value per line, millis,ir, or millis,red,ir.

Install
-------
pip install numpy scipy pyqtgraph PyQt6

Run
---
python script1_dataset_collection_protocol.py
"""
from __future__ import annotations

import csv
import sys
import time
from collections import deque
from pathlib import Path
from typing import Optional

import numpy as np
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import (
    QApplication, QFileDialog, QGridLayout, QHBoxLayout, QLabel, QLineEdit,
    QMainWindow, QMessageBox, QPushButton, QProgressBar, QSpinBox, QVBoxLayout, QWidget
)
import pyqtgraph as pg

from ppg_feature_utils import (
    CSV_COLUMNS, PPGConfig, WiFiPPGClient, compute_ppg_noise_features, parse_ir_value
)

CONFIG = PPGConfig()

PROTOCOL = [
    ("Stabilizing Data", 20, None),
    ("Resting", 60, "Resting"),
    ("Pause", 10, None),
    ("Walking", 60, "Walking"),
]

APPLE_STYLE = """
QMainWindow, QWidget { background-color: #0b0f17; color: #f5f7fb; font-family: -apple-system, BlinkMacSystemFont, Segoe UI; }
QLabel { color: #f5f7fb; font-size: 14px; }
QPushButton { background-color: rgba(255,255,255,0.10); border: 1px solid rgba(255,255,255,0.18); border-radius: 14px; padding: 10px 16px; color: #f5f7fb; font-weight: 600; }
QPushButton:hover { background-color: rgba(255,255,255,0.18); }
QPushButton:pressed { background-color: rgba(255,255,255,0.26); }
QLineEdit, QSpinBox { background-color: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.20); border-radius: 12px; padding: 7px; color: #f5f7fb; }
QProgressBar { border: 1px solid rgba(255,255,255,0.20); border-radius: 10px; text-align: center; background-color: rgba(255,255,255,0.08); color: white; }
QProgressBar::chunk { border-radius: 10px; background-color: #36d399; }
"""


class DatasetCollectionWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("PPG Dataset Collection Protocol")
        self.resize(1200, 820)

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
        pg.setConfigOptions(antialias=True, background="#0b0f17", foreground="#f5f7fb")
        central = QWidget()
        layout = QVBoxLayout(central)
        top = QGridLayout()

        self.host_edit = QLineEdit(CONFIG.tcp_host)
        self.default_ip_button = QPushButton("Use AP IP")
        self.connect_button = QPushButton("Connect")
        self.disconnect_button = QPushButton("Disconnect")
        self.start_protocol_button = QPushButton("Start New Recording Protocol")
        self.stop_protocol_button = QPushButton("Stop Protocol")
        self.save_button = QPushButton("Save CSV")
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
        for button in [self.connect_button, self.disconnect_button, self.start_protocol_button, self.stop_protocol_button, self.save_button, self.clear_button]:
            buttons.addWidget(button)

        self.title_label = QLabel("Record 0 - Waiting")
        self.title_label.setStyleSheet("font-size: 30px; font-weight: 800;")
        self.phase_label = QLabel("Phase: --")
        self.phase_label.setStyleSheet("font-size: 24px; font-weight: 700;")
        self.time_label = QLabel("Time remaining: --")
        self.rows_label = QLabel("Feature rows: 0")
        self.status_label = QLabel("Status: Disconnected")
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)

        cards = QHBoxLayout()
        for label in [self.phase_label, self.time_label, self.rows_label, self.status_label]:
            label.setStyleSheet(label.styleSheet() + " background-color: rgba(255,255,255,0.07); border-radius: 18px; padding: 16px;")
            cards.addWidget(label)

        self.plot = pg.PlotWidget(title="Raw IR PPG Streaming")
        self.plot.setLabel("left", "IR value")
        self.plot.setLabel("bottom", "Time", units="s")
        self.plot.showGrid(x=True, y=True, alpha=0.25)
        self.curve = self.plot.plot([], [], pen=pg.mkPen(width=2), skipFiniteCheck=True)

        layout.addWidget(self.title_label)
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
        self.save_button.clicked.connect(self.save_csv)
        self.clear_button.clicked.connect(self.clear_rows)

    def _build_timer(self) -> None:
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_loop)
        self.timer.start(30)

    def use_access_point_ip(self) -> None:
        self.host_edit.setText(CONFIG.tcp_host)
        self.tcp_port_spin.setValue(CONFIG.tcp_port)

    def connect_wifi(self) -> None:
        host = self.host_edit.text().strip()
        port = int(self.tcp_port_spin.value())
        try:
            self.disconnect_wifi()
            self.tcp_client = WiFiPPGClient(host=host, port=port, connect_timeout_s=CONFIG.tcp_connect_timeout_s)
            self.streaming = True
            self.status_label.setText(f"Status: Connected to {host}:{port}")
        except Exception as exc:
            self.tcp_client = None
            self.streaming = False
            self.status_label.setText(f"Status: Connection failed: {exc}")

    def disconnect_wifi(self) -> None:
        self.streaming = False
        self.protocol_running = False
        if self.tcp_client is not None:
            try:
                self.tcp_client.close()
            except Exception:
                pass
        self.tcp_client = None
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
        self.title_label.setText(f"Record {self.recording_id} - Running Protocol")
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
            self.status_label.setText(f"Status: WiFi read error: {exc}")
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
        self.phase_label.setText(f"Phase: {phase_name}" + (f" - Target {target}" if target else " - Not saved"))
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
                self.status_label.setText("Status: Protocol complete. Start a new recording or save CSV.")
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
        features = compute_ppg_noise_features(ir_window, CONFIG.sampling_rate_hz)
        row = {
            "recording_id": self.recording_id,
            "timestamp_s": time.time(),
            "sample_index": self.sample_index,
            "protocol_phase": phase_name,
            "target": target,
            "window_seconds": CONFIG.window_seconds,
            **features,
        }
        self.rows.append(row)
        self.last_feature_sample_index = self.sample_index
        self.rows_label.setText(f"Feature rows: {len(self.rows)}")

    def save_csv(self) -> None:
        if not self.rows:
            QMessageBox.information(self, "No data", "No feature rows have been collected yet.")
            return
        default_name = f"ppg_resting_walking_dataset_{int(time.time())}.csv"
        path, _ = QFileDialog.getSaveFileName(self, "Save Dataset CSV", str(Path.home() / default_name), "CSV files (*.csv)")
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
                writer.writeheader()
                writer.writerows(self.rows)
            self.status_label.setText(f"Status: Saved CSV to {path}")
        except Exception as exc:
            QMessageBox.critical(self, "Save error", f"Could not save CSV:\n{exc}")

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
    win = DatasetCollectionWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
