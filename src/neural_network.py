from PyQt6.QtWidgets    import *
from PyQt6.QtCore       import *

import os

import cv2
import numpy as np
import mvsdk
import platform

import time
from datetime import datetime
import torch.multiprocessing as mp

from ultralytics import YOLO

from src.logger import logger



MODEL_PATH = "yolo11s.pt"


def yolo_data_processing(cam_index, confidence_threshold, start_or_stop, counts_of_flaws, mlock):
    """
    Функция для обработки данных YOLO модели.
    :param cam_index: Индекс камеры или путь к видеопотоку
    :param confidence_threshold: Порог уверенности обнаружения дефекта
    :param start_or_stop: Флаг начала/остановки процесса обработки
    :param counts_of_flaws: Список для подсчета дефектов
    :param mlock: Мьютекс для синхронизации доступа к общим ресурсам
    """
    hCamera = 0
    try:
        hCamera = mvsdk.CameraInit(cam_index, -1, -1)
    except mvsdk.CameraException as e:
        print("CameraInit Failed({}): {}".format(e.error_code, e.message) )
        return

    cap = mvsdk.CameraGetCapability(hCamera)
    monoCamera = (cap.sIspCapacity.bMonoSensor != 0)
    if monoCamera:
        mvsdk.CameraSetIspOutFormat(hCamera, mvsdk.CAMERA_MEDIA_TYPE_MONO8)
    else:
        mvsdk.CameraSetIspOutFormat(hCamera, mvsdk.CAMERA_MEDIA_TYPE_BGR8)
    
    mvsdk.CameraSetTriggerMode(hCamera, 0)
    mvsdk.CameraSetAeState(hCamera, 0)
    mvsdk.CameraSetExposureTime(hCamera, 30 * 1000)
    mvsdk.CameraPlay(hCamera)
    FrameBufferSize = cap.sResolutionRange.iWidthMax * cap.sResolutionRange.iHeightMax * (1 if monoCamera else 3)
    pFrameBuffer = mvsdk.CameraAlignMalloc(FrameBufferSize, 16)


    
    model = YOLO(MODEL_PATH)
    try:
        model.to('cuda')
    except:
        logger.warning(f"Нет возможности отправить вычисления на видеокарту для камеры с индексом {cam_index}. Вычисления происходят на процессоре")

    while True:
        try:
            pRawData, FrameHead = mvsdk.CameraGetImageBuffer(hCamera, 200)
            mvsdk.CameraImageProcess(hCamera, pRawData, pFrameBuffer, FrameHead)
            mvsdk.CameraReleaseImageBuffer(hCamera, pRawData)
            mvsdk.CameraFlipFrameBuffer(pFrameBuffer, FrameHead, 1)
            frame_data = (mvsdk.c_ubyte * FrameHead.uBytes).from_address(pFrameBuffer)
            frame = np.frombuffer(frame_data, dtype=np.uint8)
            frame = frame.reshape((FrameHead.iHeight, FrameHead.iWidth, 1 if FrameHead.uiMediaType == mvsdk.CAMERA_MEDIA_TYPE_MONO8 else 3) )
            frame = cv2.resize(frame, (640,480), interpolation = cv2.INTER_LINEAR)
        except mvsdk.CameraException as e:
            if e.error_code != mvsdk.CAMERA_STATUS_TIME_OUT:
                print("CameraGetImageBuffer failed({}): {}".format(e.error_code, e.message) )

        detections = model(frame)
        for obj in detections:
            opencv_array: cv2.Mat = obj.orig_img

            # Область сохранения изображений (для тестирования)
            directory_empty = f"images/empty/{datetime.today().strftime('%Y/%m/%d')}"
            if not os.path.exists(directory_empty):
                os.makedirs(directory_empty)
            cv2.imwrite(f"{directory_empty}/{time.time_ns()}.png", opencv_array)

            directory_with_boxes = f"images/boxes/{datetime.today().strftime('%Y/%m/%d')}"
            file_name = time.time_ns()

            for data in obj.boxes.data.tolist():
                confidence = data[4]

                mlock.acquire()
                ct_conf = float(confidence_threshold[0]) / 10000
                mlock.release()

                if float(confidence) < ct_conf or not start_or_stop[0]:
                    continue

                mlock.acquire()
                counts_of_flaws[0] += 1
                file_with_flaw = f"{directory_with_boxes}/{file_name}.png"
                with open("last_flaw", "w") as f:
                    f.writelines([
                        file_with_flaw + "\n",
                        str(float(confidence)) + "\n",
                        str(float(confidence_threshold[0]) / 10000) + "\n"
                    ])

                with open("list_of_flaw", "a") as f:
                    f.write(
                        f"{datetime.today().strftime('%Y.%m.%d.%H:%M:%S')} "
                        f"{file_with_flaw} {str(float(confidence))} "
                        f"{str(float(confidence_threshold[0]) / 10000)}\n"
                    )

                logger.warning(f"Обнаружен дефект: {float(confidence)}:"
                               f"{float(confidence_threshold[0]) / 10000} *** "
                               f"{directory_with_boxes}/{file_name}.png")
                start_or_stop[0] = False
                mlock.release()

                if not os.path.exists(directory_with_boxes):
                    os.makedirs(directory_with_boxes)

                xmin, ymin, xmax, ymax = int(data[0]), int(data[1]), int(data[2]), int(data[3])
                cv2.rectangle(opencv_array, (xmin, ymin), (xmax, ymax), (0, 0, 255), 3)
                cv2.imwrite(f"{directory_with_boxes}/{file_name}.png", opencv_array)


