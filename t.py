import network
import ubinascii

from drohnev2.decorators import command
from drohnev2.startup import startup

import gc

gc.collect()

from time import sleep

try:
    import usocket as socket
except:
    import socket

import random

SEPARATOR = '|'

# Die Dictionarystruktur (dict) erlaubt später die Klartextausgabe
# des Verbindungsstatus anstelle der Zahlencodes
connectStatus = {
    1000: "STAT_IDLE",
    1001: "STAT_CONNECTING",
    1010: "STAT_GOT_IP",
    202: "STAT_WRONG_PASSWORD",
    201: "NO AP FOUND"
}


class Wlan_Server(object):
    def __init__(self, nic):
        self.nic = nic

        self.server = None
        self.paired_device_ip = None

        self.data_container = {
            'RJ': 0,
            'LJ': 0,
            'Hover_mode': False
        }

        self._public_commands = [self.register_ip]
        self._private_commands = [self.reset, self.set_config, self.set_hover_mode, self.unregister_ip,
        self.get_conn_data, self.get_sensor_data]

    def create_server(self) -> bool:
        try:
            print("Fordere Server-Socket an")
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server.bind(('', 9192))  # an lokale IP und Portnummer 9192 binden
            self.server.listen(5)  # Akzeptiere bis zu 5 eingehende Anfragen
            STAconf = self.nic.ifconfig()
            print("Empfange Anfragen auf ", STAconf[0], ":", 9192, sep='')
            return True
        except Exception as e:
            print(e)
            return False

    def server_loop(self) -> None:
        while True:
            print('\nSearch for requests')
            c, addr = self.server.accept()  # Anfrage entgegennehmen
            print('\nGot a connection from %s' % str(addr))
            # c ist ein bytes-Objekt und muss als string decodiert werden
            # damit string-Methoden darauf angewandt werden koennen.
            request = c.recv(1024).decode("utf-8")
            print(f'data detected: {request}')

            if 'CMD' in request:
                command_name, args = self.extract_command(request)
                if command_name is not None:
                    print(f'Public command detected: {command_name}, {args}')
                    self.execute_public_command(command_name, c, addr, *args)
            if self.validate_data(c, addr):
                if 'CMD' in request:
                    command_name, args = self.extract_command(request)
                    if command_name is not None:
                        print(f'Private command detected: {command_name}, {args}')
                        self.execute_private_command(command_name, c, addr, *args)
                elif 'DATA' in request:
                    result = self.extract_data(request)
                    if result[0]:
                        print(f'Data detected: {result[1]}: {result[2]}')
                        self.data_container[result[1]] = result[2]
            c.close()
            print('Connection closed')

    def validate_data(self, connection, address):
        if self.paired_device_ip is not None:
            result = self.paired_device_ip[0] == address[0]
            if not result:
                connection.send('Permission denied.')
                return False
            return True
        else:
            return False

    def extract_data(self, data):
        data_split = data.split(SEPARATOR)

        data_key = data_split[0]
        data_value = data_split[1]
        expected_data = data_key in self.data_container.keys()

        return expected_data, data_key, data_value

    # CMD|name|arg1|arg2|....
    def extract_command(self, data):
        command_split = data.split(SEPARATOR)

        if len(command_split) >= 2:
            command_name = command_split[1].lower()
            args = []
            if len(command_split) > 2:
                args = command_split[2:]
            return command_name, args
        return None, None

    def execute_public_command(self, name, connection, address, *args):
        if name in self._public_commands:
            index = self._public_commands.index(name)
            self._public_commands[index](connection, address, *args)
        else:
            print('Command not found.')

    def execute_private_command(self, name, connection, address, *args):
        if name in self._public_commands:
            index = self._public_commands.index(name)
            self._private_commands[index](connection, address, *args)
        else:
            print('Command not found.')

    def reset(self, connection, address, *args):
        self.server.close()
        startup()

    def set_config(self, connection, address, *args):
        try:
            config_str = args[0]
            self.config.save_config_with_jsonstr(config_str)
            self.config.load_config()
            connection.send('CONFIG|1')
        except Exception as e:
            connection.send('CONFIG|0')

    def set_hover_mode(self, connection, address, *args):
        if isinstance(args[0], bool):
            self.data_container['Hover_mode'] = args[0]

    def register_ip(self, connection, address, *args):
        if self.paired_device_ip is None:
            self.paired_device_ip = address
            print(f'Register ip with {address}')
            connection.send('REGISTER|1')
        else:
            connection.send('REGISTER|0')

    def unregister_ip(self, connection, address, *args):
        if self.paired_device_ip is not None and self.paired_device_ip == str(address):
            self.paired_device_ip = None
            print(f'Logout ip with {args[0]}')
            connection.send('UNREGISTER|1')
        else:
            connection.send('UNREGISTER|0')

    def get_sensor_data(self, connection, address, *args):
        try:
            data = []
            for i in range(4):
                data.append(random.randint(1, 10))

            message = f'GEODATA|{data[0]}|{data[1]}|{data[2]}|{data[3]}'
            connection.send(message.encode())
            print('Sensor data sent')
        except Exception as e:
            print(f'Error while trying sending sensor data {e}')

    def get_conn_data(self, connection, address, *args):
        try:
            number = random.randint(1, 100)
            number = 1
            message = f'CONDATA|{number}'
            connection.send(message.encode())
            print(f'Wlan data sent: {message}')
        except Exception as e:
            print(f'Error while trying sending conn data {e}')


