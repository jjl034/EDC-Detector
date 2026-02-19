# app_gui.py
import kivy
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from kivy.uix.popup import Popup
from kivy.core.window import Window

import json
import os
from threading import Thread
import time
import random
import cv2  # USB camera
import requests  # for ESP32 HTTP BLE API simulation

kivy.require('2.3.1')

ITEMS_FILE = "items.json"

# ---------------------
# Items Load/Save
# ---------------------
def load_items():
    if os.path.exists(ITEMS_FILE):
        with open(ITEMS_FILE, "r") as f:
            try:
                items = json.load(f)
                if isinstance(items, list):
                    return {item["name"]: item for item in items}
                return items
            except:
                return {}
    return {}

def save_items(items):
    with open(ITEMS_FILE, "w") as f:
        json.dump(list(items.values()), f, indent=2)

# ---------------------
# GUI Popups
# ---------------------
def show_missing_popup(item_name, last_seen):
    content = BoxLayout(orientation="vertical", padding=5)
    content.add_widget(Label(text=f"Missing: {item_name}\nLast seen: {last_seen}", font_size=14))
    popup = Popup(title="Missing Item", content=content,
                  size_hint=(None, None), size=(250, 100),
                  auto_dismiss=True, separator_height=0)
    popup.pos = (Window.width - 260, Window.height - 120)
    popup.open()
    Clock.schedule_once(lambda dt: popup.dismiss(), 4)

# ---------------------
# Screens
# ---------------------
class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.items = load_items()
        self.layout = GridLayout(cols=1, spacing=5, padding=10)
        self.add_widget(self.layout)
        self.refresh_dashboard()

        add_btn = Button(text="Add Item", size_hint_y=None, height=40)
        add_btn.bind(on_release=self.go_to_add_item)
        self.layout.add_widget(add_btn)

    def go_to_add_item(self, instance):
        self.manager.current = "add_item"

    def refresh_dashboard(self):
        self.layout.clear_widgets()
        for item_name, item in self.items.items():
            self.layout.add_widget(Label(text=f"{item_name} - Last seen: {item.get('last_seen','N/A')}"))
        add_btn = Button(text="Add Item", size_hint_y=None, height=40)
        add_btn.bind(on_release=self.go_to_add_item)
        self.layout.add_widget(add_btn)

    def update_item_last_seen(self, item_name, last_seen):
        if item_name in self.items:
            self.items[item_name]["last_seen"] = last_seen
            save_items(self.items)
            self.refresh_dashboard()
            show_missing_popup(item_name, last_seen)

# ---------------------
# Add Item Screen
# ---------------------
class AddItemScreen(Screen):
    def __init__(self, main_screen, **kwargs):
        super().__init__(**kwargs)
        self.main_screen = main_screen
        layout = BoxLayout(orientation="vertical", padding=10, spacing=5)
        self.name_input = TextInput(hint_text="Item Name", multiline=False, size_hint_y=None, height=40)
        layout.add_widget(self.name_input)
        self.mac_input = TextInput(hint_text="MAC/ID (optional)", multiline=False, size_hint_y=None, height=40)
        layout.add_widget(self.mac_input)

        btn_layout = BoxLayout(size_hint_y=None, height=40, spacing=5)
        save_btn = Button(text="Save")
        save_btn.bind(on_release=self.save_item)
        back_btn = Button(text="Back")
        back_btn.bind(on_release=self.go_back)
        btn_layout.add_widget(save_btn)
        btn_layout.add_widget(back_btn)

        layout.add_widget(btn_layout)
        self.add_widget(layout)

    def save_item(self, instance):
        name = self.name_input.text.strip()
        mac = self.mac_input.text.strip()
        if not name:
            return
        self.main_screen.items[name] = {"name": name, "mac": mac, "last_seen": "Never"}
        save_items(self.main_screen.items)
        self.main_screen.refresh_dashboard()
        self.go_back(instance)

    def go_back(self, instance):
        self.manager.current = "main"

# ---------------------
# Camera Detection
# ---------------------
def camera_detection_loop(main_screen, esp32_addresses):
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("USB camera not detected")
        return
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        # Simulate person detection
        person_detected = random.choice([True, False, False])  # 33% chance
        if person_detected:
            check_missing_items(main_screen, esp32_addresses)
        time.sleep(2)
    cap.release()

# ---------------------
# ESP32 BLE Detection
# ---------------------
def check_missing_items(main_screen, esp32_addresses):
    """
    Contacts ESP32s via HTTP API to get currently seen BLE tags.
    Compares with saved items to detect missing ones.
    """
    seen_macs = set()
    for addr in esp32_addresses:
        try:
            # Example: ESP32 serves JSON {"seen": ["MAC1", "MAC2"]}
            resp = requests.get(f"http://{addr}/seen")
            if resp.status_code == 200:
                data = resp.json()
                seen_macs.update(data.get("seen", []))
        except:
            continue

    # Detect missing items
    for item_name, item in main_screen.items.items():
        mac = item.get("mac", "").lower()
        if mac and mac not in map(str.lower, seen_macs):
            last_seen = item.get("last_seen", "Unknown")
            # Update GUI on main thread
            Clock.schedule_once(lambda dt, n=item_name, l=last_seen: main_screen.update_item_last_seen(n, l))

# ---------------------
# App
# ---------------------
class EverydayCarryApp(App):
    def build(self):
        sm = ScreenManager()
        main_screen = MainScreen(name="main")
        add_screen = AddItemScreen(main_screen, name="add_item")
        sm.add_widget(main_screen)
        sm.add_widget(add_screen)

        # ESP32 IP addresses (replace with your ESP32 devices)
        esp32_addresses = ["172.20.10.7", "172.20.10.10"]

        # Start camera/person detection in thread
        detection_thread = Thread(target=camera_detection_loop, args=(main_screen, esp32_addresses), daemon=True)
        detection_thread.start()

        return sm

if __name__ == "__main__":
    EverydayCarryApp().run()

