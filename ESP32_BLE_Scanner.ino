#include <WiFi.h>
#include <PubSubClient.h>
#include <BLEDevice.h>
#include <BLEScan.h>

const char* ssid = "YOUR_WIFI";
const char* password = "YOUR_PASS";

const char* mqtt_server = "192.168.1.37";
const int mqtt_port = 1883;

WiFiClient espClient;
PubSubClient client(espClient);

BLEScan* pBLEScan;
int scanTime = 5;

void setup_wifi() {
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
  }
}

void reconnect() {
  while (!client.connected()) {
    client.connect("ESP32_BedroomScanner");
  }
}

void setup() {
  Serial.begin(115200);
  setup_wifi();
  client.setServer(mqtt_server, mqtt_port);

  BLEDevice::init("");
  pBLEScan = BLEDevice::getScan();
  pBLEScan->setActiveScan(true);
}

void loop() {
  if (!client.connected()) reconnect();
  client.loop();

  BLEScanResults* foundDevices = pBLEScan->start(scanTime, false);

  for (int i = 0; i < foundDevices->getCount(); i++) {
    BLEAdvertisedDevice device = foundDevices->getDevice(i);

    String mac = device.getAddress().toString().c_str();
    mac.toLowerCase();   // normalize MAC

    int rssi = device.getRSSI();

    String topic = "edc/items/" + mac + "/seen";
    String payload = "{\"location\":\"bedroom\",\"rssi\":" + String(rssi) + "}";

    client.publish(topic.c_str(), payload.c_str());
  }

  pBLEScan->clearResults();
  delay(5000);
}
