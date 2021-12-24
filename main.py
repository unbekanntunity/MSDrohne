import os
import threading
import time

from kivy.clock import Clock

os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'

import kivy
kivy.require('2.0.0')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.screenmanager import Screen, ScreenManager

from kivy.properties import ObjectProperty

from Communication import client, custom_threads
from Rnd import eventHandling

import platform
platform = platform.uname()
os = platform.system

TESTCASE = True
bluetooth = None
wlan = None


class RoundedButton(Button):
    pass


class StartScreen(Screen):
    pass


class SelectableRow(BoxLayout):
    name = ObjectProperty()
    power = ObjectProperty()

    def __init__(self, parent_widget=None, **kwargs):
        super(SelectableRow, self).__init__(**kwargs)
        self.parent_widget = parent_widget
        self.connection_thread = custom_threads.DisposableThread()

    def on_touch_down(self, touch):
        if self.collide_point(touch.x, touch.y):
            self.connection_thread.events.add_event(lambda: self.parent_widget.connect(self))
            self.connection_thread.on_finished_events.add_event(self.parent_widget.connection_finished)
            self.connection_thread.start()
        return super(BoxLayout, self).on_touch_down(touch)


class ConnectionScreen(Screen):
    connections = ObjectProperty()
    status = ObjectProperty()
    scrollview = ObjectProperty()

    def __init__(self, **kwargs):
        super(ConnectionScreen, self).__init__(**kwargs)
        self.tries = 10
        self.connected = False

        self.iteration = 0
        self.animation_callback = self.connection_animation

    def on_enter(self, *args):
        bt_results = client.bluetooth_list(os)
        for index, result in zip(range(0, len(bt_results)), bt_results):
            row = SelectableRow(parent_widget=self)
            row.name.text = result[0]
            row.power.text = result[1]
            self.connections.add_widget(row)

    def connect(self, row, *args):
        succeded_it = 4
        self.connections.height = 0
        self.status.height = self.scrollview.height
        Clock.schedule_interval(self.animation_callback, 0.5)

        connected = False
        for i in range(0, self.tries):
            if TESTCASE:
                if i == succeded_it:
                    connected = True
            else:
                try:
                    bluetooth = client.BluetoothClient()
                    connected = bluetooth.connect(row.name.text)
                except Exception as e:
                    self.status.text = str(e)
            if connected:
                self.status.text = f'Connection successfully to {row.name.text}'
                time.sleep(1)
                break
            time.sleep(1)
        self.connected = connected
        row.connection_thread.stop()

    def connection_animation(self, *args):
        if self.iteration <= 3:
            self.iteration += 1
        else:
            self.iteration = 0
        self.status.text = 'connecting' + '.' * self.iteration

    def connection_finished(self):
        if self.connected:
            Clock.unschedule(self.animation_callback)
            self.manager.current = 'wlan'


class WlanScreen(Screen):
    pass


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

