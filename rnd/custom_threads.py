# *********************** custom_threads.py **************************
# Klasse für die Implementierung von eigene Threads
# Denn die normalen threads können nicht ohne weiteres gestoppt werden,
# zudem kann man nur eine Funktion per Thread starten.
# Eine andere Option wären Prozesse. Sie sind isoliert und können dadurch
# relativ einfach gestoppt werden, aber es werden keine Daten geteilt,
# was für unseren Zweck essentiell ist.
# ********************************************************************

from rnd.event_handling import EventHandler
from threading import Thread
from time import sleep


class DisposableLoopThread(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.events = EventHandler()
        self.on_finished_events = EventHandler()

        self.started = False
        self.proceed = False
        self.interval_sec = 1

        self.results = {}

    # Threads können nur einmal gestartet werden, selbst wenn sie gestoppt wurden
    def save_start(self):
        if self.started:
            self.proceed = True
        else:
            self.start()

    def start(self):
        if not self.proceed:
            self.started = True
            self.proceed = True
            Thread.start(self)

    def run(self):
        while self.proceed:
            sleep(self.interval_sec)
            self.results = self.events.invoke()

    def stop(self):
        self.proceed = False
        self.on_finished_events.invoke()

    def add_event(self, function):
        self.events.add_event(function)
        self.results[function] = None
