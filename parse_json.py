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
    """ Extract sensitive information in jsonfiles"""

    def __init__(self, input_folder: Path, output_folder: Path, package_user: str, timestamp: str):
        self.logger = logging.getLogger('anonymizing.parse_json')
        self.email = r'[\w\.-]+@[\w\.-]+'
        self.input_folder = input_folder
        self.output_folder = output_folder
        self.package_user = package_user
        self.timestamp = timestamp
        self.labels = self.get_labels()

    def create_keys(self) -> dict:
        """Extract sensitive information from nested JSON and store with coded labels in dictionary ."""

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

        # Combine separate dictionaries in one
        all_keys = ParseJson.format_dict(keys)

        #replace name labels with hash code
        hash_key_dict = {k: (self.mingle(k) if v == '__name' else v) for k, v in all_keys.items()}

        return hash_key_dict

    def extract(self, obj, key_dict: dict) -> dict:
        """Recursively search for values of key in JSON tree."""
        exceptions = ['created_at', 'instagram', 'mp4_size', 'webp_size', 'height', 'frames']
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
                                if v not in exceptions:
                                    key_dict[v] = '__name'
                        elif self.check_name(k) and self.check_datetime(v):
                            if k not in exceptions:
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

        # Add package filename to key dict as the name of the output package needs to be hashed
        if self.package_user not in key_dict:
            key_dict.update({self.package_user: '__name'})
            key_dict.update({self.input_folder.name: '__name'})
        else:
            key_dict.update({self.input_folder.name: '__name'})

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
    key_dict = parser.create_keys()

    key_series = pd.Series(key_dict, name='subt')
    key_series.to_csv(output_folder / 'keys.csv', index_label='id', header=True)

if __name__ == '__main__':
    main()
