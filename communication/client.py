# *********************** client.py **************************
# Eine Klasse für die Kommunikation mit der Drohne (ESP32)
# ************************************************************
from datetime import datetime
from time import sleep

import socket

# Konstanten
SIZE = 1024


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

    def wait_for_response(self, flag: str = '') -> str:
        """
        Sendet eine Nachricht über den Socket. Setzt voraus, dass ein Socket
        mithilfe der connect()-Methode erstellt wurde.

        Parameters
        ----------
        flag: str, optional:
            default: ''
            Eine Zeichenkette, die die Nachricht zu beinhalten hat.
        """

        while True:
            data = self.socket.recv(1024).decode('UTF-8')
            if data:
                if flag != '':
                    return data
                else:
                    if flag in data:
                        return data
                    else:
                        return ''

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