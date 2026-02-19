import cv2
import json
from pathlib import Path
import paho.mqtt.client as mqtt
import time

# --- Config ---
BROKER = "localhost"  # Replace with your MQTT broker IP
TOPIC = "edc/missing"
DATA_FILE = Path("./data/items.json")

# --- MQTT Setup ---
client = mqtt.Client()
client.connect(BROKER, 1883, 60)
client.loop_start()


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


def publish_missing_item(item_name, last_seen="Unknown"):
    payload = json.dumps({"name": item_name, "last_seen": last_seen})
    client.publish(TOPIC, payload)


# --- Webcam Detection ---
def detect_missing_items():
    items = load_items()
    if not items:
        print("No items to track.")
        return

    # Open webcam
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Cannot open webcam.")
        return

    print("Starting webcam detection... Press 'q' to quit.")

    # For demonstration, we simulate missing items by pressing 'm'
    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        # Display webcam feed (optional)
        cv2.imshow('Webcam', frame)

        key = cv2.waitKey(1) & 0xFF

        # Quit
        if key == ord('q'):
            break

        # Simulate missing item detection
        if key == ord('m'):
            # Example: randomly pick first item as missing
            missing_item = items[0]
            missing_item_name = missing_item.get("name", "Unknown")
            last_seen = missing_item.get("last_seen", "Webcam Feed")
            print(f"Missing item detected: {missing_item_name}")

            # Update last_seen to webcam location
            missing_item["last_seen"] = "Webcam Feed"
            save_items(items)

            # Publish MQTT message to GUI
            publish_missing_item(missing_item_name, last_seen)

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    detect_missing_items()
