import argparse
from pathlib import Path
import re
from zipfile import ZipFile
import pandas as pd
from anonymize import Anonymize
import time
import progressbar
import logging
import itertools
from create_keys import CreateKeys
from typing import Union
from blur_images import BlurImages
from blur_videos import BlurVideos

class AnonymizeInstagram:
    """ Detect and anonymize personal information in Instagram text files"""

    def __init__(self, output_folder: Path, input_folder: Path, zip_file: Union[Path,list], part: str, cap: bool = False, ptp: bool = False):
        self.logger = logging.getLogger('anonymizing')
        self.zip_file = zip_file
        self.input_folder = input_folder
        self.output_folder = output_folder
        self.cap = cap
        self.part = part
        self.ptp = ptp

        self.unpacked = self.unpack()

    def unpack(self):
        """Extract data package to output folder """

        if type(self.zip_file) == Path:
            print(f'Unpack Path {self.zip_file}')
            # self.logger.info(f'Unpacking zipfile {self.zip_file}...')
            # unpacked = Path(self.output_folder, self.zip_file.stem.split('_')[0])
            # with ZipFile(self.zip_file, 'r') as zip:
            #     zip.extractall(unpacked)
        if type(self.zip_file) == list:
            print(f'Unpack list {self.zip_file}')
            for index, zip_file in enumerate(self.zip_file):
                if index == 0:
                    # Hier komt Roos' code
                    print(f'Extract first zip {zip_file}')
                elif index > 0:
                    print(f'Extract special next zips {zip_file}')

        #return unpacked


    def inspect_files(self):
        """ Detect all sensitive information in files from given data package"""

        keys = CreateKeys(self.unpacked, self.input_folder, self.output_folder,self.ptp)
        keys.create_keys()

        #images = BlurImages(self.unpacked)
        #images.blur_images()

        #videos = BlurVideos(self.unpacked)
        #videos.blur_videos()

        #self.anonymize()

    def read_participants(self):
        """ Open file with all participant numbers """

        path = Path(self.input_folder) / 'participants.csv'
        participants = pd.read_csv(path, encoding="utf8")
        if len(participants.columns):
            participants = pd.read_csv(path, encoding="utf8", sep=';')

        return participants

    def anonymize(self):
        """ Find sensitive info as described in key file and replace it with anonymized substitute """

        participants = self.read_participants()
        col = list(participants.columns)
        file = self.unpacked

        self.logger.info("Anonymizing all files...")

        # Replacing sensitive info with substitute indicated in key file
        sub = list(participants[col[1]][participants[col[0]] == file.name])[0]
        import_path = Path(self.input_folder, 'keys' + f"_{sub}.csv")
        if self.cap:
            anonymize_csv = Anonymize(import_path, use_word_boundaries=True)
        else:
            anonymize_csv = Anonymize(import_path, use_word_boundaries=True, flags=re.IGNORECASE)

        anonymize_csv.substitute(file)

        # Removing unnecessary files
        delete_path = Path(self.output_folder, sub)

        # json_list = ['autofill.json', 'uploaded_contacts.json', 'contacts.json', 'account_history.json',
        #              'devices.json',
        #              'information_about_you.json', 'checkout.json']

        json_list = ['autofill.json', 'uploaded_contacts.json', 'account_history.json',
                     'devices.json', 'information_about_you.json']
        for json_file in json_list:
            try:
                file_to_rem = Path(delete_path, json_file)
                file_to_rem.unlink()
            except FileNotFoundError as e:
                self.logger.error(f"Error {e} occurred while deleting {json_file} ")
                continue

def init_logging(log_file: Path) :
    """
    Initialise Python logger
    :param log_file: Path to the log file.
    """
    logger = logging.getLogger('anonymizing')
    logger.setLevel('INFO')

    # creating a formatter
    formatter = logging.Formatter('- %(name)s - %(levelname)-8s: %(message)s')

    # set up logging to file
    fh = logging.FileHandler(log_file, 'w', 'utf-8')
    fh.setLevel(logging.INFO)

    # Set up logging to console
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    # Set handler format
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    # Add the handler to the root logger
    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger


def main():
    parser = argparse.ArgumentParser(description='Anonymize files in Instagram data download package.')
    parser.add_argument("--input_folder", "-i", help="Enter path to folder containing zipfiles",
                        default=".")
    parser.add_argument("--output_folder", "-o", help="Enter path to folder where files will be unpacked",
                        default=".")
    parser.add_argument("--log_file", "-l", help="Enter path to log file",
                        default="log_anonym_insta.txt")
    parser.add_argument('--cap', default=False, action='store_true',
                        help="Replace capitalized names only (i.e., replacing 'Ben' but not 'ben')")
    parser.add_argument('--ptp', default=False, action='store_true',
                        help="Use anonymization codes from participant list")
    args = parser.parse_args()

    logger = init_logging(Path(args.log_file))

    input_folder = Path(args.input_folder)
    output_folder = Path(args.output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)

    zip_list = list(input_folder.glob('*.zip'))

    # Check if there zip files are unique or part of a 'collection'
    usr = r'\S+'
    timestamp = r'_[0-9]{8}'
    patt = usr + timestamp

    ext_zip_list = []
    for zip_file in zip_list:
        res = re.match(patt + '.zip', str(zip_file.name))
        if res:
            print(f'Instanonymize regular {zip_file}')
            instanonym = AnonymizeInstagram(output_folder, input_folder, zip_file, args.cap,args.ptp)
            # Zipfiles in collection have: patt+suffix+.zip
        else:
            ext_zip_list.append(zip_file)

    ext_zip_str = [str(i.name) for i in ext_zip_list]
    ext_zip_str.sort()
    grp_ext_zip = [list(g) for _, g in itertools.groupby(ext_zip_str, lambda x: x.partition('_')[0])]

    for zip_grp in grp_ext_zip:
        # Account for unique zipfiles who do not meet pattern
        if len(zip_grp) == 1:
            print(f'Instanonymize weird pattern {zip_grp[0]}')
            instanonym = AnonymizeInstagram(output_folder, input_folder, Path(zip_grp[0]), args.cap, args.ptp)
        elif len(zip_grp) > 1:
            print(f'Unpack group {zip_grp}')
            instanonym = AnonymizeInstagram(output_folder, input_folder, zip_grp, args.cap, args.ptp)



            #instanonym.inspect_files()




if __name__ == '__main__':
    main()
