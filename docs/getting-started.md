# Getting started

Two paths. Do **A** first — it needs no hardware and takes 5 minutes. Then do **B**.

---

## A. Run a project with the simulator (no hardware)

```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python tools/check_setup.py                            # confirms the environment
```

Start the synthetic stream (it behaves like the ESP32 firmware: a TCP server on port 3333
sending `millis,red,ir` lines at 100 Hz):

```bash
python tools/ppg_simulator.py --scenario activity      # or: caffeine | relaxation | apnea | stress
```

In a second terminal, run any **wireless** project. When a script asks for a host and port,
use `127.0.0.1` and `3333`:

```bash
cd projects/01-physical-activity-recognition/wireless
python script1_dataset_collection_protocol.py
```

You can complete the full collect → train → run-live loop entirely on simulated data. This is
the recommended way to prepare a class before the hardware is set up.

---

## B. Run a project with real hardware

### 1. Build the sensor node

Wire the MAX3010x to the board (tables in [`hardware.md`](hardware.md)) and, optionally, print
the case in `hardware/stl/`.

### 2. Flash the firmware

Install the Arduino IDE and the **SparkFun MAX3010x** library (Library Manager → search
"MAX3010x").

- **Wired:** open `hardware/wired-arduino/project-0X-*/*.ino`, select your board and port, upload.
  Close the Serial Monitor afterwards (Python needs the port).
- **Wireless:** open `hardware/wireless-esp32/project-0X-*/*.ino`. Leave the WiFi fields on their
  placeholders to make the board create its own network `PPG_STREAM_groupN` (password `12345678`),
  or enter your router credentials. Upload, then open the Serial Monitor once to read the IP.

### 3. Connect

- **Wired:** find the COM/tty port (Arduino IDE → Tools → Port). The Python GUI has a port field.
- **Wireless — board's own network:** connect your computer's WiFi to `PPG_STREAM_groupN`, then use
  host `192.168.4.1`, port `3333`.
- **Wireless — router mode:** use the IP printed in the Serial Monitor, port `3333`.

Verify the stream first with `python tools/check_setup.py --stream 192.168.4.1:3333` — it reports
the measured sample rate and a 2 s waveform preview.

### 4. Run the project

Open the project folder and follow its `README.md`. Each project ships an `app.py` launcher
(a small local web page with buttons) and three numbered scripts you can also run directly:

```text
script1_*   collect a labeled dataset (guided protocol)
script2_*   analyze features, train + test a model, export it
script3_*   stream live and classify / score in real time
```

---

## Sample rate must match everywhere

Collection, training, and live inference assume the **same** sample rate. The Python config
default is 100 Hz. If you change firmware sample rate or averaging, update `sampling_rate_hz`
in the project's config and re-collect. See [`hardware.md`](hardware.md#sample-rate).

## If something breaks

See [`troubleshooting.md`](troubleshooting.md). The most common issues are: Serial Monitor left
open, wrong host/port, sensor not making skin contact, and a sample-rate mismatch.
