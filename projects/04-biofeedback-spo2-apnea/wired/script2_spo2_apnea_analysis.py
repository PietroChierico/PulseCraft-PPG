# Copyright (c) 2026 Pietro Chierico
# SPDX-License-Identifier: MIT

"""
Script 2 - SpO2 Voluntary Apnea Analysis Explorer

Purpose
-------
Load the CSV exported by Script 1 and explore estimated SpO2 during a voluntary
apnea protocol. The app compares oxygenation across protocol phases:
    Baseline  vs  Apnea  vs  Recovery

Main tools
----------
1. Box plot: SpO2 distribution by phase.
2. Time plot: SpO2 over time, colored by phase, for selected subject/trial.
3. Histogram explorer: SpO2 histograms by phase.
4. Subject/trial summary table with apnea duration, oxygen drop, recovery level.
5. Export summary CSV.

Install
-------
pip install pandas numpy matplotlib PyQt6

Run
---
python script2_spo2_apnea_analysis.py
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from PyQt6.QtCore import Qt
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
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

APPLE_STYLE = """
QMainWindow, QWidget {
    background-color: #07111f;
    color: #f5f7fb;
    font-family: -apple-system, BlinkMacSystemFont, Segoe UI;
}
QLabel {
    color: #f5f7fb;
    font-size: 14px;
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
QPushButton:pressed { background-color: rgba(255,255,255,0.26); }
QComboBox {
    background-color: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.20);
    border-radius: 12px;
    padding: 8px;
    color: #f5f7fb;
}
QTableWidget {
    background-color: rgba(255,255,255,0.06);
    color: #f5f7fb;
    gridline-color: rgba(255,255,255,0.18);
    border-radius: 14px;
}
QHeaderView::section {
    background-color: rgba(255,255,255,0.12);
    color: #f5f7fb;
    padding: 7px;
    border: none;
    font-weight: 700;
}
"""

REQUIRED_COLUMNS = {"subject_id", "trial_id", "phase", "elapsed_trial_s", "spo2_estimate"}
PHASE_ORDER = ["Baseline", "Apnea", "Recovery"]
PHASE_COLORS = {
    "Baseline": "#36d399",
    "Apnea": "#ff5f7e",
    "Recovery": "#7ab8ff",
}


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")

    clean = df.copy()
    clean["subject_id"] = clean["subject_id"].astype(str)
    clean["trial_id"] = pd.to_numeric(clean["trial_id"], errors="coerce")
    clean["elapsed_trial_s"] = pd.to_numeric(clean["elapsed_trial_s"], errors="coerce")
    clean["spo2_estimate"] = pd.to_numeric(clean["spo2_estimate"], errors="coerce")
    clean = clean.dropna(subset=["trial_id", "elapsed_trial_s", "spo2_estimate"])
    clean["trial_id"] = clean["trial_id"].astype(int)
    clean = clean[clean["phase"].isin(PHASE_ORDER)]
    return clean.sort_values(["subject_id", "trial_id", "elapsed_trial_s"]).reset_index(drop=True)


def recovery_time_to_near_baseline(group: pd.DataFrame, baseline_mean: float, oxygen_drop: float) -> float:
    recovery = group[group["phase"] == "Recovery"].copy()
    if recovery.empty or oxygen_drop <= 0:
        return np.nan
    target = baseline_mean - 0.05 * oxygen_drop
    recovered = recovery[recovery["spo2_estimate"] >= target]
    if recovered.empty:
        return np.nan
    return float(recovered["elapsed_trial_s"].iloc[0] - recovery["elapsed_trial_s"].iloc[0])


def compute_trial_summary(df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, float | int | str]] = []
    for (subject_id, trial_id), group in df.groupby(["subject_id", "trial_id"]):
        baseline = group[group["phase"] == "Baseline"]
        apnea = group[group["phase"] == "Apnea"]
        recovery = group[group["phase"] == "Recovery"]
        if baseline.empty or apnea.empty:
            continue

        baseline_mean = float(baseline["spo2_estimate"].mean())
        baseline_min = float(baseline["spo2_estimate"].min())
        apnea_mean = float(apnea["spo2_estimate"].mean())
        apnea_min = float(apnea["spo2_estimate"].min())
        apnea_duration = float(apnea["elapsed_trial_s"].max() - apnea["elapsed_trial_s"].min()) if len(apnea) > 1 else 0.0
        recovery_mean = float(recovery["spo2_estimate"].mean()) if not recovery.empty else np.nan
        recovery_final = float(recovery["spo2_estimate"].tail(max(1, min(50, len(recovery)))).mean()) if not recovery.empty else np.nan
        oxygen_drop = max(0.0, baseline_mean - apnea_min)
        recovery_time = recovery_time_to_near_baseline(group, baseline_mean, oxygen_drop)

        rows.append({
            "subject_id": subject_id,
            "trial_id": int(trial_id),
            "baseline_mean_spo2": baseline_mean,
            "baseline_min_spo2": baseline_min,
            "apnea_mean_spo2": apnea_mean,
            "apnea_min_spo2": apnea_min,
            "recovery_mean_spo2": recovery_mean,
            "recovery_final_spo2": recovery_final,
            "oxygen_drop_spo2": oxygen_drop,
            "apnea_duration_s": apnea_duration,
            "recovery_time_95pct_s": recovery_time,
            "samples": int(len(group)),
        })
    return pd.DataFrame(rows)


class AnalysisCanvas(FigureCanvas):
    def __init__(self) -> None:
        self.figure = Figure(figsize=(12, 7), facecolor="#07111f")
        super().__init__(self.figure)

    def reset(self) -> None:
        self.figure.clear()

    @staticmethod
    def style_axis(ax, title: str, ylabel: str = "Estimated SpO2 (%)") -> None:
        ax.set_facecolor("#0b1728")
        ax.set_title(title, color="white", fontsize=14, weight="bold", pad=12)
        ax.set_ylabel(ylabel, color="white")
        ax.tick_params(colors="white")
        ax.grid(True, alpha=0.22)
        for spine in ax.spines.values():
            spine.set_color((1, 1, 1, 0.25))


class SpO2AnalysisWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("SpO2 Apnea Analysis Explorer")
        self.resize(1450, 940)
        self.df: Optional[pd.DataFrame] = None
        self.summary: Optional[pd.DataFrame] = None
        self._build_ui()

    def _build_ui(self) -> None:
        central = QWidget()
        root = QVBoxLayout(central)

        title = QLabel("SpO2 Voluntary Apnea Analysis Explorer")
        title.setStyleSheet("font-size: 34px; font-weight: 900;")
        subtitle = QLabel(
            "Explore how oxygenation changes across Baseline, Voluntary Apnea, and Recovery. "
            "Educational signal-analysis tool only, not a medical diagnostic device."
        )
        subtitle.setStyleSheet("font-size: 15px; color: #c9d2e3;")
        self.status = QLabel("Load a CSV exported from Script 1.")
        self.status.setStyleSheet("font-size: 15px; color: #7ab8ff; font-weight: 700;")

        controls = QGridLayout()
        self.load_button = QPushButton("Load Data CSV")
        self.subject_combo = QComboBox()
        self.trial_combo = QComboBox()
        self.phase_combo = QComboBox()
        self.phase_combo.addItems(["All phases", *PHASE_ORDER])
        self.boxplot_button = QPushButton("Box Plot: Baseline vs Apnea vs Recovery")
        self.time_button = QPushButton("Time Plot: Selected Trial")
        self.hist_button = QPushButton("Histogram Explorer")
        self.summary_button = QPushButton("Metric Explorer")
        self.export_button = QPushButton("Export Summary CSV")

        controls.addWidget(self.load_button, 0, 0)
        controls.addWidget(QLabel("Subject"), 0, 1)
        controls.addWidget(self.subject_combo, 0, 2)
        controls.addWidget(QLabel("Trial"), 0, 3)
        controls.addWidget(self.trial_combo, 0, 4)
        controls.addWidget(QLabel("Phase filter"), 0, 5)
        controls.addWidget(self.phase_combo, 0, 6)
        controls.addWidget(self.boxplot_button, 1, 0, 1, 2)
        controls.addWidget(self.time_button, 1, 2)
        controls.addWidget(self.hist_button, 1, 3)
        controls.addWidget(self.summary_button, 1, 4)
        controls.addWidget(self.export_button, 1, 5, 1, 2)

        self.canvas = AnalysisCanvas()
        self.table = QTableWidget()
        self.table.setMinimumHeight(230)

        root.addWidget(title)
        root.addWidget(subtitle)
        root.addWidget(self.status)
        root.addLayout(controls)
        root.addWidget(self.canvas, stretch=3)
        root.addWidget(QLabel("Trial-level metrics"))
        root.addWidget(self.table, stretch=1)
        self.setCentralWidget(central)

        self.load_button.clicked.connect(self.load_csv)
        self.subject_combo.currentTextChanged.connect(self.update_trials)
        self.boxplot_button.clicked.connect(self.plot_phase_boxplot)
        self.time_button.clicked.connect(self.plot_selected_trial_time)
        self.hist_button.clicked.connect(self.plot_histograms)
        self.summary_button.clicked.connect(self.plot_metric_explorer)
        self.export_button.clicked.connect(self.export_summary)

    def load_csv(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Load SpO2 CSV", str(Path.home()), "CSV files (*.csv)")
        if not path:
            return
        try:
            raw = pd.read_csv(path)
            self.df = normalize_dataframe(raw)
            self.summary = compute_trial_summary(self.df)
            if self.df.empty:
                QMessageBox.warning(self, "Empty data", "No valid Baseline/Apnea/Recovery samples were found.")
                return
            self.subject_combo.clear()
            self.subject_combo.addItems(sorted(self.df["subject_id"].astype(str).unique()))
            self.update_trials()
            self.populate_table()
            self.status.setText(f"Loaded {Path(path).name} · {len(self.df)} samples · {len(self.summary)} usable trials")
            self.plot_phase_boxplot()
        except Exception as exc:
            QMessageBox.critical(self, "Load error", str(exc))

    def require_data(self) -> bool:
        if self.df is None or self.summary is None:
            QMessageBox.information(self, "No data", "Please load a CSV first.")
            return False
        return True

    def update_trials(self) -> None:
        if self.df is None or not self.subject_combo.currentText():
            return
        subject = self.subject_combo.currentText()
        trials = sorted(self.df.loc[self.df["subject_id"].astype(str) == subject, "trial_id"].unique())
        self.trial_combo.clear()
        self.trial_combo.addItems([str(int(t)) for t in trials])

    def filtered_df(self) -> pd.DataFrame:
        assert self.df is not None
        phase = self.phase_combo.currentText()
        if phase == "All phases":
            return self.df.copy()
        return self.df[self.df["phase"] == phase].copy()

    def selected_trial_df(self) -> pd.DataFrame:
        assert self.df is not None
        subject = self.subject_combo.currentText()
        trial_text = self.trial_combo.currentText()
        if not subject or not trial_text:
            return pd.DataFrame()
        trial = int(trial_text)
        return self.df[(self.df["subject_id"].astype(str) == subject) & (self.df["trial_id"] == trial)].copy()

    def populate_table(self) -> None:
        if self.summary is None:
            return
        table_df = self.summary.round(3)
        self.table.setColumnCount(len(table_df.columns))
        self.table.setRowCount(len(table_df))
        self.table.setHorizontalHeaderLabels(list(table_df.columns))
        for row_idx in range(len(table_df)):
            for col_idx, col in enumerate(table_df.columns):
                item = QTableWidgetItem(str(table_df.iloc[row_idx, col_idx]))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row_idx, col_idx, item)
        self.table.resizeColumnsToContents()

    def plot_phase_boxplot(self) -> None:
        if not self.require_data():
            return
        df = self.filtered_df()
        self.canvas.reset()
        ax = self.canvas.figure.add_subplot(111)

        phases = [phase for phase in PHASE_ORDER if phase in set(df["phase"])]
        data = [df.loc[df["phase"] == phase, "spo2_estimate"].dropna().values for phase in phases]
        box = ax.boxplot(data, labels=phases, patch_artist=True, medianprops={"color": "white", "linewidth": 2})
        for patch, phase in zip(box["boxes"], phases):
            patch.set_facecolor(PHASE_COLORS.get(phase, "#ffffff"))
            patch.set_alpha(0.55)

        self.canvas.style_axis(ax, "SpO2 Box Plot: Baseline vs Apnea vs Recovery")
        ax.set_xlabel("Protocol phase", color="white")
        self.canvas.figure.tight_layout()
        self.canvas.draw()

    def plot_selected_trial_time(self) -> None:
        if not self.require_data():
            return
        group = self.selected_trial_df()
        if group.empty:
            QMessageBox.information(self, "No trial", "Select a valid subject and trial.")
            return

        self.canvas.reset()
        ax = self.canvas.figure.add_subplot(111)
        group = group.sort_values("elapsed_trial_s")
        for phase in PHASE_ORDER:
            phase_group = group[group["phase"] == phase]
            if phase_group.empty:
                continue
            ax.plot(
                phase_group["elapsed_trial_s"],
                phase_group["spo2_estimate"],
                linewidth=3,
                label=phase,
                color=PHASE_COLORS[phase],
            )
            ax.axvspan(
                float(phase_group["elapsed_trial_s"].min()),
                float(phase_group["elapsed_trial_s"].max()),
                color=PHASE_COLORS[phase],
                alpha=0.08,
            )
        subject = self.subject_combo.currentText()
        trial = self.trial_combo.currentText()
        self.canvas.style_axis(ax, f"SpO2 Over Time · Subject {subject} · Trial {trial}")
        ax.set_xlabel("Elapsed trial time (s)", color="white")
        ax.legend(facecolor="#0b1728", edgecolor=(1, 1, 1, 0.25), labelcolor="white")
        self.canvas.figure.tight_layout()
        self.canvas.draw()

    def plot_histograms(self) -> None:
        if not self.require_data():
            return
        df = self.filtered_df()
        self.canvas.reset()
        ax = self.canvas.figure.add_subplot(111)
        for phase in PHASE_ORDER:
            values = df.loc[df["phase"] == phase, "spo2_estimate"].dropna().values
            if len(values) == 0:
                continue
            ax.hist(values, bins=24, alpha=0.42, label=phase, color=PHASE_COLORS[phase])
        self.canvas.style_axis(ax, "SpO2 Histogram Explorer", "Number of samples")
        ax.set_xlabel("Estimated SpO2 (%)", color="white")
        ax.legend(facecolor="#0b1728", edgecolor=(1, 1, 1, 0.25), labelcolor="white")
        self.canvas.figure.tight_layout()
        self.canvas.draw()

    def plot_metric_explorer(self) -> None:
        if not self.require_data():
            return
        summary = self.summary.copy()
        if summary.empty:
            QMessageBox.information(self, "No summary", "No usable trial summary was computed.")
            return
        self.canvas.reset()
        ax = self.canvas.figure.add_subplot(111)
        labels = [f"{r.subject_id}\nT{r.trial_id}" for r in summary.itertuples()]
        x = np.arange(len(summary))
        width = 0.28
        ax.bar(x - width, summary["baseline_mean_spo2"], width, label="Baseline mean", color=PHASE_COLORS["Baseline"], alpha=0.75)
        ax.bar(x, summary["apnea_min_spo2"], width, label="Apnea min", color=PHASE_COLORS["Apnea"], alpha=0.75)
        ax.bar(x + width, summary["recovery_final_spo2"], width, label="Recovery final", color=PHASE_COLORS["Recovery"], alpha=0.75)
        self.canvas.style_axis(ax, "Metric Explorer: Baseline Mean vs Apnea Minimum vs Recovery Final")
        ax.set_xlabel("Subject / Trial", color="white")
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=45, ha="right")
        ax.legend(facecolor="#0b1728", edgecolor=(1, 1, 1, 0.25), labelcolor="white")
        self.canvas.figure.tight_layout()
        self.canvas.draw()

    def export_summary(self) -> None:
        if not self.require_data():
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Summary CSV",
            str(Path.home() / "spo2_apnea_trial_summary.csv"),
            "CSV files (*.csv)",
        )
        if not path:
            return
        try:
            self.summary.to_csv(path, index=False)
            self.status.setText(f"Exported summary to {path}")
        except Exception as exc:
            QMessageBox.critical(self, "Export error", str(exc))


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyleSheet(APPLE_STYLE)
    win = SpO2AnalysisWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
