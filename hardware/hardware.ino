// ESP32 + DHT -> HTTP POST (JSON) -> PHP API
// ต้องติดตั้งไลบรารี: DHT sensor library (Adafruit), ArduinoJson v7
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include "DHT.h"

#define DHTPIN 4          // Data -> GPIO 4 (+ Pull-up 10kΩ ไป 3.3V)
#define DHTTYPE DHT22     // ใช้ DHT22 ให้เปลี่ยนเป็น DHT22

// ===== ตั้งค่าที่นี่ =====
const char* ssid = "GavinNC";
const char* password = "12345678";
// ใส่ IP เครื่องที่รัน XAMPP (ดูด้วย ipconfig) ห้ามใช้ localhost
const char* serverUrl = "http://10.234.116.141:8080/smart_farm/api/store_telemetry.php";

DHT dht(DHTPIN, DHTTYPE);

void connectWiFi() {
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) { delay(500); Serial.print("."); }
  Serial.println("\nWiFi connected: " + WiFi.localIP().toString());
}

void setup() {
  Serial.begin(115200);
  dht.begin();
  connectWiFi();
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) connectWiFi();

  float h = dht.readHumidity();
  float t = dht.readTemperature();

  if (!isnan(h) && !isnan(t)) {
    HTTPClient http;
    http.begin(serverUrl);
    http.addHeader("Content-Type", "application/json");

    JsonDocument doc;
    doc["temperature"] = t;
    doc["humidity"] = h;

    String jsonPayload;
    serializeJson(doc, jsonPayload);

    unsigned long t0 = millis();
    int code = http.POST(jsonPayload);
    Serial.printf("T=%.1f H=%.1f -> HTTP %d (%lu ms)\n", t, h, code, millis() - t0);
    http.end();
  } else {
    Serial.println("DHT read failed");
  }
  delay(10000); // ส่งทุกๆ 10 วินาที
}
