# **************************** main.py ******************************
# Hauptklasse und Einstiegspunkt der ganzen Applikation
# *******************************************************************

# **************************** Imports ****************a**************
import os
import platform
import socket

from time import sleep

platform = platform.uname()
os_on_device = platform.system

if os_on_device == 'Windows':
    os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'

import kivy
kivy.require('2.0.0')

from kivymd.app import MDApp
from kivymd.uix.textfield import MDTextField
from kivymd.uix.screen import MDScreen
from kivymd.uix.navigationdrawer import MDNavigationDrawerItem
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.list import OneLineAvatarIconListItem
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.expansionpanel import MDExpansionPanel, MDExpansionPanelOneLine
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.anchorlayout import MDAnchorLayout
from kivymd.uix.snackbar import BaseSnackbar
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.bottomsheet import MDGridBottomSheet

from kivy.metrics import dp
from kivy.graphics import Color, Ellipse
from kivy.animation import Animation

from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager

from kivy.utils import get_color_from_hex, get_random_color
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.core.text.markup import MarkupLabel
from kivy.properties import ObjectProperty, StringProperty, BooleanProperty, BoundedNumericProperty

from communication import client
from misc.custom_threads import DisposableLoopThread
from misc.configuration import Configuration
from misc.event_handling import EventHandler
from customwidgets.joystick import *

from random import randrange, uniform
from datetime import datetime

import gettext

# ******************************************************************

# ************************** Konstanten ****************************
NAME = 'mpy-uart'
SEPARATOR = '|'
DEFAULT_WP_PREFIX = 'new waypoint'

KV_DIRECTORY = './kv_files'
FONTS_DIRECTORY = './data/fonts'

CON_INTERVAL = .5

CON_STATUS = {
    10: 'too weak',
    20: 'weak',
    50: 'acceptable',
    100: 'strong'
}
CON_ICON = {
    10: './data/res/very_weak_wifi.png',
    20: './data/res/weak_wifi.png',
    50: './data/res/medium_wifi.png',
    100: './data/res/strong_wifi.png'
}

# ******************************************************************

# ********************* Plattformspezifisch ************************

wlan_client = client.WLANClient()

# *******************************************************************

# ********************** Eigene Kivy-widgets ************************


# Wir verwenden die von Kivy implementierte kv-Sprache
# Alle in der .kv-file verwendeten Klassen, müssen auch einer Pythonskript deklariert werden
class CustomSnackbar(BaseSnackbar):
    """
    Eigene Snackbar-Implementierung

    Attributes
    ---------
    text: str
        Text, der angezeigt wird.
    icon: str
        Pfad des Icons das rechts vom Text angezeigt wird.
    font_size: int
        Die Größe des Textes in sp.
    """

    text = StringProperty(None)
    icon = StringProperty(None)
    font_size = NumericProperty("15sp")


class SupportExpansionContent(MDBoxLayout):
    """
    Bereich, der beim Aufklappen der Textfelder erscheint.

    Attributes
    ----------
    answer: str
        Text, der in Box angezeigt wird.
    """

    answer = StringProperty()

    def __init__(self, text, **kwargs):
        self.answer = text
        super(SupportExpansionContent, self).__init__(**kwargs)


class WaypointCard(MDCard):
    """
    Eine Karte, die alle Informationen über ein Wegpunkt kompakt darstellt.

    Attributes
    ----------
    name: str
        Name des Wegpunktes.
    altitude: str
        Höhe des Wegpunktes.
    latitude: str
        Breitengrad des Wegpunktes.
    longitude: str
        Längengrad des Wegpunktes.
    last_updated: str
        Zuletzt bearbeitet.
    img_path: str
        default: ./data/res/example_landscape.jpg
        Der Pfad des Bildes, das oben auf der Karte angezeigt wird.
    """

    image_path = StringProperty()
    name = StringProperty()
    altitude = StringProperty()
    latitude = StringProperty()
    longitude = StringProperty()
    last_updated = StringProperty()

    def __init__(self, img='', name='', altitude='', latitude='', longitude='', last_updated='', **kwargs):
        self.image_path = img
        self.name = name
        self.altitude = altitude
        self.latitude = latitude
        self.longitude = longitude
        self.last_updated = last_updated

        self.menu_items = []
        self.buttons = [
            ('Edit', 'pencil-outline', self.edit_waypoint),
            ('Delete', 'delete-outline', self.delete_waypoint),
        ]

        # Event, die aufgerufen werden, sobald auf den zugehörigen Knopf gedrückt wurde.
        # Durch Events können auch Funktionen außerhalb dieser Klasse aufgerufen werden.
        # Besonders da diese Klasse jedes mal als Parameter übergeben wird
        self.on_edit_btn_clicked = EventHandler()
        self.on_delete_btn_clicked = EventHandler()

        super(WaypointCard, self).__init__(**kwargs)

    def on_kv_post(self, base_widget):
        """
        Wird aufgerufen sobald, alle Regeln auf den Widgets angewendet wurde.
        Bezieht sich natürlich nur auf diese Klasse.

        Parameters:
        -----------
        base_widget: Widget
            Das Widget, was ganz oben in der Hierarchie steht.
            Man muss es sich wie ein Wurzelwerk vorstellen.
        """

        self.menu_items = [
            {
                "text": button[0],
                "left_icon": button[1],
                "viewclass": "MenuListItem",
                "height": dp(54),
                "on_release": lambda x=i: self.menu_item_selected(x),

            } for i, button in enumerate(self.buttons)
        ]

        self.ids.drop_down.menu = MDDropdownMenu(
            caller=self.ids.drop_down,
            items=self.menu_items,
            width_mult=3
        )

    def open_menu(self, *args):
        self.ids.drop_down.menu.open()

    def menu_item_selected(self, index):
        """
        Wird aufgerufen, sobald eine Option ausgewählt wird.

        Parameters
        ---------
        index: int
            Der Index des Items, das ausgewählt wurde.
        """

        self.buttons[index][2]()
        self.ids.drop_down.menu.dismiss()

    def edit_waypoint(self):
        self.on_edit_btn_clicked.invoke(self)

    def delete_waypoint(self):
        self.on_delete_btn_clicked.invoke(self)


class LoadDialog(MDFloatLayout):
    """
    Das Fenster das geöffnet wird, sobald ein Bild auf der Festplatte hochgeladen werden soll.
    (Waypoints)
    """
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)


class WaypointArea(MDAnchorLayout):
    """
    Diese Klasse unterscheidet sich von den WaypointCard und ist auch KEINE Subklasse von
    WaypointCard.

    WaypointCard: Die Karten aufgelistet werden.
    WaypointArea: Der Bereich, der angezeigt wird, sobald ein Wegpunkt bearbeitet oder ein neuer
                    erschaffen wird.

    Attributes
    ----------
    title: str
        Titel, der ganz oben angezeigt wird.
    """

    title = StringProperty()

    def __init__(self, **kwargs):
        self.on_save_btn_clicked = EventHandler()
        self.on_discard_btn_clicked = EventHandler()

        self._popup = None
        super(WaypointArea, self).__init__(**kwargs)

    def show_bottom_sheet(self) -> None:
        if os_on_device in ['android', 'linux']:
            from android.storage import app_storage_path
            _bottom_sheet_menu = MDGridBottomSheet()
            data = [
                ("System folder", "folder-cog-outline", "."),
                ("Gallery folder", "folder-image", os.path.join(app_storage_path, 'DCIM'))
            ]
            for name, icon, path in data:
                _bottom_sheet_menu.add_item(
                    name,
                    lambda path=path: self.sheet_item_selected(path),
                    icon_src=icon,
                )
            _bottom_sheet_menu.open()
        else:
            self.open_manager('.')

    def sheet_item_selected(self, path) -> None:
        self.open_manager(path)

    def open_manager(self, init_path) -> None:
        """
        Öffnet das Fenster/die Dialogbox, der dann alle Dateien auf den Gerät auflistet.
        """
        if os_on_device in ['android', 'linux']:
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])
        content = LoadDialog(load=self.load, cancel=self.dismiss_manager)
        content.path = init_path
        self._popup = Popup(title="Load file", content=content,
                            size_hint=(0.9, 0.9))
        self._popup.open()

    def dismiss_manager(self) -> None:
        """
        Schließt das Fenster/die Dialogbox wieder.
        """

        self._popup.dismiss()

    def load(self, path, filename):
        """
        Lädt die Datei. Die Datei muss ein .jpg oder .png Datei sein.
        """
        if len(filename) == 0:
            CustomSnackbar(
                text=MDApp.get_running_app().translate('No file selected!'),
                icon='information',
                snackbar_x='10dp',
                snackbar_y='10dp',
                size_hint_x=.5
            ).open()
            self.dismiss_popup()
        else:
            filename = filename[0]
            suffix = filename.split('.')[-1]
            if suffix == 'jpg' or suffix == 'png':
                self.ids.image.source = filename
                self.dismiss_popup()
            else:
                CustomSnackbar(
                    text=MDApp.get_running_app().translate('File has to a .jgp or .png file!'),
                    icon='information',
                    snackbar_x='10dp',
                    snackbar_y='10dp',
                    size_hint_x=.5
                ).open()


class MenuListItem(OneLineAvatarIconListItem):
    """
    Diese Klasse stellt die Vorlage für die einzelnen Optionen des Menüs da.

    Attributes
    ----------
    left_icon: str
        Icon, der links vom Text angezeigt wird.
    """

    left_icon = StringProperty()


class MenuDropDown(MDBoxLayout):
    """
    Das Menü.
    """

    def __init__(self, **kwargs):
        self.menu = None
        super(MenuDropDown, self).__init__(**kwargs)

    def on_touch_down(self, touch):
        """
        siehe line. 1147
        """

        print(type(touch))
        # Berührt es auch dieses Objekt?
        if self.collide_point(*touch.pos):
            self.menu.open()


