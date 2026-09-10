# Worksheet 2 — Feature and model analysis

Group: _______________  Project: ______

## Features

Pick the 4 features that best separate your classes (from the `script2_*` boxplots).

| Feature | Which class is higher? | Why, physiologically? | Separation: strong / weak |
|---------|------------------------|-----------------------|---------------------------|
| | | | |
| | | | |
| | | | |
| | | | |

One feature that looks useful but is probably a **confound** (e.g. just encodes LED brightness or
which person it is): ____________________  — why: ____________________

## Model

- Model type: ______________  ·  Features used: ______________
- Train windows: ______  Test windows: ______
- **Split method:** ☐ random ☐ by session ☐ by person  ← which, and why?

## Confusion matrix

|                | pred A | pred B |
|----------------|:------:|:------:|
| **true A** | | |
| **true B** | | |

- Accuracy: ______%  ·  Where does it fail most? ______________
- Re-split by person/session — new accuracy: ______%  ·  Change: ______
- Is any test window from the same recording as a training window? ☐ no ☐ yes → fixed how?

## One-sentence honest conclusion

_______________________________________________________________________________
