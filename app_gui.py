# app_gui.py
import json
from pathlib import Path
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.clock import Clock
import paho.mqtt.client as mqtt

# --- THEME ---
THEME = {
    "background": (0.1, 0.1, 0.14, 1),
    "surface": (0.2, 0.2, 0.23, 1),
    "surface_active": (0.25, 0.25, 0.28, 1),
    "primary": (0.0, 0.48, 1.0, 1),
    "accent": (0.2, 0.8, 0.6, 1),
    "text_primary": (1, 1, 1, 1),
    "text_secondary": (0.7, 0.7, 0.75, 1),
    "danger": (1.0, 0.27, 0.27, 1),
    "border_color": (1, 1, 1, 0.2)
}
Window.clearcolor = THEME["background"]

# --- Data File ---
DATA_FILE = Path(__file__).parent / "data/items.json"
DATA_FILE.parent.mkdir(exist_ok=True)

# --- Load/Save Items ---
items_list = []

def load_items():
    global items_list
    if DATA_FILE.exists():
        with open(DATA_FILE, "r") as f:
            try:
                items_list = json.load(f)
            except json.JSONDecodeError:
                items_list = []
    else:
        items_list = []

def save_items():
    with open(DATA_FILE, "w") as f:
        json.dump(items_list, f, indent=4)

load_items()

# --- UI Widgets ---
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
            if self.state == 'down':
                r, g, b, a = self.custom_bg_color
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
        self.height = dp(54)
        self.bind(pos=self.update_canvas, size=self.update_canvas, focus=self.update_canvas)
        self.update_canvas()

    def update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            if self.focus:
                Color(*THEME["surface_active"])
            else:
                Color(*THEME["surface"])
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)])
            Color(*THEME["border_color"] if not self.focus else THEME["primary"])
            Line(rounded_rectangle=(self.x, self.y, self.width, self.height, dp(10)), width=1.2)

class ItemCard(BoxLayout):
    def __init__(self, name, desc, index, **kwargs):
        super().__init__(**kwargs)
        self.index = index
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = dp(85)
        self.padding = dp(16)
        self.spacing = dp(15)

        # Text Container
        text_content = BoxLayout(orientation='vertical', spacing=dp(2))
        text_content.add_widget(Label(text=name, font_size=dp(18), bold=True, color=THEME["text_primary"], halign='left', valign='bottom', size_hint_y=0.6, text_size=(self.width, None)))
        text_content.add_widget(Label(text=desc, font_size=dp(14), color=THEME["text_secondary"], halign='left', valign='top', size_hint_y=0.4, text_size=(self.width, None)))
        self.add_widget(text_content)

        # Edit Button
        edit_btn = ProButton(text="Edit", bg_color=THEME["surface_active"], font_size=dp(13), radius=dp(6))
        edit_btn.size_hint = (None, None)
        edit_btn.size = (dp(60), dp(34))
        edit_btn.pos_hint = {'center_y': 0.5}
        edit_btn.bind(on_release=self.on_edit)
        self.add_widget(edit_btn)

    def on_edit(self, instance):
        app = App.get_running_app()
        main_screen = app.root.get_screen('main')
        main_screen.open_edit_screen(self.index)

# --- Screens ---
class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root = BoxLayout(orientation="vertical")
        header = BoxLayout(orientation="horizontal", padding=[dp(25), dp(15)], size_hint_y=None, height=dp(70))
        header.add_widget(Label(text="Dashboard", font_size=dp(24), bold=True, color=THEME["text_primary"], halign='left'))
        header.add_widget(Label(text="Admin User", font_size=dp(14), color=THEME["primary"], halign='right'))
        root.add_widget(header)

        # Scrollable Items
        self.scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        self.items_grid = GridLayout(cols=1, spacing=dp(15), size_hint_y=None, padding=[dp(20), dp(10)])
        self.items_grid.bind(minimum_height=self.items_grid.setter('height'))
        self.scroll.add_widget(self.items_grid)
        root.add_widget(self.scroll)

        # Bottom Menu
        dock_container = BoxLayout(padding=[dp(20), dp(20), dp(20), dp(30)], size_hint_y=None, height=dp(100))
        dock = BoxLayout(orientation="horizontal", spacing=dp(15), padding=[dp(20), dp(10)])
        dock_container.add_widget(dock)
        root.add_widget(dock_container)

        # Buttons
        add_btn = ProButton(text="Add", bg_color=THEME["primary"])
        add_btn.bind(on_release=lambda x: self.manager.current = "add_item")  # <<< Syntax fixed below
        add_btn.bind(on_release=lambda x: self.manager.current.__setattr__('current', 'add_item'))
        dock.add_widget(add_btn)

        self.add_widget(root)
        self.update_items_list()

    def update_items_list(self):
        self.items_grid.clear_widgets()
        if not items_list:
            empty_box = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(200))
            empty_box.add_widget(Label(text="No Items Found", font_size=dp(20), bold=True, color=THEME["text_secondary"]))
            empty_box.add_widget(Label(text="Tap 'Add' to start your collection", font_size=dp(14), color=THEME["text_secondary"]))
            self.items_grid.add_widget(empty_box)
            return
        for idx, item in enumerate(items_list):
            card = ItemCard(item["name"], item.get("desc", ""), idx)
            self.items_grid.add_widget(card)

    def open_edit_screen(self, index):
        # Placeholder
        pass

    def show_missing_popup(self, missing_items):
        content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        for item in missing_items:
            content.add_widget(Label(text=f"{item['name']} last seen at {item['last_seen']}", color=THEME["danger"]))
        popup = Popup(title="Missing Items Detected!", content=content, size_hint=(0.8, 0.5))
        popup.open()

class AddItemScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root = BoxLayout(orientation='vertical', padding=[dp(30), dp(50), dp(30), dp(30)], spacing=dp(20))
        self.item_name = ProInput(hint_text="Item Name")
        self.item_desc = ProInput(hint_text="Description")
        root.add_widget(self.item_name)
        root.add_widget(self.item_desc)
        save_btn = ProButton(text="Save Item")
        save_btn.bind(on_release=self.save_item)
        root.add_widget(save_btn)
        self.add_widget(root)

    def save_item(self, instance):
        name = self.item_name.text.strip()
        desc = self.item_desc.text.strip()
        if name:
            items_list.append({"name": name, "desc": desc, "last_seen": "Unknown"})
            save_items()
            self.manager.get_screen("main").update_items_list()
            self.item_name.text = ""
            self.item_desc.text = ""
            self.manager.current = "main"

# --- MQTT Client ---
mqtt_client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT")
    client.subscribe("edc/missing")

def on_message(client, userdata, msg):
    try:
        missing_items = json.loads(msg.payload.decode())
        app = App.get_running_app()
        Clock.schedule_once(lambda dt: app.root.get_screen("main").show_missing_popup(missing_items))
    except Exception as e:
        print("MQTT message error:", e)

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect("localhost", 1883, 60)
mqtt_client.loop_start()

# --- App ---
class EverydayCarryApp(App):
    def build(self):
        sm = ScreenManager(transition=FadeTransition(duration=0.2))
        sm.add_widget(MainScreen(name="main"))
        sm.add_widget(AddItemScreen(name="add_item"))
        return sm

if __name__ == "__main__":
    EverydayCarryApp().run()
