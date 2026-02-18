import paho.mqtt.client as mqtt
import json
from missing_logic import load_items, save_items

# --- MQTT Settings ---
BROKER_IP = "172.20.10.9"  # Replace with your broker IP
BROKER_PORT = 1883
TOPIC = "edc/missing"

# --- Load items database ---
items = load_items()  # This is a list of dicts: [{"name": "Wallet", "mac": "...", "last_seen": "..."}]

# --- Callback function placeholder ---
missing_callback = None  # Will be set from app.py

# --- MQTT Event Handlers ---
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT broker!")
        client.subscribe(TOPIC)
    else:
        print(f"Failed to connect, return code {rc}")

def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode()
        data = json.loads(payload)  # Expecting {"mac": "...", "location": "..."}
        mac = data.get("mac")
        location = data.get("location", "Unknown Location")

        # Find the item with this MAC
        missing_item = next((item for item in items if item.get("mac") == mac), None)
        if missing_item:
            missing_item["last_seen"] = location
            save_items(items)  # Update last seen
            print(f"Missing item detected: {missing_item['name']} at {location}")

            # Trigger the GUI popup
            if missing_callback:
                missing_callback({
                    "name": missing_item["name"],
                    "last_seen": location
                })
        else:
            print(f"Unknown item with MAC {mac} detected at {location}")
    except Exception as e:
        print("Error processing MQTT message:", e)

# --- Start MQTT Client ---
def start_mqtt(callback=None):
    global missing_callback
    missing_callback = callback

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(BROKER_IP, BROKER_PORT, 60)
    client.loop_forever()

