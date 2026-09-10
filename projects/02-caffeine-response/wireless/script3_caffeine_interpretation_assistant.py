# Copyright (c) 2026 Pietro Chierico
# SPDX-License-Identifier: MIT

"""
Script 3 - Caffeine Intake Interpretation Assistant

Purpose
-------
Use an Apple-style GUI to answer:
    - When does caffeine appear to kick in for each subject?
    - Which feature shows the strongest response?
    - How subjective is the caffeine response across subjects?

Input
-----
Use caffeine_baseline_changes.csv exported by Script 2 from the WiFi IR dataset.

Install
-------
pip install numpy pandas PyQt6

Run
---
python script3_caffeine_interpretation_assistant.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication, QComboBox, QFileDialog, QGridLayout, QHBoxLayout, QLabel,
    QMainWindow, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem,
    QTextEdit, QDoubleSpinBox, QVBoxLayout, QWidget
)

BASE_DIR = Path(__file__).parent.resolve()
DEFAULT_CHANGES = BASE_DIR / "caffeine_analysis_results" / "caffeine_baseline_changes.csv"

FEATURES = [
    "bpm", "dominant_bpm", "rmssd_ms", "sdnn_ms", "ppg_amplitude",
    "signal_power", "noise_power", "snr_db", "perfusion_index_proxy",
    "motion_artifact_proxy"
]

APPLE_STYLE = """
QMainWindow, QWidget {
    background-color: #0b0f17;
    color: #f5f7fb;
    font-family: -apple-system, BlinkMacSystemFont, Segoe UI;
}
QLabel { color: #f5f7fb; font-size: 14px; }
QComboBox, QDoubleSpinBox {
    background-color: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.20);
    border-radius: 12px;
    padding: 8px;
    color: #f5f7fb;
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
QPushButton#primaryButton {
    background-color: #0071e3;
    border: 1px solid #3f9bff;
}
QTextEdit, QTableWidget {
    background-color: rgba(255,255,255,0.07);
    border: 1px solid rgba(255,255,255,0.15);
    border-radius: 18px;
    color: #f5f7fb;
    gridline-color: rgba(255,255,255,0.12);
}
QHeaderView::section {
    background-color: rgba(255,255,255,0.12);
    color: white;
    border: 0px;
    padding: 8px;
}
"""


def detect_features(df: pd.DataFrame) -> list[str]:
    return [feature for feature in FEATURES if f"{feature}_percent_change" in df.columns]


def estimate_kick_in(df: pd.DataFrame, feature: str, threshold_percent: float) -> pd.DataFrame:
    percent_col = f"{feature}_percent_change"
    value_col = f"{feature}_value"
    rows = []

    for subject_id, sub in df.groupby("subject_id"):
        sub = sub.sort_values("minutes_after_coffee")
        after = sub[sub["minutes_after_coffee"] > 0].copy()
        if after.empty:
            rows.append({
                "subject_id": subject_id,
                "estimated_kick_in_min": np.nan,
                "strongest_response_min": np.nan,
                "max_abs_percent_change": np.nan,
                "direction": "not available",
                "interpretation": "No post-coffee measurements available."
            })
            continue

        after["abs_change"] = after[percent_col].abs()
        crossed = after[after["abs_change"] >= threshold_percent]
        strongest = after.loc[after["abs_change"].idxmax()]

        if crossed.empty:
            kick = np.nan
            interpretation = "Effect not detected with selected threshold."
        else:
            kick = float(crossed.iloc[0]["minutes_after_coffee"])
            interpretation = f"Detected at {kick:.0f} minutes after coffee."

        direction_value = strongest[percent_col]
        if direction_value > 0:
            direction = "increase"
        elif direction_value < 0:
            direction = "decrease"
        else:
            direction = "no change"

        rows.append({
            "subject_id": subject_id,
            "estimated_kick_in_min": kick,
            "strongest_response_min": float(strongest["minutes_after_coffee"]),
            "max_abs_percent_change": float(strongest["abs_change"]),
            "direction": direction,
            "interpretation": interpretation,
        })

    return pd.DataFrame(rows)


def score_features(df: pd.DataFrame, threshold_percent: float) -> pd.DataFrame:
    rows = []
    for feature in detect_features(df):
        result = estimate_kick_in(df, feature, threshold_percent)
        valid = result.dropna(subset=["estimated_kick_in_min"])
        detection_rate = len(valid) / len(result) * 100 if len(result) else 0
        mean_kick = valid["estimated_kick_in_min"].mean() if not valid.empty else np.nan
        std_kick = valid["estimated_kick_in_min"].std() if len(valid) > 1 else np.nan
        mean_strength = result["max_abs_percent_change"].mean()
        rows.append({
            "feature": feature,
            "detection_rate_percent": detection_rate,
            "mean_kick_in_min": mean_kick,
            "std_kick_in_min": std_kick,
            "mean_max_abs_change_percent": mean_strength,
        })
    return pd.DataFrame(rows).sort_values(["detection_rate_percent", "mean_max_abs_change_percent"], ascending=False)


def variability_sentence(results: pd.DataFrame) -> str:
    valid = results.dropna(subset=["estimated_kick_in_min"])
    if valid.empty:
        return "No subject crossed the threshold, so inter-subject variability cannot be estimated."
    if len(valid) == 1:
        return "Only one subject crossed the threshold, so variability is not reliable yet."
    std = valid["estimated_kick_in_min"].std()
    if std < 3:
        level = "low"
    elif std < 7:
        level = "moderate"
    else:
        level = "high"
    return f"Inter-subject variability is {level}: kick-in standard deviation is {std:.2f} minutes."


class InterpretationWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Caffeine Intake Interpretation Assistant")
        self.resize(1200, 820)
        self.df: pd.DataFrame | None = None
        self.results: pd.DataFrame | None = None
        self.scores: pd.DataFrame | None = None
        self._build_ui()

    def _card(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setStyleSheet("background-color: rgba(255,255,255,0.07); border-radius: 18px; padding: 16px;")
        return label

    def _build_ui(self) -> None:
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setSpacing(16)

        title = QLabel("Caffeine Intake Project · WiFi IR Interpretation Assistant")
        title.setStyleSheet("font-size: 32px; font-weight: 900; letter-spacing: -1px;")
        subtitle = QLabel("Choose a feature and threshold to estimate when coffee kicks in and how subjective the response is.")
        subtitle.setStyleSheet("font-size: 15px; color: #a9b4c7;")

        buttons = QHBoxLayout()
        self.load_button = QPushButton("Load Baseline Changes CSV")
        self.load_button.setObjectName("primaryButton")
        self.run_button = QPushButton("Run Interpretation")
        self.best_button = QPushButton("Find Best Feature")
        self.export_button = QPushButton("Export Report CSV")
        for b in [self.load_button, self.run_button, self.best_button, self.export_button]:
            buttons.addWidget(b)

        controls = QGridLayout()
        self.feature_combo = QComboBox()
        self.threshold_spin = QDoubleSpinBox()
        self.threshold_spin.setRange(0.1, 1000.0)
        self.threshold_spin.setValue(5.0)
        self.threshold_spin.setSingleStep(1.0)
        self.threshold_spin.setSuffix(" %")
        controls.addWidget(QLabel("Feature"), 0, 0)
        controls.addWidget(self.feature_combo, 0, 1)
        controls.addWidget(QLabel("Kick-in threshold"), 0, 2)
        controls.addWidget(self.threshold_spin, 0, 3)

        cards = QHBoxLayout()
        self.file_label = self._card("File: Not loaded")
        self.subjects_label = self._card("Subjects: --")
        self.detected_label = self._card("Detected: --")
        self.variability_label = self._card("Variability: --")
        for card in [self.file_label, self.subjects_label, self.detected_label, self.variability_label]:
            cards.addWidget(card)

        self.report = QTextEdit()
        self.report.setReadOnly(True)
        self.table = QTableWidget()

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addLayout(buttons)
        layout.addLayout(controls)
        layout.addLayout(cards)
        layout.addWidget(self.report, 2)
        layout.addWidget(self.table, 3)
        self.setCentralWidget(central)

        self.load_button.clicked.connect(self.load_csv)
        self.run_button.clicked.connect(self.run_interpretation)
        self.best_button.clicked.connect(self.find_best_feature)
        self.export_button.clicked.connect(self.export_csv)

    def load_csv(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Open Baseline Changes CSV", str(DEFAULT_CHANGES), "CSV files (*.csv)")
        if not path:
            return
        try:
            self.df = pd.read_csv(path)
            if "subject_id" not in self.df.columns or "minutes_after_coffee" not in self.df.columns:
                raise ValueError("CSV must contain subject_id and minutes_after_coffee columns.")
            features = detect_features(self.df)
            if not features:
                raise ValueError("No *_percent_change feature columns found.")
            self.feature_combo.clear()
            self.feature_combo.addItems(features)
            self.file_label.setText(f"File: {Path(path).name}")
            self.subjects_label.setText(f"Subjects: {self.df['subject_id'].nunique()}")
            self.report.setText("CSV loaded. Select feature and threshold, then run interpretation.")
        except Exception as exc:
            QMessageBox.critical(self, "Load Error", str(exc))

    def run_interpretation(self) -> None:
        if self.df is None:
            QMessageBox.information(self, "No CSV", "Load baseline changes CSV first.")
            return
        feature = self.feature_combo.currentText()
        threshold = float(self.threshold_spin.value())
        self.results = estimate_kick_in(self.df, feature, threshold)
        self.populate_table(self.results)

        valid = self.results.dropna(subset=["estimated_kick_in_min"])
        detected = len(valid)
        total = len(self.results)
        self.detected_label.setText(f"Detected: {detected}/{total}")
        self.variability_label.setText("Variability: see report")

        if not valid.empty:
            mean_kick = valid["estimated_kick_in_min"].mean()
            min_kick = valid["estimated_kick_in_min"].min()
            max_kick = valid["estimated_kick_in_min"].max()
        else:
            mean_kick = min_kick = max_kick = np.nan

        report = [
            "CAFFEINE KICK-IN INTERPRETATION",
            "",
            f"Selected feature: {feature}",
            f"Threshold: {threshold:.1f}% change from baseline",
            f"Subjects with detected effect: {detected}/{total}",
            f"Mean kick-in time: {mean_kick:.2f} minutes" if np.isfinite(mean_kick) else "Mean kick-in time: not available",
            f"Range: {min_kick:.0f} to {max_kick:.0f} minutes" if np.isfinite(min_kick) else "Range: not available",
            variability_sentence(self.results),
            "",
            "Interpretation guidance:",
            "• Earlier kick-in means the selected feature changed soon after caffeine intake.",
            "• A wide range across subjects means the caffeine response is highly subjective.",
            "• Compare several features before making a final scientific conclusion.",
        ]
        self.report.setText("\n".join(report))

    def find_best_feature(self) -> None:
        if self.df is None:
            QMessageBox.information(self, "No CSV", "Load baseline changes CSV first.")
            return
        threshold = float(self.threshold_spin.value())
        self.scores = score_features(self.df, threshold)
        self.populate_table(self.scores)
        if self.scores.empty:
            self.report.setText("No features could be scored.")
            return
        best = self.scores.iloc[0]
        report = [
            "BEST FEATURE SEARCH",
            "",
            f"Threshold: {threshold:.1f}%",
            f"Best feature: {best['feature']}",
            f"Detection rate: {best['detection_rate_percent']:.1f}%",
            f"Mean kick-in time: {best['mean_kick_in_min']:.2f} minutes" if np.isfinite(best['mean_kick_in_min']) else "Mean kick-in time: not available",
            f"Mean maximum absolute change: {best['mean_max_abs_change_percent']:.2f}%",
            "",
            "The best feature is ranked by detection rate first and response strength second.",
        ]
        self.report.setText("\n".join(report))

    def populate_table(self, df: pd.DataFrame) -> None:
        preview = df.round(3).copy()
        self.table.setRowCount(len(preview))
        self.table.setColumnCount(len(preview.columns))
        self.table.setHorizontalHeaderLabels([str(c) for c in preview.columns])
        for r in range(len(preview)):
            for c, col in enumerate(preview.columns):
                item = QTableWidgetItem(str(preview.iloc[r, c]))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(r, c, item)
        self.table.resizeColumnsToContents()

    def export_csv(self) -> None:
        output = self.results if self.results is not None else self.scores
        if output is None:
            QMessageBox.information(self, "No Results", "Run interpretation or best feature search first.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save Report CSV", str(BASE_DIR / "caffeine_interpretation_report.csv"), "CSV files (*.csv)")
        if not path:
            return
        try:
            output.to_csv(path, index=False)
            QMessageBox.information(self, "Export Complete", f"Saved report to:\n{path}")
        except Exception as exc:
            QMessageBox.critical(self, "Export Error", str(exc))


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyleSheet(APPLE_STYLE)
    win = InterpretationWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
