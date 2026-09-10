# Instructor kit

Everything needed to run PulseCraft PPG as a taught lab. Adapt freely (CC BY 4.0).

## Contents

| File | Use |
|------|-----|
| [`syllabus.md`](syllabus.md) | 5-day core schedule + how to stretch to 2–3 weeks; learning outcomes; prerequisites |
| [`lesson-plans.md`](lesson-plans.md) | Session-by-session plan: timing, what to say, what students produce, checkpoints |
| [`assessment-rubric.md`](assessment-rubric.md) | Grading rubric for the group deliverable and individual understanding |
| [`slides-outline.md`](slides-outline.md) | Slide-by-slide outline for the two lectures (PPG principles; analysis in digital health) |
| [`worksheets/`](worksheets/) | Printable student worksheets — one per project + a signal-quality checklist |

## Before day 1

- **Hardware:** one sensor node per group of 2–3 (see [`../docs/hardware.md`](../docs/hardware.md)
  for the BOM). Flash and label each node. Print a case per node.
- **Software:** have students install Python 3.11+ and run
  `pip install -r requirements.txt` + `python tools/check_setup.py` *before* they arrive.
- **Dry run:** complete one full project against `tools/ppg_simulator.py` yourself. This catches
  90% of classroom problems.
- **Ethics:** decide your consent process for any recording kept beyond the session. A simple
  verbal-consent + no-identifiers policy is enough for in-class demos; see
  [`../DATA_POLICY.md`](../DATA_POLICY.md).
- **Groups:** mixed background (one comfortable with Python, one with hardware) works best.

## Delivery notes from the first run

- One week, groups of 2–3, ~3 h/day of lab time. Every group finished one project and presented.
- The simulator was added so groups blocked on hardware could keep moving — use it liberally.
- Project 01 (activity) and Project 03 (relaxation) are the most reliable first projects.
  Project 04 needs the tightest safety supervision. Project 02 needs the most wall-clock time.
