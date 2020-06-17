import argparse
from pathlib import Path
import json
import os
import re
from zipfile import ZipFile
import pandas as pd
from anonymize import Anonymize
from random import shuffle


def unpack(input_folder:str, output_folder:str):
    """Extract data download packages, i.e., zipfiles, to new folder """

    dir = Path(input_folder)

    zip_files = dir.glob('*.zip')

    for i in zip_files:
        print(f'Extracting all files from {i}')

        new_folder = Path(output_folder, i.stem.split('_')[0])

        with ZipFile(i, 'r') as zip:
            print(f'Extracting to {new_folder}')
            zip.extractall(new_folder)
            print('Done!')


def mingle(word):
    word = list(word)
    
    number = []
    for i in word:
        if isinstance(i, int):
            next
        if i.isalpha():
            number.append(ord(i)) 
    
    letters = []
    for i in range(len(number)):
        letter = chr((number[i]+i))
        if letter.isalpha(): 
            letters.append(letter)
        else:
            letters.append(number[i])
            
    numbers = []
    for i in number:
        numbers.append(i - 96)
        
    new = []
    round = 0
    for i in range(len(numbers)):
        round = round + 1
        if round == 1:
            new.append('__')
        elif round != len(numbers):
            if isinstance(letters[i], int):
                next
            elif letters[i].isalpha():
                new.append(letters[i])
        else:
            new.append(f'{numbers[i]}')
            
    return ''.join(new)


