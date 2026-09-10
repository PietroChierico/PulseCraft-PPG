# Assessment rubric

Score each row 0–3. Suggested weights in brackets. Adapt to your grading scale.

| Criterion | 0 — missing | 1 — partial | 2 — solid | 3 — excellent |
|-----------|-------------|-------------|-----------|---------------|
| **Working pipeline** [30%] | Pipeline does not run | One stage works | Collect → train → live all run on their data | Runs cleanly; handles a bad stream / edge case gracefully |
| **Data collection** [10%] | No dataset or no log | Dataset exists, thin or undocumented | Balanced, ≥ 2 people, logged conditions | Multiple sessions, per-person split planned, anomalies noted |
| **Feature analysis** [15%] | No feature reasoning | Lists features without meaning | Explains what key features measure physiologically | Links feature shifts to the specific physiology of their project |
| **Model evaluation** [15%] | Accuracy only, or none | Reports accuracy + confusion matrix | Checks for leakage; tests on unseen session | Quantifies within- vs cross-subject gap and explains it |
| **Limitations & ethics** [10%] | None stated | Generic disclaimer | Names concrete confounds and scope limits | Nuanced: fairness (skin tone), label noise, over-claiming |
| **Presentation & figures** [15%] | Unclear | Figures present but hard to read | Clean, labeled, honest figures; clear narrative | Figures make the argument on their own; claims matched to evidence |
| **Individual understanding** [5%] | Cannot explain their pipeline | Explains one part | Walks through the whole pipeline | Explains design choices and what they would do with more time |

**Automatic cap:** any unsafe Project 04 practice, or committing participant data to a public repo,
caps the lab-practice component at 0 and triggers a debrief.

## Individual viva prompts (pick 2–3)

- Point to where in your code the signal gets filtered. What does that filter remove?
- Your accuracy is X%. Show me the confusion matrix — where does it fail, and why?
- If I put the sensor on a new person right now, what happens to your model? Why?
- What is one thing in your result you are *not* sure about?
- Is the Project 04 SpO2 number a measurement? Explain.
