from kivy.uix.widget import Widget
from kivy.properties import ListProperty, NumericProperty


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
        self.js_center_origin_x = self.center_x
        self.js_center_origin_y = self.center_y

        self.js_center_x = self.js_center_origin_x
        self.js_center_y = self.js_center_origin_y

        self.process_touch = False

    def on_touch_down(self, touch):
        result = (round(touch.pos[0]) - self.center_x)**2 + (round(touch.pos[1]) - self.js_center_y)**2 - self.outer_radius**2
        if result < 0:
            self.process_touch = True
        super().on_touch_up(touch)

    def on_touch_move(self, touch):
        if self.process_touch:
            self.update_center(round(touch.pos[0]), round(touch.pos[1]))
        super().on_touch_move(touch)

    def on_touch_up(self, touch):
        self.js_center_x = self.js_center_origin_x
        self.js_center_y = self.js_center_origin_y
        self.process_touch = False
        super().on_touch_up(touch)

    def set_center(self, *args):
        self.js_center_origin_x = self.canvas.children[2].pos[0] + self.outer_radius
        self.js_center_origin_y = self.canvas.children[2].pos[1] + self.outer_radius

        self.js_center_x = self.js_center_origin_x
        self.js_center_y = self.js_center_origin_y

    def update_center(self, x, y):
        center = self.canvas.children[2]
        adapted_x = center.pos[0] + self.outer_radius
        adapted_y = center.pos[1] + self.outer_radius

        self.js_center_x = self.js_center_origin_x + (x - adapted_x)
        self.js_center_y = self.js_center_origin_y + (y - adapted_y)
