from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.metrics import dp
from kivy.graphics import Color, RoundedRectangle, Line
from pathlib import Path
import json
import os

# --- File Paths ---
DATA_FILE = Path(__file__).parent / "data/items.json"
DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
if not DATA_FILE.exists():
    with open(DATA_FILE, "w") as f:
        json.dump([], f)

# --- Theme ---
THEME = {
    "background": (0.1, 0.1, 0.14, 1),
    "surface": (0.2, 0.2, 0.23, 1),
    "surface_active": (0.25, 0.25, 0.28, 1),
    "primary": (0.0, 0.48, 1.0, 1),
    "accent": (0.2, 0.8, 0.6, 1),
    "text_primary": (1.0, 1.0, 1.0, 1),
    "text_secondary": (0.7, 0.7, 0.75, 1),
    "danger": (1.0, 0.27, 0.27, 1),
    "border_color": (1, 1, 1, 0.2)
}

# --- Global Items List ---
items_list = []

def load_items():
    global items_list
    try:
        with open(DATA_FILE, "r") as f:
            items_list = json.load(f)
    except Exception:
        items_list = []

def save_items():
    with open(DATA_FILE, "w") as f:
        json.dump(items_list, f, indent=2)

# --- Custom Widgets ---
class ProButton(Button):
    def __init__(self, bg_color=THEME["primary"], font_size=dp(16), radius=dp(8), **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_down = ""
        self.background_color = (0, 0, 0, 0)
        self.custom_bg_color = bg_color
        self.font_size = font_size
        self.bold = True
        self.color = THEME["text_primary"]
        self.radius = radius
        self.bind(pos=self.update_canvas, size=self.update_canvas, state=self.update_canvas)

    def update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            r, g, b, a = self.custom_bg_color
            if self.state == "down":
                Color(r*0.8, g*0.8, b*0.8, a)
            else:
                Color(*self.custom_bg_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[self.radius])

class ProInput(TextInput):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_active = ""
        self.background_color = THEME["surface"]
        self.foreground_color = THEME["text_primary"]
        self.hint_text_color = THEME["text_secondary"]
        self.cursor_color = THEME["primary"]
        self.padding = [dp(16)]*4
        self.font_size = dp(16)
        self.multiline = False
        self.size_hint_y = None
        self.height = dp(50)
        self.bind(pos=self.update_canvas, size=self.update_canvas, focus=self.update_canvas)
        self.update_canvas()

    def update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*THEME["surface_active"] if self.focus else THEME["surface"])
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)])
            Color(*THEME["primary"] if self.focus else THEME["border_color"])
            Line(rounded_rectangle=(self.x, self.y, self.width, self.height, dp(10)), width=1.2)

# --- Screens ---
class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        load_items()
        root = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(10))

        # Scrollable items list
        self.scroll = ScrollView(size_hint=(1, 1))
        self.grid = GridLayout(cols=1, spacing=dp(10), size_hint_y=None)
        self.grid.bind(minimum_height=self.grid.setter('height'))
        self.scroll.add_widget(self.grid)
        root.add_widget(self.scroll)

        # Add item button
        add_btn = ProButton(text="Add Item", bg_color=THEME["primary"], size_hint_y=None, height=dp(50))
        add_btn.bind(on_release=self.open_add_popup)
        root.add_widget(add_btn)

        self.add_widget(root)
        self.update_items()

    def update_items(self):
        self.grid.clear_widgets()
        if not items_list:
            self.grid.add_widget(Label(text="No items found. Tap 'Add Item' to add.", color=THEME["text_secondary"]))
            return
        for item in items_list:
            lbl = Label(text=f"{item['name']} | {item.get('desc','')} | Last Seen: {item.get('last_seen','N/A')}", size_hint_y=None, height=dp(40), color=THEME["text_primary"])
            self.grid.add_widget(lbl)

    def open_add_popup(self, instance):
        content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(10))
        name_input = ProInput(hint_text="Item Name")
        desc_input = ProInput(hint_text="Description")
        mac_input = ProInput(hint_text="MAC Address")
        save_btn = ProButton(text="Save")
        cancel_btn = ProButton(text="Cancel", bg_color=THEME["surface"])
        content.add_widget(name_input)
        content.add_widget(desc_input)
        content.add_widget(mac_input)
        btns = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        btns.add_widget(save_btn)
        btns.add_widget(cancel_btn)
        content.add_widget(btns)
        popup = Popup(title="Add Item", content=content, size_hint=(0.8, 0.6))
        save_btn.bind(on_release=lambda x: self.save_new_item(name_input.text, desc_input.text, mac_input.text, popup))
        cancel_btn.bind(on_release=lambda x: popup.dismiss())
        popup.open()

    def save_new_item(self, name, desc, mac, popup):
        if not name:
            return
        items_list.append({"name": name, "desc": desc, "mac": mac, "last_seen": "N/A"})
        save_items()
        self.update_items()
        popup.dismiss()

    # --- Called by mqtt_handler ---
    def show_missing_popup(self, item):
        popup_content = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(10))
        popup_content.add_widget(Label(text=f"Missing Item: {item['name']}"))
        popup_content.add_widget(Label(text=f"Last Seen: {item['last_seen']}"))
        ok_btn = ProButton(text="OK")
        popup_content.add_widget(ok_btn)
        popup = Popup(title="Missing Item Detected", content=popup_content, size_hint=(0.7, 0.4))
        ok_btn.bind(on_release=lambda x: popup.dismiss())
        popup.open()

# --- App ---
class EverydayCarryApp(App):
    def build(self):
        sm = ScreenManager(transition=FadeTransition())
        self.main_screen = MainScreen(name="main")
        sm.add_widget(self.main_screen)
        return sm

    # --- MQTT Missing Item Callback ---
    def missing_item_callback(self, item):
        # Called from mqtt_handler when an item goes missing
        if self.main_screen:
            self.main_screen.show_missing_popup(item)

if __name__ == "__main__":
    load_items()
    EverydayCarryApp().run()
