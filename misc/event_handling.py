# *********************** event_handling.py **************************
# Klasse für die Implementierung von Events
# Events sind Objekte, an den man Funktionen anhängen kann,
# egal, ob von welchen Typ oder von welchen Objekt, und durch
# die invoke()-Funktion ausgelöst werden.
# ********************************************************************

class EventHandler(object):
    """
    Klasse für die Implementierung der Event-Funktion nach dem Vorbild des Datentypes in C#

    Attributes
    ----------
    events: EventHandler
        Die Funktionen, die aufgerufen werden sollen.
    """

    def __init__(self):
        """
        Erstellt alle nötigen Variablen für die EventHandlerBase-Klasse.
        """

        self.events = []

    def __iadd__(self, Ehandler):
        """
        Wird bei der Subtraktion mit dieser Klasse und ihre Instanzen verwendet.
        Es handelt sich hier um eine sogenannte 'magic method'.

        Beispiel: EventhandlerBase -= 12 -> Ehandler = 12

        Parameters
        ----------
        Ehandler: method
            Die Funktion, die hinzugefügt werden soll.
        """

        self.events.append(Ehandler)
        return self

    def __isub__(self, Ehandler):
        """
        Wird bei der Subtraktion mit dieser Klasse und ihre Instanzen verwendet.
        Es handelt sich hier um eine sogenannte 'magic method'.

        Beispiel: EventhandlerBase -= 12 -> Ehandler = 12

        Parameters
        ----------
        Ehandler: method
            Die Funktion, die entfernt werden soll.
        """

        if Ehandler in self.events:
            self.events.remove(Ehandler)
        return self

    def __call__(self, *args, **keywargs):
        """
        Die Klasse kann dadurch als Funktion verwendet werden. Es handelt sich hier
        um eine sogenannte 'magic method'.

        Beispiel: EventhandlerBase()
        """

        results = []

        for event in self.events:
            res = event(*args, **keywargs)
            results.append(res)
        return results

    def invoke(self, *args):
        """
        Führt die __call__() Funktion aus.
        Soll für eine benutzerfreundliche Bedingung sein.
        """
        return self(*args)

    def add_function(self, function):
        """
        Führt die __iadd__() Funktion aus.
        Soll für eine benutzerfreundliche Bedingung sein.
        """

        self += function

    def remove_function(self, function):
        """
        Führt die __isub() Funktion aus.
        Soll für eine benutzerfreundliche Bedingung sein.
        """
        self -= function


if __name__ == '__main__':
    print(help(EventHandler))
