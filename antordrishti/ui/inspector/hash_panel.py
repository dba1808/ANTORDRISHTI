"""
Antordrishti — Hash Verification Inspector Section
Selectable cryptographic hashes with Calculate, Verify, and Copy capabilities.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QLabel, QApplication
)
from PyQt5.QtCore import pyqtSignal, Qt

from app.theme import Colors, Spacing
from ui.widgets.common import (
    CollapsibleSection, StatusIndicator, ActionButton, SectionLabel
)


class HashPanel(QWidget):
    """Hash verification panel with SHA-256, MD5, selectable text fields, and status."""

    calculate_requested = pyqtSignal()
    verify_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: #FFFFFF;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._section = CollapsibleSection("INTEGRITY & HASHES")

        # SHA-256 Row
        self._section.add_widget(SectionLabel("SHA-256 Hash"))
        sha_layout = QHBoxLayout()
        sha_layout.setSpacing(4)
        self.sha256_edit = QLineEdit("—")
        self.sha256_edit.setReadOnly(True)
        self.sha256_edit.setStyleSheet("""
            QLineEdit {
                background-color: #F8FAFC;
                border: 1px solid #CBD5E1;
                border-radius: 3px;
                font-family: 'Consolas', monospace;
                font-size: 10px;
                color: #0D7C7C;
                font-weight: 600;
                padding: 3px;
            }
        """)
        btn_copy_sha = QPushButton("Copy")
        btn_copy_sha.setFixedHeight(22)
        btn_copy_sha.setStyleSheet("font-size: 10px; padding: 2px 6px;")
        btn_copy_sha.clicked.connect(self._copy_sha256)
        sha_layout.addWidget(self.sha256_edit, 1)
        sha_layout.addWidget(btn_copy_sha)
        self._section.add_layout(sha_layout)

        # MD5 Row
        self._section.add_widget(SectionLabel("MD5 Hash"))
        md5_layout = QHBoxLayout()
        md5_layout.setSpacing(4)
        self.md5_edit = QLineEdit("—")
        self.md5_edit.setReadOnly(True)
        self.md5_edit.setStyleSheet(self.sha256_edit.styleSheet())
        btn_copy_md5 = QPushButton("Copy")
        btn_copy_md5.setFixedHeight(22)
        btn_copy_md5.setStyleSheet("font-size: 10px; padding: 2px 6px;")
        btn_copy_md5.clicked.connect(self._copy_md5)
        md5_layout.addWidget(self.md5_edit, 1)
        md5_layout.addWidget(btn_copy_md5)
        self._section.add_layout(md5_layout)

        # Status
        self._status = StatusIndicator("Pending Calculation", "pending")
        self._section.add_widget(self._status)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(6)
        calc_btn = ActionButton("Calculate", primary=True)
        calc_btn.clicked.connect(self.calculate_requested.emit)
        btn_layout.addWidget(calc_btn)

        verify_btn = ActionButton("Verify Integrity")
        verify_btn.clicked.connect(self.verify_requested.emit)
        btn_layout.addWidget(verify_btn)
        self._section.add_layout(btn_layout)

        layout.addWidget(self._section)

    def update_hashes(self, sha256: str, md5: str, status: str = "Pending"):
        self.sha256_edit.setText(sha256 or "—")
        self.md5_edit.setText(md5 or "—")

        status_map = {
            "Verified": ("Original Integrity Verified", "verified"),
            "Pending": ("Pending Calculation", "pending"),
            "Error": ("Calculation Error", "error")
        }
        text, st = status_map.get(status, (status, "pending"))
        self._status.set_text(text)
        self._status.set_status(st)

    def _copy_sha256(self):
        text = self.sha256_edit.text()
        if text and text != "—":
            QApplication.clipboard().setText(text)

    def _copy_md5(self):
        text = self.md5_edit.text()
        if text and text != "—":
            QApplication.clipboard().setText(text)
