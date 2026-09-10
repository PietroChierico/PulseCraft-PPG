# Project 04. Voluntary-apnea biofeedback and SpO2 proxy

How do the Red and IR PPG amplitudes, and their ratio, move during a short, safe, voluntary
breath-hold, and what does that tell us about how a pulse oximeter works?

> Safety first. This is a short, voluntary, supervised activity. The participant controls the
> breath-hold and stops at the first sign of discomfort. Never push a breath-hold. The SpO2
> number is an uncalibrated educational proxy, not a measurement.

| Item | Value |
|------|-------|
| Signal | Red and IR PPG, both channels are required |
| Hardware | Wired Arduino or wireless ESP32, dual-channel sketch |
| Window | 5 second rolling Red and IR ratio windows inside a full-trial CSV |
| Roughly how long | about 20 minutes per participant |
| No-hardware mode | `python tools/ppg_simulator.py --scenario apnea` |

## How it goes

1. Collect with `script1_spo2_apnea_collection.py`. The phases are 30 seconds of baseline, a
   voluntary apnea that the participant starts, then 60 seconds of recovery. Red and IR are
   recorded together.
2. Analyze with `script2_spo2_apnea_analysis.py`. Compute AC over DC for each channel and the
   ratio of ratios, then plot how it drifts during the hold and recovers afterward.
3. Challenge with `script3_spo2_apnea_interactive_challenge.py`. A live biofeedback view of the
   ratio and a proxy trend during a supervised hold.

## What you get out of it

You see why oximetry needs two wavelengths and uses `(AC/DC)_red / (AC/DC)_ir`, what a real
device calibrates with empirical curves and why this proxy is not that, and the physiological
lag, since the ratio keeps drifting for several seconds after breathing resumes.

## Run

```bash
pip install -r ../../../requirements.txt

python ../../../tools/ppg_simulator.py --scenario apnea
cd wired && python app_demo4_spo2_apnea.py                     # or  cd wireless && python app_demo4_spo2_apnea.py
```

Flash the red and ir sketch under `hardware/*/project-04-*red-ir*`.

## What to expect

During a 20 to 30 second hold the ratio of ratios shifts slightly and the proxy trends downward,
then overshoots and recovers over 30 to 60 seconds. The magnitudes vary and are not clinically
meaningful.

## Ideas to take it further

Compare finger against wrist placement. Add a simple two-point linear calibration against a real
fingertip oximeter, clearly labeled as a classroom exercise.

## Safety

See the box above and [../../SAFETY.md](../../SAFETY.md). Stop at once on dizziness, pain,
anxiety or shortness of breath. Not for anyone with a relevant cardiovascular or respiratory
condition.
