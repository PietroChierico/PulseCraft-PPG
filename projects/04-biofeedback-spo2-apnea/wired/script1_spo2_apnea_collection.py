# Copyright (c) 2026 Pietro Chierico
# SPDX-License-Identifier: MIT

"""
Script 1 - SpO2 Voluntary Apnea Dataset Collection
"""

from __future__ import annotations

import csv
import re
import sys
import time
from collections import deque
from pathlib import Path
from typing import Optional

import numpy as np
import serial
from serial.tools import list_ports
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import (
    QApplication, QComboBox, QFileDialog, QGridLayout, QHBoxLayout, QLabel,
    QLineEdit, QMainWindow, QMessageBox, QPushButton, QProgressBar, QSpinBox,
    QVBoxLayout, QWidget
)
import pyqtgraph as pg


SAMPLING_RATE_HZ = 100
MAX_SECONDS_ON_SCREEN = 20
MAX_BUFFER_SECONDS = 180

BASELINE_SECONDS = 30
RECOVERY_SECONDS = 60

BAUDRATE_DEFAULT = 115200
SERIAL_TIMEOUT_S = 0.02
SERIAL_LINES_PER_TICK = 40

SPO2_WINDOW_SECONDS = 5
SPO2_UPDATE_SECONDS = 5

# If your microcontroller adds +10000 before sending the values,
# keep this at 10000. If it sends true raw values, set this to 0.
SERIAL_VALUE_OFFSET = 0
SERIAL_STREAM_IS_NEGATED = False

CSV_COLUMNS = [
    "timestamp_s", "subject_id", "trial_id", "phase", "elapsed_trial_s",
    "red_raw", "ir_raw", "red_corrected", "ir_corrected",
    "spo2_estimate", "ratio_of_ratios"
]

APPLE_STYLE = """
QMainWindow, QWidget { background-color: #07111f; color: #f5f7fb; font-family: -apple-system, BlinkMacSystemFont, Segoe UI; }
QLabel { color: #f5f7fb; font-size: 14px; }
QLineEdit, QComboBox, QSpinBox { background-color: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.20); border-radius: 12px; padding: 8px; color: #f5f7fb; }
QPushButton { background-color: rgba(255,255,255,0.10); border: 1px solid rgba(255,255,255,0.18); border-radius: 14px; padding: 10px 16px; color: #f5f7fb; font-weight: 700; }
QPushButton:hover { background-color: rgba(255,255,255,0.18); }
QPushButton:pressed { background-color: rgba(255,255,255,0.26); }
QProgressBar { border: 1px solid rgba(255,255,255,0.20); border-radius: 10px; text-align: center; background-color: rgba(255,255,255,0.08); color: white; }
QProgressBar::chunk { border-radius: 10px; background-color: #19c8ff; }
"""


def list_serial_ports() -> list[str]:
    return [p.device for p in list_ports.comports()]


def parse_red_ir(line: str) -> Optional[tuple[float, float]]:
    """Parse one serial line and return the Red and IR samples.

    Supported formats include ``red,ir`` and ``time_us,red,ir``. When more
    than two numeric values are present, the last two numbers are treated as
    Red and IR so timestamped Arduino lines are parsed correctly.
    """
    numbers = re.findall(r"[-+]?\d*\.?\d+", line)
    if len(numbers) < 2:
        return None

    red_raw = float(numbers[-2])
    ir_raw = float(numbers[-1])

    if not np.isfinite(red_raw) or not np.isfinite(ir_raw):
        return None

    return red_raw, ir_raw


