import json
import time
import os

DATA_FILE = "data/items.json"
LOGBOOK_FILE = "data/logbook.json"

MISSING_TIMEOUT = 30  # seconds


def load_items():
    """Load items from JSON, create empty file if missing."""
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump([], f, indent=4)
        return []

    with open(DATA_FILE, "r") as f:
        return json.load(f)


def log_event(entry):
    """Append an event to the logbook, create file if missing."""
    if not os.path.exists(LOGBOOK_FILE):
        with open(LOGBOOK_FILE, "w") as f:
            json.dump([], f, indent=4)

    with open(LOGBOOK_FILE, "r") as f:
        try:
            logbook = json.load(f)
        except json.JSONDecodeError:
            logbook = []

    logbook.append(entry)

    with open(LOGBOOK_FILE, "w") as f:
        json.dump(logbook, f, indent=4)


def check_missing_items():
    """Check all required items and print/log missing ones."""
    items = load_items()
    current_time = time.time()

    missing = []

    for item in items:
        required = item.get("required", True)
        last_seen = item.get("last_seen", 0)

        if required and (current_time - last_seen) > MISSING_TIMEOUT:
            missing.append(item.get("name", "Unknown"))
            log_event({
                "timestamp": current_time,
                "mac": item.get("mac", "Unknown"),
                "event": "missing"
            })

    if missing:
        print("Missing items:")
        for name in missing:
            print("-", name)
    else:
        print("All required items present.")

