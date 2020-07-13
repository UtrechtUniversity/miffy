import module_find_blur_faces as mfbf
import module_find_blur_text as mfbt
from pathlib import Path
import progressbar
import cv2 as cv
import time
import numpy as np
import logging


class BlurVideos:
    """ Blur text and faces in videos in given folder """

    def __init__(self, data_package: Path):
        self.logger = logging.getLogger('anonymizing.videos')
        self.data_package = data_package

    def blur_videos(self):
        """Blur text and faces in videos in given folder """

        self.logger.info("Blurring videos (can take a while)...")

        mp4_list = list(self.data_package.rglob('*.mp4'))

        widgets = [progressbar.Percentage(), progressbar.Bar()]
        bar = progressbar.ProgressBar(widgets=widgets, max_value=len(mp4_list)).start()
        for index, mp4 in enumerate(mp4_list):

            try:
                cap = cv.VideoCapture(str(mp4))
                total_frames = int(cap.get(cv.CAP_PROP_FRAME_COUNT))
                img_array = []
                net = cv.dnn.readNet("frozen_east_text_detection.pb")

                for g in range(total_frames):
                    cap.set(1, g - 1)
                    success = cap.grab()
                    ret, image = cap.retrieve()

                    # if ret == True:
                    # blur faces on frame
                    frame_bf = mfbf.find_blur_faces(image)
                    # blur text on frame
                    frame_bt = mfbt.find_text_and_blur(frame_bf,net,min_confidence=0.5)

                    img_array.append(frame_bt)

                    # else:

                height, width, layers = image.shape
                size = (width, height)

                out = cv.VideoWriter(str(mp4)[:-4] + '.mp4', cv.VideoWriter_fourcc(*'DIVX'), 15, size)

                # store the blurred video
                for f in range(len(img_array)):
                    cvimage = np.array(img_array[f])
                    out.write(cvimage)

                out.release()
                time.sleep(0.1)
                bar.update(index + 1)

            except Exception as e:
                self.logger.error(f"Exception {e} occurred  while processing {mp4}")
                self.logger.warning("Skip and go to next mp4")

                time.sleep(0.1)
                bar.update(index + 1)

                continue

        bar.finish()
        print(' ')