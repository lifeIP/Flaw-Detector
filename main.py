import os
import sys
import cv2
import serial.serialutil
import torchvision.transforms.functional
from ultralytics import YOLO


import torch
import torch.multiprocessing as mp
import torchvision


import time
from PIL import Image
from datetime import datetime
import logging

from PyQt6.QtWidgets    import *
from PyQt6.QtCore       import *
from PyQt6.QtGui        import *

import serial

IS_DEBUG = True
ID = 0
MODEL_PATH = "yolo11s.pt"


logger = logging.getLogger(__name__)



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
        model.to('cuda')        
        while(True):

            detections = model(cam_index, stream=True)
            
                        
            for obj in detections:
                opencv_array = cv2.cvtColor(obj.orig_img, cv2.COLOR_RGB2BGR)
                
                # directory_empty = f"images/empty/{datetime.today().strftime('%Y/%m/%d')}"
                
                # if not os.path.exists(directory_empty):
                #     os.makedirs(directory_empty)
                
                # cv2.imwrite(f"{directory_empty}/{time.time_ns()}.png", opencv_array)


                directory_with_boxes = f"images/boxes/{datetime.today().strftime('%Y/%m/%d')}"
                file_name = time.time_ns()
                
                for data in obj.boxes.data.tolist():
                    # extract the confidence (i.e., probability) associated with the detection
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

    


class SenderThread(QThread):

    pyqtSlot(bool)
    def slot_start_stop(self, flag:bool):
        self.line_is_start = "green" if flag else "red"

    def __init__(self):
        super().__init__()
        
        is_found = False
        self.port = ""

        for i in range(64) :
            try :
                self.port = f"/dev/ttyACM{i}"
                ser = serial.Serial(self.port)
                ser.close()
                is_found = True
                break

            except serial.serialutil.SerialException:
                pass

        if not is_found:
            logger.warning(f"Критическая ошибка: не было найдено подключенного com-порт устройства")
            return
        
        self.serial_port = serial.Serial(self.port)
        self.serial_port.baudrate=9600

        self.line_is_start = "red"
        
        self.start()


    def run(self):
        while True:
            
            try:
                self.serial_port.writelines([self.line_is_start.encode()])
                line = self.serial_port.readline()
                
                if "ONLINE" not in line:
                    logger.warning(f"Критическая ошибка: Не было получено корректного ответа от платы управления")

            except:
                is_found = False
                
                try:
                    self.serial_port.close()
                except:
                    pass

                for i in range(64) :
                    try :
                        self.port = f"/dev/ttyACM{i}"
                        ser = serial.Serial(self.port)
                        ser.close()
                        is_found = True
                        break

                    except serial.serialutil.SerialException:
                        pass

                if not is_found:
                    logger.warning(f"Критическая ошибка: не было найдено подключенного com-порт устройства")
                else:
                    self.serial_port = serial.Serial(self.port)
                    self.serial_port.baudrate=9600

        


