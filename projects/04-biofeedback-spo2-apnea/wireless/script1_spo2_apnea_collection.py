# Copyright (c) 2026 Pietro Chierico
# SPDX-License-Identifier: MIT

"""
Script 1 - SpO2 Voluntary Apnea Dataset Collection

Purpose
-------
Collect a voluntary apnea dataset from an ESP32/MAX3010x WiFi TCP stream.
The ESP32 sends paired Red and Infrared PPG values, so this script plots both
channels together and estimates SpO2 from the Red/Infrared ratio of ratios.

Important
---------
This is an educational biomedical-signal demo only. SpO2 estimation depends on
sensor geometry, calibration, signal quality, and the specific optical setup.
It is not a medical device, not a diagnostic tool, and must not be used for
safety-critical breath-holding decisions.

Input
-----
Default AP mode endpoint: 192.168.4.1 port 3333.
Accepted TCP line formats:
    Red: 12345 Infrared: 67890
    Red: 12345 IR: 67890
    red=12345, ir=67890
    12345, 67890
    12345 67890
    1000,12345,67890

Install
-------
pip install numpy pyqtgraph PyQt6

Run
---
python script1_spo2_apnea_collection.py
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
    QApplication, QFileDialog, QGridLayout, QHBoxLayout, QLabel,
    QLineEdit, QMainWindow, QMessageBox, QPushButton, QProgressBar, QSpinBox,
    QVBoxLayout, QWidget
)
import pyqtgraph as pg

from ppg_wifi_ir_stream import (
    WiFiPPGClient,
    estimate_spo2_from_red_ir_windows,
    parse_red_ir_values,
)


SAMPLING_RATE_HZ = 100
MAX_SECONDS_ON_SCREEN = 20
MAX_BUFFER_SECONDS = 180

BASELINE_SECONDS = 30
RECOVERY_SECONDS = 60

ESP32_HOST_DEFAULT = "192.168.4.1"
TCP_PORT_DEFAULT = 3333
TCP_CONNECT_TIMEOUT_S = 5.0
TCP_LINES_PER_TICK = 80

SPO2_WINDOW_SECONDS = 5
SPO2_UPDATE_SECONDS = 5

# Fixed offset added in the microcontroller code, if any.
WIFI_VALUE_OFFSET = 0

# If the Arduino sketch sends mirrored PPG values (-PPG), keep this True.
# SpO2 math needs positive optical-intensity DC levels, so the calculation
# flips mirrored streams back internally before AC/DC normalization.
PPG_STREAM_IS_NEGATED = False

# Educational SpO2 display curve. For a real oximeter, this curve must be
# calibrated for the exact sensor, wavelength pair, mechanical setup, and tissue.
SPO2_CALIBRATION_INTERCEPT = 110.0
SPO2_CALIBRATION_SLOPE = 25.0
SPO2_MIN_PERCENT = 70.0
SPO2_MAX_PERCENT = 100.0

CSV_COLUMNS = [
    "timestamp_s", "subject_id", "trial_id", "phase", "elapsed_trial_s",
    "red_raw", "ir_raw", "red_corrected", "ir_corrected",
    "spo2_estimate", "ratio_of_ratios"
]

APPLE_STYLE = """
QMainWindow, QWidget { background-color: #07111f; color: #f5f7fb; font-family: -apple-system, BlinkMacSystemFont, Segoe UI; }
QLabel { color: #f5f7fb; font-size: 14px; }
QLineEdit, QSpinBox { background-color: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.20); border-radius: 12px; padding: 8px; color: #f5f7fb; }
QPushButton { background-color: rgba(255,255,255,0.10); border: 1px solid rgba(255,255,255,0.18); border-radius: 14px; padding: 10px 16px; color: #f5f7fb; font-weight: 700; }
QPushButton:hover { background-color: rgba(255,255,255,0.18); }
QPushButton:pressed { background-color: rgba(255,255,255,0.26); }
QProgressBar { border: 1px solid rgba(255,255,255,0.20); border-radius: 10px; text-align: center; background-color: rgba(255,255,255,0.08); color: white; }
QProgressBar::chunk { border-radius: 10px; background-color: #19c8ff; }
"""


class ApneaCollectionWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("SpO2 Voluntary Apnea Collection - WiFi Red + IR")
        self.resize(1300, 880)

        self.tcp_client: Optional[WiFiPPGClient] = None
        self.streaming = False

        self.phase = "Idle"
        self.phase_start_time = 0.0
        self.trial_start_time = 0.0
        self.plot_start_time = time.time()

        self.trial_id = 0
        self.rows: list[dict[str, float | int | str]] = []

        self.last_spo2_update_time = 0.0
        self.current_spo2 = np.nan
        self.current_ratio = np.nan

        self.red_raw_buffer = deque(maxlen=SAMPLING_RATE_HZ * MAX_BUFFER_SECONDS)
        self.ir_raw_buffer = deque(maxlen=SAMPLING_RATE_HZ * MAX_BUFFER_SECONDS)
        self.red_corrected_buffer = deque(maxlen=SAMPLING_RATE_HZ * MAX_BUFFER_SECONDS)
        self.ir_corrected_buffer = deque(maxlen=SAMPLING_RATE_HZ * MAX_BUFFER_SECONDS)
        self.spo2_buffer = deque(maxlen=SAMPLING_RATE_HZ * MAX_BUFFER_SECONDS)
        self.time_buffer = deque(maxlen=SAMPLING_RATE_HZ * MAX_BUFFER_SECONDS)

        self._build_ui()
        self._build_timer()

    def _build_ui(self) -> None:
        pg.setConfigOptions(antialias=True, background="#07111f", foreground="#f5f7fb")

        central = QWidget()
        layout = QVBoxLayout(central)

        self.title_label = QLabel("Voluntary Apnea SpO2 Collection - WiFi Red + IR")
        self.title_label.setStyleSheet("font-size: 32px; font-weight: 900;")

        self.safety_label = QLabel(
            "Safety: voluntary short breath-hold only. Stop immediately if uncomfortable. SpO2 is an educational Red/IR estimate."
        )
        self.safety_label.setStyleSheet(
            "font-size: 16px; color: #ffdf7e; font-weight: 700;"
        )

        top = QGridLayout()

        self.subject_edit = QLineEdit("S01")
        self.host_edit = QLineEdit(ESP32_HOST_DEFAULT)
        self.default_ip_button = QPushButton("Use AP IP")
        self.connect_button = QPushButton("Connect")
        self.disconnect_button = QPushButton("Disconnect")

        self.tcp_port_spin = QSpinBox()
        self.tcp_port_spin.setRange(1, 65535)
        self.tcp_port_spin.setSingleStep(1)
        self.tcp_port_spin.setValue(TCP_PORT_DEFAULT)

        top.addWidget(QLabel("Subject ID"), 0, 0)
        top.addWidget(self.subject_edit, 0, 1)
        top.addWidget(QLabel("ESP32 IP / Host"), 1, 0)
        top.addWidget(self.host_edit, 1, 1)
        top.addWidget(self.default_ip_button, 1, 2)
        top.addWidget(QLabel("TCP Port"), 2, 0)
        top.addWidget(self.tcp_port_spin, 2, 1)

        buttons = QHBoxLayout()

        self.start_trial_button = QPushButton("Start New Trial: Baseline")
        self.start_apnea_button = QPushButton("Start Apnea Now")
        self.stop_apnea_button = QPushButton("Stop Apnea and Start Recovery")
        self.export_button = QPushButton("Export Data CSV")
        self.clear_button = QPushButton("Clear Data")

        for button in [
            self.connect_button,
            self.disconnect_button,
            self.start_trial_button,
            self.start_apnea_button,
            self.stop_apnea_button,
            self.export_button,
            self.clear_button,
        ]:
            buttons.addWidget(button)

        cards = QHBoxLayout()

        self.phase_label = QLabel("Phase: Idle")
        self.trial_label = QLabel("Trial: 0")
        self.spo2_label = QLabel("SpO2 estimate: --")
        self.rows_label = QLabel("Rows: 0")
        self.status_label = QLabel("Status: Disconnected")

        for label in [
            self.phase_label,
            self.trial_label,
            self.spo2_label,
            self.rows_label,
            self.status_label,
        ]:
            label.setStyleSheet(
                "background-color: rgba(255,255,255,0.07); "
                "border-radius: 18px; padding: 16px; "
                "font-size: 16px; font-weight: 700;"
            )
            cards.addWidget(label)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)

        self.ppg_plot = pg.PlotWidget(title="Red and Infrared PPG WiFi Streaming")
        self.ppg_plot.setLabel("left", "PPG value")
        self.ppg_plot.setLabel("bottom", "Elapsed time", units="s")
        self.ppg_plot.showGrid(x=True, y=True, alpha=0.25)
        self.ppg_plot.addLegend()

        self.red_curve = self.ppg_plot.plot(
            [], [], pen=pg.mkPen("#ff5f7e", width=2), name="Red"
        )
        self.ir_curve = self.ppg_plot.plot(
            [], [], pen=pg.mkPen("#7ddfff", width=2), name="Infrared"
        )

        self.spo2_plot = pg.PlotWidget(title="Estimated SpO2 Trend from Red + IR")
        self.spo2_plot.setLabel("left", "SpO2 estimate", units="%")
        self.spo2_plot.setLabel("bottom", "Elapsed time", units="s")
        self.spo2_plot.setYRange(85, 101)
        self.spo2_plot.showGrid(x=True, y=True, alpha=0.25)

        self.spo2_curve = self.spo2_plot.plot(
            [], [], pen=pg.mkPen("#36d399", width=3)
        )

        layout.addWidget(self.title_label)
        layout.addWidget(self.safety_label)
        layout.addLayout(top)
        layout.addLayout(buttons)
        layout.addLayout(cards)
        layout.addWidget(self.progress)
        layout.addWidget(self.ppg_plot)
        layout.addWidget(self.spo2_plot)

        self.setCentralWidget(central)

        self.default_ip_button.clicked.connect(self.use_access_point_ip)
        self.connect_button.clicked.connect(self.connect_wifi)
        self.disconnect_button.clicked.connect(self.disconnect_wifi)
        self.start_trial_button.clicked.connect(self.start_trial)
        self.start_apnea_button.clicked.connect(self.start_apnea)
        self.stop_apnea_button.clicked.connect(self.stop_apnea)
        self.export_button.clicked.connect(self.export_csv)
        self.clear_button.clicked.connect(self.clear_data)

    def _build_timer(self) -> None:
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_loop)
        self.timer.start(30)

    def use_access_point_ip(self) -> None:
        self.host_edit.setText(ESP32_HOST_DEFAULT)
        self.tcp_port_spin.setValue(TCP_PORT_DEFAULT)

    def connect_wifi(self) -> None:
        self.disconnect_wifi(update_status=False)
        host = self.host_edit.text().strip()
        port = int(self.tcp_port_spin.value())

        try:
            self.tcp_client = WiFiPPGClient(
                host=host,
                port=port,
                connect_timeout_s=TCP_CONNECT_TIMEOUT_S,
            )
            self.streaming = True
            self.plot_start_time = time.time()
            self.status_label.setText(f"Status: Connected to {host}:{port}")

        except Exception as exc:
            self.tcp_client = None
            self.streaming = False
            self.status_label.setText(f"Status: Connection failed: {exc}")

    def disconnect_wifi(self, update_status: bool = True) -> None:
        self.streaming = False
        self.phase = "Idle"

        if self.tcp_client is not None:
            try:
                self.tcp_client.close()
            except Exception:
                pass

        self.tcp_client = None
        if update_status:
            self.status_label.setText("Status: Disconnected")

    def start_trial(self) -> None:
        if self.tcp_client is None or not self.tcp_client.connected:
            self.status_label.setText("Status: Connect WiFi before starting")
            return

        self.trial_id += 1
        self.phase = "Baseline"
        self.phase_start_time = time.time()
        self.trial_start_time = self.phase_start_time
        self.plot_start_time = self.phase_start_time
        self.last_spo2_update_time = 0.0
        self.current_spo2 = np.nan
        self.current_ratio = np.nan

        self.progress.setValue(0)
        self.status_label.setText("Status: Baseline recording started")

    def start_apnea(self) -> None:
        if self.tcp_client is None or not self.tcp_client.connected:
            self.status_label.setText("Status: Connect WiFi before starting")
            return

        if self.phase == "Apnea":
            self.status_label.setText("Status: Apnea is already running")
            return

        if self.trial_id == 0:
            self.start_trial()
            if self.trial_id == 0:
                return

        self.phase = "Apnea"
        self.phase_start_time = time.time()
        self.status_label.setText("Status: Apnea phase started by user")

    def stop_apnea(self) -> None:
        if self.phase != "Apnea":
            self.status_label.setText("Status: No apnea phase is currently running")
            return

        self.phase = "Recovery"
        self.phase_start_time = time.time()
        self.status_label.setText("Status: Recovery recording started")

    def read_wifi_data(self) -> None:
        if not self.streaming or self.tcp_client is None or not self.tcp_client.connected:
            return

        try:
            lines = self.tcp_client.read_lines(TCP_LINES_PER_TICK)
        except Exception as exc:
            self.streaming = False
            self.phase = "Idle"
            self.status_label.setText(f"Status: WiFi TCP read error: {exc}")
            return

        for line in lines:
            red_raw, ir_raw = parse_red_ir_values(line)
            if (
                red_raw is None
                or ir_raw is None
                or not np.isfinite(red_raw)
                or not np.isfinite(ir_raw)
            ):
                continue

            now = time.time()
            red_corrected = red_raw - WIFI_VALUE_OFFSET
            ir_corrected = ir_raw - WIFI_VALUE_OFFSET

            self.red_raw_buffer.append(red_raw)
            self.ir_raw_buffer.append(ir_raw)
            self.red_corrected_buffer.append(red_corrected)
            self.ir_corrected_buffer.append(ir_corrected)
            self.time_buffer.append(now)

            self.update_spo2_if_needed(now)
            self.spo2_buffer.append(self.current_spo2)

            if self.phase in {"Baseline", "Apnea", "Recovery"}:
                row = {
                    "timestamp_s": now,
                    "subject_id": self.subject_edit.text().strip() or "Unknown",
                    "trial_id": self.trial_id,
                    "phase": self.phase,
                    "elapsed_trial_s": now - self.trial_start_time,
                    "red_raw": red_raw,
                    "ir_raw": ir_raw,
                    "red_corrected": red_corrected,
                    "ir_corrected": ir_corrected,
                    "spo2_estimate": self.current_spo2,
                    "ratio_of_ratios": self.current_ratio,
                }

                self.rows.append(row)
                self.rows_label.setText(f"Rows: {len(self.rows)}")

    def update_spo2_if_needed(self, now: float) -> None:
        if now - self.last_spo2_update_time < SPO2_UPDATE_SECONDS:
            return

        window_samples = int(SPO2_WINDOW_SECONDS * SAMPLING_RATE_HZ)

        if len(self.red_raw_buffer) < window_samples or len(self.ir_raw_buffer) < window_samples:
            return

        red_window = np.array(self.red_raw_buffer, dtype=float)[-window_samples:]
        ir_window = np.array(self.ir_raw_buffer, dtype=float)[-window_samples:]

        spo2, ratio = estimate_spo2_from_red_ir_windows(
            red_window,
            ir_window,
            minimum_samples=window_samples,
            value_offset=WIFI_VALUE_OFFSET,
            stream_is_negated=PPG_STREAM_IS_NEGATED,
            calibration_intercept=SPO2_CALIBRATION_INTERCEPT,
            calibration_slope=SPO2_CALIBRATION_SLOPE,
            min_percent=SPO2_MIN_PERCENT,
            max_percent=SPO2_MAX_PERCENT,
        )

        self.last_spo2_update_time = now
        self.current_ratio = ratio
        self.current_spo2 = spo2

        if np.isnan(spo2):
            self.spo2_label.setText("SpO2 estimate: calibrating")
        else:
            self.spo2_label.setText(f"SpO2 estimate: {spo2:0.1f}%")

    def update_loop(self) -> None:
        self.read_wifi_data()
        self.update_phase_logic()
        self.update_plots()

    def update_phase_logic(self) -> None:
        self.phase_label.setText(f"Phase: {self.phase}")
        self.trial_label.setText(f"Trial: {self.trial_id}")

        if self.phase == "Baseline":
            elapsed = time.time() - self.phase_start_time
            self.progress.setValue(int(100 * min(elapsed / BASELINE_SECONDS, 1)))

            if elapsed >= BASELINE_SECONDS:
                self.status_label.setText(
                    "Status: Baseline complete. Press Start Apnea when ready."
                )

        elif self.phase == "Apnea":
            elapsed = time.time() - self.phase_start_time
            self.progress.setValue(min(int(elapsed), 100))

        elif self.phase == "Recovery":
            elapsed = time.time() - self.phase_start_time
            self.progress.setValue(int(100 * min(elapsed / RECOVERY_SECONDS, 1)))

            if elapsed >= RECOVERY_SECONDS:
                self.phase = "Complete"
                self.status_label.setText(
                    "Status: Trial complete. Start another trial or export data."
                )

        else:
            self.progress.setValue(0)

    def update_plots(self) -> None:
        if len(self.time_buffer) < 2:
            return

        visible = int(MAX_SECONDS_ON_SCREEN * SAMPLING_RATE_HZ)

        times = np.array(self.time_buffer, dtype=float)[-visible:]
        x = times - self.plot_start_time

        red = np.array(self.red_corrected_buffer, dtype=float)[-visible:]
        ir = np.array(self.ir_corrected_buffer, dtype=float)[-visible:]
        spo2 = np.array(self.spo2_buffer, dtype=float)[-visible:]

        self.red_curve.setData(x, red)
        self.ir_curve.setData(x, ir)
        self.spo2_curve.setData(x, spo2)

        x_max = float(x[-1])
        x_min = max(0.0, x_max - MAX_SECONDS_ON_SCREEN)

        self.ppg_plot.setXRange(x_min, x_max, padding=0)
        self.spo2_plot.setXRange(x_min, x_max, padding=0)

    def export_csv(self) -> None:
        if not self.rows:
            QMessageBox.information(self, "No data", "No rows have been collected yet.")
            return

        default_name = f"spo2_voluntary_apnea_wifi_red_ir_dataset_{int(time.time())}.csv"

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Data CSV",
            str(Path.home() / default_name),
            "CSV files (*.csv)",
        )

        if not path:
            return

        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
                writer.writeheader()
                writer.writerows(self.rows)

            self.status_label.setText(f"Status: Exported CSV to {path}")

        except Exception as exc:
            QMessageBox.critical(self, "Export error", f"Could not export CSV:\n{exc}")

    def clear_data(self) -> None:
        self.rows.clear()
        self.rows_label.setText("Rows: 0")
        self.status_label.setText("Status: Data cleared")

    def closeEvent(self, event) -> None:
        self.disconnect_wifi()
        event.accept()


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyleSheet(APPLE_STYLE)

    win = ApneaCollectionWindow()
    win.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
