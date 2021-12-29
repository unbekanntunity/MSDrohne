import time

from rnd.eventHandling import EventHandler
from threading import Thread


class DisposableLoopThread(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.events = EventHandler()
        self.on_finished_events = EventHandler()

        self.started = False
        self.proceed = False
        self.interval_sec = 1

        self.results = {}

    def start(self):
        if not self.proceed:
            self.started = True
            self.proceed = True
            Thread.start(self)

    def run(self):
        while self.proceed:
            time.sleep(self.interval_sec)
            self.results = self.events.invoke()

    def save_start(self):
        if self.started:
            self.proceed = True
        else:
            self.start()

    def add_event(self, function):
        self.events.add_event(function)
        self.results[function] = None

    def stop(self):
        self.proceed = False
        self.on_finished_events.invoke()
