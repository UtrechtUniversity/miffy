import module_find_blur_faces as mfbf
import module_find_blur_text as mfbt
from pathlib import Path
import progressbar
import cv2 as cv
import time
import logging


class BlurImages:
    """ Blur text and faces in images in given folder """

    def __init__(self, data_package: Path):
        self.logger = logging.getLogger('anonymizing.images')
        self.data_package = data_package

    def blur_images(self):
        """Blur text and faces in images in given folder """

        self.logger.info(f'Blurring photos of data package {self.data_package}---')

        jpg_list = list(self.data_package.rglob('*.jpg'))

        widgets = [progressbar.Percentage(), progressbar.Bar()]
        bar = progressbar.ProgressBar(widgets=widgets, max_value=len(jpg_list)).start()
        for index, jpg in enumerate(jpg_list):
            # Blur faces on images
            try:
                img = cv.imread(str(jpg))
                frame_bf = mfbf.find_blur_faces(img)

                # Blur text on the images that already contain blurred faces
                frame_bt = mfbt.find_text_and_blur(
                    frame_bf,
                    # eastPath="frozen_east_text_detection.pb",
                    net=cv.dnn.readNet("frozen_east_text_detection.pb"),
                    min_confidence=0.5)

                cv.imwrite(str(jpg), frame_bt)

                time.sleep(0.1)
                bar.update(index + 1)

            except Exception as e:
                self.logger.error(f"Exception {e} occurred  while processing {jpg}")
                self.logger.warning("Skip and go to next jpg")

                time.sleep(0.1)
                bar.update(index + 1)

                continue

        bar.finish()
