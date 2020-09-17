import argparse
import collections
import dateutil.parser
from datetime import datetime
import hashlib
import json
import logging
import pandas as pd
from pathlib import Path
import re


class ParseJson:
    """ Extract usernames in jsonfiles"""

    def __init__(self, input_folder: Path, output_folder: Path):
        self.logger = logging.getLogger('anonymizing.parse_json')
        self.email = r'[\w\.-]+@[\w\.-]+'
        self.input_folder = input_folder
        self.output_folder = output_folder
        self.labels = self.get_labels()

    def create_keys(self):
        """Extract user names from nested JSON."""

        # Create key file
        self.logger.info(f"Creating key file for {self.input_folder}...")

        keys = []
        for file in self.input_folder.glob('*.json'):
            # Per json file: extract sensitive info+labels and store in dict
            with file.open(encoding="utf8") as f:
                key_dict = {}
                data = json.load(f)
                res = self.extract(data,key_dict)
                keys.append(res)

        # Add common given names to dictionary
        common_names = self.common_names()
        keys.append(common_names)

        # Combine in one dict; replace name labels with hash code
        all_keys = ParseJson.format_dict(keys)
        hash_key_dict = {k: (self.mingle(v) if v == '__name' else v) for k, v in all_keys.items()}

        # Replace info in profile.json
        self.replace_profile()

        # hash name of package owner in name output file
        owner = str(self.input_folder.name).split('_')[0]
        sub = hash_key_dict[owner]
        outfile = self.output_folder / f'keys_{sub}.csv'

        # write keys to csv file as input for anonymizeUU package
        key_series = pd.Series(hash_key_dict, name='subt')
        key_series.to_csv(outfile, index_label='id', header=True)

    def extract(self, obj, key_dict: dict) -> dict:
        """Recursively search for values of key in JSON tree."""

        if isinstance(obj, dict):
            for k, v in obj.items():
                if v:
                    if isinstance(v, (dict, list)):
                        self.extract(v, key_dict)
                    elif isinstance(v, str):
                        # If the key matches predefined labels, value may contain sensitive info
                        if any(label.match(k) for label in self.labels):
                            if re.match(self.email, v):
                                key_dict[v] = '__emailaddress'
                            elif self.check_phone(v):
                                key_dict[v] = '__phonenumber'
                            elif self.check_name(v):
                                key_dict[v] = '__name'
                        elif self.check_name(k) and self.check_datetime(v):
                            key_dict[k] = '__name'
        elif isinstance(obj, list):
            if obj:
                try:
                    names = self.get_username(obj)
                    for name in names:
                        key_dict[name] = '__name'
                except:
                    for item in obj:
                        self.extract(item, key_dict)

        return key_dict

    def get_labels(self) -> list:
        """Get regular expressions of json search labels"""
        labels = [r'search_click',
                  r'participants',
                  r'sender',
                  r'author'
                  r'^\S*mail',
                  r'^\S*name',
                  r'^\S*friends$',
                  r'^\S*user\S*$',
                  r'^\S*owner$',
                  r'^follow\S*$',
                  r'^contact\S*$']

        regex_labels = [re.compile(l) for l in labels]

        return regex_labels

    def check_name(self, text: str):
        """check if given string is valid username"""

        name = r'^\S{6,}$'

        try:
            int(text)
            return None
        except:
            if re.match(name, text):
                return text

    def check_phone(self, text: str):
        """check if given string is valid phone nr"""

        patterns = [r'(?<!\d)\d{9,10}(?!\d)',
                    r'[0-9]{2}\-[0-9]{8}']

        phone_nrs = [re.compile(p) for p in patterns]

        if any(nr.match(text) for nr in phone_nrs):
            return text

    def check_datetime(self, text: str) -> datetime:
        """Check if given string can be converted to a datetime format"""
        try:
            res = dateutil.parser.parse(text)
            return res
        except ValueError:
            pass
        try:
            res = datetime.utcfromtimestamp(int(text))
            return res
        except ValueError:
            pass

    def get_username(self, obj: list):
        """Check if given list contains username"""

        matches = [x for x in obj if self.check_datetime(x)]

        usr_list = []

        if matches:
            for i in obj:
                if i not in matches:
                    try:
                        res = re.match(self.usr, i)
                        usr_list.append(res.group(0))
                    except:
                        pass

        return usr_list

    def common_names(self) -> dict:
        """Add common given names in NL to keys dictionary; these may occur in free text like messages"""

        name_file = Path.cwd() / 'Firstnames_NL.lst'
        with name_file.open() as f:
            names = [i.strip() for i in f.readlines()]

        # Create dictionary with original name and mingled substitute
        name_dict = {}
        for name in set(names):
            if len(name) > 1:
                name_dict[name] = '__name'

        return name_dict

    def replace_profile(self):
        """Replace sensitive info in profile.json that Anonymize can't replace """

        try:
            json_file = self.input_folder / 'profile.json'
            with json_file.open(encoding="utf8") as f:
                data = json.load(f)

            file = json.dumps(data)

            # Replace bio and gender info
            bio = re.findall(re.compile("biography\": \"(.*?)\""), file)
            gender = re.findall(re.compile("gender\": \"(.*?)\""), file)

            if len(bio) >= 1:
                file = file.replace(bio[0], '__bio')
            if len(gender) >= 1:
                file = file.replace(gender[0], '__gender')

            # Save files
            df = json.loads(file)
            with json_file.open('w', encoding="utf8") as outfile:
                json.dump(df, outfile)

        except FileNotFoundError:
            pass

    @staticmethod
    def mingle(text: str) -> str:
        """ Creates scrambled version with letters and numbers of entered word """

        if len(str(text)) > 1:
            pseudo = "__" + hashlib.md5(text.encode()).hexdigest()
        else:
            pseudo = ""

        return pseudo

    @staticmethod
    def format_dict(obj: list) -> dict:
        """Format irregular list of dictionaries and remove duplicates"""

        no_dupl = [i for n, i in enumerate(obj) if i not in obj[n + 1:]]

        new_dict = {k: v for d in no_dupl for k, v in d.items()}

        return new_dict

    @staticmethod
    def format_list(obj: list) -> set:
        """Flatten list and remove duplicates"""

        flat_usr = [i for i in ParseJson.flatten(obj)]
        try:
            flat_usr = set(flat_usr)
        except TypeError:
            pass
        return flat_usr

    @staticmethod
    def flatten(obj: list) -> list:
        """Flatten irregular list of lists"""
        for el in obj:
            if isinstance(el, collections.abc.Iterable) and not isinstance(el, (str, bytes)):
                yield from ParseJson.flatten(el)
            else:
                yield el


def main():
    parser = argparse.ArgumentParser(description='Extract usernames from nested json files.')
    parser.add_argument("--input_folder", "-i", help="Enter path to folder containing json files",
                        default=".")
    parser.add_argument("--output_folder", "-o", help="Enter path to folder where results will be saved",
                        default=".")
    args = parser.parse_args()

    input_folder = Path(args.input_folder)
    output_folder = Path(args.output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)

    parser = ParseJson(input_folder, output_folder)
    parser.create_keys()


if __name__ == '__main__':
    main()
