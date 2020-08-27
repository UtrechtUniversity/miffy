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

### Download data package

To download your Instagram data package:

1. Go to www.instagram.com and log in
2. Click on your profile picture, go to *Settings* and *Privacy and Security*
3. Scroll to *Data download* and click *Request download*
4. Enter your email adress and click *Next*
5. Enter your password and click *Request download*

Make sure that the data download package is saved as **username_YYYYMMDD.zip** (i.e., Instagram handle and date of download).


### Input folder

After the repository is cloned and the data package is downloaded, create a new folder within the cloned repository (e.g., 'input'). Here, the following files need to be saved:
* **Data package**: All necessary zipped data download packages (username_YYYYMMDD.zip)
* **First names file**: A list with the most common (Dutch) names (Firstnames_NL.lst)
* **Participant file**\*: An overview of all participants' usernames and participant codes (participants.csv)

**\*** N.B. Only necessary for participant based studies.

## Run software

When all preceding steps are taken, the data download packages can be pseudonimized. Run the program with arguments `-i` for input folder (e.g., 'input') and ` -o` output folder (e.g., 'output'):

```
$ python anonymizing_instagram_uu.py -i input -o output
```

An overview of the program's workflow is shown below:
![flowanonymize.png](flowanonymize.png)

The output of the program will be a copy of the zipped data download package with all names, usernames, email addresses, and phone numbers anonymized, and all pictures and videos blurred. This pseudonimized data download package is saved in the output folder.


## Built With

The blurring of text in images and videos is based on a pre-trained version of the [EAST model](https://github.com/argman/EAST). Replacing the extracted sensitive info with the pseudonimized substitutes in the data download package is done using the [Anonymize-UU](https://pypi.org/project/anonymize-UU/) package.


## Authors

The Miffy project is executed by Martine de Vos, Laura Boeschoten and Roos Voorvaart in assigment of the University Utrecht. See also the list of [contributors](https://github.com/your/project/contributors) who participated in this project.


## License

This project is licensed under ...


## Acknowledgments

Thank you to all people whose code we've used.
