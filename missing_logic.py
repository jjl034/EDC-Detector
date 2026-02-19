import json
import os

ITEMS_FILE = "items.json"

# Load items from JSON file
def load_items():
    if not os.path.exists(ITEMS_FILE):
        return []

    try:
        with open(ITEMS_FILE, "r") as f:
            items = json.load(f)
            # Ensure each item has the required keys
            for item in items:
                if "name" not in item:
                    item["name"] = "Unnamed"
                if "mac" not in item:
                    item["mac"] = "unknown"
                if "present" not in item:
                    item["present"] = True
                if "last_seen" not in item:
                    item["last_seen"] = "unknown"
            return items
    except json.JSONDecodeError:
        return []

# Save items to JSON file
def save_items(items_list):
    with open(ITEMS_FILE, "w") as f:
        json.dump(items_list, f, indent=4)

# Optional: Get dict keyed by MAC for quick lookup
def items_dict():
    return {item["mac"].lower(): item for item in load_items()}

# Update an item in place
def update_item(mac, present=None, last_seen=None):
    items = load_items()
    mac = mac.lower()
    updated = False
    for item in items:
        if item["mac"].lower() == mac:
            if present is not None:
                item["present"] = present
            if last_seen is not None:
                item["last_seen"] = last_seen
            updated = True
            break
    if updated:
        save_items(items)
    return updated
