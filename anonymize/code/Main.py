import os
import cv2
import json

os.chdir('C:/Users/F112974/surfdrive/Onderzoek/AweSome/deduce_instagram_05_2020/code')

import module_generate_dictionary as mgd
import module_hash_files as mhf
import module_blur_files as mbf

os.chdir('C:/Users/F112974/surfdrive/Onderzoek/AweSome/deduce_instagram_05_2020')

# 1. generate the dictionary -------------------------------------------------------------------------------------------

dict_hashes = mgd.generate_dictionary()

# 2. identify all .json files in the datadownload package --------------------------------------------------------------

directory = r"C:\Users\F112974\surfdrive\Onderzoek\AweSome\deduce_instagram_05_2020\datadownload"

path_list = [os.path.join(dirpath, filename) for dirpath, _,
                                                 filenames in os.walk(directory) for filename in filenames if
             filename.endswith('.json')]

# 3. run the dictionary over all .json files ---------------------------------------------------------------------------

for x in range(len(path_list)):

    with open(path_list[x]) as json_file:
        file = json.dumps(json.load(json_file))

        hashed_str = mhf.hash_file(dict_hashes, file)

    with open(path_list[x], 'w+') as hashed_json:
        hashed_json.write(hashed_str)

# 4. load the face detection algorithm ---------------------------------------------------------------------------------

cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml') # weet niet zeker of deze moet blijven staan

# 5. identify all .jpg files in the datadownload package ---------------------------------------------------------------

path_list = [os.path.join(dirpath, filename) for dirpath, _,
                                                 filenames in os.walk(directory) for filename in filenames if
             filename.endswith('.jpg')]

# 6. run the face blurring function over all .jpg files ----------------------------------------------------------------

for x in range(len(path_list)):
    color = cv2.imread(path_list[x])
    bw = cv2.cvtColor(color, cv2.COLOR_BGR2GRAY)
    blur = mbf.find_and_blur(bw, color)
    cv2.imwrite(path_list[x], blur)

# 7. identify all .mp4 files in the datadownload package ---------------------------------------------------------------

path_list = [os.path.join(dirpath, filename) for dirpath, _,
                                                 filenames in os.walk(directory) for filename in filenames if
             filename.endswith('.mp4')]

# 8. run the face blurring function over all .mp4 files ----------------------------------------------------------------


################## DIT WERKT (MAAR OPSLAAN NOG NIET) ##################### (moet ook nog in loop over .mp4's gezet
video_capture = cv2.VideoCapture(path_list[0])

# Define the codec and create VideoWriter object
fourcc = cv2.VideoWriter_fourcc(*'XVID')
out = cv2.VideoWriter('BLUR_TEST.avi',fourcc, 20.0, (640,480))

while(video_capture.isOpened()):
    ret, color = video_capture.read()
    if ret==True:
        bw = cv2.cvtColor(color, cv2.COLOR_BGR2GRAY)
        # detect the face and blur it
        blur = find_and_blur(bw, color)
        #Write frame
        out.write(blur)
        # display output
        cv2.imshow('Video', blur)
        # break if q is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    else:
        break

# turn camera off
video_capture.release()
out.release()
# close camera  window
cv2.destroyAllWindows()
###########################################################################