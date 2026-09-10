# Copyright (c) 2026 Pietro Chierico
# SPDX-License-Identifier: MIT

"""
Script 2 - PPG Relaxation Feature Analysis, Training, and Model Export

Purpose
-------
Load the CSV exported from Script 1, compare every PPG feature between
Pre-Relaxation and Post-Relaxation using boxplots, train a simple relaxation
model, and export the trained scorer for Script 3.

Install
-------
pip install numpy pandas matplotlib scikit-learn joblib PyQt6

Run
---
python script2_relaxation_analysis_training_export.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication, QFileDialog, QGridLayout, QHBoxLayout, QLabel, QMainWindow,
    QMessageBox, QPushButton, QTextEdit, QVBoxLayout, QWidget
)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

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
QTextEdit { background-color: rgba(255,255,255,0.07); border: 1px solid rgba(255,255,255,0.15); border-radius: 18px; color: #f5f7fb; padding: 12px; font-size: 13px; }
"""


class RelaxationTrainingWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Demo 3 - Relaxation Analysis and Model Training")
        self.resize(1350, 900)
        self.data: pd.DataFrame | None = None
        self.model_bundle: dict | None = None
        self.current_feature_index = 0
        self.available_features: list[str] = []
        self._build_ui()

    def _build_ui(self) -> None:
        central = QWidget()
        layout = QVBoxLayout(central)

        self.title_label = QLabel("Load Data and Train Relaxation Model")
        self.title_label.setStyleSheet("font-size: 32px; font-weight: 900;")
        self.subtitle_label = QLabel("Generate one boxplot per feature: Pre-Relaxation vs Post-Relaxation, then export the trained model.")
        self.subtitle_label.setStyleSheet("font-size: 16px; color: #b7c2d8;")

        buttons = QHBoxLayout()
        self.load_button = QPushButton("Load Data")
        self.prev_button = QPushButton("Previous Feature Boxplot")
        self.next_button = QPushButton("Next Feature Boxplot")
        self.train_button = QPushButton("Train Model")
        self.export_button = QPushButton("Export Trained Model")
        for button in [self.load_button, self.prev_button, self.next_button, self.train_button, self.export_button]:
            buttons.addWidget(button)

        middle = QGridLayout()
        self.figure = Figure(figsize=(7, 5), tight_layout=True)
        self.canvas = FigureCanvas(self.figure)
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        middle.addWidget(self.canvas, 0, 0, 1, 2)
        middle.addWidget(self.log_box, 0, 2, 1, 1)

        layout.addWidget(self.title_label)
        layout.addWidget(self.subtitle_label)
        layout.addLayout(buttons)
        layout.addLayout(middle)
        self.setCentralWidget(central)

        self.load_button.clicked.connect(self.load_data)
        self.prev_button.clicked.connect(self.previous_feature)
        self.next_button.clicked.connect(self.next_feature)
        self.train_button.clicked.connect(self.train_model)
        self.export_button.clicked.connect(self.export_model)

        self._log("Waiting for dataset CSV. Use the Load Data button.")

    def _log(self, message: str) -> None:
        self.log_box.append(message)

    def load_data(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Load Relaxation Dataset CSV", str(Path.home()), "CSV files (*.csv)")
        if not path:
            return
        try:
            data = pd.read_csv(path)
        except Exception as exc:
            QMessageBox.critical(self, "Load error", f"Could not load CSV:\n{exc}")
            return

        if "target" not in data.columns:
            QMessageBox.critical(self, "Invalid dataset", "The CSV must contain a 'target' column.")
            return

        data = data[data["target"].isin(["Pre-Relaxation", "Post-Relaxation"])].copy()
        self.available_features = [col for col in FEATURE_COLUMNS if col in data.columns]
        if not self.available_features:
            QMessageBox.critical(self, "Invalid dataset", "No expected feature columns were found.")
            return

        self.data = data
        self.current_feature_index = 0
        self.model_bundle = None
        self._log(f"Loaded: {path}")
        self._log(f"Rows: {len(data)}")
        self._log(f"Pre-Relaxation rows: {(data['target'] == 'Pre-Relaxation').sum()}")
        self._log(f"Post-Relaxation rows: {(data['target'] == 'Post-Relaxation').sum()}")
        self._log(f"Features: {', '.join(self.available_features)}")
        self.plot_current_feature()

    def plot_current_feature(self) -> None:
        if self.data is None or not self.available_features:
            return
        feature = self.available_features[self.current_feature_index]
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        pre = self.data.loc[self.data["target"] == "Pre-Relaxation", feature].dropna().to_numpy(dtype=float)
        post = self.data.loc[self.data["target"] == "Post-Relaxation", feature].dropna().to_numpy(dtype=float)
        ax.boxplot([pre, post], tick_labels=["Pre-Relaxation", "Post-Relaxation"], showmeans=True)
        ax.set_title(f"Feature Boxplot: {feature}", fontsize=15, fontweight="bold")
        ax.set_ylabel(feature)
        ax.grid(True, alpha=0.25)
        self.canvas.draw()
        self._log(f"Showing boxplot {self.current_feature_index + 1}/{len(self.available_features)}: {feature}")

    def previous_feature(self) -> None:
        if not self.available_features:
            return
        self.current_feature_index = (self.current_feature_index - 1) % len(self.available_features)
        self.plot_current_feature()

    def next_feature(self) -> None:
        if not self.available_features:
            return
        self.current_feature_index = (self.current_feature_index + 1) % len(self.available_features)
        self.plot_current_feature()

    def train_model(self) -> None:
        if self.data is None:
            QMessageBox.information(self, "No data", "Load a dataset first.")
            return

        data = self.data.dropna(subset=["target"]).copy()
        class_counts = data["target"].value_counts()
        if len(class_counts) < 2 or class_counts.min() < 2:
            QMessageBox.warning(self, "Not enough data", "Collect at least two windows for each class before training.")
            return

        X = data[self.available_features]
        y = (data["target"] == "Post-Relaxation").astype(int)

        stratify = y if min(np.bincount(y)) >= 2 else None
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.30, random_state=42, stratify=stratify
        )

        pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("classifier", RandomForestClassifier(n_estimators=220, random_state=42, class_weight="balanced")),
        ])
        pipeline.fit(X_train, y_train)
        predictions = pipeline.predict(X_test)
        accuracy = accuracy_score(y_test, predictions)

        try:
            probabilities = pipeline.predict_proba(X_test)[:, 1]
            mean_score = float(np.mean(probabilities) * 100.0)
        except Exception:
            mean_score = float("nan")

        self.model_bundle = {
            "pipeline": pipeline,
            "features": self.available_features,
            "positive_label": "Post-Relaxation",
            "negative_label": "Pre-Relaxation",
            "created_at_unix": time.time(),
        }

        self._log("\nTraining complete.")
        self._log(f"Test accuracy: {accuracy:.3f}")
        self._log(f"Mean test relaxation score: {mean_score:.1f}/100")
        self._log("Confusion matrix [Pre, Post]:")
        self._log(str(confusion_matrix(y_test, predictions)))
        self._log("Classification report:")
        self._log(classification_report(y_test, predictions, target_names=["Pre-Relaxation", "Post-Relaxation"], zero_division=0))

        classifier = pipeline.named_steps["classifier"]
        importances = classifier.feature_importances_
        ranked = sorted(zip(self.available_features, importances), key=lambda item: item[1], reverse=True)
        self._log("Top feature importances:")
        for name, value in ranked[:8]:
            self._log(f"  {name}: {value:.3f}")

    def export_model(self) -> None:
        if self.model_bundle is None:
            QMessageBox.information(self, "No model", "Train the model first.")
            return
        default_name = f"ppg_relaxation_model_{int(time.time())}.joblib"
        path, _ = QFileDialog.getSaveFileName(self, "Export Trained Relaxation Model", str(Path.home() / default_name), "Joblib files (*.joblib)")
        if not path:
            return
        try:
            joblib.dump(self.model_bundle, path)
            self._log(f"Exported trained model to: {path}")
            QMessageBox.information(self, "Model exported", f"Model saved to:\n{path}")
        except Exception as exc:
            QMessageBox.critical(self, "Export error", f"Could not export model:\n{exc}")


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyleSheet(APPLE_STYLE)
    win = RelaxationTrainingWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
