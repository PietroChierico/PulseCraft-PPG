# Project 02. Caffeine response, wired workflow

This is the Arduino serial version. Flash the matching sketch from `hardware/wired-arduino/`, then close the Arduino Serial Monitor before you connect from Python. Set the COM or tty port in the GUI (in Arduino IDE, under Tools then Port).

## Run

```bash
pip install -r ../../../requirements.txt
python app.py   # a launcher page with buttons for the scripts below
# or run the steps in order
python script1_caffeine_dataset_collection_protocol.py
python script2_caffeine_analysis_export.py
python script3_caffeine_interpretation_assistant.py
```

## Files

- `app.py` is a small launcher page with buttons for the three scripts.
- `script1_caffeine_dataset_collection_protocol.py` is step 1, collect a labeled dataset with a guided protocol.
- `script2_caffeine_analysis_export.py` is step 2, look at the features, train and test a small model, then export it.
- `script3_caffeine_interpretation_assistant.py` is step 3, stream live and classify or score in real time.
- `visualize_filters.py` is a live viewer for raw against filtered signal.

## Notes

Keep the sample rate identical across collect, train and live. See `../../../docs/hardware.md`.

Do not commit recorded CSVs or trained models. `.gitignore` already blocks them.

Firmware for this version is under `hardware/wired-arduino/project-02-*`.
