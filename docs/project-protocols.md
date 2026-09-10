# Project protocols

Data-collection protocols for the five projects. Each `script1_*` GUI walks the participant
through these phases automatically; phases marked *not saved* still show live so the signal can
stabilise.

## 01 — Physical activity recognition

| Phase | Duration | Saved as |
|-------|---------:|----------|
| Stabilisation | 20 s | — |
| Resting | 60 s | `Resting` (10 s windows) |
| Pause | 10 s | — |
| Walking | 60 s | `Walking` (10 s windows) |

Repeat as Record 1, 2, 3… Collect at least 3 sessions across 2+ people before training.

## 02 — Caffeine response

| Session | Structure |
|---------|-----------|
| Baseline | 15 s stabilisation + 60 s recording |
| Coffee +5 / +10 / +15 / +20 / +25 min | same, one per time point |

Analysis compares each feature against the participant's own baseline.

## 03 — Relaxation score game

| Phase | Duration | Saved |
|-------|---------:|-------|
| Stabilising baseline | 20 s | — |
| Pre-relaxation | 60 s | yes |
| Guided deep breathing | 60 s | — |
| Post-relaxation | 60 s | yes |

The score compares pre vs post feature windows.

## 04 — Voluntary-apnea biofeedback / SpO2 proxy

| Phase | Duration | Notes |
|-------|---------:|-------|
| Baseline | 30 s | normal breathing |
| Voluntary apnea | participant-controlled | **stop at any discomfort** |
| Recovery | 60 s | after the participant resumes breathing |

Paired Red + IR required. Output is an educational ratio proxy, not SpO2. Supervise; keep
breath-holds short.

## 05 — Mental stress detection

| Phase | Duration | Saved as |
|-------|---------:|----------|
| Stabilisation | 20 s | — |
| Relaxed baseline | 60 s | `Relaxed` |
| Mental arithmetic | 60 s | `Stressed` |
| Quiet recovery | 30 s | — |
| Timed reaction task | 60 s | `Stressed` |
| Cognitive interference | 60 s | `Stressed` |
| Final calm | 60 s | `Relaxed` |
