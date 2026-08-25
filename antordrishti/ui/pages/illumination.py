"""
Antordrishti — Illumination Analysis Page
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea
)
from PyQt5.QtCore import Qt

from app.theme import Colors, Spacing
from ui.widgets.common import (
    SectionLabel, ActionButton, EngineNotConnectedWidget, InfoRow, Separator
)


class IlluminationPage(QWidget):
    """Illumination Analysis page."""

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
        t = QLabel("Illumination Analysis")
        t.setProperty("heading", True)
        tb.addWidget(t)
        tb.addStretch()
        layout.addWidget(title_bar)

        content = QHBoxLayout()
        content.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        content.setSpacing(Spacing.MD)

        content.addWidget(EngineNotConnectedWidget("Illumination"), 1)

        right = QFrame()
        right.setFixedWidth(260)
        right.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.PANEL};
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
            }}
        """)
        r_layout = QVBoxLayout(right)
        r_layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        r_layout.setSpacing(Spacing.SM)

        fields = [
            "Light Direction", "Illumination Map",
            "Regional Illumination", "Shadow Consistency",
            "Highlight Consistency", "Illumination Difference",
            "Illumination Anomaly Map",
        ]
        r_layout.addWidget(SectionLabel("Analysis Results"))
        for f in fields:
            r_layout.addWidget(InfoRow(f, "Not Analysed"))

        r_layout.addWidget(Separator())
        r_layout.addWidget(ActionButton("Run Analysis", primary=True))
        r_layout.addWidget(ActionButton("Show Illumination Map"))
        r_layout.addWidget(ActionButton("Add Finding"))
        r_layout.addStretch()

        content.addWidget(right)
        layout.addLayout(content, 1)
