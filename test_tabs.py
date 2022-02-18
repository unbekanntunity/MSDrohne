from test import command


@command(cmd_type='private')
def test(self, connection, address, *agrs):
    print('Private command executed.')


test(None, None, 'public', None, None)