class NumericTextInput(MDTextField):
    """
    Klasse für die Implementierung eines Textfeldes, was nur numerische Eingaben akzeptiert.

    Attributes
    ----------
    positive_values: bool
        Gibt an, ob positive Zahlen angenommen werden sollen.
    negative_values: bool
        Gibt an, ob negative Zahlen angenommen werden sollen.
    number_range: range -> (upper, lower)
        Gibt die Grenzen an, in der sich die Zahl befinden darf.
        Sind beide Grenzen auf 0 gesetzt, wird keine Grenze gesetzt.
    input_filter: str
        default: float
        Ein von Kivy implementierter Filter, der dafür sorgt, dass nur Zahlen angenommen werden.
    filter_type: str
        default: float
        Gibt an ob, nur ganze Zahlen oder auch Fließkommazahlen angegeben werden können-
    """

    positive_values = BooleanProperty(True)
    negative_values = BooleanProperty(False)

    number_range = BoundedNumericProperty([0, 0])

    filter_type = StringProperty('float')

    def __init__(self, **kwargs) -> None:
        """
        Erstellt alle nötigen Variablen für die Klasse.

        Parameters
        ---------
        kwargs: any
            Durch die Zwei sterne vor dem Namen kann man eine undefinierte Anzahl von Parameter
            übergeben werden. kw kann also beliebig viele Parameter mit variablen Namen darstellen.
        """

        super(NumericTextInput, self).__init__(**kwargs)
        self.input_filter = self.filter_type

    def on_kv_post(self, base_widget) -> None:
        """
        siehe line. 193

        Soll sicherstellen, dass am Anfang falls kein Standardtext festgesetzt wurde,
        eine '0' statt eine leere Zeichenkette im Eingabefeld steht
        """

        if self.text == '':
            self.text = '0'
        super(NumericTextInput, self).on_kv_post(base_widget)

    def insert_text(self, substring: str, from_undo: bool = False) -> None:
        """
        Wird aufgerufen, sobald ein Text eingesetzt werden soll. Also sprich beim Einfügen oder beim
        Eintippen. Diese Methode verwenden wird um die Eingabe zu manipulieren.
        Entspricht die Zahl nicht der Anforderungen, wird sie zu 0 oder
        zur niedrigsten Zahl zurückgesetzt.

        Parameters
        ----------
        substring: str
            Die Zeichenkette, die eingeführt werden soll.
        from_undo: bool
            Soll die Zeichenkette vom zuletzt veränderten Text stammen?
        """

        super(NumericTextInput, self).insert_text(substring)

        current_number = float(self.text)

        # Ist die Zahl negativ ?
        if not self.negative_values and current_number < 0:
            self.text = '0'
            return
        # Ist die Zahl positiv ?
        if not self.positive_values and current_number > 0:
            self.text = '0'
            return

        # Ist die Zahl im Intervall ?
        lower, upper = self.number_range
        if upper and lower is not None:
            if current_number < lower or current_number > upper:
                self.text = str(lower)
                return


class AppSettings(MDBoxLayout):
    """
    Klasse für die Implementierung der App-Einstellungen.
    Das Grundlayout wird dabei als BoxLayout angesehen. Sprich wenn man AppSettings als
    Widget hinzufügt, wird es als BoxLayout behandelt.
    """

    swipe_distance_field = ObjectProperty()

    def __init__(self, **kwargs):
        self.languages_full = [entry for entry in os.listdir('./locales') if os.path.isdir('./locales/' + entry)]
        self._last_index = 0
        super(AppSettings, self).__init__(**kwargs)

    def on_kv_post(self, base_widget) -> None:
        """
        siehe line. 193

        Soll sicherstellen, dass am Anfang die aktuellsten Werte aus der Konfiguration-Datei
        abgelesen werden und die Textfelder und Knöpfe dementsprechende Texte bzw Werte annehmen.
        """

        self.add_settings()
        super(AppSettings, self).on_kv_post(base_widget)

    def add_settings(self) -> None:
        """
        Fügt die Optionen für die Einstellungen hinzu und übersetzt diese direkt.
        """

        app = MDApp.get_running_app()
        app_config = app.configuration.config_dict['app']

        menu_items = [
            {
                "text": language.split('_')[0],
                "left_icon": f'./data/res/{language.split("_")[0]}_flag.png',
                "viewclass": "MenuListItem",
                "height": dp(54),
                "on_release": lambda x=i: self.menu_item_selected(x),

            } for i, language in enumerate(self.languages_full)
        ]

        self.ids.language_drop_down.menu = MDDropdownMenu(
            caller=self.ids.caller_btn,
            items=menu_items,
            width_mult=3
        )

        self.ids.caller_btn.source = f'./data/res/{app_config["current_language"]}_flag.png'
        self.ids.caller_label.text = app_config["current_language"]

        self.swipe_distance_field.text = str(app_config['swipe_distance'])

    def has_changed(self) -> bool:
        """
        Vergleicht die Werte nach den Betreten und vor dem Verlassen der Einstellungen und
        gibt das Ergebnis im Form eines Boolean zurück.

        Returns
        -------
        <nameless>: bool
            True, hat sich verändert.
            False, hat sich nicht verändert.
        """

        app = MDApp.get_running_app()
        app_config = app.configuration.config_dict['app']

        current_distance_in_field = self.swipe_distance_field.text
        current_distance_in_con = str(app_config['swipe_distance'])
        if current_distance_in_field != current_distance_in_con:
            return True

        current_lang_in_field = self.ids.caller_label.text
        current_lang_in_con = app_config['current_language']
        if current_lang_in_field != current_lang_in_con:
            return True
        return False

    def menu_item_selected(self, index):
        """
        Wird aufgerufen, sobald eine Option angeclickt wird.

        Parameters
        ---------
        index: int
            Der Index des Items, das angeclickt wurde.
        """

        language = self.languages_full[index].split('_')[0]
        self.ids.language_drop_down.children[0].text = language
        self.ids.language_drop_down.children[1].source = f'./data/res/{language.split("_")[0]}_flag.png'

        self._last_index = index
        self.ids.language_drop_down.menu.dismiss()

    def save_config(self, *args) -> None:
        """
        Speicher die Einstellungen und aktualisiere die Daten beispielsweise,
        die Hintergrundfarbe oder die Sprache.
        """

        config = MDApp.get_running_app().configuration
        app_config = config.config_dict['app']

        language = self.languages_full[self._last_index].split('_')[0]
        app_config['current_language'] = language

        app_config['swipe_distance'] = float(self.ids.swipe_distance_text_input.text)

        config.save_config()

        # Aktualisiere die Texte in den Spinner Widgets
        self.add_settings()

        # Aktualisiere alle Texte in der App
        # MDApp.get_running_app().set_translation()
        MDApp.get_running_app().update_text()


class BouncingPoints(Widget):
    """
    Eine Klasse für die Animation der springenden Punkte.

    Attributes
    ----------
    points_size: [int, int]
        Die Grö0e der Punkte.
    spacing_x: int
        Der Abstand der Punkte auf der X-Achse zueinander
    spacing_y: int
        Der Abstand der Punkte auf der Y-Achse zueinander
    points: []
        Die Punkte.
    anim: Animation
        Die Animation.
    number: int
        Anzahl der Punkte.
    proceed: bool
        Soll die Animation fortgesetzt werden?
    """

    def __init__(self, **kwargs):
        self.points_size = [20, 20]

        self.spacing_x = 30
        self.spacing_y = 0

        self.points = []
        self.anim = None

        self.number = 4

        self.proceed = False
        self._index = 0
        super(BouncingPoints, self).__init__(**kwargs)

    def draw(self) -> None:
        """
        Zeichne die Punkte auf einem Canvas.
        """

        with self.canvas:
            for i in range(self.number):
                adjusted_y = self.y + self.height / 2 + i * self.spacing_y - \
                            (self.number / 2 * self.spacing_y + self.points_size[1]) + self.spacing_y / 2
                adjusted_x = self.x + self.width / 2 + i * self.spacing_x - \
                             (self.number / 2 * self.spacing_x + self.points_size[0]) + self.spacing_x / 2
                c = Color(rgba=get_random_color(1))
                e = Ellipse(pos=(adjusted_x + 10, adjusted_y), size=(self.points_size[0], self.points_size[1]))
                self.points.append(e)

    def start_animation(self, draw_points) -> None:
        """
        Zeichne die Punkte und starte die Animation.
        """

        if draw_points:
            self.draw()
        self.proceed = True
        self.run_animation()

    def on_animation_finished(self, *args):
        """
        Wird aufgerufen sobald die Animation abgeschlossen ist und startet direkt eine
        nächsten Durchlauf, sodass ein Schleife entsteht.
        """

        if self._index < len(self.points) - 1:
            self._index += 1
        else:
            self._index = 0

        self.run_animation()

    def run_animation(self) -> None:
        """
        Hier werden die Animationen erstellt und in die Dauerschleife eingebaut.
        """

        if self.proceed:
            current_pos = self.points[self._index].pos
            self.anim = Animation(pos=(current_pos[0], current_pos[1] + 30), duration=1)
            self.anim += Animation(pos=(current_pos[0], current_pos[1]), duration=1)
            self.anim.bind(on_complete=self.on_animation_finished)
            self.anim.start(self.points[self._index])

    def stop_animation(self) -> None:
        """
        Stoppt die Schleife, aber nicht abrupt, sodass der momentane Durchlauf zu Ende geführt wird.
        """

        self.proceed = False


class LoadingAnimation(RelativeLayout):
    """
    Die Ladeanimation.
    Beinhaltet die Animationen der springenden Punkte(BouncingPoint)
    und die Animation mit der Lupe.

    Attributes
    ----------
    points_size: [int, int]
        Die Größe der Punkte.
    glass_anim: Animation
        Die Animation für die Lupe.
    proceed: bool
        Soll die Animation fortgesetzt werden?.
    """

    def __init__(self, **kwargs):
        self.points_size = [20, 20]

        self.glass_anim = None
        self.proceed = False
        super(LoadingAnimation, self).__init__(**kwargs)

    def on_kv_post(self, base_widget) -> None:
        """
        siehe line. 193
        """

        self.ids.bouncing_p.points_size = self.points_size

    def start_animation(self, draw_points) -> None:
        """
        Starte die Lupen und Punkt-Animation
        """

        self.proceed = True
        self.run_glass_animation()
        self.ids.bouncing_p.start_animation(draw_points)

    def stop_animation(self):
        """
        Stoppt die Schleife, aber nicht abrupt, sodass der momentane Durchlauf zu Ende geführt wird.
        """

        self.proceed = False
        self.ids.bouncing_p.stop_animation()
        self.glass_anim.stop(self.ids.glass_img)

    def run_glass_animation(self, *args):
        """
        Hier werden die Animationen erstellt und in die Dauerschleife eingebaut.
        """

        if self.proceed:
            server_img = self.ids.server_img
            random_x = uniform(server_img.pos_hint['center_x'] - .05, server_img.pos_hint['center_x'] + .05)
            random_y = uniform(server_img.pos_hint['center_y'] - .1, server_img.pos_hint['center_y'] + .1)
            self.glass_anim = Animation(pos_hint={'center_x': random_x, 'center_y': random_y}, duration=1)
            self.glass_anim.bind(on_complete=self.run_glass_animation)
            self.glass_anim.start(self.ids.glass_img)


