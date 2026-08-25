"""
Antordrishti — Main Toolbar
Professional toolbar with key actions including dedicated Add Image & Add PDF buttons.
"""

from PyQt5.QtWidgets import QToolBar, QAction, QWidget, QSizePolicy
from PyQt5.QtCore import Qt, pyqtSignal, QSize

from app.resources import get_icon, Icons
from app.theme import Sizes


class MainToolbar(QToolBar):
    """Main application toolbar with quick document access."""

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

        self._build()

    def _build(self):
        actions = [
            ("New Case", Icons.NEW_CASE, self.new_case_clicked,
             "Create a new forensic case (Ctrl+N)"),
            None,
            ("Open Image", Icons.IMAGE_FORENSICS, self.open_image_clicked,
             "Open image evidence: JPG, PNG, TIFF, BMP (Ctrl+I)"),
            ("Open PDF", Icons.DOCUMENT, self.open_pdf_clicked,
             "Open PDF document (Ctrl+D)"),
            ("Open Any", Icons.OPEN, self.open_clicked,
             "Open any supported document (Ctrl+O)"),
            None,  # separator
            ("Save", Icons.SAVE, self.save_clicked,
             "Save processed evidence (Ctrl+S)"),
            None,
            ("Analysis", Icons.ANALYSIS, self.analysis_clicked,
             "Run forensic analysis (Ctrl+Shift+A)"),
            ("Report", Icons.REPORT_GEN, self.report_clicked,
             "Generate forensic report (Ctrl+Shift+R)"),
        ]

        for item in actions:
            if item is None:
                self.addSeparator()
            else:
                text, icon_name, signal, tooltip = item
                action = QAction(get_icon(icon_name, "#0D7C7C" if "Open" in text else "#334155"), text, self)
                action.setToolTip(tooltip)
                action.triggered.connect(lambda _, s=signal: s.emit())
                self.addAction(action)

        # Spacer
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.addWidget(spacer)
