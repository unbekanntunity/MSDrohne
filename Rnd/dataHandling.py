def build_data(datatype, datas):
    prefix = f'{datatype}:'
    message = ''

    try:
        if isinstance(datas, list) or isinstance(datas, tuple):
            for data in datas:
                message += data + ','
        else:
            message = datas
    except Exception as e:
        print(message)
        print(str(e))

    return prefix + message


def read_data(message):
    res = message.split(':')

    prefix = res[0]
    value = res[1]

    res_value = value.split(',')
    return prefix, res_value


if __name__ == '__main__':
    print(read_data('WD:1,2'))

