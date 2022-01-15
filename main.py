# **************************** main.py ******************************
# Hauptklasse und Einstiegspunkt der ganzen Applikation
# *******************************************************************

# **************************** Imports ****************a**************
import os
os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'

import kivy
kivy.require('2.0.0')

from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput

from kivy.graphics import Color
from kivy.graphics import Line

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout

from kivy.uix.screenmanager import Screen, ScreenManager

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.core.text.markup import MarkupLabel
from kivy.properties import ObjectProperty, StringProperty, BooleanProperty, BoundedNumericProperty

from communication import client
from misc.custom_threads import DisposableLoopThread
from misc.configuration import Configuration
from customwidgets.joystick import *

from time import sleep
from random import randrange
from datetime import datetime

import platform
import gettext

# ******************************************************************

# ************************** Konstanten ****************************

NAME = 'mpy-uart'
SEPARATOR = '|'
DEFAULT_WP_PREFIX = 'new waypoint'

KV_DIRECTORY = './kv_files'
FONTS_DIRECTORY = './data/fonts'

LANGUAGE_DICTIONARY = {
    'en': 'English',
    'ge': 'German'
}

# ******************************************************************

# ********************* Plattformspezifisch ************************

platform = platform.uname()
os_on_device = platform.system

# Je nach Betriebssystem, werden andere Bibliotheken und
# Funktionen für die Bluetooth-Kommunikation verwendet
if 'Android' in os_on_device:
    bluetooth_client: client.AndroidBluetoothClient = client.AndroidBluetoothClient()
else:
    bluetooth_client: client.BluetoothClient = client.BluetoothClient()

wlan_client = client.WLANClient()


# *******************************************************************

# ********************** Eigene Kivy-widgets ************************


# Wir verwenden die von Kivy implementierte kv-Sprache
# Alle in der .kv-file verwendeten Klassen, müssen auch einer Pythonskript deklariert werden
class RoundedButton(Button):
    pass


