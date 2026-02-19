import json
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from missing_logic import load_items, add_item
import threading
import mqtt_handler  # Your MQTT integration

# Global reference for mqtt_handler to call GUI popup
gui_app = None

class DashboardScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation="vertical", spacing=10, padding=10)
        self.items_layout = BoxLayout(orientation="vertical", spacing=5)
        self.layout.add_widget(Label(text="Everyday Carry Dashboard", font_size=24, size_hint_y=None, height=40))
        self.layout.add_widget(self.items_layout)

        add_btn = Button(text="Add Item", size_hint_y=None, height=50)
        add_btn.bind(on_release=lambda x: self.manager.current = "add_item")
        self.layout.add_widget(add_btn)

        self.add_widget(self.layout)
        self.refresh_items()

    def refresh_items(self):
        self.items_layout.clear_widgets()
        items = load_items()
        if not items:
            self.items_layout.add_widget(Label(text="No items found"))
        else:
            for item in items:
                status = "Present" if item.get("present", True) else "Missing"
                last = item.get("last_seen", "unknown")
                self.items_layout.add_widget(Label(text=f"{item['name']} ({status}) - Last seen: {last}"))

class AddItemScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical", spacing=10, padding=10)
        layout.add_widget(Label(text="Add New Item", font_size=24, size_hint_y=None, height=40))

        self.name_input = TextInput(hint_text="Item Name", multiline=False)
        self.mac_input = TextInput(hint_text="Item MAC (xx:xx:xx:xx:xx:xx)", multiline=False)

        layout.add_widget(self.name_input)
        layout.add_widget(self.mac_input)

        save_btn = Button(text="Save Item", size_hint_y=None, height=50)
        save_btn.bind(on_release=self.save_item)
        layout.add_widget(save_btn)

        back_btn = Button(text="Back to Dashboard", size_hint_y=None, height=50)
        back_btn.bind(on_release=lambda x: self.manager.current = "dashboard")
        layout.add_widget(back_btn)

        self.add_widget(layout)

    def save_item(self, instance):
        name = self.name_input.text.strip()
        mac = self.mac_input.text.strip().lower()
        if name and mac:
            add_item(name, mac)
            self.name_input.text = ""
            self.mac_input.text = ""
            self.manager.get_screen("dashboard").refresh_items()
            self.manager.current = "dashboard"
        else:
            popup = Popup(title="Error", content=Label(text="Name and MAC are required"), size_hint=(0.7, 0.3))
            popup.open()

class EverydayCarryApp(App):
    def build(self):
        global gui_app
        gui_app = self

        sm = ScreenManager()
        sm.add_widget(DashboardScreen(name="dashboard"))
        sm.add_widget(AddItemScreen(name="add_item"))

        # Start MQTT in a background thread
        threading.Thread(target=mqtt_handler.start_mqtt, daemon=True).start()

        return sm

    # Called by mqtt_handler to show missing item popup
    def show_missing_item_popup(self, name, last_seen):
        popup = Popup(title="Missing Item Detected",
                      content=Label(text=f"Item '{name}' is missing!\nLast seen: {last_seen}"),
                      size_hint=(0.7, 0.4))
        popup.open()
        # Refresh dashboard to update missing status
        self.root.get_screen("dashboard").refresh_items()


if __name__ == "__main__":
    EverydayCarryApp().run()
