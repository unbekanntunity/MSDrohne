import os
os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.widget import Widget
from kivy.properties import StringProperty, ListProperty, NumericProperty
from kivy.uix.boxlayout import BoxLayout


class JoyStick(Widget):
    outer_background_color = ListProperty([0.75, 0.75, 0.75, 1])
    outer_radius = NumericProperty(70)
    outer_diameter = NumericProperty(140)

    outer_line_color = ListProperty([0.25, 0.25, 0.25, 1])
    outer_line_width = NumericProperty(1)

    inner_background_color = ListProperty([0.1, 0.7, 0.1, 1])
    inner_radius = NumericProperty(20)
    inner_diameter = NumericProperty(40)

    inner_line_color = ListProperty([0.7, 0.7, 0.7, 1])
    inner_line_width = NumericProperty(1)

    js_center_x = NumericProperty(1)
    js_center_y = NumericProperty(1)

    def __init__(self, **kwargs):
        super().__init__()

        self.js_center_origin_x = 132
        self.js_center_origin_y = 301
        self.js_center_x = self.js_center_origin_x
        self.js_center_y = self.js_center_origin_y

    def on_touch_move(self, touch):
        self.update_center(round(touch.pos[0]), round(touch.pos[1]))

    def on_touch_up(self, touch):
        self.js_center_x = self.js_center_origin_x
        self.js_center_y = self.js_center_origin_y
        super().on_touch_up(touch)

    def collide_point(self, x, y):
        result = (x - self.center_x) ** 2 + (y - self.center_y) ** 2 < self.outer_radius ** 2

    def update_center(self, x, y):
        center = self.canvas.children[2]
        adapted_x = center.pos[0] + self.outer_radius
        adapted_y = center.pos[1] + self.outer_radius

        self.js_center_x = self.js_center_origin_x + (x - adapted_x)
        self.js_center_y = self.js_center_origin_y + (y - adapted_y)


class MyLayout(BoxLayout):
    handling = StringProperty("")
    xt = StringProperty("")
    yt = StringProperty("")

    def on_touch_move(self, touch):
        self.xt, self.yt = str(round(touch.pos[0])), str(round(touch.pos[1]))
        super(BoxLayout, self).on_touch_move(touch)


KV = """
MyLayout:
    JoyStick:
        id: js
        canvas:
            ###  Outer Background  ###
            Color:
                rgba: self.outer_background_color
            Ellipse:
                pos: (self.center_x - self.outer_radius), (self.center_y - self.outer_radius)
                size: (self.outer_diameter, self.outer_diameter)
            ###  Inner Background  ###
            Color:
                rgba: self.inner_background_color
            Ellipse:
                pos: (self.js_center_x - self.inner_radius), (self.js_center_y - self.inner_radius)
                size: (self.inner_diameter, self.inner_diameter)
                on_touch_down: print("asdasd")
            ###  Outer Border  ###
            Color:
                rgba: self.outer_line_color
            Line:
                circle: (self.center_x, self.center_y, (self.outer_radius - (self.outer_line_width / 2)))
                width: self.outer_line_width
    Label: 
        text: root.xt
    Label: 
        text: root.yt

<JoystickPad>:
    canvas:
        Color:
            rgba: self.inner_background_color
        Ellipse:
            pos: (self.center_x - self.inner_radius), (self.center_y - self.inner_radius)
            size: (self.inner_diameter, self.inner_diameter)
"""


class MyApp(App):
    def build(self):
        return Builder.load_string(KV)


MyApp().run()