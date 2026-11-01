if __name__ == '__main__':
    raise SystemError("ЗАПУЩЕН НЕ ИНИЦИАЛИЗИРУЮЩИЙ ФАЙЛ")

from PySide6.QtWidgets import (QWidget, QGridLayout, QListWidget, QListWidgetItem)


class ExampleWindow(QWidget):
    def __init__(self, prj, app):
        self.PROJECT = prj
        self.APP = app
        self.isClosed = False
        
        super().__init__()
        self.setWindowTitle("ПРИМЕР")
        self.layout = QGridLayout(self)
        self.setLayout(self.layout)
        
        
        
        self.needUpdate = False
        app.focusChanged.connect(self.onFocusChanged)

    def onFocusChanged(self, burned = False):
        global PROJECT
        
        if self.isActiveWindow() and (self.needUpdate or burned):
            pass
        elif not(self.isActiveWindow()):
            self.needUpdate = True