# Signal processing, in brief

This is the conceptual map. The authoritative details are in each project's
`ppg_*_features.py` / `ppg_feature_utils.py`.

## Pipeline

```text
raw counts ──▶ window (5–10 s) ──▶ detrend / band-pass ──▶ features ──▶ model ──▶ label or score
```

## 1. Windowing

The stream is cut into fixed windows (10 s for projects 01–03 and 05, 5 s rolling for the
SpO2 proxy in 04). One window → one feature row. Windows are the unit of both training and
live prediction.

## 2. Filtering

- **Detrend / high-pass (~0.5 Hz):** removes the slow baseline wander from breathing and
  perfusion drift so the pulse sits on zero.
- **Band-pass (~0.5–3 Hz / ~4 Hz):** keeps the heart-rate band, attenuates DC and high-frequency
  noise. Use `visualize_filters.py` in any project to see raw vs. filtered live and to feel what
  each filter throws away.

Filtering is deliberately simple and causal-friendly so the same ideas transfer to an embedded
or wearable context.

## 3. Features

Grouped by what they capture:

| Group | Examples | Reads as |
|-------|----------|----------|
| Amplitude / spread | mean, std, 5–95% range, IQR, detrended std | perfusion strength, gross motion |
| Shape / derivative | mean-abs derivative, derivative std, zero-crossing rate | steepness and regularity of the pulse |
| Spectral | pulse-band energy, noise-band energy, noise ratio, spectral centroid | how "clean" and where the energy sits |
| Rate / variability (03, 05) | pulse rate, inter-beat interval, HRV proxies | autonomic state |
| Red/IR ratio (04 only) | ratio-of-ratios, AC/DC per channel | oxygenation *proxy* — not calibrated SpO2 |

Features are chosen to be **interpretable**: students should be able to say *why* a feature moved,
not just that the model score changed.

## 4. Model

A small scikit-learn classifier (logistic regression / small tree ensemble depending on project).
Kept small on purpose:

- trains in seconds on a laptop with a class-sized dataset;
- the decision boundary can be inspected feature-by-feature in `script2_*`;
- forces the discussion "is this real physiology or did we learn the room?".

Always read the confusion matrix and test on a session the model never saw.

## 5. Honest limits

PPG features depend on placement, contact pressure, skin tone, ambient light, motion, and
individual physiology. Cross-subject models are weak with class-sized datasets. The SpO2 value
in Project 04 is an educational ratio proxy, **not** a validated measurement. Treat every output
as a teaching artifact.
