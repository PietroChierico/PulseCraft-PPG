# PulseCraft PPG — an open photoplethysmography teaching kit

**Five hands-on photoplethysmography (PPG) projects that take you from raw optical sensor data to a live, AI-assisted physiological demo.**

[![License: MIT](https://img.shields.io/badge/code-MIT-blue.svg)](LICENSE)
[![Media: CC BY 4.0](https://img.shields.io/badge/media-CC%20BY%204.0-lightgrey.svg)](MEDIA-LICENSE.md)
[![checks](https://github.com/PietroChierico/PulseCraft-PPG/actions/workflows/python-syntax-check.yml/badge.svg)](https://github.com/PietroChierico/PulseCraft-PPG/actions)
[![Try without hardware](https://img.shields.io/badge/try-no%20hardware%20needed-brightgreen.svg)](tools/README.md)

PulseCraft PPG is a set of working PPG projects: Arduino and ESP32 acquisition firmware, a
3D-printable MAX3010x sensor case, Python data-collection and feature-extraction pipelines, small
machine-learning models, and live GUI demos. A built-in signal simulator lets you run every
wireless project **before any hardware arrives**.

It was designed and built end-to-end for the **Khalifa University CMHS Summer Internship
Program 2026** (Biomedical Engineering & Biotechnology track) and is released so anyone — a lab, a
course, a workshop, a summer school, or a curious individual — can pick it up and build on it.

---

## Who this is for

- **Teachers and workshop organisers** who want a set of working PPG projects to start from.
  The projects are self-contained: use one or all five, in any order, and adapt them however
  you like.
- **Students and self-learners** who want a complete, working example of the full pipeline:
  sensor → acquisition → filtering → features → model → real-time inference.
- **Researchers** who need a clean, citable baseline for PPG demos and outreach.

No prior signal-processing or embedded experience is needed. Basic Python is enough.

## The five projects

| # | Project | Physiological question | Signal | Hardware |
|---|---------|------------------------|--------|----------|
| [01](projects/01-physical-activity-recognition/) | **Physical activity recognition** | Can we tell resting from walking by the motion artifact in PPG? | IR | Wireless (ESP32) |
| [02](projects/02-caffeine-response/) | **Caffeine response** | When do caffeine-related changes become visible in PPG features? | IR | Wired or wireless |
| [03](projects/03-relaxation-score-game/) | **Relaxation score game** | How much does a 60 s breathing exercise change pulse and HRV features? | IR | Wired or wireless |
| [04](projects/04-biofeedback-spo2-apnea/) | **Voluntary-apnea biofeedback** | How do Red/IR ratios move during a short, safe breath-hold? | Red + IR | Wired or wireless |
| [05](projects/05-mental-stress-detection/) | **Mental stress detection** | Can a model separate relaxed vs. stressed from PPG features live? | IR | Wired or wireless |

Every project follows the same three steps, so the method carries over from one to the next:

1. **Collect** — a guided GUI records a fixed protocol and writes labeled feature windows to CSV.
2. **Analyze & train** — inspect feature distributions, pick features, train and test a small model, export it.
3. **Run live** — stream from the sensor (or the simulator) and see the model decide in real time.

It was first run over about a week, with small groups sharing four sensor nodes.

## What the projects cover

- How optical PPG works and why placement, pressure, skin tone, and motion change the waveform.
- Practical filtering: detrending, band-pass design, and what each filter removes (`visualize_filters.py`).
- Turning a windowed signal into interpretable features (amplitude, derivative, spectral, HRV proxies).
- Training and testing a small classifier, and reading a confusion matrix rather than trusting an accuracy number.
- Running inference on a live stream and reasoning about its failure modes.
- Responsible physiological data handling and the limits of a non-medical device.

## Quick start (no hardware)

```bash
git clone https://github.com/PietroChierico/PulseCraft-PPG.git
cd PulseCraft-PPG
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Terminal 1 — synthetic Red+IR PPG on TCP 127.0.0.1:3333 (mimics the ESP32)
python tools/ppg_simulator.py --scenario activity

# Terminal 2 — run a project against it
cd projects/01-physical-activity-recognition/wireless
python script1_dataset_collection_protocol.py     # host 127.0.0.1, port 3333
```

Then move to real hardware by following [`docs/getting-started.md`](docs/getting-started.md).

## Hardware

| Part | Example | Notes |
|------|---------|-------|
| PPG sensor | MAX30102 or MAX30105 breakout | I²C, Red + IR (+ green on 30105) |
| Wired MCU | Arduino UNO (or Nano) | USB serial at 115200 baud |
| Wireless MCU | Adafruit Feather ESP32-C6 | WiFi TCP stream, battery-powered |
| Case | `hardware/stl/` two-piece clip | Stabilises optical contact on wrist/finger |

Full bill of materials, wiring tables, diagrams, and firmware notes: [`docs/hardware.md`](docs/hardware.md).

## Repository layout

```text
PulseCraft-PPG/
├── projects/         # The 5 projects: collect → analyze/train → run live
├── hardware/         # Arduino + ESP32 firmware and the 3D-printable case
├── tools/            # ppg_simulator.py (no-hardware mode) and check_setup.py
├── docs/             # Getting started, hardware, signal processing, troubleshooting, FAQ
├── requirements.txt
├── CITATION.cff
├── LICENSE           # MIT (code)  ·  MEDIA-LICENSE.md — CC BY 4.0 (STL, photos, diagrams)
└── SAFETY.md
```

## Citing

If you use PulseCraft PPG in a course, workshop, paper, or derivative kit, please cite it via
[`CITATION.cff`](CITATION.cff) (GitHub shows a "Cite this repository" button).

## License

- **Code** — MIT ([`LICENSE`](LICENSE)).
- **STL files, photos, diagrams, and other media** — CC BY 4.0 ([`MEDIA-LICENSE.md`](MEDIA-LICENSE.md)).

Keep attribution to Pietro Chierico when reusing the code or media.

## Safety and scope

Education and research prototyping only. **Not a medical device**, not a diagnostic tool, not for
clinical decisions. Project 04 is a short, voluntary, supervised breath-hold activity — stop at any
discomfort. See [`SAFETY.md`](SAFETY.md).

## Author and acknowledgements

**Author:** Pietro Chierico · <pietrochr@gmail.com> · PhD candidate in Biomedical Engineering.
Designed and implemented end-to-end during a visiting PhD period at Khalifa University.

- Visiting supervisor, Khalifa University: **Prof. Mohamed Elgendi**
- Home PhD supervisor, Universitat Politècnica de València: **Prof. José Javier Rieta**
- Built for the **Khalifa University CMHS Summer Internship Program 2026**, Biomedical
  Engineering & Biotechnology track — *Interactive Wearable Sensing, Physiological Monitoring,
  and AI Applications*.
