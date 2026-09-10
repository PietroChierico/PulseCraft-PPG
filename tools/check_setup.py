# Copyright (c) 2026 Pietro Chierico
# SPDX-License-Identifier: MIT
"""
PulseCraft PPG - environment and stream check.

    python tools/check_setup.py                       # check Python packages
    python tools/check_setup.py --stream 127.0.0.1:3333
    python tools/check_setup.py --stream COM5         # (serial not probed here; use the GUI)

The --stream check connects to a TCP PPG source (simulator or ESP32), reads ~3 s,
and reports the measured sample rate and value range so you can catch a rate
mismatch before collecting data.
"""
from __future__ import annotations

import argparse
import importlib
import socket
import sys
import time

PACKAGES = [
    ("numpy", "numpy"),
    ("scipy", "scipy"),
    ("pandas", "pandas"),
    ("matplotlib", "matplotlib"),
    ("scikit-learn", "sklearn"),
    ("joblib", "joblib"),
    ("pyserial", "serial"),
    ("PyQt6", "PyQt6.QtCore"),
    ("pyqtgraph", "pyqtgraph"),
    ("Flask", "flask"),
]


def check_packages() -> bool:
    ok = True
    print(f"Python {sys.version.split()[0]}")
    for name, module in PACKAGES:
        try:
            importlib.import_module(module)
            print(f"  ok    {name}")
        except Exception as exc:  # noqa: BLE001
            ok = False
            print(f"  MISS  {name}  ({exc.__class__.__name__})")
    if not ok:
        print("\nInstall everything with:  pip install -r requirements.txt")
    return ok


def check_stream(target: str, seconds: float = 3.0) -> bool:
    if ":" not in target:
        print(f"'{target}' looks like a serial port. Test serial from the project GUI's port field.")
        return False
    host, port_s = target.rsplit(":", 1)
    port = int(port_s)
    print(f"Connecting to {host}:{port} ...")
    try:
        conn = socket.create_connection((host, port), timeout=5.0)
    except OSError as exc:
        print(f"  FAILED: {exc}")
        return False

    conn.settimeout(1.0)
    buf = ""
    values: list[float] = []
    start = time.perf_counter()
    try:
        while time.perf_counter() - start < seconds:
            try:
                chunk = conn.recv(4096).decode("utf-8", "ignore")
            except socket.timeout:
                continue
            if not chunk:
                break
            buf += chunk
            while "\n" in buf:
                line, buf = buf.split("\n", 1)
                line = line.strip()
                if not line or line[0].isalpha():
                    continue
                parts = [p for p in line.replace(",", " ").split() if p]
                try:
                    values.append(float(parts[-1]))
                except (ValueError, IndexError):
                    pass
    finally:
        conn.close()

    elapsed = time.perf_counter() - start
    if not values:
        print("  connected, but no numeric samples parsed - check the stream format")
        return False
    rate = len(values) / elapsed
    print(f"  samples: {len(values)} in {elapsed:.1f} s  ->  ~{rate:.0f} Hz")
    print(f"  value range: {min(values):.0f} .. {max(values):.0f}")
    if rate < 60:
        print("  WARNING: rate well below 100 Hz. Set ESP32 SAMPLE_AVERAGE=1 or")
        print("           set sampling_rate_hz in the project config to match.")
    return True


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Check the PulseCraft PPG environment / stream.")
    p.add_argument("--stream", metavar="HOST:PORT", help="probe a TCP PPG source")
    args = p.parse_args(argv)

    pkg_ok = check_packages()
    stream_ok = True
    if args.stream:
        print()
        stream_ok = check_stream(args.stream)
    return 0 if (pkg_ok and stream_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
