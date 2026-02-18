import json
import time

DATA_FILE = "data/items.json"
LOGBOOK_FILE = "data/logbook.json"

MISSING_TIMEOUT = 30  # seconds


def load_items():
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def log_event(entry):
    with open(LOGBOOK_FILE, "r") as f:
        logbook = json.load(f)

    logbook.append(entry)

    with open(LOGBOOK_FILE, "w") as f:
        json.dump(logbook, f, indent=4)


def check_missing_items():
    items = load_items()
    current_time = time.time()

    for mac, item in items.items():
        last_seen = item.get("last_seen", 0)

        if current_time - last_seen > MISSING_TIMEOUT:
            print(f"Item missing: {mac}")

            log_event({
                "timestamp": current_time,
                "mac": mac,
                "event": "missing"
            })
