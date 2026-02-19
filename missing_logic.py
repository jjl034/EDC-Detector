import database
import time

# Store items globally in memory
items_list = []  # list of dicts: {"id", "name", "mac", "last_seen"}

def load_items():
    """Load items from DB and return as a list of dicts"""
    global items_list
    db = database.DB()
    db_items = db.get_items()  # returns list of tuples from DB
    items_list = []
    for row in db_items:
        item_id, name, desc, mac = row
        items_list.append({
            "id": item_id,
            "name": name,
            "desc": desc,
            "mac": mac,
            "last_seen": None  # default None
        })
    return items_list

def save_items():
    """Save current items back to DB if needed"""
    db = database.DB()
    for item in items_list:
        db.update_item(item["id"], item["name"], item["desc"], item["mac"])

def check_missing_items():
    """
    Return list of items considered 'missing'.
    For now, any item with last_seen older than some threshold
    """
    missing = []
    now = time.time()
    for item in items_list:
        last_seen = item.get("last_seen")
        if last_seen is None or (now - last_seen) > 60:  # 60 sec threshold
            missing.append(item)
    return missing

def update_last_seen(mac):
    """Update last_seen time for an item based on MAC"""
    now = time.time()
    for item in items_list:
        if item["mac"].lower() == mac.lower():
            item["last_seen"] = now
            break
