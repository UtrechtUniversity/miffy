# Miffy

Pseudonimizing data download packages from Instagram.

## Prerequisites

Before running the software, the following steps need to be taken:

1. **[Clone repository](#clone-repository)**
2. **[Download data package](#download-data-package)**
3. **[Create input folder](#input-folder)**

### Clone repository

To clone this repository, you'll need *Git installed* on your computer. When Git is installed, run the following code in the command line:

```
# Clone this repository
$ git clone https://github.com/UtrechtUniversity/miffy

# Go into the repository
$ cd miffy

# Install dependencies
pip install -r requirements.txt
```
N.B. When experiencing difficulties with installing torch, have a look at the [PyTorch website](https://pytorch.org/) for more information. When issues arise concerning the Anonymize software, make sure that no prior version is installed (```$ pip uninstall anonymize_UU``` and/or ```$ pip uninstall anonymoUUs```).

### Download data package

To download your Instagram data package:

1. Go to www.instagram.com and log in
2. Click on your profile picture, go to *Settings* and *Privacy and Security*
3. Scroll to *Data download* and click *Request download*
4. Enter your email adress and click *Next*
5. Enter your password and click *Request download*

Instagram will deliver your data in a compressed zip folder with format **username_YYYYMMDD.zip** (i.e., Instagram handle and date of download). For Mac users this might be different, so make sure to check that all provided files are zipped into one folder with the name **username_YYYYMMDD.zip**.

### Input folder

After the repository is cloned and the data package is downloaded, create a new folder within the cloned repository (e.g., 'input'). This folder is used to store all Instagram data packages:
* **Data package**: All necessary *zipped* data download packages (username_YYYYMMDD.zip)

Before you can run the software, you need to make sure that the main repository folder contains the following items:
* **Facial blurring software**: The *frozen_east_text_detection.pb* software, necessary for the facial blurring of images and videos, can be downloaded from [GitHub](https://github.com/oyyd/frozen_east_text_detection.pb) 
* **Participant file**\*: An overview of all participants' usernames and participant IDs (e.g., participants.csv)

**\*** N.B. Only relevant for participant based studies with *predefined* participant IDs. This file can have whatever name you prefer, as long as it is saved as .csv and contains 2 columns; the first being the original instagram handles (e.g., janjansen) and the second the participant IDs (e.g., PP001).

## Run software

When all preceding steps are taken, the data download packages can be pseudonimized. Run the program with (atleast) the arguments `-i` for input folder (e.g., 'input') and ` -o` output folder (e.g., 'output'):

```
$ python anonymizing_instagram_uu.py [OPTIONS]

Options:
  -i  path to folder containing zipfiles (e.g., -i input)
  -o  path to folder where files will be unpacked and pseudonimized (e.g., -o output)
  -l  path to log file
  -p  path to participants list to use corresponding participant IDs (e.g., -p participants.csv)
  -c  replace capitalized names only (when not entering this option, the default = False; not case sensitive) (e.g., -c)

```

An overview of the program's workflow is shown below:
![flowanonymize.png](flowanonymize.png)

The output of the program will be a copy of the zipped data download package with all names, usernames, email addresses, and phone numbers pseudonimized, and all pictures and videos blurred. This pseudonimized data download package is saved in the output folder.


## Built With

The blurring of text in images and videos is based on a pre-trained version of the [EAST model](https://github.com/argman/EAST). Replacing the extracted sensitive info with the pseudonimized substitutes in the data download package is done using the [AnonymoUUs](https://github.com/UtrechtUniversity/anonymouus) package.


## Authors

The Miffy project is executed by Martine de Vos, Laura Boeschoten and Roos Voorvaart in assigment of the University Utrecht. See also the list of [contributors](https://github.com/your/project/contributors) who participated in this project.


## License

This project is licensed under ...


## Acknowledgments

Thank you to all people whose code we've used.
