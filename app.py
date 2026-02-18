import time
import threading
from mqtt_handler import start_mqtt
from missing_logic import load_items
from app_gui import show_missing_popup, items_list

# --- Load items ---
try:
    loaded_items = load_items()
    if isinstance(loaded_items, list):
        items_list.extend(loaded_items)
    else:
        print("Error loading items: expected list")
except Exception as e:
    print("Error loading items:", e)

# --- Function to handle missing items ---
def handle_missing_item(item_name, last_seen):
    # This will trigger a popup in the GUI
    show_missing_popup(item_name, last_seen)

# --- MQTT Callback for missing items ---
def missing_item_callback(missing_item_data):
    """
    Example missing_item_data format:
    {
        "name": "Wallet",
        "last_seen": "Front Door"
    }
    """
    item_name = missing_item_data.get("name", "Unknown Item")
    last_seen = missing_item_data.get("last_seen", "Unknown Location")
    handle_missing_item(item_name, last_seen)

# --- Start MQTT Thread ---
def start_mqtt_thread():
    # Pass the callback so the MQTT handler knows what to do
    start_mqtt(callback=missing_item_callback)

mqtt_thread = threading.Thread(target=start_mqtt_thread)
mqtt_thread.daemon = True
mqtt_thread.start()

# Keep the app running
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Exiting app...")
