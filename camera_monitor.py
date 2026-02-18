import cv2
import time
from missing_logic import check_missing_items

PROTOTXT = "deploy.prototxt"
MODEL = "res10_300x300_ssd_iter_140000.caffemodel"

CONFIDENCE_THRESHOLD = 0.5
PERSON_CLASS_ID = 15
COOLDOWN = 5  # seconds


def monitor_camera():
    print("Starting camera person detection...")

    net = cv2.dnn.readNetFromCaffe(PROTOTXT, MODEL)
    cap = cv2.VideoCapture(0, cv2.CAP_V4L2)

    if not cap.isOpened():
        print("Error: Could not open camera.")
        return

    last_trigger_time = 0

    while True:
        ret, frame = cap.read()
        print("Reading frame...")
        if not ret:
            continue

        resized = cv2.resize(frame, (300, 300))
        blob = cv2.dnn.blobFromImage(resized, 0.007843, (300, 300), 127.5)
        net.setInput(blob)
        detections = net.forward()

        person_detected = False

        for i in range(detections.shape[2]):
            class_id = int(detections[0, 0, i, 1])
            confidence = float(detections[0, 0, i, 2])

            if class_id == PERSON_CLASS_ID and confidence > CONFIDENCE_THRESHOLD:
                person_detected = True
                break

        current_time = time.time()

        if person_detected and (current_time - last_trigger_time) > COOLDOWN:
            print("Person detected! Checking missing items...")
            check_missing_items()
            last_trigger_time = current_time

        time.sleep(0.1)



