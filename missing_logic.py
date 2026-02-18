# missing_logic.py
import json
import time
from pathlib import Path

# Paths for data storage
DATA_FILE = Path(__file__).parent / "data/items.json"
LOGBOOK_FILE = Path(__file__).parent / "data/logbook.json"

# Timeout for considering an item missing (seconds)
MISSING_TIMEOUT = 30  

# Ensure data folder exists
DATA_FILE.parent.mkdir(parents=True, exist_ok=True)

# Initialize files if they don't exist
if not DATA_FILE.exists():
    DATA_FILE.write_text(json.dumps({}))
if not LOGBOOK_FILE.exists():
    LOGBOOK_FILE.write_text(json.dumps([]))


def load_items():
    """Load items from the JSON file."""
    with open(DATA_FILE, "r") as f:
        items = json.load(f)
    # Normalize all MAC addresses to lowercase
    return {mac.lower(): data for mac, data in items.items()}


def save_items(items):
    """Save items dictionary to the JSON file."""
    with open(DATA_FILE, "w") as f:
        json.dump(items, f, indent=4)


def log_event(entry):
    """Append an event to the logbook."""
    with open(LOGBOOK_FILE, "r") as f:
        logbook = json.load(f)
    logbook.append(entry)
    with open(LOGBOOK_FILE, "w") as f:
        json.dump(logbook, f, indent=4)


def check_missing_items():
    """Check which required items are missing and log them."""
    items = load_items()
    current_time = time.time()

    missing = []

    for mac, item in items.items():
        # Skip invalid entries
        if not isinstance(item, dict):
            print("Skipping invalid item:", item)
            continue

        # Check if item is required (default True)
        required = item.get("required", True)
        if not required:
            continue

        last_seen = item.get("last_seen", 0)
        if current_time - last_seen > MISSING_TIMEOUT:
            print(f"Item missing: {mac} ({item.get('name', 'Unknown')})")
            missing.append(item.get("name", mac))

            # Log the missing event
            log_event({
                "timestamp": current_time,
                "mac": mac,
                "event": "missing"
            })

    if missing:
        print("Missing items:")
        for m in missing:
            print("-", m)
    else:
        print("All required items present.")