# *******************************************************************

# ******************************* Base ******************************


class CustomScreen(MDScreen):
    """
    Eigene Implementierung der Screen Klasse und die Basisklasse für die Bildschirme

    Parameters
    ----------
    configuration: Configuration
        Das Objekt der Konfiguration der App
    machine_config: dict
        Der Maschinenabschnitt der Konfiguration.
        Wird diese Variable geändert, ändert sich auch das Dictionary, in der App-Klasse
    app_config: dict:
        Die Appabschnitt der Konfiguration.
        Wird diese Variable geändert, ändert sich auch das Dictionary, in der App-Klasse
    """

    def __init__(self, **kw) -> None:
        """
        Erstellt alle nötigen Variablen für die Klasse.

        Parameters
        ---------
        kw: Any
            Durch die Zwei sterne vor dem Namen kann man eine undefinierte Anzahl von Parameter
            übergeben werden. kw kann also beliebig viele Parameter mit variablen Namen darstellen.
        """

        MDApp.get_running_app().configuration.on_config_changed.add_function(self.on_config_changed)

        # Abschnitte der Konfiguration werde in Variablen gespeichert, damit man nicht immer
        # App.get_running_app().configuration.config_dict aufrufen muss
        self.configuration = MDApp.get_running_app().configuration
        self.machine_config = self.configuration.config_dict['machine']
        self.app_config = self.configuration.config_dict['app']
        self.icon_text = {}

        self.drawer_items = {}

        super(CustomScreen, self).__init__(**kw)

    def go_back(self, screen_name) -> None:
        """
        Wechselt den Bildschirm mit einem anderen Übergang.
        Normalerweise ist der Übergang ein Linkswisch, aber bei diesen
        Übergang handelt es sich um einem Rechtswisch.
        """

        self.manager.transition.direction = 'right'
        self.manager.current = screen_name

    def on_enter(self, *args) -> None:
        """
        Wird aufgerufen, sobald dieser Bildschirm aufgerufen wird. Da es sich jedoch um eine
        Basisklasse handelt, wird diese Funktion auch aufgerufen wenn einer der Erbbildschirmen
        aufgerufen wird.
        Diese Signatur wird von Kivy vorgegeben.

        Parameters
        ----------
        args: any
            Durch den einen Stern vor dem Namen können beliebig viele positionelle Argumente
            angenommen werden.
        """

        self.manager.transition.direction = 'left'
        Clock.schedule_once(self.load_drawer, 0)

    def on_leave(self, *args) -> None:
        """
        Wird aufgerufen, sobald dieser Bildschirm verlassen wird. Da es sich jedoch um eine
        Basisklasse handelt, wird diese Funktion auch aufgerufen wenn einer der Erbbildschirmen
        aufgerufen wird.
        Diese Signatur wird von Kivy vorgegeben.

        Parameters
        ----------
        args: any
            Durch den einen Stern vor dem Namen können beliebig viele positionelle Argumente
            angenommen werden.
        """

        # Zerstört die Navigationsleiste
        self.destroy_drawer()

    def on_config_changed(self) -> None:
        """
        Wird aufgerufen, sobald die Konfiguration durch die configuration_save_config Funktion gespeichert
        wird. Das gilt jedoch nur für die das Konfigurationsobjekt, in der DroneApp-Klasse.
        """

        # Überschreibe die Konfiguration in dieser Klasse mit der in der DroneApp-Klasse
        self.configuration = MDApp.get_running_app().configuration

        self.machine_config = self.configuration.config_dict['machine']
        self.app_config = self.configuration.config_dict['app']

    def load_drawer(self, dt) -> None:
        """
        Erstellt die Navigationsleiste vor dem Betreten des Bildschirmes.
        Dabei verwenden wir das Dictionary 'text_icon'.
        Diese Dictionary beinhaltet:
            - Den Text der angezeigt wird.
            - Das Icon was rechts davon angezeigt wird.
            - Der Name des Bildschirmes zu dem gewechselt wird.

        Die Struktur muss dabei gleich bleiben.
        """

        for screen_name, value in self.icon_text.items():
            item = MDNavigationDrawerItem(icon=value['icon'],
                                          text=value['text'],
                                          bg_color=get_color_from_hex("#f7f4e7"),
                                          on_release=self.switch_screen)
            MDApp.get_running_app().root_widget.nav_drawer_list.add_widget(item)
            self.drawer_items[screen_name] = item

    @staticmethod
    def destroy_drawer(*args):
        drawer_list = MDApp.get_running_app().root_widget.nav_drawer_list.children[0]

        items = [item for item in drawer_list.children
                 if isinstance(item, MDNavigationDrawerItem)]

        for item in items:
            drawer_list.remove_widget(item)

    def switch_screen(self, *args) -> None:
        """
        Sobald ein Knopf der Navigationsleiste gedrückt wird, wechselt man durch diese
        Methode zu diesen Bildschirm.
        """

        keys = list(self.drawer_items.keys())
        values = list(self.drawer_items.values())

        drawer_item = args[0]
        if drawer_item in values:
            index = values.index(args[0])
            MDApp.get_running_app().root_widget.hide_nav_drawer()

            self.manager.current = keys[index]


class MyScreenManager(ScreenManager):
    """
    Eine eigene Implementierung der ScreenManager Klasse.
    Sie soll vor allem eine Möglichkeit der Gruppierung implementieren, die bei dem
    Menübildschirmen verwendet wird.

    Attributes
    ----------
    screen_groups: dict
        Dient zur Gruppierung von Bildschirmen, wobei der Name als Schlüssel und eine Liste mit dem
        Bildschirmnamen als Wert verwendet wird.
    """

    def __init__(self, **kwargs):
        """
        Erstellt alle nötigen Variablen für die Klasse.
        Diese Signatur wird von Kivy vorgegeben.

        Parameters
        ----------
        kwargs: any
            Durch die Zwei sterne vor dem Namen kann man eine undefinierte Anzahl von Parameter
            übergeben werden. kw kann also beliebig viele Parameter mit variablen Namen darstellen.
        """

        self.screen_groups = {
            'settings': ['settings', 'waypoints']
        }
        super(MyScreenManager, self).__init__(**kwargs)

    def go_next_screen_of_group(self, group_name: str) -> None:
        """
        Durch diese Funktion kann man zum nächsten Bildschirm wechseln, ohne den Namen
        des Bildschirmes zu kennen. Diese Funktion ist besonders bei der Wischfunktion
        der Menübildschirme wichtig.
        Hier wird zudem wieder eine anderen Überganganimation verwendet (Linkswisch)

        Parameters
        ----------
        group_name: str
            Der Name der Gruppe.

        Raises
        ------
        ValueError:
            Passiert, wenn die Gruppe nicht existiert oder wenn sich der derzeitige Bildschirm
            nicht in der angegebenen Gruppe befindet.
        """

        # Existiert die Gruppe ?
        if group_name in self.screen_groups:
            group = self.screen_groups[group_name]
            # Befindet sich derzeitige Bildschirm in der Gruppe?
            if self.current in group:
                index = group.index(self.current)
                if index == len(group) - 1:
                    index = 0
                else:
                    index += 1
                self.transition.direction = 'left'
                self.current = group[index]

            else:
                raise ValueError(f'The current screen {self.current} has to be one of{group}')
        else:
            raise ValueError(f'screen manager cant find the group, {group_name}')

    def go_previous_screen_of_group(self, group_name: str) -> None:
        """
        Durch diese Funktion kann man zum letzten Bildschirm wechseln, ohne den Namen
        des Bildschirmes zu kennen. Diese Funktion ist besonders bei der Wischfunktion
        der Menübildschirme wichtig.
        Hier wird zudem wieder eine anderen Überganganimation verwendet (Rechtsswisch).

        Parameters
        ----------
        group_name: str
            Der Name der Gruppe.

        Raises
        ------
        ValueError:
            Passiert, wenn die Gruppe nicht existiert oder wenn sich der derzeitige Bildschirm
            nicht in der angegebenen Gruppe befindet.
        """

        # Existiert die Gruppe ?
        if group_name in self.screen_groups:
            group = self.screen_groups[group_name]

            # Befindet sich derzeitige Bildschirm in der Gruppe?
            if self.current in group:
                index = group.index(self.current)
                if index == 0:
                    index = len(group) - 1
                else:
                    index -= 1
                self.transition.direction = 'right'
                self.current = group[index]
            else:
                raise ValueError(f'The current screen {self.current} has to be one of{group}')
        else:
            raise ValueError(f'screen manager cant find the group, {group_name}')

    def go_to_screen_of_group(self, group_name: str, index, transition_direction='right'):
        """
        Durch diese Funktion kann man zu einem beliebigen Bildschirm in einer beliebigen Gruppe
        wechseln.

        Parameters
        ----------
        group_name: str
            Der Name der Gruppe.
        index: int
            Der Index des Bildschirm wohin gewechselt werden soll.
        transition_direction: str
            default: right(recht)
            Die Richtung der Wisch-Animation
        """

        # Existiert die Gruppe
        if group_name in self.screen_groups:
            group = self.screen_groups[group_name]
            self.transition.direction = transition_direction
            self.current = group[index]


# *******************************************************************

# *************************** Bildschirme ***************************

