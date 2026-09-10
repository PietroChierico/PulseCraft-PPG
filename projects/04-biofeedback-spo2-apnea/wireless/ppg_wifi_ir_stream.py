# Copyright (c) 2026 Pietro Chierico
# SPDX-License-Identifier: MIT

"""
Small WiFi TCP utilities for ESP32 PPG Red/Infrared streams.

Accepted input formats:
    Red: 12345 Infrared: 67890
    Red: 12345 IR: 67890
    red=12345, ir=67890
    12345, 67890
    12345 67890
    1000,12345,67890
    ir=67890
    67890

Rules:
    - For two numeric values, the first value is Red and the second value is Infrared.
    - For three or more numeric values, the last two values are treated as Red and Infrared
      so formats such as millis,red,ir are supported.
    - Single-value lines are treated as Infrared samples for the filter visualizer.
    - Header/comment lines are ignored.
"""
from __future__ import annotations

import re
import socket
from typing import Optional

import numpy as np


_NUMBER_PATTERN = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"
_RED_LABEL_PATTERN = re.compile(
    rf"\bred\b\s*[:=,]?\s*({_NUMBER_PATTERN})",
    flags=re.IGNORECASE,
)
_IR_LABEL_PATTERN = re.compile(
    rf"\b(?:infrared|ir)\b\s*[:=,]?\s*({_NUMBER_PATTERN})",
    flags=re.IGNORECASE,
)


