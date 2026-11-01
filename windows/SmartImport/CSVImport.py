if __name__ == '__main__':
    raise SystemError("ЗАПУЩЕН НЕ ИНИЦИАЛИЗИРУЮЩИЙ ФАЙЛ")

from PySide6.QtWidgets import (QWidget, QLabel, QGridLayout, QMessageBox, QComboBox, QCheckBox, QLineEdit, QPushButton)
import traceback
import numpy as np
import os
import pandas as pd
import logging
import csv 

class CSVImportWindow(QWidget):
    def __init__(self, prj, app, filename):
        self.PROJECT = prj
        self.APP = app
        self.filename = filename
        self.needUpdate = False
        self.isClosed = False
        
        super().__init__()
        self.setWindowTitle("Импорт CSV")
        self.layout = QGridLayout(self)
        self.setLayout(self.layout)
        with open(filename, 'r') as fp:
            delimiter = csv.Sniffer().sniff(fp.readline()).delimiter
        self.array = np.loadtxt(filename, delimiter=delimiter)
        self.path = QLineEdit(self, text=filename, readOnly=True)
        self.layout.addWidget(self.path, 0, 0, 1, 3)
        
        self.name = QLineEdit(self, os.path.splitext(os.path.basename(filename)))
        self.layout.addWidget(self.name, 1, 0, 1, 3)
        
        self.dirSelector = QComboBox(self)
        self.listwindgets = []
        for key in self.PROJECT.DATAS.keys():
            self.dirSelector.addItem(key)
            self.listwindgets.append(key)
        self.dirSelector.setCurrentIndex(0)
        self.layout.addWidget(self.dirSelector, 2, 0, 1, 3)
        self.layout.addWidget(self.name, 3, 0, 1, 3)
        
        self.transposeButton = QCheckBox(self, text="Повернуть")
        self.layout.addWidget(self.transposeButton, 4, 0, 1, 3)
        self.transposeButton.stateChanged.connect(lambda _: self.onFocusChanged(burned=True))
        
        self.sizeLabel = QLabel(self, text=f"Форма: {self.array.shape}")
        self.layout.addWidget(self.sizeLabel, 5, 0, 1, 3)
        
        self.cancelButton = QPushButton(self, text="Отмена")
        self.proceedButton = QPushButton(self, text="Импорт")
        self.layout.addWidget(self.cancelButton, 6, 0, 1, 1)
        self.layout.addWidget(self.proceedButton, 6, 2, 1, 1)
        self.cancelButton.clicked.connect(self.cancel)
        self.proceedButton.clicked.connect(self.proceed)

    def cancel(self):
        self.destroy()
        self.isClosed = True
    
    def closeEvent(self, event):
        self.destroy()
        self.isClosed = True
        event.accept()
    
    def onFocusChanged(self, burned = False):
        if self.isActiveWindow() and (self.needUpdate or burned):
            self.sizeLabel.setText(f"Форма: {np.transpose(self.array).shape if self.transposeButton.isChecked() else self.array.shape}")
        elif not(self.isActiveWindow()):
            self.needUpdate = True

    def proceed(self):
        try:
            if len(self.name.text().replace(" ", "")) <= 0:
                logging.warning(f"|CSVImportWindow|proceed|\tИмя не корректно или не введено! '{self.name.text().replace(" ", "")}'")
                raise SystemError("Имя не корректно или не введено!")
            
            if self.name.text() in self.PROJECT.DATAS[self.dirSelector.currentText()].keys():
                logging.warning(f"|CSVImportWindow|proceed|\tМассив с такими же ключами ({self.name.text()}) уже присутсвует в проекте.")
                result = QMessageBox.question(self, "Предупреждение", f"Массив с такими же ключами ({self.name.text()}) уже присутсвует в проекте. Хотите ли вы заменить его?", QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.Cancel)
                
                if result == QMessageBox.StandardButton.Yes:
                    self.PROJECT.DATAS[self.dirSelector.currentText()][self.name.text()] = np.transpose(self.array) if self.transposeButton.isChecked() else self.array
                    self.destroy()
                    self.isClosed = True
                    self.PROJECT.edited = True
                elif result == QMessageBox.StandardButton.Cancel:
                    return
            else:
                self.PROJECT.DATAS[self.dirSelector.currentText()][self.name.text()] = np.transpose(self.array) if self.transposeButton.isChecked() else self.array
                self.destroy()
                self.isClosed = True
                self.PROJECT.edited = True
        except:
            logging.exception(f"|CSVImportWindow|proceed|\tОшибка {traceback.format_exc()}")
            QMessageBox.warning(self, "Ошибка!", traceback.format_exc(), QMessageBox.StandardButton.Cancel)