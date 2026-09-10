# Project 04. Voluntary-apnea biofeedback and SpO2 proxy, wireless workflow

This is the ESP32 WiFi version. Flash the matching sketch from `hardware/wireless-esp32/`. Use host `192.168.4.1` and port `3333` in the board's Access Point mode, or the IP from the Serial Monitor in router mode. With no hardware, run `tools/ppg_simulator.py` and use host `127.0.0.1`.

## Run

```bash
pip install -r ../../../requirements.txt
python ../../../tools/ppg_simulator.py --scenario apnea   # no hardware, in a separate terminal
python app_demo4_spo2_apnea.py   # a launcher page with buttons for the scripts below
# or run the steps in order
python script1_spo2_apnea_collection.py
python script2_spo2_apnea_analysis.py
python script3_spo2_apnea_interactive_challenge.py
```

## Files

- `app_demo4_spo2_apnea.py` is a small launcher page with buttons for the three scripts.
- `script1_spo2_apnea_collection.py` is step 1, collect a labeled dataset with a guided protocol.
- `script2_spo2_apnea_analysis.py` is step 2, look at the features, train and test a small model, then export it.
- `script3_spo2_apnea_interactive_challenge.py` is step 3, stream live and classify or score in real time.
- `ppg_wifi_ir_stream.py` is the stream parser and reader.
- `visualization_filter.py` is a live viewer for raw against filtered signal.

## Notes

Keep the sample rate identical across collect, train and live. See `../../../docs/hardware.md`.

Do not commit recorded CSVs or trained models. `.gitignore` already blocks them.

Firmware for this version is under `hardware/wireless-esp32/project-04-*`.
