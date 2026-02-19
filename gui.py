# app_gui.py
import kivy
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.core.window import Window

import json
import os

import paho.mqtt.client as mqtt
from threading import Thread

kivy.require("2.3.1")

ITEMS_FILE = "items.json"
MQTT_BROKER = "172.20.10.9"  # Raspberry Pi IP
MQTT_PORT = 1883
MQTT_TOPIC = "edc/devices"

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
    popup = Popup(
        title="Missing Item",
        content=content,
        size_hint=(None, None),
        size=(250, 100),
        auto_dismiss=True,
        separator_height=0
    )
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

        self.add_btn = Button(text="Add Item", size_hint_y=None, height=40)
        self.add_btn.bind(on_release=self.go_to_add_item)
        self.refresh_dashboard()

    def go_to_add_item(self, instance):
        self.manager.current = "add_item"

    def refresh_dashboard(self):
        self.layout.clear_widgets()
        for item_name, item in self.items.items():
            self.layout.add_widget(
                Label(text=f"{item_name} - Last seen: {item.get('last_seen','Never')}")
            )
        self.layout.add_widget(self.add_btn)

    def update_item_last_seen(self, item_name, last_seen):
        if item_name in self.items:
            self.items[item_name]["last_seen"] = last_seen
            save_items(self.items)
            self.refresh_dashboard()
            show_missing_popup(item_name, last_seen)

class AddItemScreen(Screen):
    def __init__(self, main_screen, **kwargs):
        super().__init__(**kwargs)
        self.main_screen = main_screen
        layout = BoxLayout(orientation="vertical", padding=10, spacing=5)
        self.name_input = TextInput(hint_text="Item Name", multiline=False, size_hint_y=None, height=40)
        layout.add_widget(self.name_input)
        self.mac_input = TextInput(hint_text="MAC/ID", multiline=False, size_hint_y=None, height=40)
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
# MQTT Handling
# ---------------------
def on_mqtt_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        mac = data.get("mac", "")
        location = data.get("location", "Unknown")
        for item_name, item in userdata["main_screen"].items.items():
            if item.get("mac", "").lower() == mac.lower():
                # Update last_seen to ESP32 location
                Clock.schedule_once(lambda dt, n=item_name, l=location: userdata["main_screen"].update_item_last_seen(n, l))
    except Exception as e:
        print("MQTT parse error:", e)

def mqtt_thread(main_screen):
    client = mqtt.Client()
    client.user_data_set({"main_screen": main_screen})
    client.on_message = on_mqtt_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.subscribe(MQTT_TOPIC)
    client.loop_forever()

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

        # Start MQTT listener thread
        Thread(target=mqtt_thread, args=(main_screen,), daemon=True).start()

        return sm

if __name__ == "__main__":
    EverydayCarryApp().run()
