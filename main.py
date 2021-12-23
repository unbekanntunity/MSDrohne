import os

from kivy.uix.label import Label

os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'

import kivy
kivy.require('2.0.0')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.screenmanager import Screen, ScreenManager

from kivy.properties import ObjectProperty

from Communication import client

import platform
platform = platform.uname()
os = platform.system


class RoundedButton(Button):
    pass


class StartScreen(Screen):
    pass


class ConnectionScreen(Screen):
    connections = ObjectProperty()

    def __init__(self, **kwargs):
        super(ConnectionScreen, self).__init__(**kwargs)
        self.entries = []

    def on_enter(self, *args):
        bt_results = client.bluetooth_list(os)
        print(bt_results)
        for index, result in zip(range(0, len(bt_results)), bt_results):
            name = Label(text=result[0], height=20, size_hint_y=None)
            power = Label(text=result[1], height=20, size_hint_y=None)
            connect = Button(text="C", height=20, size_hint_y=None, on_release=lambda *args: self.connect(*args))
            self.connections.add_widget(name)
            self.connections.add_widget(power)
            self.connections.add_widget(connect)
            self.entries.append([name, power, connect])

    def connect(self, *args):
        for entry in self.entries:
            if entry[2] == args[0]:
                name, power = entry[0], entry[1]
                self.manager.current = 'control'


class ControlScreen(Screen):
    pass


class MyScreenManager(ScreenManager):
    pass


class DroneRoot(BoxLayout):
    pass


class DroneApp(App):
    def build(self):
        root = DroneRoot()
        return root


if __name__ == '__main__':
    DroneApp().run()

