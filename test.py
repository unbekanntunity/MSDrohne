import network
import ubinascii

from drohnev2.decorators import command

import gc

gc.collect()

from time import sleep

try:
    import usocket as socket
except:
    import socket

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
            'LJ': 0
        }

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

    def server_loop(self):
        while 1:  # Endlosschleife
            c, addr = self.server.accept()  # Anfrage entgegennehmen
            print('\nGot a connection from %s' % str(addr))
            # c ist ein bytes-Objekt und muss als string decodiert werden
            # damit string-Methoden darauf angewandt werden koennen.
            request = c.recv(1024).decode("utf-8")
            print(f'data detected: {request}')

            command_name, args = self.extract_public_command(request)
            self.execute_public_command(command_name, c, *args)

            if self.validate_data(c, addr):
                self.process_data(c, addr, request)
                c.send(f'Received data: {request}\n\n')
            c.close()

    def validate_data(self, connection, address):
        if self.paired_device_ip is not None:
            result = self.paired_device_ip == str(address)
            if not result:
                connection.send('Permission denied.')
        else:
            return False

    def process_data(self, connection, address, data):
        if 'CMD' in data:
            command_name, args = self.extract_private_command(data)
            print(f'command detected: {command_name}, {args}')
            self.execute_private_command(command_name, connection, address, *args)
            # globals()[command_name](connection, *args)
        elif 'DATA' in data:
            result = self.extract_data()
            if result[0]:
                self.data_container[result[1]] = result[2]

    def extract_data(self, data):
        data_split = data.split(SEPARATOR)

        data_key = data_split[0]
        data_value = data_split[1]
        expected_data = data_key in self.data_container.keys()

        return (expected_data, data_key, data_value)

    def extract_public_command(self, data):
        command_split = data.split(SEPARATOR)
        command_name = command_split[1].lower()
        args = []
        if len(command_split) > 2:
            args = command_split[2:]

        return (command_name, args)

    def execute_public_command(self, name, connection, *args):
        if hasattr(Wlan_Server, name):
            getattr(Wlan_Server, name)(self, connection, 'public', '', *args)
        else:
            connection.send('Command not found.')

    # CMD|name|arg1|arg2|....
    def extract_private_command(self, data):
        command_split = data.split(SEPARATOR)
        command_name = command_split[1].lower()
        args = []
        if len(command_split) > 2:
            args = command_split[2:]

        return (command_name, args)

    def execute_private_command(self, name, connection, address, *args):
        if hasattr(Wlan_Server, name):
            getattr(Wlan_Server, name)(self, connection, 'private', address, *args)
        else:
            connection.send('Command not found.')

    @command(cmd_type='public')
    def reset(self, connection, passed_type, *args):
        connection.close()
        self.socket.close()
        setup()

    @command(cmd_type='private')
    def set_config(self, connection, passed_type, *args):
        try:
            config_str = args[0]
            self.config.save_config_with_jsonstr(config_str)
            self.config.load_config()
            connection.send('CONFIG|1')
        except Exception as e:
            connection.send('CONFIG|0')

    @command(cmd_type='public')
    def register_ip(self, connection, passed_type, *args):
        if self.paired_device_ip is None:
            self.paired_device_ip = args[0]
            print(f'Register ip with {args[0]}')
            connection.send('REGISTER|1')
        else:
            connection.send('REGISTER|0')

    @command(cmd_type='private')
    def unregister_ip(self, connection, passed_type, address, *args):
        if self.paired_device_ip is not None and self.paired_device_ip == str(address):
            self.paired_device_ip = None
            print(f'Logout ip with {args[0]}')
            connection.send('UNREGISTER|1')
        else:
            connection.send('UNREGISTER|0')

    @command(cmd_type='private')
    def get_sensor_data(self, connection, passed_type, address, *args):
        if self.paired_device_ip is not None and self.paired_device_ip == str(address):
            self.send_sensor_data(c)

    @command(cmd_type='private')
    def get_conn_data(self, connection, passed_type, address, *args):
        if self.paired_device_ip is not None and self.paired_device_ip == str(address):
            self.send_conn_status(c)

    def send_sensor_data(self, c):
        try:
            message = 'GEODATA|1|1|1|1'
            print('Sensor data sent')
            c.send(message.encode())

    except OSError as e:
    pass


def send_conn_status(self, c):
    try:
        message = 'CONDATA|100'
        print('Wlan data sent')
        c.send(message.encode())
    except OSError as e:
        pass


def hexMac(byteMac):
    """
    Die Funktion hexMAC nimmt die MAC-Adresse im Bytecode entgegen und
    bildet daraus einen String für die Rückgabe
    """
    macString = ""
    for i in range(0, len(byteMac)):  # Für alle Bytewerte
        macString += hex(byteMac[i])[2:]  # vom String ab Position 2 bis Ende
        if i < len(byteMac) - 1:  # Trennzeichen bis auf das letzte Byte
            macString += "-"
    return macString


def activate_nic():
    # Netzwerk-Interface-Instanz erzeugen und ESP32-Stationmodus aktivieren;
    # möglich sind network.STA_IF und network.AP_IF beide wie in LUA oder
    # AT-based oder Adruino-IDE ist in MicroPython nicht möglich
    nic = network.WLAN(network.STA_IF)  # Constructor
    nic.active(True)

    # binäre MAC-Adresse abrufen und in ein Hex-Tupel umgewandelt ausgeben
    MAC = nic.config('mac')
    myMac = hexMac(MAC)
    print("STATION MAC: \t" + myMac + "\n")
    return nic


def connect(nic, siD="pasteur-wlan", password="03Y01pasgymbln#12") -> (bool, Any, Any):
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
                return (false, None, None)

            print(connectStatus[nic.status()])
            tries += 1
            sleep(1)
    print("Erfolgreicher Verbindungsstatus: ", connectStatus[nic.status()])
    STAconf = nic.ifconfig()
    print("STA-IP:\t\t", STAconf[0], "\nSTA-NETMASK:\t", STAconf[1], "\nSTA-GATEWAY::\t", STAconf[2], "\n", "\n",
          sep='')

    return (True, STAconf, nic)


def scan(nic):
    """
    Scannt die Funkumgebung nach vorhandenen Accesspoints und liefert
    deren Kennung (SSID) sowie die Betriebsdaten zurück.
    """

    # Gib eine Liste der umgebenden APs aus
    networks_raw = nic.scan()
    autModus = ["open", "WEP", "WPA-PSK", "WPA2-PSK", "WPA/WPA2-PSK"]

    networks_decoded = []
    for AP in networks_raw:
        decoded = (AP[0].decode("utf-8"), ubinascii.hexlify(AP[1], "-").decode("utf-8"), AP[2], AP[3], AP[4], AP[5])
        networks_decoded.append(decoded)
    return networks_decoded

