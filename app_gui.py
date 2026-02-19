import json
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
import os

ITEMS_FILE = "items.json"

def load_items():
    if os.path.exists(ITEMS_FILE):
        with open(ITEMS_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_items(items):
    with open(ITEMS_FILE, "w") as f:
        json.dump(items, f, indent=2)

# Custom corner popup for notifications
class Notification(Label):
    def __init__(self, text, **kwargs):
        super().__init__(**kwargs)
        self.text = text
        self.size_hint = (None, None)
        self.size = (250, 50)
        self.pos_hint = {"right": 0.98, "y": 0.02}  # bottom-right corner
        self.color = (1, 1, 1, 1)
        with self.canvas.before:
            Color(0, 0, 0, 0.8)
            self.rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_rect, size=self.update_rect)
        Clock.schedule_once(self.dismiss, 5)  # auto-dismiss in 5 seconds

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def dismiss(self, dt):
        if self.parent:
            self.parent.remove_widget(self)

# Screens
class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical", padding=10, spacing=10)
        self.item_container = BoxLayout(orientation="vertical", spacing=5)
        layout.add_widget(self.item_container)

        btn_layout = BoxLayout(size_hint_y=None, height=50, spacing=10)
        add_btn = Button(text="Add Item")
        add_btn.bind(on_release=lambda x: self.manager.current_screen.manager.current="add_item")
        btn_layout.add_widget(add_btn)
        layout.add_widget(btn_layout)
        self.add_widget(layout)
        self.refresh_items()

    def refresh_items(self):
        self.item_container.clear_widgets()
        items = load_items()
        if not items:
            self.item_container.add_widget(Label(text="No items found"))
        for item in items:
            self.item_container.add_widget(Label(text=f"{item['name']} (Last seen: {item.get('last_seen','Unknown')})"))

class AddItemScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical", padding=10, spacing=10)
        self.name_input = TextInput(hint_text="Item Name", multiline=False)
        self.mac_input = TextInput(hint_text="Item MAC/ID", multiline=False)
        layout.add_widget(self.name_input)
        layout.add_widget(self.mac_input)

        btn_layout = BoxLayout(size_hint_y=None, height=50, spacing=10)
        save_btn = Button(text="Save Item")
        save_btn.bind(on_release=self.save_item)
        cancel_btn = Button(text="Cancel")
        cancel_btn.bind(on_release=lambda x: self.manager.current="main")
        btn_layout.add_widget(save_btn)
        btn_layout.add_widget(cancel_btn)

        layout.add_widget(btn_layout)
        self.add_widget(layout)

    def save_item(self, instance):
        items = load_items()
        items.append({
            "name": self.name_input.text.strip(),
            "mac": self.mac_input.text.strip(),
            "last_seen": "Just Added"
        })
        save_items(items)
        self.manager.current = "main"
        self.manager.get_screen("main").refresh_items()

# Main app
class EverydayCarryApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MainScreen(name="main"))
        sm.add_widget(AddItemScreen(name="add_item"))
        Clock.schedule_interval(self.check_missing_items, 2)  # check every 2 seconds
        return sm

    # Corner popup
    def show_notification(self, message):
        notification = Notification(text=message)
        self.root.add_widget(notification)

    # Placeholder camera detection callback
    def check_missing_items(self, dt):
        """
        This function should be linked to your camera detection logic.
        When an item is missing, call self.show_notification with its name & last_seen.
        """
        items = load_items()
        # Example simulation for testing:
        for item in items:
            if item.get("last_seen") != "Present":
                self.show_notification(f"Missing: {item['name']}\nLast seen: {item.get('last_seen','Unknown')}")
                item["last_seen"] = "Present"  # simulate detection reset
        save_items(items)

if __name__ == "__main__":
    EverydayCarryApp().run()
