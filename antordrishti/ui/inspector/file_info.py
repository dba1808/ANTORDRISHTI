"""
Antordrishti — File Info & Metadata Inspector Section
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout
from ui.widgets.common import CollapsibleSection, InfoRow, SectionLabel, Separator


class FileInfoPanel(QWidget):
    """Displays comprehensive file information and extracted forensic metadata."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._section = CollapsibleSection("DOCUMENT INFORMATION")

        self._rows = {}
        fields = [
            "File Name", "File Type", "File Size", "Dimensions",
            "Color Space", "Pages", "PDF Version", "Evidence Type"
        ]
        for field in fields:
            row = InfoRow(field)
            self._rows[field] = row
            self._section.add_widget(row)

        self._section.add_widget(Separator())
        self._section.add_widget(SectionLabel("Forensic Metadata"))

        meta_fields = [
            "Author", "Software", "Creation Date", "Camera Device"
        ]
        for field in meta_fields:
            row = InfoRow(field)
            self._rows[field] = row
            self._section.add_widget(row)

        layout.addWidget(self._section)

    def update_info(self, doc):
        """Update from DocumentModel."""
        from services.file_service import format_file_size
        self._rows["File Name"].set_value(doc.file_name or "—")
        self._rows["File Type"].set_value(doc.file_type or "—")
        self._rows["File Size"].set_value(
            format_file_size(doc.file_size) if doc.file_size else "—"
        )
        self._rows["Dimensions"].set_value(doc.resolution or "—")
        self._rows["Color Space"].set_value(doc.color_space or "—")
        self._rows["Pages"].set_value(str(doc.page_count))
        self._rows["PDF Version"].set_value(doc.pdf_version or ("N/A (Image)" if doc.file_type != "PDF" else "—"))
        self._rows["Evidence Type"].set_value(doc.evidence_type or "Original Evidence")

        # Metadata
        self._rows["Author"].set_value(doc.author or "Not Available")
        self._rows["Software"].set_value(doc.software or "Not Available")
        self._rows["Creation Date"].set_value(doc.creation_date or doc.last_modified or "Not Available")

        camera_str = "Not Available"
        if doc.camera_make != "Not Available" or doc.camera_model != "Not Available":
            camera_str = f"{doc.camera_make} {doc.camera_model}".strip()
        self._rows["Camera Device"].set_value(camera_str)

    def clear(self):
        for row in self._rows.values():
            row.set_value("—")
