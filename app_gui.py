# app_gui.py
import os
import json
from functools import partial
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.clock import Clock
from mqtt_handler import start_mqtt  # your MQTT integration

ITEMS_FILE = "items.json"

# ------------------ Item Logic ------------------
def load_items():
    if not os.path.exists(ITEMS_FILE):
        return {}
    with open(ITEMS_FILE, "r") as f:
        try:
            items = json.load(f)
            # convert list of dicts to dict keyed by MAC
            return {item["mac"].lower(): item for item in items}
        except json.JSONDecodeError:
            return {}

def save_items(items_dict):
    # convert dict back to list
    with open(ITEMS_FILE, "w") as f:
        json.dump(list(items_dict.values()), f, indent=2)

# ------------------ GUI Screens ------------------
class DashboardScreen(Screen):
    def on_enter(self):
        self.update_dashboard()

    def update_dashboard(self):
        self.ids.dashboard_layout.clear_widgets()
        items = load_items()
        if not items:
            self.ids.dashboard_layout.add_widget(Label(text="No items found"))
        else:
            for mac, item in items.items():
                lbl = Label(text=f"{item['name']} (Last seen: {item.get('last_seen', 'Unknown')})")
                self.ids.dashboard_layout.add_widget(lbl)

class AddItemScreen(Screen):
    def add_item(self, name_input, mac_input):
        name = name_input.text.strip()
        mac = mac_input.text.strip().lower()
        if not name or not mac:
            popup = Popup(title="Error", content=Label(text="Name and MAC required"), size_hint=(0.5,0.5))
            popup.open()
            return
        items = load_items()
        items[mac] = {"name": name, "mac": mac, "last_seen": "Unknown"}
        save_items(items)
        # Clear inputs
        name_input.text = ""
        mac_input.text = ""
        # Go back to dashboard
        self.manager.current = "dashboard"
        self.manager.get_screen("dashboard").update_dashboard()

# ------------------ Popup for Missing Item ------------------
def show_missing_item_popup(item_name, last_seen):
    content = BoxLayout(orientation="vertical")
    content.add_widget(Label(text=f"Missing Item: {item_name}\nLast seen: {last_seen}"))
    btn = Button(text="OK", size_hint=(1, 0.3))
    content.add_widget(btn)
    popup = Popup(title="Missing Item Detected", content=content, size_hint=(0.6,0.4))
    btn.bind(on_release=popup.dismiss)
    popup.open()

# ------------------ App ------------------
class EverydayCarryApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(DashboardScreen(name="dashboard"))
        sm.add_widget(AddItemScreen(name="add_item"))
        # Start MQTT with callback to popup
        start_mqtt(popup_callback=self.on_missing_item)
        return sm

    def on_missing_item(self, mac):
        items = load_items()
        item = items.get(mac.lower())
        if item:
            last_seen = item.get("last_seen", "Unknown")
            # Update last seen to "Detected missing"
            item["last_seen"] = "Missing!"
            save_items(items)
            # Update dashboard
            self.root.get_screen("dashboard").update_dashboard()
            # Show popup
            Clock.schedule_once(lambda dt: show_missing_item_popup(item["name"], last_seen))

# ------------------ Kivy GUI Layout ------------------
from kivy.lang import Builder

KV = """
ScreenManager:
    DashboardScreen:
    AddItemScreen:

<DashboardScreen>:
    name: "dashboard"
    BoxLayout:
        orientation: "vertical"
        padding: 10
        spacing: 10
        ScrollView:
            GridLayout:
                id: dashboard_layout
                cols: 1
                size_hint_y: None
                height: self.minimum_height
        Button:
            text: "Add Item"
            size_hint_y: 0.1
            on_release: app.root.current = "add_item"

<AddItemScreen>:
    name: "add_item"
    BoxLayout:
        orientation: "vertical"
        padding: 10
        spacing: 10
        Label:
            text: "Add New Item"
            size_hint_y: 0.1
        TextInput:
            id: name_input
            hint_text: "Item Name"
            size_hint_y: 0.1
        TextInput:
            id: mac_input
            hint_text: "Item MAC Address"
            size_hint_y: 0.1
        Button:
            text: "Save Item"
            size_hint_y: 0.1
            on_release: root.add_item(name_input, mac_input)
        Button:
            text: "Back to Dashboard"
            size_hint_y: 0.1
            on_release: app.root.current = "dashboard"
"""

Builder.load_string(KV)

# ------------------ Run App ------------------
if __name__ == "__main__":
    EverydayCarryApp().run()
    
