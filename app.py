import threading
from mqtt_handler import start_mqtt
from camera_monitor import monitor_camera

if __name__ == "__main__":
    print("Starting EDC Backend...")

    # Start camera monitor thread
    threading.Thread(target=monitor_camera, daemon=True).start()

    # Start MQTT (blocking)
    start_mqtt()
