# *********************** client.py **************************
# Eine Klasse für die Kommunikation mit der Drohne (ESP32)
# ************************************************************

import socket

# Konstanten
from typing import Union

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

        self.sockets = []
        self.paired_device_ips = []
        self.paired_device_ports = []

        self._first_msgs = []

    def connect(self, address: str, port: int, index: int = None) -> None:
        """
        Erstellt eine Verbindung mithilfe der IP-Adresse und dem Port über einem Socket
        und speichert die Daten.

        Parameters
        ----------
        address: str
            Die IP-Adresse des Zielgerätes(ESP32)
        port: int
            Der Port des Zielgerätes(ESP32)
        index: int, optional
            default: None
            Der Index des Sockets
        """
        if index is None:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((address, port))
            self.sockets.append(s)

            self.paired_device_ips.append(address)
            self.paired_device_ports.append(port)
            self._first_msgs.append(False)
        elif index >= 0:
            self.sockets[index].connect((address, port))
            self.paired_device_ips[index] = address
            self.paired_device_ports[index] = port
            self._first_msgs[index] = False

    def send_message(self, index: int, message: str) -> None:
        """
        Sendet eine Nachricht über den Socket. Setzt voraus, dass ein Socket
        mithilfe der connect()-Methode erstellt wurde.

        Parameters
        ----------
        index: int
            Der Index des Sockets worüber die Nachricht gesendet werden soll.
        message: str
            Die Nachricht
        """
        if self._first_msgs[index]:
            ip = self.paired_device_ips[index]
            port = self.paired_device_ports[index]

            self.reset(index)
            self.connect(ip, int(port), index)

        self.sockets[index].send(message.encode('utf-8'))
        self._first_msgs[index] = True

    def wait_for_response(self, index: int, flag: str = '') -> str:
        """
        Sendet eine Nachricht über den Socket. Setzt voraus, dass ein Socket
        mithilfe der connect()-Methode erstellt wurde.

        Parameters
        ----------
        index: int:
            Der Index des Sockets, worüber die Nachricht erwartet wird.
        flag: str, optional:
            default: ''
            Eine Zeichenkette, die die Nachricht zu beinhalten hat.
        """

        while True:
            data = self.sockets[index].recv(1024).decode('utf-8')
            if data:
                if flag != '':
                    return data
                else:
                    if flag in data:
                        return data

    def reset(self, index: Union[int, None] = None) -> None:
        """
        Setzt den Client zurück.
        """

        if index is None:
            for i in range(len(self.sockets)):
                self.sockets[i].close()
                self.sockets[i] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.paired_device_ips[i] = ''
                self.paired_device_ports[i] = ''
        else:
            self.sockets[index].close()
            self.sockets[index] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.paired_device_ips[index] = ''
            self.paired_device_ports[index] = ''

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

    @staticmethod
    def get_all_devices_on_net():
        result = who()  # who(n)
        #for j in range(0, len(result)):
        #    comm = f"\n{result[j][0]} {result[j][1]}\n{result[j][2]} {result[j][3]}\n{result[j][4]} {result[j][5]}\n"
        return result