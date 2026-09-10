# Project 05. Mental stress detection, wireless workflow

This is the ESP32 WiFi version. Flash the matching sketch from `hardware/wireless-esp32/`. Use host `192.168.4.1` and port `3333` in the board's Access Point mode, or the IP from the Serial Monitor in router mode. With no hardware, run `tools/ppg_simulator.py` and use host `127.0.0.1`.

## Run

```bash
pip install -r ../../../requirements.txt
python ../../../tools/ppg_simulator.py --scenario stress   # no hardware, in a separate terminal
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
- `ppg_stress_features.py` is shared feature extraction.
- `ppg_wifi_ir_stream.py` is the stream parser and reader.
- `visualize_filters.py` is a live viewer for raw against filtered signal.

## Notes

Keep the sample rate identical across collect, train and live. See `../../../docs/hardware.md`.

Do not commit recorded CSVs or trained models. `.gitignore` already blocks them.

Firmware for this version is under `hardware/wireless-esp32/project-05-*`.
