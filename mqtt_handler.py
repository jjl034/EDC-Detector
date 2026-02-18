import json
import time
import paho.mqtt.client as mqtt
from missing_logic import load_items, save_items

DATA_FILE = "data/items.json"

MQTT_SERVER = "localhost"  # Raspberry Pi IP
MQTT_PORT = 1883
TOPIC_PREFIX = "edc/items/"

client = mqtt.Client()


def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT Broker")
    client.subscribe(f"{TOPIC_PREFIX}+/seen")


def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode()
    print("\nMessage received:")
    print("Topic:", topic)
    print("Parsed JSON:", payload)

    # Extract MAC from topic and normalize to lowercase
    try:
        mac = topic.split("/")[2].lower()
    except IndexError:
        print("Invalid topic format:", topic)
        return

    try:
        items = load_items()
    except Exception as e:
        print("Error loading items:", e)
        return

    # Update last_seen for matching MAC
    updated = False
    for item in items:
        if not isinstance(item, dict):
            continue
        if item.get("mac", "").lower() == mac:
            item["last_seen"] = time.time()
            updated = True

    if updated:
        save_items(items)
        print(f"Updated last_seen for MAC: {mac}")
    else:
        print(f"No matching item found for MAC: {mac}")


def start_mqtt():
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_SERVER, MQTT_PORT, 60)
    client.loop_start()
    

