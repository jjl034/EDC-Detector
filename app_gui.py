import json
from pathlib import Path
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock
import threading
import paho.mqtt.client as mqtt

# --- File and MQTT Config ---
DATA_FILE = Path("./data/items.json")
BROKER = "localhost"  # Replace with your MQTT broker IP
TOPIC = "edc/missing"

# --- MQTT Setup ---
mqtt_client = mqtt.Client()


def load_items():
    if not DATA_FILE.exists():
        return []
    with open(DATA_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def save_items(items):
    DATA_FILE.parent.mkdir(exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(items, f, indent=2)


# --- GUI Screens ---
class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation="vertical", spacing=10, padding=10)
        self.items_layout = BoxLayout(orientation="vertical", spacing=5, size_hint_y=None)
        self.items_layout.bind(minimum_height=self.items_layout.setter('height'))
        self.layout.add_widget(self.items_layout)

        self.add_btn = Button(text="Add Item", size_hint_y=None, height=50)
        self.add_btn.bind(on_release=lambda x: self.manager.current = "add_item")
        self.layout.add_widget(self.add_btn)

        self.add_widget(self.layout)
        Clock.schedule_once(lambda dt: self.update_dashboard(), 0.1)

    def update_dashboard(self):
        self.items_layout.clear_widgets()
        items = load_items()
        if not items:
            self.items_layout.add_widget(Label(text="No items found"))
        else:
            for item in items:
                name = item.get("name", "Unnamed")
                last_seen = item.get("last_seen", "Unknown")
                self.items_layout.add_widget(Label(text=f"{name} (Last Seen: {last_seen})"))


class AddItemScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation="vertical", spacing=10, padding=10)
        self.name_input = TextInput(hint_text="Item Name", multiline=False, size_hint_y=None, height=40)
        self.layout.add_widget(self.name_input)

        self.save_btn = Button(text="Save Item", size_hint_y=None, height=50)
        self.save_btn.bind(on_release=self.save_item)
        self.layout.add_widget(self.save_btn)

        self.back_btn = Button(text="Back", size_hint_y=None, height=50)
        self.back_btn.bind(on_release=lambda x: self.manager.current = "main")
        self.layout.add_widget(self.back_btn)

        self.add_widget(self.layout)

    def save_item(self, instance):
        name = self.name_input.text.strip()
        if not name:
            return
        items = load_items()
        items.append({"name": name, "last_seen": "Unknown"})
        save_items(items)
        self.name_input.text = ""
        self.manager.current = "main"
        Clock.schedule_once(lambda dt: self.manager.get_screen("main").update_dashboard(), 0.1)


# --- Missing Item Popup ---
def show_missing_item_popup(name, last_seen):
    content = BoxLayout(orientation="vertical", spacing=10, padding=10)
    content.add_widget(Label(text=f"Missing Item Detected!\n{name}\nLast Seen: {last_seen}"))
    btn = Button(text="OK", size_hint_y=None, height=50)
    content.add_widget(btn)
    popup = Popup(title="Alert!", content=content, size_hint=(0.6, 0.4))
    btn.bind(on_release=popup.dismiss)
    popup.open()


# --- MQTT Callback ---
def on_mqtt_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        name = data.get("name", "Unknown")
        last_seen = data.get("last_seen", "Unknown")

        # Update last_seen in items.json
        items = load_items()
        for item in items:
            if item["name"] == name:
                item["last_seen"] = last_seen
        save_items(items)

        # Update dashboard and show popup on main thread
        Clock.schedule_once(lambda dt: (
            App.get_running_app().sm.get_screen("main").update_dashboard(),
            show_missing_item_popup(name, last_seen)
        ))
    except Exception as e:
        print(f"Error handling MQTT message: {e}")


# --- MQTT Thread ---
def start_mqtt():
    mqtt_client.on_message = on_mqtt_message
    mqtt_client.connect(BROKER, 1883, 60)
    mqtt_client.subscribe(TOPIC)
    mqtt_client.loop_forever()


# --- App ---
class EverydayCarryApp(App):
    def build(self):
        self.sm = ScreenManager()
        self.sm.add_widget(MainScreen(name="main"))
        self.sm.add_widget(AddItemScreen(name="add_item"))

        # Start MQTT in background
        threading.Thread(target=start_mqtt, daemon=True).start()
        return self.sm


if __name__ == "__main__":
    EverydayCarryApp().run()
