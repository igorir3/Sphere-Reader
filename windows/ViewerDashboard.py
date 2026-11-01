import sys
import numpy as np
import fastplotlib as fpl

from PySide6.QtWidgets import (
    QApplication, QWidget, QGridLayout,
    QHBoxLayout, QSlider, QLabel, QComboBox,
    QPushButton
)
from PySide6.QtCore import Qt
from vispy import scene
from vispy.geometry import create_sphere
from vispy.color import get_colormap
from classes import Project 

import keyboard

LINE_COLORS = [
    "cyan", "orange", "lime", "magenta", "yellow",
    "red", "blue", "white", "purple", "green"
]

class DashboardViewer(QWidget):
    def __init__(self, points, values, sigma=0.25):
        super().__init__()

        self.points = np.asarray(points, dtype=np.float32)
        self.values = np.asarray(values, dtype=np.float32)

        if self.points.ndim != 2 or self.points.shape[1] != 3: raise ValueError(f"points должен иметь форму (M, 3), {self.values.shape}")
        if self.values.ndim != 2 or self.values.shape[1] != len(self.points): raise ValueError(f"values должен иметь форму (N, M), {self.values.shape}")
        if not len(self.points) or not len(self.values): raise ValueError("Массивы не должны быть пустыми")
        if not np.isfinite(self.points).all(): raise ValueError("Координаты должны быть конечными")
        if not np.isfinite(self.values).all(): raise ValueError("Показания должны быть конечными")
        if sigma <= 0: raise ValueError("sigma должен быть положительным")

        lengths = np.linalg.norm(self.points, axis=1)
        if np.any(lengths == 0): raise ValueError("Координаты очагов не могут быть нулевыми")

        self.points = self.points / lengths[:, None]

        self.setWindowTitle("Панель просмотра данных")
        self.resize(1000, 1000)

        self.layout = QGridLayout(self)

        self.canvas = scene.SceneCanvas(
            bgcolor="#101015",
            show=False,
            keys=None
        )
        self.layout.addWidget(self.canvas.native, 0, 10, 10, 10)

        self.view = self.canvas.central_widget.add_view()
        self.view.camera = scene.cameras.TurntableCamera(distance=4, fov=63)
        sphere = create_sphere(rows=120, cols=240, radius=1.0)

        self.vertices = sphere.get_vertices()
        self.faces = sphere.get_faces()

        directions = self.vertices / np.linalg.norm(self.vertices, axis=1, keepdims=True)
        cos_angle = np.clip(directions @ self.points.T, -1.0, 1.0)
        angles = np.arccos(cos_angle)

        self.weights = np.exp(-0.5 * (angles / sigma) ** 2).astype(np.float32)

        self.vmin = min(0.0, float(self.values.min()))
        self.vmax = max(0.0, float(self.values.max()))

        if self.vmin == self.vmax: self.vmax = self.vmin + 1.0
        self.cmap = get_colormap("inferno")

        self.mesh = scene.visuals.Mesh(
            vertices=self.vertices,
            faces=self.faces,
            color=(0.3, 0.3, 0.3, 1.0),
            shading=None,
            parent=self.view.scene
        )
        
        sensor_positions = self.points * 1.02

        self.markers = scene.visuals.Markers(parent=self.view.scene)
        self.markers.set_data(sensor_positions, face_color="white", edge_color="black", size=8)

        self.labels = scene.visuals.Text(
            text=[str(i+1) for i in range(len(self.points))],
            pos=self.points * 1.08,
            color="white",
            font_size=12,
            anchor_x="center",
            anchor_y="center",
            parent=self.view.scene
        )

        controls = QHBoxLayout()
        self.layout.addLayout(controls, 11, 0, 1, 20)
        
        self.leftButton = QPushButton(text="<")
        self.rightButton = QPushButton(text=">")

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, len(self.values) - 1)
        self.slider.valueChanged.connect(self.set_frame)
        
        self.leftButton.clicked.connect(lambda: self.slider.setValue(self.slider.value() - 1 * (10 if keyboard.is_pressed('shift') else 1) * (100 if keyboard.is_pressed('ctrl') else 1)))
        self.rightButton.clicked.connect(lambda: self.slider.setValue(self.slider.value() + 1* (10 if keyboard.is_pressed('shift') else 1) * (100 if keyboard.is_pressed('ctrl') else 1)))

        self.label = QLabel()
        self.label.setMinimumWidth(140)

        controls.addWidget(self.leftButton)
        controls.addWidget(self.rightButton)
        controls.addWidget(self.slider)
        controls.addWidget(self.label)
        
        self.figure = fpl.Figure(show_tooltips=True)
        
        y = 0
        self.yMin = 0
        self.yMax = 0
        for index, array in enumerate(np.transpose(values)):
            self.figure[0, 0].add_line(y + array, colors=LINE_COLORS[index % len(LINE_COLORS)])
            self.figure[0, 0].add_text(str(index), offset=(-25, y, 0), font_size=10, face_color=LINE_COLORS[index % len(LINE_COLORS)])
            
            self.yMin = min(self.yMin, np.min(y + array))
            self.yMax = max(self.yMax, np.max(y + array))
            
            y = y + (np.max(np.abs(array))*-1) * 1.2 
        
        self.line = self.figure[0, 0].add_line(data=np.array([[0, self.yMin], [0, self.yMax]]))
        
        self.window = 2000
        self.figure[0, 0].camera.set_state({
            "x": 0 - self.window / 2,
            "width": self.window
        })
        
        self.plot_widget = self.figure.show(maintain_aspect=False)
        self.layout.addWidget(self.plot_widget, 0, 0, 10, 10)
        
        self.set_frame(0)

    def set_frame(self, index):
        heat = self.weights @ self.values[index]

        heat = np.clip((heat - self.vmin) / (self.vmax - self.vmin), 0, 1)
        colors = self.cmap.map(heat.astype(np.float32))

        self.mesh.set_data(
            vertices=self.vertices,
            faces=self.faces,
            vertex_colors=colors.astype(np.float32)
        )

        self.label.setText(f"Запись: {index + 1} / {len(self.values)}")
        self.figure[0, 0].camera.set_state({
            "x": index - self.window / 2,
            "width": self.window
        })
        
        
        self.line.data[:, 0] = np.array([index, index])
        
        

