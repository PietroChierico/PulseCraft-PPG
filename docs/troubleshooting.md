# Troubleshooting

## Setup

| Symptom | Cause | Fix |
|---------|-------|-----|
| `check_setup.py` reports missing packages | venv not active, or dependencies not installed | Run `pip install -r requirements.txt` inside the activated venv |
| `MAX3010x not found` on the Serial Monitor | wiring or power | Check SDA to SDA, SCL to SCL, VIN to 3.3 V and not 5 V, and a solid GND. Try the other I²C connector on the breakout. |
| Arduino uploads but no data appears | Serial Monitor baud is not 115200 | Set it to 115200, or just close it and connect from Python |

## Connection

| Symptom | Cause | Fix |
|---------|-------|-----|
| Python cannot open the COM or tty port | Arduino Serial Monitor still open, or wrong port | Close the Monitor, then pick the port shown in Arduino IDE under Tools, Port |
| Wireless connection refused or times out | wrong host or port, or not on the board's network | In AP mode join `PPG_STREAM_groupN`, host `192.168.4.1`, port `3333`. In router mode use the IP from the Serial Monitor. |
| Wireless drops after a few seconds | weak WiFi, or the board browns out on battery | Move closer, use a charged battery or USB, and lower `LED_BRIGHTNESS` |
| `tools/check_setup.py --stream` shows about 25 Hz | ESP32 sketch has `SAMPLE_AVERAGE = 4` | Set it to `1`, or set `sampling_rate_hz = 25.0` in the project config |

## Signal quality

| Symptom | Cause | Fix |
|---------|-------|-----|
| Flat or tiny waveform | poor contact, or pressing too hard | Rest the sensor lightly. A fingertip pad gives the strongest signal. |
| Waveform clips at the top or bottom | `LED_BRIGHTNESS` or `ADC_RANGE` | Lower the brightness, or raise the ADC range in the sketch |
| Large low-frequency swings | breathing or hand movement | Wait out the 15 to 20 second stabilisation, keep the hand still, use the case and strap |
| Live classifier flips constantly | sample-rate mismatch, or too little training data | Record again at the real rate, collect more sessions, and check the confusion matrix in `script2_*` |

## Analysis and training

| Symptom | Cause | Fix |
|---------|-------|-----|
| `script2` finds no CSV | run from the wrong folder, or `script1` never saved | Run from the project's `wired/` or `wireless/` folder, and complete a full protocol in `script1` |
| Model accuracy near 100 percent | leakage, the same session in train and test, or a trivial feature | Split by session, and drop features like `raw_mean` that only encode LED brightness |
| GUI will not start on Linux | missing Qt platform libraries | `sudo apt install libxcb-cursor0 libxkbcommon-x11-0` |

Still stuck? Open an issue with the OS, the Python version, wired or wireless, the exact command,
and the full error text. The templates are in `.github/ISSUE_TEMPLATE/`.