class StartScreen(CustomScreen):
    """
    Der Startbildschirm

    Attributes
    ----------
    fonts: list
        Beinhaltet die Pfade aller Schriftarten, die bei der Animation des Titeltextes
        verwendet werden.
    texts: list
        Beinhaltet alle Texte für den Titeltext.
    """

    def __init__(self, **kw):
        """
        Erstellt alle nötigen Variablen für die Klasse.
        Diese Signatur wird von Kivy vorgegeben.

        Parameters
        ----------
        kwargs: any
            Durch die Zwei sterne vor dem Namen kann man eine undefinierte Anzahl von Parameter
            übergeben werden. kw kann also beliebig viele Parameter mit variablen Namen darstellen.
        """
        print(os_on_device)
        # map lässt alle Element in der Liste durch eine Funktion laufen.
        # os.listdir gibt uns nur die Dateinamen aus
        # Damit wird die Schriftarten mit den HTML Tags verwenden können, brauchen wir die relativen Pfade zum
        # Projektverzeichnis. Aus diesen Grund werden alle Dateinamen mit den Verzeichnis Namen kombiniert.
        self.fonts = list(map(lambda x: f'{FONTS_DIRECTORY}/{x}', os.listdir(FONTS_DIRECTORY)))
        self.texts = ['Welcome', 'Willkommen']

        super(StartScreen, self).__init__(**kw)

    def on_enter(self, *args) -> None:
        """
        siehe line 746.
        """

        print(f'{self.width} x {self.height}')
        Clock.schedule_interval(self.change_font, 2)
        super(StartScreen, self).on_enter(*args)

    def on_leave(self, *args) -> None:
        """
        siehe line. 757
        """

        Clock.unschedule(self.change_font)
        super(StartScreen, self).on_leave(*args)

    def load_drawer(self, dt) -> None:
        """
        siehe line. 780
        """

        self.icon_text = {
            'home': {
                'text': DroneApp.translate('Home'),
                'icon': 'home-outline'
            },
            'connection': {
                'text': DroneApp.translate('Connect'),
                'icon': 'database-search-outline'
            },
            'appSettings': {
                'text': DroneApp.translate('Settings'),
                'icon': 'cog-outline'
            },
            'waypoints': {
                'text': DroneApp.translate('Waypoints'),
                'icon': 'map-outline'
            },
            'support': {
                'text': DroneApp.translate('Support'),
                'icon': 'help-circle-outline'
            }
        }
        super(StartScreen, self).load_drawer(dt)

    def change_font(self, dt) -> None:
        """
        Wird von einem Thread in bestimmten Intervall takten ausgeführt.

        Diese Funktion wählt zufällig eine Schriftart und ein Text aus und verändert dementsprechend
        den Titelbildschirm.

        Parameters
        ----------
        dt: float
            Die ZEit die zwischen Aufruf der Clock.schedule-Funktion und dieser
        """

        text = MarkupLabel(self.ids.title.text).markup[1]
        current_font_index = self.fonts.index(self.ids.title.font_family)
        current_text_index = self.texts.index(text)

        while True:
            font_index = randrange(0, len(self.fonts))
            text_index = randrange(0, len(self.texts))
            if font_index != current_font_index and text_index != current_text_index:
                break

        self.ids.title.text = f'[font={self.fonts[font_index]}]{self.texts[text_index]}[/font]'


class AppSettingsScreen(CustomScreen):
    """
    Bildschirm mit den Einstellungen, die ohne Verbindung verändert werden können.
    """

    app_settings = ObjectProperty(None)

    def __init__(self, **kwargs):

        self._dialog = None
        self._touch_card = False
        super(AppSettingsScreen, self).__init__(**kwargs)

    def load_drawer(self, dt):
        """
        siehe line. 780
        """

        self.icon_text = {
            'home': {
                'text': DroneApp.translate('Home'),
                'icon': 'home-outline'
            },
            'connection': {
                'text': DroneApp.translate('Connect'),
                'icon': 'database-search-outline'
            },
            'settings': {
                'text': DroneApp.translate('Settings'),
                'icon': 'cog-outline'
            },
            'waypoints': {
                'text': 'map-outline',
                'icon': 'map-outline'
            },
            'support': {
                'text': DroneApp.translate('Support'),
                'icon': 'help-circle-outline'
            }
        }
        super(AppSettingsScreen, self).load_drawer(dt)

    def on_pre_leave(self, *args):
        """
        Wird aufgerufen, sobald der Benutzer den Bildschirm verlassen will. Der Unterschied zu
        on_leave ist der Zeitpunkt, an den die Funktionen aufgerufen werden.
        Diese Funktion wird aufgerufen bevor die Animation startet, während die on_leave-Funktion
        aufgerufen wird, sobald die Animation und der Wechsel abgeschlossen sind.
        Diese Signatur wird von Kivy vorgegeben.
        """

        # Haben sich die Einstellungen verändert?
        changed = self.app_settings.has_changed()
        if changed:
            # Weist den Benutzer darauf hin, dass die Änderungen nicht gespeichert wurden.
            self._dialog = MDDialog(
                text="Discard draft?",
                buttons=[
                    MDFlatButton(
                        text="CANCEL",
                        theme_text_color="Custom",
                        on_release=self.cancel_leave
                    ),
                    MDFlatButton(
                        text="DISCARD",
                        theme_text_color="Custom",
                        on_release=self.confirm_leave
                    ),
                ]
            )
            self._dialog.open()
        super(AppSettingsScreen, self).on_pre_enter(*args)

    def on_touch_down(self, touch):
        """
        Wird aufgerufen sobald der Benutzer das Display berührt.

        Parameters
        ----------
        touch: MouseMotionEvent
            Enthält alle Informationen über die Berührung wie z.B die Position
        """

        # Wurde der graue Bereich berührt?
        if self.app_settings.ids.touch_card.collide_point(*touch.pos):
            self._touch_card = True
        super(AppSettingsScreen, self).on_touch_down(touch)

    def on_touch_up(self, touch):
        """
        Wird aufgerufen sobald der Benutzer aufhört das Display zu berühren.

        Parameters
        ---------
        touch: MouseMotionEvent
            Enthält alle Informationen über die letzte Berührung wie z.B die Position.
        """

        # Wurde der graue Bereich am Anfang und am Ende berührt?
        if self._touch_card and self.app_settings.ids.touch_card.collide_point(*touch.pos):
            # Berechne die Distanz, wobei wir nur die absolute und gerundete Zahl nehmen
            rounded_distance = round(touch.ox - touch.pos[0])
            self.app_settings.swipe_distance_field.text = str(abs(rounded_distance))
            self._touch_card = False
        super(AppSettingsScreen, self).on_touch_up(touch)

    def cancel_leave(self, button):
        self._dialog.dismiss()
        self.manager.current = 'appSettings'

    def confirm_leave(self, button):
        self._dialog.dismiss()

    def save_config(self):
        self.app_settings.save_config()
        self.configuration.save_config()

    def discard_config(self, button):
        self.app_settings.add_settings()


class SupportScreen(CustomScreen):
    """
    Der Bildschirm soll die FAQs in Form von ausklappbaren Boxen anzeigen.
    """

    def __init__(self, **kwargs):
        self.questions = ['Connection lost?', 'Cant find your problem here?']
        self.answers = ['Restart the app.', 'Send an e-mail to fake_email@gmail.com']

        super(SupportScreen, self).__init__(**kwargs)

    def on_enter(self, *args) -> None:
        """
        siehe line 746.
        """

        toolbar = MDApp.get_running_app().root_widget.toolbar
        toolbar.title = DroneApp.translate('Support')
        super(SupportScreen, self).on_enter(*args)

    def on_kv_post(self, base_widget):
        """
        siehe line. 193
        Fügt die Widgets dynamisch hinzu, indem wir die Listen nehmen und dadurch iterieren.
        """

        for i in range(len(self.questions)):
            self.ids.box.add_widget(
                MDExpansionPanel(
                    content=SupportExpansionContent(
                        text=self.answers[i]
                    ),
                    panel_cls=MDExpansionPanelOneLine(
                        text=self.questions[i]
                    )
                )
            )

    def load_drawer(self, dt):
        """
        siehe line. 780
        """

        # Einige Bereiche sind erst betretbar, sobald man sich einmal verbunden hat
        # Aus diesen Grund müssen zwei Versionen von Navigationsleisten erstellt werden
        if MDApp.get_running_app().connected:
            self.icon_text = {
                'home': {
                    'text': DroneApp.translate('Home'),
                    'icon': 'home-outline'
                },
                'connection': {
                    'text': DroneApp.translate('Connect'),
                    'icon': 'database-search-outline'
                },
                'control': {
                    'text': DroneApp.translate('Control'),
                    'icon': 'controller-classic-outline'
                },
                'settings': {
                    'text': DroneApp.translate('Settings'),
                    'icon': 'cog-outline'
                },
                'waypoints': {
                    'text': DroneApp.translate('Waypoints'),
                    'icon': 'map-outline'
                },
                'support': {
                    'text': DroneApp.translate('Support'),
                    'icon': 'help-circle-outline'
                }
            }
        else:
            self.icon_text = {
                'home': {
                    'text': DroneApp.translate('Home'),
                    'icon': 'home-outline'
                },
                'connection': {
                    'text': DroneApp.translate('Connect'),
                    'icon': 'database-search-outline'
                },
                'appSettings': {
                    'text': DroneApp.translate('Settings'),
                    'icon': 'cog-outline'
                },
                'waypoints': {
                    'text': DroneApp.translate('Waypoints'),
                    'icon': 'map-outline'
                },
                'support': {
                    'text': DroneApp.translate('Support'),
                    'icon': 'help-circle-outline'
                }
            }
        super(SupportScreen, self).load_drawer(dt)


