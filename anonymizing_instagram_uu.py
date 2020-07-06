import argparse
from pathlib import Path
import json
import re
from zipfile import ZipFile
import pandas as pd
import numpy as np
from anonymize import Anonymize
import string
import os
import cv2 as cv
import time
import progressbar

import module_find_blur_faces as mfbf
import module_find_blur_text as mfbt

class AnonymizeInstagram:
    """ Detect and anonymize personal information in Instagram text files"""

    def __init__(self, input_folder: Path, output_folder: Path, replace_sens: str):
        self.input_folder = Path(input_folder)
        self.output_folder = Path(output_folder)
        self.replace_sens = input("Do you want to replace capitalized names only (i.e., replacing 'Ben' but not "
                                  "'ben')? (Y/N): ")

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

    def read_json(self, files):
        """ Reads .JSON files as list """

        alldata = {}
        for file in files:
            with open(file, encoding="utf8") as json_file:
                data = json.load(json_file)
                if len(data) > 0:
                    alldata.update({f'{file}': data})

        return alldata

    def read_participants(self):
        """ Open file with all participant numbers """

        path = Path(self.input_folder) / 'participants.csv'
        participants = pd.read_csv(path, encoding="utf8")
        if len(participants.columns):
            participants = pd.read_csv(path, encoding="utf8", sep=';')

        return participants

    def extr_profile(self, df):
        """Extract all profile information from entered file """

        dictionary = {}
        for file in df:
            if file.find('profile') >= 0:
                for key in df[file]:
                    if key == 'biography':
                        dictionary.update({df[file][key]: '__biography'})
                    if key.find('facebook') >= 0:
                        dictionary.update({df[file][key]: '__facebookinfo'})
                    if key.find('birth') >= 0:
                        dictionary.update({df[file][key]: '__birthdate'})

        return (dictionary)

    def extr_usernames(self, df):
        """Extract all usernames in entered file """

        # Search for columns with usernames in them
        username = []
        for file in df:
            if type(df[file]) == dict:
                for key in df[file].keys():
                    if key.find('like') >= 0:
                        for n in range(len(df[file][key])):
                            found = df[file][key][n][1]
                            if found not in username:
                                username.append(found)
                    if key.find('follow') >= 0 or key.find('friend') >= 0:
                        founds = list(df[file][key].keys())
                        for found in founds:
                            if found not in username:
                                username.append(found)
                    if key.find('user') >= 0:
                        if len(df[file][key]) > 1 and type(df[file][key]) is not str:
                            founds = list(df[file][key].keys())
                            for found in founds:
                                if found not in username:
                                    username.append(found)
                    if key.find('comment') >= 0:
                        if key != 'allow_comments_from':
                            for n in range(len(df[file][key])):
                                found = df[file][key][n][-1]
                                if found not in username:
                                    username.append(found)
                    if key.find('saved') >= 0 or key.find('polls') >= 0:
                        founds = df[file][key]
                        for found in founds:
                            name = found[1]
                            if name not in username:
                                username.append(name)

        # Search for nested usernames
        found = []
        regex = [re.compile("\\'author\\': \\'(.*?)\\'"), re.compile("\\'search_click\\': \\'(.*?)\\'"),
                 re.compile("\\'username\\': \\'(.*?)\\'"), re.compile("\\'media_owner\\': \\'(.*?)\\'"),
                 re.compile(r"{'participants': \[(.*?)],")]
        for reg in regex:
            found.append(re.findall(reg, str(df)))

        for index in found:
            if type(index) == list:
                for item in index:
                    found_item = item.split(",")
                    for sender in found_item:
                        sender = sender.replace("'", "")
                        if sender.find(" ") == 0:
                            sender = sender.replace(" ", "")
                        if sender not in username and sender != 'Username unavailable.':
                            username.append(sender)
            elif index not in username and index != 'Username unavailable.':
                username.append(index)

        # Create dictionary with original username and mingled substitute
        participants = self.read_participants()
        dictionary = {}
        
        for name in username:
            col = list(participants.columns)
            if name not in list(participants[col[0]]) and name.lower() is not 'instagram':
                dictionary.update({name: self.mingle(name)})
            else:
                dictionary.update({name: list(participants[col[1]][participants[col[0]] == name])[0]})

        return (dictionary)

    def extr_names(self, df):
        """Extract all names in entered file """

        # Search for columns with names in them
        names = []
        for file in df:
            if type(df[file]) != dict and len(df[file]) > 1:
                for n in range(len(df[file])):
                    for key in df[file][n].keys():
                        if key.find('_name') >= 0:
                            found = df[file][n][key]
                            if len(found) > 1:
                                names.append(found)
            elif type(df[file]) == dict:
                for key in df[file].keys():
                    if key.find('name') == 0:
                        names.append(df[file][key])
                    if type(df[file][key]) == dict:
                        for i in df[file][key].keys():
                            if i.find('name') >= 0:
                                for n in range(len(df[file][key][i])):
                                    found = df[file][key][i][n]
                                    if len(found) > 1:
                                        names.append(found)

        # Search for nested names
        regex = re.compile("\\'name\\': \\'(.*?)\\'")
        found = re.findall(regex, str(df))

        for index in found:
            if type(index) == list:
                for item in index:
                    found_item = item.split(",")
                    for sender in found_item:
                        sender = sender.replace("'", "")
                        if sender.find(" ") == 0:
                            sender = sender.replace(" ", "")
                        if sender not in names and sender != 'Username unavailable.':
                            names.append(sender)
            elif index not in names and index != 'Username unavailable.':
                names.append(index)

        # Search for (the most) common names in saved usernames
        path = Path(self.input_folder) / 'Firstnames_NL.lst'
        firstnames = pd.DataFrame(open(path).read().split('\n'))[0]
        firstnames = firstnames.drop(firstnames.index[len(firstnames) - 1])

        for name in firstnames:
            if name.lower() in str(df).lower():
                if name not in names or name.lower() not in names:
                    names.append(name)

        # Create dictionary with original name and mingled substitute
        dictionary = {}
        for name in names:
            dictionary.update({name: self.mingle(name)})

        return (dictionary)

    def extr_mail(self, df):
        """Extract all email adresses in entered file """

        # Search for nested email adresses
        regex = re.compile(("([a-z0-9!#$%&'*+\/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+\/=?^_`"
                            "{|}~-]+)*(@|\sat\s)(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(\.|"
                            "\sdot\s))+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)"))

        mail_text = re.findall(regex, str(df))

        mails = []
        for i in range(len(mail_text)):
            found = mail_text[i][0].replace("'", "")
            if found.find('@') > 1 and found not in mails:
                mails.append(found)

        # Create dictionary with original email adress and mingled substitute
        dictionary = {}
        for mail in mails:
            dictionary.update({mail: '__emailadress'})

        return (dictionary)

    def extr_phone(self, df):
        """Extract all phone numbers in entered file """

        # Search for columns with phone numbers
        number = []
        for file in df:
            if type(df[file]) != dict and len(df[file]) > 1:
                for n in range(len(df[file])):
                    for key in df[file][n].keys():
                        if key.find('contact') >= 0:
                            num = df[file][n][key]
                            if num.find('@') < 0:
                                number.append(num)

        # Search for nested phone numbers
        regex = [re.compile("(?<!\d)\d{9,10}(?!\d)"), re.compile("[0-9]{2}\-[0-9]{8}")]
        for reg in regex:
            for i in re.findall(reg, str(df)):
                if i not in number:
                    number.append(i)

        # Create dictionary with original phone number and mingled substitute
        dictionary = {}
        for num in number:
            dictionary.update({num: '__phonenumber'})

        return (dictionary)

    def extr_http(self, df):
        """Extract all URLs in entered file """

        df = json.dumps(df)

        regex = re.compile("(?P<url>https?:\/\/[^\s]+)")
        https = re.findall(regex, df)

        dictionary = {}
        for http in https:
            while http[-1] in string.punctuation:
                http = http[:-1]
            dictionary.update({http: '__url'})

        return (dictionary)

    def replace_info(self, df):
        """Replace sensitive info that Anonymize can't replace """

        file = json.dumps(df)

        # Replace bio and gender info
        bio = re.findall(re.compile("\"biography\"\: \"(.*?)\""), file)
        gender = re.findall(re.compile("\"gender\"\: \"(.*?)\""), file)

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

    def unpack(self):
        """Extract download instagram packages, i.e., zipfiles, to input folder """
        print(" ")
        print('--- Unpacking ---')

        dir = Path(self.input_folder)
        zip_files = dir.glob('*.zip')

        tot = []
        for file in zip_files:
            tot.append(file)

        print("Unpacking all packages...")
        widgets = [progressbar.Percentage(), progressbar.Bar()]
        bar = progressbar.ProgressBar(widgets=widgets, max_value=len(tot)).start()
        for index in range(len(tot)):
            new_folder = Path(self.output_folder, tot[index].stem.split('_')[0])

            with ZipFile(tot[index], 'r') as zip:
                zip.extractall(new_folder)

            time.sleep(1)
            bar.update(index + 1)

        bar.finish()

        print(" ")

    def create_keys(self):
        """Extract all sensitive information from files in given folder """

        print('--- Searching ---')

        dire = Path(self.output_folder)
        
        row_count = 0
        for row in dire.glob('*'):
            row_count += 1

        part = 0
        folders = dire.glob('*')
        for folder in folders:
            part = part + 1
            print(f'Exploring {folder.stem}\'s package ({part}/{row_count} participants)')

            subdir = Path(folder)
            files = subdir.glob('*.json')

            # Create key file
            print("Creating key file...")
            df = self.read_json(files)
            dictionary = self.extr_usernames(df)
            functions = [self.extr_profile, self.extr_names, self.extr_mail, self.extr_phone, self.extr_http]

            tot = len(functions)
            widgets = [progressbar.Percentage(), progressbar.Bar()]
            bar = progressbar.ProgressBar(widgets=widgets, max_value=tot).start()
            for index in range(tot):
                dictionary.update(functions[index](df))
                time.sleep(0.1)
                bar.update(index + 1)

            bar.finish()

            self.replace_info(df)

            dic = pd.DataFrame(list(dictionary.items()))
            dic = dic.rename(columns={0: 'id', 1: 'subt'})

            subt = dictionary[f'{folder.stem}']
            export_path = Path(self.input_folder, 'keys' + f"_{subt}.csv")
            dic.to_csv(export_path, index=False, encoding='utf-8')

            # Blur photos
            print("Blurring photos...")
            path_list_jpg = [os.path.join(dirpath, filename) for dirpath, _, filenames in os.walk(folder) for filename
                             in
                             filenames if filename.endswith('.jpg')]

            tot = len(path_list_jpg)
            widgets = [progressbar.Percentage(), progressbar.Bar()]
            bar = progressbar.ProgressBar(widgets=widgets, max_value=tot).start()
            
            for i in range(tot):
                
                # Blur faces on images
                img = cv.imread(path_list_jpg[i])
                frame_bf = mfbf.find_blur_faces(img)

                # Blur text on the images that already contain blurred faces
                frame_bt = mfbt.find_text_and_blur(
                    frame_bf,
                    eastPath="frozen_east_text_detection.pb",
                    min_confidence=0.5)

                cv.imwrite(path_list_jpg[i], frame_bt)
                time.sleep(0.1)
                bar.update(i + 1)

            bar.finish()

            # Blur videos
            print("Blurring videos (can take a while)...")
            path_list_mp4 = [os.path.join(dirpath, filename) for dirpath, _, filenames in os.walk(folder) for filename
                             in
                             filenames if filename.endswith('.mp4')]

            tot = len(path_list_mp4)
            widgets = [progressbar.Percentage(), progressbar.Bar()]
            bar = progressbar.ProgressBar(widgets=widgets, max_value=tot).start()
            
            for i in range(tot):

                cap = cv.VideoCapture(path_list_mp4[i])
                total_frames = int(cap.get(cv.CAP_PROP_FRAME_COUNT))
                img_array = []

                for g in range(total_frames):
                    cap.set(1, g - 1);
                    success = cap.grab()
                    ret, image = cap.retrieve()

                    # if ret == True:
                    # blur faces on frame
                    frame_bf = mfbf.find_blur_faces(image)
                    
                    # blur text on frame
                    frame_bt = mfbt.find_text_and_blur(
                        frame_bf,
                        eastPath="frozen_east_text_detection.pb",
                        min_confidence=0.5)

                    img_array.append(frame_bt)

                    # else:

                height, width, layers = image.shape
                size = (width, height)

                out = cv.VideoWriter(path_list_mp4[i][:-4] + '.mp4', cv.VideoWriter_fourcc(*'DIVX'), 15, size)

                # store the blurred video
                for f in range(len(img_array)):
                    cvimage = np.array(img_array[f])
                    out.write(cvimage)

                out.release()
                time.sleep(0.1)
                bar.update(i + 1)

            bar.finish()

            print(' ')

        print(' ')

    def anonymize(self):
        """ Find sensitive info as described in key file and replace it with anonymized substitute """

        print('--- Anonymizing ---')

        part = self.read_participants()
        col = list(part.columns)

        dir = Path(self.output_folder)
        folders = dir.glob('*')

        tot = []
        for file in folders:
            tot.append(file)

        print("Anonymizing all packages...")
        widgets = [progressbar.Percentage(), progressbar.Bar()]
        bar = progressbar.ProgressBar(widgets=widgets, max_value=len(tot)).start()
        
        for i in range(len(tot)):

            # Replacing sensitive info with substitute indicated in key file
            sub = list(part[col[1]][part[col[0]] == tot[i].stem])[0]
            import_path = Path(self.input_folder, 'keys' + f"_{sub}.csv")
            if self.replace_sens.lower() == 'n':
                anonymize_csv = Anonymize(import_path, use_word_boundaries=True, flags=re.IGNORECASE)
            else:
                anonymize_csv = Anonymize(import_path, use_word_boundaries=True)

            anonymize_csv.substitute(tot[i])

            # Removing unnecesseray files
            delete_path = Path(self.output_folder, sub)

            files = ['autofill.json', 'uploaded_contacts.json', 'contacts.json', 'account_history.json', 'devices.json',
                     'information_about_you.json', 'checkout.json']
            for file in files:
                try:
                    file_to_rem = Path(delete_path, file)
                    file_to_rem.unlink()
                except FileNotFoundError:
                    next

            bar.update(i + 1)

        bar.finish()
        
        print(" ")
        print("Done! :) ")


def main():
    parser = argparse.ArgumentParser(description='Anonymize files in Instagram data download package.')
    parser.add_argument("--input_folder", "-i", help="Enter name of folder containing zipfiles",
                        default=".")
    parser.add_argument("--output_folder", "-o", help="Enter name of folder where files will be unpacked",
                        default=".")

    args = parser.parse_args()

    replace_sens = str
    instanonym = AnonymizeInstagram(args.input_folder, args.output_folder, replace_sens)

    instanonym.unpack()
    instanonym.create_keys()
    instanonym.anonymize()


if __name__ == '__main__':
    main()
