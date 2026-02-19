import json
import threading
import paho.mqtt.client as mqtt
from missing_logic import load_items, save_items
from app_gui import trigger_missing_popup  # Function to show popup in GUI

# MQTT broker settings
BROKER = "192.168.1.42"  # Your Raspberry Pi IP
PORT = 1883
TOPIC = "edc/items"

# Load items from JSON file
items = load_items()  # Format: [{"name": "Wallet", "mac": "AA:BB:CC:DD:EE:01", "last_seen": "..."}]

# Convert list to dict keyed by MAC for easy lookup
item_dict = {item["mac"].lower(): item for item in items}

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("MQTT connected")
        client.subscribe(TOPIC)
    else:
        print("MQTT connection failed with code", rc)

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        # payload format: {"AA:BB:CC:DD:EE:01": true, "AA:BB:CC:DD:EE:02": false}
        for mac, present in payload.items():
            mac = mac.lower()
            if mac in item_dict:
                item = item_dict[mac]
                if not present and item.get("present", True):  # Only trigger once
                    item["present"] = False
                    trigger_missing_popup(item["name"], item.get("last_seen", "unknown"))
                elif present:
                    item["present"] = True
                    item["last_seen"] = "ESP32 detected"  # Update last seen info
        # Save updated items to file
        save_items(list(item_dict.values()))
    except Exception as e:
        print("Error processing MQTT message:", e)

def start_mqtt():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(BROKER, PORT, 60)

    # Run MQTT loop in background thread so GUI stays responsive
    thread = threading.Thread(target=client.loop_forever)
    thread.daemon = True
    thread.start()
