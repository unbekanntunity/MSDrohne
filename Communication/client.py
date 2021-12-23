from datetime import datetime

from Rnd.dataHandling import *

import socket

PORT = 9192
IP_ADDRESS = "192.168.252.11"

SIZE = 1024
TIME = 10


class BluetoothClient(object):
    def __init__(self):
        self.socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)

    def connect(self, address):
        self.socket.connect((address, PORT))

    def send_message_bluetooth(self, msg):
        self.socket.send(msg)

    def wait_for_response(self):
        time_started = datetime.now()
        while True:
            if datetime.now().second - TIME is time_started:
                print("Timeout!")
                return

            data = self.socket.recv(1024)
            if data:
                return data

    def close(self):
        self.socket.close()

    def is_connected(self):
        return self.socket is not None


class WLANClient(object):
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        self.socket.connect((IP_ADDRESS, PORT))

    def send_message(self, message):
        self.socket.send(message.encode())  # Baut und sendet eine Nachricht
        data = self.socket.recv(1024).decode()  # Erhält die Antwort vom Server
        print(data)

    def wait_for_response(self):
        while True:
            data = self.socket.recv(1024)
            if data:
                return data

    def close(self):
        self.socket.close()


def bluetooth_list(os_system):
    print("start searching...")

    devices = []
    if "Android" or "Windows" in os_system:
        devices = [("s", "1"), ("a", "12"), ("aw", "100"),
                   ]
        pass
    return devices



