# Project 01 — Physical activity recognition (wireless)

ESP32 WiFi TCP workflow. Flash the matching sketch from `hardware/wireless-esp32/`. Use host `192.168.4.1` + port `3333` in the board's Access-Point mode, or the IP from the Serial Monitor in router mode. For no hardware, run `tools/ppg_simulator.py` and use host `127.0.0.1`.

## Run

```bash
pip install -r ../../../requirements.txt
# no hardware: in another terminal
python ../../../tools/ppg_simulator.py --scenario activity
# or run the steps directly, in order:
python script1_dataset_collection_protocol.py
python script2_analysis_training_export.py
python script3_live_classification.py
```

## Files

- `script1_dataset_collection_protocol.py` — step 1: collect a labeled dataset (guided protocol)
- `script2_analysis_training_export.py` — step 2: analyze features, train + test a model, export it
- `script3_live_classification.py` — step 3: stream live and classify / score in real time
- `Main_page.py` — local launcher page (buttons for the three scripts)
- `demo_1.py` — standalone live raw/filtered viewer
- `ppg_feature_utils.py` — shared feature extraction

## Notes

- Keep the sample rate identical across collect, train, and live (see `../../../docs/hardware.md`).
- Do not commit recorded CSVs or trained models — `.gitignore` blocks them.
- Firmware for this variant: `hardware/wireless-esp32/project-01-*`.
