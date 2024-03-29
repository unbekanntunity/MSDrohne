import os
import platform
platform = platform.uname()
os_on_device = platform.system

print(os_on_device)
if os_on_device == 'Windows':
    os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'

from kivy import Config
Config.set('graphics', 'multisamples', '0')

from kivymd.app import MDApp

from kivy.clock import Clock
from kivy.properties import StringProperty, NumericProperty, ObjectProperty

from kivy.uix.anchorlayout import AnchorLayout

from kivy.metrics import dp
from kivymd.uix.list import IRightBodyTouch, TwoLineAvatarIconListItem, ILeftBodyTouch, OneLineAvatarIconListItem
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.snackbar import BaseSnackbar
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDFillRoundFlatIconButton
from kivymd.uix.menu import MDDropdownMenu

from configuration import Configuration

import collections
import gettext


GERMAN_UMLAUTS = {
    'ä': '-ae-',
    'ü': '-ue-',
    'ö': '-oe-',
}


class CustomSnackbar(BaseSnackbar):
    text = StringProperty(None)
    icon = StringProperty(None)
    font_size = NumericProperty("15sp")


class NetworkListItem(TwoLineAvatarIconListItem):
    network_name = StringProperty()
    network_password = StringProperty()

    def __init__(self, name, password, **kw):
        super(NetworkListItem, self).__init__(**kw)
        self.on_arrow_up = None
        self.on_arrow_down = None

        self.on_edit = None
        self.on_delete = None

        self.network_name = name
        self.network_password = password


class RightContainer(IRightBodyTouch, MDBoxLayout):
    pass


class LeftContainer(ILeftBodyTouch, MDBoxLayout):
    pass


class LanguageListItem(OneLineAvatarIconListItem):
    left_icon = StringProperty()


class LanguageDropDown(MDBoxLayout):
    def __init__(self, **kwargs):
        self.menu = None
        super(LanguageDropDown, self).__init__(**kwargs)

    def on_touch_down(self, touch):
        self.menu.open()


class NetworkArea(AnchorLayout):
    text = StringProperty()

    network_card = ObjectProperty()
    name_field = ObjectProperty()
    pass_field = ObjectProperty()

    def __init__(self, **kwargs):
        self.on_discard = None
        self.on_save = None

        self._visible = False
        super(NetworkArea, self).__init__(**kwargs)

    def on_touch_down(self, touch):
        # True -> Wir haben den Touch registriert und verarbeitet und wollen es nicht, dass
        # dieser Touch zu den Elternobjekte weitergeleitet wird
        if self._visible and self.network_card.collide_point(*touch.pos):
            super(NetworkArea, self).on_touch_down(touch)
            return True
        elif self._visible:
            return True

    def set_visibility(self, visible):
        if hasattr(self, 'saved_attrs'):
            if visible:
                self.height, self.size_hint_y, self.opacity, self.disabled = self.saved_attrs
                del self.saved_attrs
                self._visible = True
        elif not visible:
            self.saved_attrs = self.height, self.size_hint_y, self.opacity, self.disabled
            self.height, self.size_hint_y, self.opacity, self.disabled = 0, None, 0, True
            self._visible = False


