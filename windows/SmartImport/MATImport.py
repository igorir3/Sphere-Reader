if __name__ == '__main__':
    raise SystemError("ЗАПУЩЕН НЕ ИНИЦИАЛИЗИРУЮЩИЙ ФАЙЛ")

from PySide6.QtWidgets import (QWidget, QGridLayout, QMessageBox, QComboBox, QCheckBox, QListWidget, QLineEdit, QPushButton)
import traceback
import scipy
from collections.abc import Mapping
import numpy as np
import logging

class MATImportWindow(QWidget):
    def __init__(self, prj, app, filename):
        self.PROJECT = prj
        self.APP = app
        self.filename = filename
        self.needUpdate = False
        self.isClosed = False
        
        super().__init__()
        self.setWindowTitle("Импорт MATLAB")
        self.layout = QGridLayout(self)
        self.setLayout(self.layout)
                
        self.array = self.flatten_data(self.loadmat(filename))
        
        self.path = QLineEdit(self, text=filename)
        self.path.setReadOnly(True)
        self.layout.addWidget(self.path, 1, 0, 1, 3)
        
        worksheets = list(self.array.keys())
        self.selectsheets = QListWidget(self)
        self.selectsheets.setSelectionMode(QListWidget.MultiSelection)
        self.selectsheets.addItems(worksheets)
        self.layout.addWidget(self.selectsheets, 2, 0, 3, 3)
        
        self.pathTransmutationButton = QCheckBox(self, text="Перенос путей данных")
        self.layout.addWidget(self.pathTransmutationButton,  5, 0, 1, 3)
        self.pathTransmutationButton.stateChanged.connect(lambda _: self.onFocusChanged(burned=True))
        
        self.dirSelector = QComboBox(self)
        self.listwindgets = []
        for key in self.PROJECT.DATAS.keys():
            self.dirSelector.addItem(key)
            self.listwindgets.append(key)
        self.dirSelector.setCurrentIndex(0)
        self.layout.addWidget(self.dirSelector, 6, 0, 1, 3)
        
        self.transposeButton = QCheckBox(self, text="Повернуть")
        self.layout.addWidget(self.transposeButton,  7, 0, 1, 3)
        self.transposeButton.stateChanged.connect(lambda _: self.onFocusChanged(burned=True))
        
        self.cancelButton = QPushButton(self, text="Отмена")
        self.proceedButton = QPushButton(self, text="Импорт")
        self.layout.addWidget(self.cancelButton, 8, 0, 1, 1)
        self.layout.addWidget(self.proceedButton, 8, 2, 1, 1)
        self.cancelButton.clicked.connect(self.cancel)
        self.proceedButton.clicked.connect(self.proceed)

    def loadmat(self, filename):
        def _todict(matobj):
            dict = {}
            for strg in matobj._fieldnames:
                elem = matobj.__dict__[strg]
                if isinstance(elem, scipy.io.matlab.mat_struct):
                    dict[strg] = _todict(elem)
                else:
                    dict[strg] = elem
            return dict

        def _check_keys(dict):
            for key in dict:
                if isinstance(dict[key], scipy.io.matlab.mat_struct):
                    dict[key] = _todict(dict[key])
            return dict
        
        logging.info(f"|MATImportWindow|loadmat|\tЧтение {filename=}")
        data = scipy.io.loadmat(filename, struct_as_record=False, squeeze_me=True)

        return _check_keys(data)

    def flatten_data(self, data, prefix=""):
        result = {}

        def walk(obj, path : str):
            if isinstance(obj, Mapping):
                for key, value in obj.items():
                    new_path = f"{path}\\{key}" if path else str(key)
                    walk(value, new_path)
                return
            value = obj
            
            if not isinstance(obj, (str, bytes)) and not np.isscalar(obj):
                try:
                    arr = np.asarray(obj)
                    value = np.squeeze(arr)
                except (TypeError, ValueError):
                    pass
                else:
                    if len(value) > 0:
                        result[path] = value

        walk(data, prefix)
        
        logging.info(f"|MATImportWindow|flatten_data|\t{result.keys()=}")
        return result

    def cancel(self):
        self.destroy()
        self.isClosed = True
    
    def closeEvent(self, event):
        self.destroy()
        self.isClosed = True
        event.accept()
    
    def onFocusChanged(self, burned = False):
        if self.isActiveWindow() and (self.needUpdate or burned):
            if self.pathTransmutationButton.isChecked():
                self.dirSelector.setDisabled(True)
            else:
                self.dirSelector.setEnabled(True)
        elif not(self.isActiveWindow()):
            self.needUpdate = True

    def proceed(self):
        try:
            forAbortTempDict = self.PROJECT.DATAS.copy()
            for sheet in self.selectsheets.selectedItems():
                if self.pathTransmutationButton.isChecked():
                    keys = sheet.text().split("\\")
                    rootkey = keys[0]
                    name = "_".join(keys[1:])
                else:
                    rootkey = self.dirSelector.currentText()
                    name = "_".join(sheet.text().split("\\"))
                    
                logging.info(f"|MATImportWindow|proceed|\t{[rootkey, name]}")
                if rootkey not in self.PROJECT.DATAS.keys():
                    logging.warning(f"|MATImportWindow|proceed|\tНевозможно импортировать имя из MAT ({rootkey}).")
                    result = QMessageBox.warning(self, "Предупреждение", f"Невозможно импортировать имя из MAT ({rootkey}). Он будет пропущен...", QMessageBox.StandardButton.Cancel, QMessageBox.StandardButton.Abort)
                    logging.info(f"|MATImportWindow|proceed|\tUSER ==> {result}")
                    
                    if QMessageBox.StandardButton.Abort:
                        self.PROJECT.DATAS.clear()
                        self.PROJECT.DATAS = forAbortTempDict.copy()
                        del forAbortTempDict
                        return
                    
                if name in self.PROJECT.DATAS[rootkey].keys():
                    logging.warning(f"|MATImportWindow|proceed|\tМассив с таким же ключом ({rootkey}\\{name}) уже присутсвует в проекте.")
                    result = QMessageBox.question(self, "Предупреждение", f"Массив с таким же ключом ({rootkey}\\{name}) уже присутсвует в проекте. Хотите ли вы заменить его?", QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.Abort)
                    logging.info(f"|MATImportWindow|proceed|\tUSER ==> {result}")
                    
                    if result == QMessageBox.StandardButton.Yes:
                        self.PROJECT.DATAS[rootkey][name] = np.transpose(self.array[sheet.text()]) if self.transposeButton.isChecked() else self.array[sheet.text()]
                    elif result == QMessageBox.StandardButton.Abort:
                        self.PROJECT.DATAS.clear()
                        self.PROJECT.DATAS = forAbortTempDict.copy()
                        del forAbortTempDict
                        return
                else:
                    self.PROJECT.DATAS[rootkey][name] = np.transpose(self.array[sheet.text()]) if self.transposeButton.isChecked() else self.array[sheet.text()]
            del forAbortTempDict
            self.destroy()
            self.isClosed = True
            self.PROJECT.edited = True
        except:
            logging.exception(f"|MATImportWindow|proceed|\tОшибка {traceback.format_exc()}")
            QMessageBox.warning(self, "Ошибка!", traceback.format_exc(), QMessageBox.StandardButton.Cancel)