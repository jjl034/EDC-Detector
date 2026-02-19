# app_gui.py
import kivy
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.clock import Clock
from missing_logic import load_items, save_items

# Load items at startup
items = load_items()  # items is now a list of dicts: [{"name": "Wallet", "mac": "...", "last_seen": "..."}]

class DashboardScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation="vertical")
        self.items_layout = BoxLayout(orientation="vertical", size_hint_y=None)
        self.items_layout.bind(minimum_height=self.items_layout.setter('height'))
        self.add_widget(self.layout)
        self.layout.add_widget(Label(text="Your Items", size_hint_y=None, height=40))

        # Button to go to Add Item
        add_btn = Button(text="Add Item", size_hint_y=None, height=50)
        add_btn.bind(on_release=self.go_to_add_item)
        self.layout.add_widget(add_btn)
        self.layout.add_widget(self.items_layout)
        self.refresh_items()

    def go_to_add_item(self, instance):
        self.manager.current = "add_item"

    def refresh_items(self):
        self.items_layout.clear_widgets()
        if not items:
            self.items_layout.add_widget(Label(text="No items found"))
        else:
            for item in items:
                last_seen = item.get("last_seen", "Unknown")
                self.items_layout.add_widget(Label(text=f"{item['name']} - Last seen: {last_seen}"))

    def on_enter(self):
        # Refresh when entering dashboard
        self.refresh_items()


class AddItemScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical")
        self.add_widget(layout)

        layout.add_widget(Label(text="Item Name:"))
        self.name_input = TextInput(multiline=False)
        layout.add_widget(self.name_input)

        layout.add_widget(Label(text="MAC Address:"))
        self.mac_input = TextInput(multiline=False)
        layout.add_widget(self.mac_input)

        save_btn = Button(text="Save Item")
        save_btn.bind(on_release=self.save_item)
        layout.add_widget(save_btn)

        back_btn = Button(text="Back to Dashboard")
        back_btn.bind(on_release=lambda x: setattr(self.manager, "current", "dashboard"))
        layout.add_widget(back_btn)

    def save_item(self, instance):
        name = self.name_input.text.strip()
        mac = self.mac_input.text.strip()
        if not name or not mac:
            popup = Popup(title="Error", content=Label(text="Both fields are required!"),
                          size_hint=(0.6, 0.4))
            popup.open()
            return

        # Save item
        new_item = {"name": name, "mac": mac, "last_seen": "Never"}
        items.append(new_item)
        save_items(items)
        self.manager.get_screen("dashboard").refresh_items()
        self.name_input.text = ""
        self.mac_input.text = ""
        self.manager.current = "dashboard"


class EverydayCarryApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(DashboardScreen(name="dashboard"))
        sm.add_widget(AddItemScreen(name="add_item"))

        # Start camera/person detection or MQTT simulation
        Clock.schedule_interval(self.detect_missing_items, 2)  # every 2 seconds
        return sm

    def detect_missing_items(self, dt):
        # Here you integrate your camera/ESP32 detection logic
        # For demo: check for missing items
        for item in items:
            # Simulated detection: mark random items as missing (replace this with real detection)
            import random
            if random.choice([True, False]):
                popup = Popup(title="Missing Item Detected",
                              content=Label(text=f"{item['name']} missing! Last seen at {item.get('last_seen', 'Unknown')}"),
                              size_hint=(0.8, 0.4))
                popup.open()


if __name__ == "__main__":
    EverydayCarryApp().run()
