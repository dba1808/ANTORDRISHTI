"""
Antordrishti — Metadata Sanitization Page
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QScrollArea, QMessageBox
)
from PyQt5.QtCore import Qt

from app.theme import Colors, Spacing
from ui.widgets.common import (
    SectionLabel, ActionButton, EngineNotConnectedWidget, Separator
)


class _MetadataTable(QTableWidget):
    """Metadata key-value table."""

    def __init__(self, headers=None, parent=None):
        super().__init__(parent)
        if headers is None:
            headers = ["Property", "Value"]
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.verticalHeader().setVisible(False)
        self.setAlternatingRowColors(True)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.setSelectionBehavior(QTableWidget.SelectRows)


class MetadataPage(QWidget):
    """Metadata sanitization page."""

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
        title = QLabel("Metadata Sanitization")
        title.setProperty("heading", True)
        tb_layout.addWidget(title)
        tb_layout.addStretch()
        layout.addWidget(title_bar)

        # Content
        content = QHBoxLayout()
        content.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        content.setSpacing(Spacing.MD)

        # Left: Metadata tabs
        self._tabs = QTabWidget()
        self._tables = {}

        for tab_name in ["EXIF", "XMP", "IPTC", "PDF Metadata", "Software Info"]:
            table = _MetadataTable()
            # Placeholder rows
            placeholder_data = [
                ("Status", "No document loaded"),
            ]
            table.setRowCount(len(placeholder_data))
            for row, (key, val) in enumerate(placeholder_data):
                table.setItem(row, 0, QTableWidgetItem(key))
                table.setItem(row, 1, QTableWidgetItem(val))
            self._tables[tab_name] = table
            self._tabs.addTab(table, tab_name)

        content.addWidget(self._tabs, 1)

        # Right: Actions
        actions_panel = QFrame()
        actions_panel.setFixedWidth(220)
        actions_panel.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.PANEL};
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
            }}
        """)
        act_layout = QVBoxLayout(actions_panel)
        act_layout.setContentsMargins(Spacing.MD, Spacing.MD,
                                      Spacing.MD, Spacing.MD)
        act_layout.setSpacing(Spacing.SM)

        act_layout.addWidget(SectionLabel("Actions"))
        
        self._btn_view = ActionButton("View Metadata", primary=True)
        self._btn_detect = ActionButton("Detect Anomalies")
        self._btn_sanitize = ActionButton("Sanitize Metadata")
        self._btn_export = ActionButton("Export Metadata Report")
        
        act_layout.addWidget(self._btn_view)
        act_layout.addWidget(self._btn_detect)
        act_layout.addWidget(self._btn_sanitize)
        act_layout.addWidget(self._btn_export)
        
        self._btn_detect.clicked.connect(self._on_detect_anomalies)
        self._btn_sanitize.clicked.connect(self._on_sanitize)
        act_layout.addWidget(Separator())

        # Warning
        warn = QLabel(
            "⚠ Sanitization creates a new output file. "
            "Original evidence remains unchanged."
        )
        warn.setWordWrap(True)
        warn.setStyleSheet(f"""
            font-size: 10px; color: {Colors.WARNING};
            padding: 8px;
            background-color: {Colors.WARNING_LIGHT};
            border: 1px solid {Colors.WARNING};
            border-radius: 4px;
        """)
        act_layout.addWidget(warn)

        act_layout.addStretch()
        content.addWidget(actions_panel)

        layout.addLayout(content, 1)

    def set_current_context(self, context):
        """Update metadata view from the shared active document context."""
        if context and context.document:
            self.load_document(context.document.file_path)
        else:
            self._set_table("EXIF", [("Status", "No document loaded")])
            self._set_table("PDF Metadata", [("Status", "No document loaded")])
            self._set_table("Software Info", [("Status", "No document loaded")])

    def load_document(self, file_path: str):
        """Load metadata from the already-open active document."""
        from services.document_service import load_document

        doc = load_document(file_path)
        if not doc:
            self._set_table("EXIF", [("Status", "Metadata unavailable")])
            return

        basic_rows = [
            ("Filename", doc.file_name),
            ("File Type", doc.file_type),
            ("File Size", f"{doc.file_size} bytes"),
            ("Resolution", doc.resolution or "Not Available"),
            ("Color Space", doc.color_space or "Not Available"),
            ("Pages", str(doc.page_count)),
            ("Last Modified", doc.last_modified or "Not Available"),
            ("SHA-256", doc.sha256 or "Not Available"),
            ("Integrity", doc.integrity_status),
        ]
        self._set_table("EXIF", basic_rows + sorted(doc.raw_metadata.items())[:80])
        self._set_table("PDF Metadata", [
            ("PDF Version", doc.pdf_version or "Not Available"),
            ("Author", doc.author),
            ("Creator", doc.creator),
            ("Producer", doc.producer),
            ("Creation Date", doc.creation_date),
            ("Objects", str(doc.pdf_objects)),
            ("Linearized", "Yes" if doc.pdf_linearized else "No"),
        ])
        self._set_table("Software Info", [
            ("Camera Make", doc.camera_make),
            ("Camera Model", doc.camera_model),
            ("Software", doc.software),
            ("Creator", doc.creator),
            ("Producer", doc.producer),
        ])

    def _set_table(self, tab_name: str, rows):
        table = self._tables.get(tab_name)
        if not table:
            return
        table.setRowCount(len(rows))
        for row, (key, val) in enumerate(rows):
            table.setItem(row, 0, QTableWidgetItem(str(key)))
            table.setItem(row, 1, QTableWidgetItem(str(val)))

    def _on_detect_anomalies(self):
        from services.app_state import get_app_state
        ctx = get_app_state().context
        if not ctx or not ctx.document:
            QMessageBox.warning(self, "No Document", "Please load a document first.")
            return
            
        from services.metadata_service import detect_anomalies
        anomalies = detect_anomalies(ctx.document)
        if anomalies:
            msg = "Anomalies Found:\\n\\n"
            for a in anomalies:
                msg += f"[{a['severity']}] {a['finding']}\\n"
            QMessageBox.information(self, "Anomaly Detection", msg)
        else:
            QMessageBox.information(self, "Anomaly Detection", "No obvious metadata anomalies detected.")

    def _on_sanitize(self):
        from services.app_state import get_app_state
        ctx = get_app_state().context
        if not ctx or not ctx.document:
            QMessageBox.warning(self, "No Document", "Please load a document first.")
            return
            
        from PyQt5.QtWidgets import QFileDialog
        out_path, _ = QFileDialog.getSaveFileName(self, "Save Sanitized File", "", "All Files (*.*)")
        if out_path:
            from services.metadata_service import sanitize_metadata
            success = sanitize_metadata(ctx.document.file_path, out_path)
            if success:
                QMessageBox.information(self, "Success", f"Metadata stripped and file saved to {out_path}")
                from services.db_service import get_db
                if ctx.evidence:
                    get_db().add_processing_history(ctx.evidence.evidence_id, "Metadata Sanitization", f"Saved to {out_path}")
            else:
                QMessageBox.warning(self, "Error", "Failed to sanitize metadata.")

