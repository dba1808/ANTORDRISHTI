"""
Antordrishti — Document Forensics Page (Tabbed)
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget
)
from PyQt5.QtCore import Qt

from app.theme import Colors, Spacing
from ui.widgets.common import (
    SectionLabel, ActionButton, EngineNotConnectedWidget, InfoRow, Separator
)


def _make_doc_tab(title: str, items: list) -> QWidget:
    w = QWidget()
    layout = QVBoxLayout(w)
    layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
    layout.setSpacing(Spacing.SM)
    layout.addWidget(SectionLabel(title))
    for label in items:
        layout.addWidget(InfoRow(label, "Not Analysed"))
    layout.addWidget(Separator())
    layout.addWidget(ActionButton(f"Run {title}", primary=True))
    layout.addWidget(ActionButton("Add Finding"))
    layout.addStretch()
    return w


class DocumentForensicsPage(QWidget):
    """Document Forensics tabbed page."""

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
        title = QLabel("Questioned Document Forensics")
        title.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {Colors.TEXT_PRIMARY};")
        tb_layout.addWidget(title)
        tb_layout.addStretch()
        layout.addWidget(title_bar)

        tabs = QTabWidget()
        tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {Colors.BORDER_LIGHT};
                background-color: {Colors.CANVAS};
                border-radius: 6px;
            }}
        """)

        tabs.addTab(
            _make_doc_tab("Typography Profiler", [
                "Font Family", "Font Size", "Font Weight",
                "Character Spacing", "Word Spacing",
                "Line Spacing", "Baseline Consistency", "Alignment"
            ]),
            "Typography"
        )
        tabs.addTab(
            _make_doc_tab("Writer Analysis", [
                "Writing Style", "Character Formation",
                "Stroke Analysis", "Pressure Pattern"
            ]),
            "Writer Analysis"
        )
        tabs.addTab(
            _make_doc_tab("Signature Analysis", [
                "Signature Region", "Stroke Pattern",
                "Pressure Distribution", "Consistency",
                "Questioned vs Sample"
            ]),
            "Signature"
        )
        tabs.addTab(
            _make_doc_tab("Handwriting Analysis", [
                "Handwriting Regions", "Character Analysis",
                "Baseline Alignment", "Slant Angle",
                "Spacing Pattern"
            ]),
            "Handwriting"
        )
        tabs.addTab(
            _make_doc_tab("Text Layout Analysis", [
                "Text Blocks", "Column Structure",
                "Line Detection", "Paragraph Analysis",
                "Margin Consistency"
            ]),
            "Text Layout"
        )
        tabs.addTab(
            _make_doc_tab("Stamp / Seal Analysis", [
                "Stamp Region", "Color Consistency",
                "Shape Analysis", "Text in Stamp",
                "Impression Quality"
            ]),
            "Stamp / Seal"
        )
        tabs.addTab(
            _make_doc_tab("Printed Text", [
                "Print Quality", "Printer Identification",
                "Toner Pattern", "Banding Artifacts"
            ]),
            "Printed Text"
        )

        layout.addWidget(tabs, 1)
