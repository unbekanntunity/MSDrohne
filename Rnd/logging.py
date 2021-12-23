import time
from datetime import datetime, timedelta
from enum import Enum


class LoggingOutput(Enum):
    FILE = 1
    CONSOLE = 2


class LoggingLevel(Enum):
    INFORMATION = 1
    WARNING = 2
    ERROR = 3


class LoggerOptions(object):
    def __init__(self, path=""):
        self.path = ""
        self.output = []
        self.clear_interval_sec = 0

        self.set_path(path)

    def set_path(self, path):
        self.path = path

    def add_output(self, output: LoggingOutput):
        if output not in self.output:
            self.output.append(output)

    def remove_output(self, output: LoggingOutput):
        if output in self.output:
            self.output.remove(output)

    def set_clear(self, seconds):
        self.clear_interval_sec = seconds


class Logger(object):
    def __init__(self, options: LoggerOptions):
        self.options = options

        self.prefix = {
            LoggingLevel.INFORMATION : "[Information] ",
            LoggingLevel.WARNING : "[Warning] ",
            LoggingLevel.ERROR : "[Error] "
        }

        self.queue = []
        self.busy = False

    def get_last_log(self):
        with open(self.options.path, "r") as f:
            content = f.readlines()

        if '\n' in content:
            content.remove('\n')

        with open(self.options.path, "w") as f:
            f.writelines(content)

        if len(content) == 0:
            return None

        content.reverse()
        last_log = [[], [], []]

        for line in content:
            if line != '\n':
                last_log = line
                break

        size = len(last_log)
        idx_list = [idx + 1 for idx, val in
                    enumerate(last_log) if val == ']']
        if len(idx_list) > 0:
            res = [last_log[i: j] for i, j in zip([0] + idx_list, idx_list +
                                                  ([size] if idx_list[-1] != size else []))]

            res[0] = res[0].replace('[', '').replace(']', '')
            res[1] = res[1].replace(' [', '').replace(']', '')
            res[2] = res[2].replace(' [', '').replace(']', '')
        else:
            res = None
        return res

    def log(self, source, content, level: LoggingLevel):
        date_format = '%d-%m-%Y %H:%M:%S'
        last_log = self.get_last_log()
        req = self.options.clear_interval_sec != 0 and last_log is not None
        if req and datetime.strptime(last_log[1], date_format) + timedelta(self.options.clear_interval_sec) < datetime.now():
            self.clear()

        source_tag = f'[{source}] '
        current = f'[{datetime.now().strftime(date_format)}] '
        level_tag = self.prefix[level]
        content = Logger.replace_umlauts(content)

        message = source_tag + current + level_tag + content + '\n'

        if self.busy is False:
            self.busy = True
        else:
            return

        if LoggingOutput.FILE in self.options.output:
            with open(self.options.path, 'a') as f:
                f.write(message)

        if LoggingOutput.CONSOLE in self.options.output:
            print('console:' + message)

        self.busy = False

    def clear(self):
        with open(self.options.path, 'r+') as f:
            f.truncate(0)

    @staticmethod
    def replace_umlauts(message):
        new_str = ""
        umlauts = {
            'Ä': 'Ae',
            'Ö': 'Oe',
            'Ü': 'Ue',
            'ä': 'ae',
            'ö': 'oe',
            'ü': 'ue',
            'ß': 'ss'
        }

        for char in message:
            if char in umlauts:
                new_str += umlauts[char]
            else:
                new_str += char

        return new_str


def demo():
    options = LoggerOptions('./Data/log.txt')
    options.add_output(LoggingOutput.FILE)
    options.add_output(LoggingOutput.CONSOLE)
    options.set_clear(1)

    logger = Logger(options)
    print(logger.get_last_log())


if __name__ == "__main__":
    demo()
