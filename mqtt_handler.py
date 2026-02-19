import paho.mqtt.client as mqtt
from missing_logic import load_items, update_item
from app_gui import gui_app  # reference to your running Kivy app

MQTT_BROKER = "172.20.10.9"  # replace with your broker IP
MQTT_PORT = 1883
MQTT_TOPIC = "edc/items"

mqtt_client = mqtt.Client(callback_api=mqtt.MQTTv5)

# Called when connection to broker is established
def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT broker with result code", rc)
    client.subscribe(MQTT_TOPIC)

# Called when a message is received
def on_message(client, userdata, msg):
    payload = msg.payload.decode()
    # Expected payload format: {"mac": "xx:xx:xx:xx", "present": false, "last_seen": "Front Door"}
    try:
        import json
        data = json.loads(payload)
        mac = data.get("mac", "").lower()
        present = data.get("present", True)
        last_seen = data.get("last_seen", "unknown")

        # Update local items.json
        updated = update_item(mac, present=present, last_seen=last_seen)

        # If the item is missing, trigger popup in GUI
        if not present and updated:
            item = [i for i in load_items() if i["mac"].lower() == mac][0]
            name = item.get("name", "Unknown")
            last = item.get("last_seen", "unknown")
            if gui_app:  # make sure the GUI app is running
                gui_app.show_missing_item_popup(name, last)

    except Exception as e:
        print("Error handling MQTT message:", e)

# Start MQTT client
def start_mqtt():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()
    return client


