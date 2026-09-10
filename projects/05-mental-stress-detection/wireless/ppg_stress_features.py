# Copyright (c) 2026 Pietro Chierico
# SPDX-License-Identifier: MIT

"""
Shared PPG feature extraction utilities for Project 5 - Mental Stress Detection.

The functions in this file are used by Script 1 during dataset collection and
by Script 3 during live stress-state scoring. Keeping the feature logic in one
place helps ensure the live model receives the same feature names and units that
were used during training.
"""
from __future__ import annotations

import math
from typing import Iterable

import numpy as np

try:
    from scipy.signal import butter, find_peaks, sosfiltfilt, welch
except Exception:  # pragma: no cover - allows the GUI to open without SciPy
    butter = None
    find_peaks = None
    sosfiltfilt = None
    welch = None


BASE_FEATURE_COLUMNS = [
    "mean_ir",
    "std_ir",
    "range_ir",
    "rms_ir",
    "mad_ir",
    "diff_std",
    "diff_rms",
    "signal_energy",
    "dominant_frequency_hz",
    "spectral_entropy",
    "peak_count",
    "mean_peak_distance_s",
    "pulse_amplitude_mean",
]

HRV_FEATURE_COLUMNS = [
    "heart_rate_bpm",
    "ibi_mean_s",
    "ibi_std_s",
    "sdnn_ms",
    "rmssd_ms",
    "pnn50_percent",
    "pulse_interval_cv",
    "pulse_rate_variability",
]

FEATURE_COLUMNS = [*BASE_FEATURE_COLUMNS, *HRV_FEATURE_COLUMNS]

LEGACY_FEATURE_ALIASES = {
    "mean_red": "mean_ir",
    "std_red": "std_ir",
    "range_red": "range_ir",
    "rms_red": "rms_ir",
    "mad_red": "mad_ir",
}


def _finite_array(values: Iterable[float]) -> np.ndarray:
    array = np.asarray(list(values) if not isinstance(values, np.ndarray) else values, dtype=float)
    return array[np.isfinite(array)]


def _spectral_entropy(power_values: np.ndarray) -> float:
    power = np.asarray(power_values, dtype=float)
    total = float(np.sum(power))
    if total <= 0:
        return 0.0
    probabilities = power / total
    probabilities = probabilities[probabilities > 0]
    if len(probabilities) == 0:
        return 0.0
    return float(-np.sum(probabilities * np.log2(probabilities)) / np.log2(len(probabilities)))


def _safe_bandpass(values: np.ndarray, fs: float, lowcut: float = 0.5, highcut: float = 5.0) -> np.ndarray:
    centered = values - np.mean(values)
    if butter is None or sosfiltfilt is None or len(centered) < int(fs * 2):
        return centered

    nyquist = 0.5 * fs
    low = lowcut / nyquist
    high = highcut / nyquist
    if low <= 0 or high >= 1 or low >= high:
        return centered

    try:
        sos = butter(2, [low, high], btype="bandpass", output="sos")
        return sosfiltfilt(sos, centered)
    except Exception:
        return centered


def _detect_ppg_peaks(filtered: np.ndarray, fs: float) -> np.ndarray:
    if find_peaks is None or len(filtered) < int(fs * 3):
        return np.array([], dtype=int)

    min_distance = max(1, int(0.33 * fs))  # roughly 180 bpm maximum
    prominence = max(1e-9, float(np.std(filtered) * 0.25))

    candidates: list[np.ndarray] = []
    for signal in (filtered, -filtered):
        try:
            peaks, _ = find_peaks(signal, distance=min_distance, prominence=prominence)
        except Exception:
            peaks = np.array([], dtype=int)
        candidates.append(peaks)

    def score_peak_set(peaks: np.ndarray) -> tuple[int, float]:
        if len(peaks) < 2:
            return (0, 0.0)
        intervals = np.diff(peaks) / fs
        plausible = intervals[(intervals >= 0.33) & (intervals <= 1.50)]
        if len(plausible) == 0:
            return (0, float(len(peaks)))
        return (len(plausible), float(len(peaks)))

    return max(candidates, key=score_peak_set)


