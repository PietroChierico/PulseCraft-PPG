# Copyright (c) 2026 Pietro Chierico
# SPDX-License-Identifier: MIT

"""
Script 1 - PPG Mental Stress Dataset Collection Protocol (Arduino Serial)

Purpose
-------
Collect labeled IR PPG feature rows for Project 5: Mental Stress Detection.
The protocol compares relaxed physiology with several time-pressure cognitive
stressors:

    20 s Sensor Stabilization            -> not saved
    60 s Relaxed Baseline Recording      -> saved as target Relaxed
    60 s Mental Arithmetic Stress Task   -> saved as target Stressed
    30 s Quiet Recovery                  -> not saved
    60 s Timed Reaction Stress Task      -> saved as target Stressed
    60 s Cognitive Interference Task     -> saved as target Stressed
    60 s Final Calm Recording            -> saved as target Relaxed

Every 10-second serial PPG window is converted into waveform, pulse, and HRV
features and appended to memory. Students can repeat the full protocol as
Record 1, Record 2, ... and export all rows to CSV.

Input
-----
Arduino sends one PPG/IR value per line through the USB serial port.
Accepted Serial Monitor formats include:
    90234
    ir=90234
    12345,90234
    12345,80123,90234

Close the Arduino IDE Serial Monitor before connecting from Python, because the
COM port usually cannot be shared by two programs.

Install
-------
pip install pyserial numpy scipy pyqtgraph PyQt6

Run
---
python script1_stress_dataset_collection.py
"""
from __future__ import annotations

import csv
import random
import sys
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)
import pyqtgraph as pg

from ppg_serial_ir_stream import ArduinoSerialPPGReader, list_serial_ports, parse_serial_ppg_value
from ppg_stress_features import FEATURE_COLUMNS, compute_ppg_features


@dataclass(frozen=True)
class PPGConfig:
    baudrate: int = 115200
    sampling_rate_hz: float = 100.0
    serial_timeout_s: float = 0.02
    serial_lines_per_tick: int = 50
    max_samples: int = 100 * 240
    window_seconds: int = 10


@dataclass(frozen=True)
class ProtocolPhase:
    name: str
    duration_s: int
    target: Optional[str]
    task_code: str
    instruction: str


CONFIG = PPGConfig()

PROTOCOL = [
    ProtocolPhase(
        name="Sensor Stabilization",
        duration_s=20,
        target=None,
        task_code="stabilization",
        instruction="Sit still, keep the finger steady, and let the PPG signal stabilize.",
    ),
    ProtocolPhase(
        name="Relaxed Baseline Recording",
        duration_s=60,
        target="Relaxed",
        task_code="relaxed_baseline",
        instruction="Relax your shoulders, breathe normally, and avoid speaking or moving.",
    ),
    ProtocolPhase(
        name="Mental Arithmetic Stress Task",
        duration_s=60,
        target="Stressed",
        task_code="mental_arithmetic",
        instruction="Solve the arithmetic prompts mentally as quickly as possible.",
    ),
    ProtocolPhase(
        name="Quiet Recovery",
        duration_s=30,
        target=None,
        task_code="recovery",
        instruction="Stop the task, sit quietly, and let the body recover.",
    ),
    ProtocolPhase(
        name="Timed Reaction Stress Task",
        duration_s=60,
        target="Stressed",
        task_code="timed_reaction",
        instruction="Press the Reaction Tap button only when the screen says GO.",
    ),
    ProtocolPhase(
        name="Cognitive Interference Challenge",
        duration_s=60,
        target="Stressed",
        task_code="cognitive_interference",
        instruction="Say the ink color, not the written word. Keep responding quickly.",
    ),
    ProtocolPhase(
        name="Final Calm Recording",
        duration_s=60,
        target="Relaxed",
        task_code="final_calm",
        instruction="Return to a calm state. Breathe normally and keep the finger still.",
    ),
]

