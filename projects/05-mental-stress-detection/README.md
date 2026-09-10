# Project 05 — Mental stress detection

**Question:** can a small model separate *relaxed* from *stressed* from PPG-derived waveform,
pulse, and HRV features — live?

| | |
|---|---|
| Signal | IR PPG |
| Hardware | Wired Arduino **or** wireless ESP32 |
| Feature window | 10 s |
| Time to run | ~35 min collection + ~25 min analysis |
| No-hardware mode | `python tools/ppg_simulator.py --scenario stress` |

## What students do

1. **Collect** (`script1_stress_dataset_collection.py`) — a multi-phase protocol alternating calm
   baselines with cognitive stressors (mental arithmetic, timed reaction, cognitive
   interference), each 10 s window labeled `Relaxed` or `Stressed`.
2. **Analyze & train** (`script2_stress_analysis_training_export.py`) — inspect which features
   separate the classes, train + test, export the model.
3. **Challenge** (`script3_stress_live_detection_challenge.py`) — live `Relaxed` vs `Stressed`
   readout; students try to stay "relaxed" under a stressor.

## What students learn

- Acute stress → sympathetic activation → higher HR, lower HRV, subtle waveform changes.
- Stress labels are noisy: a "stress" task is not stressful for everyone, every time.
- Feature stability, class balance, and why per-session normalization matters.

## Run

```bash
pip install -r ../../../requirements.txt

python ../../../tools/ppg_simulator.py --scenario stress
cd wired      && python app_demo5_stress.py    # or:  cd wireless && python app_demo5_stress.py
```

Wired serial format reference: `wired/arduino_serial_ppg_format_example.ino`.

## Expected result

Within-subject accuracy is usually good; the model leans on HRV-proxy and pulse-rate features.
Cross-subject generalization is weak with class-sized data — expected, and worth writing up.

## Extensions

- Add a neutral third class and see accuracy fall.
- Test the model on a fresh session recorded a day later.
- Add a "self-reported stress 1–10" slider and correlate with the model score.

## Safety

Educational demo. Not a medical device and not a psychological assessment. Stressor tasks are
mild and voluntary; let participants stop anytime.
