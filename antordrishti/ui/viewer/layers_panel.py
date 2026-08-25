"""
Antordrishti — Layers Panel
Layer visibility checkboxes with optional opacity.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QCheckBox, QHBoxLayout, QLabel, QSlider
)
from PyQt5.QtCore import Qt, pyqtSignal

from app.theme import Colors, Spacing
from app.constants import ANALYSIS_LAYERS
from ui.widgets.common import CollapsibleSection


class LayerItem(QWidget):
    """Single layer with visibility checkbox and opacity slider."""

    visibility_changed = pyqtSignal(str, bool)

    def __init__(self, name: str, parent=None):
        super().__init__(parent)
        self._name = name
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 1, 0, 1)
        layout.setSpacing(6)

        self._check = QCheckBox()
        self._check.setChecked(name in ("Original Image", "Annotations"))
        self._check.stateChanged.connect(self._on_toggle)
        layout.addWidget(self._check)

        label = QLabel(name)
        label.setStyleSheet(f"font-size: 11px; color: {Colors.TEXT_PRIMARY};")
        layout.addWidget(label, 1)

    def _on_toggle(self, state):
        self.visibility_changed.emit(self._name, state == Qt.CheckState.Checked)


class LayersPanel(QWidget):
    """Analysis layers panel."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._section = CollapsibleSection("LAYERS")

        self._layers = {}
        for name in ANALYSIS_LAYERS:
            item = LayerItem(name)
            self._layers[name] = item
            self._section.add_widget(item)

        layout.addWidget(self._section)
