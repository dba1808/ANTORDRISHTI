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

        # Title Bar
        title_bar = QWidget()
        title_bar.setFixedHeight(48)
        title_bar.setStyleSheet(f"""
            background-color: {Colors.CANVAS};
            border-bottom: 1px solid {Colors.BORDER_LIGHT};
        """)
        tb = QHBoxLayout(title_bar)
        tb.setContentsMargins(Spacing.LG, 0, Spacing.LG, 0)
        t = QLabel("Source Camera Identification & Acquisition Profiling")
        t.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {Colors.TEXT_PRIMARY};")
        tb.addWidget(t)
        tb.addStretch()
        layout.addWidget(title_bar)

        content = QHBoxLayout()
        content.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        content.setSpacing(Spacing.LG)

        # Center
        content.addWidget(EngineNotConnectedWidget("Source Camera"), 1)

        # Right panel
        right = QScrollArea()
        right.setWidgetResizable(True)
        right.setFixedWidth(280)
        right.setFrameShape(QFrame.NoFrame)
        right.setStyleSheet(f"""
            background-color: {Colors.CANVAS};
            border: 1px solid {Colors.BORDER_LIGHT};
            border-radius: 8px;
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
