"""
Antordrishti — New Case Dialog
Professional case creation with auto-generated IDs and SQLite persistence.
"""

from typing import Optional

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTextEdit, QDateEdit, QPushButton, QFormLayout, QMessageBox, QComboBox
)
from PyQt5.QtCore import Qt, QDate

from app.theme import Colors, Spacing
from models.case_model import CaseModel, IST_TZ
from services.db_service import get_db
from ui.widgets.common import ActionButton, SectionLabel
from datetime import datetime


class NewCaseDialog(QDialog):
    """Professional New Case dialog with auto-generated IDs and validation."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Case — Antordrishti")
        self.setMinimumSize(520, 560)
        self.setStyleSheet(f"background-color: {Colors.PANEL};")

        self._case = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.XXL, Spacing.XL,
                                  Spacing.XXL, Spacing.XL)
        layout.setSpacing(Spacing.MD)

        # Header
        header = QLabel("Create New Forensic Case")
        header.setStyleSheet(
            f"font-size: 16px; font-weight: 600; color: {Colors.TEXT_PRIMARY};"
        )
        layout.addWidget(header)

        desc = QLabel("Enter case information to establish a persistent forensic investigation context.")
        desc.setStyleSheet(f"font-size: 12px; color: {Colors.TEXT_SECONDARY};")
        layout.addWidget(desc)

        # Form
        form = QFormLayout()
        form.setSpacing(Spacing.SM)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # Case Name
        self._case_name = QLineEdit()
        self._case_name.setPlaceholderText("Case Name (required, e.g., Questioned Deed Examination)")
        form.addRow("Case Name:", self._case_name)

        # Auto-generate Case ID
        self._case_id = QLineEdit()
        try:
            auto_id = get_db().generate_case_id()
            self._case_id.setText(auto_id)
        except Exception:
            year = datetime.now(IST_TZ).strftime("%Y")
            self._case_id.setText(f"CASE-{year}-000001")
        form.addRow("Case ID:", self._case_id)

        # Status
        self._status = QComboBox()
        self._status.addItems(["OPEN", "IN PROGRESS", "COMPLETED", "ARCHIVED"])
        self._status.setCurrentText("OPEN")
        form.addRow("Status:", self._status)

        self._examiner = QLineEdit()
        self._examiner.setPlaceholderText("Examiner name (required)")
        form.addRow("Examiner:", self._examiner)

        self._org = QLineEdit()
        self._org.setPlaceholderText("Organization / Laboratory")
        form.addRow("Organization:", self._org)

        self._ref = QLineEdit()
        self._ref.setPlaceholderText("Reference / FIR / Docket number")
        form.addRow("Reference:", self._ref)

        self._date = QDateEdit()
        self._date.setDate(QDate.currentDate())
        self._date.setCalendarPopup(True)
        form.addRow("Date:", self._date)

        # Created Timestamp display (IST)
        now_ist = datetime.now(IST_TZ).strftime("%Y-%m-%d %H:%M:%S IST (UTC+05:30)")
        self._ts_lbl = QLabel(now_ist)
        self._ts_lbl.setStyleSheet(f"font-size: 11px; color: {Colors.TEXT_SECONDARY}; font-family: monospace;")
        form.addRow("Created (IST):", self._ts_lbl)

        self._description = QTextEdit()
        self._description.setPlaceholderText("Case description...")
        self._description.setMaximumHeight(70)
        form.addRow("Description:", self._description)

        self._notes = QTextEdit()
        self._notes.setPlaceholderText("Additional notes / chain of custody notes...")
        self._notes.setMaximumHeight(50)
        form.addRow("Notes:", self._notes)

        layout.addLayout(form)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = ActionButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        create_btn = ActionButton("Create Case", primary=True)
        create_btn.clicked.connect(self._on_create)
        btn_layout.addWidget(create_btn)

        layout.addLayout(btn_layout)

    def _validate(self) -> bool:
        """Validate required fields before creation."""
        case_id = self._case_id.text().strip()
        case_name = self._case_name.text().strip()
        examiner = self._examiner.text().strip()

        errors = []
        if not case_name:
            errors.append("Case Name is required.")
        if not case_id:
            errors.append("Case ID is required.")
        if not examiner:
            errors.append("Examiner Name is required.")

        if errors:
            QMessageBox.warning(
                self, "Validation Error",
                "Please fix the following:\n\n" + "\n".join(f"• {e}" for e in errors)
            )
            return False
        return True

    def _on_create(self):
        if not self._validate():
            return

        name = self._case_name.text().strip()
        cid = self._case_id.text().strip()
        status_val = self._status.currentText().strip().upper()
        now_dt = datetime.now(IST_TZ)

        self._case = CaseModel(
            case_id=cid,
            case_name=name,
            title=name,
            examiner_name=self._examiner.text().strip(),
            organization=self._org.text().strip(),
            reference_number=self._ref.text().strip(),
            date=self._date.date().toString("yyyy-MM-dd"),
            status=status_val,
            created=now_dt,
            modified=now_dt,
            description=self._description.toPlainText().strip(),
            notes=self._notes.toPlainText().strip(),
        )

        # Persist to SQLite
        try:
            db = get_db()
            success = db.create_case(self._case.to_dict())
            if not success:
                QMessageBox.warning(
                    self, "Duplicate Case ID",
                    f"A case with ID '{self._case.case_id}' already exists.\n"
                    "Please use a different Case ID."
                )
                return
                
            db.add_case_event(
                self._case.case_id,
                "",
                "Case Created",
                f"Created forensic case: {self._case.case_name} ({self._case.case_id})"
            )
        except Exception as e:
            QMessageBox.warning(
                self, "Database Error",
                f"Could not save case to database:\n{str(e)}"
            )

        self.accept()

    def get_case(self) -> Optional[CaseModel]:
        return self._case

    @property
    def case_id_edit(self) -> QLineEdit:
        return self._case_id

    @property
    def title_edit(self) -> QLineEdit:
        return self._title

    @property
    def examiner_edit(self) -> QLineEdit:
        return self._examiner

    @property
    def organization_edit(self) -> QLineEdit:
        return self._org

    @property
    def reference_edit(self) -> QLineEdit:
        return self._ref

    @property
    def date_edit(self) -> QDateEdit:
        return self._date

    @property
    def description_edit(self) -> QTextEdit:
        return self._description

    @property
    def notes_edit(self) -> QTextEdit:
        return self._notes
