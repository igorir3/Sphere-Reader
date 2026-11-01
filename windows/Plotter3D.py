if __name__ == '__main__':
    raise SystemError("ЗАПУЩЕН НЕ ИНИЦИАЛИЗИРУЮЩИЙ ФАЙЛ")

from PySide6.QtWidgets import QWidget, QMenuBar, QGridLayout, QDialog
from PySide6 import QtGui

import numpy as np
import fastplotlib as fpl

import sys
sys.path.append('windows\\Plotter3D')
from AddGraph3D import AddGraphDialog
from RemoveGraph3D import RemoveGraphDialog
from classes import Project

LINE_COLORS = [
    "cyan", "orange", "lime", "magenta", "yellow",
    "red", "blue", "white", "purple", "green"
]

def make_vertical_segments(values):
    segments = []

    for v in values:
        v = v-0.5
        segments.append(np.array([
            [v[0], v[1], v[2]],
            [v[0]+1, v[1]+1, v[2]+1]
        ], dtype=np.float32))

    return segments

class Plotter3DWindow(QWidget):
    def __init__(self, prj : Project, app):
        self.PROJECT = prj
        self.APP = app
        self.isClosed = False
        
        super().__init__()
        self.setWindowTitle("3D график")
        self.resize(1000, 600)
        
        self.layout = QGridLayout(self)
        self.setLayout(self.layout)

        self.x = None
        self.zMin = 0
        self.zMax = 0

        self.figure = fpl.Figure(cameras="3d")
        self.figure[0, 0].add_line(np.column_stack((np.arange(0, 1000, 1), np.zeros((1000)), np.arange(0, 1000, 1))).astype(np.float32), colors="white")

        self.lines = {}
        self.points = {}

        self.plot_widget = self.figure.show()
        self.layout.addWidget(self.plot_widget, 1, 0, 50, 50)
        
        menuBar = QMenuBar(self)
        graphBar = menuBar.addMenu("График")
        
        addGraphAction = graphBar.addAction("Добавление графиков")
        removeGraphAction = graphBar.addAction("Удаление графиков")
        graphBar.addSeparator()
        addPointsAction = graphBar.addAction("Добавление точек")
        removePointsAction = graphBar.addAction("Удаление точек")
        
        addGraphAction.triggered.connect(self.addGraph)
        removeGraphAction.triggered.connect(self.removeGraph)
        addPointsAction.triggered.connect(self.addPoints)
        removePointsAction.triggered.connect(self.removePoints)

        self.layout.addWidget(menuBar, 0, 0, 1, 50)

    def addGraph(self):
        dialog = AddGraphDialog(self, self.x, list(self.lines.keys()))
        result = dialog.exec()
        
        if result == QDialog.Accepted:
            z = 0
            for index, line in enumerate(dialog.resultValue()):
                self.lines[line] = self.PROJECT.getByKey(line)
                temp = self.lines[line]
                temp[2] = self.lines[line][2, :] + z
                self.figure[0, 0].add_line(np.transpose(temp), colors=LINE_COLORS[index % len(LINE_COLORS)])
                self.figure[0, 0].add_text(line, offset=(0, 0, z), font_size=10, face_color=LINE_COLORS[index % len(LINE_COLORS)])
                
                self.zMin = min(self.zMin, np.min(z + self.lines[line]))
                self.zMax = max(self.zMax, np.max(z + self.lines[line]))
                
                z = z + (np.max(np.abs(self.lines[line]))*-1) * 1.2 
                
                if self.x is None:
                    self.x = self.lines[line].shape[1]

    def repaintGraph(self):
        self.figure[0, 0].clear()
        self.x = None
                
        z = 0
        for index, line in enumerate(self.lines.keys()):
            temp = self.lines[line]
            temp[2] = self.lines[line][2, :] + z
            self.figure[0, 0].add_line(np.transpose(temp), colors=LINE_COLORS[index % len(LINE_COLORS)])
            self.figure[0, 0].add_text(line, offset=(0, 0, z), font_size=10, face_color=LINE_COLORS[index % len(LINE_COLORS)])
            
            self.zMin = min(self.zMin, np.min(z + self.lines[line]))
            self.zMax = max(self.zMax, np.max(z + self.lines[line]))
            
            z = z + (np.max(np.abs(self.lines[line]))*-1) * 1.2 
            
            if self.x is None:
                self.x = self.lines[line].shape[1]
                            
        for index, points in enumerate(self.points.keys()):
            self.points[points] = self.PROJECT.getByKey(points)
            
            detected_segments = make_vertical_segments(self.points[points], self.zMax, self.zMin)

            line = self.figure[0, 0].add_line_collection(
                data=detected_segments,
                thickness=2,
                colors=LINE_COLORS[index % len(LINE_COLORS)],
                name=f"{points}\nx={{x:.3f}}\ny={{y:.3f}}\nz={{y:.3f}}")
            line.tooltip_format = f"{points}\nx={{x:.3f}}\ny={{y:.3f}}\nz={{y:.3f}}"

    def removeGraph(self):             
        dialog = RemoveGraphDialog(self, self.lines.keys())
        result = dialog.exec()
        
        if result == QDialog.Accepted:
            for resultValue in dialog.resultValue():
                del self.lines[resultValue]

            self.repaintGraph()
            

    def addPoints(self):
        dialog = AddGraphDialog(self, self.x, list(self.points.keys()), xSizeInv=True)
        result = dialog.exec()
        
        if result == QDialog.Accepted:
            for index, resultValue in enumerate(dialog.resultValue()):
                self.points[resultValue] = self.PROJECT.getByKey(resultValue)

                detected_segments = make_vertical_segments(self.points[resultValue])
    
                line = self.figure[0, 0].add_line_collection(
                    data=detected_segments,
                    thickness=5,
                    colors=LINE_COLORS[index % len(LINE_COLORS)],
                    name=f"{resultValue}\nx={{x:.3f}}\ny={{y:.3f}}")
                line.tooltip_format = f"{resultValue}\nx={{x:.3f}}\ny={{y:.3f}}"
                    
    def removePoints(self):
        dialog = RemoveGraphDialog(self, self.points.keys())
        result = dialog.exec()
        
        if result == QDialog.Accepted:
            for resultValue in dialog.resultValue():
                del self.points[resultValue]
                
            self.repaintGraph()