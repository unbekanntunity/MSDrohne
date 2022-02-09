import os
os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'

import kivy
kivy.require('2.0.0')

from kivy.app import App
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.label import Label
from kivy.properties import ObjectProperty
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.popup import Popup


class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)


class Root(AnchorLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)

    def __init__(self, **kwargs):
        content = LoadDialog(load=self.load, cancel=self.dismiss_popup)
        self._popup = Popup(title="Load file", content=content,
                            size_hint=(0.9, 0.9))
        self._popup.open()
        super().__init__(**kwargs)

    def dismiss_popup(self):
        self._popup.dismiss()

    def load(self, path, filename):
        print(path)
        print(filename)

        self.dismiss_popup()


class TestApp(App):
    __version__ = "0.1"

    def build(self):
        r = Root()
        return r


def hide_widget(widget, dohide=True):
    if hasattr(widget, 'saved_attrs'):
        if not dohide:
            widget.height, widget.size_hint_y, widget.opacity, widget.disabled = widget.saved_attrs
            del widget.saved_attrs
    elif dohide:
        widget.saved_attrs = widget.height, widget.size_hint_y, widget.opacity, widget.disabled
        widget.height, widget.size_hint_y, widget.opacity, widget.disabled = 0, None, 0, True


if __name__ == '__main__':
    TestApp().run()