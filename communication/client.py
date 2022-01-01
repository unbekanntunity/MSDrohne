from datetime import datetime
from jnius import autoclass

import socket

# Konstanten
SIZE = 1024
TIME = 10


class BluetoothClient(object):
    def __init__(self):
        self.socket = None
        self.paired_device_name = ''

    def wait_for_response(self, flag=''):
        time_started = datetime.now()
        while True:
            if datetime.now().second - TIME is time_started:
                print("Timeout!")
                return

            data = self.socket.recv(1024)
            if data:
                if flag != '':
                    if str.encode(flag, 'UTf-8') in data:
                        return data
                else:
                    return data

    def reset(self):
        self.socket = None


class AndroidBluetoothClient(BluetoothClient):
    def __init__(self):
        super(BluetoothClient, self).__init__()
        self.BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
        self.BluetoothDevice = autoclass('android.bluetooth.BluetoothDevice')
        self.BluetoothSocket = autoclass('android.bluetooth.BluetoothSocket')
        self.UUID = autoclass('java.util.UUID')

        self.send_stream = None
        self.recv_stream = None

    def reset(self):
        self.send_stream = None
        self.recv_stream = None
        super(AndroidBluetoothClient, self).reset()

    def create_socket_stream(self, name):
        if self.has_paired_devices():
            paired_devices = self.BluetoothAdapter.getDefaultAdapter().getBondedDevices().toArray()
            for device in paired_devices:
                if device.getName() == name:
                    self.socket = device.createRfcommSocketToServiceRecord(
                        self.UUID.fromString("00001101-0000-1000-8000-00805F9B34FB"))
                    self.recv_stream = self.socket.getInputStream()
                    self.send_stream = self.socket.getOutputStream()
                    self.paired_device_name = name
                    break
            if self.socket is not None:
                self.socket.connect()

    def has_paired_devices(self):
        paired_devices = self.BluetoothAdapter.getDefaultAdapter().getBondedDevices().toArray()
        return paired_devices is not None and len(paired_devices) != 0


class WLANClient(object):
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.paired_device_ip = ''
        self.paired_device_port = ''

    def connect(self, address, port):
        self.socket.connect((address, port))
        self.paired_device_ip = address
        self.paired_device_port = port

    def send_message(self, message):
        self.socket.send(message.encode())
        data = self.socket.recv(1024).decode()
        print(data)

    def wait_for_response(self, only_paired_device=False):
        while True:
            data = self.socket.recv(1024)
            if data:
                if only_paired_device:
                    if str.encode(self.paired_device_ip, 'UTF-8') in data:
                        return data
                else:
                    return data

    def reset(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.paired_device_ip = ''
        self.paired_device_port = ''

    @staticmethod
    def get_ip_address():
        h_name = socket.gethostname()
        return socket.gethostbyname(h_name)
