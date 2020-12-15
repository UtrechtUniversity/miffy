import cv2 as cv
from facenet_pytorch import MTCNN
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFilter

mtcnn = MTCNN(margin=20,
              keep_all=True,
              post_process=False)


def find_blur_faces(img):
    color = cv.cvtColor(img, cv.COLOR_BGR2RGB)
    frame = Image.fromarray(color)

    boxes, probs, landmarks = mtcnn.detect(frame, landmarks=True)

    if boxes is None:
        boxes = "No faces in picture"
        return frame

    else:
        boxes = boxes.astype(int)
        for j in range(0, len(boxes)):
            mask = Image.new('L', frame.size, 0)
            draw = ImageDraw.Draw(mask)
            draw.rectangle([(boxes[j, 0], boxes[j, 1]), (boxes[j, 2], boxes[j, 3])], fill=255)
            blurred = frame.filter(ImageFilter.GaussianBlur(52))
            frame.paste(blurred, mask=mask)

        return frame
