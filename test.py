import os
os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'

import kivy
kivy.require('2.0.0')

from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy_garden.mapview import MapView


class Root(FloatLayout):
    def __init__(self, **kwargs):
        super(Root, self).__init__(**kwargs)

    def on_kv_post(self, base_widget):
        map = MapView(zoom=1, lon=50.6394, lat=3.057)
        self.add_widget(map)


class TestApp(App):
    def build(self):
        return Root()


if __name__ == '__main__':
    TestApp().run()