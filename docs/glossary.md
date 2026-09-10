# Glossary

**PPG (photoplethysmography).** Measuring blood-volume changes in tissue from how much light a
skin site absorbs or reflects over time. The pulsatile part tracks the heartbeat.

**IR and Red channels.** The two LEDs on a MAX3010x. IR alone is enough for pulse-shape work.
The Red and IR pair together is used for oxygenation proxies.

**AC and DC components.** DC is the slowly varying baseline from tissue and venous blood. AC is
the pulsatile component from arterial pulsation.

**Motion artifact.** Signal corruption from the sensor moving against the skin. It dominates
Project 01.

**Detrending, or high-pass filter.** Removing the slow baseline so the pulse is centred on zero.

**Band-pass filter.** Keeping only a frequency band, here about 0.5 to 3 Hz, the heart-rate range.

**Feature window.** A fixed-length slice of signal, 5 to 10 seconds, summarised into a row of
numbers.

**Feature.** One number describing a window, for example spectral centroid or derivative
standard deviation.

**HRV (heart-rate variability).** Beat-to-beat timing variation, a proxy for autonomic balance.

**Ratio of ratios.** `(AC_red/DC_red) / (AC_ir/DC_ir)`, the quantity a pulse oximeter calibrates
into SpO2. It is left uncalibrated here.

**SpO2.** Peripheral blood oxygen saturation. Project 04 outputs a proxy, not a measurement.

**Confusion matrix.** A table of predicted against true labels, the honest way to read classifier
performance.

**Leakage.** When information from the test set reaches training, for example the same recording
session on both sides, which inflates accuracy.

**Access Point (AP) mode.** The ESP32 makes its own WiFi network instead of joining a router.

**Sampling rate.** Samples per second. It must be identical across collection, training and live
inference.
