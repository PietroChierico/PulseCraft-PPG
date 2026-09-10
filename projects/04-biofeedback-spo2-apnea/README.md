# Project 04 — Voluntary-apnea biofeedback + SpO2 proxy

**Question:** how do Red and IR PPG amplitudes — and their ratio — move during a short, safe,
voluntary breath-hold, and what does that tell us about how a pulse oximeter works?

> **Safety first.** This is a short, voluntary, supervised classroom activity. The participant
> controls the breath-hold and stops at the first sign of discomfort. Never push breath-holds.
> The "SpO2" number is an **uncalibrated educational proxy**, not a measurement.

| | |
|---|---|
| Signal | **Red + IR PPG** (both channels required) |
| Hardware | Wired Arduino **or** wireless ESP32 — dual-channel sketch |
| Window | 5 s rolling Red/IR ratio windows inside a full-trial CSV |
| Time to run | ~20 min per participant |
| No-hardware mode | `python tools/ppg_simulator.py --scenario apnea` |

## What students do

1. **Collect** (`script1_spo2_apnea_collection.py`) — 30 s baseline · participant-started
   voluntary apnea · 60 s recovery. Red and IR are recorded together.
2. **Analyze** (`script2_spo2_apnea_analysis.py`) — compute AC/DC per channel and the
   ratio-of-ratios; plot how it drifts during the hold and recovers afterward.
3. **Challenge** (`script3_spo2_apnea_interactive_challenge.py`) — a live biofeedback view of the
   ratio and a proxy trend during a supervised hold.

## What students learn

- Why oximetry needs *two* wavelengths and uses `(AC/DC)_red / (AC/DC)_ir`.
- What a real device calibrates (empirical curves) and why this proxy is not that.
- Physiological lag: the ratio keeps drifting for seconds *after* breathing resumes.

## Run

```bash
pip install -r ../../../requirements.txt

python ../../../tools/ppg_simulator.py --scenario apnea
cd wired      && python app_demo4_spo2_apnea.py    # or:  cd wireless && python app_demo4_spo2_apnea.py
```

Flash the **red-ir** sketch: `hardware/*/project-04-*red-ir*`.

## Expected result

During a ~20–30 s hold the ratio-of-ratios shifts slightly and the proxy trends downward, then
overshoots and recovers over ~30–60 s. Magnitudes vary and are not clinically meaningful.

## Extensions

- Compare finger vs wrist placement.
- Add a simple 2-point linear calibration against a real fingertip oximeter (clearly labeled as a
  classroom exercise).

## Safety

See the box above and [`../../SAFETY.md`](../../SAFETY.md). Stop immediately on dizziness, pain,
anxiety, or shortness of breath. Not for anyone with a relevant cardiovascular or respiratory
condition.
