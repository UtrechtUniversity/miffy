import collections
import dateutil.parser
from datetime import datetime
import logging
import re


class ParseJson:
    """ Extract usernames in jsonfiles"""

    def __init__(self, data: dict):
        self.logger = logging.getLogger('anonymizing.parse_json')
        self.usr = r'^\S{6,}$'
        self.data = data
        self.labels = self.get_labels()

    def json_extract_usrs(self) -> set:
        """Extract user names from nested JSON."""

        arr = []

        # Extract values with recursive function
        values = self.extract(self.data, arr)
        flat_values = [i for i in self.flatten(values)]

        try:
            flat_values = set(flat_values)
        except TypeError:
            pass

        return flat_values

    def extract(self, obj, arr: list) -> list:
        """Recursively search for values of key in JSON tree."""

        if isinstance(obj, dict):
            for k, v in obj.items():
                if v:
                    if isinstance(v, (dict, list)):
                        self.extract(v, arr)
                    elif isinstance(v, str):
                        if any(label.match(k) for label in self.labels):
                            try:
                               int(v)
                               pass
                            except ValueError:
                                arr.append(v)
                        elif re.match(self.usr, k) and self.check_datetime(v):
                            arr.append(k)
        elif isinstance(obj, list):
            if obj:
                try:
                    names = self.get_username(obj)
                    arr.append(names)
                except:
                    for item in obj:
                        self.extract(item, arr)
        return arr

    def get_labels(self) -> list:
        """Get regular expressions of json search labels"""
        labels = [r'search_click',
                  r'participants',
                  r'sender',
                  r'^\S*name',
                  r'^\S*friends$',
                  r'^\S*user\S*$',
                  r'^\S*owner$',
                  r'^follow\S*$',
                  r'^contact\S*$']

        regex_labels = [re.compile(l) for l in labels]

        return regex_labels

    def check_datetime(self,date_text: str) -> datetime:
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

    def get_username(self,obj: list):
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

    def flatten(self,obj: list) -> list:
        """Flatten irregular list of lists"""
        for el in obj:
            if isinstance(el, collections.abc.Iterable) and not isinstance(el, (str, bytes)):
                yield from self.flatten(el)
            else:
                yield el