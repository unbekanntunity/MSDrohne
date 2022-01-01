# *********************** event_handling.py **************************
# Klasse für die Implementierung von Events
# Events sind Objekte, an den man Funktionen anhängen kann,
# egal, ob von welchen Typ oder von welchen Objekt, und durch
# die invoke()-Funktion ausgelöst werden.
# ********************************************************************

# Base
class EventHandlerBase(object):
    def __init__(self):
        self.__events = []

    # Wird bei der Addition mit dieser Klasse und ihre Instanzen verwendet
    # z.B EventhandlerBase += 12 -> Ehandler = 12
    def __iadd__(self, Ehandler):
        self.__events.append(Ehandler)
        return self

    # Wird bei der Subtraktion mit dieser Klasse und ihre Instanzen verwendet
    # z.B EventhandlerBase -= 12 -> Ehandler = 12
    def __isub__(self, Ehandler):
        self.__events.remove(Ehandler)
        return self

    # Die Klasse kann dadurch als Funktion verwendet werden
    # z.B EventhandlerBase()
    def __call__(self, *args, **keywargs):
        results = []

        for event in self.__events:
            res = event(*args, **keywargs)
            results.append(res)
        return results


# Implementierung
class EventHandler(object):
    def __init__(self):
        self.eventHandler = EventHandlerBase()

    def invoke(self):
        return self.eventHandler()

    def add_event(self, function):
        self.eventHandler += function
