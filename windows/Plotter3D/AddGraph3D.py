from PySide6.QtWidgets import (
    QGridLayout,
    QDialog,
    QPushButton,
    QListWidget
)

class AddGraphDialog(QDialog):
    def __init__(self, parent, xSize : int|None, exceptList : list|None, xSizeInv : bool = False):
        super().__init__(parent)

        self.setWindowTitle("Выбор на добавление")
        self.layout = QGridLayout(self)
        self.setLayout(self.layout)

        self.selectsheets = QListWidget(self)
        self.selectsheets.setSelectionMode(QListWidget.MultiSelection)
        
        ID = 0
        self.listwindgets = {}
        for key in parent.PROJECT.DATAS.keys():
            self.listwindgets[f"{ID}"] = []
            for sub_key in parent.PROJECT.DATAS[key].keys():
                if len(parent.PROJECT.DATAS[key][sub_key].shape) > 1:
                    if parent.PROJECT.DATAS[key][sub_key].shape[0] == 3:
                        if f"{key}\\{sub_key}" not in exceptList:
                            if xSize is None:
                                self.selectsheets.addItem(f"{key}\\{sub_key}")
                                self.listwindgets[f"{ID}"].append(f"{key}\\{sub_key}")
                            elif (parent.PROJECT.DATAS[key][sub_key][1].shape == xSize and xSizeInv == False) or (not(parent.PROJECT.DATAS[key][sub_key][1].shape == xSize) and xSizeInv == True):
                                self.selectsheets.addItem(f"{key}\\{sub_key}")
                                self.listwindgets[f"{ID}"].append(f"{key}\\{sub_key}")
            ID = ID + 1
            
        self.layout.addWidget(self.selectsheets, 0, 0, 3, 3)

        addButton = QPushButton("Добавить")
        cancelButton = QPushButton("Отмена")

        addButton.clicked.connect(self.accept)
        cancelButton.clicked.connect(self.reject)
        
        self.layout.addWidget(addButton, 3, 0, 1, 1)
        self.layout.addWidget(cancelButton, 3, 2, 1, 1)

    def resultValue(self):
        return [sheet.text() for sheet in self.selectsheets.selectedItems()]