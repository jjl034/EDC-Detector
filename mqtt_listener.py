# mqtt_listener.py

import paho.mqtt.client as mqtt
import json
import os
from datetime import datetime

# ===== SETTINGS =====
MQTT_BROKER = "localhost"      # Pi is running Mosquitto
MQTT_PORT = 1883
MQTT_TOPIC = "edc/devices"
ITEMS_FILE = "items.json"


# ==============================
# Load / Save Items
# ==============================
def load_items():
    if os.path.exists(ITEMS_FILE):
        with open(ITEMS_FILE, "r") as f:
            try:
                items = json.load(f)
                return {item["name"]: item for item in items}
            except:
                return {}
    return {}


def save_items(items):
    with open(ITEMS_FILE, "w") as f:
        json.dump(list(items.values()), f, indent=2)


# ==============================
# MQTT Callback
# ==============================
def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT with result code", rc)
    client.subscribe(MQTT_TOPIC)


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
    except:
        print("Invalid JSON received")
        return

    mac = payload.get("mac", "").lower()
    location = payload.get("location", "Unknown")
    rssi = payload.get("rssi", None)

    if not mac:
        return

    print(f"Seen {mac} at {location} (RSSI {rssi})")

    items = load_items()
    updated = False

    for item_name, item in items.items():
        stored_mac = item.get("mac", "").lower()

        if stored_mac == mac:

            item["last_seen_location"] = location
            item["last_seen_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            item["rssi"] = rssi

            print(f"Updated {item_name}")
            updated = True

    if updated:
        save_items(items)


# ==============================
# Main
# ==============================
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(MQTT_BROKER, MQTT_PORT, 60)

print("Listening for BLE devices...")

client.loop_forever()
