import os
os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'

import kivy
kivy.require('2.0.0')

from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.dropdown import DropDown
from kivy.graphics import Rectangle, Color

from kivy.clock import Clock
from kivy.lang import Builder

from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.settings import SettingsWithSidebar

from communication import client
from rnd import custom_threads
from customwidgets.joystick import *
from data import config

import time

import os
import platform
platform = platform.uname()
os_on_device = platform.system

TESTCASE = True
NAME = 'mpy-uart'
KV_DIRECTORY = './kv_files'
SEPARATOR = '|'

if 'Android' in os_on_device:
    bluetooth_client = client.AndroidBluetoothClient()
else:
    bluetooth_client = client.BluetoothClient()

wlan_client = client.WLANClient()


class RoundedButton(Button):
    pass


class CustomScreen(Screen):
    def go_back(self, screen_name):
        self.manager.transition.direction = 'right'
        self.manager.current = screen_name

    def on_enter(self, *args):
        self.manager.transition.direction = 'left'


class StartScreen(CustomScreen):
    pass


class SupportScreen(CustomScreen):
    def __init__(self, **kwargs):
        super(SupportScreen, self).__init__(**kwargs)

        self.questions = ['bluetooth', 'wlan1', 'wlan']
        self.questions = ['bluetooth', 'wlan1', 'wlan',
                          'bluetooth', 'wlan', 'wlan']
        self.answers = []

        for question in self.questions:
            self.answers.append(question + 'A')

        self.entry = []
        self.question_boxes = []
        self.text_boxes = []
        self.heights = []

    def on_enter(self, *args):
        for index in range(len(self.questions)):
            b1 = BoxLayout()
            b1.orientation = 'vertical'
            b1.size_hint_y = None

            btn = Button(text=self.questions[index])
            btn.bind(on_release=self.trigger_box)

            a1 = AnchorLayout()

            b1.add_widget(btn)
            b1.add_widget(a1)

            self.entry.append(b1)
            self.question_boxes.append(btn)
            self.text_boxes.append(a1)

            self.ids.question_box.add_widget(b1)
            print(self.ids.question_box.minimum_height)
        self.ids.question_box.height = self.get_height()

    def get_height(self):
        result = 0
        for box in self.question_boxes:
            result += box.height
        return result + 50

    def trigger_box(self, *args):
        for index in range(len(self.question_boxes)):
            if args[0] == self.question_boxes[index]:
                selected_text_box = self.text_boxes[index]
                if len(selected_text_box.children) == 0:
                    self.open_box(selected_text_box, index)
                else:
                    self.close_box(selected_text_box, index)
                break

    def open_box(self, answer_box, index):
        answer_box.add_widget(Button(text=self.answers[index]))

    def close_box(self, answer_box):
        for widget in answer_box.children:
            answer_box.remove_widget(widget)

    def reset(self):
        for widget in self.ids.question_box.children:
            self.ids.question_box.remove_widget(widget)

class ConnectionScreen(CustomScreen):
    status = ObjectProperty()
    wlan = ObjectProperty()

    def __init__(self, **kwargs):
        super(ConnectionScreen, self).__init__(**kwargs)
        self.connected = False

        self.response_thread = custom_threads.DisposableLoopThread()
        self.response_thread.events.add_event(self.check_response)

        self.bluetooth_connection_thread = custom_threads.DisposableLoopThread()
        self.bluetooth_connection_thread.add_event(self.check_bluetooth_connection)

    def on_enter(self, *args):
        self.bluetooth_connection_thread.save_start()

    def check_bluetooth_connection(self):
        if TESTCASE or bluetooth_client.has_paired_devices():
            if not TESTCASE:
                bluetooth_client.create_socket_stream(NAME)
            self.wlan.height = self.wlan.minimum_height
            self.bluetooth_connection_thread.stop()
        else:
            self.wlan.height = 0
            self.status.text = f'Turn on your bluetooth function and connect to the device {NAME}'
        time.sleep(1)

    def send_data(self, name, password):
        if TESTCASE:
            self.manager.current = 'control'
        else:
            bluetooth_client.socket.send(f'WLAN{SEPARATOR}{name}{SEPARATOR}{password}')
            self.response_thread.save_start()

    def check_response(self):
        wlan_response = bluetooth_client.wait_for_response(flag='WC')
        esp32_data = bluetooth_client.wait_for_response(flag='STAINFO')
        bluetooth_client.socket.send(f'WLANDATA{SEPARATOR}{wlan_client.get_ip_address()}')
        server_response = bluetooth_client.wait_for_response(flag='WS')

        if 'WC1' and wlan_client.paired_device_ip in wlan_response:
            if 'STAINFO' in esp32_data:
                converted_data = esp32_data.split(SEPARATOR)
                wlan_client.connect(converted_data[1], converted_data[2])
            self.status.text = f'Connection with {bluetooth_client.paired_device_name}'
            time.sleep(1)
            if 'WS1' in server_response:
                self.status.text = f'Server successfully created'
                time.sleep(1)
                self.manager.current = 'control'
        else:
            self.status.text = 'Connection failed'
            self.wlan.height = 0

            self.response_thread.stop()


