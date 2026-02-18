import cv2
import time
from missing_logic import check_missing_items

PROTOTXT = "deploy.prototxt"
MODEL = "res10_300x300_ssd_iter_140000.caffemodel"

CONFIDENCE_THRESHOLD = 0.5
COOLDOWN = 5  # seconds between triggers


def monitor_camera():
    print("Starting camera person detection...")

    # Load face detection model
    net = cv2.dnn.readNetFromCaffe(PROTOTXT, MODEL)

    # Use V4L2 backend (avoids GStreamer warnings)
    cap = cv2.VideoCapture(0, cv2.CAP_V4L2)

    if not cap.isOpened():
        print("Error: Could not open camera.")
        return

    last_trigger_time = 0

    while True:
        ret, frame = cap.read()

        if not ret:
            continue

        # Resize frame for model
        resized = cv2.resize(frame, (300, 300))

        # Correct preprocessing for res10 face model
        blob = cv2.dnn.blobFromImage(
            resized,
            1.0,
            (300, 300),
            (104.0, 177.0, 123.0)
        )

        net.setInput(blob)
        detections = net.forward()

        face_detected = False

        for i in range(detections.shape[2]):
            confidence = float(detections[0, 0, i, 2])

            if confidence > CONFIDENCE_THRESHOLD:
                face_detected = True
                break

        current_time = time.time()

        if face_detected and (current_time - last_trigger_time) > COOLDOWN:
            print("Face detected! Checking missing items...")
            check_missing_items()
            last_trigger_time = current_time

        # Slight delay to reduce CPU usage
        time.sleep(0.05)



