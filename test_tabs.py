import os
os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'
from kivy.app import App
from kivy.lang import Builder
from kivy.properties import NumericProperty, ListProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from kivy.animation import Animation

kv = '''
<AnimationExample>:
    canvas:
        Color:
            rgba: self.circle_color
        Line:
            circle: self.center_x, self.center_y, self.radius  # this sets up bindings to the Properties defined in AnimationExample
            width: self.line_width  # this sets up a binding to the line_width Property

'''


class AnimationExample(BoxLayout):
    # define properties for the circle
    circle_color = ListProperty([1, 0, 0, 1])
    radius = NumericProperty(100)
    line_width = NumericProperty(2)

    def animate(self, *args):
        # since the kv sets up bindings to the properties of this class, we can just animate those properties
        print('Animate')

        # This works for animated "width"
        width_anim = Animation(line_width=8, t='out_bounce', d=1) + Animation(line_width=2, t='out_bounce', d=1)
        width_anim.start(self)

        # to animate the circle radius
        radius_anim = Animation(radius=150, d=1) + Animation(radius=100, d=1)
        radius_anim.start(self)


class TutorialApp(App):
    def build(self):
        Builder.load_string(kv)
        r = AnimationExample()
        Clock.schedule_interval(r.animate, 2)
        return r


TutorialApp().run()