class ConnectionScreen(CustomScreen):
    """
    Verbindungsbildschirm.
    In diesen Bildschirm wird eine Verbindung zur Drohne aufgebaut.

    Zuvor muss die Drohne angeschaltet sein, damit sie sich dann mithilfe einer internen Liste gefüllt
    mit Netzwerknamen und Passwörter ins Netzwerk einklingt.
    Dann wird ein Server erstellt, mit dem dann über Sockets kommuniziert werden kann.

    Wer verwenden zwei Threads.
    Der register_thread, versucht über einen Befehl, die IP-Adresse des Gerätes zu registrieren und
    der receive_thread wartet dann auf eine Antwort.
    Wenn diese Antwort positiv also eine 1 enthält, wird man zum Kontrollbildschirm weitergeleitet.
    """

    def __init__(self, **kw):
        super(ConnectionScreen, self).__init__(**kw)

        self.waiting_text = DroneApp.translate('Waiting for response')

        self.max_steps = 4
        self._current_step = 0

        self._waiting_anim_thread = DisposableLoopThread()
        self._waiting_anim_thread.add_function(self.wait_anim)

        self._register_thread = DisposableLoopThread()
        self._register_thread.add_function(self.register_ip)

        self._receive_thread = DisposableLoopThread()
        self._receive_thread.add_function(self.receive_response)

        self._draw_points = True

    def on_kv_post(self, base_widget) -> None:
        """
        siehe line. 193
        """

        self.status.text = self.waiting_text

    def on_enter(self, *args) -> None:
        """
        siehe line 746.
        """

        toolbar = MDApp.get_running_app().root_widget.toolbar
        toolbar.title = DroneApp.translate('Connection')

        self.ids.loading_anim.start_animation(self._draw_points)
        self._waiting_anim_thread.save_start()
        self._register_thread.save_start()
        self._draw_points = False
        super(ConnectionScreen, self).on_enter(*args)

    def on_leave(self, *args) -> None:
        """
        siehe line. 757
        """

        self.ids.loading_anim.stop_animation()
        self._waiting_anim_thread.stop()
        self._register_thread.stop()
        self._receive_thread.stop()
        super(ConnectionScreen, self).on_leave(*args)

    def load_drawer(self, dt):
        """
        siehe line. 780
        """

        self.icon_text = {
            'home': {
                'text': DroneApp.translate('Home'),
                'icon': 'home-outline'
            },
            'connection': {
                'text': DroneApp.translate('Connect'),
                'icon': 'database-search-outline'
            },
            'settings': {
                'text': DroneApp.translate('Settings'),
                'icon': 'cog-outline'
            },
            'waypoints': {
                'text': DroneApp.translate('Waypoints'),
                'icon': 'map-outline'
            },
            'support': {
                'text': DroneApp.translate('Support'),
                'icon': 'help-circle-outline'
            }
        }
        super(ConnectionScreen, self).load_drawer(dt)

    def wait_anim(self) -> None:
        """
        Sorgt für eine Art Animation mit den Text, indem einfach periodisch Punkte hinzugefüt werden.
        """

        self._current_step += 1
        if self._current_step == self.max_steps:
            self.status.text = self.waiting_text
            self._current_step = 0
        else:
            self.status.text += '.'

    def register_ip(self) -> None:
        """
        Sendet den Befehl 'register_ip' zu den Microcontroller, der dieses Gerät registriert und
        damit die nächste Phase beginnen kann und der Benutzer die Drohne steuern kann.
        """

        if self.app_config['testcase']:
            sleep(3)
            self.manager.current = 'control'
            return

        sent_request = False
        # Alle Stellen an den eine Nachricht über die Sockets gesendet wird, sollte durch ein
        # Try und Catch-Block abgedeckt sein, da besonders hier viele Exception passieren können, die nicht
        # code bedingt sind.
        try:
            ip, port = get_server_address()
            wlan_client.connect(ip, port)

            wlan_client.send_message(0, f'CMD|register_ip')
            sent_request = True
        except Exception as e:
            print(e)

        if sent_request:
            self._register_thread.stop()
            self._receive_thread.save_start()

    def receive_response(self) -> None:
        """
        Nachdem der Befehl übermittel wurde, wartet die App/Client auf eine Bestätigung.
        """

        try:
            response = wlan_client.wait_for_response(0, flag='REGISTER')

            response_split = response.split(SEPARATOR)
            if response_split[1] == '1':
                self.manager.current = 'control'
            elif response_split[1] == '0':
                self.status.text = DroneApp.translate('Connection to drone failed. Please try again')
            self._receive_thread.stop()
        except Exception as e:
            print(e)


class ControlScreen(CustomScreen):
    """
    Bedingungsbildschirm.
    Das ist der eigentliche Hauptbildschirm, in der die Drohne gesteuert werden kann.

    Attributes
    ----------
    altitude: str (Property)
        Enthält Daten zu der Höhe.
    speed: str (Property)
        Enthält Daten zur Geschwindigkeit.
    latitude: str (Property)
        Enthält Daten zu den Längengrad.
    longitude: str (Property)
        Enthält Daten zu den Breitengrad.
    -> Bis hier werden alle Daten vom ESP32 übermittelt.
    battery: str (Property)
        Enthält Daten zu den momentanen Akkustand.

    status: str (Property)
        Gibt den momentanen Status an.


    _send_thread: DisposableLoopThread
        Ein Thread, der im Hintergrund Daten an den  Mikrocontroller sendet.
    _data_thread: DisposableLoopThread
        Ein Thread, der im Hintergrund die Sensordaten empfängt, die über den Mikrocontroller gesendet werden
        die über den Mikrocontroller gesendet werden und diese verarbeitet.
    _connection_thread: DisposableLoopThread
        Ein Thread, der im Hintergrund die Verbindungsstärke empfängt,
         die über den Mikrocontroller gesendet werden und diese verarbeitet.

    r_joystick: Joystick
        Rechter Joystick
    l_joystick: Joystick
        Linker Joystick

    _created: bool
        Wurden die Joystick schon erstellt?
    _hover_mode: bool
        befindet sich die Drohne im hover_mode?
        Hover_mode ist ein Modus in dem die Drohne ohne zusätzliche Daten von dem Client auf der selben H
        Höhe bliebt. Wird verwendet wenn der Client z.B in den Einstellungen ist.
    """

    altitude = StringProperty('H: 0')
    speed = StringProperty('S: 0')

    latitude = StringProperty('La: 0')
    longitude = StringProperty('Lo: 0')
    esp_connection = StringProperty('strong')
    esp_connection_icon = StringProperty('')

    battery = StringProperty('100')

    def __init__(self, **kwargs):
        """
        Erstellt alle nötigen Variablen für die Klasse und startet die Threads
        Diese Signatur wird von Kivy vorgegeben.

        Parameters
        ----------
        kwargs: any
            Durch die Zwei sterne vor dem Namen kann man eine undefinierte Anzahl von Parameter
            übergeben werden. kw kann also beliebig viele Parameter mit variablen Namen darstellen.
        """

        self.r_joystick = JoyStick()
        self.l_joystick = JoyStick()

        self.esp_connection = DroneApp.translate('strong')

        self._data_thread = DisposableLoopThread()
        self._send_thread = DisposableLoopThread()
        self._connection_thread = DisposableLoopThread()

        self._send_thread.add_function(self.send_data)
        self._send_thread.interval_sec = CON_INTERVAL

        self._data_thread.add_function(self.check_data)
        self._data_thread.interval_sec = CON_INTERVAL

        self._connection_thread.add_function(self.check_connection)
        self._connection_thread.interval_sec = CON_INTERVAL

        self._created = False
        self._hover_mode = False

        self.control_screens = ['control', 'settings', 'support', 'waypoints']

        super(ControlScreen, self).__init__(**kwargs)

    def on_enter(self, *args) -> None:
        """
        siehe line 746.
        """

        # Starte die Threads
        if not self.app_config['testcase']:
            self.toggle_hover_mode(value=False)

            ip, port = get_server_address()

            wlan_client.connect(ip, port)
            wlan_client.connect(ip, port)
            wlan_client.connect(ip, port)

            # 1. socket: Daten senden
            # 2. socket: Sensordaten abfragen
            # 3: socket: Verbindungsdaten abfragen

            self._data_thread.save_start()
            self._connection_thread.save_start()
            self._send_thread.save_start()

        MDApp.get_running_app().connected = True

        # Lass die Anzeige oben verschwinden
        toolbar = MDApp.get_running_app().root_widget.toolbar
        set_visible(toolbar, False)

        # Erstelle die erste Nachricht in der Konsole
        self.log_message(DroneApp.translate('Ready to take off'))
        self.esp_connection_icon = CON_ICON[100]

        # Wurden die Joysticks schon erstellt?
        if not self._created:
            self.ids.joystick_a.add_widget(self.r_joystick)
            self.ids.joystick_a.add_widget(self.l_joystick)

            Clock.schedule_once(self.r_joystick.set_center, 0.01)
            Clock.schedule_once(self.l_joystick.set_center, 0.01)
            self._created = True

        super(ControlScreen, self).on_enter(*args)

    def on_leave(self, *args) -> None:
        """
        siehe line. 757
        """

        # Beende die Threads
        if not self.app_config['testcase']:
            self._data_thread.stop()
            self._send_thread.stop()
            self._connection_thread.stop()
            # Ist der Benutzer z.B in den Einstellungen, soll die Drohne auf gleicher Höhe bleiben
            if self.manager.current in self.control_screens[2:]:
                self.toggle_hover_mode(value=True)

        if self.manager.current not in self.control_screens:
            self.shutdown()

        # Lass die Anzeige oben wieder erscheinen
        toolbar = MDApp.get_running_app().root_widget.toolbar
        set_visible(toolbar, True)

        super(ControlScreen, self).on_leave(*args)

    def load_drawer(self, dt):
        """
        siehe line. 780
        """

        self.icon_text = {
            'home': {
                'text': DroneApp.translate('Home'),
                'icon': 'home-outline'
            },
            'settings': {
                'text': DroneApp.translate('Settings'),
                'icon': 'cog-outline'
            },
            'control': {
                'text': DroneApp.translate('Control'),
                'icon': 'controller-classic-outline'
            },
            'waypoints': {
                'text': DroneApp.translate('Waypoints'),
                'icon': 'map-outline'
            },
            'support': {
                'text': DroneApp.translate('Support'),
                'icon': 'help-circle-outline'
            }
        }
        super(ControlScreen, self).load_drawer(dt)

    def set_waypoint(self) -> None:
        """
        Diese Funktion dient dazu ein Wegpunkt zu setzen.
        Es wird also ein neuer Wegpunkt erstellt und in der Konfiguration gespeichert.
        """

        waypoints = self.app_config['waypoints']
        names = [waypoint['name'] for waypoint in waypoints]
        # Erstelle dynamisch den Namen des Wegpunkts, ohne dass sie sich doppeln

        name = get_waypoint_name(names)

        # Erstelle den Wegpunkt mithilfe der momentanen Sensordaten
        new_waypoint = {
            'img': './data/res/example_landscape.jpg',
            'name': name,
            "date": datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
            "altitude": self.altitude.split(':')[1].split()[0],
            "longitude": self.longitude.split(':')[1].split()[0],
            "latitude": self.latitude.split(':')[1].split()[0]
        }

        # Speicher den Wegpunkt in der Konfigurationsdatei
        self.app_config['waypoints'].append(new_waypoint)
        self.configuration.save_config()

        self.log_message(DroneApp.translate('Waypoint') + ': ' + name + ' ' + DroneApp.translate('set'))

    def send_data(self) -> None:
        """
        Wird von dem _send_thread aufgerufen.
        In dieser Funktion werden die relativen Positionen der inneren, beweglichen Kreise zu den
        äußeren Kreise ermittelt und zum ESP32 gesendet.
        """

        r_relative_pos = self.r_joystick.get_center_pt()
        l_relative_pos = self.l_joystick.get_center_pt()

        if not self.app_config['testcase']:
            # Format: RJ|POS_X|POS_Y
            message = f'RJ{SEPARATOR}{r_relative_pos[0]}{SEPARATOR}{r_relative_pos[1]}'
            wlan_client.send_message(1, message)
            # Format: LJ|POS_X|POS_Y
            message = f'LJ{SEPARATOR}{l_relative_pos[0]}{SEPARATOR}{l_relative_pos[1]}'
            wlan_client.send_message(1, message)

    def check_data(self) -> None:
        """
        Wird von dem _data_thread aufgerufen.
        In dieser Funktion werden die Daten vom ESP32 empfangen, aufbereitet und in den
        zugehörigen Variablen gespeichert.
        """

        wlan_client.send_message(2, f'CMD{SEPARATOR}get_sensor_data')

        # Format GEODATA|SPEED|ALTITUDE|LATITUDE|LONGITUDE
        response = wlan_client.wait_for_response(2, flag='GEODATA')
        response_split = response.split(SEPARATOR)

        self.speed = f'S: {response_split[1]}'
        self.altitude = f'H: {response_split[2]}'
        self.latitude = f'La: {response_split[3]}'
        self.longitude = f'Lo: {response_split[4]}'

    def check_connection(self) -> None:
        """
        Wird von dem _connection_thread aufgerufen.
        In dieser Funktion werden die Verbindungsdaten vom ESP32 empfangen, aufbereitet und in den
        zugehörigen Variablen gespeichert. Ist die Verbindung zu schwach wird eine Warnung im
        Terminal ausgegeben.
        """

        esp_con = self.check_esp_connection()
        own_con = self.check_own_connection()
        print(CON_ICON[esp_con[0]])
        self.esp_connection_icon = CON_ICON[esp_con[0]]
        status_keys = list(CON_STATUS.keys())
        if esp_con[1] == status_keys[0]:
            self.log_message(DroneApp.translate('WARNING: WEAK CONNECTION(ESP32)'), 'warning')
        if own_con[1] == status_keys[0]:
            self.log_message(DroneApp.translate('WARNING: WEAK CONNECTION'), 'warning')

        self.esp_connection = DroneApp.translate(esp_con[1])

    def check_esp_connection(self) -> (int, str):
        """
        Sendet den get_conn_data Befehl, der dafür sorgt dass der Server die
        Verbindungsstärke zurücksendet.
        """

        wlan_client.send_message(3, f'CMD{SEPARATOR}get_conn_data')
        response = wlan_client.wait_for_response(3, flag='CONDATA')

        data = response.split(SEPARATOR)
        return self.get_connectivity(data[1])

    def check_own_connection(self) -> (int, str):
        """
        Prüft die eigene Verbindungsstärke zum Netzwerk

        Returns
        -------
        <nameless>: tuple(int, str)
            Die höchste Grenze und die Bezeichnung dafür.
            Wir unterteilen die Stärken in Intervallen mit Grenzen,
            wobei 100 die höchste ist.
        """

        return self.get_connectivity('100')

    def toggle_hover_mode(self, value=None) -> None:
        """
        Aktiviert oder deaktiviert den Hover-mode, wobei zum einen die Funktion und das Icon
        an den jeweiligen Zustand angepasst wird.
        Damit der Modus geändert wird, wird der set_hover_mode Befehl an den Mikrocontroller gesendet.
        """

        if value is None:
            self._hover_mode = not self._hover_mode
        elif isinstance(value, bool):
            self._hover_mode = value
        if self._hover_mode:
            self.ids.hover_mode_btn.icon = 'butterfly-outline'
            self.log_message('Hover mode activated', 'information')
        else:
            self.ids.hover_mode_btn.icon = 'butterfly'
            self.log_message('Hover mode deactivated', 'information')
        if not self.app_config['testcase']:
            wlan_client.send_message(0, f'CMD{SEPARATOR}set_hover_mode{SEPARATOR}{self._hover_mode}')

    def shutdown(self) -> None:
        """
        Der Benutzer gelangt zum Startverbindung.
        Dabei wird der ESP32 und die Clients zurückgesetzt (Verbindung wird gekappt).
        """

        if not self.app_config['testcase']:
            wlan_client.send_message(0, f'CMD{SEPARATOR}reset')
        wlan_client.reset()

        self._send_thread.stop()
        self._data_thread.stop()

        MDApp.get_running_app().connected = False
        self.go_back('home')

    def log_message(self, message, log_level='info') -> None:
        """
        Gibt eine Nachricht in den Terminal aus, wobei ein Zeitstempel hinzugefügt wird
        und die Schriftart und Größe geändert wird.
        """

        timestamp = datetime.now().strftime("%H:%M:%S")
        terminal_log = f'[{timestamp}] [{log_level}] {message}'

        label = MDLabel(text=terminal_log)
        label.font_name = './data/customfonts/Consolas'
        label.adaptive_height = True
        label.font_size = 10
        label.color = [.5, .5, .5, 1]

        self.ids.terminal.add_widget(label)

    @staticmethod
    def get_connectivity(value: str) -> (int, str):
        """
        Ermittelt anhand des Wertes, die Grenze und die dazugehörige Beschreibung.

        Returns
        -------
        <nameless>: tuple(int, str)
            Die höchste Grenze und die Bezeichnung dafür.
            Wir unterteilen die Stärken in Intervallen mit Grenzen,
            wobei 100 die höchste ist.
        """

        if not str(value).isdigit():
            raise ValueError('value has to be an integer')

        i = 0
        value = int(value)
        result = CON_STATUS[10]

        for i, (border, status) in enumerate(CON_STATUS.items()):
            if value < border:
                break

            result = status
        border_value = list(CON_STATUS.keys())[i]
        return border_value, result


