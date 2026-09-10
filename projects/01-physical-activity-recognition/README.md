# Project 01 — Physical activity recognition

**Question:** can we separate *resting* from *walking* using only the motion artifact in a
wrist/arm IR PPG signal?

| | |
|---|---|
| Signal | IR PPG |
| Hardware | Wireless (ESP32) — first choice; wired Arduino sketch included as a reference |
| Feature window | 10 s |
| Time to run | ~45 min once hardware/simulator is set up |
| No-hardware mode | `python tools/ppg_simulator.py --scenario activity` |

## What students do

1. **Collect** (`script1_dataset_collection_protocol.py`) — follow the guided protocol
   (20 s stabilise · 60 s resting · 10 s pause · 60 s walking). Each 10 s window is saved as a
   labeled feature row. Repeat for several people.
2. **Analyze & train** (`script2_analysis_training_export.py`) — compare feature distributions
   for resting vs walking, pick features, train and test a small classifier, export it.
3. **Run live** (`script3_live_classification.py`) — stream live and watch the model label
   resting/walking in real time; try to fool it.

## What students learn

- Motion artifact is not just "noise" — it carries information.
- Which features respond to movement (derivative spread, high-frequency energy, noise ratio) and
  which do not.
- Why a model that scores perfectly in the room can still be learning the wrong thing.

## Run

```bash
pip install -r ../../../requirements.txt

# no hardware:
python ../../../tools/ppg_simulator.py --scenario activity      # terminal 1
cd wireless && python script1_dataset_collection_protocol.py    # terminal 2  (host 127.0.0.1, port 3333)

# real hardware: flash hardware/wireless-esp32/project-01-wifi-ir-streamer, then use the ESP32 IP
```

`wireless/Main_page.py` opens a one-page launcher with buttons for the three scripts.

## Expected result

With 3+ clean sessions from 2+ people, a simple classifier reaches clearly-above-chance accuracy.
Walking windows show higher derivative std, higher noise-band energy, and a higher noise ratio.
Cross-person accuracy is lower than within-person — a good discussion point.

## Extensions

- Add a third class (stairs, arm swing).
- Replace the model with a small random forest; compare.
- Split train/test strictly by person and report the drop.

## Safety

Educational biomedical-signal demo. Not a medical device; not for diagnosis or safety-critical use.
