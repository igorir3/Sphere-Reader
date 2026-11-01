"""
Selector-box for item           PREVIEW
Select slice                    PREVIEW
select export type              PREVIEW
select path and name            PREVIEW
cancel      done                PREVIEW
"""
if __name__ == '__main__':
    raise SystemError("ЗАПУЩЕН НЕ ИНИЦИАЛИЗИРУЮЩИЙ ФАЙЛ")

from PySide6.QtWidgets import (QWidget, QLabel, QGridLayout, QFileDialog, QMessageBox, QComboBox, QCheckBox, QListWidget, QLineEdit, QPushButton)
from PySide6.QtGui import (QIcon)
import traceback
import classes 
import os
import logging
import winsound

import numpy as np
import tarfile
import io
from scipy.io import savemat
import pandas as pd
import os

DESC = {
#    "tar.zst" : ["Экспорт в сжатый архив", "Сжатый архив"], 
    "mat" : ["Экспорт в данные MATLAB", "MATLAB Data"], 
    "xlsx" : ["Экспорт в Excel данные", "Excel файл"], 
    "csv" : ["Экспорт в текстовую матрицу", "Текстовая матрица"]
} 
TYPES = ["mat", "xlsx", "csv"] # "tar.zst",

def parceSlice(s):
    result = []

    for part in s.split(","):
        part = part.strip()
        if part == "":
            part = ":"

        if ":" not in part:
            result.append(int(part))
            continue

        values = part.split(":")
        values = values + [""] * (3 - len(values))

        start, stop, step = (
            int(x) if x else None
            for x in values[:3]
        )

        result.append(slice(start, stop, step))

    return tuple(result)


