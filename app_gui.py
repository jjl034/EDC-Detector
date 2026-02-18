# app_gui.py
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.metrics import dp
from kivy.core.window import Window

# Minimal log module (to prevent import errors)
import logging
class KivyLogHandler(logging.Handler):
    def __init__(self, widget=None, **kwargs):
        super().__init__()
        self.widget = widget

    def emit(self, record):
        msg = self.format(record)
        if self.widget:
            self.widget.text += msg + "\n"

class UserFormatter(logging.Formatter):
    def format(self, record):
        return f"{record.levelname}: {record.getMessage()}"

import os

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

# --- Global items list ---
items_list = []

# --- Reusable UI components ---

class ProButton(Button):
    def __init__(self, bg_color=THEME["primary"], font_size=dp(16), radius=dp(8), **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_down = ""
        self.background_color = (0, 0, 0, 0)
        self.custom_bg_color = bg_color
        self.font_size = font_size
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
            Color(*THEME["surface_active"] if self.focus else THEME["surface"])
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)])
            Color(*THEME["primary"] if self.focus else THEME["border_color"])
            Line(rounded_rectangle=(self.x, self.y, self.width, self.height, dp(10)), width=1.2)

# --- Screens ---

class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=dp(40), spacing=dp(20))
        layout.add_widget(Label(text="Everyday Carry", font_size=dp(36), color=THEME["text_primary"], bold=True))
        self.username = ProInput(hint_text="Email")
        self.password = ProInput(hint_text="Password", password=True)
        layout.add_widget(self.username)
        layout.add_widget(self.password)
        self.feedback = Label(text="", color=THEME["danger"], size_hint_y=None, height=dp(20))
        layout.add_widget(self.feedback)
        btn = ProButton(text="Sign In", size_hint_y=None, height=dp(50))
        btn.bind(on_release=self.login)
        layout.add_widget(btn)
        self.add_widget(layout)

    def login(self, instance):
        user = self.username.text.strip()
        pwd = self.password.text.strip()
        if user and pwd:
            # For demo: any login works
            self.manager.current = 'main'
        else:
            self.feedback.text = "Please enter username and password."

class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=dp(20))
        layout.add_widget(Label(text="Dashboard", font_size=dp(24), color=THEME["text_primary"], bold=True))
        self.scroll = ScrollView(size_hint=(1,1))
        self.grid = GridLayout(cols=1, spacing=dp(15), size_hint_y=None)
        self.grid.bind(minimum_height=self.grid.setter('height'))
        self.scroll.add_widget(self.grid)
        layout.add_widget(self.scroll)
        add_btn = ProButton(text="Add Item", size_hint_y=None, height=dp(50))
        add_btn.bind(on_release=lambda x: self.manager.current='add_item')
        layout.add_widget(add_btn)
        self.add_widget(layout)

class AddItemScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=dp(30), spacing=dp(20))
        layout.add_widget(Label(text="Add New Item", font_size=dp(28), color=THEME["text_primary"], bold=True))
        self.name_input = ProInput(hint_text="Item Name")
        self.desc_input = ProInput(hint_text="Description")
        layout.add_widget(self.name_input)
        layout.add_widget(self.desc_input)
        save_btn = ProButton(text="Save Item", size_hint_y=None, height=dp(50))
        save_btn.bind(on_release=self.save_item)
        layout.add_widget(save_btn)
        self.add_widget(layout)

    def save_item(self, instance):
        name = self.name_input.text.strip()
        desc = self.desc_input.text.strip()
        if name:
            items_list.append({"name": name, "desc": desc})
            self.manager.get_screen('main').grid.clear_widgets()
            for item in items_list:
                self.manager.get_screen('main').grid.add_widget(Label(text=f"{item['name']} - {item['desc']}", color=THEME["text_primary"]))
            self.manager.current = 'main'

# --- App ---

class EverydayCarryApp(App):
    def build(self):
        sm = ScreenManager(transition=FadeTransition(duration=0.2))
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(AddItemScreen(name='add_item'))
        return sm

if __name__ == "__main__":
    EverydayCarryApp().run()
