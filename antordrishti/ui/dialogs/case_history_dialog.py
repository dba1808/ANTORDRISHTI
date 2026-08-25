"""
Antordrishti — Case History Dialog
Browse, open, and delete past forensic cases from SQLite.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QPushButton, QMessageBox,
    QAbstractItemView
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QCursor

from app.theme import Colors, Spacing
from services.db_service import get_db
from models.case_model import CaseModel
from ui.widgets.common import ActionButton


class CaseHistoryDialog(QDialog):
    """Dialog for browsing past forensic cases stored in SQLite."""

    case_selected = pyqtSignal(object)  # Emits CaseModel

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Case History — Antordrishti")
        self.setMinimumSize(700, 450)
        self.setStyleSheet(f"background-color: {Colors.PANEL};")

        self._selected_case = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.XL, Spacing.XL,
                                  Spacing.XL, Spacing.XL)
        layout.setSpacing(Spacing.MD)

        # Header
        header = QLabel("Case History")
        header.setStyleSheet(
            f"font-size: 16px; font-weight: 600; color: {Colors.TEXT_PRIMARY};"
        )
        layout.addWidget(header)

        desc = QLabel("Double-click a case to open it, or select and use the buttons below.")
        desc.setStyleSheet(f"font-size: 12px; color: {Colors.TEXT_SECONDARY};")
        layout.addWidget(desc)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels([
            "Case ID", "Title", "Examiner", "Date", "Status"
        ])
        self._table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self._table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self._table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.ResizeToContents
        )
        self._table.horizontalHeader().setSectionResizeMode(
            4, QHeaderView.ResizeMode.ResizeToContents
        )
        self._table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self._table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self._table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.doubleClicked.connect(self._on_double_click)
        self._table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {Colors.PANEL};
                border: 1px solid {Colors.BORDER};
                gridline-color: {Colors.BORDER_LIGHT};
                font-size: 12px;
            }}
            QTableWidget::item {{
                padding: 6px 8px;
                color: {Colors.TEXT_PRIMARY};
            }}
            QTableWidget::item:selected {{
                background-color: {Colors.ACCENT_LIGHT};
                color: {Colors.TEXT_PRIMARY};
            }}
            QHeaderView::section {{
                background-color: #F8FAFC;
                color: {Colors.TEXT_SECONDARY};
                font-weight: 600;
                font-size: 11px;
                padding: 6px 8px;
                border: none;
                border-bottom: 1px solid {Colors.BORDER};
            }}
        """)
        layout.addWidget(self._table)

        # Buttons
        btn_layout = QHBoxLayout()

        delete_btn = ActionButton("Delete Selected")
        delete_btn.clicked.connect(self._on_delete)
        btn_layout.addWidget(delete_btn)

        btn_layout.addStretch()

        cancel_btn = ActionButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        open_btn = ActionButton("Open Case", primary=True)
        open_btn.clicked.connect(self._on_open)
        btn_layout.addWidget(open_btn)

        layout.addLayout(btn_layout)

        # Load data
        self._load_cases()

    def _load_cases(self):
        """Populate the table from SQLite."""
        self._table.setRowCount(0)
        try:
            cases = get_db().get_cases()
            self._table.setRowCount(len(cases))
            for row, case_data in enumerate(cases):
                self._table.setItem(
                    row, 0, QTableWidgetItem(case_data.get("case_id", ""))
                )
                self._table.setItem(
                    row, 1, QTableWidgetItem(case_data.get("title", ""))
                )
                self._table.setItem(
                    row, 2, QTableWidgetItem(case_data.get("examiner", ""))
                )
                self._table.setItem(
                    row, 3, QTableWidgetItem(case_data.get("date", ""))
                )

                status = case_data.get("status", "Open")
                status_item = QTableWidgetItem(status)
                if status == "Open":
                    status_item.setForeground(Qt.GlobalColor.darkGreen)
                elif status == "Closed":
                    status_item.setForeground(Qt.GlobalColor.darkRed)
                self._table.setItem(row, 4, status_item)
        except Exception:
            pass

    def _get_selected_case_id(self):
        """Return the case_id of the selected row, or None."""
        rows = self._table.selectionModel().selectedRows()
        if rows:
            row = rows[0].row()
            item = self._table.item(row, 0)
            return item.text() if item else None
        return None

    def _on_open(self):
        case_id = self._get_selected_case_id()
        if not case_id:
            QMessageBox.information(
                self, "No Selection", "Please select a case to open."
            )
            return

        case_data = get_db().get_case(case_id)
        if case_data:
            self._selected_case = CaseModel.from_dict(case_data)
            self.case_selected.emit(self._selected_case)
            self.accept()

    def _on_double_click(self, index):
        self._on_open()

    def _on_delete(self):
        case_id = self._get_selected_case_id()
        if not case_id:
            QMessageBox.information(
                self, "No Selection", "Please select a case to delete."
            )
            return

        reply = QMessageBox.question(
            self, "Confirm Deletion",
            f"Are you sure you want to delete case '{case_id}'?\n\n"
            "This will also remove all associated evidence records.\n"
            "This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            get_db().delete_case(case_id)
            self._load_cases()

    def get_selected_case(self):
        return self._selected_case
