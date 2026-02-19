import paho.mqtt.client as mqtt
from missing_logic import update_last_seen, check_missing_items, items_list
from threading import Thread
import time

MQTT_BROKER = "192.168.1.42"  # replace with your broker IP
MQTT_PORT = 1883
MQTT_TOPIC = "edc/items"

# Callback for MQTT messages
def on_message(client, userdata, msg):
    """
    msg.payload should contain MAC addresses of detected items from ESP32
    Example payload: b'["AA:BB:CC:DD:EE:01", "AA:BB:CC:DD:EE:02"]'
    """
    try:
        detected_macs = eval(msg.payload.decode())  # convert string list to Python list
        for mac in detected_macs:
            update_last_seen(mac)

        # After updating last_seen, check for missing items
        missing = check_missing_items()
        for item in missing:
            # Trigger GUI popup via callback
            if userdata.get("popup_callback"):
                userdata["popup_callback"](item)

    except Exception as e:
        print("Error processing MQTT message:", e)

def start_mqtt(popup_callback=None):
    """
    Start MQTT in a separate thread
    popup_callback: function(item_dict) called when an item is missing
    """
    client = mqtt.Client(userdata={"popup_callback": popup_callback})
    client.on_message = on_message

    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.subscribe(MQTT_TOPIC)

    def loop():
        client.loop_forever()

    thread = Thread(target=loop)
    thread.daemon = True
    thread.start()
