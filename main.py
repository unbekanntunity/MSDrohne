import os
import time

os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'

import kivy
kivy.require('2.0.0')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.screenmanager import Screen, ScreenManager

from kivy.properties import ObjectProperty

from Communication import client, custom_threads

import platform
platform = platform.uname()
os = platform.system

TESTCASE = True
NAME = 'ESP32'

bluetooth_client = client.BluetoothClient()
wlan_client = None


class RoundedButton(Button):
    pass


class StartScreen(Screen):
    pass


class ConnectionScreen(Screen):
    status = ObjectProperty()
    wlan = ObjectProperty()

    def __init__(self, **kwargs):
        super(ConnectionScreen, self).__init__(**kwargs)
        self.connected = False

        self.response_thread = custom_threads.DisposableThread()
        self.bluetooth_connection_thread = custom_threads.DisposableThread()

    def on_enter(self, *args):
        if 'Android' in os:
            bluetooth_client = client.AndroidBluetoothClient()
            self.bluetooth_connection_thread.add_event(self.check_bluetooth_connection)
            self.bluetooth_connection_thread.start()
        else:
            self.wlan.height = self.wlan.minimum_height

    def check_bluetooth_connection(self):
        while True:
            if bluetooth_client.has_paired_devices() or TESTCASE:
                if not TESTCASE:
                    bluetooth_client.create_socket_stream(NAME)
                self.wlan.height = self.wlan.minimum_height
                self.bluetooth_connection_thread.stop()
            else:
                self.status.text = f'Turn on your bluetooth function and connect to the device {NAME}'
            time.sleep(1)

    def send_data(self, name, password):
        if TESTCASE:
            self.manager.current = 'control'
        else:
            bluetooth_client.socket.send(f'WLAN|{name}|{password}')
            self.response_thread.events.add_event(self.check_response)
            self.response_thread.start()

    def check_response(self):
        wlan_response = bluetooth_client.wait_for_response()
        if 'WC1' in wlan_response:
            self.status.text = f'Connection with {bluetooth_client.paired_device_name}'
            server_response = bluetooth_client.wait_for_response()
            if 'WS1' in server_response:
                self.status.text = f'Server successfully created'
                time.sleep(1)
                self.manager.current = 'control'
        else:
            self.status.text = 'Connection failed'
            self.wlan.height = 0

            self.response_thread.stop()


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