class WiFiPPGClient:
    """
    Non-blocking TCP line reader for the ESP32 PPG WiFi stream.

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
                if lines:
                    return lines
                raise ConnectionError(f"TCP read error: {exc}") from exc

            if not chunk:
                self.close()
                if lines:
                    return lines
                raise ConnectionError("TCP connection closed by the ESP32.")

            self._receive_buffer += chunk.decode("utf-8", errors="ignore")
            self._pop_complete_lines(lines, max_lines)

        return lines


def _to_float(text: str) -> Optional[float]:
    try:
        return float(text.strip())
    except (TypeError, ValueError):
        return None


def _normalize_line(line: str | bytes | object) -> str:
    if line is None:
        return ""
    if isinstance(line, bytes):
        return line.decode("utf-8", errors="ignore").strip()
    return str(line).strip()


def _numeric_tokens(text: str) -> list[float]:
    values: list[float] = []
    for token in re.findall(_NUMBER_PATTERN, text):
        value = _to_float(token)
        if value is not None:
            values.append(value)
    return values


def parse_red_ir_values(line: str | bytes | object) -> tuple[Optional[float], Optional[float]]:
    """
    Extract Red and Infrared samples from one TCP text line.

    Returns:
        (red_value, infrared_value)

    Red can be None for single-value test lines used by the filter visualizer.
    Infrared is None when the line does not contain a usable IR sample.
    """
    text = _normalize_line(line)
    if not text or text.startswith("#"):
        return None, None

    red_value: Optional[float] = None
    infrared_value: Optional[float] = None

    red_match = _RED_LABEL_PATTERN.search(text)
    if red_match:
        red_value = _to_float(red_match.group(1))

    infrared_match = _IR_LABEL_PATTERN.search(text)
    if infrared_match:
        infrared_value = _to_float(infrared_match.group(1))

    numbers = _numeric_tokens(text)

    if len(numbers) >= 2:
        fallback_red = numbers[-2]
        fallback_infrared = numbers[-1]
        if red_value is None:
            red_value = fallback_red
        if infrared_value is None:
            infrared_value = fallback_infrared
    elif len(numbers) == 1 and red_value is None and infrared_value is None:
        infrared_value = numbers[0]

    return red_value, infrared_value


def parse_ir_value(line: str | bytes | object) -> Optional[float]:
    """
    Extract only the Infrared sample from one TCP text line.

    This is used by the filter visualizer, where Red is intentionally ignored.
    """
    _, infrared_value = parse_red_ir_values(line)
    return infrared_value


def compute_ac_dc_ratio(
    raw_window: np.ndarray,
    minimum_samples: int,
    value_offset: float = 0.0,
    stream_is_negated: bool = False,
) -> float:
    """
    Compute the AC/DC ratio from one Red or Infrared PPG window.

    The AC term is RMS after a simple linear detrend. The DC term is the median
    optical-intensity level. If the microcontroller sends a mirrored PPG stream,
    the signal is flipped back before computing DC.
    """
    raw = np.asarray(raw_window, dtype=float)
    raw = raw[np.isfinite(raw)]

    if len(raw) < minimum_samples:
        return np.nan

    signal = raw - value_offset
    if stream_is_negated:
        signal = -signal

    if len(signal) == 0:
        return np.nan

    if float(np.median(signal)) < 0:
        signal = -signal

    dc_value = float(np.median(signal))
    if not np.isfinite(dc_value) or dc_value <= 1e-9:
        return np.nan

    x = np.arange(len(signal), dtype=float)
    slope, intercept = np.polyfit(x, signal, 1)
    detrended = signal - (slope * x + intercept)
    low, high = np.percentile(detrended, [1, 99])
    detrended = np.clip(detrended, low, high)
    ac_rms = float(np.sqrt(np.mean(detrended ** 2)))

    if not np.isfinite(ac_rms) or ac_rms <= 1e-9:
        return np.nan

    ratio = ac_rms / dc_value
    if not np.isfinite(ratio) or ratio <= 0:
        return np.nan

    return float(ratio)


def compute_ratio_of_ratios(
    red_raw_window: np.ndarray,
    infrared_raw_window: np.ndarray,
    minimum_samples: int,
    value_offset: float = 0.0,
    stream_is_negated: bool = False,
) -> float:
    """
    Compute the pulse-oximetry ratio of ratios:

        R = (ACred / DCred) / (ACir / DCir)
    """
    red = np.asarray(red_raw_window, dtype=float)
    infrared = np.asarray(infrared_raw_window, dtype=float)

    n = min(len(red), len(infrared))
    if n < minimum_samples:
        return np.nan

    red = red[-n:]
    infrared = infrared[-n:]
    valid = np.isfinite(red) & np.isfinite(infrared)
    red = red[valid]
    infrared = infrared[valid]

    if len(red) < minimum_samples or len(infrared) < minimum_samples:
        return np.nan

    red_ratio = compute_ac_dc_ratio(
        red,
        minimum_samples=minimum_samples,
        value_offset=value_offset,
        stream_is_negated=stream_is_negated,
    )
    infrared_ratio = compute_ac_dc_ratio(
        infrared,
        minimum_samples=minimum_samples,
        value_offset=value_offset,
        stream_is_negated=stream_is_negated,
    )

    if (
        not np.isfinite(red_ratio)
        or not np.isfinite(infrared_ratio)
        or infrared_ratio <= 1e-12
    ):
        return np.nan

    ratio = red_ratio / infrared_ratio
    if not np.isfinite(ratio) or ratio <= 0:
        return np.nan

    return float(np.clip(ratio, 0.10, 1.60))


def estimate_spo2_from_ratio(
    ratio_of_ratios: float,
    calibration_intercept: float = 110.0,
    calibration_slope: float = 25.0,
    min_percent: float = 70.0,
    max_percent: float = 100.0,
) -> float:
    """
    Convert R into an estimated SpO2 value using the educational display curve:

        SpO2 = calibration_intercept - calibration_slope * R
    """
    if not np.isfinite(ratio_of_ratios):
        return np.nan

    spo2 = calibration_intercept - calibration_slope * ratio_of_ratios
    return float(np.clip(spo2, min_percent, max_percent))


def estimate_spo2_from_red_ir_windows(
    red_raw_window: np.ndarray,
    infrared_raw_window: np.ndarray,
    minimum_samples: int,
    value_offset: float = 0.0,
    stream_is_negated: bool = False,
    calibration_intercept: float = 110.0,
    calibration_slope: float = 25.0,
    min_percent: float = 70.0,
    max_percent: float = 100.0,
) -> tuple[float, float]:
    """
    Estimate SpO2 from paired Red and Infrared PPG windows.

    Returns:
        (spo2_estimate, ratio_of_ratios)
    """
    ratio = compute_ratio_of_ratios(
        red_raw_window,
        infrared_raw_window,
        minimum_samples=minimum_samples,
        value_offset=value_offset,
        stream_is_negated=stream_is_negated,
    )
    spo2 = estimate_spo2_from_ratio(
        ratio,
        calibration_intercept=calibration_intercept,
        calibration_slope=calibration_slope,
        min_percent=min_percent,
        max_percent=max_percent,
    )
    return spo2, ratio
