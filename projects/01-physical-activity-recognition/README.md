# Project 01. Physical activity recognition

Can we tell resting from walking using only the motion artifact in a wrist or arm IR PPG signal?

| Item | Value |
|------|-------|
| Signal | IR PPG |
| Hardware | Wireless ESP32 is the first choice. A wired Arduino sketch is included as a reference. |
| Feature window | 10 seconds |
| Roughly how long | about 45 minutes once the hardware or simulator is set up |
| No-hardware mode | `python tools/ppg_simulator.py --scenario activity` |

## How it goes

1. Collect with `script1_dataset_collection_protocol.py`. Follow the guided protocol, which is
   20 seconds to stabilise, 60 seconds resting, a 10 second pause, then 60 seconds walking. Each
   10 second window is saved as a labeled feature row. Repeat for several people.
2. Analyze and train with `script2_analysis_training_export.py`. Compare the feature
   distributions for resting against walking, pick a few features, train and test a small
   classifier, and export it.
3. Run live with `script3_live_classification.py`. Stream live, watch the model label resting or
   walking in real time, and try to fool it.

`wireless/Main_page.py` opens a one-page launcher with buttons for the three scripts.

## What you get out of it

Motion artifact is not just noise, it carries information. You see which features respond to
movement, such as derivative spread, high-frequency energy and the noise ratio, and which do not.
And you see why a model that scores perfectly in one room can still be learning the wrong thing.

## Run

```bash
pip install -r ../../../requirements.txt

# no hardware, in two terminals
python ../../../tools/ppg_simulator.py --scenario activity
cd wireless && python script1_dataset_collection_protocol.py    # host 127.0.0.1, port 3333

# real hardware
# flash hardware/wireless-esp32/project-01-wifi-ir-streamer, then use the ESP32 IP
```

## What to expect

With three or more clean sessions from two or more people, a simple classifier gets clearly above
chance. Walking windows show higher derivative standard deviation, higher noise-band energy and a
higher noise ratio. Accuracy across people is lower than within one person, which is a good thing
to discuss.

## Ideas to take it further

Add a third class such as stairs or arm swing. Swap the model for a small random forest and
compare. Split train and test strictly by person and report how much accuracy drops.

## Safety

An educational biomedical-signal demo. Not a medical device, and not for diagnosis or
safety-critical use.
