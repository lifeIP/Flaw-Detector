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

RTSP_URL = 'rtsp://admin:gfhjkm1$@192.168.1.67:554/h264Preview_01_main'

os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = 'rtsp_transport;udp'

cap = cv2.VideoCapture(RTSP_URL, cv2.CAP_FFMPEG)

if not cap.isOpened():
    print('Cannot open RTSP stream')
    exit(-1)

while True:
    _, frame = cap.read()
    cv2.imshow('RTSP stream', frame)

    if cv2.waitKey(1) == 27:
        break

cap.release()
cv2.destroyAllWindows()