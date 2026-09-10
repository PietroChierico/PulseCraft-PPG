# PulseCraft PPG

An open set of photoplethysmography (PPG) projects that go from a raw optical sensor to a live,
AI-assisted physiological demo. Five small projects, released so anyone can pick them up and
adapt them.

[![License MIT](https://img.shields.io/badge/code-MIT-blue.svg)](LICENSE)
[![Media CC BY 4.0](https://img.shields.io/badge/media-CC%20BY%204.0-lightgrey.svg)](MEDIA-LICENSE.md)
[![checks](https://github.com/PietroChierico/PulseCraft-PPG/actions/workflows/python-syntax-check.yml/badge.svg)](https://github.com/PietroChierico/PulseCraft-PPG/actions)
[![no hardware needed](https://img.shields.io/badge/try-no%20hardware%20needed-brightgreen.svg)](tools/README.md)

Each project comes with Arduino and ESP32 acquisition firmware, a 3D-printable case for the
MAX3010x sensor, Python code for recording data and extracting features, a small machine-learning
model, and a live GUI demo. A built-in signal simulator lets you run any of the wireless projects
with no hardware at all.

It was built end to end for the Khalifa University CMHS Summer Internship Program 2026, in the
Biomedical Engineering and Biotechnology track, and is free to reuse and adapt.

## The five projects

| # | Project | Question | Signal | Hardware |
|---|---------|----------|--------|----------|
| [01](projects/01-physical-activity-recognition/) | Physical activity recognition | Can we tell resting from walking by the motion artifact in PPG? | IR | Wireless (ESP32) |
| [02](projects/02-caffeine-response/) | Caffeine response | When do caffeine-related changes show up in PPG features? | IR | Wired or wireless |
| [03](projects/03-relaxation-score-game/) | Relaxation score game | How much does a 60 s breathing exercise change pulse and HRV features? | IR | Wired or wireless |
| [04](projects/04-biofeedback-spo2-apnea/) | Voluntary-apnea biofeedback | How do the Red and IR amplitudes move during a short, safe breath-hold? | Red + IR | Wired or wireless |
| [05](projects/05-mental-stress-detection/) | Mental stress detection | Can a model separate relaxed from stressed live? | IR | Wired or wireless |

Every project works the same way. You record a fixed protocol with a guided GUI, then you look at
the features and train a small model, then you run that model live on a fresh stream. Learn it
once and the other four have the same shape.

It was first run over about a week, with small groups sharing four sensor nodes.

## What you work through

- How optical PPG works, and why contact, pressure, skin tone and movement change the waveform.
- Basic filtering (detrending and band-pass) and what each step removes, with `visualize_filters.py`.
- Turning a windowed signal into features you can actually interpret.
- Training a small classifier and reading a confusion matrix instead of trusting one accuracy number.
- Running that model on a live signal and seeing where it breaks.
- Handling physiological data responsibly, and the limits of a non-medical device.

## Quick start without hardware

```bash
git clone https://github.com/PietroChierico/PulseCraft-PPG.git
cd PulseCraft-PPG
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Start the simulator in one terminal. It behaves exactly like the ESP32 firmware, streaming
`millis,red,ir` over TCP on `127.0.0.1:3333`.

```bash
python tools/ppg_simulator.py --scenario activity
```

Run a project against it in a second terminal. When it asks for a host and port, use `127.0.0.1`
and `3333`.

```bash
cd projects/01-physical-activity-recognition/wireless
python script1_dataset_collection_protocol.py
```

For real hardware, follow [docs/getting-started.md](docs/getting-started.md).

## Hardware

| Part | Example | Notes |
|------|---------|-------|
| PPG sensor | MAX30102 or MAX30105 breakout | I²C, Red and IR (plus green on the 30105) |
| Wired MCU | Arduino UNO or Nano | USB serial at 115200 baud |
| Wireless MCU | Adafruit Feather ESP32-C6 | WiFi TCP stream, runs on a battery |
| Case | `hardware/stl/` two-piece clip | Keeps the optical contact steady on a wrist or finger |

The full parts list, wiring tables, diagrams and firmware notes are in
[docs/hardware.md](docs/hardware.md).

## What is in the repo

```text
PulseCraft-PPG/
├── projects/     The five projects, each with collect, analyze/train and run-live steps
├── hardware/     Arduino and ESP32 firmware, and the 3D-printable case
├── tools/        ppg_simulator.py for the no-hardware mode, and check_setup.py
├── docs/         Getting started, hardware, signal processing, troubleshooting, FAQ
├── requirements.txt
├── CITATION.cff
├── LICENSE       MIT for code. MEDIA-LICENSE.md is CC BY 4.0 for the STL, photos and diagrams
└── SAFETY.md
```

## Citing

If you use PulseCraft PPG in a course, a workshop, a paper or another kit, please cite it with
[CITATION.cff](CITATION.cff). GitHub shows a "Cite this repository" button.

## License

Code is MIT ([LICENSE](LICENSE)). The STL files, photos and diagrams are CC BY 4.0
([MEDIA-LICENSE.md](MEDIA-LICENSE.md)). Keep attribution to Pietro Chierico when you reuse the
code or the media.

## Safety

For education and research prototyping. It is not a medical device, not a diagnostic tool, and
not for clinical decisions. Project 04 is a short, voluntary, supervised breath-hold and should be
stopped at any discomfort. See [SAFETY.md](SAFETY.md).

## Author

Pietro Chierico, PhD candidate in Biomedical Engineering. Built end to end during a visiting PhD
period at Khalifa University.

Visiting supervisor at Khalifa University, Prof. Mohamed Elgendi. Home PhD supervisor at
Universitat Politècnica de València, Prof. José Javier Rieta. Built for the CMHS Summer Internship
Program 2026, in the Biomedical Engineering and Biotechnology track.
