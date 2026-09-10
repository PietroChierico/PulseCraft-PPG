# Wireless ESP32 setup

These sketches turn the ESP32 into a WiFi TCP PPG streamer.

## Wiring for the Adafruit Feather ESP32-C6

| MAX3010x | ESP32-C6 Feather |
|----------|------------------|
| GND | GND |
| VIN | 3.3V |
| SDA | SDA / IO19 |
| SCL | SCL / IO18 |
| INT | not connected |

## Connection modes

By default the sketch first tries the router WiFi credentials. If those are left as
placeholders it starts an Access Point instead. Connect your computer to that Access Point and
use host `192.168.4.1` and port `3333`.

## Sketches

- `project-01-wifi-ir-streamer/esp32_wireless.ino`
- `project-02-wifi-ir-streamer/esp32_wireless.ino`
- `project-03-wifi-ir-streamer/esp32_wireless.ino`
- `project-04-wifi-red-ir-streamer/esp32_wireless_red_ir.ino`
- `project-05-wifi-ir-streamer/esp32_wireless.ino`

The sketches stream positive raw sensor counts. Project 04 is the only one that needs a paired
Red and IR stream for its Python workflow. The other wireless sketches also send Red and IR, but
the project code uses IR only.
