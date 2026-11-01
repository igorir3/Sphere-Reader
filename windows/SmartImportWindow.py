if __name__ == '__main__':
    raise SystemError("ЗАПУЩЕН НЕ ИНИЦИАЛИЗИРУЮЩИЙ ФАЙЛ")

from PySide6.QtWidgets import (QWidget, QGridLayout, QFileDialog, QMessageBox, QLineEdit, QPushButton)
from PySide6.QtGui import (QIcon)
import traceback
import os
import logging

import sys
sys.path.append('windows\\SmartImport')
from CSVImport import CSVImportWindow
from XLSXImport import XLSXImportWindow
from MATImport import MATImportWindow
import winsound

class SelectPathWindow(QWidget):
    def __init__(self, prj, app):
        self.PROJECT = prj
        self.APP = app
        self.isClosed = False
        self.ImportWindow = None
        
        super().__init__()
        self.setWindowTitle("Выбор файла")
        self.layout = QGridLayout(self)
        self.setLayout(self.layout)
        self.setGeometry(100, 100, 600, 80)
        
        self.path = QLineEdit(self, placeholderText="Полное имя файла")
        self.path.textChanged.connect(lambda _: self.onFocusChanged(burned=True))
        self.layout.addWidget(self.path, 1, 0, 1, 10)

        self.pathButton = QPushButton()
        self.pathButton.setIcon(QIcon.fromTheme("folder"))
        self.pathButton.clicked.connect(self.selectPath)
        self.layout.addWidget(self.pathButton, 1, 10, 1, 1)
        
        self.cancelButton = QPushButton(self, text="Отмена")
        self.proceedButton = QPushButton(self, text="Продолжить")
        self.layout.addWidget(self.cancelButton, 2, 0, 1, 1)
        self.layout.addWidget(self.proceedButton, 2, 10, 1, 1)
        self.cancelButton.clicked.connect(self.cancel)
        self.proceedButton.clicked.connect(self.proceed)
        
        self.needUpdate = False
        app.focusChanged.connect(self.onFocusChanged)
        app.focusWindowChanged.connect(self.onFocusChanged)

    def onFocusChanged(self, burned = False):
        if self.isActiveWindow() and (self.needUpdate or burned):
            pass
        elif self.ImportWindow is not None:
            if self.ImportWindow.isClosed:
                self.destroy()
                self.isClosed = True
        elif not(self.isActiveWindow()):
            self.needUpdate = True
    
    def selectPath(self):
        filename, _ = QFileDialog.getOpenFileName(self)
        logging.info(f"|SelectPathWindow|selectPath|\t{filename=}")
        if filename:
            try:
                self.path.setText(filename)
            except:
                logging.exception(f"|SelectPathWindow|selectPath|\tОшибка: {traceback.format_exc()}")
                QMessageBox.warning(self, "Ошибка!", traceback.format_exc(), QMessageBox.StandardButton.Cancel)
    
    def cancel(self):
        self.destroy()
        self.isClosed = True
        
    def closeEvent(self, event):
        self.destroy()
        self.isClosed = True
        event.accept()
        
    def proceed(self):
        try:
            logging.info(f"|SelectPathWindow|proceed|\tЧтение {self.path.text()}")
            if os.path.exists(self.path.text()):
                if self.path.text().endswith(".csv"):
                    self.ImportWindow = CSVImportWindow(self.PROJECT, self.APP, self.path.text())
                    winsound.MessageBeep(winsound.MB_ICONINFORMATION)
                    self.ImportWindow.show()
                elif self.path.text().endswith(".xlsx"):
                    self.ImportWindow = XLSXImportWindow(self.PROJECT, self.APP, self.path.text())
                    winsound.MessageBeep(winsound.MB_ICONINFORMATION)
                    self.ImportWindow.show()
                elif self.path.text().endswith(".mat"):
                    self.ImportWindow = MATImportWindow(self.PROJECT, self.APP, self.path.text())
                    winsound.MessageBeep(winsound.MB_ICONINFORMATION)
                    self.ImportWindow.show()
                elif self.path.text().endswith(".sgm"):
                    self.PROJECT.loadFromSphere(self.path.text())
                else:
                    logging.warning(f"|SelectPathWindow|proceed|\tДанный тип файлов не поддерживается для импорта")
                    raise SystemError("Данный тип файлов не поддерживается для импорта")
                self.setEnabled(False)
        except:
            logging.exception(f"|SelectPathWindow|proceed|\tОшибка {traceback.format_exc()}")
            QMessageBox.warning(self, "Ошибка!", traceback.format_exc(), QMessageBox.StandardButton.Cancel)