# Copyright (c) 2026 Pietro Chierico
# SPDX-License-Identifier: MIT

"""
Small WiFi TCP utilities for ESP32 PPG IR streams.

Accepted input formats:
    90234
    12345,90234
    12345,80123,90234
    ir=90234

For three-column CSV lines, the third value is treated as IR.
For two-column CSV lines, the second value is treated as IR.
"""
from __future__ import annotations

import re
import socket
from typing import Optional


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

    Header lines such as "ir" or "millis,red,ir" are ignored.
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
