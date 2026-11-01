import logging
from datetime import datetime
import os

from PySide6.QtWidgets import (QApplication)
import multiprocess as multiprocessing

import sys
sys.path.append('windows')

import classes
from MainWindow import MainWindow

if __name__ == '__main__':
    if not(os.path.exists("logs")):
        os.mkdir("logs")
    
    formatter = logging.Formatter('%(asctime)s\t%(levelname)s\t%(message)s')

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(f'logs\\{datetime.now().strftime("%d_%m_%Y-%H_%M_%S")}.log', encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    logging.basicConfig(handlers=[stream_handler, file_handler], level=logging.INFO)
    logging.info("Логгер запущен!")
    
    PROJECT = classes.Project()
    logging.info(f"Проект инициализирован: {str(PROJECT.DATAS)=}")
    multiprocessing.freeze_support()

    app = QApplication(sys.argv)
    window = MainWindow(PROJECT, app)
    app.exec()