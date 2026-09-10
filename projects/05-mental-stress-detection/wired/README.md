# Project 05. Mental stress detection, wired workflow

This is the Arduino serial version. Flash the matching sketch from `hardware/wired-arduino/`, then close the Arduino Serial Monitor before you connect from Python. Set the COM or tty port in the GUI (in Arduino IDE, under Tools then Port).

## Run

```bash
pip install -r ../../../requirements.txt
python app_demo5_stress.py   # a launcher page with buttons for the scripts below
# or run the steps in order
python script1_stress_dataset_collection.py
python script2_stress_analysis_training_export.py
python script3_stress_live_detection_challenge.py
```

## Files

- `app_demo5_stress.py` is a small launcher page with buttons for the three scripts.
- `script1_stress_dataset_collection.py` is step 1, collect a labeled dataset with a guided protocol.
- `script2_stress_analysis_training_export.py` is step 2, look at the features, train and test a small model, then export it.
- `script3_stress_live_detection_challenge.py` is step 3, stream live and classify or score in real time.
- `arduino_serial_ppg_format_example.ino` is a reference sketch showing the serial format.
- `ppg_serial_ir_stream.py` is the stream parser and reader.
- `ppg_stress_features.py` is shared feature extraction.
- `requirements.txt` is the same list as the repo root.
- `visualize_filters.py` is a live viewer for raw against filtered signal.

## Notes

Keep the sample rate identical across collect, train and live. See `../../../docs/hardware.md`.

Do not commit recorded CSVs or trained models. `.gitignore` already blocks them.

Firmware for this version is under `hardware/wired-arduino/project-05-*`.
