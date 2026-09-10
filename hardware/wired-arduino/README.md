# Wired Arduino setup

These sketches stream PPG samples from a MAX30102 or MAX30105 to Python over USB serial at
115200 baud.

## Wiring

| MAX3010x | Arduino UNO |
|----------|-------------|
| GND | GND |
| VIN | 3.3V |
| SDA | SDA |
| SCL | SCL |
| INT | not connected |

## Sketches

- `project-01-ir-streamer/arduino_ir_streamer.ino`
- `project-02-ir-streamer/arduino_ir_streamer.ino`
- `project-03-ir-streamer/arduino_ir_streamer.ino`
- `project-04-red-ir-streamer/arduino_red_ir_streamer.ino`
- `project-05-ir-streamer/arduino_ir_streamer.ino`

Close the Arduino IDE Serial Monitor before you connect from Python.