def hex_mac(byte_mac):
    mac_string = ""
    for i in range(0, len(byte_mac)):  # Für alle Bytewerte
        mac_string += hex(byte_mac[i])[2:]  # vom String ab Position 2 bis Ende
        if i < len(byteMac) - 1:  # Trennzeichen bis auf das letzte Byte
            mac_string += "-"
    return mac_string


def activate_nic():
    nic = network.WLAN(network.STA_IF)  # Constructor
    nic.active(True)
    print(f'Hostname: {nic.config("dhcp_hostname")}')

    # binäre MAC-Adresse abrufen und in ein Hex-Tupel umgewandelt ausgeben
    MAC = nic.config('mac')
    myMac = hex_mac(MAC)
    print("STATION MAC: \t" + myMac + "\n")
    return nic


def connect(nic, siD, password) -> (bool, Any, Any):
    print('name: ' + siD)
    print('password: ' + password)
    # zeige_ap_liste(nic)
    max_tries = 10
    tries = 0
    # Verbindung mit AP im lokalen Netzwerk aufnehmen, falls noch nicht verbunden
    if not nic.isconnected():
        # Zum AP im lokalen Netz verbinden und Status anzeigen
        nic.connect(siD, password)

        # warten bis die Verbindung zum Accesspoint steht
        while nic.status() != network.STAT_GOT_IP:
            if tries == max_tries:
                return False, None, None

            print(connectStatus[nic.status()])
            tries += 1
            sleep(1)
    print("Erfolgreicher Verbindungsstatus: ", connectStatus[nic.status()])
    STAconf = nic.ifconfig()
    print("STA-IP:\t\t", STAconf[0], "\nSTA-NETMASK:\t", STAconf[1], "\nSTA-GATEWAY::\t", STAconf[2], "\n", "\n",
          sep='')

    return True, STAconf, nic


def scan(nic):
    """
    Scannt die Funkumgebung nach vorhandenen Accesspoints und liefert
    deren Kennung (SSID) sowie die Betriebsdaten zurück.
    """
    # Gib eine Liste der umgebenden APs aus
    networks_raw = nic.scan()

    networks_decoded = []
    for AP in networks_raw:
        decoded = (AP[0].decode("utf-8"), ubinascii.hexlify(AP[1], "-").decode("utf-8"), AP[2], AP[3], AP[4], AP[5])
        networks_decoded.append(decoded)
    return networks_decoded



