# Project 02. Caffeine response

How long after a coffee do caffeine-related changes show up in PPG features, and how much does
that differ from one person to another?

| Item | Value |
|------|-------|
| Signal | IR PPG |
| Hardware | Wired Arduino or wireless ESP32 |
| Feature window | 10 seconds |
| Roughly how long | one session of about 40 minutes, then about 30 minutes of analysis. The recording spans roughly half an hour of real time. |
| No-hardware mode | `python tools/ppg_simulator.py --scenario caffeine` |

## How it goes

1. Collect with `script1_caffeine_dataset_collection_protocol.py`. Record a baseline, then
   sessions at +5, +10, +15, +20 and +25 minutes after the coffee. Each session is 15 seconds to
   stabilise and 60 seconds of recording, saved as 10 second feature windows tagged with the
   subject and the time point.
2. Analyze with `script2_caffeine_analysis_export.py`. Plot each feature as a change from that
   subject's baseline over time, and export summary CSVs and figures.
3. Interpret with `script3_caffeine_interpretation_assistant.py`. A GUI that helps you see when
   the response appears, which feature moves most, and how consistent it is across people.

## What you get out of it

You work against a personal baseline rather than absolute values. You have to think about
confounds like time of day, posture, temperature and whether the person has eaten, and how to
keep them under control. And you see that a well-known physiological effect can still be small,
noisy and very person-dependent.

## Run

```bash
pip install -r ../../../requirements.txt

python ../../../tools/ppg_simulator.py --scenario caffeine     # no hardware
cd wired && python app.py                                      # or  cd wireless && python app.py
```

## What to expect

Group-level trends, for example a modest shift in heart rate or pulse amplitude, usually appear
by +10 to +20 minutes. Individual curves vary a lot, and some people show almost nothing. That
variability is the point.

## Ideas to take it further

Run a blind decaf against caffeinated control. Fit the time to onset per person and compare it
with the caffeine pharmacokinetics literature.

## Safety

An educational demo. Not a medical device. Respect each participant's caffeine tolerance and
choices, and offer a decaf or no-coffee alternative.
