"""
Antordrishti — About Dialog
"""

import sys
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
)
from PyQt5.QtCore import Qt
from PyQt5.Qt import PYQT_VERSION_STR

from app.theme import Colors, Spacing
from app.constants import APP_NAME, APP_VERSION, APP_BUILD, APP_DESCRIPTION
from ui.widgets.common import ActionButton, Separator, InfoRow


class AboutDialog(QDialog):
    """About Antordrishti dialog."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About Antordrishti")
        self.setFixedSize(420, 380)
        self.setStyleSheet(f"background-color: {Colors.PANEL};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.XXL, Spacing.XL,
                                  Spacing.XXL, Spacing.XL)
        layout.setSpacing(Spacing.MD)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # App name
        name = QLabel(f"\u0985\u09a8\u09cd\u09a4\u09b0\u09cd\u09a6\u09c3\u09b7\u09cd\u099f\u09bf | {APP_NAME}")
        name.setStyleSheet(
            f"font-size: 20px; font-weight: 700; color: {Colors.ACCENT};"
            f" letter-spacing: 1.5px;"
        )
        name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(name)

        # Subtitle
        sub = QLabel("Document Forensic & Authenticity Analysis Suite")
        sub.setStyleSheet(f"font-size: 12px; color: {Colors.TEXT_SECONDARY};")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(sub)

        layout.addWidget(Separator())

        # Version info
        layout.addWidget(InfoRow("Version", APP_VERSION))
        layout.addWidget(InfoRow("Build", APP_BUILD))
        layout.addWidget(InfoRow("Python", sys.version.split()[0]))
        layout.addWidget(InfoRow("PyQt5", PYQT_VERSION_STR))

        layout.addWidget(Separator())

        # Description
        desc = QLabel(APP_DESCRIPTION)
        desc.setWordWrap(True)
        desc.setStyleSheet(f"font-size: 11px; color: {Colors.TEXT_SECONDARY};")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc)

        layout.addStretch()

        # Close
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = ActionButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
