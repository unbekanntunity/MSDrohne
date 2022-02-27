# *********************** custom_threads.py **************************
# Klasse für die Implementierung von eigene Threads
# Denn die normalen threads können nicht ohne weiteres gestoppt werden,
# zudem kann man nur eine Funktion per Thread starten.
# Eine andere Option wären Prozesse. Sie sind isoliert und können dadurch
# relativ einfach gestoppt werden, aber es werden keine Daten geteilt,
# was für unseren Zweck essentiell ist.
# ********************************************************************

from misc.event_handling import EventHandler
from threading import Thread
from time import sleep


class DisposableLoopThread(Thread):
    """
    Klasse für die Implementierung eigener Threads, die mehrere Funktionen gleichzeitig
    in einer Schleife aufrufen und gestoppt werden können. Zudem werden die Ergebnisse
    der Funktionen unabhängig voneinander in einer Liste gespeichert.
    Man kann zudem Funktionen aufrufen, sobald der Thread gestoppt wurde.
    Die Häufigkeit, wie oft die Funktion aufgerufen wird, bleibt bei jeder Funktion jedoch gleich.
    Parent: Thread

    Attributes
    ----------
    event_handler: EventHandler
        Die Funktionen, die in der Schleife aufgerufen werden sollen.
    on_finished_events: EventHandler
        Die Funktionen, aufgerufen werden sollen, sobald der Thread gestoppt wurde.
    started: bool
        Wurde der Thread gestartet?
    proceed: bool
        Sollen die Funktionen weiterhin aufgerufen werden, oder wurde der Thread gestoppt?
    interval_sec: int
        Das Intervall, in der zwischen jeden Durchlauf gewartet wird.
    results: list
        Die Ergebnisse jeder Funktionen.

    Methods
    -------
    get_json_string():
        Gibt den Inhalt der Konfiguration als JSON-string zurück.
    load_config():
        lädt die Konfiguration
    save_config():
        speichert die Konfiguration
    """

    def __init__(self):
        """
        (siehe parent)
        Erstellt alle nötigen Variablen für die DisposableLoopThread-Klasse.
        """

        Thread.__init__(self)
        self.event_handler = EventHandler()
        self.on_finished_events = EventHandler()
        self.daemon = True

        self.started = False
        self.proceed = False
        self.interval_sec = 1

        self.results = {}

    def save_start(self) -> None:
        """
        Startet den Thread, wobei jeder Thread nur einmal gestartet werden kann. Diese Funktion ist
        also gegenüber der in der Elternklasse: Thread()-Klasse definierten, start()-Funktion zu empfehlen.
        """

        if self.started:
            self.restart()
        else:
            self.start()

    def restart(self) -> None:
        """
        Startet den Thread neu, indem der Konstruktor aufgerufen wird und setzt sie wieder mit den
        alten Variablen gleich.
        """

        interval_sec = self.interval_sec
        event_handler = self.event_handler
        on_finished_event_handler = self.on_finished_events

        self.__init__()
        self.interval_sec = interval_sec
        self.event_handler = event_handler
        self.on_finished_events = on_finished_event_handler

        self.save_start()

    def run(self) -> None:
        """
        (siehe parent)
        Die Hauptfunktion jedes Threads. Diese Funktion läuft in einer Dauerschleife bis,
        das Objekt zerstört oder das Programm beendet wird.
        Die Ergebnisse werden in 'self.results' gespeichert.
        """

        while self.proceed:
            self.results = self.event_handler.invoke()
            sleep(self.interval_sec)

    def start(self) -> None:
        """
        (siehe parent)
        Startet den Thread. Nicht zu empfehlen.
        """

        if not self.proceed:
            self.started = True
            self.proceed = True
            Thread.start(self)

    def stop(self) -> None:
        """
        Stoppt die Ausführung der im 'self.events' definierten Funktionen.
        """

        self.proceed = False
        self.on_finished_events.invoke()

    def add_function(self, function) -> None:
        """
        Fügt eine auszuführende Funktion  den dazugehörenden Platz in der 'self.results' Liste hinzu,
        selbst wenn diese Funktionen kein Rückgabewert hat.

        Parameters
        ----------
        function: method
            Die Funktion, die ausgeführt werden soll.
        """

        self.event_handler.add_function(function)
        self.results[function] = None

    def remove_event(self, function) -> None:
        """
        Entfernt eine Funktion, sofern sie existiert und deren Plart in der 'self.results' Liste.

        Parameters
        ----------
        function: method
            Die Funktion, die entfernt werden soll.
        """

        if function in self.event_handler:
            index = self.event_handler.events.index(function)

            self.event_handler.remove_function(function)
            self.results.pop(index)
