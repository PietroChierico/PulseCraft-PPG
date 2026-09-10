# Getting started

There are two paths. Do A first, since it needs no hardware and takes about five minutes. Then
do B when you have a sensor.

## A. Run a project with the simulator

```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python tools/check_setup.py                            # confirms the environment
```

Start the synthetic stream. It behaves like the ESP32 firmware, running a TCP server on port
3333 and sending `millis,red,ir` lines at 100 Hz.

```bash
python tools/ppg_simulator.py --scenario activity      # also caffeine, relaxation, apnea, stress
```

In a second terminal, run any wireless project. When a script asks for a host and a port, use
`127.0.0.1` and `3333`.

```bash
cd projects/01-physical-activity-recognition/wireless
python script1_dataset_collection_protocol.py
```

You can do the whole loop, collect then train then run live, entirely on simulated data. This is
the easiest way to get familiar with a project before the hardware is set up.

## B. Run a project with real hardware

### 1. Build the sensor node

Wire the MAX3010x to the board using the tables in [hardware.md](hardware.md), and print the case
in `hardware/stl/` if you want one.

### 2. Flash the firmware

Install the Arduino IDE and the SparkFun MAX3010x library (Library Manager, search "MAX3010x").

For the wired setup, open `hardware/wired-arduino/project-0X-*/*.ino`, select your board and
port, and upload. Close the Serial Monitor afterwards, because Python needs the port.

For the wireless setup, open `hardware/wireless-esp32/project-0X-*/*.ino`. Leave the WiFi fields
on their placeholders and the board makes its own network `PPG_STREAM_groupN` (password
`12345678`), or enter your router credentials instead. Upload, then open the Serial Monitor once
to read the IP.

### 3. Connect

For the wired setup, find the COM or tty port in Arduino IDE under Tools then Port. The Python
GUI has a port field.

For the wireless setup on the board's own network, connect your computer's WiFi to
`PPG_STREAM_groupN`, then use host `192.168.4.1` and port `3333`. In router mode, use the IP
printed in the Serial Monitor and port `3333`.

Check the stream first with `python tools/check_setup.py --stream 192.168.4.1:3333`. It reports
the measured sample rate and a short waveform preview.

### 4. Run the project

Open the project folder and follow its `README.md`. Each project has an `app.py` launcher, a
small local web page with buttons, and three numbered scripts you can also run directly.

```text
script1_*   collect a labeled dataset with a guided protocol
script2_*   analyze features, train and test a model, export it
script3_*   stream live and classify or score in real time
```

Before a real recording, run through the [signal-quality checklist](signal-quality-checklist.md).

## Sample rate must match everywhere

Collection, training and live inference all assume the same sample rate. The Python config
default is 100 Hz. If you change the firmware sample rate or averaging, update `sampling_rate_hz`
in the project config and record again. See [hardware.md](hardware.md#sample-rate).

## If something breaks

See [troubleshooting.md](troubleshooting.md). The usual causes are a Serial Monitor left open,
the wrong host or port, the sensor not touching skin properly, and a sample-rate mismatch.
