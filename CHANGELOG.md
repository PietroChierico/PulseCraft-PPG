# Changelog

The format loosely follows [Keep a Changelog](https://keepachangelog.com/). Versioning is
semantic.

## 1.0.0, 2026-09

First public release.

- Five projects (activity recognition, caffeine response, relaxation, an apnea and SpO2 proxy,
  stress detection). Each one follows the same collect, analyze and train, run live pattern, in
  wired and wireless variants.
- Arduino UNO and Adafruit Feather ESP32-C6 acquisition firmware. The ESP32 sketches stream a
  true 100 Hz (`SAMPLE_AVERAGE = 1`) to match the Python `sampling_rate_hz` default.
- Two-piece 3D-printable MAX3010x enclosure in `hardware/stl/`.
- `tools/ppg_simulator.py`, a synthetic Red and IR TCP stream so every wireless project runs
  with no hardware, with six scenario presets.
- `tools/check_setup.py`, an environment and live-stream sample-rate check.
- `docs/` covering getting started, hardware, signal processing, the signal-quality checklist,
  troubleshooting, an FAQ, a glossary and the project protocols.
- GitHub scaffolding, issue and PR templates, a Code of Conduct, `CITATION.cff`, and a CI syntax
  check.

### Notes

The firmware is checked statically only. It has not been re-tested on hardware for this release.
