@command(cmd_type='public')
def register_ip(self, connection, address, *args):
    if self.paired_device_ip is None:
        self.paired_device_ip = address
        print(f'Register ip with {address}')
        connection.send('REGISTER|1')
    else:
        connection.send('REGISTER|0')