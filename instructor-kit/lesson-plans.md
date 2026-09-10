# Lesson plans

Timings assume a 3-hour lab block. Adjust to your slot. "Checkpoint" = do not let groups move on
until this works.

---

## Day 1 — Hardware and the signal

**Goal:** every group has a working sensor node and can describe the raw waveform.

| Time | Activity |
|------|----------|
| 0:00 | Lecture: PPG principles — light absorption, AC/DC, what the pulse is. (slides 1–8) |
| 0:35 | Lecture: PPG challenges — motion, contact pressure, ambient light, skin tone, and why they matter for fairness. (slides 9–15) |
| 1:00 | Lab: wire the MAX3010x; flash the streamer sketch; confirm data on the Serial Monitor. |
| 1:40 | Lab: run `python tools/check_setup.py` then `visualize_filters.py`. Compare raw / moving-average / band-pass live. |
| 2:15 | Lab: run `tools/ppg_simulator.py` and connect a project script to it — everyone sees the no-hardware path. |
| 2:40 | Worksheet: *Signal-quality checklist*. Each group saves one annotated raw-vs-filtered screenshot. |

**Checkpoint:** live waveform visible from real hardware **and** from the simulator; band-pass
output looks like a clean pulse.

**Common problems:** 5 V instead of 3.3 V to the sensor; Serial Monitor left open; pressing the
sensor too hard. See [`../docs/troubleshooting.md`](../docs/troubleshooting.md).

---

## Day 2 — Collect a dataset

**Goal:** each group has a labeled dataset for its project.

| Time | Activity |
|------|----------|
| 0:00 | Assign projects. Demo the collect → analyze → run-live pattern on Project 01 end to end (use the simulator). |
| 0:30 | Groups read their project `README.md` and the matching protocol in [`../docs/project-protocols.md`](../docs/project-protocols.md). |
| 0:45 | Lab: run `script1_*` and complete the protocol. Repeat for 3+ sessions and 2+ people. |
| 2:15 | Groups inspect their CSV: how many windows per class? Is it balanced? Any obviously bad sessions? |
| 2:45 | Worksheet: *Data collection log* — who, when, conditions, anything unusual. |

**Checkpoint:** a CSV with ≥ 30 windows per class from ≥ 2 people, and a data collection log.

**Teaching point:** bad data now = a meaningless model on Day 3. Re-record rather than push on.

---

## Day 3 — Analyze and train

**Goal:** a trained, tested model and an honest read of it.

| Time | Activity |
|------|----------|
| 0:00 | Lecture: descriptive vs algorithmic analysis; what a feature is; how to read a boxplot and a confusion matrix. (slides 16–24) |
| 0:40 | Lab: run `script2_*`. For each feature, decide: does it separate the classes, and *why physiologically*? |
| 1:30 | Lab: choose a feature subset, train, test. Look at the confusion matrix, not just accuracy. |
| 2:10 | Leakage hunt: is any test window from the same session as a training window? Re-split by session/person and compare. |
| 2:40 | Worksheet: *Feature and model analysis*. |

**Checkpoint:** exported model file + a filled feature/model worksheet including a leakage check.

---

## Day 4 — Run live and stress-test

**Goal:** a working live demo and an understanding of when it breaks.

| Time | Activity |
|------|----------|
| 0:00 | Short lecture: limitations, what you can and cannot claim, ethics of "stress/emotion detection". (slides 25–30) |
| 0:25 | Lab: run `script3_*` live. Does it match how the participant actually feels/moves? |
| 1:10 | Break it on purpose: move the sensor, change person, loosen contact. Record what fails. |
| 1:50 | Extension task from the project README. |
| 2:30 | Worksheet: *Live evaluation and failure modes*. |

**Checkpoint:** live demo runs; group can name at least three failure modes with causes.

---

## Day 5 — Communicate

**Goal:** a clear 6–8 minute talk with honest figures.

| Time | Activity |
|------|----------|
| 0:00 | Mini-lecture: figure design, claims vs limits. |
| 0:30 | Lab: build 4–6 figures (protocol, feature boxplot, confusion matrix, live screenshot). |
| 1:30 | Rehearse in pairs of groups; peer feedback. |
| 2:00 | Presentations + feedback. |

**Deliverable:** slides, figures, code/notebook, completed worksheets. Grade with
[`assessment-rubric.md`](assessment-rubric.md).
