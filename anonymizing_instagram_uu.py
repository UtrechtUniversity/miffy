import argparse
from pathlib import Path
import json
import os
import re
from zipfile import ZipFile

import pandas as pd
from anonymize import Anonymize


def _main_folder():
    pass

def _main_usernames(n):
    print("Extracting all sensitive information:")

    # CREATE PATHS TO FILES
    json_file_users = _main_files(n)[2] + '\\' + 'connections.json'
    json_file_user = _main_files(n)[2] + '\\' + 'profile.json'
    json_file_like = _main_files(n)[2] + '\\' + 'likes.json'
    json_file_seen = _main_files(n)[2] + '\\' + 'seen_content.json'
    json_file_com = _main_files(n)[2] + '\\' + 'comments.json'
    json_file_saved = _main_files(n)[2] + '\\' + 'saved.json'
    json_file_search = _main_files(n)[2] + '\\' + 'searches.json'
    json_file_account = _main_files(n)[2] + '\\' + 'account_history.json'

    json_file_mes = _main_files(n)[2] + '\\' + 'messages.json'
    json_file_media = _main_files(n)[2] + '\\' + 'media.json'
    json_file_ac = _main_files(n)[2] + '\\' + 'account_history.json'

    # FIND ALL USERNAMES IN PROFILE + CONNECTIONS
    # Load profile.json to get username of user
    with open(json_file_user, encoding="utf8") as json_user:
        user = json.load(json_user)

    user = pd.DataFrame.from_dict(user,
                                  orient='index').T

    # Load connections.json to get username of all connections
    with open(json_file_users, encoding="utf8") as json_users:
        connections = json.load(json_users)

    connections = pd.DataFrame.from_dict(connections,
                                         orient='index').T

    connections = connections.index.values.tolist()

    # Create scramble function
    from random import shuffle

    def shuffle_word(word):
        word = list(word)
        shuffle(word)
        return ''.join(word)

    # Create dictionary with original username as key
    dictionary = {}
    dictionary = {user['username'][0]: ('__' + shuffle_word(user['username'][0]))}

    for name in connections:
        new = {name: ('__' + shuffle_word(name))}
        dictionary.update(new)

    # FIND USERNAMES IN OTHER FILES
    # Saved media
    if (os.path.exists(json_file_saved)):

        with open(json_file_saved, encoding="utf8") as json_saved:
            saved = json.load(json_saved)

        users = pd.DataFrame(saved['saved_media'])[1]

    else:
        users = []

    # Likes
    if (os.path.exists(json_file_like)):

        with open(json_file_like, encoding="utf8") as json_likes:
            likes = json.load(json_likes)

        user_like = pd.DataFrame(likes['media_likes'])[1]
        user_like = user_like.append(pd.DataFrame(likes['comment_likes'])[1])

    else:
        user_like = []

    # Seen content
    if (os.path.exists(json_file_seen)):
        with open(json_file_seen, encoding="utf8") as json_seen:
            seen = json.load(json_seen)

        user_seen = pd.DataFrame(seen['chaining_seen'])['username']
        user_seen = user_seen.append(pd.DataFrame(seen['ads_seen'])['author'])
        user_seen = user_seen.append(pd.DataFrame(seen['posts_seen'])['author'])
        user_seen = user_seen.append(pd.DataFrame(seen['videos_watched'])['author'])
    else:
        user_seen = []

    # Search media
    if (os.path.exists(json_file_search)):

        with open(json_file_search, encoding="utf8") as json_search:
            search = json.load(json_search)

        user_search = pd.DataFrame(search)['search_click']
    else:
        user_search = []

    # Media comments
    if (os.path.exists(json_file_com)):

        with open(json_file_com, encoding="utf8") as json_comments:
            comments = json.load(json_comments)

        user_com = pd.DataFrame(comments['media_comments'])[2]
    else:
        user_com = []

    # Messages
    if (os.path.exists(json_file_mes)):

        with open(json_file_mes, encoding="utf8") as json_messages:
            message = json.load(json_messages)

        messages = pd.DataFrame.from_dict(message[1],
                                          orient='index').T
        for i in range(0, len(message)):
            messages = messages.append(pd.DataFrame.from_dict(message[i],
                                                              orient='index').T)

        messages = pd.DataFrame(messages['conversation'].dropna().values.tolist())
        user_mes = messages['sender']
    else:
        user_mes = []

    # Merge all usernames and add most comon first names
    users = users.append(user_seen)
    users = users.append(user_like)
    users = users.append(user_search)
    users = users.append(user_com)
    users = users.append(user_mes)
    users = set(users)

    for name in users:
        if name in dictionary:
            next
        else:
            dictionary.update({name: ('__' + shuffle_word(name))})

    # FIND FIRST NAMES
    # Load profile.json to get name of user
    with open(json_file_account, encoding="utf8") as json_user:
        name = json.load(json_user)

    if 'registration_info' in name:
        dictionary.update({name['registration_info']['registration_username']: dictionary[user['username'][0]]})
    dictionary.update({user['email'][0]: dictionary[user['username'][0]]})
    dictionary.update({user['name'][0]: dictionary[user['username'][0]]})

    # Find firstnames in other files
    firstnames = pd.DataFrame(open('Firstnames_NL.lst').read().split('\n'))[0]
    firstnames = firstnames.drop(firstnames.index[len(firstnames) - 1])

    # Add firstnames used in messages
    with open(json_file_mes, encoding="utf8") as json_messages:
        message = json.load(json_messages)
    message = str(message)

    # Add firstnames used in media
    with open(json_file_media, encoding="utf8") as json_messages:
        media = json.load(json_messages)
    media = str(media)

    # Add firstnames used in comments
    comments = str(comments)

    found_names = []
    round = 1

    print("Looking for first names...")
    for name in firstnames:
        # print("Looking for first names: " + f'{(round/len(firstnames)) * 100}' + '%')
        if name.lower() in message.lower():
            found_names.append(name)
        elif name.lower() in comments.lower():
            found_names.append(name)
        elif name.lower() in media.lower():
            found_names.append(name)
        round = round + 1

    for name in found_names:
        dictionary.update({name: '__' + shuffle_word(name)})

    # FIND PHONE NUMBERS
    with open(json_file_ac, encoding="utf8") as json_user:
        account = json.load(json_user)
    account = str(account)

    inp = message + media + comments + account

    phone = re.findall("(?<!\d)\d{10}(?!\d)",
                       inp)

    phone2 = []
    if len(re.findall("[0-9]{2}\-[0-9]{8}", inp)) > 0:
        phone2 = re.findall("[0-9]{2}\-[0-9]{8}", inp)

    print("Looking for phone numbers...")
    phone_dic = []
    for i in range(len(phone)):
        if phone[i].startswith('06'):
            phone_dic.append(phone[i])
    for i in range(len(phone2)):
        if phone2[i].startswith('06'):
            phone_dic.append(phone2[i])

    for number in phone_dic:
        dictionary.update({number: '__phonenumber'})

    # FIND EMAIL ADRESSES
    regex = re.compile(("([a-z0-9!#$%&'*+\/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+\/=?^_`"
                        "{|}~-]+)*(@|\sat\s)(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(\.|"
                        "\sdot\s))+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)"))

    mail = re.findall(regex, inp)

    print("Looking for email adresses...")
    mail_dic = []
    for i in range(len(mail)):
        if mail[i][0].endswith('.com'):
            mail_dic.append(mail[i][0].replace("'", ""))
        if mail[i][0].endswith('.nl'):
            mail_dic.append(mail[i][0].replace("'", ""))

    for mail in mail_dic:
        if mail in dictionary:
            next
        else:
            dictionary.update({mail: '__emailadress'})

    # RETURN DICTIONARY
    if 'instagram' in dictionary:
        del dictionary['instagram']

    return (dictionary)


