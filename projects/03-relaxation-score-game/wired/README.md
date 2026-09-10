# Project 03 — Relaxation score game (wired)

Arduino serial workflow. Flash the matching sketch from `hardware/wired-arduino/`, then **close the Arduino Serial Monitor** before connecting from Python. In the GUI, set the COM/tty port (Arduino IDE -> Tools -> Port).

## Run

```bash
pip install -r ../../../requirements.txt
python app_demo3_relaxation.py                 # one-page launcher for the scripts below
# or run the steps directly, in order:
python script1_relaxation_dataset_collection.py
python script2_relaxation_analysis_training_export.py
python script3_relaxation_live_score_game.py
```

## Files

- `app_demo3_relaxation.py` — local launcher page
- `script1_relaxation_dataset_collection.py` — step 1: collect a labeled dataset (guided protocol)
- `script2_relaxation_analysis_training_export.py` — step 2: analyze features, train + test a model, export it
- `script3_relaxation_live_score_game.py` — step 3: stream live and classify / score in real time
- `visualize_filters.py` — live raw vs filtered viewer

## Notes

- Keep the sample rate identical across collect, train, and live (see `../../../docs/hardware.md`).
- Do not commit recorded CSVs or trained models — `.gitignore` blocks them.
- Firmware for this variant: `hardware/wired-arduino/project-03-*`.
