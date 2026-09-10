# Copyright (c) 2026 Pietro Chierico
# SPDX-License-Identifier: MIT

"""
Small serial utilities for Arduino PPG IR streams over USB cable.

Accepted Arduino Serial.print / Serial.println formats:
    90234
    ir=90234
    IR: 90234
    12345,90234
    12345,80123,90234

For CSV-like lines, the last numeric value is treated as the PPG/IR sample.
This matches common Arduino Serial Monitor output and also works with lines
that contain labels such as "millis,red,ir" after the header is ignored.
"""
from __future__ import annotations

import re
from typing import Optional

try:
    import serial
    from serial.tools import list_ports
except Exception:  # pragma: no cover - keeps import safe before installation
    serial = None
    list_ports = None


_NUMBER_PATTERN = re.compile(r"[-+]?\d*\.\d+|[-+]?\d+")


def list_serial_ports() -> list[str]:
    """Return available serial/COM port device names."""
    if list_ports is None:
        return []
    return [port.device for port in list_ports.comports()]


def parse_serial_ppg_value(line: str) -> Optional[float]:
    """
    Extract one numeric PPG/IR value from an Arduino serial text line.

    The parser is intentionally permissive because student Arduino sketches
    often print different formats. If more than one number is present, the last
    numeric value is used. This supports "millis,ir" and "millis,red,ir".
    Header lines that contain no numbers return None.
    """
    text = line.strip()
    if not text or text.startswith("#"):
        return None
    numbers = _NUMBER_PATTERN.findall(text)
    if not numbers:
        return None
    try:
        return float(numbers[-1])
    except ValueError:
        return None


# Backward-compatible alias used by earlier project code.
parse_ir_value = parse_serial_ppg_value


class ArduinoSerialPPGReader:
    """
    Small line reader for Arduino USB serial PPG streams.

    The class opens the selected COM/serial port and reads newline-terminated
    samples without blocking the GUI for long periods. Make sure the Arduino IDE
    Serial Monitor is closed before connecting from Python, because only one
    program can usually own the serial port at a time.
    """

    def __init__(self, port: str, baudrate: int = 115200, timeout_s: float = 0.02) -> None:
        if serial is None:
            raise RuntimeError("pyserial is not installed. Run: pip install pyserial")
        port = port.strip()
        if not port:
            raise ValueError("Serial port cannot be empty.")
        self.port = port
        self.baudrate = int(baudrate)
        self.timeout_s = float(timeout_s)
        self.serial_connection = serial.Serial(
            port=self.port,
            baudrate=self.baudrate,
            timeout=self.timeout_s,
        )
        try:
            self.serial_connection.reset_input_buffer()
        except Exception:
            pass

    @property
    def connected(self) -> bool:
        return bool(self.serial_connection is not None and self.serial_connection.is_open)

    def close(self) -> None:
        if self.serial_connection is None:
            return
        try:
            if self.serial_connection.is_open:
                self.serial_connection.close()
        except Exception:
            pass

    def read_lines(self, max_lines: int) -> list[str]:
        if not self.connected:
            return []
        lines: list[str] = []
        for _ in range(max(1, int(max_lines))):
            try:
                raw_line = self.serial_connection.readline()
            except Exception as exc:
                self.close()
                raise ConnectionError(f"Serial read error: {exc}") from exc
            if not raw_line:
                break
            lines.append(raw_line.decode("utf-8", errors="ignore").strip())
        return lines
