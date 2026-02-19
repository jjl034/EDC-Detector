# person_detector.py
import cv2
import json
import time
import paho.mqtt.client as mqtt
from pathlib import Path

# --- MQTT Setup ---
MQTT_BROKER = "localhost"
MQTT_TOPIC = "edc/missing"

mqtt_client = mqtt.Client()
mqtt_client.connect(MQTT_BROKER, 1883, 60)
mqtt_client.loop_start()

# --- Items Data ---
DATA_FILE = Path(__file__).parent / "data/items.json"

def load_items():
    if DATA_FILE.exists():
        with open(DATA_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def check_missing_items():
    """Return a list of missing items"""
    items = load_items()
    # Example logic: mark all items as missing for demonstration
    # Replace this with ESP32 detection logic later
    missing_items = [item for item in items if item.get("last_seen") != "Home"]
    return missing_items

# --- OpenCV Person Detector ---
hog = cv2.HOGDescriptor()
hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

cap = cv2.VideoCapture(0)  # USB camera

person_detected_last_frame = False

print("Starting camera person detection...")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame")
        break

    # Resize for speed
    frame_resized = cv2.resize(frame, (640, 480))

    # Detect people
    rects, weights = hog.detectMultiScale(frame_resized, winStride=(8,8), padding=(16,16), scale=1.05)
    person_detected = len(rects) > 0

    # Draw rectangles
    for (x, y, w, h) in rects:
        cv2.rectangle(frame_resized, (x, y), (x + w, y + h), (0, 255, 0), 2)

    # Check if person just left (was detected last frame but now gone)
    if person_detected_last_frame and not person_detected:
        print("Person left, checking missing items...")
        missing_items = check_missing_items()
        if missing_items:
            # Publish missing items to MQTT
            mqtt_client.publish(MQTT_TOPIC, json.dumps(missing_items))
            print(f"Published missing items: {[item['name'] for item in missing_items]}")

    person_detected_last_frame = person_detected

    # Show camera feed (optional)
    cv2.imshow("Person Detector", frame_resized)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
