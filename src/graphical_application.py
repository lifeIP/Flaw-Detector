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

        self.confidence_threshold_0 = 0
        self.confidence_threshold_1 = 0
        self.confidence_threshold_2 = 0
        self.confidence_threshold_3 = 0

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


        with open("./settings.st", "r") as file:
            lines = file.readlines()

            self.confidence_threshold_0 = lines[0].rstrip()
            self.confidence_threshold_1 = lines[1].rstrip()
            self.confidence_threshold_2 = lines[2].rstrip()
            self.confidence_threshold_3 = lines[3].rstrip()
            

        self.initUI()

        self.login("")
        
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
        # TODO: Надо раскоментировать
        # if er_id >= 9850 and er_id < 9860:
        #     logger.warning(f"Был вызван обработчик критических ошибок: {er_id}")
            
        #     self.is_line_start = False
        #     self.signal_start_or_stop.emit(self.is_line_start)
        #     self.signal_start_stop_line.emit(1 if self.is_line_start else 0)
        #     self.slot_change_status(2)
        # elif er_id >= 9750 and er_id < 9760:
        #     self.is_line_start = False
        #     self.signal_start_or_stop.emit(self.is_line_start)
        #     self.signal_start_stop_line.emit(1 if self.is_line_start else 0)
        #     self.slot_change_status(2)
        # else:
            pass
            


            
        # TODO: При возникновении критических ошибок линия должна останавливаться, а также на экране должна отобразиться надпись ОШИБКА


    # Меняет пороговое значение для нейросети
    signal_change_confidence_threshold = pyqtSignal(int, int)
    

    def change_confidence_threshold_0(self, value):
        if value == "": self.confidence_threshold_0 = int(self.lineEdit_confidence_threshold_0.placeholderText())
        else: self.confidence_threshold_0 = int(value)
        self.signal_change_confidence_threshold.emit(self.confidence_threshold_0, 0)

    def change_confidence_threshold_1(self, value):
        if value == "": self.confidence_threshold_1 = int(self.lineEdit_confidence_threshold_1.placeholderText())
        else: self.confidence_threshold_1 = int(value)
        self.signal_change_confidence_threshold.emit(self.confidence_threshold_0, 1)
    
    def change_confidence_threshold_2(self, value):
        if value == "": self.confidence_threshold_2 = int(self.lineEdit_confidence_threshold_2.placeholderText())
        else: self.confidence_threshold_2 = int(value)
        self.signal_change_confidence_threshold.emit(self.confidence_threshold_0, 2)
    
    def change_confidence_threshold_3(self, value):
        if value == "": self.confidence_threshold_3 = int(self.lineEdit_confidence_threshold_3.placeholderText())
        else: self.confidence_threshold_3 = int(value)
        self.signal_change_confidence_threshold.emit(self.confidence_threshold_0, 3)
    

    def login(self, password):
        
        if password == "admin123":
            self.flag = False
            self.label_2.setText("<b style='color: green;'>***Пароль введен***</b>")
        else:
            self.flag = True
            self.label_2.setText("<b style='color: red;'>***Введите пароль***</b>")

        
        self.lineEdit_confidence_threshold_0.setEnabled(not self.flag)
        self.lineEdit_confidence_threshold_1.setEnabled(not self.flag)
        self.lineEdit_confidence_threshold_2.setEnabled(not self.flag)
        self.lineEdit_confidence_threshold_3.setEnabled(not self.flag)
        self.saveButton.setEnabled(not self.flag)
        self.cancelButton.setEnabled(not self.flag)
        

    def btnSavePressed(self):
        with open("./settings.st", "w") as file:

            lines = [self.confidence_threshold_0,
                     self.confidence_threshold_1, 
                     self.confidence_threshold_2,
                     self.confidence_threshold_3]
            
            
            for line in lines: 
                file.write(str(line) + '\n')

        self.lineEdit_confidence_threshold_0.setPlaceholderText(f"{self.confidence_threshold_0}")
        self.lineEdit_confidence_threshold_1.setPlaceholderText(f"{self.confidence_threshold_1}")
        self.lineEdit_confidence_threshold_2.setPlaceholderText(f"{self.confidence_threshold_2}")
        self.lineEdit_confidence_threshold_3.setPlaceholderText(f"{self.confidence_threshold_3}")

        self.lineEdit_password.clear()
        self.login("")
        
        # TODO: Надо сделать отправку
        

    def btnCancelPressed(self):
        self.lineEdit_confidence_threshold_0.clear()
        self.lineEdit_confidence_threshold_1.clear()
        self.lineEdit_confidence_threshold_2.clear()
        self.lineEdit_confidence_threshold_3.clear()

        self.confidence_threshold_0 = int(self.lineEdit_confidence_threshold_0.placeholderText())
        self.confidence_threshold_1 = int(self.lineEdit_confidence_threshold_1.placeholderText())
        self.confidence_threshold_2 = int(self.lineEdit_confidence_threshold_2.placeholderText())
        self.confidence_threshold_3 = int(self.lineEdit_confidence_threshold_3.placeholderText())

        self.lineEdit_password.clear()
        self.login("")
        


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



        self.label_2 = QLabel()
        self.label_2.setText("<b style='color: red;'>***Введите пароль***</b>")
        self.label_2.setWordWrap(True)
        self.label_2.setFont(QFont(None, 20))
        self.label_2.setAlignment(Qt.AlignmentFlag.AlignCenter)


        #++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        # Работа с паролем ++++++++++++++++++++++++++++++++++++++
        self.lineEdit_password = QLineEdit()
        self.lineEdit_password.textChanged.connect(self.login)
        self.lineEdit_password.setFont(QFont(None, 20))
        self.lineEdit_password.setEchoMode(QLineEdit.EchoMode.Password)

        lable_password_name = QLabel("Пароль")
        lable_password_name.setFont(QFont(None, 20))
        
        self.formLayout_2 = QFormLayout()
        self.formLayout_2.addRow(lable_password_name, self.lineEdit_password)

        self.saveButton = QPushButton("Сохранить")
        self.saveButton.setFont(QFont(None, 20))
        self.saveButton.pressed.connect(self.btnSavePressed)
        
        self.cancelButton = QPushButton("Откатить")
        self.cancelButton.setFont(QFont(None, 20))
        self.cancelButton.pressed.connect(self.btnCancelPressed)

        h_box_layout_buttons = QHBoxLayout()
        h_box_layout_buttons.addWidget(self.saveButton, 1)
        h_box_layout_buttons.addWidget(self.cancelButton, 1)
        
        # Работа с паролем --------------------------------------
        #--------------------------------------------------------
        



        #++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        # Настройка порогового значения++++++++++++++++++++++++++
        self.lineEdit_confidence_threshold_0 = QLineEdit()
        self.lineEdit_confidence_threshold_0.textChanged.connect(self.change_confidence_threshold_0)
        self.lineEdit_confidence_threshold_0.setValidator(QIntValidator())
        self.lineEdit_confidence_threshold_0.setMaxLength(4)
        self.lineEdit_confidence_threshold_0.setPlaceholderText(f"{self.confidence_threshold_0}")
        self.lineEdit_confidence_threshold_0.setFont(QFont(None, 20))


        self.lineEdit_confidence_threshold_1 = QLineEdit()
        self.lineEdit_confidence_threshold_1.textChanged.connect(self.change_confidence_threshold_1)
        self.lineEdit_confidence_threshold_1.setValidator(QIntValidator())
        self.lineEdit_confidence_threshold_1.setMaxLength(4)
        self.lineEdit_confidence_threshold_1.setPlaceholderText(f"{self.confidence_threshold_1}")
        self.lineEdit_confidence_threshold_1.setFont(QFont(None, 20))


        self.lineEdit_confidence_threshold_2 = QLineEdit()
        self.lineEdit_confidence_threshold_2.textChanged.connect(self.change_confidence_threshold_2)
        self.lineEdit_confidence_threshold_2.setValidator(QIntValidator())
        self.lineEdit_confidence_threshold_2.setMaxLength(4)
        self.lineEdit_confidence_threshold_2.setPlaceholderText(f"{self.confidence_threshold_2}")
        self.lineEdit_confidence_threshold_2.setFont(QFont(None, 20))


        self.lineEdit_confidence_threshold_3 = QLineEdit()
        self.lineEdit_confidence_threshold_3.textChanged.connect(self.change_confidence_threshold_3)
        self.lineEdit_confidence_threshold_3.setValidator(QIntValidator())
        self.lineEdit_confidence_threshold_3.setMaxLength(4)
        self.lineEdit_confidence_threshold_3.setPlaceholderText(f"{self.confidence_threshold_3}")
        self.lineEdit_confidence_threshold_3.setFont(QFont(None, 20))


        label_PZ_0 = QLabel("ПЗ 1 (0-9999)")
        label_PZ_0.setFont(QFont(None, 20))

        label_PZ_1 = QLabel("ПЗ 2 (0-9999)")
        label_PZ_1.setFont(QFont(None, 20))

        label_PZ_2 = QLabel("ПЗ 3 (0-9999)")
        label_PZ_2.setFont(QFont(None, 20))

        label_PZ_3 = QLabel("ПЗ 4 (0-9999)")
        label_PZ_3.setFont(QFont(None, 20))

        self.formLayout_1 = QFormLayout()
        self.formLayout_1.addRow(label_PZ_0, self.lineEdit_confidence_threshold_0)
        self.formLayout_1.addRow(label_PZ_1, self.lineEdit_confidence_threshold_1)
        self.formLayout_1.addRow(label_PZ_2, self.lineEdit_confidence_threshold_2)
        self.formLayout_1.addRow(label_PZ_3, self.lineEdit_confidence_threshold_3)
        # Настройка порогового значения--------------------------
        #--------------------------------------------------------

        


        
        placeholder2 = QWidget()
        placeholder2.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)
        
        v_box_layout_settings_widget = QVBoxLayout()
        v_box_layout_settings_widget.addLayout(self.formLayout_1)
        v_box_layout_settings_widget.addWidget(placeholder2)
        v_box_layout_settings_widget.addWidget(self.label_2)
        v_box_layout_settings_widget.addLayout(self.formLayout_2)
        v_box_layout_settings_widget.addLayout(h_box_layout_buttons)
        
        settings_widget = QWidget()
        settings_widget.setLayout(v_box_layout_settings_widget)


        tabs = QTabWidget()
        tabs.addTab(layout_vertical_box_main_widget, "Главная")
        tabs.addTab(settings_widget, "Настройки")
        tabs.addTab(QWidget(), "О программе")


        main_layout = QVBoxLayout(self)
        main_layout.addWidget(tabs)


        self.signal_get_error_count.connect(self.manage.slot_get_error_count)        
        self.manage.signal_get_error_count.connect(self.slot_get_error_count)


        self.signal_change_confidence_threshold.connect(self.manage.slot_change_confidence_threshold)
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