class NetworkRoot(MDScreen):
    def __init__(self, **kw):
        self.old_networks = []
        self.current_edited_idx = -1

        self.language_full = [entry for entry in os.listdir('./locales') if os.path.isdir('./locales/' + entry)]

        self.clear_networks_dialog = None

        self.menu = MDDropdownMenu()
        super(NetworkRoot, self).__init__(**kw)

    def on_kv_post(self, base_widget):
        self.ids.add_network_area.set_visibility(False)
        self.ids.edit_network_area.set_visibility(False)

        self.ids.add_network_area.on_save = lambda *arguements: \
            self.save_network(self.ids.add_network_area, 'add')
        self.ids.add_network_area.on_discard = lambda *arguments: \
            self.discard_network(self.ids.add_network_area, *arguments)

        self.ids.edit_network_area.on_save = lambda *arguements: \
            self.save_network(self.ids.edit_network_area, 'edit')
        self.ids.edit_network_area.on_discard = lambda *arguments: \
            self.discard_network(self.ids.edit_network_area, *arguments)

        networks = MDApp.get_running_app().configuration.config_dict['networks']
        self.add_to_network_list(networks)

        self.old_networks = networks.copy()

        menu_items = [
            {
                "text": language.split('_')[0],
                "left_icon": f'./data/res/{language.split("_")[0]}_flag.png',
                "viewclass": "LanguageListItem",
                "height": dp(54),
                "on_release": lambda x=i: self.menu_item_selected(x),

            } for i, language in enumerate(self.language_full)
        ]

        self.ids.language_drop_down.menu = MDDropdownMenu(
            caller=self.ids.caller_btn,
            items=menu_items,
            width_mult=3
        )

    def menu_item_selected(self, index: int) -> None:
        app = MDApp.get_running_app()

        # In der Variable self.languague_full befinden sich die Namen der Verzeichnisse in denen die
        # Übersetzungsdateien sind z.B de_DE
        # Wir wollen jedoch nur eine den ersten Teil haben z.B de
        language = self.language_full[index].split('_')[0]
        app.configuration.config_dict['current_language'] = language

        self.ids.language_drop_down.children[0].text = language
        self.ids.language_drop_down.children[1].source = f'./data/res/{language.split("_")[0]}_flag.png'

        # Speicher die Konfiguration ab
        app.configuration.save_config()

        # Aktualisiere die registrierten Texte
        app.set_translation()
        app.update_text()

        # Schließ das Menü
        self.ids.language_drop_down.menu.dismiss()

    def create_list_item(self, name, password):
        entry = NetworkListItem(name=name, password=password)
        entry.on_edit = self.edit_network
        entry.on_delete = self.delete_network
        entry.on_arrow_up = lambda x: self.move_network('up', x)
        entry.on_arrow_down = lambda y: self.move_network('down', y)
        return entry

    def add_to_network_list(self, updated_part):
        for network in updated_part:
            self.ids.network_list.add_widget(self.create_list_item(network['name'], network['password']))

    def add_network(self, *args):
        self.ids.add_network_area.set_visibility(True)

    def clear_networks(self, *args):
        self.clear_networks_dialog = MDDialog(
            text=MDApp.get_running_app().translate('Do u really want to delete all entries?'),
            buttons=[
                MDFlatButton(
                    text=MDApp.get_running_app().translate('Yes'),
                    theme_text_color="Custom",
                    text_color=MDApp.get_running_app().theme_cls.primary_color,
                    on_release=self.accept_clear
                ),
                MDFlatButton(
                    text=MDApp.get_running_app().translate('No'),
                    theme_text_color="Custom",
                    text_color=MDApp.get_running_app().theme_cls.primary_color,
                    on_release=self.cancel_clear
                )
            ]
        )
        self.clear_networks_dialog.open()

    def accept_clear(self, *args):
        networks = MDApp.get_running_app().configuration.config_dict['networks']
        networks.clear()

        self.ids.network_list.clear_widgets()
        self.clear_networks_dialog.dismiss(force=True)

        CustomSnackbar(
            text=MDApp.get_running_app().translate('All entries deleted!'),
            icon='information',
            snackbar_x='10dp',
            snackbar_y='10dp',
            size_hint_x=.5
        ).open()

    def cancel_clear(self, *args):
        self.clear_networks_dialog.dismiss(force=True)

    def restore_networks(self, *args):
        names = [child.network_name for child in self.ids.network_list.children]
        passwords = [child.network_name for child in self.ids.network_list.children]

        old_names = [network['name'] for network in self.old_networks]
        old_passwords = [network['password'] for network in self.old_networks]

        if collections.Counter(names) != collections.Counter(old_names) and\
                collections.Counter(passwords) != collections.Counter(old_passwords):
            self.ids.network_list.clear_widgets()
            self.add_to_network_list(self.old_networks)
            CustomSnackbar(
                text=MDApp.get_running_app().bind_text(self, 'List refreshed!'),
                icon='information',
                snackbar_x='10dp',
                snackbar_y='10dp',
                size_hint_x=.5
            ).open()
        else:
            CustomSnackbar(
                text=MDApp.get_running_app().bind_text(self, 'List is already up to date!'),
                icon='information',
                snackbar_x='10dp',
                snackbar_y='10dp',
                size_hint_x=.5
            ).open()

    def save_networks(self):
        try:
            MDApp.get_running_app().configuration.save_config()
            CustomSnackbar(
                text=MDApp.get_running_app().bind_text(self, 'List saved!'),
                icon='information',
                snackbar_x='10dp',
                snackbar_y='10dp',
                size_hint_x=.5
            ).open()
            Clock.schedule_once(lambda *arguments: exit(0), 1)
        except Exception as e:
            CustomSnackbar(
                text='Ohh, something went wrong!',
                icon='alert-circle-outline',
                snackbar_x='10dp',
                snackbar_y='10dp',
                size_hint_x=.5
            ).open()

    @staticmethod
    def discard_network(network_area, button):
        network_area.name_field.required = False
        network_area.name_field.text = ''
        network_area.name_field.required = True

        network_area.pass_field.required = False
        network_area.pass_field.text = ''
        network_area.pass_field.required = True

        network_area.set_visibility(False)

    def move_network(self, direction, item):
        networks = MDApp.get_running_app().configuration.config_dict['networks']
        items = self.ids.network_list.children.copy()

        factor = {
            'up': {
                'value': 1,
                'limit': len(items) - 1
            },
            'down': {
                'value': -1,
                'limit': 0
            }
        }

        for i, child in enumerate(items):
            if child == item:
                idx = len(items) - 1 - i
                if i != factor[direction]['limit']:
                    networks[idx], networks[idx - factor[direction]['value']] = networks[idx - factor[direction]['value']], networks[idx]
                    self.ids.network_list.remove_widget(child)
                    self.ids.network_list.add_widget(child, i + (1 * factor[direction]['value']))
                    break
                else:
                    return

    def edit_network(self, item):
        networks = MDApp.get_running_app().configuration.config_dict['networks']
        for i, child in enumerate(self.ids.network_list.children):
            if child == item:
                reversed_index = len(networks) - 1 - i
                self.current_edited_idx = i
                self.ids.edit_network_area.set_visibility(True)
                self.ids.edit_network_area.name_field.text = networks[reversed_index]['name']
                self.ids.edit_network_area.pass_field.text = networks[reversed_index]['password']
                break

    def save_network(self, area, mode):
        if mode != 'edit' and mode != 'add':
            raise ValueError('mode has to be edit or add')

        networks = MDApp.get_running_app().configuration.config_dict['networks']

        names = [network['name'] for network in networks]
        passwords = [network['password'] for network in networks]

        name_field = area.name_field
        password_field = area.pass_field

        app = MDApp.get_running_app()
        if name_field.text == '':
            CustomSnackbar(
                text=app.translate('Name cant be empty!'),
                icon='alert-circle-outline',
                snackbar_x='10dp',
                snackbar_y='10dp',
                size_hint_x=.5
            ).open()
            return
        if password_field.text == '':
            CustomSnackbar(
                text=app.translate('Password cant be empty!'),
                icon='alert-circle-outline',
                snackbar_x='10dp',
                snackbar_y='10dp',
                size_hint_x=.5
            ).open()
            return

        if name_field.text in names and password_field.text in passwords:
            CustomSnackbar(
                text='Network already exists!',
                icon='information',
                snackbar_x='10dp',
                snackbar_y='10dp',
                size_hint_x=.5
            ).open()
            return
        else:
            if mode == 'edit':
                self.apply_edit_changes(networks, name_field, password_field)
            else:
                self.apply_add_changes(networks, name_field, password_field)
            area.set_visibility(False)

    def apply_add_changes(self, networks, name_field, password_field):
        new_network = {
            'name': name_field.text,
            'password': password_field.text
        }

        networks.append(new_network)

        name_field.text = ''
        password_field.text = ''

        self.add_to_network_list([new_network])

    def apply_edit_changes(self, networks, name_field, password_field):
        item = self.ids.network_list.children[self.current_edited_idx]

        networks[len(networks) - 1 - self.current_edited_idx] = {
            'name': name_field.text,
            'password': password_field.text
        }

        new_item = self.create_list_item(name_field.text, password_field.text)

        self.ids.network_list.remove_widget(item)
        self.ids.network_list.add_widget(new_item, self.current_edited_idx)

    def delete_network(self, *args):
        networks = MDApp.get_running_app().configuration.config_dict['networks']
        for i, child in enumerate(self.ids.network_list.children):
            if child == args[0]:
                networks.pop(i)
                self.ids.network_list.remove_widget(args[0])
                break


