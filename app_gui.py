from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.metrics import dp
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from database import DB
from missing_logic import check_missing_items, load_items
from pathlib import Path
import json

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

Window.clearcolor = THEME["background"]

items_list = []

# --- UI Helpers ---
class ProButton(Button):
    def __init__(self, bg_color=THEME["primary"], font_size=dp(16), radius=dp(8), **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_down = ""
        self.background_color = (0,0,0,0)
        self.custom_bg_color = bg_color
        self.font_size = font_size
        self.color = THEME["text_primary"]
        self.radius = radius
        self.bind(pos=self.update_canvas, size=self.update_canvas, state=self.update_canvas)
        self.update_canvas()

    def update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            r,g,b,a = self.custom_bg_color
            if self.state=='down':
                Color(r*0.8,g*0.8,b*0.8,a)
            else:
                Color(r,g,b,a)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[self.radius])

class ProInput(TextInput):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal=""
        self.background_active=""
        self.background_color = THEME["surface"]
        self.foreground_color = THEME["text_primary"]
        self.hint_text_color = THEME["text_secondary"]
        self.cursor_color = THEME["primary"]
        self.padding = [dp(16), dp(16), dp(16), dp(16)]
        self.font_size = dp(16)
        self.multiline = False
        self.size_hint_y = None
        self.height = dp(54)
        self.bind(pos=self.update_canvas, size=self.update_canvas, focus=self.update_canvas)
        self.update_canvas()

    def update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*THEME["surface_active"] if self.focus else THEME["surface"])
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)])
            Color(*THEME["primary"] if self.focus else THEME["border_color"])
            Line(rounded_rectangle=(self.x,self.y,self.width,self.height,dp(10)), width=1.2)

# --- Screens ---
class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db = DB()
        root = BoxLayout(orientation="vertical")

        # Header
        header = BoxLayout(orientation="horizontal", padding=[dp(20),dp(15)], size_hint_y=None, height=dp(60))
        header.add_widget(Label(text="Dashboard", font_size=dp(24), bold=True, color=THEME["text_primary"]))
        header.add_widget(Label(text="Admin", font_size=dp(14), color=THEME["primary"], halign="right"))
        root.add_widget(header)

        # Item list
        self.scroll = ScrollView(size_hint=(1,1))
        self.items_grid = GridLayout(cols=1, spacing=dp(15), size_hint_y=None, padding=[dp(20),dp(10)])
        self.items_grid.bind(minimum_height=self.items_grid.setter("height"))
        self.scroll.add_widget(self.items_grid)
        root.add_widget(self.scroll)

        self.update_items_list()
        self.add_widget(root)

    def update_items_list(self):
        self.items_grid.clear_widgets()
        items_list.clear()
        for item_id, name, desc, mac in self.db.get_items():
            items_list.append({"id":item_id,"name":name,"desc":desc,"mac":mac})
            box = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(60), padding=dp(10))
            box.add_widget(Label(text=f"{name} | {desc} | {mac}", color=THEME["text_primary"]))
            edit_btn = ProButton(text="Edit", bg_color=THEME["surface_active"], font_size=dp(14))
            box.add_widget(edit_btn)
            self.items_grid.add_widget(box)

class EverydayCarryApp(App):
    def build(self):
        sm = ScreenManager(transition=FadeTransition(duration=0.2))
        sm.add_widget(MainScreen(name="main"))
        return sm

if __name__=="__main__":
    EverydayCarryApp().run()

