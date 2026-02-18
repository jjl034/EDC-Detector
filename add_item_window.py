import tkinter as tk
import json
import os

DATA_FILE = "../raspberry_pi_backend/data/items.json"


class AddItemWindow:
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("Add New Item")

        tk.Label(self.window, text="Item Name").pack()
        self.name_entry = tk.Entry(self.window)
        self.name_entry.pack()

        tk.Label(self.window, text="MAC Address").pack()
        self.mac_entry = tk.Entry(self.window)
        self.mac_entry.pack()

        tk.Button(self.window, text="Save", command=self.save_item).pack(pady=10)

    def save_item(self):
        name = self.name_entry.get().strip()
        mac = self.mac_entry.get().strip().lower()  # normalize lowercase

        if not name or not mac:
            return

        if not os.path.exists(DATA_FILE):
            items = {}
        else:
            with open(DATA_FILE, "r") as f:
                items = json.load(f)

        if mac not in items:
            items[mac] = {
                "name": name,
                "last_seen": 0,
                "location": "unknown",
                "rssi": 0
            }
        else:
            items[mac]["name"] = name

        with open(DATA_FILE, "w") as f:
            json.dump(items, f, indent=4)

        self.window.destroy()
