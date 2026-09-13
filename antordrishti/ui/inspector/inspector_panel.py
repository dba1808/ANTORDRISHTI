"""
Antordrishti — Inspector Panel
Right dock panel container with stacked sections on a clean white background.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QFrame, QLabel
)
from PyQt5.QtCore import Qt

from app.theme import Colors, Sizes, Spacing
from ui.inspector.file_info import FileInfoPanel
from ui.inspector.hash_panel import HashPanel
from ui.inspector.forensic_filters import ForensicFiltersPanel
from ui.inspector.typography_profiler import TypographyProfiler
from ui.inspector.findings_panel import FindingsPanel


class InspectorPanel(QWidget):
    """Right-side inspector panel with collapsible sections."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)  # type: ignore[arg-type]
        self.setMinimumWidth(260)
        self.setMaximumWidth(360)
        self.setStyleSheet("""
            InspectorPanel {
                background-color: #FFFFFF;
                border-left: 1px solid #E2E8F0;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Title Header
        title = QLabel("  INSPECTOR")
        title.setFixedHeight(34)
        title.setStyleSheet("""
            font-size: 11px;
            font-weight: 800;
            color: #475569;
            letter-spacing: 1px;
            padding-left: 12px;
            background-color: #F8FAFC;
            border-bottom: 1px solid #E2E8F0;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(title)

        # Scroll area with explicit white background
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background-color: #FFFFFF;")

        container = QWidget()
        container.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)  # type: ignore[arg-type]
        container.setStyleSheet("background-color: #FFFFFF;")
        self._container_layout = QVBoxLayout(container)
        self._container_layout.setContentsMargins(0, 0, 0, 0)
        self._container_layout.setSpacing(0)

        # Sections
        self.file_info = FileInfoPanel()
        self.hash_panel = HashPanel()
        self.forensic_filters = ForensicFiltersPanel()
        self.typography = TypographyProfiler()
        self.findings = FindingsPanel()

        self._container_layout.addWidget(self.file_info)
        self._container_layout.addWidget(self.hash_panel)
        self._container_layout.addWidget(self.forensic_filters)
        self._container_layout.addWidget(self.typography)
        self._container_layout.addWidget(self.findings)
        self._container_layout.addStretch()

        scroll.setWidget(container)
        layout.addWidget(scroll)

    def update_document(self, doc_model):
        """Update all inspector sections for a loaded document."""
        if doc_model:
            self.file_info.update_info(doc_model)
            self.hash_panel.update_hashes(doc_model.sha256, doc_model.md5,
                                          doc_model.integrity_status)
