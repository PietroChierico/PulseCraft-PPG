# FAQ

**Do I need hardware to try this?**
No. `tools/ppg_simulator.py` produces synthetic Red and IR PPG on TCP `127.0.0.1:3333`, exactly
like the ESP32 firmware. Every wireless project runs against it end to end.

**Which sensor should I buy?**
A MAX30102 or a MAX30105. Either one works. The 30105 adds a green LED that is unused here. Pick
a breakout with an onboard 3.3 V regulator.

**Arduino or ESP32?**
Wired Arduino is the simplest and most stable option on a lab bench. Wireless ESP32 is better for
the motion projects and for a wearable feel. Projects 02 to 05 support both. Project 01 is
wireless first.

**How much time does it take?**
Each project is a short session once the hardware or the simulator is ready. The first run took
about a week with small groups, but the projects are independent, so do one or all five at
whatever pace suits you.

**Can I keep the recordings?**
Yes, locally. Do not commit them. `.gitignore` blocks CSVs, models and output folders by
default. See `DATA_POLICY.md`.

**Is the SpO2 number in Project 04 real?**
No. It is an uncalibrated ratio-of-ratios proxy for teaching. It is not a pulse oximeter.

**Can I use a different board, a Raspberry Pi, or phone-camera PPG?**
The Python side only needs a line-based stream of numbers. Any source that sends `ir` or
`millis,red,ir` lines over serial or TCP will work. Change the host and port, or the serial port
name, in the GUI.

**Why are the models so small?**
So they train in seconds on a laptop, stay interpretable, and make overfitting on a small
dataset obvious. Swapping in a bigger model is an easy next step.

**What can I change and redistribute?**
Everything. Code is MIT, media is CC BY 4.0. Keep attribution to Pietro Chierico and cite the
repo.

**How do I cite it?**
Use `CITATION.cff`. GitHub shows a "Cite this repository" button. Add a Zenodo DOI after your
first release if you want a permanent citation.
