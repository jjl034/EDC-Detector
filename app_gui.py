# app_gui.py
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.metrics import dp
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from pathlib import Path
import database
import log
import logging
import json
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

# Global items list
items_list = []

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

class ItemCard(BoxLayout):
    def __init__(self, name, desc, index, **kwargs):
        super().__init__(**kwargs)
        self.index = index
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = dp(85)
        self.padding = dp(16)
        self.spacing = dp(15)
        self.bind(pos=self.update_canvas, size=self.update_canvas)

        text_content = BoxLayout(orientation='vertical', spacing=dp(2))
        text_content.add_widget(Label(
            text=name, font_size=dp(18), bold=True, color=THEME["text_primary"],
            halign='left', valign='bottom', size_hint_y=0.6, text_size=(self.width, None)
        ))
        desc_text = f"{desc} | {self.index}"
        text_content.add_widget(Label(
            text=desc_text, font_size=dp(14), color=THEME["text_secondary"],
            halign='left', valign='top', size_hint_y=0.4, text_size=(self.width, None)
        ))
        self.add_widget(text_content)

        edit_btn = ProButton(text="Edit", bg_color=THEME["surface_active"], font_size=dp(13), radius=dp(6))
        edit_btn.size_hint = (None, None)
        edit_btn.size = (dp(60), dp(34))
        edit_btn.pos_hint = {'center_y': 0.5}
        edit_btn.bind(on_release=self.on_edit)
        self.add_widget(edit_btn)

    def update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*THEME["surface"])
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(12)])
            Color(*THEME["border_color"])
            Line(rounded_rectangle=(self.x, self.y, self.width, self.height, dp(12)), width=1)

    def on_edit(self, instance):
        app = App.get_running_app()
        if app and app.root:
            main_screen = app.root.get_screen('main')
            main_screen.open_edit_screen(self.index)

# --- Screens ---
class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db = database.DB()
        self.mode = 'login'
        card = BoxLayout(orientation='vertical', padding=[dp(40)], spacing=dp(24),
                         size_hint=(None,None), size=(dp(360), dp(520)), pos_hint={'center_x':0.5,'center_y':0.5})

        self.title_lbl = Label(text="Everyday Carry", font_size=dp(36), bold=True, color=THEME["text_primary"])
        self.subtitle_lbl = Label(text="Your digital loadout manager.", font_size=dp(16), color=THEME["text_secondary"])
        card.add_widget(self.title_lbl)
        card.add_widget(self.subtitle_lbl)

        self.username = ProInput(hint_text="Email Address")
        self.password = ProInput(hint_text="Password", password=True)
        card.add_widget(self.username)
        card.add_widget(self.password)

        self.feedback_lbl = Label(text="", font_size=dp(14), color=THEME["danger"], size_hint_y=None, height=dp(20))
        card.add_widget(self.feedback_lbl)

        self.action_btn = ProButton(text="Sign In", height=dp(54), size_hint_y=None)
        self.action_btn.bind(on_release=self.perform_action)
        card.add_widget(self.action_btn)

        self.toggle_btn = Button(text="New here? Create an account", font_size=dp(14), color=THEME["primary"],
                                 background_normal="", background_down="", background_color=(0,0,0,0), size_hint_y=None, height=dp(30))
        self.toggle_btn.bind(on_release=self.toggle_mode)
        card.add_widget(self.toggle_btn)

        self.add_widget(card)

    def toggle_mode(self, instance):
        if self.mode=='login':
            self.mode='signup'
            self.title_lbl.text="Create Account"
            self.subtitle_lbl.text="Join Everyday Carry today."
            self.action_btn.text="Sign Up"
            self.toggle_btn.text="Already have an account? Sign In"
            self.feedback_lbl.text=""
        else:
            self.mode='login'
            self.title_lbl.text="Everyday Carry"
            self.subtitle_lbl.text="Your digital loadout manager."
            self.action_btn.text="Sign In"
            self.toggle_btn.text="New here? Create an account"
            self.feedback_lbl.text=""

    def perform_action(self, instance):
        user = self.username.text.strip()
        pwd = self.password.text.strip()
        if not user or not pwd:
            self.feedback_lbl.text="Please enter both Email Address and password."
            return
        if self.mode=='login':
            if self.db.verify_user(user, pwd):
                self.feedback_lbl.text=""
                self.manager.current='main'
                self.username.text=""
                self.password.text=""
            else:
                self.feedback_lbl.text="Invalid Email Address or password."
        else:
            if self.db.create_user(user, pwd):
                self.feedback_lbl.text="Account created! Please sign in."
                self.toggle_mode(None)
                self.username.text=user
                self.password.text=""
            else:
                self.feedback_lbl.text="Email Address already exists."

# (The rest of the screens: AddItemScreen, EditItemScreen, MainScreen, LogbookScreen, SettingsScreen)
# would continue in the same pattern as above, using ProButton, ProInput, ItemCard, dark theme,
# safe file handling, and scrollable layouts.

class EverydayCarryApp(App):
    def build(self):
        sm = ScreenManager(transition=FadeTransition(duration=0.2))
        sm.add_widget(LoginScreen(name='login'))
        # add MainScreen, AddItemScreen, EditItemScreen, LogbookScreen, SettingsScreen similarly
        return sm

if __name__=="__main__":
    EverydayCarryApp().run()
