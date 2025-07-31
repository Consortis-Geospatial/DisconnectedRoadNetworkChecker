from . import resources_rc
from qgis.PyQt.QtCore import Qt, QTimer
from qgis.PyQt.QtWidgets import (
    QAction, QDockWidget, QVBoxLayout, QLabel,
    QListWidget, QWidget, QComboBox, QPushButton, QDoubleSpinBox
)
from qgis.PyQt.QtGui import QColor
from qgis.core import (
    QgsProject, QgsGeometry, QgsSpatialIndex,
    QgsVectorLayer, QgsWkbTypes, QgsFeatureRequest
)
from qgis.gui import QgisInterface, QgsRubberBand, QgsMapCanvas


class DisconnectedRoadChecker(QDockWidget):
    def __init__(self, plugin):
        super().__init__("Έλεγχος μη συνδεδεμένων τμημάτων οδικού δικτύου")
        self.plugin = plugin
        self.setFloating(False)
        self.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetClosable)

        self.widget = QWidget()
        self.layout = QVBoxLayout(self.widget)

        self.layout.addWidget(QLabel("Επέλεξε επίπεδο πρός έλεγχο:"))
        self.layer_combo = QComboBox()
        self.layout.addWidget(self.layer_combo)

        self.layout.addWidget(QLabel("Ελάχιστο αποδεκτό μήκος γραμμής (m):"))
        self.length_spinbox = QDoubleSpinBox()
        self.length_spinbox.setRange(0, 1000)
        self.length_spinbox.setValue(5.0)
        self.length_spinbox.setSuffix(" m")
        self.layout.addWidget(self.length_spinbox)

        self.run_button = QPushButton("Έλεγχος")
        self.layout.addWidget(self.run_button)

        self.layout.addWidget(QLabel("Μη συνδεμένα τμήματα:"))
        self.geometry_list = QListWidget()
        self.layout.addWidget(self.geometry_list)

        self.select_button = QPushButton("Επιλογή όλων")
        self.layout.addWidget(self.select_button)

        self.setWidget(self.widget)

        self.run_button.clicked.connect(self.plugin.run_check)
        self.geometry_list.itemClicked.connect(self.plugin.zoom_to_feature)
        self.select_button.clicked.connect(self.plugin.select_flagged_features)

    def populate_layer_list(self):
        self.layer_combo.clear()
        for layer in QgsProject.instance().mapLayers().values():
            if isinstance(layer, QgsVectorLayer) and layer.geometryType() == QgsWkbTypes.LineGeometry:
                self.layer_combo.addItem(layer.name(), layer)

    def selected_layer(self):
        return self.layer_combo.currentData()

    def max_length(self):
        return self.length_spinbox.value()

    def add_geometry(self, fid):
        self.geometry_list.addItem(str(fid))

    def clear_results(self):
        self.geometry_list.clear()


class DisconnectedRoadCheckerPlugin:
    def __init__(self, iface: QgisInterface):
        self.iface = iface
        self.canvas: QgsMapCanvas = iface.mapCanvas()
        self.panel = DisconnectedRoadChecker(self)
        self.flagged_ids = []

        self.rubber_band = QgsRubberBand(self.canvas, QgsWkbTypes.LineGeometry)
        self.rubber_band.setColor(QColor(255, 0, 0, 180))
        self.rubber_band.setWidth(3)

    def initGui(self):
        # Load the icon from resources
        from qgis.PyQt.QtGui import QIcon
        icon = QIcon(":/icon.png")  # Path as defined in resources.qrc
        self.action = QAction(icon, "Έλεγχος μη συνδεδεμένων τμημάτων οδικού δικτύου", self.iface.mainWindow())
        self.action.triggered.connect(self.show_panel)
        self.iface.addToolBarIcon(self.action)

    def unload(self):
        self.iface.removeToolBarIcon(self.action)
        self.iface.removeDockWidget(self.panel)

    def show_panel(self):
        self.panel.populate_layer_list()
        self.iface.addDockWidget(Qt.RightDockWidgetArea, self.panel)
        self.panel.show()

    def run_check(self):
        self.panel.clear_results()
        self.flagged_ids = []
        layer = self.panel.selected_layer()
        if not layer:
            return

        max_length = self.panel.max_length()
        spatial_index = QgsSpatialIndex(layer.getFeatures())

        for feature in layer.getFeatures():
            geom = feature.geometry()
            if geom.isMultipart():
                lines = geom.asMultiPolyline()
            else:
                lines = [geom.asPolyline()]

            dangling_nodes = 0
            for line in lines:
                if not line:
                    continue
                start_point = line[0]
                end_point = line[-1]

                if not self.is_connected(start_point, feature.id(), spatial_index, layer):
                    dangling_nodes += 1
                if not self.is_connected(end_point, feature.id(), spatial_index, layer):
                    dangling_nodes += 1

            if dangling_nodes > 1 and geom.length() <= max_length:
                fid = feature.id()
                self.panel.add_geometry(fid)
                self.flagged_ids.append(fid)

    def is_connected(self, point, feature_id, spatial_index, layer):
        point_geom = QgsGeometry.fromPointXY(point)
        buffer = point_geom.buffer(0.5, 5)
        nearby_ids = spatial_index.intersects(buffer.boundingBox())

        for fid in nearby_ids:
            if fid == feature_id:
                continue
            other_feat = layer.getFeature(fid)
            if other_feat.geometry().intersects(buffer):
                return True
        return False

    def zoom_to_feature(self, item):
        fid = int(item.text())
        layer = self.panel.selected_layer()
        if not layer:
            return

        feature = layer.getFeature(fid)
        geom = feature.geometry()
        if not geom:
            return

        self.canvas.setExtent(geom.boundingBox())
        self.canvas.zoomScale(50)

        self.rubber_band.reset(QgsWkbTypes.LineGeometry)
        self.rubber_band.addGeometry(geom, layer)
        self.rubber_band.show()

        QTimer.singleShot(700, self.rubber_band.hide)
        QTimer.singleShot(1000, self.rubber_band.show)
        QTimer.singleShot(1500, self.rubber_band.hide)

    def select_flagged_features(self):
        layer = self.panel.selected_layer()
        if not layer or not self.flagged_ids:
            return
        layer.removeSelection()
        layer.selectByIds(self.flagged_ids)
