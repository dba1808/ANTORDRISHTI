"""
Antordrishti — Export Options Dialog
Provides options for exporting reports, evidence, or analysis results.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QCheckBox, QLineEdit, QFileDialog
)
from PyQt5.QtCore import Qt

from app.theme import Colors, Spacing
from ui.widgets.common import ActionButton, SectionLabel, Separator


class ExportDialog(QDialog):
    """Export configuration dialog."""

    def __init__(self, export_type: str = "Report", parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Export {export_type} — Antordrishti")
        self.setMinimumSize(460, 360)
        self.setStyleSheet(f"background-color: {Colors.PANEL};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.XXL, Spacing.XL, Spacing.XXL, Spacing.XL)
        layout.setSpacing(Spacing.MD)

        title = QLabel(f"Export {export_type}")
        title.setStyleSheet(
            f"font-size: 16px; font-weight: 600; color: {Colors.TEXT_PRIMARY};"
        )
        layout.addWidget(title)
        layout.addWidget(Separator())

        layout.addWidget(SectionLabel("Format"))
        self._format_combo = QComboBox()
        if export_type == "Report":
            self._format_combo.addItems(["PDF Document (*.pdf)", "HTML Page (*.html)", "Plain Text (*.txt)"])
        elif export_type == "Image":
            self._format_combo.addItems(["PNG Image (*.png)", "JPEG Image (*.jpg)", "TIFF Image (*.tiff)"])
        else:
            self._format_combo.addItems(["ZIP Evidence Package (*.zip)", "JSON Case Metadata (*.json)"])
        layout.addWidget(self._format_combo)

        layout.addWidget(SectionLabel("Include Components"))
        self._cb_case = QCheckBox("Case & Examiner Metadata")
        self._cb_case.setChecked(True)
        self._cb_hash = QCheckBox("Hash Verification Records")
        self._cb_hash.setChecked(True)
        self._cb_findings = QCheckBox("Forensic Findings & Annotations")
        self._cb_findings.setChecked(True)
        layout.addWidget(self._cb_case)
        layout.addWidget(self._cb_hash)
        layout.addWidget(self._cb_findings)

        layout.addWidget(Separator())

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        cancel_btn = ActionButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        export_btn = ActionButton("Export", primary=True)
        export_btn.clicked.connect(self.accept)
        btn_layout.addWidget(export_btn)

        layout.addLayout(btn_layout)