class NetworkApp(MDApp):
    configuration = Configuration('./data/network.json', load_at_init=True)

    def __init__(self, **kwargs):
        super(NetworkApp, self).__init__(**kwargs)

        self.translated_labels = []
        self.translated_parts = []

        self.translation = None

    def build(self):
        self.theme_cls.material_style = "M3"
        self.set_translation()
        return NetworkRoot()

    def set_translation(self) -> None:
        language = self.configuration.config_dict['current_language'] + '_' + \
                   self.configuration.config_dict['current_language'].upper()
        self.translation = gettext.translation('base', localedir='locales',
                                               languages=[language])
        self.translation.install()

    def bind_text(self, label, text, entire_text=None) -> str:
        """
        Registriert den Label. Durch die update_text Funktion kann dann der Text aktualisiert werden.
        Das wird vor allem wichtig, wenn die Sprache geändert wurde una alle Texte in der App
        geändert werden müssen.

        Parameters
        ----------
        label: Label
            Das Label.
        text: str
            Der Teil des Textes, der übersetzt werden soll.
        entire_text: str
            Der ganze Text.

        Returns
        -------
        <nameless>: str
            Die übersetzte Zeichenkette.
            Findet sich keine Übersetzung wird die Zeichenkette unverändert zurückgegeben.
        """
        if entire_text is None:
            entire_text = text

        self.translated_labels.append(label)
        translated_text = self.translate(text)

        self.translated_parts.append(translated_text)
        return entire_text.replace(text, translated_text)

    def update_text(self) -> None:
        """
        Aktualisiert die registrierten Widgets.
        """

        for index, widget in enumerate(self.translated_labels):
            translated_text = self.translate(self.translated_parts[index])
            widget.text = widget.text.replace(self.translated_parts[index], translated_text)
            if isinstance(widget, MDFillRoundFlatIconButton):
                widget.apply_class_lang_rules(self)
            self.translated_parts[index] = translated_text

    @staticmethod
    def translate(message: str) -> str:
        """
        Übersetzte eine Zeichenkette mit der Sprache, die gerade in der App
        eingestellt ist und gibt sie wieder zurück.
        Falls keine Übersetzung vorhanden wird, wird die Zeichenkette unübersetzt zurückgegeben.

        Parameters
        ----------
        message: str
            Die zu übersetzende Zeichenkette.
        """

        app = MDApp.get_running_app()
        if app.configuration.config_dict['current_language'] != 'de':
            for key, value in GERMAN_UMLAUTS.items():
                message = message.replace(key, value)

        decoded = app.translation.gettext(message)

        if app.configuration.config_dict['current_language'] == 'de':
            for key, value in GERMAN_UMLAUTS.items():
                decoded = decoded.replace(value, key)
        return decoded


if __name__ == '__main__':
    NetworkApp().run()
