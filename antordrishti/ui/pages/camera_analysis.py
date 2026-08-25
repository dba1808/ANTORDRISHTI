"""
Antordrishti — Source Camera Analysis Page
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea
)
from PyQt5.QtCore import Qt

from app.theme import Colors, Spacing
from ui.widgets.common import (
    SectionLabel, ActionButton, EngineNotConnectedWidget, InfoRow,
    Separator, CollapsibleSection
)


class CameraAnalysisPage(QWidget):
    """Source Camera Analysis page."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        title_bar = QWidget()
        title_bar.setFixedHeight(36)
        title_bar.setStyleSheet(f"""
            background-color: {Colors.PANEL};
            border-bottom: 1px solid {Colors.BORDER_LIGHT};
        """)
        tb = QHBoxLayout(title_bar)
        tb.setContentsMargins(Spacing.MD, 0, Spacing.MD, 0)
        tb.addWidget(QLabel("Source Camera Analysis"))
        tb.itemAt(0).widget().setProperty("heading", True)
        tb.addStretch()
        layout.addWidget(title_bar)

        content = QHBoxLayout()
        content.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        content.setSpacing(Spacing.MD)

        # Center
        content.addWidget(EngineNotConnectedWidget("Source Camera"), 1)

        # Right panel
        right = QScrollArea()
        right.setWidgetResizable(True)
        right.setFixedWidth(280)
        right.setFrameShape(QFrame.NoFrame)
        right.setStyleSheet(f"""
            background-color: {Colors.PANEL};
            border: 1px solid {Colors.BORDER};
            border-radius: 4px;
        """)

        info = QWidget()
        info.setStyleSheet("background: transparent;")
        info_layout = QVBoxLayout(info)
        info_layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        info_layout.setSpacing(Spacing.SM)

        sections = [
            ("Camera Information", [
                "Camera Make", "Camera Model", "Serial Number",
                "Firmware Version", "Lens Info"
            ]),
            ("Image Acquisition", [
                "Date/Time", "Exposure", "Aperture",
                "ISO", "Focal Length", "Flash"
            ]),
            ("Sensor Analysis", [
                "Sensor Pattern", "PRNU Status",
                "CFA Pattern", "Dead Pixels"
            ]),
            ("JPEG Signature", [
                "Quantization Table", "Huffman Table",
                "Thumbnail Consistency"
            ]),
            ("Camera Consistency", [
                "Overall Match", "Confidence"
            ]),
        ]

        for sec_title, fields in sections:
            info_layout.addWidget(SectionLabel(sec_title))
            for f in fields:
                info_layout.addWidget(InfoRow(f, "—"))
            info_layout.addWidget(Separator())

        info_layout.addWidget(ActionButton("Run Analysis", primary=True))
        info_layout.addWidget(ActionButton("Compare Camera"))
        info_layout.addWidget(ActionButton("Add Finding"))
        info_layout.addStretch()

        right.setWidget(info)
        content.addWidget(right)
        layout.addLayout(content, 1)
