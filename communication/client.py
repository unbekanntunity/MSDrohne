# *********************** client.py **************************
# Eine Klasse für die Kommunikation mit der Drohne (ESP32)
# ************************************************************
from datetime import datetime
from time import sleep
from jnius import autoclass

import socket

# Konstanten
SIZE = 1024


class BluetoothClient(object):
    """
    Basisklasse für die Bluetooth-Kommunikation.
    Die Kommunikation soll dabei nur mit einen Gerät stattfinden (ESP32).

    Attributes
    ----------
    socket: Any
        Socket, worüber Nachrichten gesendet und empfangen werden.
    paired_device_name: str
        Der Name des verbundenen Gerätes (ESP32).

    Methods
    -------
    wait_for_response(flag=None)
        Wartet bis eine Nachricht angekommen ist.
    reset()
        Setzt den Client zurück.
    """

    def __init__(self):
        """
        Erstellt alle nötigen Variablen für die BluetoothClient-Klasse.
        """

        self.socket = None
        self.paired_device_name = ''

    def wait_for_response(self, flag: str = '', timeout_sec: int = -1) -> str:
        """
        Wartet bis eine Nachricht angekommen ist.
        Dabei wird der Thread wird dabei blockiert.

        Parameters
        ----------
        flag: str, optional
            default: None
            Zeichenkette, die in der Nachricht enthalten sein muss.
            Nur falls diese Zeichenkette in der Nachricht ist, wird sie zurückgegeben,
            ansonsten wird weiter auf eine passende Nachricht gewartet.
        timeout_sec: int, optional
            default: -1
            Die Zeitspanne in der, auf der Nachricht gewartet wird.

        Returns
        -------
        data: str
            Die Nachricht. Falls ein der timeout_sec parameter verwendet wurde und keine passende
            Nachricht in der Zeitspanne gefangen wurde, wird eine leere Zeichenkette zurückgegeben.
        """

        time_started = datetime.now()
        while True:
            if timeout_sec > -1 and datetime.now().second - timeout_sec is time_started:
                print("Timeout!")
                return ''

            data = self.socket.recv(1024)
            if data:
                if flag != '':
                    if str.encode(flag, 'UTf-8') in data:
                        return data
                else:
                    return data
            sleep(0.1)

    def reset(self) -> None:
        """
        Der momentane Socket wird geschlossen und auf None gesetzt.
        """

        if self.socket is not None:
            self.socket.close()
            self.socket = None


# TODO: Doc aufbessern
class AndroidBluetoothClient(BluetoothClient):
    from jnius import autoclass

    """
    Implementierung für Android-Geräte.
    Parent: BluetoothClient

    Attributes
    ----------
    bluetoothAdapter: Any
    bluetoothDevice: Any
    bluetoothSocket: Any
    uuid: Any
    send_stream: Any
    recv_stream: Any

    Methods
    -------
    reset():
        (Siehe Parent)
    create_socket_stream(name):
        Sucht nach dem Gerät mit dem angegebenen Namen und erstellt ein Socket.
    has_paired_devices(name=''):
        Überprüft, ob das Gerät mit einem einen Gerät verbunden ist.
    """

    def __init__(self):
        """
        (siehe parent)
        Erstellt alle nötigen Variablen für die BluetoothClient-Klasse.
        """

        super(BluetoothClient, self).__init__()
        # Zugriff auf die Android API(geschrieben in Java) über pyjnius
        self.bluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
        self.bluetoothDevice = autoclass('android.bluetooth.BluetoothDevice')
        self.bluetoothSocket = autoclass('android.bluetooth.BluetoothSocket')
        self.uuid = autoclass('java.util.UUID')

        self.send_stream = None
        self.recv_stream = None

    def reset(self):
        """
        (siehe parent)
        Setzt zudem die Variablen (den Input- und Outputstream) zurück.
        """

        self.send_stream = None
        self.recv_stream = None
        super(AndroidBluetoothClient, self).reset()

    def create_socket_stream(self, name: str) -> None:
        """
        Sucht nach dem Gerät mit dem angegebenen Namen und erstellt ein Socket.
        Worüber dann Daten gesendet und empfangen werden können.

        Parameters
        ----------
        name: str
            Der Name des gesuchten Gerätes, womit eine Verbindung erstellt werden soll.
        """

        if self.has_paired_devices():
            paired_devices = self.bluetoothAdapter.getDefaultAdapter().getBondedDevices().toArray()
            for device in paired_devices:
                if device.getName() == name:
                    self.socket = device.createRfcommSocketToServiceRecord(
                        self.uuid.fromString("00001101-0000-1000-8000-00805F9B34FB"))
                    self.recv_stream = self.socket.getInputStream()
                    self.send_stream = self.socket.getOutputStream()
                    self.paired_device_name = name
                    break
            if self.socket is not None:
                self.socket.connect()

    def get_paired_devices(self):
        return list(map(lambda x: x.getName(), self.bluetoothAdapter.getDefaultAdapter().getBondedDevices().toArray()))

    def has_paired_devices(self, name: str = '') -> bool:
        """
        Überprüft, ob der Client eine Bluetooth-Verbindung hat.
        Falls ein Name übergeben wurde, wird geschaut ob der Client eine Verbindung mit einem Gerät,
        der diesen Namen trägt, hat.

        Parameters
        ----------
        name: str, optional
            default: ''
            Der Name des gesuchten Gerätes.

        Returns
        -------
        <nameless>: boola
            Das Ergebnis der Suche.
        """

        paired_devices = self.get_paired_devices()
        if len(paired_devices) != 0:
            if name != '':
                return name in map(lambda x: x.getName(), paired_devices)
            else:
                return True
        return False


