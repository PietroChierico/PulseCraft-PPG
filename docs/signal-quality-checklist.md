# Signal-quality checklist

Run through this before trusting any recording.

- [ ] Sensor powered from 3.3 V, not 5 V.
- [ ] Serial Monitor closed for wired, or the right host and port for wireless.
- [ ] `python tools/check_setup.py --stream <host:port>` shows about 100 Hz, or your configured rate.
- [ ] Sensor resting on the skin with light, steady contact, not pressed.
- [ ] Consistent measurement site (fingertip pad, wrist, and so on), and note which one.
- [ ] Cable and board still and supported. This matters most for Project 01.
- [ ] Not under strong direct light.
- [ ] Full stabilisation phase waited out before recording.
- [ ] Band-pass output in `visualize_filters.py` looks like a clean, regular pulse.
- [ ] No flat-topping or clipping at the top or bottom of the raw trace.

A quick sanity check. Estimate the heart rate by eye from the band-pass trace and confirm it
matches the person. If the waveform is flat, clipped or irregular, fix the setup and record
again.
