# import cv2 as cv



# ids = list()
# for i in range(100):
#     try:
#         cap = cv.VideoCapture(i)
#         ret, src = cap.read()
#         if ret:
#             ids.append(i)
#             cap.release()
#     except:
#         pass


# print(ids)


import cv2
import os

RTSP_URL_0 = 'rtsp://admin:gfhjkm1$@192.168.10.68:554/h264Preview_01_main'

os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = 'rtsp_transport;udp'

cap_0 = cv2.VideoCapture(RTSP_URL_0, cv2.CAP_FFMPEG)

def show_img(cap, name):
    _, frame = cap.read()
    frame = cv2.resize(frame, (640, 480))
    cv2.imshow(name, frame)


while True:

    show_img(cap_0, "0")

    if cv2.waitKey(1) == 27:
        break

cap_0.release()
cv2.destroyAllWindows()