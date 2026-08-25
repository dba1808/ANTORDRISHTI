"""
Antordrishti — Document Info Dialog
Displays document properties and metadata.
"""

from typing import Optional

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt

from app.theme import Colors, Spacing
from models.document_model import DocumentModel
from services.file_service import format_file_size
from ui.widgets.common import ActionButton, SectionLabel, InfoRow, Separator


class DocumentInfoDialog(QDialog):
    """Displays properties for the active document."""

    def __init__(self, doc: Optional[DocumentModel] = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Document Properties — Antordrishti")
        self.setMinimumSize(480, 440)
        self.setStyleSheet(f"background-color: {Colors.PANEL};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.XXL, Spacing.XL, Spacing.XXL, Spacing.XL)
        layout.setSpacing(Spacing.MD)

        title = QLabel("Document Properties")
        title.setStyleSheet(
            f"font-size: 16px; font-weight: 600; color: {Colors.TEXT_PRIMARY};"
        )
        layout.addWidget(title)
        layout.addWidget(Separator())

        if doc:
            layout.addWidget(InfoRow("File Name", doc.file_name or "—"))
            layout.addWidget(InfoRow("File Path", doc.file_path or "—"))
            layout.addWidget(InfoRow("File Type", doc.file_type or "—"))
            layout.addWidget(InfoRow("File Size", format_file_size(doc.file_size) if doc.file_size else "—"))
            layout.addWidget(InfoRow("MIME Type", doc.mime_type or "—"))
            layout.addWidget(InfoRow("Resolution", doc.resolution or "—"))
            layout.addWidget(InfoRow("Color Space", doc.color_space or "—"))
            layout.addWidget(InfoRow("Pages", str(doc.page_count)))
            layout.addWidget(InfoRow("Last Modified", doc.last_modified or "—"))
            layout.addWidget(Separator())
            layout.addWidget(SectionLabel("Cryptographic Hashes"))
            sha_row = InfoRow("SHA-256", doc.sha256 or "Not calculated")
            sha_row.set_mono()
            layout.addWidget(sha_row)
            md5_row = InfoRow("MD5", doc.md5 or "Not calculated")
            md5_row.set_mono()
            layout.addWidget(md5_row)
        else:
            no_doc = QLabel("No document is currently loaded.")
            no_doc.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_doc.setStyleSheet(f"font-size: 12px; color: {Colors.TEXT_TERTIARY};")
            layout.addWidget(no_doc)

        layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = ActionButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
