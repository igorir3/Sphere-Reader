if __name__ == '__main__':
    raise SystemError("ЗАПУЩЕН НЕ ИНИЦИАЛИЗИРУЮЩИЙ ФАЙЛ")

from PySide6.QtWidgets import QWidget, QMenuBar, QGridLayout, QDialog
from PySide6 import QtGui

import numpy as np
import fastplotlib as fpl

import sys
sys.path.append('windows\\Plotter2D')
from AddGraph import AddGraphDialog
from RemoveGraph import RemoveGraphDialog
from classes import Project

LINE_COLORS = [
    "cyan", "orange", "lime", "magenta", "yellow",
    "red", "blue", "white", "purple", "green"
]

def make_vertical_segments(x_values, y0, y1):
    segments = []

    for xv in x_values:
        segments.append(np.array([
            [xv, y0],
            [xv, y1]
        ], dtype=np.float32))

    return segments

class Plotter2DWindow(QWidget):
    def __init__(self, prj : Project, app):
        self.PROJECT = prj
        self.APP = app
        self.isClosed = False
        
        super().__init__()
        self.setWindowTitle("2D график")
        self.resize(1000, 600)
        
        self.layout = QGridLayout(self)
        self.setLayout(self.layout)

        self.x = None
        self.yMin = 0
        self.yMax = 0

        self.figure = fpl.Figure(show_tooltips=True)

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
            y = 0
            for index, resultValue in enumerate(dialog.resultValue()):
                self.lines[resultValue] = self.PROJECT.getByKey(resultValue)
                self.figure[0, 0].add_line(y + self.lines[resultValue], colors=LINE_COLORS[index % len(LINE_COLORS)])
                self.figure[0, 0].add_text(resultValue, offset=(-25, y, 0), font_size=10, face_color=LINE_COLORS[index % len(LINE_COLORS)])
                
                self.yMin = min(self.yMin, np.min(y + self.lines[resultValue]))
                self.yMax = max(self.yMax, np.max(y + self.lines[resultValue]))
                
                y = y + (np.max(np.abs(self.lines[resultValue]))*-1) * 1.2 

                if self.x is None: self.x = self.lines[resultValue].shape

    def repaintGraph(self):
        self.figure[0, 0].clear()
        self.x = None
                
        y = 0
        for index, line in enumerate(self.lines.keys()):
            self.figure[0, 0].add_line(y + self.lines[line], colors=LINE_COLORS[index % len(LINE_COLORS)])
            self.figure[0, 0].add_text(line, offset=(-25, y, 0), font_size=10, face_color=LINE_COLORS[index % len(LINE_COLORS)])
            
            self.yMin = min(self.yMin, np.min(y + self.lines[line]))
            self.yMax = max(self.yMax, np.max(y + self.lines[line]))
            
            y = y + (np.max(np.abs(self.lines[line]))*-1) * 1.2 
            
            if self.x is None:
                self.x = self.lines[line].shape
                            
        for index, points in enumerate(self.points.keys()):
            self.points[points] = self.PROJECT.getByKey(points)
            
            detected_segments = make_vertical_segments(self.points[points], self.yMax, self.yMin)

            line = self.figure[0, 0].add_line_collection(
                data=detected_segments,
                thickness=2,
                colors=LINE_COLORS[index % len(LINE_COLORS)],
                name=f"{points}\nx={{x:.3f}}\ny={{y:.3f}}")
            line.tooltip_format = f"{points}\nx={{x:.3f}}\ny={{y:.3f}}"

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

                detected_segments = make_vertical_segments(self.points[resultValue], self.yMax + (abs(self.yMax)/5), self.yMin - (abs(self.yMin)/5))
    
                line = self.figure[0, 0].add_line_collection(
                    data=detected_segments,
                    thickness=2,
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