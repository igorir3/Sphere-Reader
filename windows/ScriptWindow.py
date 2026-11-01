if __name__ == '__main__':
    raise SystemError("ЗАПУЩЕН НЕ ИНИЦИАЛИЗИРУЮЩИЙ ФАЙЛ")

from PySide6.QtWidgets import (QWidget, QLabel, QGridLayout, QFileDialog, QMessageBox, QComboBox, QCheckBox, QListWidget, QLineEdit, QPushButton, QSpinBox, QDoubleSpinBox)
from PySide6.QtGui import (QIcon)
import traceback
import classes 
import os
import logging
import winsound

class ScriptWindow(QWidget):
    def __init__(self, prj, app, config):
        self.PROJECT = prj
        self.APP = app
        self.isClosed = False
        
        super().__init__()
        self.setWindowTitle(config["name"])
        self.layout = QGridLayout(self)
        self.setLayout(self.layout)
        self.config = config
        
        self.selectsheets = QListWidget(self)
        if self.config["multiply"]:
            self.selectsheets.setSelectionMode(QListWidget.MultiSelection)
        
        ID = 0
        self.listwindgets = {}
        for key in self.PROJECT.DATAS.keys():
            self.listwindgets[f"{ID}"] = []
            for sub_key in self.PROJECT.DATAS[key].keys():
                if self.config["shape"] is not None:
                    if len(self.PROJECT.DATAS[key][sub_key].shape) in self.config["shape"]:
                        self.selectsheets.addItem(f"{key}\\{sub_key}")
                        self.listwindgets[f"{ID}"].append(f"{key}\\{sub_key}")
                else:
                    self.selectsheets.addItem(f"{key}\\{sub_key}")
                    self.listwindgets[f"{ID}"].append(f"{key}\\{sub_key}")
            ID = ID + 1
            
        self.layout.addWidget(self.selectsheets, 0, 0, 3, 3)
        
        self.paramsCustomItems = {}
        y = 4
        for param in self.config["inputParams"].keys():
            if self.config["inputParams"][param] == int:
                self.paramsCustomItems[param] = QSpinBox()
                self.paramsCustomItems[param].setValue(5)
                self.paramsCustomItems[param].setSingleStep(1)
                self.layout.addWidget(self.paramsCustomItems[param], y, 0, 1, 3)
                y = y + 1
            elif self.config["inputParams"][param] == float:
                self.paramsCustomItems[param] = QDoubleSpinBox()
                self.paramsCustomItems[param].setValue(1.0)
                self.paramsCustomItems[param].setSingleStep(0.1)
                self.layout.addWidget(self.paramsCustomItems[param], y, 0, 1, 3)
                y = y + 1
            elif self.config["inputParams"][param] == str:
                self.paramsCustomItems[param] = QLineEdit()
                self.layout.addWidget(self.paramsCustomItems[param], y, 0, 1, 3)
                y = y + 1
                
        self.chapters = QComboBox(self)
        self.chapterItems = {"roots" : []}
        for key in self.PROJECT.DATAS.keys():
            self.chapters.addItem(key)
            self.chapterItems[f"roots"].append(key)
        self.layout.addWidget(self.chapters, y, 0, 1, 3)
        
        self.name = QLineEdit(self, placeholderText="Имя для сохранения данных")
        self.layout.addWidget(self.name, y+1, 0, 1, 3)
            
        self.proceedButton = QPushButton("Запуск")
        self.layout.addWidget(self.proceedButton, y+2, 0, 1, 1)
        self.cancelButton = QPushButton("Отмена")
        self.layout.addWidget(self.cancelButton, y+2, 2, 1, 1)
        self.needUpdate = False
        self.cancelButton.clicked.connect(self.cancel)
        self.proceedButton.clicked.connect(self.proceed)
        app.focusChanged.connect(self.onFocusChanged)

    def onFocusChanged(self, burned = False):
        global PROJECT
        
        if self.isActiveWindow() and (self.needUpdate or burned):
            pass
        elif not(self.isActiveWindow()):
            self.needUpdate = True
            
    def closeEvent(self, event):
            self.destroy()
            self.isClosed = True
            event.accept()
            
    def proceed(self):
        params = {}
        for key in self.paramsCustomItems.keys():
            if type(self.paramsCustomItems[key]) is QLineEdit:
                params[key] = self.paramsCustomItems[key].text() 
            else:
                params[key] = self.paramsCustomItems[key].value() 
            
        try:
            if self.config["multiply"]:
                data = self.config["exec"]([self.PROJECT.getByKey(item.text()) for item in self.selectsheets.selectedItems()], params)
            else:
                data = self.config["exec"](self.PROJECT.getByKey(self.selectsheets.selectedItems()[0].text()), params)
            self.PROJECT.DATAS[self.chapters.currentText()][self.name.text()] = data
            self.PROJECT.edited = True
        except:
            QMessageBox.warning(self, "Ошибка!", traceback.format_exc(), QMessageBox.StandardButton.Cancel)
            logging.exception(f"|MainWindow|\tОшибка: {traceback.format_exc()}")
            winsound.MessageBeep(winsound.MB_ICONERROR)
            
        winsound.MessageBeep(winsound.MB_ICONINFORMATION)
    
    def cancel(self):
        self.destroy()
        self.isClosed = True