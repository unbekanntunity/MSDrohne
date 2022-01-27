import os
os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'


from kivymd.app import MDApp

from kivy.properties import StringProperty
from kivymd.uix.behaviors import RoundedRectangularElevationBehavior
from kivymd.uix.card import MDCard

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


class RoundedCard(MDCard, RoundedRectangularElevationBehavior):
    pass


class NetworkRoot(MDScreen):
    def on_kv_post(self, base_widget):
        networks = MDApp.get_running_app().configuration.config_dict['networks']
        for network in networks:
            self.ids.network_list.add_widget(ListItem(name=network['name'], password=network['password']))


class NetworkApp(MDApp):
    configuration = Configuration('../data/network.json', load_at_init=True)

    def build(self):
        return NetworkRoot()


if __name__ == '__main__':
    NetworkApp().run()
