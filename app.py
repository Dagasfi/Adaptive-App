import os
os.environ['KIVY_NO_ARGS']='1'
# os.environ["KIVY_NO_CONSOLELOG"] = "1"


# from kivymd.icon_definitions import md_icons
from kivymd.app import MDApp as App


from kivy.uix.widget import Widget
from kivy.lang import Builder
from kivy.properties import ListProperty
from kivy.uix.screenmanager import Screen, ScreenManager

from kivy.clock import mainthread
from kivy.logger import Logger

from PIL import Image as PILImage

import threading
import time

from flask import Flask, request, send_file
import json
import base64
import numpy as np

host_name = "127.0.0.1"
port = 23336
server = Flask(__name__)


# Designate Our .kv design file
basedir = os.path.dirname(__file__)
filename = "adaptive.kv"
if basedir is not "":
    filename = "/" + filename
Builder.load_file(basedir+filename)

layouts = ["list", "grid_2", "grid_3", "grid_4", "grid_5"]
themes = ["light", "dark"]


class MyLayout(Screen):

    color = ListProperty((0,0,0))
    bg_color = ListProperty((1,1,1))
    rows = 3
    cols = 5
    totalItems = 12
    image = None

    def change_layout(self, change, cols='0'):
        splitted = change.split("_")
        if len(splitted) == 1 and splitted[0] == "list":
            self.ids.mainBoxLayout.orientation = "vertical"
            self.ids.mainGridLayout.cols = 1
            self.ids.mainGridLayout.rows = self.totalItems
            for element in self.ids.mainGridLayout.children:
                element.height = 50
        elif len(splitted) == 2 and splitted[0] == "grid":
            self.cols = int(splitted[1])
            
            self.ids.mainBoxLayout.orientation = "horizontal"
            self.ids.mainGridLayout.cols = self.cols
            self.ids.mainGridLayout.rows = int(self.totalItems/self.cols)
            for element in self.ids.mainGridLayout.children:
                element.height = 100             

    def change_theme(self, change):
        if change == "light":
            self.color = [0,0,0]
            self.bg_color = [1,1,1]
        elif change == "dark":
            self.color = [1,1,1]
            self.bg_color = [0,0,0]

    def checkbox_click(self, instance, value, change):
        if value == True:
            if change in ["list", "grid_2", "grid_3", "grid_4", "grid_5"]:
                self.change_layout(change)
            elif change in themes:
                self.change_theme(change)
    
    @mainthread
    def export(self, *args):
        print("clicked export")
        self.export_to_png("test1.png")

    @mainthread
    def export_image(self):
        print("exoport image")
        img = self.export_as_image()
        pil_img = PILImage.frombytes('RGBA',
                                     img.texture.size,
                                     img.texture.pixels)
        self.image = pil_img

    

class AdaptiveApp(App):
    
    def build(self):
        screen = Screen()
        self.ui = MyLayout()
        screen.add_widget(self.ui)
        self.export_flag = 0
        self.image = None
        self.exporter = threading.Thread(target=self.listen_export, args=(), daemon=True)
        self.exporter.start()
        return screen
    
    def switch_layout_style(self, change):
        change = change.lower()
        self.ui.change_layout(change)

    def switch_theme_style(self, change):
        self.theme_cls.theme_style = change.capitalize()
        self.ui.change_theme(change)
 
    def listen_export(self):
        while True:
            if self.export_flag:
                self.ui.export_image()
                time.sleep(0.5)
                while(self.ui.image is None):
                    time.sleep(0.1)
                self.export_flag = 0
            time.sleep(0.1)

class AppMain():

    def __init__(self):
        self.app = AdaptiveApp()
        print("Instantiated the APP!")
    
    @mainthread
    def start_app(self):
        print("Starting the app.")
        self.app.start()

@server.route('/adapt', methods = ['GET'])
def adapt():
    change= request.args.get('change')
    print(change)
    assert change is not None
    change = change.lower()
    if change in themes:
        main_app.switch_theme_style(change)
    elif change in layouts:
        main_app.switch_layout_style(change)
    ret = "switched to: "+ change
    return ret


@server.route('/image', methods = ['GET'])
def get_image():
    main_app.export_flag = True
    while main_app.export_flag:
        time.sleep(0.1)
    img = main_app.ui.image
    data = {}
    data['image'] = json.dumps(np.array(img).tolist())
    main_app.ui.image = None
    return data


if __name__ == '__main__':
    main_app = AdaptiveApp()
    threading.Thread(target=lambda: server.run(host=host_name, port=port, debug=True, use_reloader=False)).start()
    main_app.run()

