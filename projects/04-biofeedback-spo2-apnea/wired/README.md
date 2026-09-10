# Project 04 — Voluntary-apnea biofeedback + SpO2 proxy (wired)

Arduino serial workflow. Flash the matching sketch from `hardware/wired-arduino/`, then **close the Arduino Serial Monitor** before connecting from Python. In the GUI, set the COM/tty port (Arduino IDE -> Tools -> Port).

## Run

```bash
pip install -r ../../../requirements.txt
python app_demo4_spo2_apnea.py                 # one-page launcher for the scripts below
# or run the steps directly, in order:
python script1_spo2_apnea_collection.py
python script2_spo2_apnea_analysis.py
python script3_spo2_apnea_interactive_challenge.py
```

## Files

- `app_demo4_spo2_apnea.py` — local launcher page
- `script1_spo2_apnea_collection.py` — step 1: collect a labeled dataset (guided protocol)
- `script2_spo2_apnea_analysis.py` — step 2: analyze features, train + test a model, export it
- `script3_spo2_apnea_interactive_challenge.py` — step 3: stream live and classify / score in real time
- `visualization_filter.py` — live raw vs filtered viewer

## Notes

- Keep the sample rate identical across collect, train, and live (see `../../../docs/hardware.md`).
- Do not commit recorded CSVs or trained models — `.gitignore` blocks them.
- Firmware for this variant: `hardware/wired-arduino/project-04-*`.
