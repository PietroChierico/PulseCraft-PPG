# Project 02 — Caffeine response (wired)

Arduino serial workflow. Flash the matching sketch from `hardware/wired-arduino/`, then **close the Arduino Serial Monitor** before connecting from Python. In the GUI, set the COM/tty port (Arduino IDE -> Tools -> Port).

## Run

```bash
pip install -r ../../../requirements.txt
python app.py                 # one-page launcher for the scripts below
# or run the steps directly, in order:
python script1_caffeine_dataset_collection_protocol.py
python script2_caffeine_analysis_export.py
python script3_caffeine_interpretation_assistant.py
```

## Files

- `app.py` — local launcher page
- `script1_caffeine_dataset_collection_protocol.py` — step 1: collect a labeled dataset (guided protocol)
- `script2_caffeine_analysis_export.py` — step 2: analyze features, train + test a model, export it
- `script3_caffeine_interpretation_assistant.py` — step 3: stream live and classify / score in real time
- `visualize_filters.py` — live raw vs filtered viewer

## Notes

- Keep the sample rate identical across collect, train, and live (see `../../../docs/hardware.md`).
- Do not commit recorded CSVs or trained models — `.gitignore` blocks them.
- Firmware for this variant: `hardware/wired-arduino/project-02-*`.
