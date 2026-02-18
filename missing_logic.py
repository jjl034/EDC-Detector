import json
import time
from pathlib import Path

DATA_FILE = Path.home() / "EDC-Detector" / "data" / "items.json"
LOGBOOK_FILE = Path.home() / "EDC-Detector" / "data" / "logbook.json"

MISSING_TIMEOUT = 30  # seconds

# Ensure directories/files exist
DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
LOGBOOK_FILE.parent.mkdir(parents=True, exist_ok=True)

if not DATA_FILE.exists():
    DATA_FILE.write_text("[]")
if not LOGBOOK_FILE.exists():
    LOGBOOK_FILE.write_text("[]")


def load_items():
    with open(DATA_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def log_event(entry):
    with open(LOGBOOK_FILE, "r") as f:
        try:
            logbook = json.load(f)
        except json.JSONDecodeError:
            logbook = []

    logbook.append(entry)

    with open(LOGBOOK_FILE, "w") as f:
        json.dump(logbook, f, indent=4)


def check_missing_items():
    items = load_items()
    current_time = time.time()

    missing = []

    for item in items:
        if not isinstance(item, dict):
            print("Skipping invalid item:", item)
            continue
        last_seen = item.get("last_seen", 0)
        mac = item.get("mac", "").lower()
        required = item.get("required", True)
        if required and current_time - last_seen > MISSING_TIMEOUT:
            missing.append(item.get("name", mac))
            log_event({"timestamp": current_time, "mac": mac, "event": "missing"})

    if missing:
        print("Missing items:")
        for m in missing:
            print(f"- {m}")
    else:
        print("All required items present.")
