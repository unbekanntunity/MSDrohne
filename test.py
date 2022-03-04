import os

from kivy.uix.button import Button

os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'

import kivy
kivy.require('2.0.0')

from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy_garden.mapview import MapView
from kivy_garden.mapview import MapMarker


class Root(FloatLayout):
    def __init__(self, **kwargs):
        self._map = MapView(zoom=1, lon=50.6394, lat=3.057)
        super(Root, self).__init__(**kwargs)

    def on_kv_post(self, base_widget):
        btn = Button()
        btn.bind(on_release=self.add_wp)
        btn.size_hint = .3, .3
        self.add_widget(self._map)
        self.add_widget(btn)

    def add_wp(self, *args):
        print('ades')
        m1 = MapMarker(lon=50.6394, lat=3.057)  # Lille
        self._map.add_marker(m1)


class TestApp(App):
    def build(self):
        return Root()


if __name__ == '__main__':
    TestApp().run()