"""
Antordrishti — Evidence Fusion Page
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QProgressBar
)
from PyQt5.QtCore import Qt

from app.theme import Colors, Spacing
from ui.widgets.common import SectionLabel, ActionButton, Separator, InfoRow


class _FusionItem(QFrame):
    """Single analysis module in the fusion display."""

    def __init__(self, name: str, status: str = "Not Analysed",
                 confidence: float = 0, strength: str = "N/A", parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            _FusionItem {{
                background-color: {Colors.PANEL};
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: 4px;
            }}
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(Spacing.MD, 8, Spacing.MD, 8)
        layout.setSpacing(Spacing.MD)

        name_label = QLabel(name)
        name_label.setStyleSheet(f"font-size: 12px; color: {Colors.TEXT_PRIMARY};")
        name_label.setMinimumWidth(180)
        layout.addWidget(name_label)

        status_label = QLabel(status)
        s_color = Colors.TEXT_TERTIARY
        if status == "Complete":
            s_color = Colors.SUCCESS
        elif status == "Running":
            s_color = Colors.ACCENT
        status_label.setStyleSheet(f"font-size: 11px; color: {s_color};")
        status_label.setMinimumWidth(100)
        layout.addWidget(status_label)

        conf_label = QLabel(f"{confidence:.0f}%" if confidence > 0 else "—")
        conf_label.setStyleSheet(f"font-size: 11px; color: {Colors.TEXT_SECONDARY};")
        conf_label.setMinimumWidth(50)
        layout.addWidget(conf_label)

        str_label = QLabel(strength)
        str_label.setStyleSheet(f"font-size: 11px; color: {Colors.TEXT_SECONDARY};")
        layout.addWidget(str_label)
        layout.addStretch()


class EvidenceFusionPage(QWidget):
    """Evidence Fusion page showing all analysis modules and overall assessment."""

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
        t = QLabel("Evidence Fusion")
        t.setProperty("heading", True)
        tb.addWidget(t)
        tb.addStretch()
        layout.addWidget(title_bar)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        c_layout = QVBoxLayout(container)
        c_layout.setContentsMargins(Spacing.XL, Spacing.MD, Spacing.XL, Spacing.MD)
        c_layout.setSpacing(Spacing.SM)

        # Header row
        header = QHBoxLayout()
        for label, width in [("Module", 180), ("Status", 100),
                             ("Confidence", 50), ("Evidence Strength", 0)]:
            h = QLabel(label)
            h.setStyleSheet(f"""
                font-size: 10px; font-weight: 600;
                color: {Colors.TEXT_TERTIARY};
                letter-spacing: 0.5px;
            """)
            if width:
                h.setMinimumWidth(width)
            header.addWidget(h)
        header.addStretch()
        c_layout.addLayout(header)

        modules = [
            "Copy-Move Detection", "Splicing Analysis",
            "Resampling Detection", "Noise Pattern Analysis",
            "Compression Analysis", "Illumination Analysis",
            "Metadata Analysis", "Typography Analysis",
            "Source Camera Analysis", "Model-Based Detection",
        ]
        for m in modules:
            c_layout.addWidget(_FusionItem(m))

        c_layout.addWidget(Separator())

        # Overall Assessment
        assessment = QFrame()
        assessment.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.PANEL};
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
                padding: 16px;
            }}
        """)
        a_layout = QVBoxLayout(assessment)
        a_layout.setSpacing(Spacing.SM)

        a_layout.addWidget(SectionLabel("Overall Assessment"))

        status = QLabel("Analysis Pending")
        status.setStyleSheet(
            f"font-size: 16px; font-weight: 600; color: {Colors.TEXT_TERTIARY};"
        )
        a_layout.addWidget(status)

        note = QLabel(
            "No analysis has been performed yet. Run forensic analysis modules "
            "to populate the evidence fusion results.\n\n"
            "Note: This assessment is computed from the combined results of "
            "all analysis modules. No fabricated conclusions are presented."
        )
        note.setWordWrap(True)
        note.setStyleSheet(f"font-size: 11px; color: {Colors.TEXT_SECONDARY};")
        a_layout.addWidget(note)

        c_layout.addWidget(assessment)

        c_layout.addWidget(ActionButton("Run All Analyses", primary=True))
        c_layout.addWidget(ActionButton("Generate Fusion Report"))
        c_layout.addStretch()

        scroll.setWidget(container)
        layout.addWidget(scroll, 1)
