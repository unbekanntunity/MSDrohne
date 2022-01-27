import os
os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'

import kivy
kivy.require('2.0.0')

from kivy.app import App
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.label import Label


class Root(AnchorLayout):
    pass

def ping():
    print("asdasd")

class TestApp(App):
    __version__ = "0.1"

    def build(self):
        r = Root()
        r.add_widget(Label(text='aa'))
        hide_widget(r, dohide=False)
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