from PyQt6.QtWidgets    import *
from PyQt6.QtCore       import *
from PyQt6.QtGui        import *

import serial
import time

from src.logger import logger

class SenderThread(QThread):
    signal_critical_error = pyqtSignal(int)

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

            except:
                pass

        if not is_found:
            logger.warning(f"Критическая ошибка: не было найдено подключенного com-порт устройства")
            self.signal_critical_error.emit(9850)
            

        try:
            self.serial_port = serial.Serial(self.port)
            self.serial_port.baudrate=9600
        except:
            logger.warning(f"Не получилось получить доступ к COM-порту: {self.port}, id: 0")
            self.signal_critical_error.emit(9851)
            

        self.line_is_start = "red"
        self.start()


    def run(self):
        while True:
            try:
                self.serial_port.writelines([self.line_is_start.encode()])
                line = self.serial_port.readline()
                
                if "ONLINE" not in line:
                    logger.warning(f"Критическая ошибка: Не было получено корректного ответа от платы управления")
                    self.signal_critical_error.emit(9852)
                    return

            except:
                is_found = False
                
                try:
                    self.serial_port.close()
                except:
                    logger.warning(f"Не удалось закрыть COM-порт: {self.port}")
                    self.signal_critical_error.emit(9853)
                    return

                for i in range(64) :
                    try :
                        self.port = f"/dev/ttyACM{i}"
                        ser = serial.Serial(self.port)
                        ser.close()
                        is_found = True
                        break

                    except:
                        pass

                if not is_found:
                    logger.warning(f"Критическая ошибка: не было найдено подключенного com-порт устройства")
                    self.signal_critical_error.emit(9854)
                    return
                else:
                    try:
                        self.serial_port = serial.Serial(self.port)
                        self.serial_port.baudrate=9600
                    except:
                        logger.warning(f"Не получилось получить доступ к COM-порту: {self.port}, id: 2")
                        self.signal_critical_error.emit(9855)
                        return
                # time.sleep(15)

                