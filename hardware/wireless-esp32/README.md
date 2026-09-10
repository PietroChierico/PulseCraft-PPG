# Wireless ESP32 setup

These sketches turn the ESP32 into a WiFi TCP PPG streamer.

## Common wiring for Adafruit Feather ESP32-C6

| MAX3010x | ESP32-C6 Feather |
|---|---|
| GND | GND |
| VIN | 3.3V |
| SDA | SDA / IO19 |
| SCL | SCL / IO18 |
| INT | Not connected |

## Connection modes

By default, the sketch first tries router WiFi credentials. If those are left as placeholders, it starts an Access Point. Connect your computer to that AP and use:

```text
Host: 192.168.4.1
Port: 3333
```

## Sketches

- `project-01-wifi-ir-streamer/esp32_wireless.ino`
- `project-02-wifi-ir-streamer/esp32_wireless.ino`
- `project-03-wifi-ir-streamer/esp32_wireless.ino`
- `project-04-wifi-red-ir-streamer/esp32_wireless_red_ir.ino`
- `project-05-wifi-ir-streamer/esp32_wireless.ino`

The shipped sketches stream positive raw sensor counts. Project 04 is the only one that requires a paired Red + IR stream for the Python workflow; the other wireless sketches also transmit Red and IR, but the project code uses IR.