def compute_ppg_features(ir_window: np.ndarray, fs: float) -> dict[str, float]:
    """
    Convert one IR PPG window into waveform, pulse, and HRV features.

    Parameters
    ----------
    ir_window:
        One PPG window, normally 10 seconds of IR samples.
    fs:
        Sampling frequency in Hz.

    Returns
    -------
    dict[str, float]
        Feature dictionary. Missing or low-quality windows return zeros for
        features that cannot be estimated safely.
    """
    ir = _finite_array(ir_window)
    if len(ir) < 5:
        features = {name: 0.0 for name in FEATURE_COLUMNS}
        features.update({legacy: features[current] for legacy, current in LEGACY_FEATURE_ALIASES.items()})
        return features

    centered = ir - np.mean(ir)
    filtered = _safe_bandpass(ir, fs=fs)
    diff = np.diff(ir)

    if welch is not None and len(ir) >= int(fs * 4):
        freqs, power = welch(centered, fs=fs, nperseg=min(len(ir), int(fs * 8)))
        band = (freqs >= 0.05) & (freqs <= 5.0)
        freqs_band = freqs[band]
        power_band = power[band]
        dominant_frequency = float(freqs_band[int(np.argmax(power_band))]) if len(power_band) else 0.0
        entropy = _spectral_entropy(power_band) if len(power_band) else 0.0
    else:
        spectrum_power = np.abs(np.fft.rfft(centered)) ** 2
        freqs = np.fft.rfftfreq(len(centered), d=1.0 / fs)
        band = (freqs >= 0.05) & (freqs <= 5.0)
        dominant_frequency = float(freqs[band][int(np.argmax(spectrum_power[band]))]) if np.any(band) else 0.0
        entropy = _spectral_entropy(spectrum_power[band]) if np.any(band) else 0.0

    peaks = _detect_ppg_peaks(filtered, fs=fs)
    peak_count = int(len(peaks))

    if peak_count >= 2:
        all_intervals = np.diff(peaks) / fs
        intervals = all_intervals[(all_intervals >= 0.33) & (all_intervals <= 1.50)]
    else:
        intervals = np.array([], dtype=float)

    if len(intervals) >= 1:
        mean_peak_distance = float(np.mean(intervals))
        heart_rate_bpm = float(60.0 / mean_peak_distance) if mean_peak_distance > 0 else 0.0
        ibi_mean = mean_peak_distance
        ibi_std = float(np.std(intervals))
        sdnn_ms = float(np.std(intervals, ddof=1) * 1000.0) if len(intervals) >= 2 else 0.0
        pulse_interval_cv = float(ibi_std / ibi_mean) if ibi_mean > 0 else 0.0
    else:
        mean_peak_distance = 0.0
        heart_rate_bpm = 0.0
        ibi_mean = 0.0
        ibi_std = 0.0
        sdnn_ms = 0.0
        pulse_interval_cv = 0.0

    if len(intervals) >= 2:
        interval_diffs = np.diff(intervals)
        rmssd_ms = float(math.sqrt(np.mean(interval_diffs ** 2)) * 1000.0)
        pnn50_percent = float(np.mean(np.abs(interval_diffs) > 0.05) * 100.0)
        pulse_rate_variability = float(np.std(60.0 / intervals)) if np.all(intervals > 0) else 0.0
    else:
        rmssd_ms = 0.0
        pnn50_percent = 0.0
        pulse_rate_variability = 0.0

    if peak_count >= 1:
        baseline = np.percentile(filtered, 10)
        pulse_amplitude = float(np.mean(filtered[peaks] - baseline))
    else:
        pulse_amplitude = 0.0

    features = {
        "mean_ir": float(np.mean(ir)),
        "std_ir": float(np.std(ir)),
        "range_ir": float(np.max(ir) - np.min(ir)),
        "rms_ir": float(math.sqrt(np.mean(ir ** 2))),
        "mad_ir": float(np.mean(np.abs(ir - np.mean(ir)))),
        "diff_std": float(np.std(diff)) if len(diff) else 0.0,
        "diff_rms": float(math.sqrt(np.mean(diff ** 2))) if len(diff) else 0.0,
        "signal_energy": float(np.mean(centered ** 2)),
        "dominant_frequency_hz": dominant_frequency,
        "spectral_entropy": entropy,
        "peak_count": float(peak_count),
        "mean_peak_distance_s": mean_peak_distance,
        "pulse_amplitude_mean": pulse_amplitude,
        "heart_rate_bpm": heart_rate_bpm,
        "ibi_mean_s": ibi_mean,
        "ibi_std_s": ibi_std,
        "sdnn_ms": sdnn_ms,
        "rmssd_ms": rmssd_ms,
        "pnn50_percent": pnn50_percent,
        "pulse_interval_cv": pulse_interval_cv,
        "pulse_rate_variability": pulse_rate_variability,
    }
    features.update({legacy: features[current] for legacy, current in LEGACY_FEATURE_ALIASES.items()})
    return features
