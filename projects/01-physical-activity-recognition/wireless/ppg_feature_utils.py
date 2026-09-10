# Copyright (c) 2026 Pietro Chierico
# SPDX-License-Identifier: MIT

"""
Shared PPG feature utilities for Resting vs Walking demos.

WiFi TCP input formats accepted by the parser:
    one IR PPG value per line, for example:
        80211
        80235
        80197

    or CSV lines from the ESP32 streamer, for example:
        millis,red,ir
        12345,80123,90234

    or two-column CSV lines, for example:
        millis,ir
        12345,90234
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import re
import socket

import numpy as np
from scipy.signal import butter, filtfilt, welch


@dataclass
class PPGConfig:
    tcp_host: str = "192.168.4.1"
    tcp_port: int = 3333
    tcp_connect_timeout_s: float = 5.0
    sampling_rate_hz: float = 100.0
    window_seconds: float = 10.0
    tcp_lines_per_tick: int = 50
    max_samples: int = 30000


FEATURE_COLUMNS = [
    "raw_mean",
    "raw_std",
    "raw_range",
    "raw_iqr",
    "detrended_std",
    "derivative_mean_abs",
    "derivative_std",
    "zero_crossing_rate",
    "pulse_energy",
    "noise_energy",
    "noise_ratio",
    "spectral_centroid",
]

CSV_COLUMNS = [
    "recording_id",
    "timestamp_s",
    "sample_index",
    "protocol_phase",
    "target",
    "window_seconds",
    *FEATURE_COLUMNS,
]


class WiFiPPGClient:
    """
    Small non-blocking TCP line reader for the ESP32 PPG WiFi stream.

    The ESP32 opens a TCP server. This client connects to that server and reads
    newline-terminated text samples without blocking the GUI update loop.
    """

    def __init__(self, host: str, port: int, connect_timeout_s: float = 5.0) -> None:
        host = host.strip()
        if not host:
            raise ValueError("ESP32 IP / host cannot be empty.")
        if port <= 0 or port > 65535:
            raise ValueError("TCP port must be between 1 and 65535.")

        self.host = host
        self.port = int(port)
        self.socket = socket.create_connection((self.host, self.port), timeout=connect_timeout_s)
        self.socket.setblocking(False)
        self._receive_buffer = ""
        self._closed = False

    @property
    def connected(self) -> bool:
        return not self._closed and self.socket is not None

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        try:
            self.socket.close()
        except Exception:
            pass

    def _pop_complete_lines(self, lines: list[str], max_lines: int) -> None:
        while len(lines) < max_lines and "\n" in self._receive_buffer:
            line, self._receive_buffer = self._receive_buffer.split("\n", 1)
            lines.append(line.rstrip("\r"))

    def read_lines(self, max_lines: int) -> list[str]:
        if not self.connected:
            return []

        lines: list[str] = []
        self._pop_complete_lines(lines, max_lines)

        while len(lines) < max_lines:
            try:
                chunk = self.socket.recv(4096)
            except BlockingIOError:
                break
            except socket.timeout:
                break
            except OSError as exc:
                self.close()
                raise ConnectionError(f"TCP read error: {exc}") from exc

            if not chunk:
                self.close()
                raise ConnectionError("TCP connection closed by the ESP32.")

            self._receive_buffer += chunk.decode("utf-8", errors="ignore")
            self._pop_complete_lines(lines, max_lines)

        return lines


def _to_float(text: str) -> Optional[float]:
    try:
        return float(text.strip())
    except (TypeError, ValueError):
        return None


def parse_ir_value(line: str) -> Optional[float]:
    """
    Extract one IR sample from a TCP text line.

    Accepted examples:
        90234
        12345,90234
        12345,80123,90234
        ir=90234

    For three-column ESP32 lines, the third value is treated as IR.
    For two-column ESP32 lines, the second value is treated as IR.
    """
    line = line.strip()
    if not line or line.startswith("#"):
        return None

    if "," in line:
        parts = [part.strip() for part in line.split(",")]
        if len(parts) >= 3:
            value = _to_float(parts[2])
            if value is not None:
                return value
        if len(parts) >= 2:
            value = _to_float(parts[1])
            if value is not None:
                return value
        if parts:
            value = _to_float(parts[0])
            if value is not None:
                return value
        return None

    value = _to_float(line)
    if value is not None:
        return value

    numeric_tokens = re.findall(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?", line)
    if not numeric_tokens:
        return None
    return _to_float(numeric_tokens[-1])


def parse_red_value(line: str) -> Optional[float]:
    """
    Backward-compatible alias for older scripts.

    The current WiFi workflow uses IR data. This alias keeps old imports working
    while extracting the IR value with the new parser.
    """
    return parse_ir_value(line)


def highpass_filter(x: np.ndarray, fs: float, cutoff_hz: float = 0.5) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    if len(x) < 40:
        return x - np.mean(x)
    nyquist = 0.5 * fs
    normalized_cutoff = cutoff_hz / nyquist
    b, a = butter(2, normalized_cutoff, btype="highpass")
    return filtfilt(b, a, x)


def compute_ppg_noise_features(ir_raw: np.ndarray, fs: float) -> dict[str, float]:
    ir_raw = np.asarray(ir_raw, dtype=float)
    ir_detrended = highpass_filter(ir_raw, fs)

    raw_mean = float(np.mean(ir_raw))
    raw_std = float(np.std(ir_raw))
    raw_range = float(np.percentile(ir_raw, 95) - np.percentile(ir_raw, 5))
    raw_iqr = float(np.percentile(ir_raw, 75) - np.percentile(ir_raw, 25))

    derivative = np.diff(ir_raw)
    derivative_mean_abs = float(np.mean(np.abs(derivative))) if len(derivative) else 0.0
    derivative_std = float(np.std(derivative)) if len(derivative) > 1 else 0.0

    centered = ir_detrended - np.mean(ir_detrended)
    zero_crossing_rate = (
        float(np.sum(np.diff(np.signbit(centered))) / max(len(centered) - 1, 1))
        if len(centered) > 2
        else 0.0
    )

    if len(ir_detrended) >= 64:
        freqs, power = welch(ir_detrended, fs=fs, nperseg=min(256, len(ir_detrended)))
        pulse_band = (freqs >= 0.5) & (freqs <= 3.0)
        noise_band = (freqs > 3.0) & (freqs <= 12.0)
        total_band = (freqs >= 0.5) & (freqs <= 12.0)

        pulse_energy = float(np.trapezoid(power[pulse_band], freqs[pulse_band])) if np.any(pulse_band) else 0.0
        noise_energy = float(np.trapezoid(power[noise_band], freqs[noise_band])) if np.any(noise_band) else 0.0
        total_energy = pulse_energy + noise_energy + 1e-9
        noise_ratio = float(noise_energy / total_energy)

        if np.any(total_band) and np.sum(power[total_band]) > 0:
            spectral_centroid = float(np.sum(freqs[total_band] * power[total_band]) / np.sum(power[total_band]))
        else:
            spectral_centroid = 0.0
    else:
        pulse_energy = 0.0
        noise_energy = 0.0
        noise_ratio = 0.0
        spectral_centroid = 0.0

    return {
        "raw_mean": raw_mean,
        "raw_std": raw_std,
        "raw_range": raw_range,
        "raw_iqr": raw_iqr,
        "detrended_std": float(np.std(ir_detrended)),
        "derivative_mean_abs": derivative_mean_abs,
        "derivative_std": derivative_std,
        "zero_crossing_rate": zero_crossing_rate,
        "pulse_energy": pulse_energy,
        "noise_energy": noise_energy,
        "noise_ratio": noise_ratio,
        "spectral_centroid": spectral_centroid,
    }
