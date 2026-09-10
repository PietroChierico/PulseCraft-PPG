# Copyright (c) 2026 Pietro Chierico
# SPDX-License-Identifier: MIT
"""
PulseCraft PPG - synthetic signal simulator (no hardware needed).

Opens a TCP server that behaves like the ESP32 wireless firmware: it accepts one
client and streams newline-terminated `millis,red,ir` samples at a fixed rate.
Every wireless project in this repository can run against it end to end.

Usage
-----
    python tools/ppg_simulator.py --scenario activity
    python tools/ppg_simulator.py --scenario apnea --host 0.0.0.0 --port 3333 --rate 100

Then point a project's script/GUI at host 127.0.0.1 (or your LAN IP) and port 3333.

Scenarios
---------
    activity     resting pulse with periodic walking bursts (motion artifact)
    caffeine     heart rate drifts upward over ~4 minutes
    relaxation   heart rate falls and beat-to-beat variability rises after ~60 s
    apnea        after ~40 s: baseline drift + Red/IR ratio shift, recovers after ~30 s
    stress       elevated heart rate, reduced variability, small baseline tremor
    plain        clean resting PPG, no events

Only depends on numpy and the standard library.
"""
from __future__ import annotations

import argparse
import math
import socket
import sys
import time

import numpy as np

DC_IR = 90000.0
DC_RED = 70000.0
AC_FRACTION = 0.03  # pulsatile amplitude as a fraction of DC


def cardiac_waveform(phase: np.ndarray) -> np.ndarray:
    """A rough PPG pulse shape in [0, 1] from a 0..2pi phase: sharp systolic upstroke
    plus a smaller dicrotic bump."""
    systolic = np.exp(-((np.mod(phase, 2 * math.pi) - 1.2) ** 2) / 0.30)
    dicrotic = 0.35 * np.exp(-((np.mod(phase, 2 * math.pi) - 3.1) ** 2) / 0.45)
    return 0.85 * systolic + dicrotic


class Scenario:
    def __init__(self, name: str) -> None:
        self.name = name
        self.hr_hz = 1.1          # ~66 bpm
        self.hrv = 0.02           # relative beat interval jitter
        self.resp_hz = 0.25       # ~15 breaths/min
        self.motion = 0.0         # motion artifact amplitude (rel. to AC)
        self.ratio = 1.0          # Red/IR AC ratio multiplier (1.0 ~ healthy)

    def update(self, t: float) -> None:
        n = self.name
        if n == "activity":
            burst = (t % 40.0) > 22.0
            self.motion = 2.5 if burst else 0.05
            self.hr_hz = 1.6 if burst else 1.05
        elif n == "caffeine":
            self.hr_hz = 1.05 + 0.35 * min(t / 240.0, 1.0)
        elif n == "relaxation":
            k = min(max((t - 60.0) / 60.0, 0.0), 1.0)
            self.hr_hz = 1.15 - 0.20 * k
            self.hrv = 0.02 + 0.06 * k
        elif n == "apnea":
            in_apnea = 40.0 <= t < 70.0
            since = t - 40.0
            if in_apnea:
                self.resp_hz = 0.01
                self.ratio = 1.0 + 0.06 * min(since / 30.0, 1.0)
                self.hr_hz = 1.05 + 0.10 * min(since / 30.0, 1.0)
            elif t >= 70.0:
                rec = min((t - 70.0) / 30.0, 1.0)
                self.resp_hz = 0.25
                self.ratio = 1.06 - 0.06 * rec
                self.hr_hz = 1.15 - 0.10 * rec
        elif n == "stress":
            self.hr_hz = 1.45
            self.hrv = 0.008
            self.motion = 0.15


def generate(scenario: Scenario, rate: float):
    """Infinite generator yielding (red, ir) integer samples."""
    dt = 1.0 / rate
    t = 0.0
    phase = 0.0
    rng = np.random.default_rng(12345)
    beat_interval = 1.0 / scenario.hr_hz
    next_beat = beat_interval
    while True:
        scenario.update(t)
        # advance cardiac phase; redraw a jittered interval once per beat
        phase += 2 * math.pi * scenario.hr_hz * dt
        if t >= next_beat:
            beat_interval = (1.0 / scenario.hr_hz) * (1.0 + rng.normal(0.0, scenario.hrv))
            next_beat = t + max(beat_interval, 0.3)

        pulse = cardiac_waveform(np.array([phase]))[0]
        resp = 0.15 * math.sin(2 * math.pi * scenario.resp_hz * t)
        motion = scenario.motion * math.sin(2 * math.pi * 2.3 * t) * (0.6 + 0.4 * rng.random())
        noise = rng.normal(0.0, 0.03)

        ac_ir = AC_FRACTION * (pulse + resp + motion + noise)
        ac_red = AC_FRACTION * scenario.ratio * (pulse + resp + 0.9 * motion + noise)

        ir = DC_IR * (1.0 + ac_ir)
        red = DC_RED * (1.0 + ac_red)
        yield int(max(red, 0)), int(max(ir, 0))
        t += dt


def serve(host: str, port: int, rate: float, scenario_name: str) -> None:
    scenario = Scenario(scenario_name)
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((host, port))
    srv.listen(1)
    print(f"[ppg_simulator] scenario={scenario_name} rate={rate:g} Hz")
    print(f"[ppg_simulator] listening on {host}:{port} - point a project here (Ctrl+C to stop)")

    try:
        while True:
            conn, addr = srv.accept()
            print(f"[ppg_simulator] client connected: {addr[0]}:{addr[1]}")
            conn.sendall(b"millis,red,ir\n")
            samples = generate(Scenario(scenario_name), rate)
            start = time.perf_counter()
            sent = 0
            try:
                while True:
                    red, ir = next(samples)
                    millis = int((time.perf_counter() - start) * 1000)
                    conn.sendall(f"{millis},{red},{ir}\n".encode("ascii"))
                    sent += 1
                    target = start + sent / rate
                    sleep = target - time.perf_counter()
                    if sleep > 0:
                        time.sleep(sleep)
            except (BrokenPipeError, ConnectionResetError, OSError):
                print("[ppg_simulator] client disconnected - waiting for a new one")
            finally:
                conn.close()
    except KeyboardInterrupt:
        print("\n[ppg_simulator] stopped")
    finally:
        srv.close()


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Synthetic PPG TCP streamer for PulseCraft PPG.")
    p.add_argument("--scenario", default="plain",
                   choices=["plain", "activity", "caffeine", "relaxation", "apnea", "stress"])
    p.add_argument("--host", default="127.0.0.1", help="bind address (use 0.0.0.0 for LAN)")
    p.add_argument("--port", type=int, default=3333)
    p.add_argument("--rate", type=float, default=100.0, help="samples per second")
    args = p.parse_args(argv)
    serve(args.host, args.port, args.rate, args.scenario)
    return 0


if __name__ == "__main__":
    sys.exit(main())
