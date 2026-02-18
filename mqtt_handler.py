import json
import os
import time
import paho.mqtt.client as mqtt

DATA_FILE = "data/items.json"
LOGBOOK_FILE = "data/logbook.json"

MQTT_BROKER = "localhost"
MQTT_PORT = 1883

# Ensure data directory exists
os.makedirs("data", exist_ok=True)

# Ensure files exist
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({}, f)

if not os.path.exists(LOGBOOK_FILE):
    with open(LOGBOOK_FILE, "w") as f:
        json.dump([], f)


def load_items():
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_items(items):
    with open(DATA_FILE, "w") as f:
        json.dump(items, f, indent=4)


def log_event(entry):
    with open(LOGBOOK_FILE, "r") as f:
        logbook = json.load(f)

    logbook.append(entry)

    with open(LOGBOOK_FILE, "w") as f:
        json.dump(logbook, f, indent=4)


def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT Broker")
    client.subscribe("edc/items/+/seen")


def on_message(client, userdata, msg):
    print("\nMessage received:")
    print("Topic:", msg.topic)

    try:
        payload = json.loads(msg.payload.decode())
        print("Parsed JSON:", payload)

        mac = msg.topic.split("/")[-2].lower()  # normalize MAC
        location = payload.get("location")
        rssi = payload.get("rssi")

        items = load_items()

        if mac not in items:
            items[mac] = {
                "name": "Unknown",
                "last_seen": 0,
                "location": "unknown",
                "rssi": 0
            }

        items[mac]["last_seen"] = time.time()
        items[mac]["location"] = location
        items[mac]["rssi"] = rssi

        save_items(items)

        log_event({
            "timestamp": time.time(),
            "mac": mac,
            "event": "seen",
            "location": location,
            "rssi": rssi
        })

    except Exception as e:
        print("Error handling message:", e)


def start_mqtt():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_forever()
    