class SettingsScreen(CustomScreen):
    """
    Bildschirm mit den Einstellungen, die mit Verbindung verändert werden können.
    """

    app_settings = ObjectProperty(None)

    def __init__(self, **kw):
        self._touch_card = True
        super(SettingsScreen, self).__init__(**kw)

    def on_enter(self, *args) -> None:
        """
        siehe line 746.
        """

        toolbar = MDApp.get_running_app().root_widget.toolbar
        toolbar.title = DroneApp.translate('Settings')

        super(SettingsScreen, self).on_enter(*args)

    def on_touch_down(self, touch):
        """
        siehe line. 1147
        """

        # Wurde der graue Bereich berührt?
        if self.app_settings.ids.touch_card.collide_point(*touch.pos):
            self._touch_card = True
        super(SettingsScreen, self).on_touch_down(touch)

    def on_touch_up(self, touch):
        """
        siehe line. 1160

        """
        # Wurde der graue Bereich am Anfang und am Ende berührt?
        if self._touch_card and self.app_settings.ids.touch_card.collide_point(*touch.pos):
            # Berechne die Distanz, wobei wir nur die absolute und gerundete Zahl nehmen
            rounded_distance = round(touch.ox - touch.pos[0])
            self.app_settings.swipe_distance_field.text = str(abs(rounded_distance))
            self._touch_card = False
        super(SettingsScreen, self).on_touch_up(touch)

    def load_drawer(self, dt):
        """
        siehe line. 780
        """

        self.icon_text = {
            'home': {
                'text': DroneApp.translate('Home'),
                'icon': 'home-outline'
            },
            'connection': {
                'text': DroneApp.translate('Connect'),
                'icon': 'database-search-outline'
            },
            'settings': {
                'text': DroneApp.translate('Settings'),
                'icon': 'cog-outline'
            },
            'control': {
                'text': DroneApp.translate('Control'),
                'icon': 'controller-classic-outline'
            },
            'waypoints': {
                'text': DroneApp.translate('Waypoints'),
                'icon': 'map-outline'
            },
            'support': {
                'text': DroneApp.translate('Support'),
                'icon': 'help-circle-outline'
            }
        }
        super(SettingsScreen, self).load_drawer(dt)

    def save_config(self) -> None:
        """
        Wird aufgerufen, der Speicher-knopf gedrückt wird.
        In dieser Funktion werden die Einstellungen gespeichert.
        """

        self.app_settings.save_config()
        self.configuration.save_config()
        # self.notify()

        self.manager.get_screen('control').log_message(DroneApp.translate('Settings saved'), 'information')
        self.go_back('control')

    def notify(self) -> None:
        """
        In dieser Funktion wird der ESP32 mithilfe eines Command benachrichtigt,
        der dann die übergebene Konfigurationsdatei nimmt und sich abspeichert.
        """

        if not self.app_config['testcase']:
            json_string = self.config_obj.get_json_string_from_dict(self.machine_config)
            wlan_client.send_message(0, f'CMD{SEPARATOR}set_config{SEPARATOR}{json_string}')


