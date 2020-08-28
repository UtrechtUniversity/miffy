from pathlib import Path
import json
import re
import pandas as pd
import string
import logging
import hashlib

class CreateKeys:
    """ Detect personal sensitive information in text; create keyfile for user and person names"""

    def __init__(self, data_package: Path, input_folder: Path, output_folder: Path):
        self.logger = logging.getLogger('anonymizing.keys')
        self.data_package = data_package
        self.input_folder = input_folder
        self.output_folder = output_folder

    def mingle(self, word):
        """ Creates scrambled version with letters and numbers of entered word """

        if len(str(word)) > 1:
            pseudo = "__" + hashlib.md5(word.encode()).hexdigest()
        else:
            pseudo = ""

        return pseudo

    def read_participants(self):
        """ Open file with all participant numbers """

        path = Path(self.input_folder) / 'participants.csv'
        participants = pd.read_csv(path, encoding="utf8")
        if len(participants.columns):
            participants = pd.read_csv(path, encoding="utf8", sep=';')

        return participants

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
                username.extend(list(df_search[col].dropna(how='all')))
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
                username.extend([item[1] for item in list(df_saved[col].dropna(how = 'all'))])
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
        participants = self.read_participants()
        participants = participants.set_index(participants.columns[0])
        dictionary = participants.to_dict()[participants.columns[0]]

        for name in set(username):
            try:
                if name not in dictionary and name.lower() is not 'instagram':
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

        # Add (the most) common names to 'names'
        path = Path(self.input_folder) / 'Firstnames_NL.lst'
        names.extend(open(path).read().split('\n'))

        # Create dictionary with original name and mingled substitute
        dictionary = {}
        for name in set(names):
            if len(name) > 1:
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
        """Replace sensitive info in profile.json that Anonymize can't replace """

        try:
            # Read profile.json
            json_file = Path(self.data_package, 'profile.json')
            with open(json_file, encoding="utf8") as f:
                data = json.load(f)

            file = json.dumps(data)

            # Replace bio and gender info
            bio = re.findall(re.compile("biography\"\: \"(.*?)\""), file)
            gender = re.findall(re.compile("gender\"\: \"(.*?)\""), file)

            if len(bio) >= 1:
                file = file.replace(bio[0], '__bio')
            if len(gender) >= 1:
                file = file.replace(gender[0], '__gender')

            # Save replaced profile.json file
            df = json.loads(file)
            with open(json_file, 'w', encoding="utf8") as outfile:
                json.dump(df, outfile)

        except FileNotFoundError:
            pass

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
