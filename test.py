def server_loop(self) -> None:
    while True:
        print('\nSearch for requests')
        c, addr = self.server.accept()  # Anfrage entgegennehmen
        print('\nGot a connection from %s' % str(addr))
        # c ist ein bytes-Objekt und muss als string decodiert werden
        # damit string-Methoden darauf angewandt werden koennen.
        request = c.recv(1024).decode("utf-8")
        print(f'data detected: {request}')

        if 'CMD' in data:
            command_name, args = self.extract_command(request)
            if command_name is not None:
                print(f'Public command detected: {command_name}, {args}')
                self.execute_command(command_name, 'public', c, addr, *args)
        elif self.validate_data(c, addr)
            self.process_data(c, addr, request)
        c.close()
        print('Connection closed')
