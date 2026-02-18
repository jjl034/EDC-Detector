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
from kivy.uix.popup import Popup
import database

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

# --- Global Items List ---
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
            if self.focus:
                Color(*THEME["surface_active"])
            else:
                Color(*THEME["surface"])
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)])
            if self.focus:
                Color(*THEME["primary"])
            else:
                Color(*THEME["border_color"])
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

        text_content = BoxLayout(orientation='vertical', spacing=dp(2))
        text_content.add_widget(Label(
            text=name,
            font_size=dp(18),
            bold=True,
            color=THEME["text_primary"],
            halign='left',
            valign='bottom',
            size_hint_y=0.6,
            text_size=(self.width, None)
        ))

        desc_text = f"{desc} | {self.index}"
        text_content.add_widget(Label(
            text=desc_text,
            font_size=dp(14),
            color=THEME["text_secondary"],
            halign='left',
            valign='top',
            size_hint_y=0.4,
            max_lines=1,
            text_size=(self.width, None)
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

        card = BoxLayout(orientation='vertical', padding=dp(40), spacing=dp(24))
        card.size_hint = (None, None)
        card.size = (dp(360), dp(520))
        card.pos_hint = {'center_x': 0.5, 'center_y': 0.5}

        title_box = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(80), spacing=dp(5))
        self.title_lbl = Label(text="Everyday Carry", font_size=dp(36), bold=True, color=THEME["text_primary"], halign='center')
        self.subtitle_lbl = Label(text="Your digital loadout manager.", font_size=dp(16), color=THEME["text_secondary"], halign='center')
        title_box.add_widget(self.title_lbl)
        title_box.add_widget(self.subtitle_lbl)
        card.add_widget(title_box)

        input_container = BoxLayout(orientation='vertical', spacing=dp(15), size_hint_y=None, height=dp(130))
        self.username = ProInput(hint_text="Email Address")
        self.password = ProInput(hint_text="Password", password=True)
        input_container.add_widget(self.username)
        input_container.add_widget(self.password)
        card.add_widget(input_container)

        self.feedback_lbl = Label(text="", font_size=dp(14), color=THEME["danger"], size_hint_y=None, height=dp(20), halign='center')
        card.add_widget(self.feedback_lbl)

        self.action_btn = ProButton(text="Sign In", height=dp(54), size_hint_y=None)
        self.action_btn.bind(on_release=self.perform_action)
        card.add_widget(self.action_btn)

        self.toggle_btn = Button(
            text="New here? Create an account",
            font_size=dp(14),
            color=THEME["primary"],
            background_normal="",
            background_down="",
            background_color=(0, 0, 0, 0),
            size_hint_y=None,
            height=dp(30)
        )
        self.toggle_btn.bind(on_release=self.toggle_mode)
        card.add_widget(self.toggle_btn)

        self.add_widget(card)

    def toggle_mode(self, instance):
        if self.mode == 'login':
            self.mode = 'signup'
            self.title_lbl.text = "Create Account"
            self.subtitle_lbl.text = "Join Everyday Carry today."
            self.action_btn.text = "Sign Up"
            self.toggle_btn.text = "Already have an account? Sign In"
            self.feedback_lbl.text = ""
        else:
            self.mode = 'login'
            self.title_lbl.text = "Everyday Carry"
            self.subtitle_lbl.text = "Your digital loadout manager."
            self.action_btn.text = "Sign In"
            self.toggle_btn.text = "New here? Create an account"
            self.feedback_lbl.text = ""

    def perform_action(self, instance):
        user = self.username.text.strip()
        pwd = self.password.text.strip()
        if not user or not pwd:
            self.feedback_lbl.text = "Please enter both Email Address and password."
            self.feedback_lbl.color = THEME["danger"]
            return

        if self.mode == 'login':
            if self.db.verify_user(user, pwd):
                self.feedback_lbl.text = ""
                self.manager.current = 'main'
                self.username.text = ""
                self.password.text = ""
            else:
                self.feedback_lbl.text = "Invalid Email Address or password."
                self.feedback_lbl.color = THEME["danger"]
        else:
            if self.db.create_user(user, pwd):
                self.feedback_lbl.text = "Account created! Please sign in."
                self.feedback_lbl.color = THEME["accent"]
                self.toggle_mode(None)
                self.username.text = user
                self.password.text = ""
            else:
                self.feedback_lbl.text = "Email Address already exists."
                self.feedback_lbl.color = THEME["danger"]

# --- Add Item Screen ---
class AddItemScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root = BoxLayout(orientation='vertical', padding=[dp(30), dp(50), dp(30), dp(30)], spacing=dp(20))
        root.add_widget(Label(text="Add New Item", font_size=dp(28), bold=True, color=THEME["text_primary"], size_hint_y=None, height=dp(60), halign='center'))

        form = BoxLayout(orientation='vertical', spacing=dp(20), size_hint_y=None, height=dp(200))
        self.item_name = ProInput(hint_text="Item Name (e.g. Wallet)")
        self.item_desc = ProInput(hint_text="Description (e.g. Leather, brown)")
        self.item_mac = ProInput(hint_text="MAC Address (optional)")
        form.add_widget(self.item_name)
        form.add_widget(self.item_desc)
        form.add_widget(self.item_mac)
        root.add_widget(form)

        actions = BoxLayout(orientation='horizontal', spacing=dp(15), size_hint_y=None, height=dp(60))
        cancel_btn = ProButton(text="Cancel", bg_color=THEME["surface"], font_size=dp(16))
        cancel_btn.color = THEME["text_secondary"]
        cancel_btn.bind(on_release=self.cancel)
        save_btn = ProButton(text="Save Item", bg_color=THEME["primary"])
        save_btn.bind(on_release=self.save_item)
        actions.add_widget(cancel_btn)
        actions.add_widget(save_btn)
        root.add_widget(actions)

        self.add_widget(root)

    def cancel(self, instance):
        self.clear_inputs()
        self.manager.current = 'main'

    def save_item(self, instance):
        name = self.item_name.text.strip()
        desc = self.item_desc.text.strip()
        mac = self.item_mac.text.strip()
        if name:
            db = database.DB()
            db.add_item(name, desc, mac)
            items_list.append({"name": name, "desc": desc, "mac": mac})
            self.manager.get_screen('main').update_items_list()
            self.clear_inputs()
            self.manager.current = 'main'

    def clear_inputs(self):
        self.item_name.text = ""
        self.item_desc.text = ""
        self.item_mac.text = ""

# --- Main Screen ---
class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root = BoxLayout(orientation='vertical')
        header = BoxLayout(orientation='horizontal', padding=[dp(25), dp(15)], size_hint_y=None, height=dp(70))
        title = Label(text="Dashboard", font_size=dp(24), bold=True, color=THEME["text_primary"], halign='left', valign='middle')
        title.bind(size=title.setter('text_size'))
        header.add_widget(title)
        user_lbl = Label(text="Admin User", font_size=dp(14), color=THEME["primary"], halign='right', valign='middle')
        user_lbl.bind(size=user_lbl.setter('text_size'))
        header.add_widget(user_lbl)
        root.add_widget(header)

        self.scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        self.items_grid = GridLayout(cols=1, spacing=dp(15), size_hint_y=None, padding=[dp(20), dp(10)])
        self.scroll.add_widget(self.items_grid)
        root.add_widget(self.scroll)
        self.update_items_list()

        dock_container = BoxLayout(padding=[dp(20), dp(20), dp(20), dp(30)], size_hint_y=None, height=dp(100))
        dock = BoxLayout(orientation="horizontal", spacing=dp(15), padding=[dp(20), dp(10)])
        with dock.canvas.before:
            Color(*THEME["surface"])
            RoundedRectangle(pos=dock.pos, size=dock.size, radius=[dp(20)])
        dock.bind(pos=lambda inst, v: self.update_dock_display(dock), size=lambda inst, v: self.update_dock_display(dock))

        add_btn = ProButton(text="Add", bg_color=THEME["primary"])
        def go_to_add_item(instance): self.manager.current = 'add_item'
        add_btn.bind(on_release=go_to_add_item)
        dock.add_widget(add_btn)

        self.add_widget(root)
        self.add_widget(dock_container)
        dock_container.add_widget(dock)

    def update_dock_display(self, instance):
        instance.canvas.before.clear()
        with instance.canvas.before:
            Color(*THEME["surface"])
            RoundedRectangle(pos=instance.pos, size=instance.size, radius=[dp(20)])
            Color(*THEME["border_color"])
            Line(rounded_rectangle=(instance.x, instance.y, instance.width, instance.height, dp(20)), width=1)

    def update_items_list(self):
        self.items_grid.clear_widgets()
        if not items_list:
            empty_box = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(200))
            empty_box.add_widget(Label(text="No Items Found", font_size=dp(20), bold=True, color=THEME["text_secondary"]))
            empty_box.add_widget(Label(text="Tap 'Add' to start your collection", font_size=dp(14), color=THEME["text_secondary"]))
            self.items_grid.add_widget(empty_box)
            return
        for index, item in enumerate(items_list):
            card = ItemCard(item['name'], item.get('desc', ''), index)
            self.items_grid.add_widget(card)

    def open_edit_screen(self, index):
        pass  # Implement if editing is needed

# --- Popup Helper ---
def show_missing_popup(item_name, last_seen):
    content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(20))
    content.add_widget(Label(text=f"Missing Item: {item_name}", font_size=dp(20), color=THEME["danger"]))
    content.add_widget(Label(text=f"Last seen at: {last_seen}", font_size=dp(16), color=THEME["text_primary"]))
    btn = ProButton(text="Close", bg_color=THEME["primary"])
    popup = Popup(title="Item Missing!", content=content, size_hint=(0.8, 0.4))
    btn.bind(on_release=popup.dismiss)
    content.add_widget(btn)
    popup.open()

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
