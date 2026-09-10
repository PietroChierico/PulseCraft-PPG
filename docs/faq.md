# FAQ

**Do I need hardware to try this?**
No. `tools/ppg_simulator.py` emits synthetic Red+IR PPG on TCP `127.0.0.1:3333`, exactly like the
ESP32 firmware. Every wireless project runs end-to-end against it.

**Which sensor should I buy?**
MAX30102 or MAX30105 — either works. The MAX30105 adds a green LED (unused here). Choose a
breakout with an onboard 3.3 V regulator.

**Arduino or ESP32?**
Wired Arduino is simplest and most stable for a controlled lab bench. Wireless ESP32 is better for
motion projects and a "wearable" feel. Projects 02–05 support both; Project 01 is wireless-first.

**How long is the lab?**
One week with groups of 2–3 (the original delivery). It stretches to 2–3 weeks by adding more
data collection, cross-subject analysis, and a written report. See `instructor-kit/syllabus.md`.

**Can students keep their recordings?**
Yes, locally. Do **not** commit them. `.gitignore` blocks CSVs, models, and output folders by
default. See `DATA_POLICY.md`.

**Is the SpO2 number in Project 04 real?**
No. It is an uncalibrated ratio-of-ratios *proxy* for teaching. It is not a pulse oximeter.

**Can I use a different board / a Raspberry Pi / phone camera PPG?**
The Python side only needs a line-based stream of numbers. Any source that emits `ir` or
`millis,red,ir` lines over serial or TCP will work. Update the host/port or port name in the GUI.

**Why are the models so small?**
So they train in seconds, stay interpretable, and make students confront overfitting on
class-sized data. Swapping in a bigger model is a good extension exercise.

**What can I change and redistribute?**
Everything. Code is MIT, media is CC BY 4.0. Keep attribution to Pietro Chierico and cite the repo.

**How do I cite it?**
Use `CITATION.cff` — GitHub renders a "Cite this repository" button. Add a Zenodo DOI after your
first release if you want a permanent citation.
