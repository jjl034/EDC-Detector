import json
import time
import threading
import paho.mqtt.client as mqtt
from pathlib import Path
import cv2  # OpenCV for webcam
import random

DATA_FILE = Path("./data/items.json")
BROKER = "localhost"  # Replace with your MQTT broker IP
TOPIC = "edc/missing"

# --- MQTT Setup ---
mqtt_client = mqtt.Client()
mqtt_client.connect(BROKER, 1883, 60)
mqtt_client.loop_start()


# --- Load/Save Items ---
def load_items():
    if not DATA_FILE.exists():
        return []
    with open(DATA_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def save_items(items):
    DATA_FILE.parent.mkdir(exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(items, f, indent=2)


# --- Update Last Seen ---
def update_last_seen(item_name, location="Front Door"):
    items = load_items()
    for item in items:
        if item["name"] == item_name:
            item["last_seen"] = location
            break
    save_items(items)


# --- Webcam Detection Logic ---
def check_webcam_for_missing_items():
    """
    Replace this simple demo loop with your actual detection logic.
    This example randomly flags an item as missing every 15s.
    """
    items = load_items()
    cap = cv2.VideoCapture(0)  # USB webcam

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Webcam not detected")
            time.sleep(5)
            continue

        # --- Detection Placeholder ---
        # Replace with actual detection logic:
        # e.g., check for visual marker, QR, color, or BLE tag in frame
        if items:
            missing_item = random.choice(items)  # Demo missing item
            payload = json.dumps({
                "name": missing_item["name"],
                "last_seen": missing_item.get("last_seen", "Unknown")
            })
            mqtt_client.publish(TOPIC, payload)
            print(f"Missing item published: {missing_item['name']}")

        time.sleep(15)  # adjust as needed


if __name__ == "__main__":
    print("EDC Webcam Detection running...")
    detection_thread = threading.Thread(target=check_webcam_for_missing_items, daemon=True)
    detection_thread.start()

    while True:
        time.sleep(1)
