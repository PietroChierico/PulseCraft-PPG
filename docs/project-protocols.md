# Project protocols

The recording protocol for each of the five projects. The `script1_*` GUI walks the participant
through the phases automatically. Phases marked "not saved" still show live so the signal can
settle.

## 01. Physical activity recognition

| Phase | Duration | Saved as |
|-------|---------:|----------|
| Stabilisation | 20 s | not saved |
| Resting | 60 s | `Resting`, in 10 s windows |
| Pause | 10 s | not saved |
| Walking | 60 s | `Walking`, in 10 s windows |

Repeat as Record 1, 2, 3 and so on. Collect at least three sessions across two or more people
before training.

## 02. Caffeine response

| Session | Structure |
|---------|-----------|
| Baseline | 15 s stabilisation, then 60 s recording |
| Coffee +5, +10, +15, +20, +25 min | the same, one per time point |

The analysis compares each feature against the participant's own baseline.

## 03. Relaxation score game

| Phase | Duration | Saved |
|-------|---------:|-------|
| Stabilising baseline | 20 s | not saved |
| Pre-relaxation | 60 s | saved |
| Guided deep breathing | 60 s | not saved |
| Post-relaxation | 60 s | saved |

The score compares the pre and post feature windows.

## 04. Voluntary-apnea biofeedback and SpO2 proxy

| Phase | Duration | Notes |
|-------|---------:|-------|
| Baseline | 30 s | normal breathing |
| Voluntary apnea | participant controlled | stop at any discomfort |
| Recovery | 60 s | after the participant starts breathing again |

Paired Red and IR are required. The output is an educational ratio proxy, not SpO2. Supervise the
activity and keep the breath-holds short.

## 05. Mental stress detection

| Phase | Duration | Saved as |
|-------|---------:|----------|
| Stabilisation | 20 s | not saved |
| Relaxed baseline | 60 s | `Relaxed` |
| Mental arithmetic | 60 s | `Stressed` |
| Quiet recovery | 30 s | not saved |
| Timed reaction task | 60 s | `Stressed` |
| Cognitive interference | 60 s | `Stressed` |
| Final calm | 60 s | `Relaxed` |
