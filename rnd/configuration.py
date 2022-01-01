# *********************** configuration.py **************************
# Klasse für das Laden und Speichern der Konfiguration, die
# in der config.json gespeichert ist
# ********************************************************************

import json


class Configuration(object):
    def __init__(self, file_path, load_at_init=False):
        self.file_path = file_path
        self.config_dict = {}

        if load_at_init:
            self.load_config()

    def load_config(self) -> None:
        string = ''

        with open(self.file_path, 'r') as f:
            lines = f.readlines()
            string = string.join(lines)
            self.config_dict = json.loads(string)

    def save_config(self) -> None:
        with open(self.file_path, 'w') as f:
            jsonstr = json.dumps(self.config_dict, indent=4, sort_keys=True)
            f.write(jsonstr)


if __name__ == '__main__':
    con = Configuration('../data/config.json')
    con.load_config()

    con.config_dict['tick'] = 10
    con.save_config()
