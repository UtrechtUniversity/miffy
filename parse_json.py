def extract_values(obj, keys):
    """Pull all values of specified key from nested JSON."""

    usr = r'^\S{6,}$'
    arr = []

    def extract(obj, arr, keys):
        """Recursively search for values of key in JSON tree."""
        if isinstance(obj, dict):
            print('Found dict')
            for k, v in obj.items():
                print(f'Key {k} and value {v}')
                if v:
                    if isinstance(v, (dict, list)):
                        print(f'Value {v} is list; redo extract')
                        extract(v, arr, keys)
                    elif isinstance(v, str):
                        if any(label.match(k) for label in regex_labels):
                            print(f'Key {k} matches regex labels')
                            print(f'Append value {v}')
                            arr.append(v)
                        elif re.match(usr, k) and check_datetime(v):
                            print(f'Key {k} matches user and value {v} is datetime')
                            arr.append(k)
        elif isinstance(obj, list):
            print('Found list')
            if obj:
                try:
                    names = get_username(obj)
                    print(f'Names {names} found in list; append')
                    arr.append(names)
                except:
                    for item in obj:
                        print(f'Redo extract for {item}')
                        extract(item, arr, keys)
            else:
                print('Seems like {obj} is empty list')
                pass
        return arr

    results = extract(obj, arr, keys)
    return set(results)

def check_datetime(date_text):
    """Check if given string can be converted to a datetime format"""
    try:
        res = dateutil.parser.parse(date_text)
        return res
    except ValueError:
        pass
    try:
        res = datetime.utcfromtimestamp(int(date_text))
        return res
    except ValueError:
        pass


def get_username(my_list):
    """Check if given list contains username"""

    matches = [x for x in my_list if check_datetime(x)]
    usr = r'^\S{6,}$'

    usr_list = []

    if matches:
        for i in my_list:
            if i not in matches:
                try:
                    res = re.match(usr, i)
                    usr_list.append(res.group(0))
                except:
                    pass
    else:
        pass

    return usr_list

labels = [r'search_click',
              r'participants',
              r'sender',
              r'^\S+name',
              r'^\S+friends$',
              r'^\S+users$',
              r'^follow\S+$']

regex_labels = [re.compile(l) for l in labels]