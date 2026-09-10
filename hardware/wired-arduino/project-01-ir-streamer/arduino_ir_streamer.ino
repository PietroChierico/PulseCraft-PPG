// Copyright (c) 2026 Pietro Chierico
// SPDX-License-Identifier: MIT

/*
  PulseCraft PPG - Arduino UNO + MAX30102/MAX30105 IR serial streamer

  Project: 01 - Physical Activity Recognition

  Wiring:
    Sensor GND -> Arduino GND
    Sensor VIN -> Arduino 3.3V
    Sensor SDA -> Arduino SDA
    Sensor SCL -> Arduino SCL
    Sensor INT -> not connected

  Serial stream format:
    time_us,ir

  Python parsers in this repository use the last numeric value in each line as
  the IR sample, so both "ir" and "time_us,ir" formats are accepted.
*/

#include <Wire.h>
#include "MAX30105.h"

MAX30105 particleSensor;

void setup() {
  Serial.begin(115200);
  delay(1000);

  Wire.begin();

  Serial.println("Initializing MAX3010x sensor...");

  if (!particleSensor.begin(Wire, I2C_SPEED_STANDARD)) {
    Serial.println("MAX3010x not found. Check wiring.");
    while (1) {
      ;
    }
  }

  particleSensor.setup(
    0x1F,  // LED brightness
    1,     // sample averaging: 1 = no averaging/filtering
    2,     // mode: Red + IR. The stream below uses IR.
    100,   // sample rate: 100 Hz
    411,   // pulse width
    4096   // ADC range
  );

  Serial.println("Sensor ready.");
  Serial.println("time_us,ir");
}

void loop() {
  particleSensor.check();

  while (particleSensor.available()) {
    unsigned long timestampUs = micros();
    long irValue = particleSensor.getFIFOIR();

    particleSensor.nextSample();

    Serial.print(timestampUs);
    Serial.print(",");
    Serial.println(irValue);
  }
}