def usernames(input_folder:str, output_folder:str):
    """Search all files on explicit (user)names, email adresses and phone numbers """

    print("Extracting all sensitive information from unpacked files.")

    # CREATE PATHS TO FILES
    files = ['profile', 'connections', 'saved', 'likes', 'seen_content', 'searches', 'comments', 'messages', 'account_history', 'media', 'contacts', 'uploaded_contacts']
    dir = Path(output_folder)
    folders = dir.glob('*')
    
    for folder in folders:
        
        json_files = []
        for file in files:
            json_files.append(Path(folder, file+'.json'))
    
    
        # FIND ALL USERNAMES IN PROFILE + CONNECTIONS
        # Load profile.json to get username of user
        with open(json_files[0], encoding="utf8") as json_user:
            user = json.load(json_user)
    
        user = pd.DataFrame.from_dict(user,
                                      orient='index').T
    
        # Load connections.json to get username of all connections
        with open(json_files[1], encoding="utf8") as json_users:
            connections = json.load(json_users)
    
        connections = pd.DataFrame.from_dict(connections,
                                             orient='index').T
    
        connections = connections.index.values.tolist()
    
        # Create dictionary with original username as key
        dictionary = {}
        username = user['username'][0]
        dictionary = {username: mingle(f'{username}')}
    
        for name in connections:
            new = {name: mingle(name)}
            dictionary.update(new)
            
            
        # FIND USERNAMES IN OTHER FILES
        # Saved media
        if (os.path.exists(json_files[2])):
    
            with open(json_files[2], encoding="utf8") as json_saved:
                saved = json.load(json_saved)
    
            users = pd.DataFrame(saved['saved_media'])[1]
    
        else:
            users = []
    
        # Likes
        if (os.path.exists(json_files[3])):
    
            with open(json_files[3], encoding="utf8") as json_likes:
                likes = json.load(json_likes)
    
            user_like = pd.DataFrame(likes['media_likes'])[1]
            user_like = user_like.append(pd.DataFrame(likes['comment_likes'])[1])
    
        else:
            user_like = []
    
        # Seen content
        if (os.path.exists(json_files[4])):
            with open(json_files[4], encoding="utf8") as json_seen:
                seen = json.load(json_seen)
    
            user_seen = pd.DataFrame(seen['chaining_seen'])['username']
            user_seen = user_seen.append(pd.DataFrame(seen['ads_seen'])['author'])
            user_seen = user_seen.append(pd.DataFrame(seen['posts_seen'])['author'])
            user_seen = user_seen.append(pd.DataFrame(seen['videos_watched'])['author'])
        else:
            user_seen = []
    
        # Search media
        if (os.path.exists(json_files[5])):
    
            with open(json_files[5], encoding="utf8") as json_search:
                search = json.load(json_search)
    
            user_search = pd.DataFrame(search)['search_click']
        else:
            user_search = []
    
        # Media comments
        if (os.path.exists(json_files[6])):
    
            with open(json_files[6], encoding="utf8") as json_comments:
                comments = json.load(json_comments)
    
            user_com = pd.DataFrame(comments['media_comments'])[2]
        else:
            user_com = []
    
        # Messages
        if (os.path.exists(json_files[7])):
    
            with open(json_files[7], encoding="utf8") as json_messages:
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
                dictionary.update({name: mingle(name)})
    
    
        # FIND FIRST NAMES
        # Load account_history.json to get name of user
        with open(json_files[8], encoding="utf8") as json_user:
            account = json.load(json_user)
    
        if 'registration_info' in name:
            dictionary.update({account['registration_info']['registration_username']: dictionary[user['username'][0]]})
        dictionary.update({user['email'][0]: dictionary[user['username'][0]]})
        dictionary.update({user['name'][0]: dictionary[user['username'][0]]})
    
        # Find firstnames in other files
        # (uploaded) contacts from phone
        if (os.path.exists(json_files[10])):

            with open(json_files[10], encoding="utf8") as json_contacts:
                contacts = json.load(json_contacts)
                
            if contacts != ['You have no data in this section']:
                contacts = pd.DataFrame(contacts)
                
                for contact in range(len(contacts)):
                    name = contacts['first_name'][contact]
                    lastname = contacts['last_name'][contact]
                    if lastname != '' and name != '':
                        new = {name: mingle(name)}
                        new2 = {lastname: new[name]}
                        dictionary.update(new)
                        dictionary.update(new2)
                    elif lastname == '' and name != '' :
                        new = {name: mingle(name)}
                        dictionary.update(new)
                    
        elif (os.path.exists(json_files[11])):
            
            with open(json_files[11], encoding="utf8") as json_contacts:
                contacts = json.load(json_contacts)
                
            if contacts != ['You have no data in this section']:
                contacts = pd.DataFrame(contacts)
                
                for contact in range(len(contacts)):
                    name = contacts['first_name'][contact]
                    lastname = contacts['last_name'][contact]
                    if lastname != '' and name != '':
                        new = {name: mingle(name)}
                        new2 = {lastname: new[name]}
                        dictionary.update(new)
                        dictionary.update(new2)
                    elif lastname == '' and name != '' :
                        new = {name: mingle(name)}
                        dictionary.update(new)
        
        # Look for most common names
        path = Path(input_folder) / 'Firstnames_NL.lst'
        firstnames = pd.DataFrame(open(path).read().split('\n'))[0]
        firstnames = firstnames.drop(firstnames.index[len(firstnames) - 1])
    
        # Add firstnames used in messages
        with open(json_files[7], encoding="utf8") as json_messages:
            message = json.load(json_messages)
        message = str(message)
    
        # Add firstnames used in media
        with open(json_files[9], encoding="utf8") as json_messages:
            media = json.load(json_messages)
        media = str(media)
    
        # Add firstnames used in comments
        comments = str(comments)
    
        found_names = []
        round = 1
    
        for name in firstnames:
            if name not in dictionary:
                if name.lower() in message.lower():
                    found_names.append(name)
                elif name.lower() in comments.lower():
                    found_names.append(name)
                elif name.lower() in media.lower():
                    found_names.append(name)
                round = round + 1
    
        for name in found_names:
            dictionary.update({name: mingle(name)})
    
    
        # FIND PHONE NUMBERS
        # Phone numbers in contact file
        if isinstance(contacts, pd.DataFrame):
            phones = re.findall('(?<!\d)\d{5,11}(?!\d)', str(list(contacts['contact'])))
            for number in phones:
                dictionary.update({number: '__phonenumber'})
            
        # Phone numbers in other files
        account = str(account)
        inp = message + media + comments + account
    
        phone = re.findall("(?<!\d)\d{10}(?!\d)",
                           inp)
        phone2 = []
        if len(re.findall("[0-9]{2}\-[0-9]{8}", inp)) > 0:
            phone2 = re.findall("[0-9]{2}\-[0-9]{8}", inp)
    
        phone_dic = []
        for i in range(len(phone)):
            if phone[i].startswith('06') or phone[i].startswith('6') or phone[i].startswith('020') or phone[i].startswith('20'):
                phone_dic.append(phone[i])
        for i in range(len(phone2)):
            if phone2[i].startswith('06') or phone2[i].startswith('6') or phone2[i].startswith('020') or phone2[i].startswith('20'):
                phone_dic.append(phone2[i])
    
        for number in phone_dic:
            dictionary.update({number: '__phonenumber'})
    
    
        # FIND EMAIL ADRESSES
        regex = re.compile(("([a-z0-9!#$%&'*+\/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+\/=?^_`"
                            "{|}~-]+)*(@|\sat\s)(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(\.|"
                            "\sdot\s))+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)"))
    
        # Email adresses from contacts file
        if isinstance(contacts, pd.DataFrame):
            mails = re.findall(regex, str(list(contacts['contact'])))
            
            for i in range(len(mails)):
                a= mails[i][0].replace("'", "")
                dictionary.update({a: '__emailadress'})
        
        # Email adresses from other files
        mail = re.findall(regex, inp)
    
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


        # SAVE DICTIONARY AS KEY FILE  
        df = pd.DataFrame(list(dictionary.items()))
        df = df.rename(columns={0: 'id', 1: 'subt'})
        
        export_path = Path(input_folder, 'keys'+f"_{folder.stem}.csv")
        df.to_csv(export_path, index=False, encoding='utf-8')
        
        
def anonymize(input_folder:str, output_folder:str):
    dir = Path(output_folder)
    folders = dir.glob('*')
    
    for folder in folders:
    #for n in range(len(_main_folder())):

        print('Anonymizing ' + f'{folder.stem}' + '\'s instagram data...')

        import_path = Path(input_folder, 'keys'+f"_{folder.stem}.csv")

        anonymize_csv = Anonymize(import_path, use_word_boundaries=True)
        anonymize_csv.substitute(folder)

        print('Done!')


def main():
    parser = argparse.ArgumentParser(description='Anonymize files in Instagram data download package.')
    parser.add_argument("--input_folder", "-i", help="Enter name of folder containing zipfiles",
                        default=".")
    parser.add_argument("--output_folder", "-o", help="Enter name of folder where files will be unpacked",
                        default=".")

    args = parser.parse_args()

    unpack(args.input_folder, args.output_folder)
    usernames(args.input_folder, args.output_folder)
    anonymize(args.input_folder, args.output_folder)

if __name__ == '__main__':

    main()
