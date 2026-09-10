// Copyright (c) 2026 Pietro Chierico
// SPDX-License-Identifier: MIT

/*
  Minimal Arduino serial output format example for Project 5.

  Replace readPpgSample() with your real PPG sensor reading.
  The Python scripts use the last number printed on each line as the PPG/IR sample.
*/

const unsigned long SAMPLE_INTERVAL_US = 10000;  // 100 Hz
unsigned long lastSampleTimeUs = 0;

float readPpgSample() {
  // Example for an analog PPG module connected to A0.
  // For a digital sensor such as MAX30102, replace this line with the IR value.
  return analogRead(A0);
}

void setup() {
  Serial.begin(115200);
  while (!Serial) {
    ;
  }
}

void loop() {
  unsigned long nowUs = micros();
  if (nowUs - lastSampleTimeUs >= SAMPLE_INTERVAL_US) {
    lastSampleTimeUs += SAMPLE_INTERVAL_US;

    float ppgValue = readPpgSample();

    // Simple format accepted by Python:
    Serial.println(ppgValue);

    // Alternative accepted formats:
    // Serial.print("ir="); Serial.println(ppgValue);
    // Serial.print(millis()); Serial.print(","); Serial.println(ppgValue);
  }
}
