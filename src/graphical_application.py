from PyQt6.QtWidgets    import *
from PyQt6.QtCore       import *
from PyQt6.QtGui        import *

from src.logger import logger    


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

        self.status = 0

        self.count_of_defects = 0
        self.is_line_start = False

        self.worker_thread = QThread(self)
        from src.neural_network import ManagePThread
        self.manage = ManagePThread()

        self.serial_thread = QThread(self)
        from src.com_port import SenderThread
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
        if self.status == 2:
            import subprocess
            subprocess.Popen(['systemctl', 'reboot'])
            return

        self.is_line_start = not self.is_line_start
        self.signal_start_or_stop.emit(self.is_line_start)
        self.signal_start_stop_line.emit(1 if self.is_line_start else 0)
        self.slot_change_status(1 if self.is_line_start else 0)



    @pyqtSlot(int)
    def slot_change_status(self, status):
        self.status = status
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
    def slot_send_critical_error(self, er_id):
        
        if er_id >= 9850 and er_id < 9860:
            logger.warning(f"Был вызван обработчик критических ошибок: {er_id}")
            
            self.is_line_start = False
            self.signal_start_or_stop.emit(self.is_line_start)
            self.signal_start_stop_line.emit(1 if self.is_line_start else 0)
            self.slot_change_status(2)
        elif er_id >= 9750 and er_id < 9760:
            self.is_line_start = False
            self.signal_start_or_stop.emit(self.is_line_start)
            self.signal_start_stop_line.emit(1 if self.is_line_start else 0)
            self.slot_change_status(2)
        else:
            pass
            


            
        # TODO: При возникновении критических ошибок линия должна останавливаться, а также на экране должна отобразиться надпись ОШИБКА


    # Меняет пороговое значение для нейросети
    signal_change_confidence_threshold = pyqtSignal(int, int)
            

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


        layout_vertical_box_main = QVBoxLayout()
        layout_vertical_box_main.addWidget(label_count_of_defects_name, 2)
        layout_vertical_box_main.addWidget(self.label_count_of_defects, 2)
        layout_vertical_box_main.addWidget(button_reset_counter, 1)
        layout_vertical_box_main.addWidget(placeholder, 5)
        layout_vertical_box_main.addWidget(self.label_status, 2)
        layout_vertical_box_main.addWidget(self.button_stop_or_start_line, 4)

        layout_vertical_box_main_widget = QWidget()
        layout_vertical_box_main_widget.setLayout(layout_vertical_box_main)








        tabs = QTabWidget()
        tabs.addTab(layout_vertical_box_main_widget, "Основная")
        tabs.addTab(QWidget(), "Настройки")


        main_layout = QVBoxLayout(self)
        main_layout.addWidget(tabs)


        self.signal_get_error_count.connect(self.manage.slot_get_error_count)        
        self.manage.signal_get_error_count.connect(self.slot_get_error_count)


        self.manage.signal_critical_error.connect(self.slot_send_critical_error)
        self.signal_start_or_stop.connect(self.manage.slot_start_stop)
        self.signal_close_thread.connect(self.manage.slot_exit_thread)
        self.signal_change_confidence_threshold.connect(self.manage.slot_change_confidence_threshold)
        self.manage.moveToThread(self.worker_thread)
        self.worker_thread.start()


        self.signal_start_stop_line.connect(self.manage_serial.slot_start_stop)
        self.manage_serial.signal_critical_error.connect(self.slot_send_critical_error)


        self.manage_serial.moveToThread(self.serial_thread)
        self.serial_thread.start()


        self.show()