class WaypointsScreen(CustomScreen):
    """
    Wegpunktbildschirm.
    In diesen Bildschirm werden alle Wegpunkte angezeigt,
    die dann bearbeitet, gelöscht werden können.
    """

    def __init__(self, **kwargs):
        self.waypoints = []

        self._waypoint_cards = []

        self._current_edited_index = None
        self._clear_waypoints_dialog = None

        self._toolbar = None
        super(WaypointsScreen, self).__init__(**kwargs)

    def on_kv_post(self, base_widget):
        """
        siehe line. 193
        Nimmt noch letzte Änderungen an den WaypointsAreas-Objekte vor. Das ist erst hier möglich da vieles
        auf diese Instanz zugreifen, wie z.B die Events. Zudem werden die Bereiche am Anfang unsichtbar gemacht.
        """

        self.ids.edit_waypoint_area.title = DroneApp.translate('Edit waypoint')
        self.ids.edit_waypoint_area.on_save_btn_clicked.add_function(lambda area: self.save_waypoint(area, 'edit'))
        self.ids.edit_waypoint_area.on_discard_btn_clicked.add_function(self.discard_waypoint)

        self.ids.add_waypoint_area.title = DroneApp.translate('Add new waypoint')
        self.ids.add_waypoint_area.on_save_btn_clicked.add_function(lambda area: self.save_waypoint(area, 'add'))
        self.ids.add_waypoint_area.on_discard_btn_clicked.add_function(self.discard_waypoint)

        set_visible(self.ids.edit_waypoint_area, False)
        set_visible(self.ids.add_waypoint_area, False)

    def on_enter(self, *args) -> None:
        """
        siehe line 746.
        """

        self._toolbar = MDApp.get_running_app().root_widget.toolbar
        self._toolbar.right_action_items = [
            ['plus', self.add_waypoint],
            ['delete-alert-outline', self.delete_waypoints]
        ]
        self._toolbar.title = DroneApp.translate('Waypoints')

        # Breite des Grids bestimmen
        for i in range(6):
            cols = i
            grid_width = i * (160 + 30)
            if grid_width > self.width:
                self.ids.grid.cols = cols - 1
                break

        self.load_grid(None, load_all=True)
        super(WaypointsScreen, self).on_enter(*args)

    def on_pre_leave(self, *args):
        """
        siehe line. 1422
        Entfernt die Knöpfe in der Kopfzeile
        """

        self._toolbar.right_action_items = []
        self.clear_grid()

        super(WaypointsScreen, self).on_pre_leave(*args)

    def load_drawer(self, dt):
        """
        siehe line. 780
        """

        # Einige Bereiche sind erst betretbar, sobald man sich einmal verbunden hat
        # Aus diesen Grund müssen zwei Versionen von Navigationsleisten erstellt werden
        if MDApp.get_running_app().connected:
            self.icon_text = {
                'home': {
                    'text': DroneApp.translate('Home'),
                    'icon': 'home-outline'
                },
                'connection': {
                    'text': DroneApp.translate('Connect'),
                    'icon': 'database-search-outline'
                },
                'control': {
                    'text': DroneApp.translate('Control'),
                    'icon': 'controller-classic-outline'
                },
                'settings': {
                    'text': DroneApp.translate('Settings'),
                    'icon': 'cog-outline'
                },
                'waypoints': {
                    'text': DroneApp.translate('Waypoints'),
                    'icon': 'map-outline'
                },
                'support': {
                    'text': DroneApp.translate('Support'),
                    'icon': 'help-circle-outline'
                }
            }
        else:
            self.icon_text = {
                'home': {
                    'text': DroneApp.translate('Home'),
                    'icon': 'home-outline'
                },
                'connection': {
                    'text': DroneApp.translate('Connect'),
                    'icon': 'database-search-outline'
                },
                'appSettings': {
                    'text': DroneApp.translate('Settings'),
                    'icon': 'cog-outline'
                },
                'waypoints': {
                    'text': DroneApp.translate('Waypoints'),
                    'icon': 'map-outline'
                },
                'support': {
                    'text': DroneApp.translate('Support'),
                    'icon': 'help-circle-outline'
                }
            }
        super(WaypointsScreen, self).load_drawer(dt)

    def load_grid(self, waypoints, load_all=False) -> None:
        """
        Lädt das grid, indem er die Widgets konstruiert und sie zu dem Layout hinzufügt.
        """

        if load_all:
            content = self.app_config['waypoints'].copy()
        else:
            content = waypoints
        for waypoint in content:
            card = self.build_card(waypoint)
            self._waypoint_cards.append(card)
            self.ids.grid.add_widget(card)

    def clear_grid(self) -> None:
        """
        Leert alle Listen, sowohl die interne als auch die visuelle Liste/Grid.
        """

        self.ids.grid.clear_widgets()
        self.waypoints.clear()
        self._waypoint_cards.clear()

    def edit_waypoint(self, waypoint_card) -> None:
        """
        Bearbeitet ein Wegpunkt, indem ein Fenster erscheint. Dort können alle Daten geändert werden und
        diese Änderungen abgespeichert werden.
        Davor müssen die Textfelder und die Bilder mit den Daten des Wegpunktes synchronisiert werden.

        Parameters
        ----------
        waypoint_card: WaypointCard
            Die Karte, dessen Knopf zum Bearbeiten gedrückt wurde. Diese Karte beinhaltet
            zudem die Daten des Wegpunktes.
        """

        edit_area = self.ids.edit_waypoint_area
        index = self._waypoint_cards.index(waypoint_card)

        card = self._waypoint_cards[index]
        self._current_edited_index = index

        edit_area.ids.image.source = card.ids.image.source
        edit_area.ids.name_field.text = card.ids.name_label.text
        edit_area.ids.altitude_field.text = card.ids.altitude_label.text
        edit_area.ids.latitude_field.text = card.ids.latitude_label.text
        edit_area.ids.longitude_field.text = card.ids.longitude_label.text

        # Lass das Fenster erscheinen
        set_visible(edit_area, True)

    def save_waypoint(self, area, mode) -> None:
        """
        Speichert die Änderungen.
        Das gilt sowohl für das Bearbeiten des Wegpunktes, als auch
        das Hinzufügen eines neuen.

        Parameters
        ----------
        area: WaypointArea
            Das Fenster
        mode: str
            Den Modus, sprich ob es sich um Hinzufügen oder Bearbeiten handelt.
        """

        if mode != 'edit' and mode != 'add':
            raise ValueError('mode must be add or edit.')

        name = area.ids.name_field.text
        names = [waypoint['name'] for waypoint in self.waypoints]
        if mode == 'edit':
            old_name = self._waypoint_cards[self._current_edited_index].ids.name_label.text
        else:
            old_name = ''

        if name == '':
            CustomSnackbar(
                text=MDApp.get_running_app().translate('Name can´t be empty!'),
                icon='information',
                snackbar_x='10dp',
                snackbar_y='10dp',
                size_hint_x=.5
            ).open()
        elif name in names and name != old_name:
            CustomSnackbar(
                text=MDApp.get_running_app().translate('Name already exists'),
                icon='information',
                snackbar_x='10dp',
                snackbar_y='10dp',
                size_hint_x=.5
            ).open()
        else:
            waypoint = {
                'img': area.ids.image.source,
                'name': area.ids.name_field.text,
                'altitude': area.ids.altitude_field.text,
                'latitude': area.ids.latitude_field.text,
                'longitude': area.ids.longitude_field.text,
                'date': datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
            }

            if mode == 'edit':
                self.apply_edit_changes(waypoint)
            else:
                self.apply_add_changes(waypoint)
            CustomSnackbar(
                text=MDApp.get_running_app().translate('Changes applied!'),
                icon='information',
                snackbar_x='10dp',
                snackbar_y='10dp',
                size_hint_x=.5
            ).open()
            set_visible(area, False)

    def delete_waypoint(self, waypoint_card) -> None:
        """
        Löscht ein Wegpunkt und die Karte in der graphischen Liste (Gitter/Grid).

        Parameters
        ----------
        waypoint_card: WaypointCard
            Die Karte, dessen Knopf zum Bearbeiten gedrückt wurde. Diese Karte beinhaltet
            zudem die Daten des Wegpunktes.
        """

        index = self._waypoint_cards.index(waypoint_card)

        self.waypoints.pop(index)
        self._waypoint_cards.pop(index)
        self.ids.grid.remove_widget(waypoint_card)

        self.app_config['waypoints'].pop(index)
        self.configuration.save_config()

        CustomSnackbar(
            text=MDApp.get_running_app().translate('Waypoint deleted!'),
            icon='information',
            snackbar_x='10dp',
            snackbar_y='10dp',
            size_hint_x=.5
        ).open()

    def add_waypoint(self, button):
        """
        Lässt den Benutzer ein neues Wegpunkt hinzufügen, indem ein Fenster mit Textfeldern und Bildern
        geöffnet wird. Der Benutzer kann dann die Daten verändern und anschließen abspeichern.
        Die Textfelder und Bilder müssen mit den Standardwerten zuvor gefüllt werden.

        Parameters
        ----------
        button: Button
            Der Knopf der gedrückt wurde, damit diese Funktion ausgeführt wird.
        """

        add_area = self.ids.add_waypoint_area

        names = [waypoint['name'] for waypoint in self.waypoints]
        add_area.ids.name_field.text = get_waypoint_name(names)
        add_area.ids.altitude_field.text = '0'
        add_area.ids.latitude_field.text = '0'
        add_area.ids.longitude_field.text = '0'

        set_visible(add_area, True)

    def apply_edit_changes(self, waypoint) -> None:
        """
        Wendet die Änderungen an, die beim Bearbeiten entstehen , indem...
        ...der Wegpunkt in der Liste überschrieben wird
        ...die alte Wegpunktkarte gelöscht und durch eine neue ersetzt wird

        Parameters
        ----------
        waypoint: dict
            Der neue Wegpunkt in Form eines Dictionary.
        """

        self.waypoints[self._current_edited_index] = waypoint
        self.app_config['waypoints'][self._current_edited_index] = waypoint
        self.configuration.save_config()

        self.ids.grid.remove_widget(self._waypoint_cards[self._current_edited_index])

        card = self.build_card(waypoint)
        self._waypoint_cards[self._current_edited_index] = card
        self.ids.grid.add_widget(card, (len(self.waypoints) - 1) - self._current_edited_index)

        self._current_edited_index = -1

    def apply_add_changes(self, waypoint) -> None:
        """
        Wendet die Änderungen an, die beim Hinzufügen entstehen , indem...
        ...der Wegpunkt an die Liste angehängt wird
        ...eine neue Karte konstruiert wird und in an die graphische Liste (Gitter/Grid) angehängt wird

        Parameters
        ----------
        waypoint: dict
            Der neue Wegpunkt in Form eines Dictionary.
        """
        self.waypoints.append(waypoint)
        self.app_config['waypoints'].append(waypoint)
        self.configuration.save_config()

        self.load_grid([waypoint])

    def accept_clear(self, button) -> None:
        """
        Bestätigt man das Löschen aller Wegpunkte, wird diese Funktion ausgeführt,
        die alle Wegpunkte in der graphischen Liste, in der internen Liste und
        in der Konfiguration löscht.

        Parameters
        ----------
        button: Button
            Der Knopf der gedrückt wurde, damit diese Funktion ausgeführt wird.
        """
        if len(self.app_config['waypoints']) == 0:
            CustomSnackbar(
                text=MDApp.get_running_app().translate('List is already empty!'),
                icon='information',
                snackbar_x='10dp',
                snackbar_y='10dp',
                size_hint_x=.5
            ).open()
        else:
            self.app_config['waypoints'].clear()
            self.configuration.save_config()

            self.clear_grid()
            self._clear_waypoints_dialog.dismiss()

            CustomSnackbar(
                text=MDApp.get_running_app().translate('Waypoints deleted!'),
                icon='information',
                snackbar_x='10dp',
                snackbar_y='10dp',
                size_hint_x=.5
            ).open()

    def cancel_clear(self, button) -> None:
        """
        Möchte man doch nicht alle Wegpunkte löschen, wird diese Funktion ausgeführt,
        die den Dialog schließt.

        Parameters
        ----------
        button: Button
           Der Knopf der gedrückt wurde, damit diese Funktion ausgeführt wird.
        """

        self._clear_waypoints_dialog.dismiss()

    def delete_waypoints(self, button) -> None:
        """
        Möchte man alle Wegpunkte löschen, erscheint ein Dialog/Fenster als Bestätigung,
        der ein Text und zwei Knöpfe beinhaltet.

        Parameters
        ----------
        button: Button
            Der Knopf der gedrückt wurde, damit diese Funktion ausgeführt wird.
        """

        self._clear_waypoints_dialog = MDDialog(
            text=MDApp.get_running_app().bind_text(self, 'Do u really want to delete all entries?'),
            buttons=[
                MDFlatButton(
                    text=MDApp.get_running_app().bind_text(self, 'Yes'),
                    theme_text_color="Custom",
                    text_color=MDApp.get_running_app().theme_cls.primary_color,
                    on_release=self.accept_clear
                ),
                MDFlatButton(
                    text=MDApp.get_running_app().bind_text(self, 'No'),
                    theme_text_color="Custom",
                    text_color=MDApp.get_running_app().theme_cls.primary_color,
                    on_release=self.cancel_clear
                )
            ]
        )
        self._clear_waypoints_dialog.open()

    def build_card(self, waypoint) -> WaypointCard:
        card = WaypointCard(waypoint['img'],
                            waypoint['name'], waypoint['altitude'], waypoint['latitude'],
                            waypoint['longitude'], waypoint['date'])
        card.on_edit_btn_clicked.add_function(self.edit_waypoint)
        card.on_delete_btn_clicked.add_function(self.delete_waypoint)
        card.size_hint = None, None
        card.size = 160, 220
        return card

    @staticmethod
    def discard_waypoint(area) -> None:
        """
        Verwirft die Änderungen. Wird sowohl beim Bearbeiten, als auch beim Hinzufügen
        eines Wegpunktes verwendet.

        Parameters
        ----------
        area: WaypointArea
            Das Fenster zum Bearbeiten oder Hinzufügen.
        """

        # Lass das Fenster wieder unsichtbar werden.
        set_visible(area, False)

