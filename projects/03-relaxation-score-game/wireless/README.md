# Project 03 — Relaxation score game (wireless)

ESP32 WiFi TCP workflow. Flash the matching sketch from `hardware/wireless-esp32/`. Use host `192.168.4.1` + port `3333` in the board's Access-Point mode, or the IP from the Serial Monitor in router mode. For no hardware, run `tools/ppg_simulator.py` and use host `127.0.0.1`.

## Run

```bash
pip install -r ../../../requirements.txt
# no hardware: in another terminal
python ../../../tools/ppg_simulator.py --scenario relaxation
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
- `ppg_wifi_ir_stream.py` — stream parser / reader
- `visualize_filters.py` — live raw vs filtered viewer

## Notes

- Keep the sample rate identical across collect, train, and live (see `../../../docs/hardware.md`).
- Do not commit recorded CSVs or trained models — `.gitignore` blocks them.
- Firmware for this variant: `hardware/wireless-esp32/project-03-*`.
