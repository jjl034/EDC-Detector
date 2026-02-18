from threading import Thread
from mqtt_handler import start_mqtt
from camera_monitor import monitor_camera

if __name__ == "__main__":
    print("Starting EDC Backend...")

    # Start MQTT handler
    start_mqtt()

    # Start camera monitoring in a separate thread
    camera_thread = Thread(target=monitor_camera)
    camera_thread.daemon = True
    camera_thread.start()

    # Keep main thread alive
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("\nExiting...")
