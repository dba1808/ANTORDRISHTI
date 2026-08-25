"""
Antordrishti — Evidence Manager Page
Manage evidence items, wire to SQLite, auto-generate EVD-IDs, integrity verification.
"""

import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QFrame, QMenu, QFileDialog, QMessageBox,
    QAbstractItemView
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor

from app.theme import Colors, Spacing
from ui.widgets.common import SectionLabel, ActionButton, Separator
from services.db_service import get_db
from models.evidence_model import EvidenceModel
from services.hash_service import calculate_hashes


class EvidenceManagerPage(QWidget):
    """Evidence Manager page with evidence table and actions wired to SQLite."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_case_id = ""

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
        tb = QHBoxLayout(title_bar)
        tb.setContentsMargins(Spacing.MD, 0, Spacing.MD, 0)
        t = QLabel("Evidence Manager")
        t.setProperty("heading", True)
        tb.addWidget(t)
        
        self._case_label = QLabel()
        self._case_label.setStyleSheet(f"color: {Colors.TEXT_TERTIARY}; font-size: 11px;")
        tb.addWidget(self._case_label)
        
        tb.addStretch()
        layout.addWidget(title_bar)

        # Content
        content = QVBoxLayout()
        content.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        content.setSpacing(Spacing.MD)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(Spacing.SM)
        self.btn_add = ActionButton("Add Evidence", primary=True)
        self.btn_add.clicked.connect(self._on_add_evidence)
        self.btn_verify = ActionButton("Verify Integrity")
        self.btn_verify.clicked.connect(self._on_verify_evidence)
        self.btn_view = ActionButton("View Details")
        btn_export = ActionButton("Export")
        btn_export.clicked.connect(self._on_export_evidence)
        
        btn_remove = ActionButton("Remove")
        btn_remove.clicked.connect(self._on_remove_evidence)

        toolbar.addWidget(self.btn_add)
        toolbar.addWidget(self.btn_verify)
        toolbar.addWidget(self.btn_view)
        toolbar.addWidget(btn_export)
        toolbar.addStretch()
        toolbar.addWidget(btn_remove)
        content.addLayout(toolbar)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels([
            "Evidence ID", "Name", "Type", "File Path", "SHA-256", "Status", "Date Added"
        ])
        
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        
        self._table.verticalHeader().setVisible(False)
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._show_context_menu)
        
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

        content.addWidget(self._table, 1)
        layout.addLayout(content, 1)

        # Set up a polling timer to check if current case has changed
        # A more robust way would be signals, but this is a simple page isolation
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._check_case_update)
        self._timer.start(2000)

    def set_case(self, case_id: str):
        """Set the active case and reload evidence."""
        if self._current_case_id != case_id:
            self._current_case_id = case_id
            if case_id:
                self._case_label.setText(f"(Active: {case_id})")
                self.btn_add.setEnabled(True)
            else:
                self._case_label.setText("(No active case)")
                self.btn_add.setEnabled(False)
            self._load_data()

    def _check_case_update(self):
        """Check the main window's active case and update if needed."""
        # Find main window by traversing parents
        parent = self.parentWidget()
        while parent:
            if hasattr(parent, '_current_case') and parent._current_case:
                self.set_case(parent._current_case.case_id)
                return
            parent = parent.parentWidget()
        
        self.set_case("")

    def _load_data(self):
        """Load evidence from SQLite for the current case."""
        self._table.setRowCount(0)
        if not self._current_case_id:
            return

        db = get_db()
        items = db.get_evidence_for_case(self._current_case_id)
        
        self._table.setRowCount(len(items))
        for row, item in enumerate(items):
            self._table.setItem(row, 0, QTableWidgetItem(item.get("evidence_id", "")))
            self._table.setItem(row, 1, QTableWidgetItem(item.get("name", "")))
            self._table.setItem(row, 2, QTableWidgetItem(item.get("evidence_type", "")))
            self._table.setItem(row, 3, QTableWidgetItem(item.get("file_path", "")))
            
            sha256 = item.get("sha256", "")
            if sha256 and len(sha256) > 16:
                sha256 = sha256[:8] + "..." + sha256[-8:]
            self._table.setItem(row, 4, QTableWidgetItem(sha256))
            
            status = item.get("status", "Pending")
            status_item = QTableWidgetItem(status)
            if status == "Verified":
                status_item.setForeground(Qt.GlobalColor.darkGreen)
            elif status == "Error":
                status_item.setForeground(Qt.GlobalColor.darkRed)
            self._table.setItem(row, 5, status_item)
            
            created = item.get("created_at", "")[:16].replace("T", " ")
            self._table.setItem(row, 6, QTableWidgetItem(created))

    def _on_add_evidence(self):
        if not self._current_case_id:
            QMessageBox.warning(self, "No Case", "Please create or open a case first.")
            return

        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Evidence Files", "",
            "Supported Files (*.jpg *.jpeg *.png *.tiff *.tif *.bmp *.pdf);;All Files (*.*)"
        )
        
        if not files:
            return
            
        db = get_db()
        added = 0
        
        # Could show a progress dialog here for large files since hashing takes time
        for f in files:
            name = os.path.basename(f)
            # Calculate hash immediately on import
            sha256, md5 = calculate_hashes(f)
            status = "Verified" if sha256 else "Error"
            
            evd_id = db.generate_evidence_id(self._current_case_id)
            
            evidence = EvidenceModel(
                evidence_id=evd_id,
                case_id=self._current_case_id,
                name=name,
                evidence_type="Original Evidence",
                source="File Import",
                file_path=f,
                sha256=sha256 or "",
                md5=md5 or "",
                status=status
            )
            
            if db.add_evidence(evidence.to_dict()):
                added += 1
                
        if added > 0:
            self._load_data()
            QMessageBox.information(self, "Evidence Added", f"Successfully added {added} evidence item(s).")

    def _on_verify_evidence(self):
        rows = self._table.selectionModel().selectedRows()
        if not rows:
            QMessageBox.information(self, "No Selection", "Please select evidence items to verify.")
            return
            
        db = get_db()
        verified = 0
        failed = 0
        
        for index in rows:
            row = index.row()
            evd_id = self._table.item(row, 0).text()
            file_path = self._table.item(row, 3).text()
            
            if not os.path.exists(file_path):
                db.update_evidence(evd_id, self._current_case_id, {"status": "Missing File"})
                failed += 1
                continue
                
            # Recompute hash
            current_sha256, _ = calculate_hashes(file_path)
            
            # Get original hash from DB
            items = db.get_evidence_for_case(self._current_case_id)
            original_sha256 = ""
            for item in items:
                if item.get("evidence_id") == evd_id:
                    original_sha256 = item.get("sha256", "")
                    break
                    
            if current_sha256 and current_sha256 == original_sha256:
                db.update_evidence(evd_id, self._current_case_id, {"status": "Verified"})
                verified += 1
            else:
                db.update_evidence(evd_id, self._current_case_id, {"status": "Integrity Failed"})
                failed += 1
                
        self._load_data()
        QMessageBox.information(
            self, "Verification Complete", 
            f"Verification finished.\n\nVerified (Match): {verified}\nFailed (Mismatch/Missing): {failed}"
        )

    def _on_remove_evidence(self):
        rows = self._table.selectionModel().selectedRows()
        if not rows:
            return
            
        reply = QMessageBox.question(
            self, "Confirm Removal",
            f"Are you sure you want to remove the {len(rows)} selected evidence item(s)?\n"
            "This only removes the record, not the actual file.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            db = get_db()
            for index in rows:
                evd_id = self._table.item(index.row(), 0).text()
                db.delete_evidence(evd_id, self._current_case_id)
            self._load_data()

    def _on_export_evidence(self):
        from ui.dialogs.export_dialog import ExportDialog
        dlg = ExportDialog("Evidence Package", self)
        if dlg.exec_():
            QMessageBox.information(self, "Export Evidence", "Evidence package exported successfully.")

    def _show_context_menu(self, pos):
        menu = QMenu(self)
        
        action_verify = menu.addAction("Verify Integrity")
        action_verify.triggered.connect(self._on_verify_evidence)
        
        menu.addSeparator()
        
        action_remove = menu.addAction("Remove from Case")
        action_remove.triggered.connect(self._on_remove_evidence)
        
        action_export = menu.addAction("Export")
        action_export.triggered.connect(self._on_export_evidence)
        
        menu.exec_(self._table.mapToGlobal(pos))