class App(QWidget):

    def keyPressEvent(self, event):
        # если нажата клавиша F11
        if event.key() == Qt.Key.Key_F11:
            # если в полный экран 
            if self.isFullScreen():
                # вернуть прежнее состояние
                self.showNormal()
            else:
                # иначе во весь экран
                self.showFullScreen()

        elif event.key() == Qt.Key.Key_Escape:
            self.close()


    def __init__(self):
        super().__init__()

        self.title = 'Дефектоскоп'
        self.left = 100
        self.top = 100
        self.width = 640
        self.height = 480

        self.count_of_defects = 0
        self.is_line_start = False

        self.worker_thread = QThread(self)
        self.manage = ManagePThread()

        self.serial_thread = QThread(self)
        self.manage_serial = SenderThread()

        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.slot_timer_timeout)


        self.initUI()
        self.slot_change_status(1 if self.is_line_start else 0)
        self.timer.start(300)


    pyqtSlot()
    def slot_timer_timeout(self):
        self.signal_get_error_count.emit()
        self.timer.start(300)

    signal_start_or_stop = pyqtSignal(bool)
    signal_close_thread = pyqtSignal(bool)

    signal_get_error_count = pyqtSignal()
    

    pyqtSlot(int)
    def slot_get_error_count(self, counts):
    
        if counts != 0:
            self.signal_start_stop_line.emit(0)
            self.is_line_start = False
            self.signal_start_or_stop.emit(self.is_line_start)
            self.slot_change_status(1 if self.is_line_start else 0)
    

        self.count_of_defects += counts
        self.label_count_of_defects.setText(f"{self.count_of_defects}")


    pyqtSlot()
    def slot_reset_defects_counter(self):
        logger.warning(f"Сброс счетчика: {self.count_of_defects} -> 0")
        self.count_of_defects = 0
        self.label_count_of_defects.setText(f"{0}")
        


    def closeEvent(self, e):
        self.signal_close_thread.emit(True)
        logger.warning(f"Приложение закрыто")
        e.accept()


    signal_start_stop_line = pyqtSignal(bool)

    pyqtSlot()
    def slot_button_stop_or_start_line(self):
        self.is_line_start = not self.is_line_start
        self.signal_start_or_stop.emit(self.is_line_start)
        self.signal_start_stop_line.emit(1 if self.is_line_start else 0)
        self.slot_change_status(1 if self.is_line_start else 0)



    @pyqtSlot(int)
    def slot_change_status(self, status):
        if status == 1:
            self.label_status.setText("СТАТУС: <b style='color: green;'>РАБОТЕТ</b>")
            self.button_stop_or_start_line.setText("Остановить дефектоскоп")
            self.line_status = 1
        elif status == 0:
            self.label_status.setText("СТАТУС: <b style='color: blue;'>ОСТАНОВЛЕН</b>")
            self.button_stop_or_start_line.setText("Запустить дефектоскоп")
            self.line_status = 0
        elif status == 2:
            self.label_status.setText("СТАТУС: <b style='color: red;'>ОШИБКА</b>")
            self.line_status = 2
            self.button_stop_or_start_line.setText("ПЕРЕЗАГРУЗКА")


    pyqtSlot(int)
    def slot_critical_error(self, er_id):
        print("critical_error", er_id)
        # TODO: При возникновении критических ошибок линия должна останавливаться, а также на экране должна отобразиться надпись ОШИБКА

            

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        label_count_of_defects_name = QLabel("КОЛИЧЕСТВО ДЕФЕКТОВ")
        label_count_of_defects_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_count_of_defects_name.setFont(QFont(None, 28))


        self.label_count_of_defects = QLabel(f"{self.count_of_defects}")
        self.label_count_of_defects.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_count_of_defects.setFont(QFont(None, 62))


        button_reset_counter = QPushButton("СБРОСИТЬ СЧЕТЧИК")
        button_reset_counter.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)
        button_reset_counter.setFont(QFont(None, 28))
        button_reset_counter.clicked.connect(self.slot_reset_defects_counter)


        self.label_status = QLabel("СТАТУС")
        self.label_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_status.setFont(QFont(None, 28))


        placeholder = QWidget()
        placeholder.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)


        self.button_stop_or_start_line = QPushButton()
        self.button_stop_or_start_line.setText("Запустить дефектоскоп")
        self.button_stop_or_start_line.clicked.connect(self.slot_button_stop_or_start_line)
        self.button_stop_or_start_line.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)
        self.button_stop_or_start_line.setFont(QFont(None, 28))


        layout_vertical_box_main = QVBoxLayout(self)
        layout_vertical_box_main.addWidget(label_count_of_defects_name, 2)
        layout_vertical_box_main.addWidget(self.label_count_of_defects, 2)
        layout_vertical_box_main.addWidget(button_reset_counter, 1)
        layout_vertical_box_main.addWidget(placeholder, 5)
        layout_vertical_box_main.addWidget(self.label_status, 2)
        layout_vertical_box_main.addWidget(self.button_stop_or_start_line, 4)


        self.signal_get_error_count.connect(self.manage.slot_get_error_count)        
        self.manage.signal_get_error_count.connect(self.slot_get_error_count)


        self.manage.signal_critical_error.connect(self.slot_critical_error)
        self.signal_start_or_stop.connect(self.manage.slot_start_stop)
        self.signal_close_thread.connect(self.manage.slot_exit_thread)
        self.manage.moveToThread(self.worker_thread)
        self.worker_thread.start()


        
        self.signal_start_stop_line.connect(self.manage_serial.slot_start_stop)
        self.manage_serial.moveToThread(self.serial_thread)
        self.serial_thread.start()


        self.show()



if __name__ == "__main__":

    try:
        import shutil
        shutil.move("flaw.log", f"logs/{int(time.time())}.log")
        open('flaw.log', 'w').close()
    except:
        open('flaw.log', 'w').close()
        

    # Начиаем логирование
    FORMAT = '%(asctime)s %(message)s'
    logging.basicConfig(format=FORMAT, filename="flaw.log")
    logger.warning(f"Приложение запущено")
    
    # Запуск графического приложения
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec())
    
