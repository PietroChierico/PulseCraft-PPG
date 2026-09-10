# Troubleshooting

## Setup

| Symptom | Cause | Fix |
|---------|-------|-----|
| `check_setup.py` reports missing packages | venv not active or deps not installed | `pip install -r requirements.txt` inside the activated venv |
| `MAX3010x not found` on Serial Monitor | wiring / power | Check SDA↔SDA, SCL↔SCL, VIN→3.3 V (not 5 V), solid GND. Try the other I²C connector on the breakout. |
| Arduino uploads but no data | Serial Monitor baud ≠ 115200 | Set 115200, or just close it and connect from Python |

## Connection

| Symptom | Cause | Fix |
|---------|-------|-----|
| Python can't open the COM/tty port | Arduino Serial Monitor still open, or wrong port | Close the Monitor; pick the port shown in Arduino IDE → Tools → Port |
| Wireless: connection refused / timeout | wrong host or port, or not on the board's network | AP mode: join `PPG_STREAM_groupN`, host `192.168.4.1`, port `3333`. Router mode: use the IP from Serial Monitor. |
| Wireless drops after a few seconds | weak WiFi, board brown-out on battery | Move closer; use a charged battery or USB; lower `LED_BRIGHTNESS` |
| `tools/check_setup.py --stream ...` shows ~25 Hz | ESP32 sketch `SAMPLE_AVERAGE = 4` | Set it to `1`, or set `sampling_rate_hz = 25.0` in the project config |

## Signal quality

| Symptom | Cause | Fix |
|---------|-------|-----|
| Flat or tiny waveform | poor contact, or pressing too hard | Rest the sensor lightly; fingertip pad gives the strongest signal |
| Waveform clips at top/bottom | `LED_BRIGHTNESS` / `ADC_RANGE` | Lower brightness, or raise ADC range in the sketch |
| Huge low-frequency swings | breathing / hand movement | Wait out the 15–20 s stabilisation; keep the hand still; use the case + strap |
| Live classifier flips constantly | sample-rate mismatch, or trained on too little data | Re-collect at the real rate; collect more sessions; check the confusion matrix in `script2_*` |

## Analysis / training

| Symptom | Cause | Fix |
|---------|-------|-----|
| `script2` finds no CSV | ran from the wrong folder, or `script1` never saved | Run from the project's `wired/` or `wireless/` folder; complete a full protocol in `script1` |
| Model accuracy ~100% | leakage: same session in train and test, or a trivial feature | Split by session; drop `raw_mean`-type features that just encode brightness |
| GUI won't start on Linux | missing Qt platform libs | `sudo apt install libxcb-cursor0 libxkbcommon-x11-0` (or run the simulator + scripts headless where supported) |

Still stuck? Open an issue with: OS, Python version, wired/wireless, the exact command, and the
full error text. Template: `.github/ISSUE_TEMPLATE/`.
