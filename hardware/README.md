# Hardware

Acquisition firmware and the 3D-printable sensor case. The full guide — bill of materials,
wiring diagrams, network modes, sample-rate notes — is in
[`../docs/hardware.md`](../docs/hardware.md).

```text
hardware/
├── wired-arduino/     # Arduino UNO + MAX3010x, USB serial @ 115200
│   └── project-0X-*/  # one streamer sketch per project
├── wireless-esp32/    # Adafruit Feather ESP32-C6 + MAX3010x, WiFi TCP :3333
│   └── project-0X-*/  # one streamer sketch per project
└── stl/               # two-piece MAX3010x clip enclosure (CC BY 4.0)
```

## Which sketch

| Project | Wired | Wireless | Stream |
|---------|-------|----------|--------|
| 01, 02, 03, 05 | `wired-arduino/project-0X-ir-streamer/` | `wireless-esp32/project-0X-wifi-ir-streamer/` | IR (`time_us,ir` / `millis,red,ir`) |
| 04 | `wired-arduino/project-04-red-ir-streamer/` | `wireless-esp32/project-04-wifi-red-ir-streamer/` | Red + IR |

The MCU only streams samples — all protocol and analysis logic is in the Python projects.

## Arduino library

**SparkFun MAX3010x Pulse and Proximity Sensor Library** (`MAX30105.h`), via the Arduino Library
Manager. ESP32 sketches also need the **esp32** boards package.

## No hardware?

`../tools/ppg_simulator.py` replaces the wireless firmware with a synthetic stream on
`127.0.0.1:3333`. Every wireless project runs against it.

## Sensor placement

Gentle, stable contact. Hard pressure collapses perfusion and flattens the waveform. Fingertip
pad gives the strongest signal; wrist is more realistic but noisier. Use the printed case + a
strap for motion-sensitive work.
