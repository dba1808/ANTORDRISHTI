"""
Antordrishti — Watermark Detection Page
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QGroupBox, QRadioButton, QFrame, QScrollArea
)
from PyQt5.QtCore import Qt

from app.theme import Colors, Spacing
from ui.widgets.common import (
    SectionLabel, ActionButton, EngineNotConnectedWidget,
    Separator, StatusIndicator
)


class WatermarkPage(QWidget):
    """Watermark Detection page."""

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
        tb_layout = QHBoxLayout(title_bar)
        tb_layout.setContentsMargins(Spacing.LG, 0, Spacing.LG, 0)
        title = QLabel("Forensic Watermark & Steganography Examination")
        title.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {Colors.TEXT_PRIMARY};")
        tb_layout.addWidget(title)
        tb_layout.addStretch()
        layout.addWidget(title_bar)

        # Content
        content = QHBoxLayout()
        content.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        content.setSpacing(Spacing.LG)

        # Center: Visualization
        center = EngineNotConnectedWidget("Watermark Detection")
        content.addWidget(center, 1)

        # Right: Controls
        right = QFrame()
        right.setFixedWidth(260)
        right.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.CANVAS};
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: 8px;
            }}
        """)
        r_layout = QVBoxLayout(right)
        r_layout.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        r_layout.setSpacing(Spacing.MD)

        # Watermark Type
        r_layout.addWidget(SectionLabel("Watermark Type"))
        for wt in ["Visible", "Invisible", "Fragile", "Semi-Fragile", "Robust"]:
            rb = QRadioButton(wt)
            if wt == "Visible":
                rb.setChecked(True)
            r_layout.addWidget(rb)

        r_layout.addWidget(Separator())

        # Actions
        r_layout.addWidget(SectionLabel("Actions"))
        r_layout.addWidget(ActionButton("Detect Watermark", primary=True))
        r_layout.addWidget(ActionButton("Extract Watermark"))
        r_layout.addWidget(ActionButton("Verify Watermark"))
        r_layout.addWidget(ActionButton("Compare Watermark"))
        r_layout.addWidget(ActionButton("Check Integrity"))

        r_layout.addWidget(Separator())

        # Status
        r_layout.addWidget(SectionLabel("Watermark Status"))
        self._status = StatusIndicator("Not Detected", "pending")
        r_layout.addWidget(self._status)

        r_layout.addStretch()
        content.addWidget(right)

        layout.addLayout(content, 1)
