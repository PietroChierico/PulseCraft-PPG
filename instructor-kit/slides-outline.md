# Slides outline

Two short lectures (~30 min each) plus three mini-lectures. Build your own deck; this is the
skeleton. One idea per slide.

## Lecture A — PPG principles and physiology (slides 1–8)

1. Title — what we will build this week (show the live demo).
2. What is PPG — light in, light out, blood volume changes absorption.
3. The optical path — LED, tissue, photodiode; transmissive vs reflective.
4. AC and DC — the pulsatile arterial component on a slow baseline.
5. What you can read from it — heart rate, HRV, respiration modulation, pulse shape.
6. Red vs IR — why two wavelengths enable an oxygenation estimate (ratio of ratios).
7. Where it is used — oximeters, smartwatches, fitness bands; research vs consumer grade.
8. This kit — MAX3010x + Arduino/ESP32 + Python; the collect → analyze → live pattern.

## Lecture B — PPG challenges (slides 9–15)

9. The signal is fragile — list the enemies.
10. Motion artifact — sensor moves relative to skin; often larger than the pulse.
11. Contact pressure — too hard collapses perfusion; too loose lets light leak.
12. Ambient light and temperature.
13. Skin tone and perfusion — melanin absorbs; documented accuracy disparities in pulse oximetry;
    why this matters for fair devices.
14. Sampling and quantisation — rate, averaging, ADC range, clipping.
15. Consequence for us — why every protocol has a stabilisation phase and why we window.

## Lecture C — analysis in digital health (slides 16–24)

16. Two meanings of "analysis" — descriptive summaries vs trained algorithms.
17. Windowing — one window, one feature row.
18. Features by family — amplitude, shape/derivative, spectral, rate/variability, Red/IR ratio.
19. Reading a boxplot — overlap means weak separation.
20. A small model — logistic regression / small ensemble; why small here.
21. Train / test split — and why it must respect sessions and people.
22. Confusion matrix — the honest scoreboard.
23. Data leakage — the most common way to fool yourself.
24. Within-subject vs cross-subject — expect a drop; report it.

## Mini-lecture D — claims and limits (slides 25–30)

25. What this device is and is not (not medical).
26. Confounds specific to each project.
27. Label noise — a "stress task" is not stressful for everyone.
28. Ethics of affect/stress detection — consent, purpose, over-claiming.
29. Fairness — test across skin tones; state who your data represents.
30. How to phrase a result you are unsure about.

## Mini-lecture E — figures and storytelling (Day 5)

- One message per figure; label axes and units; show the raw data behind a summary.
- Match every claim on a slide to a figure that supports it.
- Put limitations on their own slide, not buried.
