# Signal-quality checklist

Group: _______________  Node ID: ______  Date/time: ______________

Run through this before you trust any recording.

- [ ] Sensor powered from **3.3 V** (not 5 V).
- [ ] Serial Monitor closed (wired) / correct host + port (wireless).
- [ ] `python tools/check_setup.py --stream <host:port>` shows **~100 Hz** (or your configured rate).
- [ ] Sensor rests on the skin with **light, steady** contact — not pressed.
- [ ] Site chosen and recorded: ☐ fingertip pad ☐ wrist ☐ other: ______
- [ ] Cable/board is still and supported (critical for Project 01).
- [ ] Not under strong direct light.
- [ ] Waited the full stabilisation phase before recording.
- [ ] Band-pass output in `visualize_filters.py` looks like a clean, regular pulse.
- [ ] No flat-topping / clipping at the top or bottom of the raw trace.

**Attach:** one screenshot of raw vs band-pass, annotated with the heart rate you estimate by eye.

Estimated heart rate by eye: ______ bpm  ·  Looks clean? ☐ yes ☐ borderline ☐ re-record
