"""
Antordrishti — Typography Profiler Inspector Section
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
)

from app.theme import Colors, Spacing
from ui.widgets.common import (
    CollapsibleSection, InfoRow, ActionButton, SectionLabel
)


class _TypefaceItem(QWidget):
    """Single typeface display with consistency status."""

    def __init__(self, name: str, status: str = "Consistent", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(8)

        name_label = QLabel(name)
        name_label.setStyleSheet(f"font-size: 11px; color: {Colors.TEXT_PRIMARY};")

        status_label = QLabel(status)
        is_anomaly = "anomaly" in status.lower()
        color = Colors.ERROR if is_anomaly else Colors.SUCCESS
        status_label.setStyleSheet(f"font-size: 10px; color: {color}; font-weight: 500;")

        layout.addWidget(name_label)
        layout.addStretch()
        layout.addWidget(status_label)


class TypographyProfiler(QWidget):
    """Typography profiler inspector panel."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._section = CollapsibleSection("TYPOGRAPHY PROFILER")

        # Detected Typefaces
        self._section.add_widget(SectionLabel("Detected Typefaces"))
        self._section.add_widget(_TypefaceItem("Arial", "Consistent"))
        self._section.add_widget(_TypefaceItem("Times New Roman", "Consistent"))
        self._section.add_widget(_TypefaceItem("Courier New", "Anomaly Detected"))

        # Properties
        self._section.add_widget(SectionLabel("Properties"))
        props = [
            ("Font Family", "—"), ("Font Size", "—"), ("Font Weight", "—"),
            ("Character Spacing", "—"), ("Word Spacing", "—"),
            ("Line Spacing", "—"), ("Baseline", "—"), ("Alignment", "—"),
        ]
        self._prop_rows = {}
        for key, val in props:
            row = InfoRow(key, val)
            self._prop_rows[key] = row
            self._section.add_widget(row)

        # Actions
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(Spacing.SM)
        btn_layout.addWidget(ActionButton("Compare Text Regions"))
        btn_layout.addWidget(ActionButton("Highlight Differences"))
        self._section.add_layout(btn_layout)

        add_btn = ActionButton("Add Finding")
        self._section.add_widget(add_btn)

        layout.addWidget(self._section)


# Alias
TypographyProfilerPanel = TypographyProfiler
