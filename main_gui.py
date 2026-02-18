import tkinter as tk
import json
import time
import os
from add_item_window import AddItemWindow

DATA_FILE = "../raspberry_pi_backend/data/items.json"
MISSING_TIMEOUT = 30


class EDCGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Everyday Carry Detector")

        self.frame = tk.Frame(root)
        self.frame.pack(padx=10, pady=10)

        self.title = tk.Label(self.frame, text="Tracked Items", font=("Arial", 16))
        self.title.pack()

        self.items_frame = tk.Frame(self.frame)
        self.items_frame.pack()

        self.add_button = tk.Button(
            self.frame, text="Add Item", command=self.open_add_window
        )
        self.add_button.pack(pady=10)

        self.refresh()

    def load_items(self):
        if not os.path.exists(DATA_FILE):
            return {}

        with open(DATA_FILE, "r") as f:
            return json.load(f)

    def refresh(self):
        for widget in self.items_frame.winfo_children():
            widget.destroy()

        items = self.load_items()
        current_time = time.time()

        for mac, item in items.items():
            name = item.get("name", "Unknown")
            location = item.get("location", "unknown")
            last_seen = item.get("last_seen", 0)

            is_missing = current_time - last_seen > MISSING_TIMEOUT

            color = "red" if is_missing else "green"

            label = tk.Label(
                self.items_frame,
                text=f"{name} ({mac}) - {location}",
                fg=color,
            )
            label.pack(anchor="w")

        self.root.after(2000, self.refresh)

    def open_add_window(self):
        AddItemWindow(self.root)


if __name__ == "__main__":
    root = tk.Tk()
    gui = EDCGUI(root)
    root.mainloop()
