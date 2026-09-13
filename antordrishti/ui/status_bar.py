"""
Antordrishti — Status Bar
Bottom status bar with case, evidence, document, status, page, zoom, integrity info.
"""

from PyQt5.QtWidgets import QStatusBar, QLabel, QWidget, QHBoxLayout
from PyQt5.QtCore import Qt

from app.theme import Colors, Fonts, Spacing
from app.constants import AppStatus


class ForensicStatusBar(QStatusBar):
    """Professional forensic status bar with clean light aesthetic."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizeGripEnabled(True)
        self.setStyleSheet("""
            QStatusBar {
                background-color: #F8FAFC;
                border-top: 1px solid #E2E8F0;
                min-height: 28px;
            }
        """)

        # Case info
        self._case_label = self._make_label("Case: —")
        self.addWidget(self._case_label)
        self.addWidget(self._make_separator())

        # Evidence info
        self._evidence_label = self._make_label("Evidence: —")
        self.addWidget(self._evidence_label)
        self.addWidget(self._make_separator())

        # Document info
        self._doc_label = self._make_label("Document: —")
        self.addWidget(self._doc_label)
        self.addWidget(self._make_separator())

        # Status
        self._status_dot = QLabel("●")
        self._status_dot.setStyleSheet(f"color: {Colors.SUCCESS}; font-size: 10px;")
        self._status_label = self._make_label("Ready")
        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(4)
        status_layout.addWidget(self._status_dot)
        status_layout.addWidget(self._status_label)
        self.addWidget(status_widget)

        # Right side — permanent widgets
        self._page_label = self._make_label("Page: — / —")
        self.addPermanentWidget(self._page_label)
        self.addPermanentWidget(self._make_separator())

        self._zoom_label = self._make_label("Zoom: 100%")
        self.addPermanentWidget(self._zoom_label)
        self.addPermanentWidget(self._make_separator())

        self._integrity_label = self._make_label("Integrity: —")
        self.addPermanentWidget(self._integrity_label)

    def set_case(self, case_id: str):
        self._case_label.setText(f"Case: {case_id}" if case_id else "Case: —")

    def set_evidence(self, evidence_id: str):
        self._evidence_label.setText(f"Evidence: {evidence_id}" if evidence_id else "Evidence: —")

    def set_document(self, doc_name: str):
        self._doc_label.setText(
            f"Document: {doc_name}" if doc_name else "Document: —"
        )

    def set_status(self, status: AppStatus):
        self._status_label.setText(status.value)
        color_map = {
            AppStatus.READY: Colors.SUCCESS,
            AppStatus.LOADING: Colors.ACCENT,
            AppStatus.DOCUMENT_LOADED: Colors.SUCCESS,
            AppStatus.PROCESSING: Colors.ACCENT,
            AppStatus.ANALYSIS_PENDING: Colors.WARNING,
            AppStatus.ANALYSIS_COMPLETE: Colors.SUCCESS,
            AppStatus.WARNING: Colors.WARNING,
            AppStatus.ERROR: Colors.ERROR,
        }
        color = color_map.get(status, Colors.TEXT_TERTIARY)
        self._status_dot.setStyleSheet(f"color: {color}; font-size: 10px;")

    def set_page(self, current: int, total: int):
        self._page_label.setText(f"Page: {current} / {total}")

    def set_zoom(self, zoom_percent: int):
        self._zoom_label.setText(f"Zoom: {zoom_percent}%")

    def set_integrity(self, status: str):
        self._integrity_label.setText(f"Integrity: {status}")
        color = {
            "Verified": Colors.SUCCESS,
            "Pending": Colors.TEXT_TERTIARY,
            "Not Verified": Colors.WARNING,
            "Invalid": Colors.ERROR,
        }.get(status, Colors.TEXT_TERTIARY)
        self._integrity_label.setStyleSheet(
            f"font-size: 11px; color: {color}; font-weight: 600; padding: 0px 4px;"
        )

    def _make_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setStyleSheet("font-size: 11px; color: #475569; font-weight: 500;")
        return label

    def _make_separator(self) -> QLabel:
        sep = QLabel("|")
        sep.setStyleSheet("color: #CBD5E1; font-size: 11px; padding: 0 4px;")
        return sep