class ControlScreen(CustomScreen):
    altitude = StringProperty()
    speed = StringProperty()

    latitude = StringProperty()
    longitude = StringProperty()

    battery = StringProperty()

    def __init__(self, **kwargs):
        super(ControlScreen, self).__init__(**kwargs)

        self.receive_thread = custom_threads.DisposableLoopThread()
        self.send_thread = custom_threads.DisposableLoopThread()

        self.receive_thread.add_event(self.receive_data)
        self.send_thread.add_event(self.send_data)

        self.speed = "0"
        self.altitude = "0"
        self.longitude = "0"
        self.latitude = "0"
        self.battery = "0"

        self.r_joystick = JoyStick()
        self.l_joystick = JoyStick()

        if not TESTCASE:
            self.receive_thread.save_start()
            self.send_thread.save_start()

        self.menu_btn = Button(text='Menu')
        self.menu_dropdown = DropDown()

    def on_enter(self, *args):
        self.ids.top_a.add_widget(self.menu_btn)

        waypoints_btn = Button(text='waypoints', size_hint_y=None, height=44)
        waypoints_btn.bind(on_release=self.open_waypoints)
        settings_btn = Button(text='settings', size_hint_y=None, height=44)
        settings_btn.bind(on_release=self.open_settings)
        self.menu_dropdown.add_widget(settings_btn)
        self.menu_dropdown.add_widget(waypoints_btn)

        self.menu_btn.bind(on_release=self.menu_dropdown.open)

        self.ids.joystick_a.add_widget(self.r_joystick)
        self.ids.joystick_a.add_widget(self.l_joystick)

        self.ids.back_btn.bind(on_press=self.back_to_main)

        Clock.schedule_once(self.r_joystick.set_center, 0.01)
        Clock.schedule_once(self.l_joystick.set_center, 0.01)

    def send_data(self):
        message = f'LJ{SEPARATOR}{self.joystick.js_center_x}{SEPARATOR}{self.joystick.js_center_y}'
        wlan_client.send_message(message)
        message = f'RJ{SEPARATOR}{self.joystick.js_center_x}{SEPARATOR}{self.joystick.js_center_y}'
        wlan_client.send_message(message)

    def receive_data(self):
        response = wlan_client.wait_for_response()
        datas = response.split(SEPARATOR)

        self.altitude = datas[0]
        self.speed = datas[1]
        self.latitude = datas[2]
        self.longitude = datas[3]

    def open_waypoints(self, *args):
        self.menu_dropdown.dismiss()
        self.manager.current = 'waypoints'

    def open_settings(self, *args):
        self.menu_dropdown.dismiss()
        App.get_running_app().open_settings()

    def reset(self):
        self.ids.top_a.remove_widget(self.menu_btn)

        for widget in self.ids.joystick_a.children:
            self.ids.joystick_a.remove_widget(widget)

    def back_to_main(self, *args):
        if not TESTCASE:
            wlan_client.send_message(f'CMD{SEPARATOR}reset')

        screens = self.manager.screens
        for screen in screens:
            try:
                screen.reset()
            except AttributeError as e:
                pass

        bluetooth_client.reset()
        wlan_client.reset()

        self.go_back('start')


class WaypointsScreen(CustomScreen):
    pass


class MyScreenManager(ScreenManager):
    pass


class DroneRoot(BoxLayout):
    pass


class DroneApp(App):
    def build(self):
        self.settings_cls = SettingsWithSidebar
        self.load_kv_files()
        return DroneRoot()

    def build_config(self, config):
        config.setdefaults('example', {
            'boolexample': True,
            'numericexample': 10,
            'optionsexample': 'option2',
            'stringexample': 'some_string',
            'pathexample': '/some/path'})

    def build_settings(self, settings):
        settings.add_json_panel('Panel name',
                                self.config,
                                data=config.settings_json)

    def load_kv_files(self):
        files = os.listdir(KV_DIRECTORY)
        for file in files:
            path = KV_DIRECTORY + '/' + file
            Builder.load_file(path)


if __name__ == '__main__':
    DroneApp().run()

