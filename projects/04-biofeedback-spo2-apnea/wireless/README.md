# Project 04 — Voluntary-apnea biofeedback + SpO2 proxy (wireless)

ESP32 WiFi TCP workflow. Flash the matching sketch from `hardware/wireless-esp32/`. Use host `192.168.4.1` + port `3333` in the board's Access-Point mode, or the IP from the Serial Monitor in router mode. For no hardware, run `tools/ppg_simulator.py` and use host `127.0.0.1`.

## Run

```bash
pip install -r ../../../requirements.txt
# no hardware: in another terminal
python ../../../tools/ppg_simulator.py --scenario apnea
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
- `ppg_wifi_ir_stream.py` — stream parser / reader
- `visualization_filter.py` — live raw vs filtered viewer

## Notes

- Keep the sample rate identical across collect, train, and live (see `../../../docs/hardware.md`).
- Do not commit recorded CSVs or trained models — `.gitignore` blocks them.
- Firmware for this variant: `hardware/wireless-esp32/project-04-*`.
