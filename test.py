import os
os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'

import kivy
kivy.require('2.0.0')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from kivy.properties import StringProperty
from kivy.uix.label import Label


class Root(BoxLayout):

    def __init__(self, **kwargs):
        super(BoxLayout, self).__init__(**kwargs)
        self.fonts = ['./data/fonts/ChopinScript']

        self.l = Label(text='test', markup=True)
        self.ids.test.add_widget(self.l)

        Clock.schedule_interval(self.set_rnd_title, 2)

    def set_rnd_title(self, *args):
        self.l.text = f'[font={self.fonts[0]}]test[/font]'
        self.l.font_size = 50
        print(f'font changed')


class TestApp(App):
    def build(self):
        return Root()


if __name__ == '__main__':
    TestApp().run()
