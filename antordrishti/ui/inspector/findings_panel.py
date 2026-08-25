"""
Antordrishti — Findings Inspector Panel
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout, QFrame
)

from app.theme import Colors, Spacing
from ui.widgets.common import CollapsibleSection, SectionLabel, ActionButton


class FindingCard(QFrame):
    """Single finding display card."""

    def __init__(self, finding_id: str, module: str, status: str,
                 severity: str, confidence: float, region: str, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            FindingCard {{
                background-color: {Colors.PANEL_ALT};
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: 4px;
                padding: 8px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(3)

        # Header
        header = QHBoxLayout()
        id_label = QLabel(finding_id)
        id_label.setStyleSheet(
            f"font-size: 11px; font-weight: 600; color: {Colors.ACCENT};"
        )
        sev_label = QLabel(severity)
        sev_colors = {
            "Low": Colors.SUCCESS, "Medium": Colors.WARNING,
            "High": Colors.ERROR, "Critical": Colors.ERROR,
        }
        sev_label.setStyleSheet(
            f"font-size: 10px; font-weight: 500; "
            f"color: {sev_colors.get(severity, Colors.TEXT_TERTIARY)};"
        )
        header.addWidget(id_label)
        header.addStretch()
        header.addWidget(sev_label)
        layout.addLayout(header)

        # Module + Status
        mod_label = QLabel(f"Module: {module}")
        mod_label.setStyleSheet(f"font-size: 10px; color: {Colors.TEXT_SECONDARY};")
        layout.addWidget(mod_label)

        status_label = QLabel(f"Status: {status}")
        status_label.setStyleSheet(f"font-size: 10px; color: {Colors.TEXT_SECONDARY};")
        layout.addWidget(status_label)

        # Confidence + Region
        conf_label = QLabel(f"Confidence: {confidence:.0f}%  •  {region}")
        conf_label.setStyleSheet(f"font-size: 10px; color: {Colors.TEXT_TERTIARY};")
        layout.addWidget(conf_label)


class FindingsPanel(QWidget):
    """Forensic findings inspector section."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._section = CollapsibleSection("FORENSIC FINDINGS")

        # Demo findings
        self._section.add_widget(FindingCard(
            "F-001", "Copy-Move Detection", "Potential Anomaly",
            "Medium", 87.0, "Page 1, Region A"
        ))
        self._section.add_widget(FindingCard(
            "F-002", "Metadata Analysis", "No Significant Anomaly Detected",
            "Low", 23.0, "Document-wide"
        ))

        self._section.add_widget(ActionButton("Add Finding"))

        layout.addWidget(self._section)

    def add_finding(self, finding):
        """Add a finding to the panel."""
        if hasattr(finding, "finding_id"):
            card = FindingCard(
                finding.finding_id or "F-NEW",
                getattr(finding, "module", "General"),
                getattr(finding, "status", "Anomaly"),
                getattr(finding, "severity", "Medium"),
                getattr(finding, "confidence", 0.0),
                getattr(finding, "region", "Region"),
            )
            self._section.add_widget(card)
