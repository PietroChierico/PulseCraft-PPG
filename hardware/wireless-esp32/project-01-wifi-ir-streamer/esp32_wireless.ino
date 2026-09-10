// Copyright (c) 2026 Pietro Chierico
// SPDX-License-Identifier: MIT

/*
  ESP32-C6 Feather + MAX30102 / MAX30105 PPG WiFi Streamer

  Board:
    Adafruit Feather ESP32-C6

  Sensor:
    I2C PPG sensor, for example MAX30102 or MAX30105

  Wiring:
    Sensor GND  -> Feather GND
    Sensor VIN  -> Feather 3.3V
    Sensor SDA  -> Feather SDA / IO19
    Sensor SCL  -> Feather SCL / IO18
    Sensor INT  -> Not connected

  TCP stream format:
    millis,red,ir

  PC connects to:
    AP mode: 192.168.4.1 port 3333
    WiFi router mode: use the IP printed in Serial Monitor
*/

#include <WiFi.h>
#include <Wire.h>
#include "MAX30105.h"

// ESP32-C6 Feather I2C pins
#define I2C_SDA_PIN 19
#define I2C_SCL_PIN 18

// Leave these as they are to make the ESP32 create its own WiFi network.
// Or put your router WiFi name/password here.
const char* WIFI_SSID     = "YOUR_WIFI_NAME";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

// Fallback Access Point settings
const char* AP_SSID     = "PPG_STREAM_group1";
const char* AP_PASSWORD = "12345678";   // Must be at least 8 characters

const uint16_t TCP_PORT = 3333;
const uint32_t WIFI_TIMEOUT_MS = 15000;

WiFiServer server(TCP_PORT);
WiFiClient client;
MAX30105 ppg;

// Sensor settings
// Increase LED_BRIGHTNESS if the signal is too weak.
// Decrease it if the sensor gets warm or battery life is poor.
const byte LED_BRIGHTNESS = 0x1F;  // 0x00 to 0xFF
const byte SAMPLE_AVERAGE = 1;   // 1 => true 100 Hz output, matches the Python sampling_rate_hz default. Was 4 (=> 25 Hz).
const byte LED_MODE = 2;           // 1 = Red only, 2 = Red + IR, 3 = Red + IR + Green
const int SAMPLE_RATE = 100;       // Hz
const int PULSE_WIDTH = 411;       // 69, 118, 215, 411
const int ADC_RANGE = 16384;       // 2048, 4096, 8192, 16384

bool usingAccessPoint = false;

// NEO: Set onboard NeoPixel color.
// Values are low brightness to avoid too much power use.
void setNeoColor(uint8_t red, uint8_t green, uint8_t blue) {
#if defined(PIN_NEOPIXEL)
  neopixelWrite(PIN_NEOPIXEL, red, green, blue);
#endif
}

// NEO: Initialize onboard NeoPixel pin.
void setupNeoPixel() {
#if defined(PIN_NEOPIXEL)
  pinMode(PIN_NEOPIXEL, OUTPUT);
  setNeoColor(32, 8, 0);   // Orange: boot
#endif
}

void startAccessPoint() {
  WiFi.mode(WIFI_AP);
  WiFi.softAP(AP_SSID, AP_PASSWORD);

  IPAddress ip = WiFi.softAPIP();
  usingAccessPoint = true;

  setNeoColor(32, 0, 32);  // Purple: fallback AP active

  Serial.println();
  Serial.println("Started ESP32 Access Point.");
  Serial.print("WiFi network: ");
  Serial.println(AP_SSID);
  Serial.print("Password: ");
  Serial.println(AP_PASSWORD);
  Serial.print("Connect your PC to this WiFi, then connect to IP: ");
  Serial.println(ip);
  Serial.print("TCP port: ");
  Serial.println(TCP_PORT);
}

