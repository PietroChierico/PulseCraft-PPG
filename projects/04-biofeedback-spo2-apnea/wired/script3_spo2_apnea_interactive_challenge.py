# Copyright (c) 2026 Pietro Chierico
# SPDX-License-Identifier: MIT

"""
Script 3 - SpO2 Apnea Leaderboard Game

Purpose
-------
Turn the voluntary apnea SpO2 dataset into an interactive leaderboard game.
The goal is to reward trials where the participant keeps oxygenation high while
holding a longer voluntary apnea.

Game idea
---------
A high score is achieved by:
    1. Longer apnea duration.
    2. Higher minimum SpO2 during apnea.
    3. Smaller oxygen drop from baseline.
    4. Good recovery after apnea.

This is an educational biomedical-signal game only. It is not medical advice,
not a diagnostic tool, and should not encourage unsafe breath holding.

Install
-------
pip install pandas numpy matplotlib PyQt6

Run
---
python script3_spo2_apnea_leaderboard_game.py
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
    font-weight: 800;
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


def compute_game_scores(df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, float | int | str]] = []
    for (subject_id, trial_id), group in df.groupby(["subject_id", "trial_id"]):
        baseline = group[group["phase"] == "Baseline"]
        apnea = group[group["phase"] == "Apnea"]
        recovery = group[group["phase"] == "Recovery"]
        if baseline.empty or apnea.empty:
            continue

        baseline_mean = float(baseline["spo2_estimate"].mean())
        apnea_min = float(apnea["spo2_estimate"].min())
        apnea_mean = float(apnea["spo2_estimate"].mean())
        apnea_duration = float(apnea["elapsed_trial_s"].max() - apnea["elapsed_trial_s"].min()) if len(apnea) > 1 else 0.0
        recovery_final = float(recovery["spo2_estimate"].tail(max(1, min(50, len(recovery)))).mean()) if not recovery.empty else np.nan
        oxygen_drop = max(0.0, baseline_mean - apnea_min)
        recovery_time = recovery_time_to_near_baseline(group, baseline_mean, oxygen_drop)

        # Scoring philosophy:
        # - Duration is good, but capped to avoid making unsafe breath holding the only objective.
        # - High minimum SpO2 is strongly rewarded.
        # - Large oxygen drops are penalized.
        # - Recovery is rewarded if final recovery is close to baseline.
        duration_score = min(40.0, max(0.0, apnea_duration / 60.0 * 40.0))
        oxygen_floor_score = max(0.0, min(35.0, (apnea_min - 85.0) / 15.0 * 35.0))
        stability_score = max(0.0, 15.0 - oxygen_drop * 2.0)
        recovery_score = 0.0
        if not np.isnan(recovery_final):
            recovery_gap = abs(baseline_mean - recovery_final)
            recovery_score = max(0.0, 10.0 - recovery_gap * 2.0)

        total_score = int(round(duration_score + oxygen_floor_score + stability_score + recovery_score))
        badge = "Oxygen Champion"
        if total_score < 50:
            badge = "Needs Recovery"
        elif total_score < 70:
            badge = "Stable Breather"
        elif total_score < 85:
            badge = "Apnea Contender"

        rows.append({
            "rank": 0,
            "subject_id": subject_id,
            "trial_id": int(trial_id),
            "score": total_score,
            "badge": badge,
            "apnea_duration_s": apnea_duration,
            "baseline_mean_spo2": baseline_mean,
            "apnea_min_spo2": apnea_min,
            "apnea_mean_spo2": apnea_mean,
            "oxygen_drop_spo2": oxygen_drop,
            "recovery_final_spo2": recovery_final,
            "recovery_time_95pct_s": recovery_time,
            "duration_score": duration_score,
            "oxygen_floor_score": oxygen_floor_score,
            "stability_score": stability_score,
            "recovery_score": recovery_score,
        })

    scores = pd.DataFrame(rows)
    if scores.empty:
        return scores
    scores = scores.sort_values(
        ["score", "apnea_duration_s", "apnea_min_spo2"], ascending=[False, False, False]
    ).reset_index(drop=True)
    scores["rank"] = np.arange(1, len(scores) + 1)
    return scores


class GameCanvas(FigureCanvas):
    def __init__(self) -> None:
        self.figure = Figure(figsize=(12, 7), facecolor="#07111f")
        super().__init__(self.figure)

    def reset(self) -> None:
        self.figure.clear()

    @staticmethod
    def style_axis(ax, title: str, ylabel: str = "") -> None:
        ax.set_facecolor("#0b1728")
        ax.set_title(title, color="white", fontsize=14, weight="bold", pad=12)
        if ylabel:
            ax.set_ylabel(ylabel, color="white")
        ax.tick_params(colors="white")
        ax.grid(True, alpha=0.22)
        for spine in ax.spines.values():
            spine.set_color((1, 1, 1, 0.25))

    def plot_leaderboard(self, scores: pd.DataFrame) -> None:
        self.reset()
        ax = self.figure.add_subplot(111)
        top = scores.head(12).copy().sort_values("score", ascending=True)
        labels = [f"#{int(r.rank)} {r.subject_id} · T{int(r.trial_id)}" for r in top.itertuples()]
        ax.barh(labels, top["score"], color="#7ab8ff", alpha=0.85)
        for i, r in enumerate(top.itertuples()):
            ax.text(
                r.score + 1,
                i,
                f"{int(r.score)} pts · {r.apnea_duration_s:0.1f}s · min {r.apnea_min_spo2:0.1f}%",
                va="center",
                color="white",
                fontsize=10,
            )
        self.style_axis(ax, "Oxygenation Apnea Leaderboard", "")
        ax.set_xlabel("Game score", color="white")
        ax.set_xlim(0, max(105, float(top["score"].max()) + 18))
        self.figure.tight_layout()
        self.draw()

    def plot_selected_trial(self, group: pd.DataFrame, score_row: pd.Series) -> None:
        self.reset()
        ax = self.figure.add_subplot(111)
        group = group.sort_values("elapsed_trial_s")
        for phase in PHASE_ORDER:
            phase_group = group[group["phase"] == phase]
            if phase_group.empty:
                continue
            ax.plot(
                phase_group["elapsed_trial_s"],
                phase_group["spo2_estimate"],
                linewidth=3,
                color=PHASE_COLORS[phase],
                label=phase,
            )
            ax.axvspan(
                float(phase_group["elapsed_trial_s"].min()),
                float(phase_group["elapsed_trial_s"].max()),
                color=PHASE_COLORS[phase],
                alpha=0.08,
            )
        title = (
            f"#{int(score_row['rank'])} · Subject {score_row['subject_id']} · Trial {int(score_row['trial_id'])} · "
            f"{int(score_row['score'])} pts"
        )
        self.style_axis(ax, title, "Estimated SpO2 (%)")
        ax.set_xlabel("Elapsed trial time (s)", color="white")
        ax.legend(facecolor="#0b1728", edgecolor=(1, 1, 1, 0.25), labelcolor="white")
        self.figure.tight_layout()
        self.draw()

    def plot_score_breakdown(self, score_row: pd.Series) -> None:
        self.reset()
        ax = self.figure.add_subplot(111)
        labels = ["Duration", "Oxygen floor", "Stability", "Recovery"]
        values = [
            float(score_row["duration_score"]),
            float(score_row["oxygen_floor_score"]),
            float(score_row["stability_score"]),
            float(score_row["recovery_score"]),
        ]
        ax.bar(labels, values, color=["#7ab8ff", "#36d399", "#ffce5c", "#c79cff"], alpha=0.85)
        for i, value in enumerate(values):
            ax.text(i, value + 0.7, f"{value:0.1f}", ha="center", color="white", fontweight="bold")
        self.style_axis(ax, "Score Breakdown", "Points")
        ax.set_ylim(0, 45)
        self.figure.tight_layout()
        self.draw()


class SpO2LeaderboardGameWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("SpO2 Apnea Leaderboard Game")
        self.resize(1450, 940)
        self.df: Optional[pd.DataFrame] = None
        self.scores: Optional[pd.DataFrame] = None
        self._build_ui()

    def _build_ui(self) -> None:
        central = QWidget()
        root = QVBoxLayout(central)

        title = QLabel("SpO2 Apnea Leaderboard Game")
        title.setStyleSheet("font-size: 36px; font-weight: 900;")
        subtitle = QLabel(
            "Challenge: keep oxygenation high while maintaining a longer voluntary apnea. "
            "Score rewards duration, high minimum SpO2, small oxygen drop, and recovery."
        )
        subtitle.setStyleSheet("font-size: 15px; color: #c9d2e3;")
        warning = QLabel(
            "Safety note: educational analysis only. Do not use this app to encourage unsafe breath holding. Stop immediately if uncomfortable."
        )
        warning.setStyleSheet(
            "background-color: rgba(255,95,126,0.13); border: 1px solid rgba(255,95,126,0.28); "
            "border-radius: 18px; padding: 12px; color: #ffd6de; font-weight: 800;"
        )
        self.status = QLabel("Load a CSV exported from Script 1 to generate the leaderboard.")
        self.status.setStyleSheet("font-size: 15px; color: #7ab8ff; font-weight: 700;")

        controls = QGridLayout()
        self.load_button = QPushButton("Load Data CSV")
        self.leaderboard_button = QPushButton("Show Leaderboard")
        self.trial_button = QPushButton("Show Selected Trial")
        self.breakdown_button = QPushButton("Show Score Breakdown")
        self.export_button = QPushButton("Export Leaderboard CSV")
        self.player_combo = QComboBox()

        controls.addWidget(self.load_button, 0, 0)
        controls.addWidget(QLabel("Player / Trial"), 0, 1)
        controls.addWidget(self.player_combo, 0, 2, 1, 3)
        controls.addWidget(self.leaderboard_button, 1, 0)
        controls.addWidget(self.trial_button, 1, 1)
        controls.addWidget(self.breakdown_button, 1, 2)
        controls.addWidget(self.export_button, 1, 3)

        self.hero = QLabel("Winner: --")
        self.hero.setStyleSheet(
            "background: rgba(255,255,255,0.07); border: 1px solid rgba(255,255,255,0.14); "
            "border-radius: 24px; padding: 18px; font-size: 22px; font-weight: 900;"
        )

        self.canvas = GameCanvas()
        self.table = QTableWidget()
        self.table.setMinimumHeight(260)

        root.addWidget(title)
        root.addWidget(subtitle)
        root.addWidget(warning)
        root.addWidget(self.status)
        root.addLayout(controls)
        root.addWidget(self.hero)
        root.addWidget(self.canvas, stretch=3)
        root.addWidget(QLabel("Full leaderboard"))
        root.addWidget(self.table, stretch=1)
        self.setCentralWidget(central)

        self.load_button.clicked.connect(self.load_csv)
        self.leaderboard_button.clicked.connect(self.show_leaderboard)
        self.trial_button.clicked.connect(self.show_selected_trial)
        self.breakdown_button.clicked.connect(self.show_score_breakdown)
        self.export_button.clicked.connect(self.export_leaderboard)

    def load_csv(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Load SpO2 CSV", str(Path.home()), "CSV files (*.csv)")
        if not path:
            return
        try:
            raw = pd.read_csv(path)
            self.df = normalize_dataframe(raw)
            self.scores = compute_game_scores(self.df)
            if self.scores.empty:
                QMessageBox.warning(self, "No scores", "No usable trials found. Need at least Baseline and Apnea samples.")
                return
            self.populate_player_combo()
            self.populate_table()
            self.update_winner_card()
            self.status.setText(f"Loaded {Path(path).name} · {len(self.df)} samples · {len(self.scores)} leaderboard entries")
            self.show_leaderboard()
        except Exception as exc:
            QMessageBox.critical(self, "Load error", str(exc))

    def require_data(self) -> bool:
        if self.df is None or self.scores is None or self.scores.empty:
            QMessageBox.information(self, "No data", "Please load a CSV first.")
            return False
        return True

    def populate_player_combo(self) -> None:
        assert self.scores is not None
        self.player_combo.clear()
        for row in self.scores.itertuples():
            label = f"#{int(row.rank)} · {row.subject_id} · Trial {int(row.trial_id)} · {int(row.score)} pts · {row.badge}"
            self.player_combo.addItem(label, (str(row.subject_id), int(row.trial_id)))

    def populate_table(self) -> None:
        if self.scores is None:
            return
        display_cols = [
            "rank",
            "subject_id",
            "trial_id",
            "score",
            "badge",
            "apnea_duration_s",
            "apnea_min_spo2",
            "oxygen_drop_spo2",
            "recovery_final_spo2",
        ]
        table_df = self.scores[display_cols].round(3)
        self.table.setColumnCount(len(table_df.columns))
        self.table.setRowCount(len(table_df))
        self.table.setHorizontalHeaderLabels(list(table_df.columns))
        for row_idx in range(len(table_df)):
            for col_idx, col in enumerate(table_df.columns):
                item = QTableWidgetItem(str(table_df.iloc[row_idx, col_idx]))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if col == "rank" and str(table_df.iloc[row_idx, col_idx]) == "1":
                    item.setText("🏆 1")
                self.table.setItem(row_idx, col_idx, item)
        self.table.resizeColumnsToContents()

    def update_winner_card(self) -> None:
        if self.scores is None or self.scores.empty:
            self.hero.setText("Winner: --")
            return
        winner = self.scores.iloc[0]
        self.hero.setText(
            f"Winner: Subject {winner['subject_id']} · Trial {int(winner['trial_id'])} · "
            f"{int(winner['score'])}/100 pts · apnea {winner['apnea_duration_s']:0.1f}s · "
            f"minimum SpO2 {winner['apnea_min_spo2']:0.1f}% · {winner['badge']}"
        )

    def selected_score_row(self) -> Optional[pd.Series]:
        if not self.require_data():
            return None
        data = self.player_combo.currentData()
        if data is None:
            return None
        subject, trial = data
        rows = self.scores[(self.scores["subject_id"].astype(str) == subject) & (self.scores["trial_id"] == int(trial))]
        if rows.empty:
            return None
        return rows.iloc[0]

    def selected_trial_group(self, row: pd.Series) -> pd.DataFrame:
        assert self.df is not None
        return self.df[
            (self.df["subject_id"].astype(str) == str(row["subject_id"]))
            & (self.df["trial_id"] == int(row["trial_id"]))
        ].copy()

    def show_leaderboard(self) -> None:
        if not self.require_data():
            return
        self.canvas.plot_leaderboard(self.scores)

    def show_selected_trial(self) -> None:
        row = self.selected_score_row()
        if row is None:
            return
        group = self.selected_trial_group(row)
        self.canvas.plot_selected_trial(group, row)

    def show_score_breakdown(self) -> None:
        row = self.selected_score_row()
        if row is None:
            return
        self.canvas.plot_score_breakdown(row)

    def export_leaderboard(self) -> None:
        if not self.require_data():
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Leaderboard CSV",
            str(Path.home() / "spo2_apnea_leaderboard.csv"),
            "CSV files (*.csv)",
        )
        if not path:
            return
        try:
            self.scores.to_csv(path, index=False)
            self.status.setText(f"Exported leaderboard to {path}")
        except Exception as exc:
            QMessageBox.critical(self, "Export error", str(exc))


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyleSheet(APPLE_STYLE)
    win = SpO2LeaderboardGameWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
