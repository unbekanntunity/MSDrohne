import time

from Rnd.eventHandling import EventHandler
from threading import Thread


class DisposableThread(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.events = EventHandler()
        self.proceed = False
        self.interval_sec = 1

    def start(self):
        if not self.proceed:
            self.proceed = True
            self.run()

    def run(self):
        while self.proceed:
            time.sleep(self.interval_sec)
            self.events.invoke()

    def add_event(self, function):
        self.events.add_event(function)

    def stop(self):
        self.proceed = False