class SmartExportWindow(QWidget):
    def __init__(self, prj : classes.Project, app):
        self.PROJECT = prj
        self.APP = app
        self.isClosed = False
        
        super().__init__()
        self.setWindowTitle("Мастер экспорта")
        self.layout = QGridLayout(self)
        self.setLayout(self.layout)
        
        self.itemSelector = QComboBox(self)
        self.itemSelector.currentTextChanged.connect(lambda _: self.onFocusChanged(burned=True))
        self.typeSelected = None
        self.itemSelected = None
        
        ID = 0
        self.listwindgets = {"roots" : []}
        for key in self.PROJECT.DATAS.keys():
            self.itemSelector.addItem(key)
            self.listwindgets[f"roots"].append(key)
            self.listwindgets[f"{ID}"] = []
            for sub_key in self.PROJECT.DATAS[key].keys():
                self.itemSelector.addItem(f"{key}\\{sub_key}")
                self.listwindgets[f"{ID}"].append(f"{key}\\{sub_key}")
            ID = ID + 1
        self.itemSelector.setCurrentIndex(0)
        self.itemSelected = self.itemSelector.currentText()
        self.layout.addWidget(self.itemSelector, 0, 0, 1, 4)
        
        self.transposeButton = QCheckBox(self, text="Повернуть")
        self.layout.addWidget(self.transposeButton, 1, 0, 1, 4)
        self.transposeButton.stateChanged.connect(lambda _: self.onFocusChanged(burned=True))
        
        self.sliceLabel = QLabel("Отрезок:")
        self.sliceX = QLineEdit(self)
        self.sliceY = QLineEdit(self)
        self.sliceY.setText(" ")
        self.sliceY.setReadOnly(True)
        
        self.sliceX.textChanged.connect(lambda _: self.onFocusChanged(burned=True))
        self.sliceY.textChanged.connect(lambda _: self.onFocusChanged(burned=True))
        
        item = self.checkItem(self.itemSelected) 
        
        self.sliceX.setPlaceholderText(f"0:{item["size"][0]}")
        self.sliceY.setPlaceholderText(f"0:{item["size"][1]}")
        
        self.layout.addWidget(self.sliceLabel, 2, 0, 1, 1)
        self.layout.addWidget(self.sliceX, 2, 1, 1, 1)
        self.layout.addWidget(self.sliceY, 2, 2, 1, 1)
        
        self.typeSelector = QListWidget(self)
        for key in TYPES:
            if item[key]:
                self.typeSelector.addItem(key)
        self.typeSelector.setCurrentRow(0)
        self.typeSelected = self.typeSelector.currentItem().text()
        self.typeSelector.itemClicked.connect(lambda _: self.onFocusChanged(burned=True))
        
        self.layout.addWidget(self.typeSelector, 3, 0, 3, 4)

        self.path = QLineEdit(str(os.path.join(os.getenv("HOME"), f"output.{self.typeSelected}") if os.getenv("HOME") is not None else f"output.{self.typeSelected}"))
        self.path.textChanged.connect(lambda _: self.onFocusChanged(burned=True))
        self.layout.addWidget(self.path, 6, 0, 1, 3)

        self.pathButton = QPushButton()
        self.pathButton.setIcon(QIcon.fromTheme("folder"))
        self.pathButton.clicked.connect(self.selectPath)
        self.layout.addWidget(self.pathButton, 6, 3, 1, 1)
        
        self.cancelButton = QPushButton(self, text="Отмена")
        self.proceedButton = QPushButton(self, text="Экспорт")
        self.layout.addWidget(self.cancelButton, 7, 0, 1, 1)
        self.layout.addWidget(self.proceedButton, 7, 3, 1, 1)
        self.cancelButton.clicked.connect(self.cancel)
        self.proceedButton.clicked.connect(self.proceed)
        
        self.needUpdate = False
        app.focusChanged.connect(self.onFocusChanged)
        
    def selectPath(self):
        filename, _ = QFileDialog.getSaveFileName(self, f"{DESC[self.typeSelected][0]}", ".", f"{DESC[self.typeSelected][1]} (*.{self.typeSelected})")
        logging.info(f"|SmartExportWindow|selectPath|\tВыбран: {filename=}")
        if filename:
            try:
                self.path.setText(filename)
            except:
                logging.exception(f"|SmartExportWindow|selectPath|\tОшибка: {traceback.format_exc()}")
                QMessageBox.warning(self, "Ошибка!", traceback.format_exc(), QMessageBox.StandardButton.Cancel)

    def editArray(self, item):
        array = item.copy() if self.transposeButton.isChecked() == False else np.transpose(item)
        if len(array.shape) == 1:
            array = array[parceSlice(self.sliceX.text())]
        elif len(array.shape) == 2:
            array = array[parceSlice(f"{self.sliceX.text()}, {self.sliceY.text()}")]
        return array

    def checkItem(self, itemKey):
        filters = {"tar.zst" : True, "mat" : True, "xlsx" : True, "csv" : True} 
        item = self.PROJECT.getByKey(itemKey)
        logging.info(f"|SmartExportWindow|checkItem|\t{filters=}")
        
        size = [0, 0]
        if type(item) == dict:
            logging.info(f"|SmartExportWindow|checkItem|\tisDict")
            filters["csv"] = False
            for key in item.keys():
                array = self.editArray(item[key])
                    
                shape = [array.shape[0], array.shape[1] if len(array.shape) >= 2 else 0]
                logging.info(f"|SmartExportWindow|checkItem|\t{key} {shape}")
                if shape[0] > 1048575 or shape[1] > 16383:
                    filters["xlsx"] = False
                
                size[0] = max(size[0], shape[0])
                size[1] = max(size[1], shape[1])
        else:
            array = self.editArray(item)
                
            shape = [array.shape[0], array.shape[1] if len(array.shape) >= 2 else 0]
            logging.info(f"|SmartExportWindow|checkItem|\t{shape}")
            if shape[0] > 1048575 or shape[1] > 16383:
                filters["xlsx"] = False
                
            size[0] = max(size[0], shape[0])
            size[1] = max(size[1], shape[1])
                
        filters["size"] = size
        logging.info(f"|SmartExportWindow|checkItem|\t{filters=}")
        return filters
        
    def proceed(self):
        item = self.PROJECT.getByKey(self.itemSelected)
        
        logging.info(f"|SmartExportWindow|proceed|\tЭкспорт {self.typeSelected}: {self.path.text()}")
        try:
            if self.typeSelected == "tar.zst":
                with tarfile.open(name=self.path.text(), mode='w:zst') as archive:
                    if type(item) == dict:
                        for key in item.keys():
                            info = tarfile.TarInfo(name=f"{"_".join(key.split("\\"))}.csv")
                            buffer = io.BytesIO()
                            
                            np.savetxt(buffer, self.editArray(item[key]))
                            info.size = buffer.getbuffer().nbytes
                            buffer.seek(0)
                            
                            archive.addfile(info, buffer)
                    else:
                        info = tarfile.TarInfo(name=f"{"_".join(self.itemSelected.split("\\"))}.csv")
                        buffer = io.BytesIO()
                                                    
                        np.savetxt(buffer, self.editArray(item))
                        info.size = buffer.getbuffer().nbytes
                        buffer.seek(0)
                        
                        archive.addfile(info, buffer)
            
            ##### MAT #####
            
            elif self.typeSelected == "mat":
                dataForSaving = {}
                if type(item) == dict:
                    dataForSaving = item.copy()
                    for key in dataForSaving.keys():
                        dataForSaving[key] = self.editArray(dataForSaving[key])
                else:
                    dataForSaving = {"data" : self.editArray(item)}

                savemat(self.path.text(), dataForSaving, do_compression=True)
            
            ##### XLSX #####
            
            elif self.typeSelected == "xlsx":
                with pd.ExcelWriter(self.path.text(), engine="xlsxwriter") as writer:
                    if type(item) == dict:
                        for key in item.keys():
                            pd.DataFrame(self.editArray(item[key])).to_excel(
                                writer,
                                sheet_name=f"{key}",
                                index=False,
                                header=False,
                            )
                    else:
                        pd.DataFrame(self.editArray(item)).to_excel(
                            writer,
                            sheet_name=f"worksheet",
                            index=False,
                            header=False,
                        )
            
            ##### XLSX #####
            
            elif self.typeSelected == "csv":
                if type(item) == dict:
                    logging.warning(f"|SmartExportWindow|proceed|\tDict не может быть записан в .csv файл")
                    raise SystemError("Dict не может быть записан в .csv файл")
                np.savetxt(self.path.text(), self.editArray(item))
        except:
            QMessageBox.warning(self, "Ошибка!", traceback.format_exc(), QMessageBox.StandardButton.Cancel)
            logging.exception(f"|MainWindow|\tОшибка: {traceback.format_exc()}")
            winsound.MessageBeep(winsound.MB_ICONERROR)
            
        winsound.MessageBeep(winsound.MB_ICONINFORMATION)
            
    def closeEvent(self, event):
        self.destroy()
        self.isClosed = True
        event.accept()
        
    def cancel(self):
        self.destroy()
        self.isClosed = True
    
    def onFocusChanged(self, burned = False):
        if self.isActiveWindow() and (self.needUpdate or burned):
            try:
                self.typeSelected = self.typeSelector.currentItem().text()
            except Exception as e:
                logging.error(f"|SmartExportWindow|onFocusChanged|\t{e}")
                self.typeSelector.setCurrentRow(0)
                self.typeSelected = self.typeSelector.currentItem().text()
            self.itemSelected = self.itemSelector.currentText()
            logging.info(f"|SmartExportWindow|onFocusChanged|{self.itemSelected=}")
            logging.info(f"|SmartExportWindow|onFocusChanged|{self.typeSelected=}")
            
            item = self.checkItem(self.itemSelected) 
            
            self.sliceX.setPlaceholderText(f"0:{item["size"][0]}")
            self.sliceY.setPlaceholderText(f"0:{item["size"][1]}")

            if item["size"][1] == 0:
                self.sliceY.setText(" ")
                self.sliceY.setReadOnly(True)
            else:
                self.sliceY.clear()
                self.sliceY.setReadOnly(False)
            self.sliceX.update()
            self.sliceY.update()    
            
            item = self.checkItem(self.itemSelected) 
            
            path = self.path.text()
            if path.endswith(self.typeSelected) == False:
                path = list(os.path.split(path))
                path[1] = path[1].split(".")[0]
                self.path.setText(f"{os.path.join(*path)}.{self.typeSelected}")
                self.path.update()
                
            self.typeSelector.clear()
            addedTypes = []
            for key in TYPES:
                if item[key]:
                    self.typeSelector.addItem(key)
                    addedTypes.append(key)
            self.typeSelector.setCurrentRow(addedTypes.index(self.typeSelected))
            
            self.needUpdate = False
        elif not(self.isActiveWindow()):
            self.needUpdate = True