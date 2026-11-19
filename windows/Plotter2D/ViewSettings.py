from PySide6.QtWidgets import (
    QGridLayout,
    QDialog,
    QCheckBox,
    QHBoxLayout,
    QSlider,
    QLabel
)
from PySide6.QtCore import Signal, Qt


class GraphSettingsDialog(QDialog):
    parameterChanged = Signal(str, object)
    
    def __init__(self, parent, settings):
        super().__init__(parent)
        
        self.setWindowTitle("Настройки графика")
        self.layout = QGridLayout(self)
        self.setLayout(self.layout)
        
        self.temp_map = QCheckBox("Тепловая карта")
        self.temp_map.setChecked(settings["temp_map"])
        self.temp_map_soft = QCheckBox("Сглаживание карты")
        self.temp_map_soft.setChecked(settings["temp_map_soft"])
        self.aspect = QCheckBox("Сохранять пропорции")
        self.aspect.setChecked(settings["aspect"])
        
        self.aspect_width_layout = QHBoxLayout()
        self.aspect_width_label = QLabel("Размер X")
        self.aspect_width = QSlider(Qt.Orientation.Horizontal)
        self.aspect_width.setRange(1, 100_000)
        self.aspect_width.setValue(int(settings["X aspect"]))
        self.aspect_width_layout.addWidget(self.aspect_width_label)
        self.aspect_width_layout.addWidget(self.aspect_width)
        
        self.aspect_height_layout = QHBoxLayout()
        self.aspect_height_label = QLabel("Размер Y")
        self.aspect_height = QSlider(Qt.Orientation.Horizontal)
        self.aspect_height.setRange(1, 100_000)
        self.aspect_height.setValue(int(settings["Y aspect"] * 100))
        self.aspect_height_layout.addWidget(self.aspect_height_label)
        self.aspect_height_layout.addWidget(self.aspect_height)
        
        self.aspect.toggled.connect(lambda value: self.parameterChanged.emit("aspect", value))
        self.temp_map.toggled.connect(lambda value: self.parameterChanged.emit("temp_map", value))
        self.temp_map_soft.toggled.connect(lambda value: self.parameterChanged.emit("temp_map_soft", value))
        self.aspect_width.valueChanged.connect(lambda value: self.parameterChanged.emit("X aspect", value))
        self.aspect_height.valueChanged.connect(lambda value: self.parameterChanged.emit("Y aspect", value/100))

        self.layout.addWidget(self.temp_map, 0, 0, 1, 5)
        self.layout.addWidget(self.temp_map_soft, 1, 0, 1, 5)
        
        self.layout.addWidget(self.aspect, 3, 0, 1, 5)
        self.layout.addLayout(self.aspect_width_layout, 4, 0, 1, 5)
        self.layout.addLayout(self.aspect_height_layout, 5, 0, 1, 5)