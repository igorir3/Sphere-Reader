from PySide6.QtWidgets import (
    QGridLayout,
    QDialog,
    QPushButton,
    QListWidget
)

class RemoveGraphDialog(QDialog):
    def __init__(self, parent, keys):
        super().__init__(parent)

        self.setWindowTitle("Выбор на удаление")
        self.layout = QGridLayout(self)
        self.setLayout(self.layout)

        self.selectsheets = QListWidget(self)
        self.selectsheets.setSelectionMode(QListWidget.MultiSelection)
        self.selectsheets.addItems(keys)
        self.layout.addWidget(self.selectsheets, 0, 0, 3, 3)

        addButton = QPushButton("Добавить")
        cancelButton = QPushButton("Отмена")

        addButton.clicked.connect(self.accept)
        cancelButton.clicked.connect(self.reject)
        
        self.layout.addWidget(addButton, 3, 0, 1, 1)
        self.layout.addWidget(cancelButton, 3, 2, 1, 1)

    def resultValue(self):
        return [sheet.text() for sheet in self.selectsheets.selectedItems()]