"""
Antordrishti Application Setup
QApplication subclass with theme loading, font configuration, and DPI awareness.
"""

import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QCoreApplication
from PyQt5.QtGui import QFont

from app.theme import Fonts
from app.resources import load_stylesheet


class AntordrishtiApp(QApplication):
    """Main application class with theme and DPI configuration."""

    def __init__(self, argv):
        # High-DPI must be set before QApplication init
        if hasattr(Qt.ApplicationAttribute, "AA_EnableHighDpiScaling"):
            QCoreApplication.setAttribute(
                Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True
            )
        if hasattr(Qt.ApplicationAttribute, "AA_UseHighDpiPixmaps"):
            QCoreApplication.setAttribute(
                Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True
            )

        super().__init__(argv)

        self.setApplicationName("Antordrishti")
        self.setApplicationVersion("1.0.0")
        self.setOrganizationName("Antordrishti")

        self._setup_font()
        self._setup_stylesheet()

    def _setup_font(self):
        """Configure the application font."""
        font = QFont(Fonts.FAMILY, Fonts.SIZE_BODY)
        font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
        self.setFont(font)

    def _setup_stylesheet(self):
        """Load and apply the QSS stylesheet."""
        qss = load_stylesheet()
        if qss:
            self.setStyleSheet(qss)