# *******************************************************************

# *************************** Einstiegspunkt ************************


class DroneRoot(MDScreen):
    """
    Das 'Root-Widget' der App, der ganz oben in der Hierarchie steht und auf
    den alles hinführt.

    Man muss sich den Aufbau wie ein Wurzelwerk eines Baumes vorstellen.
    Jedes Widget hat Eltern- und Tochterwidget/-s.

    Die hier definierten Widgets werden durch jeden Bildschirm verwendet.

    Attributes
    ----------
    nav_drawer: MDNavigationDrawer
        Die Navigationsleiste an der Seite.
    nav_drawer_list: MDNavigationDrawerMenu
        Der eigentliche Inhalt der Navigationsleiste mit den Knöpfen und Texten.
    toolbar: MDToolbar
        Die Leisten ganz oben.
    """

    nav_drawer = ObjectProperty()
    nav_drawer_list = ObjectProperty()

    toolbar = ObjectProperty()

    def on_kv_post(self, base_widget):
        """
        siehe line. 193
        Fügt ein Knopf zur Kopfleiste hinzu und öndert den Titel.
        """

        self.toolbar.left_action_items = [
            ['menu', self.show_nav_drawer, '']
        ]
        self.toolbar.title = DroneApp.translate('Home')

        super(DroneRoot, self).on_kv_post(base_widget)

    def show_nav_drawer(self, *args) -> None:
        """
        Öffnet die Navigationsleiste an der Seite.
        """

        self.nav_drawer.set_state('open')

    def hide_nav_drawer(self, *args) -> None:
        """
        Schließt die Navigationsleiste an der Seite.
        """

        self.nav_drawer.set_state('close')


class DroneApp(MDApp):
    """
    Die App.
    """

    def __init__(self, **kwargs) -> None:
        self.configuration = Configuration('./data/config.json', True)
        self.configuration.on_config_changed.add_function(self.on_config_changed)

        self.translated_labels = []
        self.translated_parts = []

        self.translation = None
        self.root_widget = None

        self.connected = False

        super(DroneApp, self).__init__(**kwargs)

    def on_config_changed(self) -> None:
        """
        Wird ausgeführt sobald die save_config-Funktion aufgerufen wird, egal von welcher Klasse.
        """

        self.configuration.load_config()

    def bind_text(self, label, text, entire_text=None) -> str:
        """
        Registriert den Label. Durch die update_text Funktion kann dann der Text aktualisiert werden.
        Das wird vor allem wichtig, wenn die Sprache geändert wurde una alle Texte in der App
        übersetzt werden müssen.

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

        self.translated_labels.append(label)
        translated_text = self.translation.gettext(text)

        if entire_text is None:
            entire_text = text

        self.translated_parts.append(translated_text)
        return entire_text.replace(text, translated_text)

    def update_text(self) -> None:
        """
        Aktualisiert die registrierten Labels und übersetzt alle Texte nochmal.
        """

        for index, label in enumerate(self.translated_labels):
            translated_text = self.translation.gettext(self.translated_parts[index])
            label.text = label.text.replace(self.translated_parts[index], translated_text)
            self.translated_parts[index] = translated_text

    def set_translation(self) -> None:
        language = self.configuration.config_dict['app']['current_language'] + '_' + \
                   self.configuration.config_dict['app']['current_language'].upper()
        self.translation = gettext.translation('base', localedir='locales',
                                               languages=[language])
        self.translation.install()

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
        return app.translation.gettext(message)

    def build(self):
        """
        Diese Funktion baut die App und ist die Ausgangsfunktion.
        """
        #from kivy.core.window import Window
        #Window.size = (900, 400)
        if os_on_device in ['android', 'linux']:
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])

        self.set_translation()
        self.load_kv_files()
        self.root_widget = DroneRoot()
        return self.root_widget

    def on_stop(self) -> None:
        """
        Wird aufgerufen wenn die App gestoppt wird bzw geschlossen wird.
        """

        self.cut_connection()

    def on_pause(self) -> bool:
        """
        Wird aufgerufen wenn die App pausiert wird.

        Returns
        -------
        <nameless>: bool
            True: App pausieren
            False: App sofort stoppen/schließen
        """

        if not self.configuration.config_dict['testcase']:
            wlan_client.send_message(0, f'CMD{SEPARATOR}set_hover_mode{SEPARATOR}True')

        Clock.schedule_once(self.cut_connection(), 10)
        return True

    def on_resume(self) -> None:
        """
        Wird aufgerufen wenn die App fortgesetzt wird.
        """

        Clock.unschedule(self.cut_connection())

        if not self.configuration.config_dict['testcase']:
            wlan_client.send_message(0, f'CMD{SEPARATOR}set_hover_mode{SEPARATOR}False')

    def cut_connection(self) -> None:
        if not self.configuration.config_dict['testcase']:
            wlan_client.send_message(0, f'CMD{SEPARATOR}reset')

    @staticmethod
    def load_kv_files() -> None:
        """
        Lädt alle kv-Dateien, die sich in ./kv_files befinden.
        """

        files = os.listdir(KV_DIRECTORY)
        for file in files:
            path = KV_DIRECTORY + '/' + file
            Builder.load_file(path)


def set_visible(wid, visible) -> None:
    """
    Lässt ein Widget unsichtbar werden, indem Höhe, Durchsichtigkeit u.s.w
    verändert werden. Diese werten werden dann temporär gespeichert und anschließend
    sobald man dieses Objekt wieder sichtbar machen möchte gelöscht.

    Parameters
    ----------
    wid: Widget
        Das Objekt. Das Objekt muss dabei von der Widget-Klasse erben.
    visible: bool
        True: Sichtbar
        False: Unsichtbar
    """

    if hasattr(wid, 'saved_attrs'):
        if visible:
            wid.height, wid.size_hint_y, wid.opacity, wid.disabled = wid.saved_attrs
            del wid.saved_attrs
    elif not visible:
        wid.saved_attrs = wid.height, wid.size_hint_y, wid.opacity, wid.disabled
        wid.height, wid.size_hint_y, wid.opacity, wid.disabled = 0, None, 0, False


def get_waypoint_name(existing_names) -> str:
    """
    Generiert eine einzigartigen Zeichenkette und gibt diesen zurück.
    Parameters
    ----------
    existing_names: list
     Eine Liste mit verwendeten Zeichenketten

    Returns
    -------
    name: str
        Die generierte Zeichenketten.

    """
    name = DEFAULT_WP_PREFIX
    i = 0
    while name in existing_names:
        i += 1
        name = DEFAULT_WP_PREFIX + '(' + str(i) + ')'
    return name


def get_server_address() -> (str, int):
    """
    Gibt die IP-Adresse und den Port des Servers zurück, der gehardcoded wurde.

    Returns
    -------
    <nameless>: tuple(str, int)
        Die Adresse und den Port
    """

    return socket.gethostbyname('espressif.box'), 9192


# *******************************************************************


if __name__ == '__main__':
    DroneApp().run()
