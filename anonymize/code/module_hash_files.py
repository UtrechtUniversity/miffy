def hash_file(dict_hashes, file):
    str_file = str(file)

    for word, initial in dict_hashes.items():
        str_file = str_file.replace(word, initial)

    return (str_file)