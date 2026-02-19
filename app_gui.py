import kivy
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup

from missing_logic import load_items, save_items
from mqtt_handler import start_mqtt

kivy.require("2.3.1")

# Global dictionary keyed by MAC
items = load_items()
item_dict = {item["mac"].lower(): item for item in items}

# Function to trigger missing item popup
def trigger_missing_popup(item_name, last_seen):
    popup = Popup(title="Missing Item Detected",
                  content=Label(text=f"{item_name} is missing!\nLast seen: {last_seen}"),
                  size_hint=(0.6, 0.4))
    popup.open()


# ---------- Screens ----------
class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation="vertical", padding=10, spacing=10)
        self.add_widget(self.layout)
        self.refresh_dashboard()

    def refresh_dashboard(self):
        self.layout.clear_widgets()
        self.layout.add_widget(Label(text="Your Items", font_size=24, size_hint_y=None, height=40))
        grid = GridLayout(cols=2, spacing=5, size_hint_y=None)
        grid.bind(minimum_height=grid.setter('height'))

        if not item_dict:
            grid.add_widget(Label(text="No items found"))
        else:
            for item in item_dict.values():
                grid.add_widget(Label(text=item["name"]))
                status = "Present" if item.get("present", True) else "Missing"
                grid.add_widget(Label(text=status))

        self.layout.add_widget(grid)

        add_btn = Button(text="Add Item", size_hint_y=None, height=40)
        add_btn.bind(on_release=lambda x: self.manager.current = "add_item")  # Navigate to AddItemScreen
        self.layout.add_widget(add_btn)


class AddItemScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation="vertical", padding=10, spacing=10)
        self.add_widget(self.layout)

        self.name_input = TextInput(hint_text="Item Name", size_hint_y=None, height=40)
        self.mac_input = TextInput(hint_text="Item MAC Address", size_hint_y=None, height=40)

        self.layout.add_widget(self.name_input)
        self.layout.add_widget(self.mac_input)

        add_btn = Button(text="Add", size_hint_y=None, height=40)
        add_btn.bind(on_release=self.add_item)
        self.layout.add_widget(add_btn)

        back_btn = Button(text="Back", size_hint_y=None, height=40)
        back_btn.bind(on_release=lambda x: self.manager.current = "main")
        self.layout.add_widget(back_btn)

    def add_item(self, instance):
        name = self.name_input.text.strip()
        mac = self.mac_input.text.strip().lower()
        if name and mac and mac not in item_dict:
            new_item = {"name": name, "mac": mac, "present": True, "last_seen": "added via GUI"}
            item_dict[mac] = new_item
            save_items(list(item_dict.values()))
            self.manager.get_screen("main").refresh_dashboard()
            self.name_input.text = ""
            self.mac_input.text = ""
            self.manager.current = "main"
        else:
            popup = Popup(title="Error",
                          content=Label(text="Invalid name or MAC already exists"),
                          size_hint=(0.6, 0.4))
            popup.open()


# ---------- App ----------
class EverydayCarryApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MainScreen(name="main"))
        sm.add_widget(AddItemScreen(name="add_item"))
        start_mqtt()  # Start MQTT in background
        return sm


if __name__ == "__main__":
    EverydayCarryApp().run()
