import cv2
import time
from missing_logic import check_missing_items

PROTOTXT = "deploy.prototxt"
MODEL = "res10_300x300_ssd_iter_140000.caffemodel"

CONFIDENCE_THRESHOLD = 0.5
COOLDOWN = 5  # seconds between triggers


def monitor_camera():
    print("Starting camera person detection...")

    # Load face detection model safely
    try:
        net = cv2.dnn.readNetFromCaffe(PROTOTXT, MODEL)
        print("Face detection model loaded successfully.")
    except Exception as e:
        print("Error loading face detection model:", e)
        return

    # Try V4L2 backend first, fallback to default if it fails
    try:
        cap = cv2.VideoCapture("v4l2src device=/dev/video0 ! videoconvert ! appsink", cv2.CAP_GSTREAMER)
        if not cap.isOpened():
            print("V4L2 failed, trying default VideoCapture...")
            cap = cv2.VideoCapture(0)
    except Exception as e:
        print("Error opening camera:", e)
        return

    if not cap.isOpened():
        print("Error: Could not open camera at all.")
        return

    print("Camera opened successfully.")
    last_trigger_time = 0

    while True:
        try:
            ret, frame = cap.read()
            if not ret or frame is None:
                print("Failed to grab frame, retrying...")
                time.sleep(0.1)
                continue

            # Resize frame for model
            resized = cv2.resize(frame, (300, 300))

            # Preprocessing for res10 face model
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
                try:
                    check_missing_items()
                except Exception as e:
                    print("Error checking missing items:", e)
                last_trigger_time = current_time

            time.sleep(0.05)  # Reduce CPU usage

        except Exception as e:
            print("Unexpected error in camera loop:", e)
            time.sleep(1)
