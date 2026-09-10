# Changelog

All notable changes to this project are documented here. Format loosely follows
[Keep a Changelog](https://keepachangelog.com/). Versioning is semantic.

## [1.0.0] — 2026-09

First public release.

### Added
- Five projects (activity, caffeine, relaxation, apnea/SpO2 proxy, stress), each with the
  collect → analyze/train → run-live pattern, in wired and/or wireless variants.
- Arduino UNO and Adafruit Feather ESP32-C6 acquisition firmware.
- Two-piece 3D-printable MAX3010x enclosure (`hardware/stl/`).
- `tools/ppg_simulator.py` — synthetic Red+IR TCP stream so every wireless project runs with no
  hardware; five scenario presets.
- `tools/check_setup.py` — environment and live-stream / sample-rate check.
- `docs/`: getting started, hardware (BOM + wiring + diagrams), signal processing, troubleshooting,
  FAQ, glossary, project protocols.
- `instructor-kit/`: syllabus, per-session lesson plans, grading rubric, slide outline, printable
  student worksheets.
- GitHub scaffolding: issue/PR templates, Code of Conduct, `CITATION.cff`, CI syntax check.

### Changed
- ESP32 sketches now use `SAMPLE_AVERAGE = 1` for a true 100 Hz output that matches the Python
  `sampling_rate_hz` default (previously 4 → effective 25 Hz).
- Project READMEs rewritten (learning goals, expected results, extensions); documentation and
  instructor kit added.

### Notes
- Firmware is checked statically only; it has not been re-tested on hardware for this release.
