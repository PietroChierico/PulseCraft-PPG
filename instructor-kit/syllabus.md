# Syllabus

**Module:** Hands-on photoplethysmography — from optical sensor to live physiological model
**Level:** upper undergraduate / summer internship. **Format:** lab-based, groups of 2–3.
**Core length:** 5 days, ~3 h lab/day (~15 h). Scales to 2–3 weeks.

## Prerequisites

- Basic Python (run a script, edit a variable, read an error).
- No prior DSP, ML, or embedded experience assumed.

## Learning outcomes

By the end, a student can:

1. Explain how PPG works and name the physical factors that degrade it (placement, pressure,
   skin tone, ambient light, motion).
2. Acquire a physiological signal from a microcontroller over serial or WiFi.
3. Apply and justify basic filtering (detrend, band-pass) and show what each step removes.
4. Turn a windowed signal into interpretable features and reason about what each feature means.
5. Train, test, and critically evaluate a small classifier, including detecting data leakage.
6. Run a model on a live stream and describe its failure modes.
7. Handle physiological data responsibly and state the limits of a non-medical device.

## 5-day core schedule

| Day | Morning | Afternoon | Student output |
|-----|---------|-----------|----------------|
| 1 | Lecture: PPG principles & physiology. Lecture: PPG challenges (motion, pressure, noise, skin tone). | Lab: build the sensor node; stream live with `visualize_filters.py`; run the simulator. | Working node; annotated raw vs filtered screenshot. |
| 2 | Assign projects. Walk through the collect → analyze → run-live pattern on Project 01. | Lab: **collect** datasets (project protocol). | Labeled dataset CSV (kept locally). |
| 3 | Lecture: what "analysis" means in digital health (descriptive vs algorithmic); features. | Lab: **analyze & train**; feature boxplots; confusion matrix. | Trained model + feature discussion in worksheet. |
| 4 | Short lecture: reading results honestly; limitations; leakage. | Lab: **run live**; stress-test the model; extension task. | Live demo working; extension attempted. |
| 5 | Prepare figures and a 6–8 min talk. | Group presentations + feedback. | Slides, figures, notebook/scripts, worksheet. |

## Stretching to 2–3 weeks

Add, in order of value:

- **More data:** 3–5 sessions per group across 3+ people; a strict per-person train/test split.
- **Cross-subject study:** train on N people, test on a held-out person; write up the accuracy drop.
- **Second project:** each group does a contrasting project and compares methods.
- **Written report:** 4–6 pages, IMRaD, with a limitations section (use the rubric).
- **Guest topics:** wearables vs research-grade PPG; epidermal electrodes; rehabilitation sensing.

## Deliverables

- **Group:** slides, figures, the code/notebook used, and the completed worksheet.
- **Individual:** a short viva or one-page reflection demonstrating understanding of the pipeline
  and the limitations (graded with the rubric).

## Assessment weighting (suggested)

| Component | Weight |
|-----------|-------:|
| Working pipeline (collect → train → live) | 30% |
| Analysis quality & honesty (features, confusion matrix, leakage check) | 25% |
| Presentation & figures | 20% |
| Individual understanding (viva / reflection) | 15% |
| Lab practice: safety, data handling, teamwork | 10% |
