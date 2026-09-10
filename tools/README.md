# Tools

Small helpers that make the kit usable before you have hardware, and without it.

## `ppg_simulator.py`

Starts a TCP server that imitates the ESP32 wireless firmware. It accepts one client and then
streams `millis,red,ir` lines at a fixed rate.

```bash
python tools/ppg_simulator.py --scenario activity        # default port 3333
```

| `--scenario` | What it does |
|--------------|--------------|
| `plain` | clean resting PPG |
| `activity` | resting pulse with periodic walking bursts, for Project 01 |
| `caffeine` | heart rate drifts up over about 4 minutes, for Project 02 |
| `relaxation` | heart rate down, variability up after about 60 seconds, for Project 03 |
| `apnea` | baseline, then a Red and IR ratio shift during a roughly 30 second hold, then recovery, for Project 04 |
| `stress` | elevated heart rate, low variability, slight tremor, for Project 05 |

Other flags are `--host 0.0.0.0` to expose it on the LAN, `--port`, and `--rate` which defaults
to 100.

Point the project's script or GUI at host `127.0.0.1` and port `3333`. The whole loop, collect
then train then run live, works on simulated data, which is handy for getting familiar with a
project or for testing changes in CI.

## `check_setup.py`

```bash
python tools/check_setup.py                           # are all Python packages importable
python tools/check_setup.py --stream 127.0.0.1:3333   # measure the live sample rate
```

The `--stream` probe reads about 3 seconds and prints the measured rate and value range. If it
shows well under 100 Hz you have a rate mismatch to fix before recording. See
[../docs/hardware.md](../docs/hardware.md#sample-rate).
