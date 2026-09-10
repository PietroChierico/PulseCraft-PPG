# Glossary

**PPG (photoplethysmography)** — measuring blood-volume changes in tissue from how much light a
skin site absorbs/reflects over time. The pulsatile part tracks the heartbeat.

**IR / Red channel** — the two LEDs on a MAX3010x. IR alone is enough for pulse-shape work; the
Red/IR pair is used for oxygenation proxies.

**AC / DC components** — DC is the slowly varying baseline (tissue, venous blood); AC is the
pulsatile component from arterial pulsation.

**Motion artifact** — signal corruption from the sensor moving relative to skin; dominates
Project 01.

**Detrending / high-pass filter** — removing the slow baseline so the pulse is centred on zero.

**Band-pass filter** — keeping only a frequency band (here ~0.5–3 Hz, the heart-rate range).

**Feature window** — a fixed-length slice of signal (5–10 s) summarised into a row of numbers.

**Feature** — one number describing a window (e.g. spectral centroid, derivative std).

**HRV (heart-rate variability)** — beat-to-beat timing variation; a proxy for autonomic balance.

**Ratio of ratios** — `(AC_red/DC_red) / (AC_ir/DC_ir)`; the quantity a pulse oximeter calibrates
into SpO2. Uncalibrated here.

**SpO2** — peripheral blood oxygen saturation. Project 04 outputs a *proxy*, not a measurement.

**Confusion matrix** — table of predicted vs. true labels; the honest way to read classifier
performance.

**Leakage** — when information from the test set sneaks into training (e.g. same recording
session on both sides), inflating accuracy.

**Access Point (AP) mode** — the ESP32 makes its own WiFi network instead of joining a router.

**Sampling rate** — samples per second. Must be identical across collection, training, and live
inference.