class ManagePThread(QThread):
    
    signal_critical_error = pyqtSignal(int)

    def __init__(self):
        super().__init__()

        DevList = mvsdk.CameraEnumerateDevice()
        nDev = len(DevList)
        if nDev < 1:
            print("No camera was found!")
            return

        self.cam_index_0 = DevList[0]
        # Другие индексы камер закомментированы...

        self.manager = mp.Manager()
        self.mlock = mp.Lock()

        self.start_or_stop = self.manager.list([False, False])

        self.counts_of_flaws_0 = self.manager.list([0])
        self.counts_of_flaws_1 = self.manager.list([0])
        self.counts_of_flaws_2 = self.manager.list([0])
        self.counts_of_flaws_3 = self.manager.list([0])

        self.confidence_threshold_0 = self.manager.list([8000])
        self.confidence_threshold_1 = self.manager.list([8000])
        self.confidence_threshold_2 = self.manager.list([8000])
        self.confidence_threshold_3 = self.manager.list([8000])

        with open("./settings.st", "r") as file:
            lines = file.readlines()
            self.confidence_threshold_0[0] = int(lines[0].rstrip())
            self.confidence_threshold_1[0] = int(lines[1].rstrip())
            self.confidence_threshold_2[0] = int(lines[2].rstrip())
            self.confidence_threshold_3[0] = int(lines[3].rstrip())

        # Передаем обработчик данных отдельно от класса
        self.thread_4 = mp.Process(target=yolo_data_processing, args=(
            self.cam_index_0,
            self.confidence_threshold_0,
            self.start_or_stop,
            self.counts_of_flaws_0,
            self.mlock
        ))
        # Остальные потоки аналогично закомментированы...

        self.start()



    pyqtSlot(int, int)
    def slot_change_confidence_threshold(self, confidence_threshold: int, ct_id: int):
        if      ct_id == 0: self.confidence_threshold_0[0] = confidence_threshold
        elif    ct_id == 1: self.confidence_threshold_1[0] = confidence_threshold
        elif    ct_id == 2: self.confidence_threshold_2[0] = confidence_threshold
        elif    ct_id == 3: self.confidence_threshold_3[0] = confidence_threshold
        else:   logger.warning(f"Возникла проблема в slot_change_confidence_threshold, что-то не так с ct_id: {ct_id}, confidence_threshold: {confidence_threshold}")

    pyqtSlot(bool)
    def slot_start_stop(self, start: bool):
        logger.warning(f"Обработка запущена" if start else "Обработка приостановлена")
        self.mlock.acquire()
        self.start_or_stop[0] = start
        self.mlock.release()
    
    pyqtSlot(bool)
    def slot_exit_thread(self, exit: bool):
        self.mlock.acquire()
        self.start_or_stop[1] = exit
        self.mlock.release()
        logger.warning(f"Попытка закрытия программы")
        
        self.thread_4.terminate()
        # self.thread_5.terminate()
        # self.thread_6.terminate()
        # self.thread_7.terminate()
        self.terminate()

    
    signal_get_error_count = pyqtSignal(int)

    pyqtSlot()
    def slot_get_error_count(self):
        self.mlock.acquire()
        count = self.counts_of_flaws_0[0] + self.counts_of_flaws_1[0] + self.counts_of_flaws_2[0] + self.counts_of_flaws_3[0]
        
        self.counts_of_flaws_0[0] = 0
        self.counts_of_flaws_1[0] = 0
        self.counts_of_flaws_2[0] = 0
        self.counts_of_flaws_3[0] = 0

        self.mlock.release()
        self.signal_get_error_count.emit(count)



          


    def run(self):
       
        self.thread_4.start()
        # self.thread_5.start()
        # self.thread_6.start()
        # self.thread_7.start()


        self.thread_4.join()
        # self.thread_5.join()
        # self.thread_6.join()
        # self.thread_7.join()