def unpack():
    """Extract data download packages, i.e., zipfiles, to new folder """

    dir = Path.cwd()

    zip_files = dir.glob('*.zip')

    for i in zip_files:
        print(f'Extracting all files from {i}')
            #'Extracting all files from ' + f'{_main_files(n)[1]}' + ' (' + f'{n + 1}' + ' of ' + f'{len(_main_folder())}' + ' packages)')

        new_folder = i.stem.split('_')[0]

        with ZipFile(i, 'r') as zip:
            print(f'Extracting to {new_folder}')
            zip.extractall(new_folder)
            print('Done!')


def main_key():
    for n in range(len(_main_folder())):
        df = pd.DataFrame(list(_main_usernames(n).items()))
        df = df.rename(columns={0: 'id', 1: 'subt'})

        id = re.sub(r"\d+", "", _main_folder()[n])
        id = id.replace("_.zip", "")
        subt = df['subt'][0]

        df.to_csv('keys_' + f'{id}' + '.csv', index=False, encoding='utf-8')

        print('Anonymizing ' + f'{id}' + '\'s instagram data.')

        anonymize_csv = Anonymize('keys_' + f'{id}' + '.csv', use_word_boundaries=True)
        anonymize_csv.substitute(_main_files(n)[2])

        print('Done!')
        print('The anonymized data is saved in the following folder: ' + f'{_main_files(n)[0]}' + '\\' + f'{subt}')


if __name__ == '__main__':

    unpack()

    # main_key()