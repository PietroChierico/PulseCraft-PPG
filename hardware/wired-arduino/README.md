# Wired Arduino setup

These sketches stream PPG samples from MAX30102/MAX30105 to Python over USB serial at 115200 baud.

## Common wiring

| MAX3010x | Arduino UNO |
|---|---|
| GND | GND |
| VIN | 3.3V |
| SDA | SDA |
| SCL | SCL |
| INT | Not connected |

## Sketches

- `project-01-ir-streamer/arduino_ir_streamer.ino`
- `project-02-ir-streamer/arduino_ir_streamer.ino`
- `project-03-ir-streamer/arduino_ir_streamer.ino`
- `project-04-red-ir-streamer/arduino_red_ir_streamer.ino`
- `project-05-ir-streamer/arduino_ir_streamer.ino`

Close the Arduino IDE Serial Monitor before connecting from Python.
