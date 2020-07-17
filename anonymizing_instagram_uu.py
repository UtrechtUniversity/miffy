import argparse
from pathlib import Path
import re
from zipfile import ZipFile
import pandas as pd
from anonymize import Anonymize
import time
import progressbar
import logging
from create_keys import CreateKeys
from blur_images import BlurImages
from blur_videos import BlurVideos

class AnonymizeInstagram:
    """ Detect and anonymize personal information in Instagram text files"""

    def __init__(self, output_folder: Path, input_folder: Path, zip_file: Path, part: str, cap: bool = False):
        self.logger = logging.getLogger('anonymizing')
        self.zip_file = zip_file
        self.input_folder = input_folder
        self.output_folder = output_folder
        self.cap = cap
        self.part = part

        self.unpacked = self.unpack()

    def unpack(self):
        """Extract data package to output folder """

        try:
            for zip_file in self.zip_file:
                self.logger.info(f'Unpacking zipfile {zip_file}...')

                index = len(self.part)+9
                pattern = zip_file.name[index:-4]
                unpacked = Path(self.output_folder, self.part)

                if int(pattern[-1]) == 1:
                    with ZipFile(zip_file, 'r') as zip:
                        zip.extractall(unpacked)

                elif int(pattern[-1]) > 1:
                    with ZipFile(zip_file, 'r') as zipObj:
                        listOfFileNames = zipObj.namelist()
                        for fileName in listOfFileNames:
                            if fileName.endswith('.json'):
                                if Path(unpacked, fileName).is_file():
                                    p = Path(unpacked, fileName)
                                    p.replace(Path(unpacked, f"{p.stem}{pattern[-1]}{p.suffix}"))
                                zipObj.extract(fileName, unpacked)
        except TypeError:
            self.logger.info(f'Unpacking zipfile {self.zip_file}...')
            unpacked = Path(self.output_folder, self.part)
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

        self.anonymize()

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
    parser.add_argument('--cap', default=True, action='store_true',
                        help="Replace capitalized names only (i.e., replacing 'Ben' but not 'ben')")
    args = parser.parse_args()

    logger = init_logging(Path(args.log_file))

    input_folder = Path(args.input_folder)
    output_folder = Path(args.output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)

    zip_list = list(input_folder.glob('*.zip'))
    part_list = pd.read_csv(Path(input_folder, 'participants.csv'), encoding="utf8", sep = ';')
    part_list = list(part_list[part_list.columns[0]])

    widgets = [progressbar.Percentage(), progressbar.Bar()]
    bar = progressbar.ProgressBar(widgets=widgets, max_value=len(part_list)).start()

    for index, parti in enumerate(part_list):
        part = parti
        logger.info(f"Started anonymizing {part}:")

        if str(zip_list).count(part) == 1:
            zip_file = re.findall(f'({part}'+'_[0-9]{8}.zip)', str(zip_list))
            zip_file = Path(input_folder, zip_file[0])

            instanonym = AnonymizeInstagram(output_folder, input_folder, zip_file, part, args.cap)
            instanonym.inspect_files()

            logger.info(f"Finished anonymizing {part}.")

        elif str(zip_list).count(part) > 1:
            zip_file = []
            for zip in zip_list:
                try:
                    files = re.findall(f'({part}.*.zip)', str(zip))[0]
                    zip_file.append(Path(input_folder, files))
                except:
                    next

            instanonym = AnonymizeInstagram(output_folder, input_folder, zip_file, part, args.cap)
            instanonym.inspect_files()

            logger.info(f"Finished anonymizing {part}.")

        else:
            logger.info(f"No package found for {part}.")
            next

        print(" ")
        time.sleep(1)
        bar.update(index + 1)

    bar.finish()


if __name__ == '__main__':
    main()
