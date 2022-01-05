from misc.configuration import Configuration

config = Configuration('./data/test_config.json')
config.load_config()

app_config = config.config_dict['app']
settings = {}

print(app_config)

cat = {}


def find_settings_rec(name, category, target_dict, target_key=None, parent_key=None, parent_category=None):
    category[name] = dict()
    for (key, value) in target_dict.items():
        a_result = False
        if key == 'value':
            return True
        elif isinstance(value, dict):
            new_category = {key: dict()}

            category[name] = new_category
            result = find_settings_rec(key, new_category, value, key, target_key, category)
            if result:
                category[target_key] = target_dict
                a_result = True
        if a_result:
            parent_category[target_key] = target_dict


def find_settings(name, target_dict):
    cat[name] = dict()
    for (key, value) in target_dict.items():
        if isinstance(value, dict):
            new_cat = {}
            new_cat[key] = dict()
            cat[name] = new_cat
            for (a_key, a_value) in value.items():
                if isinstance(a_value, dict):
                    new_new_cat = {}
                    new_new_cat[a_key] = dict()
                    new_cat[key] = new_new_cat
                    result = False
                    print(a_value)
                    for (b_key, b_value) in a_value.items():
                        if isinstance(b_value, dict):
                            new_new_new_cat = {}
                            new_new_new_cat[b_key] = dict()
                            new_new_cat[a_key] = new_new_new_cat

                            for (c_key, c_value) in b_value.items():
                                if isinstance(c_value, dict):
                                    new_new_new_new_cat = {}
                                    new_new_new_new_cat[c_value] = dict()
                                    new_new_new_cat[b_key] = new_new_new_new_cat
                                    break
                                elif c_key == 'value':
                                    result = True
                    if result:
                        new_new_cat[a_key] = a_value
                    break
            break

#find_settings('app', app_config)
find_settings_rec('app',  cat, app_config)

config.config_dict = cat
config.save_config()

print(cat)



