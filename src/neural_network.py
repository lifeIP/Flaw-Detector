from PyQt6.QtWidgets    import *
from PyQt6.QtCore       import *

import os
import cv2
import time
from datetime import datetime
import torch.multiprocessing as mp

from ultralytics import YOLO

from src.logger import logger



MODEL_PATH = "yolo11s.pt"


class ManagePThread(QThread):
    
    signal_critical_error = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        
        # получаем список всех камер
        ids = list()
        for i in range(100):
            try:
                cap = cv2.VideoCapture(i)
                ret, src = cap.read()
                if ret:
                    ids.append(i)
                    cap.release()
            except:
                pass
        
        if(len(ids) < 4):
            logger.warning(f"Критическая ошибка: было найдено только {len(ids)} камер! {ids}")
            self.signal_critical_error.emit(0)

            #TODO: надо сделать автоматический выбор камер и если нет достаточного количества, то должно быть сообщено об ошибке пользователю 
            self.cam_index_0 = ids[0]

        else:
            self.cam_index_0 = ids[0] 
            self.cam_index_1 = ids[1]
            self.cam_index_2 = ids[2]
            self.cam_index_3 = ids[3]


        self.confidence_threshold = 8000 # 0 - 9999
        
        self.manager = mp.Manager()
        self.mlock = mp.Lock()
        
        self.start_or_stop = self.manager.list([False, False])

        self.counts_of_flaws_0 = self.manager.list([0])
        self.counts_of_flaws_1 = self.manager.list([0])
        self.counts_of_flaws_2 = self.manager.list([0])
        self.counts_of_flaws_3 = self.manager.list([0])

        self.start()


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



    def yolo_data_processing(self, cam_index, confidence_threshold, start_or_stop, counts_of_flaws, mlock):
        model = YOLO(MODEL_PATH)
        try:
            model.to('cuda')        
        except:
            pass

        while(True):

            detections = model(cam_index, stream=True)
            
                        
            for obj in detections:
                opencv_array = obj.orig_img
                
                #++++++++++++++++++++++++++++++++++++++++++++++++
                # Этот участок кода должен быть удален для релиза
                directory_empty = f"images/empty/{datetime.today().strftime('%Y/%m/%d')}"
                
                if not os.path.exists(directory_empty):
                    os.makedirs(directory_empty)
                
                cv2.imwrite(f"{directory_empty}/{time.time_ns()}.png", opencv_array)
                # Этот участок кода должен быть удален для релиза
                #------------------------------------------------

                directory_with_boxes = f"images/boxes/{datetime.today().strftime('%Y/%m/%d')}"
                file_name = time.time_ns()
                
                for data in obj.boxes.data.tolist():
                    confidence = data[4]

                    if float(confidence) < float(confidence_threshold)/10000:
                        continue

                    if not start_or_stop[0]:
                        continue
        
                    mlock.acquire()
                    counts_of_flaws[0] += 1
                    logger.warning(f"Обнаружен дефект: {float(confidence)}:{float(confidence_threshold)/10000} *** {directory_with_boxes}/{file_name}.png")
                    start_or_stop[0] = False
                    mlock.release()
              
                    if not os.path.exists(directory_with_boxes):
                        os.makedirs(directory_with_boxes)

                    xmin, ymin, xmax, ymax = int(data[0]), int(data[1]), int(data[2]), int(data[3])
                    cv2.rectangle(opencv_array, (xmin, ymin) , (xmax, ymax), (0, 255, 0), 2)
                    
                    cv2.imwrite(f"{directory_with_boxes}/{file_name}.png", opencv_array)
            


    def run(self):
       
        thread_4 = mp.Process(target=self.yolo_data_processing, args=(self.cam_index_0, self.confidence_threshold, self.start_or_stop, self.counts_of_flaws_0, self.mlock))
        # thread_5 = mp.Process(target=self.yolo_data_processing, args=(self.cam_index_1, self.confidence_threshold, self.start_or_stop, self.counts_of_flaws_1, self.mlock))
        # thread_6 = mp.Process(target=self.yolo_data_processing, args=(self.cam_index_2, self.confidence_threshold, self.start_or_stop, self.counts_of_flaws_2, self.mlock))
        # thread_7 = mp.Process(target=self.yolo_data_processing, args=(self.cam_index_3, self.confidence_threshold, self.start_or_stop, self.counts_of_flaws_3, self.mlock))


        thread_4.start()
        # thread_5.start()
        # thread_6.start()
        # thread_7.start()


        thread_4.join()
        # thread_5.join()
        # thread_6.join()
        # thread_7.join()