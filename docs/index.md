# PulseCraft PPG

An open set of photoplethysmography (PPG) projects that go from a raw optical sensor to a live,
AI-assisted physiological demo.

Arduino and ESP32 acquisition firmware, a 3D-printable MAX3010x case, Python code for recording
data and extracting features, small machine-learning models, live GUI demos, and a signal
simulator so you can run everything before any hardware arrives.

Code is at <https://github.com/PietroChierico/PulseCraft-PPG>.

Start with [Getting started](getting-started.md). See also [Hardware](hardware.md),
[Signal processing](signal-processing.md),
[Signal-quality checklist](signal-quality-checklist.md),
[Troubleshooting](troubleshooting.md), [FAQ](faq.md) and [Glossary](glossary.md).

## Projects

| # | Project | Signal | Hardware |
|---|---------|--------|----------|
| 01 | Physical activity recognition (resting vs walking) | IR | Wireless |
| 02 | Caffeine response over time | IR | Wired or wireless |
| 03 | Relaxation score game (breathing) | IR | Wired or wireless |
| 04 | Voluntary-apnea biofeedback with a SpO2 proxy | Red + IR | Wired or wireless |
| 05 | Mental stress detection (live classifier) | IR | Wired or wireless |

See [Project protocols](project-protocols.md) for the recording steps.

## Attribution

Designed and built by **Pietro Chierico** during a visiting PhD period at **Khalifa University**.
Visiting supervisor at Khalifa University, **Prof. Mohamed Elgendi**. Home PhD supervisor at
Universitat Politècnica de València, **Prof. José Javier Rieta**. Built for the **CMHS Summer
Internship Program 2026**, in the Biomedical Engineering and Biotechnology track.

For education and research only. Not a medical device.
