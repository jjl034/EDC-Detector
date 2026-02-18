# app_gui.py
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.core.window import Window
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.metrics import dp
from kivy.uix.popup import Popup
from kivy.graphics import Color, RoundedRectangle, Line
import database  # Your database.py that stores users/items

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

# --- Global ---
current_user = None  # Track logged-in user


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


class ItemCard(BoxLayout):
    def __init__(self, item, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = dp(80)
        self.padding = dp(10)
        self.spacing = dp(15)

        # Labels for name and description
        name_lbl = Label(text=item["name"], font_size=dp(18), bold=True, color=THEME["text_primary"], halign="left")
        desc_lbl = Label(text=item.get("desc", ""), font_size=dp(14), color=THEME["text_secondary"], halign="left")
        box = BoxLayout(orientation="vertical")
        box.add_widget(name_lbl)
        box.add_widget(desc_lbl)
        self.add_widget(box)


# --- Screens ---
class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db = database.DB()
        self.mode = "login"

        layout = BoxLayout(orientation="vertical", padding=dp(40), spacing=dp(20))
        self.title_lbl = Label(text="Everyday Carry", font_size=dp(32), bold=True, color=THEME["text_primary"])
        layout.add_widget(self.title_lbl)

        self.username = ProInput(hint_text="Email Address")
        self.password = ProInput(hint_text="Password", password=True)
        layout.add_widget(self.username)
        layout.add_widget(self.password)

        self.feedback = Label(text="", color=THEME["danger"], size_hint_y=None, height=dp(20))
        layout.add_widget(self.feedback)

        self.action_btn = ProButton(text="Sign In")
        self.action_btn.bind(on_release=self.perform_action)
        layout.add_widget(self.action_btn)

        toggle_btn = Button(text="New here? Sign Up", font_size=dp(14),
                            color=THEME["primary"], background_color=(0, 0, 0, 0))
        toggle_btn.bind(on_release=self.toggle_mode)
        layout.add_widget(toggle_btn)

        self.add_widget(layout)

    def toggle_mode(self, instance):
        if self.mode == "login":
            self.mode = "signup"
            self.title_lbl.text = "Create Account"
            self.action_btn.text = "Sign Up"
        else:
            self.mode = "login"
            self.title_lbl.text = "Everyday Carry"
            self.action_btn.text = "Sign In"
        self.feedback.text = ""

    def perform_action(self, instance):
        global current_user
        user = self.username.text.strip()
        pwd = self.password.text.strip()
        if not user or not pwd:
            self.feedback.text = "Please fill in both fields."
            return

        if self.mode == "login":
            if self.db.verify_user(user, pwd):
                current_user = user
                self.manager.get_screen("main").load_items()
                self.manager.current = "main"
                self.username.text = ""
                self.password.text = ""
                self.feedback.text = ""
            else:
                self.feedback.text = "Invalid credentials."
        else:
            if self.db.create_user(user, pwd):
                self.feedback.text = "Account created! Please login."
                self.toggle_mode(None)
            else:
                self.feedback.text = "User already exists."


class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(10))

        header = BoxLayout(size_hint_y=None, height=dp(60))
        header.add_widget(Label(text="Dashboard", font_size=dp(24), color=THEME["text_primary"]))
        self.layout.add_widget(header)

        # Scrollable items
        self.scroll = ScrollView()
        self.grid = GridLayout(cols=1, spacing=dp(10), size_hint_y=None, padding=[dp(10)])
        self.grid.bind(minimum_height=self.grid.setter("height"))
        self.scroll.add_widget(self.grid)
        self.layout.add_widget(self.scroll)

        # Add Item button
        add_btn = ProButton(text="Add Item", bg_color=THEME["primary"], size_hint_y=None, height=dp(50))
        add_btn.bind(on_release=lambda x: self.manager.current = "add_item")
        self.layout.add_widget(add_btn)

        self.add_widget(self.layout)

    def load_items(self):
        self.grid.clear_widgets()
        items = database.DB().get_items(current_user)
        if not items:
            self.grid.add_widget(Label(text="No Items Found", color=THEME["text_secondary"], size_hint_y=None, height=dp(50)))
        else:
            for item in items:
                self.grid.add_widget(ItemCard(item))


class AddItemScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation="vertical", padding=dp(30), spacing=dp(20))
        self.layout.add_widget(Label(text="Add Item", font_size=dp(28), color=THEME["text_primary"]))

        self.item_name = ProInput(hint_text="Item Name")
        self.layout.add_widget(self.item_name)
        self.item_desc = ProInput(hint_text="Description")
        self.layout.add_widget(self.item_desc)

        save_btn = ProButton(text="Save Item")
        save_btn.bind(on_release=self.save_item)
        self.layout.add_widget(save_btn)

        self.add_widget(self.layout)

    def save_item(self, instance):
        name = self.item_name.text.strip()
        desc = self.item_desc.text.strip()
        if name:
            database.DB().add_item(current_user, name, desc)
            self.manager.get_screen("main").load_items()
            self.manager.current = "main"
            self.item_name.text = ""
            self.item_desc.text = ""


# --- Missing Item Popup ---
def show_missing_item(item_name, last_seen):
    content = BoxLayout(orientation="vertical", padding=dp(20), spacing=dp(10))
    content.add_widget(Label(text=f"Missing Item Detected!\n{item_name}\nLast seen at: {last_seen}", font_size=dp(18)))
    btn = ProButton(text="Close")
    content.add_widget(btn)
    popup = Popup(title="Missing Item", content=content, size_hint=(0.7, 0.4))
    btn.bind(on_release=popup.dismiss)
    popup.open()


# --- App ---
class EverydayCarryApp(App):
    def build(self):
        sm = ScreenManager(transition=FadeTransition())
        sm.add_widget(LoginScreen(name="login"))
        sm.add_widget(MainScreen(name="main"))
        sm.add_widget(AddItemScreen(name="add_item"))
        return sm


if __name__ == "__main__":
    EverydayCarryApp().run()
