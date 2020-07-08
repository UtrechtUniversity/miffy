# Miffy

Anonymize and analyze data download packages from social media platforms

### Prerequisites

To clone this repository, you'll need Git installed on your computer. 

Obtain your data download package as a zipped folder and move it to the input folder

Download a pretrained version of the EAST model [here](https://www.pyimagesearch.com/2018/08/20/opencv-text-detection-east-text-detector/).
Once you have cloned this repository, place the model in the same folder as the anonymization script.


## Installing

From your command line:

```
# Clone this repository
$ git clone https://github.com/UtrechtUniversity/miffy

# Go into the repository
$ cd miffy

# Install dependencies; TODO add requirements 
pip install -r requirements.txt 

```
Run the program with arguments `-i` for input folder and ` -o` output folder

```
$ python anonymizing_instagram_uu.py -i ./input/ -o ./output

```

The output will be a copy of the zipped data download package with all usernames and email addresses anonymized.

## Built With

The blurring of text in images and videos is based on a pre-trained version of the [EAST model](https://github.com/argman/EAST).



## Authors

See also the list of [contributors](https://github.com/your/project/contributors) who participated in this project.

## License

This project is licensed under ...

## Acknowledgments

* Hat tip to anyone whose code was used
* Inspiration
* etc
