# Project 03 — Relaxation score game

**Question:** how much does one 60 s guided breathing exercise change pulse and heart-rate
variability features — and can we turn that into a live "relaxation score"?

| | |
|---|---|
| Signal | IR PPG |
| Hardware | Wired Arduino **or** wireless ESP32 |
| Feature window | 10 s |
| Time to run | ~30 min per participant |
| No-hardware mode | `python tools/ppg_simulator.py --scenario relaxation` |

## What students do

1. **Collect** (`script1_relaxation_dataset_collection.py`) — 20 s stabilise · 60 s pre-relaxation
   (saved) · 60 s guided deep breathing · 60 s post-relaxation (saved).
2. **Analyze & train** (`script2_relaxation_analysis_training_export.py`) — quantify the pre→post
   feature shift; fit a model / scoring function.
3. **Play** (`script3_relaxation_live_score_game.py`) — a live score that rewards a calmer,
   slower, more variable pulse; students try breathing techniques to raise it.

## What students learn

- Slow breathing (~6 breaths/min) increases HRV and respiratory sinus arrhythmia — visible in
  the waveform.
- The difference between measuring a *state change* and classifying a *person*.
- How to design a score that is motivating without being gameable by holding still.

## Run

```bash
pip install -r ../../../requirements.txt

python ../../../tools/ppg_simulator.py --scenario relaxation
cd wired      && python app_demo3_relaxation.py    # or:  cd wireless && python app_demo3_relaxation.py
```

## Expected result

Most participants show a lower pulse rate and higher beat-to-beat variability post-exercise.
The effect is usually clearer than the caffeine one and returns toward baseline within minutes.

## Extensions

- Compare box breathing vs 4-7-8 vs paced 6/min.
- Add a biofeedback bar that animates with the breathing cycle.

## Safety

Educational demo. Not a medical device. If a participant feels light-headed during deep
breathing, stop and return to normal breathing.
