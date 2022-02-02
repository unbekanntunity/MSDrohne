'''
3D Rotating Monkey Head
========================
This example demonstrates using OpenGL to display a rotating monkey head. This
includes loading a Blender OBJ file, shaders written in OpenGL's Shading
Language (GLSL), and using scheduled callbacks.
The monkey.obj file is an OBJ file output from the Blender free 3D creation
software. The file is text, listing vertices and faces and is loaded
using a class in the file objloader.py. The file simple.glsl is
a simple vertex and fragment shader written in GLSL.
'''
import os
os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.resources import resource_find
from kivy.graphics.transformation import Matrix
from kivy.graphics.opengl import glEnable, glDisable, GL_DEPTH_TEST
from kivy.graphics import RenderContext, Callback, PushMatrix, PopMatrix, \
    Color, Translate, Rotate, Mesh, UpdateNormalMatrix
from objloader import ObjFile


class Renderer(Widget):
    def __init__(self, **kwargs):
        self.canvas = RenderContext(compute_normal_mat=True)
        self.canvas.shader.source = resource_find('simple.glsl')
        self.scene = ObjFile(resource_find("monkey.obj"))
        super(Renderer, self).__init__(**kwargs)
        with self.canvas:
            self.cb = Callback(self.setup_gl_context)
            PushMatrix()
            self.setup_scene()
            PopMatrix()
            self.cb = Callback(self.reset_gl_context)
        self.update_glsl(1/60.)

        self.points = []

        self.tick = 0
        self.max_tick = 5

    def setup_gl_context(self, *args):
        glEnable(GL_DEPTH_TEST)

    def reset_gl_context(self, *args):
        glDisable(GL_DEPTH_TEST)

    def update_glsl(self, delta):
        asp = self.width / float(self.height)
        proj = Matrix().view_clip(-asp, asp, -1, 1, 1, 100, 1)
        self.canvas['projection_mat'] = proj
        self.canvas['diffuse_light'] = (1.0, 1.0, 0.8)
        self.canvas['ambient_light'] = (0.1, 0.1, 0.1)
        self.rot.angle += delta * 100

    def on_touch_down(self, touch):
        self.points.append(touch.pos)

    def on_touch_move(self, touch):
        if len(self.points) == 0:
            return

        last_point = self.points.pop()
        new_point = touch.pos

        diff_x = last_point[0] - new_point[0]
        diff_y = last_point[1] - new_point[1]
        print(diff_x, diff_y)

        if diff_x != 0 and diff_y != 0:
            diff_z = diff_y / -diff_x
        else:
            diff_z = 0

        axis = (self.rot.axis[0] + diff_y, self.rot.axis[1] - diff_x, self.rot.axis[2] + diff_z)
        self.rot.axis = axis
        self.update_glsl(1 / 60.)

        self.points.append(touch.pos)
        self.tick = 0
        super(Renderer, self).on_touch_move(touch)

    def on_touch_up(self, touch):
        self.points.clear()

    def setup_scene(self):
        Color(1, 1, 1, 1)
        PushMatrix()
        Translate(0, 0, -3)
        self.rot = Rotate(0, 1, 0, 0)
        m = list(self.scene.objects.values())[0]
        UpdateNormalMatrix()
        self.mesh = Mesh(
            vertices=m.vertices,
            indices=m.indices,
            fmt=m.vertex_format,
            mode='triangles',
        )
        PopMatrix()


class RendererApp(App):
    def build(self):
        return Renderer()


if __name__ == "__main__":
    RendererApp().run()