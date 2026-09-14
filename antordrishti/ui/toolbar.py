"""
Antordrishti — Main Toolbar
Professional forensic desktop toolbar with clear action hierarchy.
"""

from PyQt5.QtWidgets import QToolBar, QAction, QWidget, QSizePolicy
from PyQt5.QtCore import Qt, pyqtSignal, QSize

from app.resources import get_icon, Icons
from app.theme import Sizes, Colors


class MainToolbar(QToolBar):
    """Main application toolbar with clear action hierarchy."""

    new_case_clicked = pyqtSignal()
    open_clicked = pyqtSignal()
    open_image_clicked = pyqtSignal()
    open_pdf_clicked = pyqtSignal()
    import_clicked = pyqtSignal()
    scan_clicked = pyqtSignal()
    camera_clicked = pyqtSignal()
    save_clicked = pyqtSignal()
    compare_clicked = pyqtSignal()
    report_clicked = pyqtSignal()
    analysis_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__("Main Toolbar", parent)
        self.setMovable(False)
        self.setIconSize(QSize(Sizes.TOOLBAR_ICON, Sizes.TOOLBAR_ICON))
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.setFixedHeight(Sizes.TOOLBAR_HEIGHT)
        self.setStyleSheet("""
            QToolBar {
                background-color: #FFFFFF;
                border-bottom: 1px solid #E2E8F0;
                padding: 2px 10px;
                spacing: 6px;
            }
            QToolButton {
                background: transparent;
                border: 1px solid transparent;
                border-radius: 4px;
                padding: 5px 10px;
                font-size: 11px;
                font-weight: 500;
                color: #334155;
            }
            QToolButton:hover {
                background-color: #F8FAFC;
                border: 1px solid #CBD5E1;
                color: #0F172A;
            }
            QToolButton:pressed {
                background-color: #F1F5F9;
            }
        """)

        self._build()

    def _build(self):
        actions = [
            ("New Case", Icons.NEW_CASE, self.new_case_clicked,
             "Create a new forensic case (Ctrl+N)", True),
            None,
            ("Open Image", Icons.IMAGE_FORENSICS, self.open_image_clicked,
             "Open image evidence: JPG, PNG, TIFF, BMP (Ctrl+I)", False),
            ("Open PDF", Icons.DOCUMENT, self.open_pdf_clicked,
             "Open PDF document (Ctrl+D)", False),
            ("Open Any", Icons.OPEN, self.open_clicked,
             "Open any supported document (Ctrl+O)", False),
            None,  # separator
            ("Save", Icons.SAVE, self.save_clicked,
             "Save processed evidence (Ctrl+S)", False),
            None,
            ("Scan", Icons.SCAN, self.scan_clicked,
             "Acquire document from scanner", False),
            None,
            ("Analysis", Icons.ANALYSIS, self.analysis_clicked,
             "Run forensic analysis (Ctrl+Shift+A)", True),
            ("Report", Icons.REPORT_GEN, self.report_clicked,
             "Generate forensic report (Ctrl+Shift+R)", True),
        ]

        for item in actions:
            if item is None:
                self.addSeparator()
            else:
                text, icon_name, signal, tooltip, is_primary = item
                icon_color = "#B08D3A" if is_primary else "#475569"
                action = QAction(get_icon(icon_name, icon_color, 18), text, self)
                action.setToolTip(tooltip)
                action.triggered.connect(lambda _, s=signal: s.emit())
                self.addAction(action)

        # Spacer
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.addWidget(spacer)