class Dashboard(QWidget):
    def __init__(self, prj : Project, app):
            self.PROJECT = prj
            self.APP = app
            self.isClosed = False
            
            super().__init__()
            self.setWindowTitle("Ввод данных для панели")
            self.layout = QGridLayout(self)
            self.setLayout(self.layout)
            
            self.bLabel = QLabel(self, text="Данные магнитных датчиков")
            self.bDirSelector = QComboBox(self)
            self.listwindgets = []
            for key in self.PROJECT.DATAS["b"].keys():
                self.bDirSelector.addItem(f"b\\{key}")
                self.listwindgets.append(f"b\\{key}")
            self.bDirSelector.setCurrentIndex(0)
            self.proceedButton = QPushButton(self, text="Открыть")

            self.layout.addWidget(self.bLabel, 0, 0, 1, 3)
            self.layout.addWidget(self.bDirSelector, 1, 0, 1, 3)
            self.proceedButton.clicked.connect(self.proceed)
            self.layout.addWidget(self.proceedButton, 2, 1, 1, 1)
            
            self.needUpdate = False
            app.focusChanged.connect(self.onFocusChanged)
    
    def onFocusChanged(self, burned = False):
        global PROJECT
        
        if self.isActiveWindow() and (self.needUpdate or burned):
            pass
        elif not(self.isActiveWindow()):
            self.needUpdate = True
            
    def proceed(self):
        points = np.array([[0.0, 0.0, 1.0], [0.10206783792008463, -0.5788554735638644, 0.8090169943749475], [0.5523374641860205, -0.20103439623378594, 0.8090169943749475], [0.4502696262659356, 0.37782107733007825, 0.8090169943749475], [-0.10206783792008482, 0.5788554735638642, 0.8090169943749475], [-0.5523374641860204, 0.2010343962337861, 0.8090169943749475], [-0.4502696262659356, -0.37782107733007825, 0.8090169943749475], [-0.4755282581475772, -0.8236391035463317, 0.30901699437494745], [-0.8937007903129088, -0.32528048601407955, 0.30901699437494745], [-0.8937007903129087, 0.3252804860140798, 0.30901699437494745], [-0.47552825814757654, 0.823639103546332, 0.30901699437494745], [0.16514923091291273, 0.9366078308002486, 0.30901699437494745], [0.7285515593999962, 0.6113273447861689, 0.30901699437494745], [0.9510565162951535, 0.0, 0.30901699437494745], [0.7285515593999959, -0.6113273447861692, 0.30901699437494745], [0.1651492309129123, -0.9366078308002487, 0.30901699437494745], [-0.728551559399996, 0.6113273447861692, -0.30901699437494734], [-0.16514923091291264, 0.9366078308002487, -0.30901699437494734], [1.2246467991473532e-16, 0.0, -1.0], [0.45026962626593564, 0.3778210773300783, -0.8090169943749473], [-0.45026962626593564, -0.3778210773300783, -0.8090169943749473], [-0.5523374641860205, 0.20103439623378613, -0.8090169943749473], [0.10206783792008466, -0.5788554735638645, -0.8090169943749473], [-0.16514923091291267, -0.9366078308002487, -0.30901699437494734], [0.5523374641860206, -0.20103439623378597, -0.8090169943749473], [0.8937007903129089, -0.32528048601407955, -0.30901699437494734], [0.47552825814757693, -0.823639103546332, -0.30901699437494734], [0.8937007903129089, 0.3252804860140796, -0.30901699437494734], [-0.7285515593999962, -0.611327344786169, -0.30901699437494734], [-0.9510565162951536, 1.1647083184890926e-16, -0.30901699437494734], [0.47552825814757693, 0.823639103546332, -0.30901699437494734], [-0.10206783792008485, 0.5788554735638644, -0.8090169943749473]])
        values = self.PROJECT.getByKey(self.listwindgets[self.bDirSelector.currentIndex()])
        self.window = DashboardViewer(points=points, values=np.transpose(values), sigma=0.2)
        self.window.show()
        self.deleteLater()
        

if __name__ == "__main__":
    pass