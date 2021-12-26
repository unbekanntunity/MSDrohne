from datetime import datetime

from jnius import autoclass

PORT = 9192
IP_ADDRESS = "192.168.252.11"

SIZE = 1024
TIME = 10


class BluetoothClient(object):
    def __init__(self):
        self.socket = None
        self.paired_device_name = ''

    def wait_for_response(self):
        time_started = datetime.now()
        while True:
            if datetime.now().second - TIME is time_started:
                print("Timeout!")
                return

            data = self.socket.recv(1024)
            if data:
                return data


class AndroidBluetoothClient(BluetoothClient):
    def __init__(self):
        super(BluetoothClient, self).__init__()
        self.BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
        self.BluetoothDevice = autoclass('android.bluetooth.BluetoothDevice')
        self.BluetoothSocket = autoclass('android.bluetooth.BluetoothSocket')
        self.UUID = autoclass('java.util.UUID')

        self.send_stream = None
        self.recv_stream = None

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



