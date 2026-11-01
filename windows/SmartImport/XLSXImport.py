if __name__ == '__main__':
    raise SystemError("ЗАПУЩЕН НЕ ИНИЦИАЛИЗИРУЮЩИЙ ФАЙЛ")

from PySide6.QtWidgets import (QWidget, QGridLayout, QMessageBox, QComboBox, QCheckBox, QListWidget, QLineEdit, QPushButton)
import traceback
import numpy as np
import pandas as pd
import logging

class XLSXImportWindow(QWidget):
    def __init__(self, prj, app, filename):
        self.PROJECT = prj
        self.APP = app
        self.filename = filename
        self.needUpdate = False
        self.isClosed = False
        
        super().__init__()
        self.setWindowTitle("Импорт XLSX")
        self.layout = QGridLayout(self)
        self.setLayout(self.layout)
                
        self.array = pd.read_excel(filename, sheet_name=None)
        
        self.path = QLineEdit(self, text=filename)
        self.path.setReadOnly(True)
        self.layout.addWidget(self.path, 1, 0, 1, 3)
        
        worksheets = list(self.array.keys())
        self.selectsheets = QListWidget(self)
        self.selectsheets.setSelectionMode(QListWidget.MultiSelection)
        self.selectsheets.addItems(worksheets)
        self.layout.addWidget(self.selectsheets, 2, 0, 3, 3)
        
        self.dirSelector = QComboBox(self)
        self.listwindgets = []
        for key in self.PROJECT.DATAS.keys():
            self.dirSelector.addItem(key)
            self.listwindgets.append(key)
        self.dirSelector.setCurrentIndex(0)
        self.layout.addWidget(self.dirSelector, 5, 0, 1, 3)
        
        self.transposeButton = QCheckBox(self, text="Повернуть")
        self.layout.addWidget(self.transposeButton,  6, 0, 1, 3)
        self.transposeButton.stateChanged.connect(lambda _: self.onFocusChanged(burned=True))
        
        self.cancelButton = QPushButton(self, text="Отмена")
        self.proceedButton = QPushButton(self, text="Импорт")
        self.layout.addWidget(self.cancelButton, 7, 0, 1, 1)
        self.layout.addWidget(self.proceedButton, 7, 2, 1, 1)
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
            pass
        elif not(self.isActiveWindow()):
            self.needUpdate = True

    def proceed(self):
        try:
            forAbortTempDict = self.PROJECT.DATAS.copy()
            for sheet in self.selectsheets.selectedItems():
                if sheet.text() in self.PROJECT.DATAS[self.dirSelector.currentText()].keys():
                    logging.warning(f"|XLSXImportWindow|proceed|\tМассив с таким же ключом ({self.dirSelector.currentText()}\\{sheet.text()}) уже присутсвует в проекте.")
                    result = QMessageBox.question(self, "Предупреждение", f"Массив с таким же ключом ({self.dirSelector.currentText()}\\{sheet.text()}) уже присутсвует в проекте. Хотите ли вы заменить его?", QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.Cancel, QMessageBox.StandardButton.Abort)
                    logging.info(f"|XLSXImportWindow|proceed|\tUSER ==> {result}")
                    
                    if result == QMessageBox.StandardButton.Yes:
                        self.PROJECT.DATAS[self.dirSelector.currentText()][sheet.text()] = np.transpose(np.squeeze(self.array[sheet.text()].to_numpy())) if self.transposeButton.isChecked() else np.squeeze(self.array[sheet.text()].to_numpy())
                    elif result == QMessageBox.StandardButton.Abort:
                        self.PROJECT.DATAS.clear()
                        self.PROJECT.DATAS = forAbortTempDict.copy()
                        del forAbortTempDict
                        return
                else:
                    self.PROJECT.DATAS[self.dirSelector.currentText()][sheet.text()] = np.transpose(np.squeeze(self.array[sheet.text()].to_numpy())) if self.transposeButton.isChecked() else np.squeeze(self.array[sheet.text()].to_numpy())
            del forAbortTempDict
            self.destroy()
            self.isClosed = True
            self.PROJECT.edited = True
        except:
            logging.exception(f"|XLSXImportWindow|proceed|\tОшибка {traceback.format_exc()}")
            QMessageBox.warning(self, "Ошибка!", traceback.format_exc(), QMessageBox.StandardButton.Cancel)