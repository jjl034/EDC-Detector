from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.uix.popup import Popup

import threading
import time
import cv2
import database
import mqtt_handler  # your MQTT integration
import missing_logic

# --- Theme ---
THEME = {
    "background": (0.1, 0.1, 0.14, 1),
    "surface": (0.2, 0.2, 0.23, 1),
    "surface_active": (0.25, 0.25, 0.28, 1),
    "primary": (0.0, 0.48, 1.0, 1),
    "accent": (0.2, 0.8, 0.6, 1),
    "text_primary": (1, 1, 1, 1),
    "text_secondary": (0.7, 0.7, 0.75, 1),
    "danger": (1, 0.27, 0.27, 1),
    "border_color": (1, 1, 1, 0.2)
}

items_list = []  # global list of items

# --- Custom Widgets ---
class ProButton(Button):
    def __init__(self, bg_color=THEME["primary"], font_size=dp(16), radius=dp(8), **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_down = ""
        self.background_color = (0,0,0,0)
        self.custom_bg_color = bg_color
        self.font_size = font_size
        self.bold = True
        self.color = THEME["text_primary"]
        self.radius = radius
        self.bind(pos=self.update_canvas, size=self.update_canvas, state=self.update_canvas)
    def update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            r,g,b,a = self.custom_bg_color
            if self.state == 'down':
                Color(r*0.8,g*0.8,b*0.8,a)
            else:
                Color(r,g,b,a)
            RoundedRectangle(pos=self.pos,size=self.size,radius=[self.radius])

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
    def update_canvas(self,*args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*THEME["surface_active"] if self.focus else THEME["surface"])
            RoundedRectangle(pos=self.pos,size=self.size,radius=[dp(10)])
            Color(*THEME["primary"] if self.focus else THEME["border_color"])
            Line(rounded_rectangle=(self.x,self.y,self.width,self.height,dp(10)),width=1.2)

class ItemCard(BoxLayout):
    def __init__(self,name,desc,index,**kwargs):
        super().__init__(**kwargs)
        self.orientation='horizontal'
        self.size_hint_y=None
        self.height=dp(85)
        self.padding=dp(16)
        self.spacing=dp(15)
        self.index=index

        text_content = BoxLayout(orientation='vertical',spacing=dp(2))
        text_content.add_widget(Label(
            text=name,font_size=dp(18),bold=True,color=THEME["text_primary"],
            halign='left',valign='bottom',size_hint_y=0.6,text_size=(self.width,None)
        ))
        text_content.add_widget(Label(
            text=desc,font_size=dp(14),color=THEME["text_secondary"],
            halign='left',valign='top',size_hint_y=0.4,text_size=(self.width,None)
        ))
        self.add_widget(text_content)

        edit_btn = ProButton(text="Edit",bg_color=THEME["surface_active"],font_size=dp(13),radius=dp(6))
        edit_btn.size_hint=(None,None)
        edit_btn.size=(dp(60),dp(34))
        edit_btn.pos_hint={'center_y':0.5}
        edit_btn.bind(on_release=self.on_edit)
        self.add_widget(edit_btn)

    def update_canvas(self,*args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*THEME["surface"])
            RoundedRectangle(pos=self.pos,size=self.size,radius=[dp(12)])
            Color(*THEME["border_color"])
            Line(rounded_rectangle=(self.x,self.y,self.width,self.height,dp(12)),width=1)

    def on_edit(self, instance):
        app = App.get_running_app()
        if app:
            app.root.get_screen('edit_item').load_item(self.index, items_list[self.index])
            app.root.current = 'edit_item'

# --- Screens ---
class LoginScreen(Screen):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.db = database.DB()
        self.mode='login'
        layout = BoxLayout(orientation='vertical',padding=dp(40),spacing=dp(24))
        layout.size_hint=(None,None)
        layout.size=(dp(360),dp(400))
        layout.pos_hint={'center_x':0.5,'center_y':0.5}

        self.username = ProInput(hint_text="Email")
        self.password = ProInput(hint_text="Password",password=True)
        layout.add_widget(self.username)
        layout.add_widget(self.password)

        self.feedback = Label(text="",color=THEME["danger"],size_hint_y=None,height=dp(20))
        layout.add_widget(self.feedback)

        login_btn = ProButton(text="Login",height=dp(54),size_hint_y=None)
        login_btn.bind(on_release=self.perform_action)
        layout.add_widget(login_btn)

        toggle_btn = Button(text="New here? Sign Up",font_size=dp(14),color=THEME["primary"],
                            background_normal="",background_down="",background_color=(0,0,0,0),
                            size_hint_y=None,height=dp(30))
        toggle_btn.bind(on_release=self.toggle_mode)
        layout.add_widget(toggle_btn)

        self.title_lbl = Label(text="Everyday Carry",font_size=dp(36),bold=True,color=THEME["text_primary"])
        layout.add_widget(self.title_lbl)

        self.add_widget(layout)

    def toggle_mode(self, instance):
        self.mode = 'signup' if self.mode=='login' else 'login'
        self.feedback.text=""

    def perform_action(self,instance):
        user=self.username.text.strip()
        pwd=self.password.text.strip()
        if not user or not pwd:
            self.feedback.text="Please enter Email and Password"
            return
        if self.mode=='login':
            if self.db.verify_user(user,pwd):
                self.manager.current='main'
                self.username.text=""
                self.password.text=""
            else:
                self.feedback.text="Invalid Email or Password"
        else:
            if self.db.create_user(user,pwd):
                self.feedback.text="Account created! Please login."
                self.mode='login'
            else:
                self.feedback.text="Email already exists"

class MainScreen(Screen):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical')
        header = BoxLayout(orientation='horizontal',padding=[dp(25),dp(15)],size_hint_y=None,height=dp(70))
        header.add_widget(Label(text="Dashboard",font_size=dp(24),bold=True,color=THEME["text_primary"],halign='left'))
        header.add_widget(Label(text="Admin",font_size=dp(14),color=THEME["primary"],halign='right'))
        layout.add_widget(header)

        self.scroll=ScrollView(size_hint=(1,1))
        self.items_grid=GridLayout(cols=1,spacing=dp(15),size_hint_y=None,padding=[dp(20),dp(10)])
        self.items_grid.bind(minimum_height=self.items_grid.setter('height'))
        self.scroll.add_widget(self.items_grid)
        layout.add_widget(self.scroll)

        dock = BoxLayout(orientation='horizontal',spacing=dp(15),padding=[dp(20),dp(10)],size_hint_y=None,height=dp(60))
        add_btn = ProButton(text="Add")
        add_btn.bind(on_release=lambda x: setattr(self.manager,'current','add_item'))
        dock.add_widget(add_btn)
        layout.add_widget(dock)

        self.add_widget(layout)
        Clock.schedule_once(lambda dt:self.load_items())

    def load_items(self):
        self.items_grid.clear_widgets()
        db=database.DB()
        items=db.get_items()
        global items_list
        items_list=[]
        for row in items:
            item_id,name,desc,mac=row
            items_list.append({"id":item_id,"name":name,"desc":desc,"mac":mac})
            self.items_grid.add_widget(ItemCard(name,desc,len(items_list)-1))
        if not items_list:
            self.items_grid.add_widget(Label(text="No Items Found",color=THEME["text_secondary"],font_size=dp(18)))

    def update_items_list(self):
        self.load_items()

# --- Add Item Screen ---
class AddItemScreen(Screen):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        root=BoxLayout(orientation='vertical',padding=[dp(30),dp(50),dp(30),dp(30)],spacing=dp(20))
        self.name_input=ProInput(hint_text="Item Name")
        self.desc_input=ProInput(hint_text="Description")
        root.add_widget(self.name_input)
        root.add_widget(self.desc_input)
        save_btn=ProButton(text="Save Item")
        save_btn.bind(on_release=self.save_item)
        root.add_widget(save_btn)
        cancel_btn=ProButton(text="Cancel")
        cancel_btn.bind(on_release=lambda x:setattr(self.manager,'current','main'))
        root.add_widget(cancel_btn)
        self.add_widget(root)

    def save_item(self,instance):
        name=self.name_input.text.strip()
        desc=self.desc_input.text.strip()
        if name:
            db=database.DB()
            db.add_item(name,desc,'')
            global items_list
            items_list.append({"id":len(items_list)+1,"name":name,"desc":desc,"mac":''})
            self.manager.get_screen('main').update_items_list()
            self.name_input.text=""
            self.desc_input.text=""
            self.manager.current='main'

# --- App ---
class EverydayCarryApp(App):
    def build(self):
        sm=ScreenManager(transition=FadeTransition(duration=0.2))
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(AddItemScreen(name='add_item'))

        # Start MQTT in separate thread
        threading.Thread(target=mqtt_handler.start_mqtt, args=(self,),daemon=True).start()

        # Start camera thread for person detection
        threading.Thread(target=self.camera_check,daemon=True).start()

        return sm

    def camera_check(self):
        cap=cv2.VideoCapture(0)
        while True:
            ret,frame=cap.read()
            if not ret:
                continue
            # Simple detection placeholder: assume person detected if frame is not empty
            if frame is not None:
                missing_items=missing_logic.check_missing_items()
                if missing_items:
                    for item in missing_items:
                        Clock.schedule_once(lambda dt,i=item:self.show_missing_popup(i))
            time.sleep(2)

    def show_missing_popup(self,item):
        content=BoxLayout(orientation='vertical',padding=dp(10))
        content.add_widget(Label(text=f"Missing: {item['name']}\nLast seen: {item.get('last_seen','unknown')}"))
        btn=ProButton(text="OK")
        content.add_widget(btn)
        popup=Popup(title="Missing Item Detected",content=content,size_hint=(0.6,0.4))
        btn.bind(on_release=popup.dismiss)
        popup.open()

if __name__=="__main__":
    EverydayCarryApp().run()
