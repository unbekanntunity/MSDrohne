import os
os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'

import kivy
kivy.require('2.0.0')

from kivy.app import App
from kivy.uix.textinput import TextInput
from kivy.uix.anchorlayout import AnchorLayout

class Root(AnchorLayout):
    pass

class TestApp(App):
    __version__ = "0.1"

    def build(self):
        return Root()


if __name__ == '__main__':
    TestApp().run()