import os
os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'


from kivymd.app import MDApp

from kivy.properties import StringProperty
from kivymd.uix.behaviors import RoundedRectangularElevationBehavior
from kivymd.uix.card import MDCard, MDCardSwipe

from kivymd.uix.list import IRightBodyTouch, TwoLineAvatarIconListItem
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout

from misc.configuration import Configuration


class ListItem(TwoLineAvatarIconListItem):
    network_name = StringProperty()
    network_password = StringProperty()

    def __init__(self, name, password, **kw):
        super(ListItem, self).__init__(**kw)
        self.network_name = name
        self.network_password = password


class RightContainer(IRightBodyTouch, MDBoxLayout):
    adaptive_width = True


class NetworkRoot(MDScreen):
    def on_kv_post(self, base_widget):
        self.set_visibility_widget(self.ids.network_card)

        networks = MDApp.get_running_app().configuration.config_dict['networks']
        for network in networks:
            self.ids.network_list.add_widget(ListItem(name=network['name'], password=network['password']))

    def on_add(self, *args):
        self.set_visibility_widget(self.ids.network_card, dohide=False)

    def save_network(self, *args):
        self.set_visibility_widget(self.ids.network_card)

    @staticmethod
    def set_visibility_widget(widget, dohide=True):
        if hasattr(widget, 'saved_attrs'):
            if not dohide:
                widget.height, widget.size_hint_y, widget.opacity, widget.disabled = widget.saved_attrs
                del widget.saved_attrs
        elif dohide:
            widget.saved_attrs = widget.height, widget.size_hint_y, widget.opacity, widget.disabled
            widget.height, widget.size_hint_y, widget.opacity, widget.disabled = 0, None, 0, True


class NetworkApp(MDApp):
    configuration = Configuration('../data/network.json', load_at_init=True)

    def build(self):
        self.theme_cls.material_style = "M3"

        return NetworkRoot()


if __name__ == '__main__':
    NetworkApp().run()
