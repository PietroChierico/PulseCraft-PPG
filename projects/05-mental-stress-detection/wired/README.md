# Project 05 — Mental stress detection (wired)

Arduino serial workflow. Flash the matching sketch from `hardware/wired-arduino/`, then **close the Arduino Serial Monitor** before connecting from Python. In the GUI, set the COM/tty port (Arduino IDE -> Tools -> Port).

## Run

```bash
pip install -r ../../../requirements.txt
python app_demo5_stress.py                 # one-page launcher for the scripts below
# or run the steps directly, in order:
python script1_stress_dataset_collection.py
python script2_stress_analysis_training_export.py
python script3_stress_live_detection_challenge.py
```

## Files

- `app_demo5_stress.py` — local launcher page
- `script1_stress_dataset_collection.py` — step 1: collect a labeled dataset (guided protocol)
- `script2_stress_analysis_training_export.py` — step 2: analyze features, train + test a model, export it
- `script3_stress_live_detection_challenge.py` — step 3: stream live and classify / score in real time
- `arduino_serial_ppg_format_example.ino` — serial format reference sketch
- `ppg_serial_ir_stream.py` — stream parser / reader
- `ppg_stress_features.py` — shared feature extraction
- `requirements.txt` — same as the repo root list
- `visualize_filters.py` — live raw vs filtered viewer

## Notes

- Keep the sample rate identical across collect, train, and live (see `../../../docs/hardware.md`).
- Do not commit recorded CSVs or trained models — `.gitignore` blocks them.
- Firmware for this variant: `hardware/wired-arduino/project-05-*`.
