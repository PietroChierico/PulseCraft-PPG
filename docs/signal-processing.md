# Signal processing, in brief

This is the conceptual map. The exact details are in each project's `ppg_*_features.py` or
`ppg_feature_utils.py`.

## Pipeline

Raw counts become a window of 5 to 10 seconds. The window is detrended and band-passed, then
turned into features. A small model maps the features to a label or a score.

## 1. Windowing

The stream is cut into fixed windows, 10 seconds for projects 01 to 03 and 05, and a 5 second
rolling window for the SpO2 proxy in 04. One window makes one feature row. The window is the
unit of both training and live prediction.

## 2. Filtering

A high-pass around 0.5 Hz removes the slow baseline wander from breathing and perfusion drift, so
the pulse sits on zero. A band-pass of roughly 0.5 to 3 or 4 Hz keeps the heart-rate band and
attenuates DC and high-frequency noise. Run `visualize_filters.py` in any project to see raw
against filtered, live, and get a feel for what each filter throws away.

The filtering is kept simple and causal-friendly so the same ideas carry over to an embedded or
wearable context.

## 3. Features

| Group | Examples | Reads as |
|-------|----------|----------|
| Amplitude and spread | mean, std, 5 to 95 percent range, IQR, detrended std | perfusion strength, gross motion |
| Shape and derivative | mean absolute derivative, derivative std, zero-crossing rate | steepness and regularity of the pulse |
| Spectral | pulse-band energy, noise-band energy, noise ratio, spectral centroid | how clean the signal is and where its energy sits |
| Rate and variability (03, 05) | pulse rate, inter-beat interval, HRV proxies | autonomic state |
| Red and IR ratio (04 only) | ratio of ratios, AC over DC per channel | oxygenation proxy, not calibrated SpO2 |

The features are chosen to be interpretable. You should be able to say why a feature moved, not
just that the model score changed.

## 4. Model

A small scikit-learn classifier, either logistic regression or a small tree ensemble depending
on the project. It is kept small on purpose. It trains in seconds on a class-sized dataset, the
decision boundary can be inspected feature by feature in `script2_*`, and its size forces the
question of whether a result is real physiology or just the room.

Always read the confusion matrix, and test on a session the model never saw.

## 5. Honest limits

PPG features depend on placement, contact pressure, skin tone, ambient light, motion and
individual physiology. Cross-subject models are weak with small datasets. The SpO2 value in
Project 04 is an educational ratio proxy, not a validated measurement. Treat every output as a
teaching artifact.
