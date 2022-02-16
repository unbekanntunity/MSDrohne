def server_loop(self) -> None:
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

        if c != self.paired_device_connection:
            c.close()