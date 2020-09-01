import argparse
from pathlib import Path,PurePath
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

    def __init__(self, output_folder: Path, input_folder: Path, zip_file: Union[Path, list],
                 cap: bool = False, ptp: bool = False):
        self.logger = logging.getLogger('anonymizing')
        self.zip_file = zip_file
        self.input_folder = input_folder
        self.output_folder = output_folder
        self.cap = cap
        self.ptp = ptp

        self.unpacked = self.unpack()
        self.inspect_files()
        self.anonymize()

    def unpack(self):
        """Extract data package to output folder """

        try:
            # Check if variable is a path; statement also valid for other OS
            if isinstance(self.zip_file,PurePath):
                unpacked = self.extract()

            elif isinstance(self.zip_file,list):
                self.logger.info(f'Extracting zipfile {self.zip_file} in {self.output_folder}')
                for index, zip_file in enumerate(self.zip_file):
                    if index == 0:
                        self.zip_file = Path(zip_file)
                        unpacked = self.extract()
                    elif index > 0:
                        self.logger.info(f'Extracting files for {zip_file} in {self.output_folder}'
                                         f'; replace existing files with name+suffix {index-1}')
                        with ZipFile(zip_file, 'r') as zipObj:
                            listOfFileNames = zipObj.namelist()
                            unpacked = Path(self.output_folder, self.zip_file.stem)
                            for fileName in listOfFileNames:
                                if fileName.endswith('.json'):
                                    if Path(unpacked, fileName).is_file():
                                        p = Path(unpacked, fileName)
                                        p.replace(Path(unpacked, f"{p.stem}_{index-1}{p.suffix}"))
                                    zipObj.extract(fileName, unpacked)
            else:
                self.logger.warning('Can not extract {self.zip_file}, do nothing')
                unpacked = ' '

        except Exception as e:
            self.logger.error(f"Exception {e} occurred  while processing {self.zip_file}")
            self.logger.warning("Skip and go to next zip")

        return unpacked

    def extract(self):
        """Extract data package to output folder """
        self.logger.info(f'Extracting zipfile {self.zip_file}...')
        extracted = Path(self.output_folder, self.zip_file.stem)
        with ZipFile(self.zip_file, 'r') as zip:
             zip.extractall(extracted)

        return extracted

    def inspect_files(self):
        """ Detect all sensitive information in files from given data package"""

        print(f'Time for inspection')
        keys = CreateKeys(self.unpacked, self.input_folder, self.output_folder, self.ptp)
        keys.create_keys()

        images = BlurImages(self.unpacked)
        images.blur_images()

        videos = BlurVideos(self.unpacked)
        videos.blur_videos()

        self.anonymize()

    def read_participants(self) -> dict:
        """ Create dictionary with participant names and numbers """

        path = Path(self.input_folder) / 'participants.csv'
        participants = pd.read_csv(path, encoding="utf8")
        if len(participants.columns):
            participants = pd.read_csv(path, encoding="utf8", sep=';')

        participants = participants.set_index(participants.columns[0])
        dictionary = participants.to_dict()[participants.columns[0]]

        return dictionary

    def anonymize(self):
        """ Find sensitive info as described in key file and replace it with anonymized substitute """

        self.logger.info("Anonymizing all files...")

        own_name = str(self.unpacked.name).partition('_')[0]

        # Replacing sensitive info with substitute indicated in key file
        if self.ptp:
            part_dic = self.read_participants()
            sub = part_dic[own_name]
        else:
            sub = own_name

        import_path = Path(self.input_folder, 'keys' + f"_{own_name}.csv")

        if self.cap:
            anonymize_csv = Anonymize(import_path, use_word_boundaries=True)
        else:
            anonymize_csv = Anonymize(import_path, use_word_boundaries=True, flags=re.IGNORECASE)

        anonymize_csv.substitute(self.unpacked)

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


def init_logging(log_file: Path):
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
        # Regular pattern of zipfile for Insta DDP
        res = re.match(patt + '.zip', str(zip_file.name))
        if res:
            instanonym = AnonymizeInstagram(output_folder, input_folder, zip_file, args.cap, args.ptp)
        else:
            # Zipfiles in collection have a suffix, like usr_timestamp_part1.zip
            ext_zip_list.append(zip_file)

    ext_zip_str = [str(i) for i in ext_zip_list]
    ext_zip_str.sort()
    grp_ext_zip = [list(g) for _, g in itertools.groupby(ext_zip_str, lambda x: x.partition('_')[0])]

    for zip_grp in grp_ext_zip:
        # Account for unique zipfiles that do not meet regular pattern
        if len(zip_grp) == 1:
            instanonym = AnonymizeInstagram(output_folder, input_folder, Path(zip_grp[0]), args.cap, args.ptp)
        elif len(zip_grp) > 1:
            logger.info(f'Collection of files found with same user + timestamp: {zip_grp}')
            instanonym = AnonymizeInstagram(output_folder, input_folder, zip_grp, args.cap, args.ptp)

    #instanonym.inspect_files()


if __name__ == '__main__':
    main()
