# Copyright (c) 2026 Pietro Chierico
# SPDX-License-Identifier: MIT

"""
Script 3 - Live PPG Mental Stress Detection Challenge

Purpose
-------
Load the trained model exported by Script 2, stream live IR PPG data over WiFi,
compute the same 10-second PPG and HRV features, and display a stress score
from 0 to 100.

The optional live challenge cycles through calm monitoring, mental arithmetic,
a timed reaction task, and recovery tracking so students can watch the score
change in real time.

Input
-----
The ESP32 sends IR PPG data over WiFi TCP.
Default AP mode endpoint: 192.168.4.1 port 3333.
The parser accepts one IR value per line, millis,ir, or millis,red,ir.

Install
-------
pip install numpy scipy pyqtgraph PyQt6 joblib scikit-learn

Run
---
python script3_stress_live_detection_challenge.py
"""
from __future__ import annotations

import random
import sys
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import joblib
import numpy as np

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QProgressBar,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)
import pyqtgraph as pg

from ppg_stress_features import compute_ppg_features
from ppg_wifi_ir_stream import WiFiPPGClient, parse_ir_value


@dataclass(frozen=True)
class PPGConfig:
    tcp_host: str = "192.168.4.1"
    tcp_port: int = 3333
    tcp_connect_timeout_s: float = 5.0
    sampling_rate_hz: float = 100.0
    tcp_lines_per_tick: int = 60
    max_samples: int = 100 * 240
    window_seconds: int = 10


@dataclass(frozen=True)
class ChallengePhase:
    name: str
    duration_s: int
    task_code: str
    instruction: str


CONFIG = PPGConfig()

LIVE_CHALLENGE = [
    ChallengePhase(
        name="Calm Monitoring",
        duration_s=30,
        task_code="calm",
        instruction="Stay still, breathe normally, and let the first stress score stabilize.",
    ),
    ChallengePhase(
        name="Mental Arithmetic Burst",
        duration_s=60,
        task_code="mental_arithmetic",
        instruction="Solve each arithmetic prompt quickly without speaking.",
    ),
    ChallengePhase(
        name="Timed Reaction Burst",
        duration_s=45,
        task_code="timed_reaction",
        instruction="Press Reaction Tap only when GO appears.",
    ),
    ChallengePhase(
        name="Recovery Tracking",
        duration_s=45,
        task_code="recovery",
        instruction="Stop the stress task and watch whether the score returns toward relaxed values.",
    ),
]

APPLE_STYLE = """
QMainWindow, QWidget { background-color: #070b13; color: #f5f7fb; font-family: -apple-system, BlinkMacSystemFont, Segoe UI; }
QLabel { color: #f5f7fb; font-size: 14px; }
QPushButton { background-color: rgba(255,255,255,0.10); border: 1px solid rgba(255,255,255,0.18); border-radius: 15px; padding: 11px 16px; color: #f5f7fb; font-weight: 700; }
QPushButton:hover { background-color: rgba(255,255,255,0.18); }
QPushButton:pressed { background-color: rgba(255,255,255,0.26); }
QLineEdit, QSpinBox { background-color: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.20); border-radius: 13px; padding: 8px; color: #f5f7fb; }
QProgressBar { border: 1px solid rgba(255,255,255,0.20); border-radius: 11px; text-align: center; background-color: rgba(255,255,255,0.08); color: white; font-weight: 800; }
QProgressBar::chunk { border-radius: 11px; background-color: #ff4d6d; }
"""


class MentalStressLiveChallengeWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Project 5 - Live PPG Mental Stress Detection")
        self.resize(1280, 920)

        self.tcp_client: Optional[WiFiPPGClient] = None
        self.streaming = False
        self.model_bundle: dict | None = None
        self.sample_index = 0
        self.last_prediction_sample_index = 0
        self.ir_buffer = deque(maxlen=CONFIG.max_samples)
        self.score_history = deque(maxlen=140)

        self.challenge_running = False
        self.challenge_phase_index = 0
        self.challenge_phase_start_time = 0.0
        self.next_prompt_time = 0.0
        self.challenge_prompt = "Load a model, connect the sensor, and start the challenge."
        self.reaction_active = False
        self.reaction_stimulus_time = 0.0
        self.next_reaction_time = 0.0
        self.reaction_hits = 0
        self.reaction_misses = 0
        self.reaction_false_starts = 0
        self.last_reaction_ms: Optional[float] = None

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
        self.load_model_button = QPushButton("Load Model")
        self.start_challenge_button = QPushButton("Start Live Challenge")
        self.reset_button = QPushButton("Reset")
        self.reaction_button = QPushButton("Reaction Tap")

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
        for button in [
            self.connect_button,
            self.disconnect_button,
            self.load_model_button,
            self.start_challenge_button,
            self.reset_button,
            self.reaction_button,
        ]:
            buttons.addWidget(button)

        self.title_label = QLabel("Live Mental Stress Detection Challenge")
        self.title_label.setStyleSheet("font-size: 32px; font-weight: 900;")
        self.score_label = QLabel("Stress Score: -- / 100")
        self.score_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.score_label.setStyleSheet(
            "font-size: 42px; font-weight: 950; background-color: rgba(255,77,109,0.12); "
            "border-radius: 26px; padding: 24px;"
        )
        self.state_label = QLabel("State: load model and connect sensor")
        self.state_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.state_label.setStyleSheet(
            "font-size: 22px; font-weight: 800; background-color: rgba(255,255,255,0.075); "
            "border-radius: 22px; padding: 18px;"
        )
        self.challenge_label = QLabel(f"Challenge: {self.challenge_prompt}")
        self.challenge_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.challenge_label.setWordWrap(True)
        self.challenge_label.setStyleSheet(
            "font-size: 24px; font-weight: 850; background-color: rgba(255,255,255,0.075); "
            "border-radius: 22px; padding: 18px;"
        )
        self.reaction_label = QLabel("Reaction metrics: hits 0 · misses 0 · false starts 0 · last -- ms")
        self.reaction_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.reaction_label.setStyleSheet(
            "font-size: 15px; font-weight: 700; background-color: rgba(255,255,255,0.075); "
            "border-radius: 18px; padding: 12px;"
        )
        self.status_label = QLabel("Status: Waiting")
        self.model_label = QLabel("Model: not loaded")
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)

        cards = QHBoxLayout()
        for label in [self.status_label, self.model_label]:
            label.setStyleSheet("background-color: rgba(255,255,255,0.075); border-radius: 19px; padding: 16px;")
            cards.addWidget(label)

        self.raw_plot = pg.PlotWidget(title="Raw IR PPG Streaming")
        self.raw_plot.setLabel("left", "IR value")
        self.raw_plot.setLabel("bottom", "Time", units="s")
        self.raw_plot.showGrid(x=True, y=True, alpha=0.25)
        self.raw_curve = self.raw_plot.plot([], [], pen=pg.mkPen("#35d7ff", width=2), skipFiniteCheck=True)

        self.score_plot = pg.PlotWidget(title="Mental Stress Score History")
        self.score_plot.setLabel("left", "Stress score")
        self.score_plot.setLabel("bottom", "Prediction window")
        self.score_plot.setYRange(0, 100)
        self.score_plot.showGrid(x=True, y=True, alpha=0.25)
        self.score_curve = self.score_plot.plot([], [], pen=pg.mkPen("#ff4d6d", width=3), skipFiniteCheck=True)

        layout.addWidget(self.title_label)
        layout.addLayout(top)
        layout.addLayout(buttons)
        layout.addWidget(self.score_label)
        layout.addWidget(self.state_label)
        layout.addWidget(self.challenge_label)
        layout.addWidget(self.reaction_label)
        layout.addWidget(self.progress)
        layout.addLayout(cards)
        layout.addWidget(self.raw_plot)
        layout.addWidget(self.score_plot)
        self.setCentralWidget(central)

        self.default_ip_button.clicked.connect(self.use_access_point_ip)
        self.connect_button.clicked.connect(self.connect_wifi)
        self.disconnect_button.clicked.connect(self.disconnect_wifi)
        self.load_model_button.clicked.connect(self.load_model)
        self.start_challenge_button.clicked.connect(self.start_challenge)
        self.reset_button.clicked.connect(self.reset_game)
        self.reaction_button.clicked.connect(self.handle_reaction_tap)

    def _build_timer(self) -> None:
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_loop)
        self.timer.start(30)

    def use_access_point_ip(self) -> None:
        self.host_edit.setText(CONFIG.tcp_host)
        self.tcp_port_spin.setValue(CONFIG.tcp_port)

    def load_model(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Load Mental Stress Model", str(Path.home()), "Joblib files (*.joblib)")
        if not path:
            return
        try:
            bundle = joblib.load(path)
            if "pipeline" not in bundle or "features" not in bundle:
                raise ValueError("Invalid model file. Expected keys: pipeline and features.")
            self.model_bundle = bundle
            self.model_label.setText(f"Model: {Path(path).name}")
            self.status_label.setText("Status: Model loaded")
        except Exception as exc:
            self.model_bundle = None
            self.model_label.setText("Model: load failed")
            self.status_label.setText(f"Status: Model error: {exc}")

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
        self.challenge_running = False
        if self.tcp_client is not None:
            try:
                self.tcp_client.close()
            except Exception:
                pass
        self.tcp_client = None
        if update_status:
            self.status_label.setText("Status: Disconnected")

    def start_challenge(self) -> None:
        if self.model_bundle is None:
            self.status_label.setText("Status: Load a trained model before starting the challenge")
            return
        if self.tcp_client is None or not self.tcp_client.connected:
            self.status_label.setText("Status: Connect WiFi before starting the challenge")
            return
        self.challenge_running = True
        self.challenge_phase_index = 0
        self.challenge_phase_start_time = time.time()
        self.next_prompt_time = 0.0
        self.reaction_active = False
        self.next_reaction_time = time.time() + random.uniform(1.2, 3.0)
        self.reaction_hits = 0
        self.reaction_misses = 0
        self.reaction_false_starts = 0
        self.last_reaction_ms = None
        self.status_label.setText("Status: Live challenge running")
        self.update_reaction_label()

    def reset_game(self) -> None:
        self.score_history.clear()
        self.progress.setValue(0)
        self.score_label.setText("Stress Score: -- / 100")
        self.state_label.setText("State: game reset")
        self.challenge_running = False
        self.challenge_prompt = "Load a model, connect the sensor, and start the challenge."
        self.challenge_label.setText(f"Challenge: {self.challenge_prompt}")
        self.reaction_hits = 0
        self.reaction_misses = 0
        self.reaction_false_starts = 0
        self.last_reaction_ms = None
        self.update_reaction_label()
        self.update_score_plot()

    def read_wifi_data(self) -> None:
        if not self.streaming or self.tcp_client is None or not self.tcp_client.connected:
            return
        try:
            lines = self.tcp_client.read_lines(CONFIG.tcp_lines_per_tick)
        except Exception as exc:
            self.streaming = False
            self.challenge_running = False
            self.status_label.setText(f"Status: WiFi TCP read error: {exc}")
            return
        for line in lines:
            value = parse_ir_value(line)
            if value is not None:
                self.ir_buffer.append(value)
                self.sample_index += 1

    def update_loop(self) -> None:
        self.read_wifi_data()
        self.update_raw_plot()
        self.maybe_predict()
        if self.challenge_running:
            self.update_challenge()

    def update_raw_plot(self) -> None:
        if len(self.ir_buffer) < 2:
            return
        visible_samples = int(10 * CONFIG.sampling_rate_hz)
        ir = np.array(self.ir_buffer, dtype=float)[-visible_samples:]
        x = np.arange(len(ir), dtype=float) / CONFIG.sampling_rate_hz
        x = x - x[-1]
        self.raw_curve.setData(x, ir)
        self.raw_plot.setXRange(-10, 0, padding=0)

    def maybe_predict(self) -> None:
        if self.model_bundle is None:
            return
        window_samples = int(CONFIG.window_seconds * CONFIG.sampling_rate_hz)
        if len(self.ir_buffer) < window_samples:
            percent = int(100 * len(self.ir_buffer) / window_samples)
            self.progress.setValue(percent)
            self.state_label.setText("State: collecting enough signal for first stress score")
            return
        if self.sample_index - self.last_prediction_sample_index < window_samples:
            return

        ir_window = np.array(self.ir_buffer, dtype=float)[-window_samples:]
        features = compute_ppg_features(ir_window, CONFIG.sampling_rate_hz)
        feature_names = list(self.model_bundle["features"])
        row = np.array([[features.get(name, 0.0) for name in feature_names]], dtype=float)
        pipeline = self.model_bundle["pipeline"]

        try:
            score = float(pipeline.predict_proba(row)[0, 1] * 100.0)
        except Exception:
            try:
                score = float(pipeline.predict(row)[0] * 100.0)
            except Exception as exc:
                self.status_label.setText(f"Status: prediction error: {exc}")
                return

        score = max(0.0, min(100.0, score))
        self.score_history.append(score)
        self.last_prediction_sample_index = self.sample_index
        self.progress.setValue(int(score))
        self.score_label.setText(f"Stress Score: {score:0.1f} / 100")

        if score >= 65:
            state_text = "State: likely stressed"
        elif score <= 35:
            state_text = "State: likely relaxed"
        else:
            state_text = "State: mixed / transition"
        self.state_label.setText(state_text)
        self.status_label.setText("Status: live stress score updated")
        self.update_score_plot()

    def update_score_plot(self) -> None:
        if not self.score_history:
            self.score_curve.setData([], [])
            return
        y = np.array(self.score_history, dtype=float)
        x = np.arange(len(y), dtype=float)
        self.score_curve.setData(x, y)
        self.score_plot.setYRange(0, 100)

    def update_challenge(self) -> None:
        phase = LIVE_CHALLENGE[self.challenge_phase_index]
        elapsed = time.time() - self.challenge_phase_start_time
        remaining = max(0.0, phase.duration_s - elapsed)
        self.title_label.setText(f"Live Mental Stress Detection Challenge - {phase.name} ({remaining:0.0f}s left)")

        if phase.task_code == "mental_arithmetic":
            self.update_arithmetic_prompt()
        elif phase.task_code == "timed_reaction":
            self.update_reaction_task(time.time())
        else:
            self.challenge_prompt = phase.instruction
            self.update_challenge_label(self.challenge_prompt)

        if elapsed >= phase.duration_s:
            self.challenge_phase_index += 1
            if self.challenge_phase_index >= len(LIVE_CHALLENGE):
                self.challenge_running = False
                self.title_label.setText("Live Mental Stress Detection Challenge - Complete")
                self.challenge_prompt = "Challenge complete. Review the stress score history."
                self.update_challenge_label(self.challenge_prompt, accent_color="#36d399")
                self.status_label.setText("Status: challenge complete")
            else:
                self.challenge_phase_start_time = time.time()
                self.next_prompt_time = 0.0
                self.reaction_active = False
                self.next_reaction_time = time.time() + random.uniform(1.2, 3.0)

    def update_arithmetic_prompt(self) -> None:
        now = time.time()
        if now < self.next_prompt_time:
            return
        start = random.randint(90, 260)
        step = random.choice([7, 9, 11, 13, 17])
        expression = str(start)
        for _ in range(random.randint(2, 4)):
            if random.random() < 0.8:
                expression += f" - {step}"
            else:
                expression += f" + {random.randint(3, 15)}"
        self.challenge_prompt = f"Mental arithmetic: {expression} = ?"
        self.next_prompt_time = now + 6.0
        self.update_challenge_label(self.challenge_prompt, accent_color="#ff4d6d")

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
        if not self.challenge_running:
            return
        phase = LIVE_CHALLENGE[self.challenge_phase_index]
        if phase.task_code != "timed_reaction":
            self.status_label.setText("Status: Reaction Tap is only used during the reaction phase")
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
            f"font-size: 24px; font-weight: 850; background-color: rgba(255,255,255,0.075); "
            f"border: 2px solid {accent_color}; border-radius: 22px; padding: 18px; color: {accent_color};"
        )

    def update_reaction_label(self) -> None:
        last_text = "--" if self.last_reaction_ms is None else f"{self.last_reaction_ms:0.0f}"
        self.reaction_label.setText(
            f"Reaction metrics: hits {self.reaction_hits} · misses {self.reaction_misses} · "
            f"false starts {self.reaction_false_starts} · last {last_text} ms"
        )

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt naming convention
        self.disconnect_wifi(update_status=False)
        event.accept()


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyleSheet(APPLE_STYLE)
    window = MentalStressLiveChallengeWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
