import json
import threading
from pathlib import Path
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle, Line
import paho.mqtt.client as mqtt

# --- Theme Settings ---
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
Window.clearcolor = THEME["background"]

DATA_FILE = Path("./data/items.json")
DATA_FILE.parent.mkdir(exist_ok=True, parents=True)
if not DATA_FILE.exists():
    with open(DATA_FILE, "w") as f:
        json.dump([], f)

# --- Global Items List ---
items_list = []

# --- UI Elements ---


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
            if self.state == 'down':
                Color(r * 0.8, g * 0.8, b * 0.8, a)
            else:
                Color(r, g, b, a)
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
        self.padding = [dp(16)] * 4
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
    def __init__(self, item_data, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = dp(85)
        self.padding = dp(16)
        self.spacing = dp(15)

        # Text content
        text_box = BoxLayout(orientation='vertical')
        text_box.add_widget(Label(text=item_data["name"], font_size=dp(18), bold=True,
                                  color=THEME["text_primary"], halign="left", valign="middle"))
        desc_text = f"{item_data.get('desc','')} | Last seen: {item_data.get('last_seen','N/A')}"
        text_box.add_widget(Label(text=desc_text, font_size=dp(14), color=THEME["text_secondary"],
                                  halign="left", valign="middle"))
        self.add_widget(text_box)


# --- Screens ---


class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=dp(40), spacing=dp(24))
        self.username = ProInput(hint_text="Username")
        self.password = ProInput(hint_text="Password", password=True)
        layout.add_widget(Label(text="Login", font_size=dp(28), bold=True, color=THEME["text_primary"]))
        layout.add_widget(self.username)
        layout.add_widget(self.password)
        self.feedback_lbl = Label(text="", color=THEME["danger"])
        layout.add_widget(self.feedback_lbl)
        login_btn = ProButton(text="Login")
        login_btn.bind(on_release=self.login)
        layout.add_widget(login_btn)
        self.add_widget(layout)

    def login(self, instance):
        # Dummy login: accept any input
        if self.username.text and self.password.text:
            self.manager.current = "main"
        else:
            self.feedback_lbl.text = "Enter both username and password."


class AddItemPopup(Popup):
    def __init__(self, add_callback, **kwargs):
        super().__init__(**kwargs)
        self.title = "Add New Item"
        self.size_hint = (0.8, 0.5)
        self.auto_dismiss = False
        self.add_callback = add_callback

        box = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(20))
        self.name_input = ProInput(hint_text="Item Name")
        self.desc_input = ProInput(hint_text="Description")
        box.add_widget(self.name_input)
        box.add_widget(self.desc_input)

        btn_box = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        cancel_btn = ProButton(text="Cancel", bg_color=THEME["surface"])
        cancel_btn.color = THEME["text_secondary"]
        cancel_btn.bind(on_release=self.dismiss)
        save_btn = ProButton(text="Add Item")
        save_btn.bind(on_release=self.save_item)
        btn_box.add_widget(cancel_btn)
        btn_box.add_widget(save_btn)
        box.add_widget(btn_box)
        self.content = box

    def save_item(self, instance):
        name = self.name_input.text.strip()
        desc = self.desc_input.text.strip()
        if name:
            self.add_callback(name, desc)
            self.dismiss()


class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.root_box = BoxLayout(orientation='vertical')
        self.scroll = ScrollView(size_hint=(1, 1))
        self.items_grid = GridLayout(cols=1, spacing=dp(15), size_hint_y=None, padding=[dp(20), dp(10)])
        self.items_grid.bind(minimum_height=self.items_grid.setter('height'))
        self.scroll.add_widget(self.items_grid)
        self.root_box.add_widget(self.scroll)

        # Add button
        add_btn = ProButton(text="Add Item", size_hint_y=None, height=dp(50))
        add_btn.bind(on_release=self.open_add_popup)
        self.root_box.add_widget(add_btn)
        self.add_widget(self.root_box)
        self.load_items()

    def open_add_popup(self, instance):
        popup = AddItemPopup(self.add_item)
        popup.open()

    def add_item(self, name, desc):
        item = {"name": name, "desc": desc, "last_seen": "N/A"}
        items_list.append(item)
        self.save_items()
        self.update_dashboard()

    def load_items(self):
        global items_list
        with open(DATA_FILE, "r") as f:
            items_list = json.load(f)
        self.update_dashboard()

    def save_items(self):
        with open(DATA_FILE, "w") as f:
            json.dump(items_list, f, indent=2)

    def update_dashboard(self):
        self.items_grid.clear_widgets()
        if not items_list:
            empty_lbl = Label(text="No items found.\nUse 'Add Item' to start.", font_size=dp(18),
                              color=THEME["text_secondary"])
            self.items_grid.add_widget(empty_lbl)
        for item in items_list:
            self.items_grid.add_widget(ItemCard(item))

    def popup_missing_item(self, item_name, last_seen):
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(20))
        content.add_widget(Label(text=f"Item Missing!\n\n{item_name}\nLast seen: {last_seen}",
                                 font_size=dp(16)))
        btn = ProButton(text="Close")
        content.add_widget(btn)
        popup = Popup(title="Missing Item Detected", content=content, size_hint=(0.7, 0.4))
        btn.bind(on_release=popup.dismiss)
        popup.open()


# --- MQTT Listener Thread ---


def mqtt_thread(main_screen: MainScreen):
    def on_connect(client, userdata, flags, rc):
        print("Connected to MQTT broker:", rc)
        client.subscribe("edc/missing")

    def on_message(client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            item_name = payload.get("name", "Unknown")
            last_seen = payload.get("last_seen", "Unknown")
            # Trigger GUI popup
            main_screen.popup_missing_item(item_name, last_seen)
        except Exception as e:
            print("Error processing MQTT message:", e)

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect("localhost", 1883, 60)  # Change to your broker IP if needed
    client.loop_forever()


# --- App ---


class EverydayCarryApp(App):
    def build(self):
        sm = ScreenManager(transition=FadeTransition(duration=0.2))
        self.main_screen = MainScreen(name="main")
        sm.add_widget(LoginScreen(name="login"))
        sm.add_widget(self.main_screen)
        threading.Thread(target=mqtt_thread, args=(self.main_screen,), daemon=True).start()
        return sm


if __name__ == "__main__":
    EverydayCarryApp().run()