class WLANClient(object):
    """
    Klasse für die Kommunikation über WLAN
    Die Kommunikation soll dabei nur mit einen Gerät stattfinden (ESP32).

    Attributes
    ----------
    socket: Any
        Socket, worüber Nachrichten gesendet und empfangen werden-
    paired_device_ip: str
        Die IP-Adresse des Zielgerätes(ESP32)-
    paired_device_port: int
        Der Port des Zielgerätes(ESP32)-

    Methods
    -------
    connect(address, port):
        Erstellt ein Socket und speichert die IP und den Port.
    send_message(message):
        Sendet eine Nachricht über den Socket.
    wait_for_response(self, flag='', only_paired_device=False):
        Wartet bis eine Nachricht angekommen ist.
    reset():
        Setzt den Client zurück und kappt die Verbindung.
    get_ip_address():
        Gibt die IP-Adresse im momentanen Netzwerk zurück.
    """

    def __init__(self):
        """
        Erstellt alle nötigen Variablen für die WLANClient-Klasse.
        """

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.paired_device_ip = ''
        self.paired_device_port = ''

    def connect(self, address: str, port: int) -> None:
        """
        Erstellt eine Verbindung mithilfe der IP-Adresse und dem Port über einem Socket
        und speichert die Daten.

        Parameters
        ----------
        address: str
            Die IP-Adresse des Zielgerätes(ESP32)
        port: int
            Der Port des Zielgerätes(ESP32)

        """

        self.socket.connect((address, port))
        self.paired_device_ip = address
        self.paired_device_port = port

    def send_message(self, message: str) -> None:
        """
        Sendet eine Nachricht über den Socket. Setzt voraus, dass ein Socket
        mithilfe der connect()-Methode erstellt wurde.

        Parameters
        ----------
        message: str
            Die Nachricht
        """

        self.socket.send(message.encode())
        data = self.socket.recv(1024).decode()
        print(data)

    def wait_for_response(self, flag: str = '', only_paired_device: bool = False) -> str:
        """
        Sendet eine Nachricht über den Socket. Setzt voraus, dass ein Socket
        mithilfe der connect()-Methode erstellt wurde.

        Parameters
        ----------
        flag: str, optional:
            default: ''
            Eine Zeichenkette, die die Nachricht zu beinhalten hat.
        only_paired_device: bool, optional
            default: False
            Sollen nur Nachrichten, von den Gerät, dessen Daten durch die connect() Methode gespeichert
            wurden, beachtet werden?
        """

        while True:
            data = self.socket.recv(1024).decode('UTF-8')
            if data:
                if only_paired_device:
                    if self.paired_device_ip in data:
                        if flag != '':
                            return data
                        elif flag in data:
                            return data
                else:
                    return data
            sleep(1)

    def reset(self) -> None:
        """
        Setzt den Client zurück.
        """

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.paired_device_ip = ''
        self.paired_device_port = ''

    # TODO: Funktioniert, es auch ohne WLAN?
    @staticmethod
    def get_ip_address() -> str:
        """
        Ermittelt die IP-Adresse vom Client.

        Returns
        -------
        <nameless>: str
            Die IP-Adresse, falls möglich
        """

        h_name = socket.gethostname()
        return socket.gethostbyname(h_name)