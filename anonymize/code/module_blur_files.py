import cv2

cascade = cv2.CascadeClassifier('C:/Users/F112974/surfdrive/Onderzoek/AweSome/deduce_instagram_05_2020/code/haarcascade_frontalface_default.xml')

def find_and_blur(bw, color):

    faces = cascade.detectMultiScale(bw, 1.1, 4)

    for (x, y, w, h) in faces:

        roi_color = color[y:y + h, x:x + w]

        blur = cv2.GaussianBlur(roi_color, (101, 101), 0)

        color[y:y + h, x:x + w] = blur

    return color