CSV_COLUMNS = [
    "recording_id",
    "timestamp_s",
    "sample_index",
    "serial_port",
    "baudrate",
    "sampling_rate_hz",
    "protocol_phase",
    "task_code",
    "target",
    "window_seconds",
    "challenge_prompt",
    "reaction_hits",
    "reaction_misses",
    "reaction_false_starts",
    "last_reaction_ms",
    *FEATURE_COLUMNS,
]

APPLE_STYLE = """
QMainWindow, QWidget { background-color: #070b13; color: #f5f7fb; font-family: -apple-system, BlinkMacSystemFont, Segoe UI; }
QLabel { color: #f5f7fb; font-size: 14px; }
QPushButton { background-color: rgba(255,255,255,0.10); border: 1px solid rgba(255,255,255,0.18); border-radius: 15px; padding: 11px 16px; color: #f5f7fb; font-weight: 700; }
QPushButton:hover { background-color: rgba(255,255,255,0.18); }
QPushButton:pressed { background-color: rgba(255,255,255,0.26); }
QComboBox, QSpinBox { background-color: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.20); border-radius: 13px; padding: 8px; color: #f5f7fb; }
QProgressBar { border: 1px solid rgba(255,255,255,0.20); border-radius: 11px; text-align: center; background-color: rgba(255,255,255,0.08); color: white; }
QProgressBar::chunk { border-radius: 11px; background-color: #ff4d6d; }
"""

COLOR_WORDS = [
    ("RED", "#ff4d6d"),
    ("BLUE", "#35d7ff"),
    ("GREEN", "#36d399"),
    ("YELLOW", "#facc15"),
    ("PURPLE", "#a78bfa"),
    ("ORANGE", "#fb923c"),
]


class MentalStressDatasetCollectionWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Project 5 - PPG Mental Stress Dataset Collection - Arduino Serial")
        self.resize(1280, 900)

        self.serial_reader: Optional[ArduinoSerialPPGReader] = None
        self.streaming = False
        self.protocol_running = False
        self.recording_id = 0
        self.phase_index = 0
        self.phase_start_time = 0.0
        self.sample_index = 0
        self.last_feature_sample_index = 0
        self.rows: list[dict[str, float | int | str]] = []
        self.ir_buffer = deque(maxlen=CONFIG.max_samples)

        self.challenge_prompt = "Waiting for protocol."
        self.next_prompt_time = 0.0
        self.reaction_active = False
        self.reaction_stimulus_time = 0.0
        self.next_reaction_time = 0.0
        self.reaction_hits = 0
        self.reaction_misses = 0
        self.reaction_false_starts = 0
        self.last_reaction_ms: Optional[float] = None

        self._build_ui()
        self._build_timer()
        self.refresh_ports()

    def _build_ui(self) -> None:
        pg.setConfigOptions(antialias=True, background="#070b13", foreground="#f5f7fb")
        central = QWidget()
        layout = QVBoxLayout(central)
        top = QGridLayout()

        self.port_combo = QComboBox()
        self.refresh_button = QPushButton("Refresh Ports")
        self.connect_button = QPushButton("Connect Serial")
        self.disconnect_button = QPushButton("Disconnect")
        self.start_protocol_button = QPushButton("Start New Stress Recording")
        self.stop_protocol_button = QPushButton("Stop Protocol")
        self.export_button = QPushButton("Export Data")
        self.clear_button = QPushButton("Clear Rows")
        self.reaction_button = QPushButton("Reaction Tap")

        self.baudrate_spin = QSpinBox()
        self.baudrate_spin.setRange(9600, 1000000)
        self.baudrate_spin.setValue(CONFIG.baudrate)
        self.baudrate_spin.setSingleStep(9600)

        self.sampling_rate_spin = QSpinBox()
        self.sampling_rate_spin.setRange(10, 250)
        self.sampling_rate_spin.setValue(int(CONFIG.sampling_rate_hz))
        self.sampling_rate_spin.setSingleStep(5)

        top.addWidget(QLabel("Arduino Serial / COM Port"), 0, 0)
        top.addWidget(self.port_combo, 0, 1)
        top.addWidget(self.refresh_button, 0, 2)
        top.addWidget(QLabel("Baudrate"), 1, 0)
        top.addWidget(self.baudrate_spin, 1, 1)
        top.addWidget(QLabel("Sampling Rate (Hz)"), 1, 2)
        top.addWidget(self.sampling_rate_spin, 1, 3)

        buttons = QHBoxLayout()
        for button in [
            self.connect_button,
            self.disconnect_button,
            self.start_protocol_button,
            self.stop_protocol_button,
            self.export_button,
            self.clear_button,
            self.reaction_button,
        ]:
            buttons.addWidget(button)

        self.title_label = QLabel("Record 0 - Waiting for Mental Stress Protocol")
        self.title_label.setStyleSheet("font-size: 31px; font-weight: 900;")
        self.subtitle_label = QLabel(
            "Serial input: Arduino USB COM port -> relaxed baseline -> mental arithmetic -> reaction task -> cognitive challenge -> final calm recording"
        )
        self.subtitle_label.setStyleSheet("font-size: 16px; color: #b7c2d8;")
        self.phase_label = QLabel("Phase: --")
        self.phase_label.setStyleSheet("font-size: 23px; font-weight: 800;")
        self.time_label = QLabel("Time remaining: --")
        self.rows_label = QLabel("Feature rows: 0")
        self.status_label = QLabel("Status: Select a COM port and connect")
        self.challenge_label = QLabel("Challenge: waiting")
        self.challenge_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.challenge_label.setWordWrap(True)
        self.challenge_label.setStyleSheet(
            "font-size: 30px; font-weight: 900; background-color: rgba(255,77,109,0.12); "
            "border-radius: 24px; padding: 24px;"
        )
        self.reaction_label = QLabel("Reaction metrics: hits 0 - misses 0 - false starts 0 - last -- ms")
        self.reaction_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.reaction_label.setStyleSheet(
            "font-size: 16px; font-weight: 700; background-color: rgba(255,255,255,0.075); "
            "border-radius: 18px; padding: 14px;"
        )
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)

        cards = QHBoxLayout()
        for label in [self.phase_label, self.time_label, self.rows_label, self.status_label]:
            label.setStyleSheet(
                label.styleSheet()
                + " background-color: rgba(255,255,255,0.075); border-radius: 19px; padding: 16px;"
            )
            cards.addWidget(label)

        self.plot = pg.PlotWidget(title="Raw PPG Streaming from Arduino Serial")
        self.plot.setLabel("left", "PPG / IR value")
        self.plot.setLabel("bottom", "Time", units="s")
        self.plot.showGrid(x=True, y=True, alpha=0.25)
        self.curve = self.plot.plot([], [], pen=pg.mkPen("#ff4d6d", width=2), skipFiniteCheck=True)

        layout.addWidget(self.title_label)
        layout.addWidget(self.subtitle_label)
        layout.addLayout(top)
        layout.addLayout(buttons)
        layout.addWidget(self.challenge_label)
        layout.addWidget(self.reaction_label)
        layout.addLayout(cards)
        layout.addWidget(self.progress)
        layout.addWidget(self.plot)
        self.setCentralWidget(central)

        self.refresh_button.clicked.connect(self.refresh_ports)
        self.connect_button.clicked.connect(self.connect_serial)
        self.disconnect_button.clicked.connect(self.disconnect_serial)
        self.start_protocol_button.clicked.connect(self.start_protocol)
        self.stop_protocol_button.clicked.connect(self.stop_protocol)
        self.export_button.clicked.connect(self.export_data)
        self.clear_button.clicked.connect(self.clear_rows)
        self.reaction_button.clicked.connect(self.handle_reaction_tap)

    def _build_timer(self) -> None:
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_loop)
        self.timer.start(30)

    def sampling_rate_hz(self) -> float:
        return float(self.sampling_rate_spin.value())

    def refresh_ports(self) -> None:
        current = self.port_combo.currentText().strip()
        ports = list_serial_ports()
        self.port_combo.clear()
        self.port_combo.addItems(ports)
        if current and current in ports:
            self.port_combo.setCurrentText(current)
        if ports:
            self.status_label.setText(f"Status: found {len(ports)} serial port(s)")
        else:
            self.status_label.setText("Status: no COM ports found. Connect Arduino and press Refresh Ports.")

    def connect_serial(self) -> None:
        self.disconnect_serial(update_status=False)
        port = self.port_combo.currentText().strip()
        if not port:
            self.status_label.setText("Status: select an Arduino COM port first")
            return
        try:
            self.serial_reader = ArduinoSerialPPGReader(
                port=port,
                baudrate=int(self.baudrate_spin.value()),
                timeout_s=CONFIG.serial_timeout_s,
            )
            self.streaming = True
            self.status_label.setText(f"Status: connected to {port} at {int(self.baudrate_spin.value())} baud")
        except Exception as exc:
            self.serial_reader = None
            self.streaming = False
            self.status_label.setText(f"Status: serial connection failed: {exc}")

    def disconnect_serial(self, update_status: bool = True) -> None:
        self.streaming = False
        self.protocol_running = False
        if self.serial_reader is not None:
            try:
                self.serial_reader.close()
            except Exception:
                pass
        self.serial_reader = None
        if update_status:
            self.status_label.setText("Status: disconnected")

    def reset_challenge_state(self) -> None:
        self.challenge_prompt = "Waiting for protocol."
        self.next_prompt_time = 0.0
        self.reaction_active = False
        self.reaction_stimulus_time = 0.0
        self.next_reaction_time = 0.0
        self.reaction_hits = 0
        self.reaction_misses = 0
        self.reaction_false_starts = 0
        self.last_reaction_ms = None
        self.update_reaction_label()

    def start_protocol(self) -> None:
        if self.serial_reader is None or not self.serial_reader.connected:
            self.status_label.setText("Status: connect the Arduino serial port before starting")
            return
        self.recording_id += 1
        self.phase_index = 0
        self.phase_start_time = time.time()
        self.last_feature_sample_index = self.sample_index
        self.protocol_running = True
        self.reset_challenge_state()
        self.prepare_current_phase()
        self.title_label.setText(f"Record {self.recording_id} - Mental Stress Protocol Running")
        self.status_label.setText("Status: protocol running")

    def stop_protocol(self) -> None:
        self.protocol_running = False
        self.title_label.setText(f"Record {self.recording_id} - Stopped")
        self.phase_label.setText("Phase: --")
        self.time_label.setText("Time remaining: --")
        self.progress.setValue(0)
        self.challenge_label.setText("Challenge: stopped")

    def prepare_current_phase(self) -> None:
        phase = PROTOCOL[self.phase_index]
        now = time.time()
        self.challenge_prompt = phase.instruction
        self.next_prompt_time = now
        self.reaction_active = False
        self.next_reaction_time = now + random.uniform(1.2, 3.0)
        self.update_challenge_label(phase.instruction)

    def read_serial_data(self) -> None:
        if not self.streaming or self.serial_reader is None or not self.serial_reader.connected:
            return
        try:
            lines = self.serial_reader.read_lines(CONFIG.serial_lines_per_tick)
        except Exception as exc:
            self.streaming = False
            self.protocol_running = False
            self.status_label.setText(f"Status: serial read error: {exc}")
            return
        for line in lines:
            value = parse_serial_ppg_value(line)
            if value is not None:
                self.ir_buffer.append(value)
                self.sample_index += 1

    def update_loop(self) -> None:
        self.read_serial_data()
        self.update_plot()
        if self.protocol_running:
            self.update_protocol()

    def update_plot(self) -> None:
        if len(self.ir_buffer) < 2:
            return
        fs = self.sampling_rate_hz()
        visible_samples = int(10 * fs)
        ir = np.array(self.ir_buffer, dtype=float)[-visible_samples:]
        x = np.arange(len(ir), dtype=float) / fs
        x = x - x[-1]
        self.curve.setData(x, ir)
        self.plot.setXRange(-10, 0, padding=0)

    def update_protocol(self) -> None:
        phase = PROTOCOL[self.phase_index]
        elapsed = time.time() - self.phase_start_time
        remaining = max(0.0, phase.duration_s - elapsed)
        save_text = f" - Target {phase.target}" if phase.target else " - Not saved"
        self.phase_label.setText(f"Phase: {phase.name}{save_text}")
        self.time_label.setText(f"Time remaining: {remaining:0.1f} s")
        self.progress.setValue(int(100 * min(elapsed / phase.duration_s, 1.0)))

        self.update_task_prompt(phase)

        if phase.target is not None:
            self.maybe_append_feature_row(phase)

        if elapsed >= phase.duration_s:
            self.phase_index += 1
            if self.phase_index >= len(PROTOCOL):
                self.protocol_running = False
                self.title_label.setText(f"Record {self.recording_id} - Complete")
                self.phase_label.setText("Phase: Complete")
                self.time_label.setText("Time remaining: 0.0 s")
                self.progress.setValue(100)
                self.challenge_label.setText("Challenge: protocol complete")
                self.status_label.setText("Status: recording complete. Start another recording or export data.")
            else:
                self.phase_start_time = time.time()
                self.last_feature_sample_index = self.sample_index
                self.prepare_current_phase()

    def update_task_prompt(self, phase: ProtocolPhase) -> None:
        now = time.time()
        if phase.task_code == "mental_arithmetic":
            if now >= self.next_prompt_time:
                self.challenge_prompt = self.generate_arithmetic_prompt()
                self.next_prompt_time = now + 6.0
                self.update_challenge_label(self.challenge_prompt)
            return

        if phase.task_code == "timed_reaction":
            self.update_reaction_task(now)
            return

        if phase.task_code == "cognitive_interference":
            if now >= self.next_prompt_time:
                prompt, color = self.generate_cognitive_prompt()
                self.challenge_prompt = prompt
                self.next_prompt_time = now + 4.0
                self.update_challenge_label(prompt, accent_color=color)
            return

        self.challenge_prompt = phase.instruction
        self.update_challenge_label(phase.instruction)

    def generate_arithmetic_prompt(self) -> str:
        start = random.randint(80, 250)
        step = random.choice([7, 9, 13, 17])
        count = random.randint(2, 4)
        expression = str(start)
        for _ in range(count):
            if random.random() < 0.75:
                expression += f" - {step}"
            else:
                expression += f" + {random.randint(3, 18)}"
        return f"Mental arithmetic: {expression} = ?"

    def generate_cognitive_prompt(self) -> tuple[str, str]:
        written_word, _ = random.choice(COLOR_WORDS)
        ink_name, ink_color = random.choice(COLOR_WORDS)
        while ink_name == written_word:
            ink_name, ink_color = random.choice(COLOR_WORDS)
        prompt = f"Say the INK color, not the word: {written_word}"
        return prompt, ink_color

    def update_reaction_task(self, now: float) -> None:
        if self.reaction_active:
            if now - self.reaction_stimulus_time > 1.2:
                self.reaction_misses += 1
                self.reaction_active = False
                self.next_reaction_time = now + random.uniform(1.0, 2.8)
                self.challenge_prompt = "Missed stimulus. Wait for the next GO."
                self.update_challenge_label(self.challenge_prompt, accent_color="#fb923c")
                self.update_reaction_label()
            return

        if now >= self.next_reaction_time:
            self.reaction_active = True
            self.reaction_stimulus_time = now
            self.challenge_prompt = "GO! Press Reaction Tap now."
            self.update_challenge_label(self.challenge_prompt, accent_color="#36d399")
        else:
            self.challenge_prompt = "Reaction task: wait... press only when GO appears."
            self.update_challenge_label(self.challenge_prompt)

    def handle_reaction_tap(self) -> None:
        if not self.protocol_running:
            return
        phase = PROTOCOL[self.phase_index]
        if phase.task_code != "timed_reaction":
            self.status_label.setText("Status: Reaction Tap is only used during the reaction task")
            return

        now = time.time()
        if self.reaction_active:
            self.last_reaction_ms = (now - self.reaction_stimulus_time) * 1000.0
            self.reaction_hits += 1
            self.reaction_active = False
            self.next_reaction_time = now + random.uniform(1.0, 2.8)
            self.challenge_prompt = f"Hit: {self.last_reaction_ms:0.0f} ms. Wait for the next GO."
            self.update_challenge_label(self.challenge_prompt, accent_color="#35d7ff")
        else:
            self.reaction_false_starts += 1
            self.challenge_prompt = "False start. Wait for GO before pressing."
            self.update_challenge_label(self.challenge_prompt, accent_color="#ff4d6d")
        self.update_reaction_label()

    def update_challenge_label(self, text: str, accent_color: str = "#ff4d6d") -> None:
        self.challenge_label.setText(f"Challenge: {text}")
        self.challenge_label.setStyleSheet(
            f"font-size: 30px; font-weight: 900; background-color: rgba(255,255,255,0.08); "
            f"border: 2px solid {accent_color}; border-radius: 24px; padding: 24px; color: {accent_color};"
        )

    def update_reaction_label(self) -> None:
        last_text = "--" if self.last_reaction_ms is None else f"{self.last_reaction_ms:0.0f}"
        self.reaction_label.setText(
            f"Reaction metrics: hits {self.reaction_hits} - misses {self.reaction_misses} - "
            f"false starts {self.reaction_false_starts} - last {last_text} ms"
        )

    def maybe_append_feature_row(self, phase: ProtocolPhase) -> None:
        fs = self.sampling_rate_hz()
        window_samples = int(CONFIG.window_seconds * fs)
        if len(self.ir_buffer) < window_samples:
            return
        if self.sample_index - self.last_feature_sample_index < window_samples:
            return
        ir_window = np.array(self.ir_buffer, dtype=float)[-window_samples:]
        features = compute_ppg_features(ir_window, fs)
        row: dict[str, float | int | str] = {
            "recording_id": self.recording_id,
            "timestamp_s": time.time(),
            "sample_index": self.sample_index,
            "serial_port": self.port_combo.currentText().strip(),
            "baudrate": int(self.baudrate_spin.value()),
            "sampling_rate_hz": fs,
            "protocol_phase": phase.name,
            "task_code": phase.task_code,
            "target": phase.target or "",
            "window_seconds": CONFIG.window_seconds,
            "challenge_prompt": self.challenge_prompt,
            "reaction_hits": self.reaction_hits,
            "reaction_misses": self.reaction_misses,
            "reaction_false_starts": self.reaction_false_starts,
            "last_reaction_ms": 0.0 if self.last_reaction_ms is None else float(self.last_reaction_ms),
        }
        row.update(features)
        self.rows.append(row)
        self.last_feature_sample_index = self.sample_index
        self.rows_label.setText(f"Feature rows: {len(self.rows)}")
        self.status_label.setText(f"Status: saved {phase.target} row from {phase.name}")

    def export_data(self) -> None:
        if not self.rows:
            QMessageBox.information(self, "No rows", "No feature rows have been collected yet.")
            return
        default_name = f"ppg_mental_stress_serial_dataset_{int(time.time())}.csv"
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Mental Stress Dataset CSV",
            str(Path.home() / default_name),
            "CSV files (*.csv)",
        )
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=CSV_COLUMNS)
                writer.writeheader()
                for row in self.rows:
                    writer.writerow({column: row.get(column, "") for column in CSV_COLUMNS})
            self.status_label.setText(f"Status: exported {len(self.rows)} rows to {Path(path).name}")
        except Exception as exc:
            QMessageBox.critical(self, "Export error", f"Could not export CSV:\n{exc}")

    def clear_rows(self) -> None:
        self.rows.clear()
        self.rows_label.setText("Feature rows: 0")
        self.status_label.setText("Status: rows cleared")

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt naming convention
        self.disconnect_serial(update_status=False)
        event.accept()


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyleSheet(APPLE_STYLE)
    window = MentalStressDatasetCollectionWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
