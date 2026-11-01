if __name__ == '__main__':
    raise SystemError("ЗАПУЩЕН НЕ ИНИЦИАЛИЗИРУЮЩИЙ ФАЙЛ")


from PySide6.QtWidgets import (QWidget, QGridLayout, QMainWindow, QFileDialog, QMessageBox, QListWidget, QListWidgetItem, QLabel, QPlainTextEdit, QTreeWidget, QTreeWidgetItem)
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtCore import Qt
import os
import classes
import traceback
import logging
import winsound

import sys
sys.path.append('windows')
from SmartExportWindow import SmartExportWindow
from SmartImportWindow import SelectPathWindow as SmartImportWindow
from ScriptWindow import ScriptWindow
from Plotter2D import Plotter2DWindow
from Plotter3D import Plotter3DWindow
from ViewerDashboard import Dashboard
import importlib.util
import pathlib

DESC = {
    "b" : "Показания магнитный датчиков",
    "a" : "Показания акселерометра",
    "w" : "Показания гироскопа",
    "t" : "Показания тензометрических датчиков",
    "c" : "Показания центрального магнитного датчика",
    "sphere" : "Данные загруженные с шара или другого внешнего источника"
}

class MainWindow(QMainWindow):
    def __init__(self, prj : classes.Project, app):
        self.PROJECT = prj
        self.APP = app
        self.scripts = []
        
        super().__init__()
        self.setWindowTitle("PROGRAM")
        self.setGeometry(100, 100, 800, 400)
        self.setAcceptDrops(True)
        
        centralWidget = QWidget()
        self.layout = QGridLayout(self)
        centralWidget.setLayout(self.layout)
        self.setCentralWidget(centralWidget)
        self.needUpdate = False
        
        self.windows = []
        
        menuBar = self.menuBar()
        fileMenu = menuBar.addMenu("Файлы")
        
        ActionNewProject = fileMenu.addAction("Новый проект", )
        ActionNewProject.triggered.connect(self.NewProject)
        ActionNewProject.setShortcut("Ctrl+N")
        fileMenu.addSeparator()
        
        ActionSaveProject = fileMenu.addAction("Сохранить проект")
        ActionSaveProject.triggered.connect(self.SaveProject)
        ActionSaveProject.setShortcut("Ctrl+S")
        ActionSaveProject.setShortcutContext(Qt.ApplicationShortcut)
        
        ActionSaveProject = fileMenu.addAction("Сохранить проект как")
        ActionSaveProject.triggered.connect(lambda: self.SaveProject(RewriteFilename=True))

        ActionLoadProject = fileMenu.addAction("Загрузить проект")
        ActionLoadProject.triggered.connect(self.LoadProject)
        ShortcutSaveProject = QShortcut(QKeySequence("Ctrl+L"), self) 
        ShortcutSaveProject.activated.connect(self.LoadProject)
        
        
        editMenu = menuBar.addMenu("Данные")
        
        ActionAddData = editMenu.addAction("Загрузить с шара")
        ActionAddData.triggered.connect(self.AddData)
        ShortcutAddData = QShortcut(QKeySequence("Ctrl+D"), self)
        ShortcutAddData.activated.connect(self.AddData)
        
        ActionSaveMat = editMenu.addAction("Экспорт в .mat")
        ActionSaveMat.triggered.connect(self.SaveMat)
        
        ActionSaveCsv = editMenu.addAction("Экспорт в .csv")
        ActionSaveCsv.triggered.connect(self.SaveCsv)
        
        editMenu.addSeparator()
        
        ActionSmartExportWindow = editMenu.addAction("Мастер экспорта")
        ActionSmartExportWindow.triggered.connect(lambda: self.showWindow(SmartExportWindow))
        
        ActionSmartImportWindow = editMenu.addAction("Мастер импорта")
        ActionSmartImportWindow.triggered.connect(lambda: self.showWindow(SmartImportWindow))
        
        imageMenu = menuBar.addMenu("Изображение")
        
        Plotter2DAction = imageMenu.addAction("2D график")
        Plotter2DAction.triggered.connect(lambda: self.showWindow(Plotter2DWindow))
        Plotter3DAction = imageMenu.addAction("3D график")
        Plotter3DAction.triggered.connect(lambda: self.showWindow(Plotter3DWindow))
        DashboardAction = imageMenu.addAction("Dashboard")
        DashboardAction.triggered.connect(lambda: self.showWindow(Dashboard))
        
        scriptsMenu = menuBar.addMenu("Скрипты")
        self.scripts = self.load_scripts()
        self.scriptsMenuItems = []
        self.configs = []
        for script in self.scripts:
            self.configs.append(script.config())
            self.configs[-1]["exec"] = script.main
            self.scriptsMenuItems.append(scriptsMenu.addAction(self.configs[-1]["name"]))
            cfg = len(self.configs)-1
            self.scriptsMenuItems[-1].triggered.connect(lambda checked=False, cfg=cfg: self.showScriptWindow(cfg))
        
        self.listWidget = QTreeWidget(self)
        self.listWidget.setHeaderLabel("Данные")
        self.listwindgets = {"roots" : []}
        
        ID = 0
        for key in self.PROJECT.DATAS.keys():
            root = QTreeWidgetItem(self.listWidget, [key])
            self.listwindgets["roots"].append(root)
            self.listwindgets[f"{ID}"] = []
            for sub_key in self.PROJECT.DATAS[key].keys():
                self.listwindgets[f"{ID}"].append(QTreeWidgetItem(root, [f"{key}\\{sub_key}"]))
            ID = ID + 1
        self.selectedItem = None
        self.listWidget.expandAll()
        self.listWidget.itemClicked.connect(self.listWidgetCurrentItemSave)
        self.layout.addWidget(self.listWidget, 0, 0, 5, 5)
        
        self.typeLabel = QLabel(f"Данные : ")
        self.layout.addWidget(self.typeLabel, 0, 5, 1, 5)
        self.formatLabel = QLabel(f"Формат матрицы : ")
        self.layout.addWidget(self.formatLabel, 1, 5, 1, 5)
        self.descLabel = QLabel(f"Описание : ")
        self.layout.addWidget(self.descLabel, 2, 5, 1, 5)
        self.descPlainText = QPlainTextEdit(readOnly=True)
        self.layout.addWidget(self.descPlainText, 3, 5, 2, 5)
        
        app.focusChanged.connect(self.OnFocusChanged)
        self.show()
    def showScriptWindow(self, configIndex):
        logging.info(f"|MainWindow|\tОтображение скрипта {configIndex}: {self.configs[configIndex]["name"]}")
        self.windows.append(ScriptWindow(self.PROJECT, self.APP, self.configs[configIndex]))
        self.windows[-1].show()
        self.needUpdate = True
        
    def showWindow(self, window):
        logging.info(f"|MainWindow|\tОтображение окна: {window}")
        self.windows.append(window(self.PROJECT, self.APP))
        self.windows[-1].show()
        self.needUpdate = True
        
    def load_scripts(self):
        modules = []

        if not(os.path.exists("scripts")):
            os.mkdir("scripts")
            
        for path in os.listdir("scripts"):
            if path.startswith("_"):
                continue
            try:
                path = pathlib.Path(os.path.join("scripts", path))
                spec = importlib.util.spec_from_file_location(path.stem, path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                cfg = module.config()
                for key in ["name", "shape", "multiply", "inputParams"]:
                    if key not in cfg.keys():
                        raise Exception(f"{key} не найден в config {path}")
            except:
                pass
            else:
                modules.append(module)

        return modules
        
    def OnFocusChanged(self, burned = False):
        if self.isActiveWindow() and (self.needUpdate or burned):
            for index in range(len(self.windows)):
                if self.windows[index].isClosed:
                    del self.windows[index]
            
            if self.selectedItem is not None:
                keys = self.selectedItem.split("\\")
                if len(keys) == 1:
                    self.typeLabel.setText(f"Данные : {keys[0]}")
                    self.formatLabel.setText(f"Формат матрицы : ")
                    self.descPlainText.setPlainText(DESC[keys[0]] if keys[0] in DESC.keys() else "")
                elif len(keys) == 2:
                    self.typeLabel.setText(f"Формат матрицы : {keys[0]} - {keys[1]}")
                    self.formatLabel.setText(f"Матрица: {self.PROJECT.DATAS[keys[0]][keys[1]].shape}")
                    self.descPlainText.setPlainText((DESC[keys[0]] if keys[0] in DESC.keys() else "") + "\n" + (DESC[keys[1]] if keys[1] in DESC.keys() else ""))
                
            self.listWidget.clear()
            self.listwindgets.clear()
            self.listwindgets["roots"] = []
            
            ID = 0
            for key in self.PROJECT.DATAS.keys():
                root = QTreeWidgetItem(self.listWidget, [key])
                self.listwindgets["roots"].append(root)
                self.listwindgets[f"{ID}"] = []
                for sub_key in self.PROJECT.DATAS[key].keys():
                    self.listwindgets[f"{ID}"].append(QTreeWidgetItem(root, [f"{key}\\{sub_key}"]))
                ID = ID + 1
            self.selectedItem = None
            self.listWidget.reset()
            self.listWidget.expandAll()
            
        elif not(self.isActiveWindow()):
            self.needUpdate = True
        
    def listWidgetCurrentItemSave(self, item):
        self.selectedItem = item.text(0).split("\t")[0]
        self.OnFocusChanged(burned=True)
        
    def NewProject(self):
        logging.info("|MainWindow|\tСоздание нового проекта")
        if self.PROJECT.edited:
            result = QMessageBox.question(self, "Предупреждение", "Ваш проект не был сохранён, желаете ли вы его сохранить?", QMessageBox.StandardButton.Yes, defaultButton=QMessageBox.StandardButton.Cancel)
            logging.info(f"|MainWindow|\tВопрос об сохранении: {result}")
            if result == QMessageBox.StandardButton.Yes:
                self.SaveProject()
            elif result == QMessageBox.StandardButton.Cancel:
                return
        self.PROJECT.NewProject()
        
    def LoadProject(self, filename : None|str = None):
        logging.info(f"|MainWindow|\tЗагрузка {filename=}")
        if self.PROJECT.edited:
            result = QMessageBox.question(self, "Предупреждение", "Ваш проект не был сохранён, желаете ли вы его сохранить?", QMessageBox.StandardButton.Yes, defaultButton=QMessageBox.StandardButton.Cancel)
            logging.info(f"|MainWindow|\tВопрос об сохранении: {result}")
            
            if result == QMessageBox.StandardButton.Yes:
                self.SaveProject()
            elif result == QMessageBox.StandardButton.Cancel:
                return

        if not(filename):
            filename, _ = QFileDialog.getOpenFileName(self, "Загрузка проекта", ".", "Архив проекта (*.tar.zst)")
            logging.info(f"|MainWindow|\tВыбор файла: {filename=}")
            
        if filename:
            self.PROJECT.LoadProject(filename)
            winsound.MessageBeep(winsound.MB_ICONINFORMATION)
    
    def SaveProject(self, RewriteFilename : bool = False):
        logging.info(f"|MainWindow|\tСохранение {RewriteFilename=}")
        if self.PROJECT.filename is not None and RewriteFilename == False:
            self.PROJECT.SaveProject()
        else:
            filename, _ = QFileDialog.getSaveFileName(self, "Сохранение проекта", ".", "Архив проекта (*.tar.zst)")
            logging.info(f"|MainWindow|\tВыбор файла: {filename=}")
            
            if filename:
                try:
                    self.PROJECT.SaveProject(filename)
                    winsound.MessageBeep(winsound.MB_ICONINFORMATION)
                except:
                    QMessageBox.warning(self, "Ошибка!", traceback.format_exc(), QMessageBox.StandardButton.Cancel)
                    logging.exception(f"|MainWindow|\tОшибка: {traceback.format_exc()}")
                    winsound.MessageBeep(winsound.MB_ICONERROR)
        self.OnFocusChanged(burned=True)
    
    def AddData(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Загрузка данных с шара", ".", "Данные с шара (*.sgm)")
        logging.info(f"|MainWindow|\tЗагрузка SGM {filename=}")
        if filename:
            try:
                self.PROJECT.loadFromSphere(filename)
                winsound.MessageBeep(winsound.MB_ICONINFORMATION)
            except:
                logging.error(f"|MainWindow|\tОшибка: {traceback.format_exc()}")
                QMessageBox.warning(self, "Ошибка!", traceback.format_exc(), QMessageBox.StandardButton.Cancel)
                winsound.MessageBeep(winsound.MB_ICONERROR)
            else:
                self.OnFocusChanged(burned=True)
    
    def SaveMat(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Сохранение проекта", ".", "MATLAB файл данных (*.mat)")
        logging.info(f"|MainWindow|\tЗагрузка MAT {filename=}")
        if filename:
            try:
                self.PROJECT.SaveMat(filename)
                winsound.MessageBeep(winsound.MB_ICONINFORMATION)
            except:
                logging.error(f"|MainWindow|\tОшибка: {traceback.format_exc()}")
                QMessageBox.warning(self, "Ошибка!", traceback.format_exc(), QMessageBox.StandardButton.Cancel)
                winsound.MessageBeep(winsound.MB_ICONERROR)
    
    def SaveCsv(self):
        path = QFileDialog.getExistingDirectory(self, "Сохранение проекта", os.getenv("HOME"), QFileDialog.ShowDirsOnly)
        logging.info(f"|MainWindow|\tЗагрузка CSV {path=}")
        if path:
            try:
                self.PROJECT.SaveCsv(path)
                winsound.MessageBeep(winsound.MB_ICONINFORMATION)
            except:
                logging.error(f"|MainWindow|\tОшибка: {traceback.format_exc()}")
                QMessageBox.warning(self, "Ошибка!", traceback.format_exc(), QMessageBox.StandardButton.Cancel)
                winsound.MessageBeep(winsound.MB_ICONERROR)
                
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = []

        for url in event.mimeData().urls():
            if url.isLocalFile():
                files.append(url.toLocalFile())
        
        logging.info(f"|MainWindow|\tDRAG-AND-DROP {files=}")
        
        if files:
            for path in files:
                path : str
                if path.endswith(".tar.zst"):
                    logging.info(f"|MainWindow|\ttarzst {path=}")
                    self.LoadProject(path)
                elif path.endswith(".sgm"):
                    logging.info(f"|MainWindow|\tsgm {path=}")
                    try:
                        self.PROJECT.loadFromSphere(path)
                    except:
                        logging.error(f"|MainWindow|\tОшибка: {traceback.format_exc()}")
                        QMessageBox.warning(self, "Ошибка!", traceback.format_exc(), QMessageBox.StandardButton.Cancel)
                        winsound.MessageBeep(winsound.MB_ICONERROR)
                    else:
                        self.OnFocusChanged(burned=True)
            winsound.MessageBeep(winsound.MB_ICONINFORMATION)

        event.acceptProposedAction()