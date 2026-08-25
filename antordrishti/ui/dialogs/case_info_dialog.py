"""
Antordrishti — Case Info Dialog
Displays current case information with options to edit or close.
"""

from typing import Optional

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QFormLayout,
    QTextEdit, QLineEdit
)
from PyQt5.QtCore import Qt

from app.theme import Colors, Spacing
from models.case_model import CaseModel
from ui.widgets.common import ActionButton, SectionLabel, InfoRow, Separator


class CaseInfoDialog(QDialog):
    """Displays case metadata and details."""

    def __init__(self, case: Optional[CaseModel] = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Case Information — Antordrishti")
        self.setMinimumSize(480, 420)
        self.setStyleSheet(f"background-color: {Colors.PANEL};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.XXL, Spacing.XL, Spacing.XXL, Spacing.XL)
        layout.setSpacing(Spacing.MD)

        title = QLabel("Case Details")
        title.setStyleSheet(
            f"font-size: 16px; font-weight: 600; color: {Colors.TEXT_PRIMARY};"
        )
        layout.addWidget(title)
        layout.addWidget(Separator())

        if case:
            layout.addWidget(InfoRow("Case ID", case.case_id or "—"))
            layout.addWidget(InfoRow("Title", case.title or "—"))
            layout.addWidget(InfoRow("Examiner", case.examiner_name or "—"))
            layout.addWidget(InfoRow("Organization", case.organization or "—"))
            layout.addWidget(InfoRow("Reference", case.reference_number or "—"))
            layout.addWidget(InfoRow("Date", case.date or "—"))
            layout.addWidget(InfoRow("Status", case.status or "Open"))
            layout.addWidget(Separator())
            layout.addWidget(SectionLabel("Description"))
            desc = QLabel(case.description or "No description provided.")
            desc.setWordWrap(True)
            desc.setStyleSheet(f"font-size: 11px; color: {Colors.TEXT_SECONDARY};")
            layout.addWidget(desc)
        else:
            no_case = QLabel("No case is currently open.\nCreate a new case from File -> New Case.")
            no_case.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_case.setStyleSheet(f"font-size: 12px; color: {Colors.TEXT_TERTIARY};")
            layout.addWidget(no_case)

        layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = ActionButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
