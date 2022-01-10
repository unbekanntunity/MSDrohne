# *********************** joystick.py **************************
# Klasse, die eine eigenes "Onscreen-Joystick" implementiert
# kv.file: kv_files/joystick.kv
# **************************************************************
import kivy.input
from kivy.uix.widget import Widget
from kivy.properties import ListProperty, NumericProperty
from kivy.input.providers.mouse import MouseMotionEvent


class JoyStick(Widget):
    """
    Klasse für die Kommunikation über WLAN (ESP32)
    Die Graphik besteht aus zwei Kreisen, mit unterschiedlichen Radien
    Der kleinere Kreis, ist dabei der bewegliche Teil.

    Class Properties
    ----------------
    Einstellbar ------------------------------
    outer_background_color: Kivy.ObservableList
        Hintergrund des äußeren Bereiches (Grenze innerer Kreis -  Grenze äußerer Kreis) (RGBA) -> [R, G, B, A]
    outer_radius: float
        Radius des äußeren Bereiches
    outer_diameter: float
        Durchmesser des äußeren Bereiches

    outer_line_color: Kivy.ObservableList
        Farbe der Grenze des äußeren Bereiches (RGBA)
    outer_line_width: float
        Dicke der Grenze des äußeren Bereiches

    inner_background_color: Kivy.ObservableList
        Hintergrund des inneren Bereiches (RGBA)
    inner_radius: float
        Radius des inneren Bereiches
    inner_diameter: float
        Durchmesser des inneren Bereiches

    inner_line_color: Kivy.ObservableList
        Farbe der Grenze des inneren Bereiches (RGBA)
    inner_line_width: float
        Dicke der Grenze des inneren Bereiches
    ------------------------------------------

    js_center_x: float
        Der X-Wert der Koordinate des inneren Kreises
    js_center_y: float
        Der Y-Wert der Koordinate des inneren Kreises

    Attributes
    ----------
    process_touch: bool
        Soll der registrierte Touch weiterverarbeitet werden?
        Sprich soll die update_center() Methode aufgerufen werden und der innere Kreis verschoben werden
        Ja: Wenn die Berührung innerhalb der äußeren Kreises war
        Nein: Wenn die Berührung außerhalb der äußeren Kreises war

    Methods
    -------
    on_touch_down(touch):
        Wird bei der ersten Berührung, also beim Absetzen aufgerufen.
    on_touch_move(touch):
        Wird aufgerufen, wenn der Finger auf den Display bewegt wird.
    on_touch_up(touch):
        Wird beim aufsetzen des Fingers aufgerufen.
    set_center():
        Positioniert den inneren Kreis (beweglicher Teil) im Zentrum des Kreises
    update_center(x, y):
        Aktualisiert die Position des inneren Kreises (beweglicher Teils), abhängig von dem x und y Wert
    """
    # Properties: Sobald diese Variablen geändert werden, spiegelt sich diese Veränderung auch
    # in den Objekten wieder, die diese Variable verwenden z.b in den .kv-files (Binding)

    # Äußerer Kreis
    outer_background_color = ListProperty([0.75, 0.75, 0.75, 1])
    outer_radius = NumericProperty(70)
    outer_diameter = NumericProperty(140)

    outer_line_color = ListProperty([0.25, 0.25, 0.25, 1])
    outer_line_width = NumericProperty(1)

    # Innerer Kreis
    inner_background_color = ListProperty([0.1, 0.7, 0.1, 1])
    inner_radius = NumericProperty(20)
    inner_diameter = NumericProperty(40)

    inner_line_color = ListProperty([0.7, 0.7, 0.7, 1])
    inner_line_width = NumericProperty(1)

    js_center_x = NumericProperty(1)
    js_center_y = NumericProperty(1)

    def __init__(self, **kwargs):
        """
        Erstellt alle nötigen Variablen für die Joystick-Klasse.

        Parameters
        ----------
        **kwargs: Any
            Wenn eine Klasse von der Klasse 'Widget' erbt, wird in den Konstruktor eine
            gewisse Anzahl and Parameter übergeben, auch wenn wir sie selber nicht verwenden.
        """
        super().__init__()  # Super bezieht sich immer auf die Elternklasse
        self.js_center_origin_x = self.center_x
        self.js_center_origin_y = self.center_y

        self.js_center_x = self.js_center_origin_x
        self.js_center_y = self.js_center_origin_y

        self.process_touch = False

    # Events
    def on_touch_down(self, touch) -> None:
        """
        Wird bei der ersten Berührung, also beim Absetzen aufgerufen und ist ein
        von Kivy erstelltes Event.

        Parameters
        ----------
        touch: MouseMotionEvent
            Das Objekt, das Daten über die Berührung wie z.B die Position enthält.
        """
        # Ist der Anfangspunkt im Kreis?
        result = (round(touch.pos[0]) - self.center_x)**2 + (round(touch.pos[1]) - self.js_center_y)**2 - self.outer_radius**2
        if result < 0:
            self.process_touch = True
        super().on_touch_up(touch)

    def on_touch_move(self, touch: MouseMotionEvent) -> None:
        """
        Wird während der Bewegung des Finger auf den Bildschirm aufgerufen und ist ein
        von Kivy erstelltes Event.

        Parameters
        ----------
        touch: MouseMotionEvent
            Das Objekt, das Daten über die Berührung wie z.B die Position enthält.
        """
        if self.process_touch:
            self.update_center(round(touch.pos[0]), round(touch.pos[1]))
        super().on_touch_move(touch)

    def on_touch_up(self, touch: MouseMotionEvent) -> None:
        """
        Wird nach der letzten Berührung, also dem Aufsetzen des Fingers aufgerufen und ist ein
        von Kivy erstelltes Event.

        Parameters
        ----------
        touch: MouseMotionEvent
            Das Objekt, das Daten über die Berührung wie z.B die Position enthält.
        """
        self.js_center_x = self.js_center_origin_x
        self.js_center_y = self.js_center_origin_y
        self.process_touch = False
        super().on_touch_up(touch)

    def get_center_pt(self):
        """
        Gibt die relative Position des inneren Kreises zurück.
        Falls dieser außerhalb des äußeren Kreises ist, wird ein Wert von 1 zurückgegeben.


        Returns
        -------
        (x, y): tuple(float, float)
            Die Werte für die relative Position
        """

        x = (1 - (self.center_x / self.js_center_x)) * 10
        y = (1 - (self.center_y / self.js_center_y)) * 10

        if x > 1:
            x = 1
        if y > 1:
            y = 1

        return (x, y)

    # TODO: args entfernen
    def set_center(self, *args) -> None:
        """
        Positioniert den inneren Kreis (bewegliche Teil) im Zentrum des Kreises.
        Diese sollte am Anfang über eine Clock aufgerufen werden und nicht direkt im
        im Konstruktor oder beim on_enter() Event ,da an diesen Stellen die UI noch gebaut wird.
        Macht man es jedoch doch, kann sich der kleine Kreis (innere Bereich) verschieben und
        außerhalb des äußeren Bereiches landen.

        Beispiel:
        def on_enter():
            Clock.schedule_once(self.joystick.set_center, 0.1)
        """

        self.js_center_origin_x = self.canvas.children[2].pos[0] + self.outer_radius
        self.js_center_origin_y = self.canvas.children[2].pos[1] + self.outer_radius

        self.js_center_x = self.js_center_origin_x
        self.js_center_y = self.js_center_origin_y

    def update_center(self, x, y) -> None:
        """
        Aktualisiert die Position des inneren Kreises (beweglicher Teils), abhängig
        von dem x und y Wert. Dabei wird die Differenz aus der momentanen Position des
        inneren Kreises und der Position der Berührung gezogen.

        Das Zentrum(Anchor) befindet sich unten rechts von der Graphik. AUs diesen Grund muss eine
        kleine Berechnung getätigt werden, um das zu korrigieren.

        Parameters
        ----------
        x: float
            Der X-Wert, der berührten Stelle auf den Bildschirm
        y: float
            Der Y-Wert, der berührten Stelle auf den Bildschirm
        """

        center = self.canvas.children[2]
        adapted_x = center.pos[0] + self.outer_radius
        adapted_y = center.pos[1] + self.outer_radius

        self.js_center_x = self.js_center_origin_x + (x - adapted_x)
        self.js_center_y = self.js_center_origin_y + (y - adapted_y)
