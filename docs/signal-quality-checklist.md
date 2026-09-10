# Signal-quality checklist

Run through this before trusting any recording.

- [ ] Sensor powered from **3.3 V** (not 5 V).
- [ ] Serial Monitor closed (wired) / correct host + port (wireless).
- [ ] `python tools/check_setup.py --stream <host:port>` shows **~100 Hz** (or your configured rate).
- [ ] Sensor rests on the skin with **light, steady** contact — not pressed.
- [ ] Consistent measurement site (fingertip pad, wrist, …) — and note which one.
- [ ] Cable/board is still and supported (matters most for Project 01).
- [ ] Not under strong direct light.
- [ ] Waited out the full stabilisation phase before recording.
- [ ] Band-pass output in `visualize_filters.py` looks like a clean, regular pulse.
- [ ] No flat-topping / clipping at the top or bottom of the raw trace.

A quick sanity check: estimate the heart rate by eye from the band-pass trace and confirm it
matches the person. If the waveform is flat, clipped, or irregular, fix the setup and re-record.
