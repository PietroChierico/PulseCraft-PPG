# Changelog

Format loosely follows [Keep a Changelog](https://keepachangelog.com/). Versioning is semantic.

## [1.0.0] — 2026-09

First public release.

- Five projects (activity recognition, caffeine response, relaxation, apnea/SpO2 proxy, stress
  detection), each with the collect → analyze/train → run-live pattern, in wired and/or wireless
  variants.
- Arduino UNO and Adafruit Feather ESP32-C6 acquisition firmware; ESP32 sketches stream a true
  100 Hz (`SAMPLE_AVERAGE = 1`) to match the Python `sampling_rate_hz` default.
- Two-piece 3D-printable MAX3010x enclosure (`hardware/stl/`).
- `tools/ppg_simulator.py` — synthetic Red+IR TCP stream so every wireless project runs with no
  hardware; six scenario presets.
- `tools/check_setup.py` — environment and live-stream / sample-rate check.
- `docs/`: getting started, hardware (BOM + wiring + diagrams), signal processing, signal-quality
  checklist, troubleshooting, FAQ, glossary, project protocols.
- GitHub scaffolding: issue/PR templates, Code of Conduct, `CITATION.cff`, CI syntax check.

### Notes
- Firmware is checked statically only; it has not been re-tested on hardware for this release.
