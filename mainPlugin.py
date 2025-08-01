from . import resources_rc
from qgis.PyQt.QtCore import Qt, QTimer
from qgis.PyQt.QtWidgets import (
    QAction, QDockWidget, QVBoxLayout, QLabel,
    QListWidget, QWidget, QComboBox, QPushButton, QDoubleSpinBox, QProgressBar
)
from qgis.PyQt.QtGui import QColor
from qgis.core import (
    QgsProject, QgsGeometry, QgsSpatialIndex,
    QgsVectorLayer, QgsWkbTypes, QgsFeatureRequest
)
from qgis.gui import QgisInterface, QgsRubberBand, QgsMapCanvas


class DisconnectedRoadChecker(QDockWidget):
    def __init__(self, plugin):
        super().__init__("Disconnected Road Checker")
        self.plugin = plugin
        self.setFloating(False)
        # Configure dock widget features
        self.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetClosable)

        self.widget = QWidget()
        self.layout = QVBoxLayout(self.widget)

        self.layout.addWidget(QLabel("Select layer to check:"))
        self.layer_combo = QComboBox()
        self.layout.addWidget(self.layer_combo)

        self.layout.addWidget(QLabel("Maximum allowed segment length (m):"))
        self.length_spinbox = QDoubleSpinBox()
        self.length_spinbox.setRange(0, 1000)
        self.length_spinbox.setValue(5.0)
        self.length_spinbox.setSuffix(" m")
        self.layout.addWidget(self.length_spinbox)

        self.run_button = QPushButton("Run Check")
        self.layout.addWidget(self.run_button)

        # Add progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.layout.addWidget(self.progress_bar)

        self.status_label = QLabel("")  # Status message label
        self.layout.addWidget(self.status_label)

        self.layout.addWidget(QLabel("Disconnected road segments found:"))
        self.geometry_list = QListWidget()
        self.layout.addWidget(self.geometry_list)

        self.select_button = QPushButton("Select All")
        self.layout.addWidget(self.select_button)

        self.setWidget(self.widget)

        # Connect signals
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

    # Methods to update progress bar and status message
    def set_progress(self, value):
        self.progress_bar.setValue(value)

    def set_status_message(self, message):
        self.status_label.setText(message)


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
        self.action = QAction(icon, "Disconnected Road Checker", self.iface.mainWindow())
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
        self.panel.set_status_message("")  # Clear previous status message
        self.panel.set_progress(0)

        layer = self.panel.selected_layer()
        if not layer:
            self.panel.set_status_message("Please select a valid layer.")
            return

        max_length = self.panel.max_length()
        features = list(layer.getFeatures())  # Save features for iteration and length
        total = len(features)
        if total == 0:
            self.panel.set_status_message("Layer has no features.")
            self.panel.set_progress(100)
            return

        spatial_index = QgsSpatialIndex(layer.getFeatures())  # Pass iterator, not list

        for i, feature in enumerate(features):
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

            progress = int(((i + 1) / total) * 100)
            self.panel.set_progress(progress)

        if not self.flagged_ids:
            self.panel.set_status_message("No disconnected road segments found.")
        else:
            self.panel.set_status_message(f"Found {len(self.flagged_ids)} disconnected road segments.")

        self.panel.set_progress(100)

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
