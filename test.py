from misc.configuration import Configuration

config = Configuration('./data/config.json')
config.load_config()

print(config.config_dict)