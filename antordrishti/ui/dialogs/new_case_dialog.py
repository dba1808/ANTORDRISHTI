"""
Antordrishti — New Case Dialog
Professional case creation with auto-generated IDs and SQLite persistence.
"""

from typing import Optional

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTextEdit, QDateEdit, QPushButton, QFormLayout, QMessageBox
)
from PyQt5.QtCore import Qt, QDate

from app.theme import Colors, Spacing
from models.case_model import CaseModel
from services.db_service import get_db
from ui.widgets.common import ActionButton, SectionLabel


class NewCaseDialog(QDialog):
    """Professional New Case dialog with auto-generated IDs and validation."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Case — Antordrishti")
        self.setMinimumSize(500, 520)
        self.setStyleSheet(f"background-color: {Colors.PANEL};")

        self._case = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.XXL, Spacing.XL,
                                  Spacing.XXL, Spacing.XL)
        layout.setSpacing(Spacing.MD)

        # Header
        header = QLabel("Create New Case")
        header.setStyleSheet(
            f"font-size: 16px; font-weight: 600; color: {Colors.TEXT_PRIMARY};"
        )
        layout.addWidget(header)

        desc = QLabel("Enter case information to create a new forensic case.")
        desc.setStyleSheet(f"font-size: 12px; color: {Colors.TEXT_SECONDARY};")
        layout.addWidget(desc)

        # Form
        form = QFormLayout()
        form.setSpacing(Spacing.SM)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # Auto-generate Case ID
        self._case_id = QLineEdit()
        try:
            auto_id = get_db().generate_case_id()
            self._case_id.setText(auto_id)
        except Exception:
            self._case_id.setPlaceholderText("e.g., CASE-2026-001")
        form.addRow("Case ID:", self._case_id)

        self._title = QLineEdit()
        self._title.setPlaceholderText("Case title (required)")
        form.addRow("Title:", self._title)

        self._examiner = QLineEdit()
        self._examiner.setPlaceholderText("Examiner name (required)")
        form.addRow("Examiner:", self._examiner)

        self._org = QLineEdit()
        self._org.setPlaceholderText("Organization")
        form.addRow("Organization:", self._org)

        self._ref = QLineEdit()
        self._ref.setPlaceholderText("Reference number")
        form.addRow("Reference:", self._ref)

        self._date = QDateEdit()
        self._date.setDate(QDate.currentDate())
        self._date.setCalendarPopup(True)
        form.addRow("Date:", self._date)

        self._description = QTextEdit()
        self._description.setPlaceholderText("Case description...")
        self._description.setMaximumHeight(80)
        form.addRow("Description:", self._description)

        self._notes = QTextEdit()
        self._notes.setPlaceholderText("Additional notes...")
        self._notes.setMaximumHeight(60)
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
        title = self._title.text().strip()
        examiner = self._examiner.text().strip()

        errors = []
        if not case_id:
            errors.append("Case ID is required.")
        if not title:
            errors.append("Case Title is required.")
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

        self._case = CaseModel(
            case_id=self._case_id.text().strip(),
            title=self._title.text().strip(),
            examiner_name=self._examiner.text().strip(),
            organization=self._org.text().strip(),
            reference_number=self._ref.text().strip(),
            date=self._date.date().toString("yyyy-MM-dd"),
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
                
            db._conn.execute(
                """INSERT INTO case_events
                   (case_id, evidence_id, event_type, description, timestamp)
                   VALUES (?, ?, ?, ?, ?)""",
                (self._case.case_id, "", "Case Created", f"Manually created case: {self._case.title}", __import__('datetime').datetime.now().isoformat())
            )
            db._conn.commit()
        except Exception as e:
            QMessageBox.warning(
                self, "Database Error",
                f"Could not save case to database:\n{str(e)}"
            )
            # Still allow in-memory creation
            pass

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
