from PyQt6.QtWidgets    import *
from PyQt6.QtCore       import *
from PyQt6.QtGui        import *

import serial

from src.logger import logger

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
        

        try:
            self.serial_port = serial.Serial(self.port)
            self.serial_port.baudrate=9600
        except:
            pass

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
                    try:
                        self.serial_port = serial.Serial(self.port)
                        self.serial_port.baudrate=9600
                    except:
                        pass