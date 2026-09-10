# Project 05. Mental stress detection

Can a small model separate relaxed from stressed, live, using PPG-derived waveform, pulse and HRV
features?

| Item | Value |
|------|-------|
| Signal | IR PPG |
| Hardware | Wired Arduino or wireless ESP32 |
| Feature window | 10 seconds |
| Roughly how long | about 35 minutes to collect, then about 25 minutes of analysis |
| No-hardware mode | `python tools/ppg_simulator.py --scenario stress` |

## How it goes

1. Collect with `script1_stress_dataset_collection.py`. A multi-phase protocol that alternates
   calm baselines with cognitive stressors such as mental arithmetic, a timed reaction task and
   cognitive interference. Each 10 second window is labeled `Relaxed` or `Stressed`.
2. Analyze and train with `script2_stress_analysis_training_export.py`. See which features
   separate the classes, train and test, then export the model.
3. Challenge with `script3_stress_live_detection_challenge.py`. A live `Relaxed` against
   `Stressed` readout. Participants try to stay relaxed under a stressor.

## What you get out of it

Acute stress activates the sympathetic nervous system, which raises heart rate, lowers HRV and
subtly changes the waveform. Stress labels are noisy, since a stress task is not stressful for
everyone every time. You also deal with feature stability, class balance and why per-session
normalization matters.

## Run

```bash
pip install -r ../../../requirements.txt

python ../../../tools/ppg_simulator.py --scenario stress
cd wired && python app_demo5_stress.py                         # or  cd wireless && python app_demo5_stress.py
```

The wired serial format is shown in `wired/arduino_serial_ppg_format_example.ino`.

## What to expect

Accuracy within one person is usually good, and the model leans on HRV-proxy and pulse-rate
features. Generalization across people is weak with a small dataset, which is expected and worth
writing up.

## Ideas to take it further

Add a neutral third class and watch accuracy fall. Test the model on a fresh session recorded a
day later. Add a self-reported stress slider from 1 to 10 and correlate it with the model score.

## Safety

An educational demo. Not a medical device and not a psychological assessment. The stressor tasks
are mild and voluntary, and participants can stop at any time.
