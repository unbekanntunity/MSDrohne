class EventHandlerBase(object):
    def __init__(self):
        self.__events = []

    def __iadd__(self, Ehandler):
        self.__events.append(Ehandler)
        return self

    def __isub__(self, Ehandler):
        self.__events.remove(Ehandler)
        return self

    def __call__(self, *args, **keywargs):
        results = []

        for event in self.__events:
            res = event(*args, **keywargs)
            results.append(res)
        return results


class EventHandler(object):
    def __init__(self):
        self.eventHandler = EventHandlerBase()

    def invoke(self):
        return self.eventHandler()

    def add_event(self, function):
        self.eventHandler += function