class NumericTextInput(TextInput):
    """
    Klasse für die Implentierung eines Textfeldes, was nur numerische Eingaben akzeptiert.

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
    """

    positive_values = BooleanProperty(True)
    negative_values = BooleanProperty(False)

    number_range = BoundedNumericProperty([0, 0])

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
        self.input_filter = 'float'

    def on_kv_post(self, base_widget) -> None:
        """
        Wird aufgerufen, sobald die kv-Datei geladen wird und soll sicherstellen, dass
        am Anfang falls kein Standardtext festgesetzt wurde, eine '0' statt eine leere Zeichenkette
        im Eingabefeld steht
        """

        if self.text is '':
            self.text = '0'
        super(NumericTextInput, self).on_kv_post(base_widget)

    def insert_text(self, substring: str, from_undo: bool = False) -> None:
        """
        Wird aufgerufen, sobald ein Text eingsetzt werden soll. Also sprich beim Einfügen oder beim
        Eintippen. Diese Methode verwenden wird um die Eingabe zu manipulieren.

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
            return
        # Ist die Zahl positiv ?
        if not self.positive_values and current_number > 0:
            return

        # Ist die Zahl im Intervall ?
        lower, upper = self.number_range
        if upper and lower is not None:
            if current_number < lower or current_number > upper:
                return
        # Wenn Nein lösche die zuletzt eingegebene Zahl


class AppSettings(BoxLayout):
    """
    Klasse für die Implementierung der App-Einstellungen.
    Das Grundlayout wird dabei als BoxLayout angesehen. Sprich wenn man AppSettings als
    Widget hinzufügt, wird es als BoxLayout behandelt.

    Attributes
    ----------
    translated_languages: dict
        Die übersetzten Namen der Sprachen
    translated_theme_names: dict
        Die übersetzten Namen der Farbthemen
    current_test_mode: bool
        Dieser Wert ist wichtig für die Knöpfe in der Einstellung.
        Je nach Wert, wird der Status einer der beiden Knöpfe verändert.
        Am Anfang wird auch so ermittelt welcher der beiden Knöpfe schon gedrückt sein sollen.

    """

    translated_languages = {}
    translated_theme_names = {}

    current_test_mode = BooleanProperty()

    def on_kv_post(self, base_widget) -> None:
        """
        Wird aufgerufen, sobald die kv-Datei geladen wird und soll sicherstellen, dass
        am Anfang die aktuellsten Werte aus der Konfiguration-Datei abgelesen werden und die
        Textfelder und Knöpfe dementsprechende Texte bzw Werte annehmen.
        z.B Wenn die Sprache Deutsch ist, soll beim Textfeld für die Sprachen Deutsch
        am Anfang angezeigt werden.
        """

        app = App.get_running_app()
        app_config = app.configuration.config_dict['app']
        self.current_test_mode = app_config['testcase']

        self.add_settings()
        super(AppSettings, self).on_kv_post(base_widget)

    def add_settings(self) -> None:
        """
        Fügt die Optionen für die Einstellungen hinzu und übersetzt diese direkt.
        """

        self.translated_theme_names.clear()
        self.translated_languages.clear()

        app = App.get_running_app()
        app_config = app.configuration.config_dict['app']

        # Stellt sicher, dass die derzeitige Sprache verwendet wird
        app.translation = gettext.translation('base', localedir='locales', languages=[app_config['current_language']])
        app.translation.install()

        # Lies die vordefinierten Farbthemen von der Konfiguration
        theme_names = list(app_config['themes'].keys())

        # Übersetzte die Namen und speichert diese ab
        for theme_name in theme_names:
            self.translated_theme_names[app.translation.gettext(theme_name)] = theme_name

        # Verwende nun die übersetzten Farbschemen für den Spinner
        self.ids.color_spinner.text = app.translation.gettext(app_config['current_theme'])
        self.ids.color_spinner.values = self.translated_theme_names.keys()

        # Übersetzte die Namen der Sprachen im Dict, damit wir später die Werte vergleichen
        # können und den Kürzel erhalten.
        # In der Konfiguration wird nämlich nur der Kürzel gespeichert.
        # Am Anfang sind sie auf Englisch und werden dann in die derzeitig verwendete Sprache übersetzt
        for (short, language) in LANGUAGE_DICTIONARY.items():
            self.translated_languages[short] = app.translation.gettext(language)

        # Verwende nun die übersetzten Farbschemen für den Spinner
        self.ids.language_spinner.text = self.translated_languages[app_config['current_language']]
        self.ids.language_spinner.values = self.translated_languages.values()

        self.ids.swipe_distance_text_input.text = str(app_config['swipe_distance'])

    def validate_config(self) -> bool:
        """
        Überprüft, ob die Werte gültig sind.
        """

        return True

    def save_config(self) -> None:
        """
        Speicher die Einstellungen und aktualisiere die Daten beispielsweise,
        die Hintergrundfarbe oder die Sprache.
        """

        # Speicher die Farbthema ab
        config = App.get_running_app().configuration
        app_config = config.config_dict['app']
        app_config['current_theme'] = self.translated_theme_names[self.ids.color_spinner.text]

        # Finde den Kürzel und speicher diesen ab
        for (short, language) in self.translated_languages.items():
            if self.ids.language_spinner.text == language:
                app_config['current_language'] = short

        app_config['testcase'] = self.current_test_mode
        app_config['swipe_distance'] = float(self.ids.swipe_distance_text_input.text)

        config.save_config()
        # Aktualisiere die Texte in den Spinner Widgets
        self.add_settings()

        # Aktualisiere alle Texte in der App
        App.get_running_app().update_text()


# *******************************************************************

# ******************************* Base ******************************


class CustomScreen(Screen):
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

        super(CustomScreen, self).__init__(**kw)
        App.get_running_app().configuration.on_config_changed.add_function(self.on_config_changed)

        # Abschnitte der Konfiguration werde in Variablen gespeichert, damit man nicht immer
        # App.get_running_app().configuration.config_dict aufrufen muss
        self.configuration = App.get_running_app().configuration
        self.machine_config = self.configuration.config_dict['machine']
        self.app_config = self.configuration.config_dict['app']

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
        """

        self.manager.transition.direction = 'left'

    def on_config_changed(self):
        """
        Wird aufgerufen, sobald die Konfiguration durch die configuration_save_config Funktion gespeichert
        wird. Das gilt jedoch nur für die das Konfigurationsobjekt, in der DroneApp-Klasse.
        """

        # Überschreibe die Konfiguration in dieser Klasse mit der in der DroneApp-Klasse
        self.configuration = App.get_running_app().configuration

        self.machine_config = self.configuration.config_dict['machine']
        self.app_config = self.configuration.config_dict['app']


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

        Parameters
        ---------
        kwargs: any
            Durch die Zwei sterne vor dem Namen kann man eine undefinierte Anzahl von Parameter
            übergeben werden. kw kann also beliebig viele Parameter mit variablen Namen darstellen.
        """

        super(MyScreenManager, self).__init__(**kwargs)
        self.screen_groups = {
            'settings': ['settings', 'waypoints']
        }

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


class MenuScreen(CustomScreen):
    """
    Eine zusätzliche Implementierung der Basisklassen CustomScreen für die Menübildschirme.
    (Bildschirme, die bei den Einstellungen im Kontrollbildschirm verwendet werden).

    Attributes
    ----------
    nav_bar_buttons: list
        Die Knöpfe, die in der Navigationsleiste verwendet werden.
    nav_bar: BoxLayout
        Die Navigationsleiste.
    """

    nav_bar_buttons = []

    def __init__(self, **kwargs):
        """
        Erstellt alle nötigen Variablen für die Klasse.

        Parameters
        ---------
        kwargs: any
            Durch die Zwei sterne vor dem Namen kann man eine undefinierte Anzahl von Parameter
            übergeben werden. kw kann also beliebig viele Parameter mit variablen Namen darstellen.
        """

        super(MenuScreen, self).__init__(**kwargs)
        self.nav_bar = None

    def on_pre_enter(self, *args) -> None:
        """
        Wird aufgerufen, wenn dieser Bildschirm aufgerufen wird und die Animation gerade startet.
        Der Unterschied zu on_enter:
        on_pre_enter:
            - Wird vor on_enter aufgerufen
            - Die Animation startet gerade
        on_enter:
            - Die Animation ist beendet
            - Der Bildschirm ist gerendert

        Parameters
        ---------
        args: any
            Durch den einen Stern vor dem Namen können  beliebig viele positionelle Argumente
            angenommen werden.
            Dieses Signatur wird von Kivy vorgegeben.
        """

        self.nav_bar = App.get_running_app().root.ids.nav_bar
        # Wurde die Navigationsleiste schon erstellt?
        # Wenn nein dann erstelle sie
        if self.nav_bar.size_hint_y is None:
            self.nav_bar.size_hint_y = 0.1

            settings_group = self.manager.screen_groups['settings']
            for settings in settings_group:
                btn = Button(text=settings)
                btn.bind(on_release=self.on_nav_bar_btn_clicked)
                self.nav_bar_buttons.append(btn)
                self.nav_bar.add_widget(btn)
        super(MenuScreen, self).on_pre_enter(*args)

    def on_nav_bar_btn_clicked(self, *args) -> None:
        """
        Wird aufgerufen, wenn ein Knopf der Navigationsleiste gedrückt wird.
        Sobald ein Knopf gedrückt wird, soll der Bildschirm zu den gewünschten Ziel gewechselt werden.


        Parameters
        ---------
        args: any
            Durch den einen Stern vor dem Namen können beliebig viele positionelle Argumente
            angenommen werden.
            Dieses Signatur wird von Kivy vorgegeben.
        """

        index = self.nav_bar_buttons.index(args[0])
        current_index = self.manager.screen_groups['settings'].index(self.manager.current)
        if current_index > index:
            transition = 'right'
        else:
            transition = 'left'
        self.manager.go_to_screen_of_group('settings', index, transition)

    def close_menu(self, *args) -> None:
        """
        Die Funktion wird aufgerufen, wenn ein bestimmter Knopf(Zurück-Knopf) gedrückt wird.
        Dann werden alle Knöpfe und der Bereich für die Navigationsleiste minimiert.
        """

        # Zerstöre alle Knöpfe
        for index in range(len(self.nav_bar.children)):
            self.nav_bar.remove_widget(self.nav_bar.children[0])
        self.nav_bar_buttons.clear()

        # Minimiere den Navigationsbereich
        # Size_hint_y steht für die relative Höhe zum Eltern Widget.
        # Um die Höhe mit absoluten Zahlen zu setzen, muss es auf None gesetzt werden
        self.nav_bar.size_hint_y = None
        self.nav_bar.height = 0
        self.go_back('control')

    def on_touch_up(self, touch):
        """
        Wird aufgerufen, sobald der Benutzer sein Finger von den Bildschirm abhebt.
        Diese Funktion ist für die Wischfunktion in den Menübildschirm verantwortlich.
        Basierend auf die Richtung der Wisches, wird der nächste Bildschirm oder der vorherige
        Bildschirm aufgerufen.

        Parameters
        ----------
        touch: MouseMotionEvent
            Das Objekt, das Daten über die Berührung wie z.B die Position enthält.
        """

        # touch.ox beinhaltet die Startposition des Touches
        if touch.x < touch.ox - self.app_config['swipe_distance']:
            self.manager.go_next_screen_of_group('settings')
        elif touch.x > touch.ox + self.app_config['swipe_distance']:
            self.manager.go_previous_screen_of_group('settings')


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

        Parameters
        ---------
        kwargs: any
            Durch die Zwei sterne vor dem Namen kann man eine undefinierte Anzahl von Parameter
            übergeben werden. kw kann also beliebig viele Parameter mit variablen Namen darstellen.
        """

        super(StartScreen, self).__init__(**kw)
        self.fonts = list(map(lambda x: f'{FONTS_DIRECTORY}/{x}', os.listdir(FONTS_DIRECTORY)))
        self.texts = ['Welcome', 'Willkommen']

    def on_enter(self, *args) -> None:
        """
        Wird aufgerufen, sobald dieser Bildschirm aufgerufen wird.
        Diese Funktion startet den Thread, der dann wiederum die Animation abspielt.

        Parameters
        ---------
        args: any
            Durch den einen Stern vor dem Namen können beliebig viele positionelle Argumente
            angenommen werden.
            Dieses Signatur wird von Kivy vorgegeben.
        """

        print(f'{self.width} x {self.height}')
        Clock.schedule_interval(self.change_font, 2)
        super(StartScreen, self).on_enter(*args)

    def on_leave(self, *args) -> None:
        """
        Wird aufgerufen, sobald der Benutzer diesen Bildschirm verlässt.
        Sobald der Benutzer dien Bildschirm verlässt, wird der Thread gestoppt.

        Parameters
        ---------
        args: any
            Durch den einen Stern vor dem Namen können beliebig viele positionelle Argumente
            angenommen werden.
            Dieses Signatur wird von Kivy vorgegeben.
        """
        Clock.unschedule(self.change_font)
        super(StartScreen, self).on_leave(*args)

    def change_font(self, *args) -> None:
        """
        Wird von einem Thread in bestimmten Intervalltakten ausgeführt.

        Diese Funktion wählt zufällig eine Schriftart und ein Text aus und verändert dementsprechend
        den Titelbildschirm.

        Parameters
        ---------
        args: any
            Durch den einen Stern vor dem Namen können beliebig viele positionelle Argumente
            angenommen werden.
            Dieses Signatur wird von Kivy vorgegeben.
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
    app_settings = ObjectProperty(None)

    def save_config(self):
        validation = self.app_settings.validate_config()
        if validation:
            self.app_settings.save_config()

        self.configuration.save_config()


class SupportScreen(CustomScreen):
    def __init__(self, **kwargs):
        super(SupportScreen, self).__init__(**kwargs)

        self.questions = ['bluetooth', 'wlan1', 'wlan']
        self.questions = ['bluetooth', 'wlan1', 'wlan',
                          'bluetooth', 'wlan', 'wlan']
        self.answers = []

        for question in self.questions:
            self.answers.append(question + 'A')

        self.entry = []
        self.question_boxes = []
        self.text_boxes = []
        self.heights = []

    # Wird beim Laden der kv-Dateien aufgerufen
    def on_kv_post(self, base_widget) -> None:
        for index in range(len(self.questions)):
            b1 = BoxLayout()
            b1.orientation = 'vertical'
            b1.size_hint_y = None

            btn = Button(text=self.questions[index])
            btn.bind(on_release=self.trigger_box)

            a1 = AnchorLayout()

            b1.add_widget(btn)
            b1.add_widget(a1)

            self.entry.append(b1)
            self.question_boxes.append(btn)
            self.text_boxes.append(a1)

            self.ids.question_box.add_widget(b1)
        self.ids.question_box.height = self.get_height()
        super(SupportScreen, self).on_kv_post(base_widget)

    def get_height(self) -> int:
        result = 0
        for box in self.question_boxes:
            result += box.height
        return result + 50

    def trigger_box(self, *args) -> None:
        index = self.question_boxes.index(args[0])
        selected_text_box = self.text_boxes[index]
        if len(selected_text_box.children) == 0:
            self.open_box(selected_text_box, index)
        else:
            self.close_box(selected_text_box)

    def open_box(self, answer_box: BoxLayout, index: int) -> None:
        answer_box.add_widget(Button(text=self.answers[index]))

    @staticmethod
    def close_box(answer_box: BoxLayout) -> None:
        for widget in answer_box.children:
            answer_box.remove_widget(widget)


class ConnectionScreen(CustomScreen):
    status = ObjectProperty()
    wlan = ObjectProperty()

    def __init__(self, **kwargs):
        super(ConnectionScreen, self).__init__(**kwargs)
        self.connected = False

        self.response_thread = DisposableLoopThread()
        self.response_thread.event_handler.add_function(self.check_response)

        self.bluetooth_connection_thread = DisposableLoopThread()
        self.bluetooth_connection_thread.add_function(self.check_bluetooth_connection)

    def on_enter(self, *args) -> None:
        super(ConnectionScreen, self).on_enter(*args)
        self.bluetooth_connection_thread.save_start()

    def on_leave(self, *args) -> None:
        self.bluetooth_connection_thread.stop()

    def check_bluetooth_connection(self) -> None:
        if self.app_config['testcase'] or bluetooth_client.has_paired_devices(NAME):
            if not self.app_config['testcase']:
                bluetooth_client.create_socket_stream(NAME)
            self.wlan.height = self.wlan.minimum_height
            self.bluetooth_connection_thread.stop()
        else:
            self.wlan.height = 0
            self.status.text = translate(f'Turn on your bluetooth function and connect to the device') + NAME
        sleep(1)

    def send_data(self, name: str, password: str) -> None:
        if self.app_config['testcase']:
            self.manager.current = 'control'
        else:
            bluetooth_client.socket.send(f'WLAN{SEPARATOR}{name}{SEPARATOR}{password}')
            self.response_thread.save_start()

    def check_response(self) -> None:
        wlan_response = bluetooth_client.wait_for_response(flag='WC')
        esp32_data = bluetooth_client.wait_for_response(flag='STAINFO')
        bluetooth_client.socket.send(f'WLANDATA{SEPARATOR}{wlan_client.get_ip_address()}')
        server_response = bluetooth_client.wait_for_response(flag='WS')

        if 'WC1' and wlan_client.paired_device_ip in wlan_response:
            if 'STAINFO' in esp32_data:
                converted_data = esp32_data.split(SEPARATOR)
                wlan_client.connect(converted_data[1], int(converted_data[2]))
            self.status.text = f'Connection with {bluetooth_client.paired_device_name}'
            sleep(1)
            if 'WS1' in server_response:
                self.status.text = translate('Server successfully created')
                sleep(1)
                self.manager.current = 'control'
        else:
            self.status.text = translate('Connection failed')
            self.wlan.height = 0

            self.response_thread.stop()


class ControlScreen(CustomScreen):
    altitude = StringProperty()
    speed = StringProperty()

    latitude = StringProperty()
    longitude = StringProperty()

    battery = StringProperty()

    status = StringProperty()

    def __init__(self, **kwargs):
        super(ControlScreen, self).__init__(**kwargs)
        self.receive_thread = DisposableLoopThread()
        self.send_thread = DisposableLoopThread()

        self.receive_thread.add_function(self.receive_data)
        self.send_thread.add_function(self.send_data)
        self.send_thread.interval_sec = self.machine_config['tick']['value']

        self.speed = "0"
        self.altitude = "0"
        self.longitude = "0"
        self.latitude = "0"
        self.battery = "0"

        self.r_joystick = JoyStick()
        self.l_joystick = JoyStick()

        self.status = translate('Ready to take off')
        self.created = False

        if not self.app_config['testcase']:
            self.receive_thread.save_start()

        self.send_thread.save_start()

    def on_enter(self, *args) -> None:
        super(ControlScreen, self).on_enter(*args)
        if not self.created:
            self.ids.joystick_a.add_widget(self.r_joystick)
            self.ids.joystick_a.add_widget(self.l_joystick)

            self.ids.back_btn.bind(on_press=self.back_to_main)

            Clock.schedule_once(self.r_joystick.set_center, 0.01)
            Clock.schedule_once(self.l_joystick.set_center, 0.01)
            self.created = True

            if not self.app_config['testcase']:
                # Damit der Esp32 eine Connection hat, um die Sensordaten zu senden
                wlan_client.send_message('ping')

    def set_waypoint(self, *args):
        waypoints = self.app_config['waypoints']

        name = DEFAULT_WP_PREFIX
        i = 0
        while name in waypoints.keys():
            i += 1
            name = DEFAULT_WP_PREFIX + '(' + str(i) + ')'

        new_waypoint = {
            "date": datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
            "altitude": self.altitude,
            "longitude": self.longitude,
            "latitude": self.latitude
        }

        self.app_config['waypoints'][name] = new_waypoint
        self.configuration.save_config()

        self.status = translate('Waypoint') + ': ' + name + ' ' + translate('set')

    def on_config_changed(self):
        super(ControlScreen, self).on_config_changed()
        self.send_thread.interval_sec = self.machine_config['tick']['value']

    def send_data(self) -> None:
        r_relative_pos = self.r_joystick.get_center_pt()
        l_relative_pos = self.l_joystick.get_center_pt()

        if not self.app_config['testcase']:
            message = f'RJ{SEPARATOR}{r_relative_pos[0]}{SEPARATOR}{r_relative_pos[1]}'
            wlan_client.send_message(message)
            message = f'LJ{SEPARATOR}{l_relative_pos[0]}{SEPARATOR}{l_relative_pos[1]}'
            wlan_client.send_message(message)

    def receive_data(self) -> None:
        response = wlan_client.wait_for_response()
        datas = response.split(SEPARATOR)

        self.altitude = datas[0]
        self.speed = datas[1]
        self.latitude = datas[2]
        self.longitude = datas[3]

    def back_to_main(self, *args) -> None:
        if not self.app_config['testcase']:
            wlan_client.send_message(f'CMD{SEPARATOR}reset')

        bluetooth_client.reset()
        wlan_client.reset()

        self.go_back('start')


class SettingsScreen(MenuScreen):
    app_settings = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(SettingsScreen, self).__init__(**kwargs)

    def on_enter(self, *args) -> None:
        super(SettingsScreen, self).on_enter(*args)
        self.ids.tick_field.text = str(self.machine_config['tick']['value'])

    def save_config(self, *args) -> None:
        tick = self.ids.tick_field.text
        result = self.try_set_tick(tick)

        app_settings_validation = self.app_settings.validate_config()
        if result and app_settings_validation:
            self.app_settings.save_config()
            self.configuration.save_config()
            self.notify()

        self.manager.get_screen('control').status = translate('Settings saved')
        self.close_menu(None)

    def try_set_tick(self, tick: str) -> bool:
        int_tick = 0
        try:
            int_tick = int(tick)
        except ValueError:
            return False

        self.machine_config['tick']['value'] = int_tick
        return True

    def notify(self) -> None:
        if not self.app_config['testcase']:
            json_string = self.config_obj.get_json_string_from_dict(self.machine_config)
            wlan_client.send_message(f'CMD{SEPARATOR}set_config{SEPARATOR}{json_string}')


class WaypointsScreen(MenuScreen):
    def __init__(self, **kwargs):
        super(WaypointsScreen, self).__init__(**kwargs)
        self.waypoints = self.app_config['waypoints']
        self.pos_xs = [.1, .1, .42]

        self.columns = []
        self.edit_buttons = []
        self.remove_buttons = []
        self.grids = []

        self.title_labels = []
        self.altitude_labels = []
        self.latitude_labels = []
        self.longitude_labels = []
        self.date_labels = []

        # Temporäre Objekte für das bearbeitende Wegpunkt
        self.fields = []
        self.current_edit = None

    def on_enter(self, *args) -> None:
        self.waypoints = self.app_config['waypoints']

        list_area = self.ids.list_area
        list_area.height = self.get_height()

        if len(self.waypoints) != 0:
            frame_height = list_area.height / len(self.waypoints)

        for (index, key, value) in zip(range(len(self.waypoints)), self.waypoints.keys(), self.waypoints.values()):

            main = FloatLayout(size=list_area.size)

            anchor = AnchorLayout(anchor_y='top', pos_hint={'x': .0, 'y': .0})
            title_label = Label(text=key, size_hint=(.1, .3), font_size=20)
            anchor.add_widget(title_label)
            self.title_labels.append(title_label)

            grid = GridLayout(cols=2, size_hint=(.8, .7), pos_hint={'x': 0, 'y': 0})

            names = ['altitude', 'latitude', 'longitude', 'last update']
            values_names = ['altitude', 'latitude', 'longitude', 'date']
            lists = [self.altitude_labels, self.latitude_labels, self.longitude_labels, self.date_labels]

            for i in range(4):
                t_b = BoxLayout()
                label_name = Label(text=names[i])
                label_value = Label(text=str(value[values_names[i]]))
                t_b.add_widget(label_name)
                t_b.add_widget(label_value)
                lists[i].append(label_value)
                grid.add_widget(t_b)
            self.grids.append(grid)

            box_anchor = AnchorLayout(anchor_x='right', pos_hint={'x': 0, 'y': 0})
            box = BoxLayout(orientation='vertical', size_hint=(0.2, 1), padding=20, spacing=10)

            edit_button = RoundedButton(text='edit', size_hint_y=.4)
            edit_button.bind(on_release=self.edit_waypoint)
            remove_button = RoundedButton(text='remove', size_hint_y=.4)
            remove_button.bind(on_release=self.remove_waypoint)
            box.add_widget(edit_button)
            box.add_widget(remove_button)
            box_anchor.add_widget(box)

            self.edit_buttons.append(edit_button)
            self.remove_buttons.append(remove_button)

            main.add_widget(anchor)
            main.add_widget(box_anchor)
            main.add_widget(grid)

            with main.canvas.before:
                Color(rgba=[.5, .5, .5, 1])
                Line(width=1, rectangle=(0, index * frame_height, list_area.width, frame_height))

            self.columns.append(main)

            list_area.add_widget(main)

        super(WaypointsScreen, self).on_enter(args)

    def on_leave(self, *args) -> None:
        self.remove_waypoint_widgets()
        super(WaypointsScreen, self).on_leave(*args)

    def remove_waypoint_widgets(self) -> None:
        children = self.ids.list_area.children
        for index in range(len(children)):
            self.ids.list_area.remove_widget(self.ids.list_area.children[0])

    def go_back_to_menu(self, *args) -> None:
        for index in range(len(self.waypoints)):
            self.remove_waypoint(self.remove_buttons[0])
        self.manager.get_screen('control').status = ''

    def edit_waypoint(self, *args):
        if len(self.fields) != 0:
            self.save_edited_waypoint(self.current_edit)

        edit_btn = args[0]
        self.current_edit = edit_btn
        index = self.edit_buttons.index(edit_btn)
        labels = [self.altitude_labels[index], self.latitude_labels[index], self.longitude_labels[index]]

        children = self.grids[index].children

        for i, label in enumerate(labels):
            box = children[(len(children) - 1) - i]
            box.remove_widget(label)

            ti = NumericTextInput(multiline=False)

            ti.text = label.text
            ti.font_size = label.font_size

            self.fields.append(ti)
            box.add_widget(ti)

        edit_btn.text = 'save'
        edit_btn.unbind(on_release=self.edit_waypoint)
        edit_btn.bind(on_release=self.save_edited_waypoint)

    def save_edited_waypoint(self, *args):
        edit_btn = args[0]

        index = self.edit_buttons.index(edit_btn)
        title = self.title_labels[index].text

        last_update_date = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")

        self.app_config['waypoints'][title] = {
            "altitude": self.fields[0].text,
            "latitude": self.fields[1].text,
            "longitude": self.fields[2].text,
            "date": last_update_date,
        }

        lists = [self.altitude_labels, self.latitude_labels, self.longitude_labels, self.date_labels]

        self.configuration.save_config()
        children = self.grids[index].children
        for i, field in enumerate(self.fields):
            number = float(self.fields[i].text)
            if number.is_integer():
                number = int(number)

            widget = children[(len(children) - 1) - i]
            widget.remove_widget(field)

            temp_l = Label(text=str(number))
            widget.add_widget(temp_l)
            lists[i][index] = temp_l

        self.fields.clear()

        edit_btn.text = 'edit'
        edit_btn.unbind(on_release=self.save_edited_waypoint)
        edit_btn.bind(on_release=self.edit_waypoint)

    def remove_waypoint(self, *args) -> None:
        index = self.remove_buttons.index(args[0])

        if self.current_edit == self.edit_buttons[index]:
            self.fields.clear()
            self.current_edit = None

        self.app_config['waypoints'].pop(self.title_labels[index].text)
        self.configuration.save_config()
        self.waypoints = self.app_config['waypoints']

        self.ids.list_area.remove_widget(self.columns[index])
        self.ids.list_area.height = self.get_height()

        self.edit_buttons.pop(index)
        self.columns.pop(index)
        self.grids.pop(index)
        self.title_labels.pop(index)
        self.altitude_labels.pop(index)
        self.longitude_labels.pop(index)
        self.latitude_labels.pop(index)
        self.date_labels.pop(index)
        self.remove_buttons.pop(index)

    def get_height(self) -> int:
        return len(self.waypoints) * (self.width / 5.5)

    @staticmethod
    def adjust_pos_hint(label, text_before, text_after) -> None:
        print('ss')
        label.pos_hint = {
            'x': label.pos_hint['x'] + (len(text_before) - len(text_after)) * -0.0055,
            'y': label.pos_hint['y']
        }


# *******************************************************************

# *************************** Einstiegspunkt ************************


class DroneRoot(BoxLayout):
    pass


class DroneApp(App):
    __version__ = "0.1"

    current_theme = StringProperty()

    def __init__(self, **kwargs):
        super(DroneApp, self).__init__(**kwargs)
        self.configuration = Configuration('./data/config.json', True)

        self.translated_labels = []
        self.translated_parts = []

        self.translation = None

        self.current_theme = self.configuration.config_dict['app']['current_theme']
        self.configuration.on_config_changed.add_function(self.on_config_changed)

    def on_config_changed(self):
        self.configuration.load_config()
        self.current_theme = self.configuration.config_dict['app']['current_theme']

    def bind_text(self, label, text, entire_text):
        self.translated_labels.append(label)
        translated_text = self.translation.gettext(text)

        self.translated_parts.append(translated_text)
        return entire_text.replace(text, translated_text)

    def update_text(self):
        for index, label in enumerate(self.translated_labels):
            translated_text = self.translation.gettext(self.translated_parts[index])
            label.text = label.text.replace(self.translated_parts[index], translated_text)
            self.translated_parts[index] = translated_text

    def build(self):
        self.translation = gettext.translation('base', localedir='locales',
                                               languages=[self.configuration.config_dict['app']['current_language']])
        self.translation.install()
        self.load_kv_files()
        return DroneRoot()

    @staticmethod
    def load_kv_files():
        files = os.listdir(KV_DIRECTORY)
        for file in files:
            path = KV_DIRECTORY + '/' + file
            Builder.load_file(path)


def translate(message) -> str:
    return App.get_running_app().translation.gettext(message)


# *******************************************************************


if __name__ == '__main__':
    DroneApp().run()
