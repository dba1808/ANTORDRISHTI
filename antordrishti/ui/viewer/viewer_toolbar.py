"""
Antordrishti — Viewer Toolbar
Vertical tool strip near the document viewer.
"""

from PyQt5.QtWidgets import QToolBar, QAction, QWidget, QSizePolicy
from PyQt5.QtCore import Qt, pyqtSignal, QSize

from app.resources import get_icon, Icons
from app.theme import Sizes


class ViewerToolbar(QToolBar):
    """Vertical tool strip for document viewer actions."""

    tool_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__("Viewer Tools", parent)
        self.setOrientation(Qt.Orientation.Vertical)
        self.setMovable(False)
        self.setIconSize(QSize(18, 18))
        self.setFixedWidth(32)
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)

        tools = [
            ("Select", Icons.SELECT, "Select tool"),
            ("Pan", Icons.PAN, "Pan / Hand tool"),
            ("Zoom", Icons.ZOOM_IN, "Zoom tool"),
            None,
            ("ROI", Icons.ROI, "Region of Interest"),
            ("Measure", Icons.MEASURE, "Measurement tool"),
            ("Annotate", Icons.ANNOTATE, "Annotation tool"),
            None,
            ("Compare", Icons.COMPARE, "Compare tool"),
            ("Layers", Icons.LAYERS, "Show / Hide Analysis Layers"),
        ]

        for item in tools:
            if item is None:
                self.addSeparator()
            else:
                name, icon, tooltip = item
                action = QAction(get_icon(icon), name, self)
                action.setToolTip(tooltip)
                action.setCheckable(True)
                action.triggered.connect(
                    lambda checked, n=name: self.tool_selected.emit(n)
                )
                self.addAction(action)
