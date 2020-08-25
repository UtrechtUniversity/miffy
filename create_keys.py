from pathlib import Path
import json
import re
import pandas as pd
import string
import logging

class CreateKeys:
    """ Detect personal sensitive information in text; create keyfile for user and person names"""

    def __init__(self, data_package: Path, input_folder: Path, output_folder: Path, ptp: bool = False):
        self.logger = logging.getLogger('anonymizing.keys')
        self.data_package = data_package
        self.input_folder = input_folder
        self.output_folder = output_folder
        self.ptp = ptp

    def mingle(self, word):
        """ Creates scrambled version with letters and numbers of entered word """

        word = list(word)

        # Calculates corresponding number of each letter
        number = []
        for i in word:
            if isinstance(i, int):
                next
            if i.isalpha():
                number.append(ord(i))

        numbers = []
        for i in number:
            numbers.append(i - 96)

        # Creates new letters based on the position of each letter
        letters = []
        for i in range(len(number)):
            letter = chr((number[i] + i))
            if letter.isalpha():
                letters.append(letter)
            else:
                letters.append(number[i])

        # Creates scrambled version of letters and numbers
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

    def read_participants(self) -> dict:
        """ Create dictionary with participant names and numbers """

        path = Path(self.input_folder) / 'participants.csv'
        participants = pd.read_csv(path, encoding="utf8")
        if len(participants.columns):
            participants = pd.read_csv(path, encoding="utf8", sep=';')

        participants = participants.set_index(participants.columns[0])
        dictionary = participants.to_dict()[participants.columns[0]]

        return dictionary

    def extr_profile(self, df):
        """Extract all profile information from entered file """

        try:
            df_profile = df[list(df.columns[df.columns.str.contains(pat='facebook|birth|email')])].dropna(how='all')
        except ValueError:
            newList = [i for i in list(df.columns) if not isinstance(i, int)]
            df = df[newList]
            df_profile = df[list(df.columns[df.columns.str.contains(pat='facebook|birth|email')])].dropna(how='all')

        dictionary = {}
        for file in df_profile.columns:
            if file.find('mail') >= 0:
                dictionary.update({df_profile[file][0]: '__email'})
            elif (file.find('facebook') >= 0) and (file.find('birth') < 0):
                dictionary.update({df_profile[file][0]: '__facebookinfo'})
            elif file.find('birth') >= 0:
                dictionary.update({df_profile[file][0]: '__birthdate'})

        return dictionary

    def extr_usernames(self, df):
        """Extract all usernames in entered file """

        username = []

        try:
            df_users = df[list(df.columns[df.columns.str.contains(pat='user|follow|friends')])].dropna(how='all')
        except ValueError:
            newList = [i for i in list(df.columns) if not isinstance(i, int)]
            df = df[newList]
            df_users = df[list(df.columns[df.columns.str.contains(pat='user|follow|friends')])].dropna(how='all')

        df_search = df[list(df.columns[df.columns.str.contains(pat='search')])].dropna(how='all')
        df_seen = df[list(df.columns[df.columns.str.contains(pat='seen|watched')])].dropna(how='all')
        df_saved = df[list(df.columns[df.columns.str.contains(pat='saved')])].dropna(how='all')
        df_likes = df[list(df.columns[df.columns.str.contains(pat='like')])].dropna(how='all')
        df_comments = df[list(df.columns[df.columns.str.contains(pat='_comment')])].dropna(how='all')

        username.extend(list(df_users.index))

        for col in df_search.columns:
            try:
                username.extend(list(df_search[col]))
            except:
                next

        for col in df_seen.columns:
            try:
                for idx, row in df_seen[col].iteritems():
                    if pd.isna(row):
                        next
                    else:
                        try:
                            username.append(row['author'])
                        except KeyError:
                            username.append(row['username'])
            except:
                next

        try:
            df_messages = df['participants'].dropna(how='all')
            username.extend([j for i in list(df_messages) for j in i])
        except:
            next

        for col in df_saved.columns:
            try:
                username.extend([item[1] for item in list(df_saved[col])])
            except:
                next

        for col in df_likes.columns:
            try:
                username.extend([item[1] for item in list(df_likes[col].dropna(how = 'all'))])
            except:
                next

        for col in df_comments.columns:
            try:
                username.extend([item[2] for item in list(df_comments[col].dropna(how = 'all'))])
            except:
                next

        # Create dictionary with original username and mingled substitute
        if self.ptp :
            self.logger.info(f"Reading participants file")
            dictionary = self.read_participants()
            for name in set(username):
                try:
                    if name not in dictionary and name.lower() is not 'instagram':
                        dictionary.update({name: self.mingle(name)})
                except AttributeError:
                    next
        else:
            self.logger.info(f"No participants file")
            dictionary = {}
            for name in set(username):
                try:
                    if name.lower() is not 'instagram':
                        dictionary.update({name: self.mingle(name)})
                except AttributeError:
                    next

        return dictionary

    def extr_names(self, df):
        """Extract all names in entered file """

        names = []
        try:
            names.extend(list(df['name'].dropna(how='all')))
        except:
            next

        try:
            names.extend(df['registration_info'].dropna(how='all')['registration_username'])
        except:
            next

        try:
            df_names = df[list(df.columns[df.columns.str.contains(pat='t_name')])].dropna(how='all')
            for col in df_names.columns:
                names.extend(list(df_names[col]))
        except:
            next

        # Search for (the most) common names in saved usernames
        path = Path(self.input_folder) / 'Firstnames_NL.lst'
        file = pd.DataFrame(open(path).read().split('\n'))[0]

        firstnames = []
        for i in file:
            if len(i) > 2:
                firstnames.append(i)

        for name in firstnames:
            if name.lower() in json.dumps(df.to_dict(orient='list')).lower():
                if name not in names or name.lower() not in names:
                    names.append(name)

        # Create dictionary with original name and mingled substitute
        dictionary = {}
        for name in set(names):
            dictionary.update({name: self.mingle(name)})

        return dictionary

    def extr_mail(self, df):
        """Extract all email adresses in entered file """

        mails = []
        try:
            mails.extend(list(df['email'].dropna(how='all')))
        except:
            next

        # Search for nested email adresses
        regex = re.compile(("([a-z0-9!#$%&'*+\/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+\/=?^_`"
                            "{|}~-]+)*(@|\sat\s)(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(\.|"
                            "\sdot\s))+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)"))

        mail_text = re.findall(regex, json.dumps(df.to_dict(orient='list')))

        for i in range(len(mail_text)):
            found = mail_text[i][0].replace("'", "")
            if found.find('@') > 1 and found not in mails:
                mails.append(found)

        # Create dictionary with original email adress and mingled substitute
        dictionary = {}
        for mail in set(mails):
            dictionary.update({mail: '__emailadress'})

        return dictionary

    def extr_phone(self, df):
        """Extract all phone numbers in entered file """

        number = []
        try:
            df_phone = df[list(df.columns[df.columns.str.contains(pat='contact')])].dropna(how='all')
            for col in df_phone.columns:
                if df_phone[col].str.contains(re.compile("[0-9]")).any():
                    for i in df_phone[col].index:
                        try:
                            number.append(int(df_phone[col][i]))
                        except:
                            next
                else:
                    next
        except:
            next

        # Search for nested phone numbers
        regex = [re.compile("(?<!\d)\d{9,10}(?!\d)"), re.compile("[0-9]{2}\-[0-9]{8}")]
        for reg in regex:
            for i in re.findall(reg, json.dumps(df.to_dict(orient='list'))):
                if i not in number:
                    number.append(i)

        # Create dictionary with original phone number and mingled substitute
        dictionary = {}
        for num in set(number):
            dictionary.update({num: '__phonenumber'})

        return dictionary

    def extr_http(self, df):
        """Extract all URLs in entered file """

        regex = re.compile("(?P<url>https?:\/\/[^\s]+)")
        https = re.findall(regex, json.dumps(df.to_dict(orient='list')))

        dictionary = {}
        for http in set(https):
            while http[-1] in string.punctuation:
                http = http[:-1]
            dictionary.update({http: '__url'})

        return dictionary

    def replace_info(self):
        """Replace sensitive info that Anonymize can't replace """

        dic = {}
        for json_file in self.data_package.glob('*.json'):
            with open(json_file, encoding="utf8") as f:
                data = json.load(f)
                if len(data) > 0:
                    dic.update({f'{json_file}': data})

        file = json.dumps(dic)

        # Replace bio and gender info
        bio = re.findall(re.compile("biography\"\: \"(.*?)\""), file)
        gender = re.findall(re.compile("gender\"\: \"(.*?)\""), file)

        if len(bio) >= 1:
            file = file.replace(bio[0], '__bio')
        if len(gender) >= 1:
            file = file.replace(gender[0], '__gender')

        # Save files
        df = json.loads(file)
        files = df.keys()
        for file in files:
            export_path = Path(file)
            with open(export_path, 'w', encoding="utf8") as outfile:
                json.dump(df[file], outfile)

    def create_keys(self):
        """Extract all sensitive information from files in given folder """

        json_files = self.data_package.glob('*.json')
        df = pd.DataFrame()
        for json_file in json_files:
            try:
                my_df = pd.read_json(json_file)
                df = df.append(my_df, sort=False)
            except ValueError:
                with open(json_file, encoding="utf8") as f:
                    data = json.load(f)
                my_df = pd.DataFrame(dict([(k, pd.Series(v)) for k, v in data.items()]))
                df = df.append(my_df, sort=False)

        # Create key file
        self.logger.info(f"Creating key file for {self.data_package}...")
        dictionary = self.extr_usernames(df)
        functions = [self.extr_profile, self.extr_names, self.extr_mail, self.extr_phone, self.extr_http]

        for function in functions:
            try:
                dictionary.update(function(df))
            except TypeError:
                next

        self.replace_info()

        dic = pd.DataFrame(list(dictionary.items()))
        dic = dic.rename(columns={0: 'id', 1: 'subt'})

        subt = dictionary[f'{self.data_package.name}']
        export_path = Path(self.input_folder, 'keys' + f"_{subt}.csv")
        dic.to_csv(export_path, index=False, encoding='utf-8')
