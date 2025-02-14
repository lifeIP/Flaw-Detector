import sys

from PyQt6.QtWidgets    import *

from src.graphical_application import App
from src.logger import logger, init_logger





if __name__ == "__main__":

    # Начиаем логирование
    init_logger()
    logger.warning(f"Приложение запущено")
    
    # Запуск графического приложения
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec())
    
