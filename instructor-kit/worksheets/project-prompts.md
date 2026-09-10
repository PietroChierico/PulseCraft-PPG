# Project-specific prompts

Answer your project's questions in the report and talk. These are the "so what".

## 01 — Physical activity recognition

- Which feature family (amplitude, derivative, spectral) carries the resting/walking difference?
- Is motion artifact "noise" here, or signal? Defend your answer.
- How much does accuracy drop from within-person to cross-person? What does that imply for a
  real fitness tracker?

## 02 — Caffeine response

- For each participant, when (if ever) does the response become visible? Make one figure showing
  all participants' curves.
- Which feature responds most consistently across people?
- List three confounds you could not control and how they might explain a null result.

## 03 — Relaxation score game

- Quantify the pre→post change in your top HRV-related feature (mean ± spread).
- Can your score be gamed by simply holding still? How did you prevent that?
- How long does the relaxation effect last if you re-measure after 5 minutes?

## 04 — Voluntary-apnea biofeedback

- Sketch the ratio-of-ratios trace across baseline → hold → recovery. Where is the minimum,
  relative to when breathing resumed? Explain the lag.
- Why does a real oximeter need calibration curves that your proxy does not have?
- What safety controls did you use, and what would you add for a larger group?

## 05 — Mental stress detection

- Which stressor task produced the clearest physiological change? Which produced the least?
- How balanced were your `Relaxed` vs `Stressed` windows, and did you correct for it?
- Your model outputs "stressed". What are you *actually* entitled to claim from that?
