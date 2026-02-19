#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEScan.h>
#include <BLEAdvertisedDevice.h>
#include <ArduinoJson.h>

// --- WiFi ---
const char* ssid = "iPhone (4)";
const char* password = "Fluffy11";

// --- MQTT ---
const char* mqtt_server = "172.20.10.9";  // Raspberry Pi IP
const int mqtt_port = 1883;
const char* mqtt_topic = "edc/missing";

// --- Device Location ---
const char* locationName = "Kitchen"; // Change for each ESP32

// --- BLE ---
int scanTime = 5;
BLEScan* pBLEScan;

// --- MQTT Client ---
WiFiClient espClient;
PubSubClient client(espClient);

void connectWiFi() {
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) delay(500);
}

void connectMQTT() {
  while (!client.connected()) {
    if (!client.connect(locationName)) delay(2000);
  }
}

void setup() {
  Serial.begin(115200);
  connectWiFi();
  client.setServer(mqtt_server, mqtt_port);

  BLEDevice::init("");
  pBLEScan = BLEDevice::getScan();
  pBLEScan->setActiveScan(true);
  pBLEScan->setInterval(100);
  pBLEScan->setWindow(99);
}

void loop() {
  if (!client.connected()) connectMQTT();
  client.loop();

  BLEScanResults* foundDevices = pBLEScan->start(scanTime, false);
  int count = foundDevices->getCount();

  for (int i = 0; i < count; i++) {
    BLEAdvertisedDevice device = foundDevices->getDevice(i);
    int rssi = device.getRSSI();

    if (rssi >= -60) {  // Only close devices
      String name = device.getName().c_str();
      String mac = device.getAddress().toString().c_str();

      StaticJsonDocument<256> doc;
      doc["mac"] = mac;
      doc["name"] = name;
      doc["rssi"] = rssi;
      doc["last_seen"] = locationName;

      char buffer[256];
      serializeJson(doc, buffer);
      client.publish(mqtt_topic, buffer);
    }
  }

  pBLEScan->clearResults();
  delay(3000);
}