void connectWiFi() {
  bool credentialsChanged =
    strcmp(WIFI_SSID, "YOUR_WIFI_NAME") != 0 &&
    strlen(WIFI_SSID) > 0;

  if (!credentialsChanged) {
    startAccessPoint();
    return;
  }

  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false);

  setNeoColor(0, 0, 32);   // Blue: connecting to router WiFi

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  Serial.println();
  Serial.print("Connecting to WiFi: ");
  Serial.println(WIFI_SSID);

  uint32_t startAttempt = millis();

  while (WiFi.status() != WL_CONNECTED &&
         millis() - startAttempt < WIFI_TIMEOUT_MS) {
    delay(500);
    Serial.print(".");
  }

  Serial.println();

  if (WiFi.status() == WL_CONNECTED) {
    usingAccessPoint = false;

    setNeoColor(0, 32, 0);   // Green: connected to router WiFi

    Serial.println("Connected to router WiFi.");
    Serial.print("ESP32 IP address: ");
    Serial.println(WiFi.localIP());
    Serial.print("TCP port: ");
    Serial.println(TCP_PORT);
  } else {
    Serial.println("Could not connect to router WiFi. Starting fallback AP.");
    WiFi.disconnect(true);
    delay(500);
    startAccessPoint();
  }
}

void setupSensor() {
  Serial.println("Starting I2C...");

  setNeoColor(32, 8, 0);   // Orange: sensor starting

  // The ESP32-C6 Feather uses SDA IO19 and SCL IO18.
  Wire.begin(I2C_SDA_PIN, I2C_SCL_PIN);
  Wire.setClock(400000);

  Serial.println("Searching for MAX3010x sensor...");

  if (!ppg.begin(Wire, I2C_SPEED_FAST)) {
    setNeoColor(64, 0, 0);   // Red: sensor error

    Serial.println("ERROR: MAX3010x sensor not found.");
    Serial.println("Check GND, 3.3V, SDA, and SCL connections.");
    while (true) {
      delay(1000);
    }
  }

  ppg.setup(
    LED_BRIGHTNESS,
    SAMPLE_AVERAGE,
    LED_MODE,
    SAMPLE_RATE,
    PULSE_WIDTH,
    ADC_RANGE
  );

  ppg.clearFIFO();

  Serial.println("MAX3010x sensor found and configured.");
  Serial.println("Stream format: millis,red,ir");
}

void acceptClientIfNeeded() {
  if (client && client.connected()) {
    return;
  }

  WiFiClient newClient = server.available();

  if (newClient) {
    if (client) {
      client.stop();
    }

    client = newClient;
    client.setNoDelay(true);

    client.println("millis,red,ir");

    setNeoColor(0, 32, 32);   // Cyan: PC connected to TCP stream

    Serial.println();
    Serial.println("PC connected to PPG stream.");
  }
}
void streamSample(int32_t red, int32_t ir) {
  char line[64];

  int n = snprintf(
    line,
    sizeof(line),
    "%lu,%ld,%ld\n",
    (unsigned long)millis(),
    (long)red,
    (long)ir
  );

  Serial.write((const uint8_t*)line, n);

  if (client && client.connected()) {
    client.write((const uint8_t*)line, n);
  }
}

void setup() {
  Serial.begin(115200);
  delay(2000);

  Serial.println();
  Serial.println("ESP32-C6 Feather PPG WiFi Streamer");

#if defined(NEOPIXEL_I2C_POWER)
  // On the Feather this pin powers the STEMMA QT / I2C connector.
  pinMode(NEOPIXEL_I2C_POWER, OUTPUT);
  digitalWrite(NEOPIXEL_I2C_POWER, HIGH);
#endif

  setupNeoPixel();

  setupSensor();
  connectWiFi();

  server.begin();

  Serial.println();
  Serial.println("TCP server started.");
  Serial.println("Place your finger gently on the PPG sensor.");
}

void loop() {
  acceptClientIfNeeded();

  // Read all samples waiting in the MAX3010x FIFO.
  ppg.check();

while (ppg.available()) {
  int32_t red = (int32_t)ppg.getFIFORed();
  int32_t ir  = (int32_t)ppg.getFIFOIR();

  streamSample(red, ir);

  ppg.nextSample();
}

  // Optional: allow the PC to disconnect by sending x.
  if (client && client.connected() && client.available()) {
    char c = client.read();
    if (c == 'x' || c == 'X') {
      client.stop();

      if (usingAccessPoint) {
        setNeoColor(32, 0, 32);  // Purple: AP still active
      } else {
        setNeoColor(0, 32, 0);   // Green: router WiFi still connected
      }

      Serial.println("PC disconnected.");
    }
  }
}