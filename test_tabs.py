import datetime


def add_message(message, log_level='info'):
    timestamp = datetime.datetime.now().strftime("%m/%d/%Y | %H:%M:%S")

    terminal_log = f'[{timestamp}] [{log_level}] {message}'
    return terminal_log


if __name__ == '__main__':
    print(add_message('adasd'))