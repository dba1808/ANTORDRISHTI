"""
Antordrishti — OCR & Text Extraction Page
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPlainTextEdit, QFrame, QScrollArea, QSplitter, QGroupBox,
    QRadioButton, QButtonGroup
)
from PyQt5.QtCore import Qt

from app.theme import Colors, Spacing
from ui.widgets.common import (
    SectionLabel, ActionButton, EngineNotConnectedWidget, Separator
)


class OCRPage(QWidget):
    """OCR & Text Extraction page."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Title
        title_bar = QWidget()
        title_bar.setFixedHeight(36)
        title_bar.setStyleSheet(f"""
            background-color: {Colors.PANEL};
            border-bottom: 1px solid {Colors.BORDER_LIGHT};
        """)
        tb_layout = QHBoxLayout(title_bar)
        tb_layout.setContentsMargins(Spacing.MD, 0, Spacing.MD, 0)
        title = QLabel("OCR & Text Extraction")
        title.setProperty("heading", True)
        tb_layout.addWidget(title)
        tb_layout.addStretch()
        layout.addWidget(title_bar)

        # Content splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: Document preview placeholder
        preview = EngineNotConnectedWidget("OCR")
        splitter.addWidget(preview)

        # Right: Controls + Results
        right = QWidget()
        right.setMaximumWidth(340)
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(Spacing.MD, Spacing.MD,
                                        Spacing.MD, Spacing.MD)
        right_layout.setSpacing(Spacing.MD)

        # Language
        right_layout.addWidget(SectionLabel("Language"))
        self._lang = QComboBox()
        self._lang.addItems(["English", "Bengali", "Hindi", "Auto Detect"])
        right_layout.addWidget(self._lang)

        # OCR Mode
        right_layout.addWidget(SectionLabel("OCR Mode"))
        mode_group = QGroupBox()
        mode_group.setStyleSheet("QGroupBox { border: none; margin-top: 0px; }")
        mode_layout = QVBoxLayout(mode_group)
        mode_layout.setContentsMargins(0, 0, 0, 0)
        self._mode_full = QRadioButton("Full Page")
        self._mode_full.setChecked(True)
        self._mode_region = QRadioButton("Selected Region")
        self._mode_blocks = QRadioButton("Text Blocks")
        mode_layout.addWidget(self._mode_full)
        mode_layout.addWidget(self._mode_region)
        mode_layout.addWidget(self._mode_blocks)
        right_layout.addWidget(mode_group)

        right_layout.addWidget(Separator())

        # Results
        right_layout.addWidget(SectionLabel("Extracted Text"))
        self._result_text = QPlainTextEdit()
        self._result_text.setPlaceholderText(
            "OCR results will appear here after extraction..."
        )
        self._result_text.setReadOnly(True)
        right_layout.addWidget(self._result_text, 1)

        # Confidence
        self._conf_label = QLabel("OCR Confidence: —")
        self._conf_label.setStyleSheet(
            f"font-size: 11px; color: {Colors.TEXT_TERTIARY};"
        )
        right_layout.addWidget(self._conf_label)

        right_layout.addWidget(Separator())

        # Actions
        right_layout.addWidget(SectionLabel("Actions"))
        right_layout.addWidget(ActionButton("Run OCR", primary=True))
        right_layout.addWidget(ActionButton("Copy Text"))
        right_layout.addWidget(ActionButton("Export Text"))
        right_layout.addWidget(ActionButton("Compare Text"))

        splitter.addWidget(right)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)

        layout.addWidget(splitter, 1)
