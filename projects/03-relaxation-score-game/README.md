# Project 03. Relaxation score game

How much does one 60 second guided breathing exercise change pulse and heart-rate variability
features, and can we turn that into a live relaxation score?

| Item | Value |
|------|-------|
| Signal | IR PPG |
| Hardware | Wired Arduino or wireless ESP32 |
| Feature window | 10 seconds |
| Roughly how long | about 30 minutes per participant |
| No-hardware mode | `python tools/ppg_simulator.py --scenario relaxation` |

## How it goes

1. Collect with `script1_relaxation_dataset_collection.py`. The phases are 20 seconds to
   stabilise, 60 seconds pre-relaxation which is saved, 60 seconds of guided deep breathing, and
   60 seconds post-relaxation which is saved.
2. Analyze and train with `script2_relaxation_analysis_training_export.py`. Quantify the shift
   from pre to post, and fit a model or a scoring function.
3. Play with `script3_relaxation_live_score_game.py`. A live score that rewards a calmer, slower,
   more variable pulse. Participants try breathing techniques to raise it.

## What you get out of it

Slow breathing, around 6 breaths per minute, increases HRV and respiratory sinus arrhythmia, and
you can see it in the waveform. You also see the difference between measuring a change of state
and classifying a person, and you have to design a score that motivates without being gamed by
simply holding still.

## Run

```bash
pip install -r ../../../requirements.txt

python ../../../tools/ppg_simulator.py --scenario relaxation
cd wired && python app_demo3_relaxation.py                     # or  cd wireless && python app_demo3_relaxation.py
```

## What to expect

Most participants show a lower pulse rate and higher beat-to-beat variability after the exercise.
The effect is usually clearer than the caffeine one, and it returns toward baseline within a few
minutes.

## Ideas to take it further

Compare box breathing, 4-7-8 breathing and paced 6 per minute breathing. Add a biofeedback bar
that animates with the breathing cycle.

## Safety

An educational demo. Not a medical device. If a participant feels light-headed during deep
breathing, stop and go back to normal breathing.
