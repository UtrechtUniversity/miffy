import argparse
from pathlib import Path
import re
from zipfile import ZipFile
import pandas as pd
from anonymize import Anonymize
import string
import os
import time
import progressbar
from create_keys import CreateKeys
from blur_images import BlurImages
from blur_videos import BlurVideos


class AnonymizeInstagram:
    """ Detect and anonymize personal information in Instagram text files"""

    def __init__(self, output_folder: Path, input_folder: Path, zip_file: Path, cap: bool = False):
        self.zip_file = zip_file
        self.input_folder = input_folder
        self.output_folder = output_folder
        self.cap = cap

        self.unpacked = self.unpack()

    def unpack(self):
        """Extract data package to output folder """

        print(f'Unpacking zipfile {self.zip_file}---')
        unpacked = Path(self.output_folder, self.zip_file.stem.split('_')[0])

        with ZipFile(self.zip_file, 'r') as zip:
            zip.extractall(unpacked)

        return unpacked

    def inspect_files(self):
        """ Detect all sensitive information in files from given data package"""

        keys = CreateKeys(self.unpacked, self.input_folder, self.output_folder)
        keys.create_keys()

        images = BlurImages(self.unpacked)
        images.blur_images()

        videos = BlurVideos(self.unpacked)
        videos.blur_videos()

        anonymize()

    def read_participants(self):
        """ Open file with all participant numbers """

        path = Path(self.input_folder) / 'participants.csv'
        participants = pd.read_csv(path, encoding="utf8")
        if len(participants.columns):
            participants = pd.read_csv(path, encoding="utf8", sep=';')

        return participants

    def anonymize(self):
        """ Find sensitive info as described in key file and replace it with anonymized substitute """

        part = self.read_participants()
        col = list(part.columns)

        dir = Path(self.unpacked)
        file_list = list(dir.glob('*'))

        logging.getLogger().info("Anonymizing all files...")
        widgets = [progressbar.Percentage(), progressbar.Bar()]
        bar = progressbar.ProgressBar(widgets=widgets, max_value=len(file_list).start())
        for index, file in enumerate(file_list):

            # Replacing sensitive info with substitute indicated in key file
            sub = list(part[col[1]][part[col[0]] == file.stem])[0]
            import_path = Path(self.input_folder, 'keys' + f"_{sub}.csv")
            if self.cap:
                anonymize_csv = Anonymize(import_path, use_word_boundaries=True)
            else:
                anonymize_csv = Anonymize(import_path, use_word_boundaries=True, flags=re.IGNORECASE)

            anonymize_csv.substitute(file)

            # Removing unnecesseray files
            delete_path = Path(self.output_folder, sub)

            json_list = ['autofill.json', 'uploaded_contacts.json', 'contacts.json', 'account_history.json',
                         'devices.json',
                         'information_about_you.json', 'checkout.json']
            for json_file in json_list:
                try:
                    file_to_rem = Path(delete_path, json_file)
                    file_to_rem.unlink()
                except FileNotFoundError as e:
                    logging.getLogger().error(f"Error {e} occurred while deleting {json_file} ")
                    continue

            bar.update(index + 1)

        bar.finish()
        print(" ")
        print("Done! :) ")

def init_logging(log_file: Path) :
    """
    Initialise Python logger
    :param log_file: Path to the log file.
    """
    logging.basicConfig(
        filename=str(log_file),
        level=logging.INFO,
        format='[%(asctime)s] {%(threadName)s:%(lineno)d} %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    # Log all levels to file
    logging.getLogger().setLevel(logging.INFO)

    # Set up logging to console
    console = logging.StreamHandler()
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    console.setFormatter(formatter)
    # console.setLevel(logging.DEBUG)

    # Add the handler to the root logger
    logging.getLogger().addHandler(console)

def main():
    parser = argparse.ArgumentParser(description='Anonymize files in Instagram data download package.')
    parser.add_argument("--input_folder", "-i", help="Enter path to folder containing zipfiles",
                        default=".")
    parser.add_argument("--output_folder", "-o", help="Enter path to folder where files will be unpacked",
                        default=".")
    parser.add_argument("--log_file", "-l", help="Enter path to log file",
                        default="log_anonym_insta.txt")
    parser.add_argument('--cap', default=True, action='store_true',
                        help="Replace capitalized names only (i.e., replacing 'Ben' but not 'ben')")
    args = parser.parse_args()

    init_logging(Path(args.log))

    input_folder = Path(args.input_folder)
    output_folder = Path(args.output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)

    zip_list = list(input_folder.glob('*.zip'))

    widgets = [progressbar.Percentage(), progressbar.Bar()]
    bar = progressbar.ProgressBar(widgets=widgets, max_value=len(zip_list)).start()

    for index, zip_file in enumerate(zip_list):
        logging.getLogger().info(f"Started anonymizing {zip_file}.")
        instanonym = AnonymizeInstagram(output_folder, input_folder, zip_file, args.cap)
        instanonym.inspect_files()

        logging.getLogger().info(f"Finished anonymizing {zip_file}.")
        time.sleep(1)
        bar.update(index + 1)

    bar.finish()


if __name__ == '__main__':
    main()
