# Tools

Small helpers that make the kit usable before (and without) hardware.

## `ppg_simulator.py` — run projects with no hardware

Starts a TCP server that imitates the ESP32 wireless firmware: one client, then a stream of
`millis,red,ir` lines at a fixed rate.

```bash
python tools/ppg_simulator.py --scenario activity        # default port 3333
```

| `--scenario` | What it does |
|--------------|--------------|
| `plain` | clean resting PPG |
| `activity` | resting pulse + periodic walking bursts (motion artifact) — for Project 01 |
| `caffeine` | heart rate drifts up over ~4 min — for Project 02 |
| `relaxation` | HR down, variability up after ~60 s — for Project 03 |
| `apnea` | baseline + Red/IR ratio shift during a ~30 s hold, then recovery — for Project 04 |
| `stress` | elevated HR, low variability, slight tremor — for Project 05 |

Other flags: `--host 0.0.0.0` (expose on LAN), `--port`, `--rate` (default 100).

Point the project's script or GUI at `127.0.0.1` : `3333`. The collect → train → run-live loop
works fully on simulated data — ideal for preparing a class or testing changes in CI.

## `check_setup.py` — verify environment and stream

```bash
python tools/check_setup.py                        # are all Python packages importable?
python tools/check_setup.py --stream 127.0.0.1:3333   # measure the live sample rate
```

The `--stream` probe reads ~3 s and prints the measured rate and value range. If it shows well
under 100 Hz you have a rate mismatch to fix before collecting (see
[`../docs/hardware.md`](../docs/hardware.md#sample-rate)).