def estimate_spo2(
    red_raw_window: np.ndarray,
    ir_raw_window: np.ndarray,
) -> tuple[float, float]:
    """
    Educational SpO2 estimate using the ratio-of-ratios method.

    Important:
    - SpO2 requires a real optical DC component.
    - If the microcontroller added a fake offset, this function removes it.
    - If the corrected signal has no valid DC component, SpO2 is not reliable.
    """

    red_raw = np.asarray(red_raw_window, dtype=float)
    ir_raw = np.asarray(ir_raw_window, dtype=float)

    if len(red_raw) < SPO2_WINDOW_SECONDS * SAMPLING_RATE_HZ:
        return np.nan, np.nan

    red = red_raw - SERIAL_VALUE_OFFSET
    ir = ir_raw - SERIAL_VALUE_OFFSET
    if SERIAL_STREAM_IS_NEGATED:
        red = -red
        ir = -ir

    red_dc = float(np.mean(red))
    ir_dc = float(np.mean(ir))

    # Robust AC amplitude estimate.
    red_ac = float(np.percentile(red, 95) - np.percentile(red, 5))
    ir_ac = float(np.percentile(ir, 95) - np.percentile(ir, 5))

    if red_ac <= 0 or ir_ac <= 0:
        return np.nan, np.nan

    # A valid pulse oximetry DC component should not be near zero.
    if abs(red_dc) < 1e-6 or abs(ir_dc) < 1e-6:
        return np.nan, np.nan

    ratio = (red_ac / abs(red_dc)) / (ir_ac / abs(ir_dc))

    if not np.isfinite(ratio) or ratio <= 0:
        return np.nan, np.nan

    # Educational approximation only. Real devices require calibration.
    spo2 = 110.0 - 25.0 * ratio
    spo2 = float(np.clip(spo2, 70.0, 100.0))

    return spo2, float(ratio)


class ApneaCollectionWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("SpO2 Voluntary Apnea Collection")
        self.resize(1300, 880)

        self.serial_connection: Optional[serial.Serial] = None
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

        self.title_label = QLabel("Voluntary Apnea SpO2 Collection")
        self.title_label.setStyleSheet("font-size: 32px; font-weight: 900;")

        self.safety_label = QLabel(
            "Safety: voluntary short breath-hold only. Stop immediately if uncomfortable."
        )
        self.safety_label.setStyleSheet(
            "font-size: 16px; color: #ffdf7e; font-weight: 700;"
        )

        top = QGridLayout()

        self.subject_edit = QLineEdit("S01")

        self.port_combo = QComboBox()
        self.refresh_button = QPushButton("Refresh Ports")
        self.connect_button = QPushButton("Connect")
        self.disconnect_button = QPushButton("Disconnect")

        self.baudrate_spin = QSpinBox()
        self.baudrate_spin.setRange(9600, 921600)
        self.baudrate_spin.setSingleStep(9600)
        self.baudrate_spin.setValue(BAUDRATE_DEFAULT)

        top.addWidget(QLabel("Subject ID"), 0, 0)
        top.addWidget(self.subject_edit, 0, 1)
        top.addWidget(QLabel("Serial Port"), 1, 0)
        top.addWidget(self.port_combo, 1, 1)
        top.addWidget(self.refresh_button, 1, 2)
        top.addWidget(QLabel("Baudrate"), 2, 0)
        top.addWidget(self.baudrate_spin, 2, 1)

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
        self.spo2_label = QLabel("SpO2: --")
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

        self.ppg_plot = pg.PlotWidget(title="RED and IR PPG Streaming")
        self.ppg_plot.setLabel("left", "PPG value")
        self.ppg_plot.setLabel("bottom", "Elapsed time", units="s")
        self.ppg_plot.showGrid(x=True, y=True, alpha=0.25)
        self.ppg_plot.addLegend()

        self.red_curve = self.ppg_plot.plot(
            [], [], pen=pg.mkPen("#ff5c7a", width=2), name="RED"
        )
        self.ir_curve = self.ppg_plot.plot(
            [], [], pen=pg.mkPen("#7ddfff", width=2), name="IR"
        )

        self.spo2_plot = pg.PlotWidget(title="Estimated SpO2 Trend")
        self.spo2_plot.setLabel("left", "SpO2", units="%")
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

        self.refresh_ports()

        self.refresh_button.clicked.connect(self.refresh_ports)
        self.connect_button.clicked.connect(self.connect_serial)
        self.disconnect_button.clicked.connect(self.disconnect_serial)
        self.start_trial_button.clicked.connect(self.start_trial)
        self.start_apnea_button.clicked.connect(self.start_apnea)
        self.stop_apnea_button.clicked.connect(self.stop_apnea)
        self.export_button.clicked.connect(self.export_csv)
        self.clear_button.clicked.connect(self.clear_data)

    def _build_timer(self) -> None:
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_loop)
        self.timer.start(30)

    def refresh_ports(self) -> None:
        self.port_combo.clear()
        ports = list_serial_ports()
        self.port_combo.addItems(ports if ports else ["No ports found"])

    def connect_serial(self) -> None:
        port = self.port_combo.currentText()

        if port == "No ports found":
            self.status_label.setText("Status: No serial ports found")
            return

        try:
            self.serial_connection = serial.Serial(
                port=port,
                baudrate=int(self.baudrate_spin.value()),
                timeout=SERIAL_TIMEOUT_S,
            )
            time.sleep(2.0)
            self.serial_connection.reset_input_buffer()
            self.streaming = True
            self.plot_start_time = time.time()
            self.status_label.setText(f"Status: Connected to {port}")

        except Exception as exc:
            self.serial_connection = None
            self.streaming = False
            self.status_label.setText(f"Status: Connection failed: {exc}")

    def disconnect_serial(self) -> None:
        self.streaming = False
        self.phase = "Idle"

        if self.serial_connection is not None:
            try:
                self.serial_connection.close()
            except Exception:
                pass

        self.serial_connection = None
        self.status_label.setText("Status: Disconnected")

    def start_trial(self) -> None:
        if self.serial_connection is None or not self.serial_connection.is_open:
            self.status_label.setText("Status: Connect serial before starting")
            return

        self.trial_id += 1
        self.phase = "Baseline"
        self.phase_start_time = time.time()
        self.trial_start_time = self.phase_start_time
        self.plot_start_time = self.phase_start_time
        self.last_spo2_update_time = 0.0

        self.progress.setValue(0)
        self.status_label.setText("Status: Baseline recording started")

    def start_apnea(self) -> None:
        if self.phase == "Apnea":
            self.status_label.setText("Status: Apnea is already running")
            return

        if self.trial_id == 0:
            self.start_trial()

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

    def read_serial_data(self) -> None:
        if (
            not self.streaming
            or self.serial_connection is None
            or not self.serial_connection.is_open
        ):
            return

        for _ in range(SERIAL_LINES_PER_TICK):
            try:
                line = self.serial_connection.readline().decode(
                    "utf-8", errors="ignore"
                )
            except Exception as exc:
                self.streaming = False
                self.status_label.setText(f"Status: Serial read error: {exc}")
                return

            parsed = parse_red_ir(line)

            if parsed is None:
                continue

            red_raw, ir_raw = parsed
            now = time.time()

            red_corrected = red_raw - SERIAL_VALUE_OFFSET
            ir_corrected = ir_raw - SERIAL_VALUE_OFFSET
            if SERIAL_STREAM_IS_NEGATED:
                red_corrected = -red_corrected
                ir_corrected = -ir_corrected

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

        if len(self.red_raw_buffer) < window_samples:
            return

        red_window = np.array(self.red_raw_buffer, dtype=float)[-window_samples:]
        ir_window = np.array(self.ir_raw_buffer, dtype=float)[-window_samples:]

        spo2, ratio = estimate_spo2(red_window, ir_window)

        self.last_spo2_update_time = now
        self.current_spo2 = spo2
        self.current_ratio = ratio

        if np.isnan(spo2):
            self.spo2_label.setText("SpO2: invalid DC")
        else:
            self.spo2_label.setText(f"SpO2: {spo2:0.1f}%")

    def update_loop(self) -> None:
        self.read_serial_data()
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

        default_name = f"spo2_voluntary_apnea_dataset_{int(time.time())}.csv"

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
        self.disconnect_serial()
        event.accept()


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyleSheet(APPLE_STYLE)

    win = ApneaCollectionWindow()
    win.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()