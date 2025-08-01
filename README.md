# DisconnectedRoadChecker
**DisconnectedRoadChecker** is a QGIS plugin that identifies disconnected islands in road networks, flagging line segments shorter than a user-defined length threshold with unconnected endpoints, helping detect gaps or errors in road network data.

---

## Features

- Analyze any line layer in your QGIS project.
- User-defined maximum length threshold for flagging short disconnected islands.
- Identify road segments with unconnected endpoints using spatial indexing.
- Visual feedback of flagged disconnected islands via red rubber bands on the map canvas.
- List and zoom to flagged disconnected islands in a dockable panel.
- Select all flagged disconnected islands for further inspection or editing.

---

## How It Works

1. Activate the plugin via the toolbar icon.
2. Select a line layer from the dropdown menu in the dockable panel.
3. Specify the maximum allowed segment length (in meters) for disconnected islands.
4. Click the "Run Check" button to analyze the layer.
5. View flagged disconnected islands in the results list.
6. Click a segment in the list to zoom to its location, with temporary rubber band highlighting.
7. Use the "Select All" button to highlight all flagged disconnected islands in the layer.

---

## Installation

1. Clone or download this repository:
   ```bash
   git clone https://github.com/Consortis-Geospatial/DisconnectedRoadNetworkChecker.git
   ```
2. Copy the folder to your QGIS plugin directory:
   - Linux: `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`
   - Windows: `%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\`
3. Open QGIS and enable the plugin via Plugins > Manage and Install Plugins.

---

## Screenshot
Coming Soon...

---

## Developer Notes

- Written in Python using PyQt and PyQGIS APIs.
- Uses a custom `QDockWidget` to display flagged disconnected island IDs and interact with the map.
- Spatial indexing (`QgsSpatialIndex`) ensures efficient detection of unconnected endpoints.
- Temporary rubber band visualization for flagged disconnected islands with a blinking effect.
- Designed for road network validation, particularly in datasets using EPSG:2100 or similar projections.

---

## Support and Contributions

- **Homepage**: [https://github.com/Consortis-Geospatial](https://github.com/Consortis-Geospatial)
- **Issue Tracker**: [https://github.com/Consortis-Geospatial/DisconnectedRoadChecker/issues](https://github.com/Consortis-Geospatial/DisconnectedRoadChecker/issues)
- **Author**: Gkaravelis Andreas - Consortis Geospatial
- **Email**: gkaravelis@consortis.gr
- **Repository**: [https://github.com/Consortis-Geospatial/DisconnectedRoadChecker](https://github.com/Consortis-Geospatial/DisconnectedRoadChecker)

---

## License
This plugin is released under the GPL-3.0 license.
