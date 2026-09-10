# Project 02 — Caffeine response

**Question:** how long after a coffee do caffeine-related changes become visible in PPG features,
and how much does that differ between people?

| | |
|---|---|
| Signal | IR PPG |
| Hardware | Wired Arduino **or** wireless ESP32 |
| Feature window | 10 s |
| Time to run | one ~40 min session, then ~30 min analysis (data collection spans ~30 min real time) |
| No-hardware mode | `python tools/ppg_simulator.py --scenario caffeine` |

## What students do

1. **Collect** (`script1_caffeine_dataset_collection_protocol.py`) — record a **baseline**, then
   sessions at **+5, +10, +15, +20, +25 min** after the coffee. Each session: 15 s stabilise +
   60 s recording, saved as 10 s feature windows tagged with subject and time point.
2. **Analyze** (`script2_caffeine_analysis_export.py`) — plot each feature as a change from that
   subject's baseline over time; export summary CSVs and figures.
3. **Interpret** (`script3_caffeine_interpretation_assistant.py`) — a GUI that helps answer:
   when does the response appear, which feature moves most, how consistent is it across people.

## What students learn

- Comparing *within-subject* against a personal baseline instead of absolute values.
- Confounds: circadian drift, posture, temperature, having eaten — and how to control them.
- That a "known" physiological effect can be small, noisy, and subject-dependent.

## Run

```bash
pip install -r ../../../requirements.txt

python ../../../tools/ppg_simulator.py --scenario caffeine     # no hardware
cd wired      && python app.py        # or:  cd wireless && python app.py
```

## Expected result

Group-level trends (e.g. a modest heart-rate / pulse-amplitude shift) usually emerge by +10 to
+20 min, but individual curves vary a lot and some subjects show almost nothing. That variability
*is* the lesson.

## Extensions

- Decaf vs caffeinated blind control.
- Fit the time-to-onset per subject and compare to the caffeine pharmacokinetics literature.

## Safety

Educational demo. Not a medical device. Respect participants' caffeine tolerance and choices;
offer a decaf/no-coffee alternative.
