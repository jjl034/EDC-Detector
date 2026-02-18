import json
from pathlib import Path

DATA_FILE = Path.home() / "EDC-Detector" / "data" / "items.json"
LOGBOOK_FILE = Path.home() / "EDC-Detector" / "data" / "logbook.json"

# Ensure directories exist
DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
LOGBOOK_FILE.parent.mkdir(parents=True, exist_ok=True)

# Ensure files exist
if not DATA_FILE.exists():
    with open(DATA_FILE, "w") as f:
        json.dump([], f)  # empty list to hold items

if not LOGBOOK_FILE.exists():
    with open(LOGBOOK_FILE, "w") as f:
        json.dump([], f)  # empty list to hold log entries

def save_item_to_file(item):
    """
    Adds a new item dict to items.json.
    """
    with open(DATA_FILE, "r") as f:
        try:
            items = json.load(f)
            if not isinstance(items, list):
                items = []
        except json.JSONDecodeError:
            items = []

    items.append(item)

    with open(DATA_FILE, "w") as f:
        json.dump(items, f, indent=4)

def log_event(entry):
    """
    Appends an entry to the logbook file.
    """
    with open(LOGBOOK_FILE, "r") as f:
        try:
            logbook = json.load(f)
            if not isinstance(logbook, list):
                logbook = []
        except json.JSONDecodeError:
            logbook = []

    logbook.append(entry)

    with open(LOGBOOK_FILE, "w") as f:
        json.dump(logbook, f, indent=4)
