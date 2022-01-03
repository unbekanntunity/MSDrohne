# *********************** configuration.py **************************
# Klasse für das Laden und Speichern der Konfiguration, die
# in der ./data/config.json gespeichert ist
# ********************************************************************
from misc.event_handling import EventHandler
import json


class Configuration(object):
    """
    Klasse für die Konfiguration der Applikation. Die Konfiguration, muss im JSON-Format gespeichert sein und
    sollte nur typischen Datentypen haben z.B int, string, bool u.s.w.

    Attributes
    ----------
    file_path: str
        Dateipfad der Konfiguration.
    config_dict: dict
        Die geladene Konfiguration als 'Dictionary'.
    on_config_changed: EventHandler
        Ein selbst erstelltes Event, was ausgelöst wird, sobald die save_config() Methode aufgerufen wurde.

    Methods
    -------
    get_json_string():
        Gibt den Inhalt der Konfiguration als JSON-string zurück.
    load_config():
        lädt die Konfiguration
    save_config():
        speichert die Konfiguration
    """

    def __init__(self, file_path: str, load_at_init: bool = False):
        """
        Erstellt alle nötigen Variablen für die Configuration-Klasse.

        Parameters
        ----------
        file_path: str
            Dateipfad der Konfigurationsdatei
        load_at_init: bool
            Soll die Datei im Konstruktor geladen werden?
        """

        self.file_path = file_path
        self.config_dict = {}
        self.on_config_changed = EventHandler()

        if load_at_init:
            self.load_config()

    def get_json_string_from_file(self) -> str:
        """
        Liest den Inhalt der Konfigurationsdatei und gibt ihm als Zeichenkette zurück.

        Returns
        -------
        <nameless>:str
            Konvertiere Zeichenkette im JSON-Format
        """

        string = ''
        with open(self.file_path, 'r') as f:
            lines = f.readlines()
            return string.join(lines)

    @staticmethod
    def get_json_string_from_dict(target_dict: dict) -> str:
        """
        Konvertiert ein 'Dictionary' zu einer Zeichenkette, die den JSON-Format entspricht und gíbt ihm zurück.

        Parameters
        ----------
        target_dict: dict
            Das 'Dictionary', was konvertiert werden soll.
        Returns
        -------
        <nameless>:str
            Konvertiere Zeichenkette im JSON-Format
        """

        return json.dumps(target_dict, indent=4, sort_keys=True)

    def load_config(self) -> None:
        """
        Lädt die Konfiguration, indem als erstes der Inhalt der Datei gelesen wird und diese dann
        zu einem 'Dictionary' umgewandelt wird. Zu beachten ist, dass das Format sehr wichtig ist und kleine
        Abweichungen schon zum Fehlschlag der Konvertierung führen können.

        Aus diesen Grund sollte man am Anfang alle nötigen Einstellungen und Werte erstmal im self.config_dict
        speichern und dann die save_config() Methode aufrufen, damit das auch im richtigen Format
        in der JSON-Datei geschrieben wird.
        """

        string = self.get_json_string_from_file()
        self.config_dict = json.loads(string)

    def save_config(self) -> None:
        """
        Speichert die Konfiguration in der JSON-Datei, indem die Variable 'config_dict', in einen
        JSON-String umgewandelt wird. Wobei alle Schlüssel alphabetisch sortiert werden und Einrückungen
        eingefügt werden, damit es besser lesbar ist. Anschließend in die Datei festgeschrieben wird.
        Die Konvertierung ist relativ einfach, da bei beiden Typen, Schlüssel und Werte existieren.
        """

        with open(self.file_path, 'w') as f:
            json_str = json.dumps(self.config_dict, indent=4, sort_keys=True)
            f.write(json_str)
        self.on_config_changed.invoke()


if __name__ == '__main__':
    con = Configuration('../data/config.json')
    con.load_config()

    con.config_dict['tick'] = 10
    con.save_config()
