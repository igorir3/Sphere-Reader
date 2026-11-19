import logging
from datetime import datetime
import os
import argparse

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
    
    parser = argparse.ArgumentParser()
    parser.add_argument('prj_file', type=str, help='Файл проекта для открытия при запуске', default=None, nargs='?')
    args = parser.parse_args()
    
    PROJECT = classes.Project()
    if args.prj_file:
        if os.path.exists(args.prj_file):
            PROJECT.LoadProject(args.prj_file)
            
    logging.info(f"Проект инициализирован: {str(PROJECT.DATAS)=}")
    multiprocessing.freeze_support()

    app = QApplication(sys.argv)
    window = MainWindow(PROJECT, app)
    app.exec()