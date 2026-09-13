"""
Antordrishti — Navigation Panel
Left forensic sidebar with structured module groupings,
clean typography, active gold indicators, and quick document actions.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QButtonGroup,
    QSizePolicy, QScrollArea, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QCursor

from app.theme import Colors, Fonts, Spacing, Sizes
from app.resources import get_icon, Icons
from app.constants import NavPage


class QuickAccessCard(QPushButton):
    """Compact hover card for quick document adding."""

    def __init__(self, title: str, subtitle: str, icon_name: str, parent=None):
        super().__init__(parent)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFixedHeight(46)
        self.setIcon(get_icon(icon_name, "#B08D3A"))
        self.setIconSize(QSize(18, 18))
        self.setText(f" {title}\n  {subtitle}")
        self.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 4px;
                text-align: left;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: 600;
                color: #0F172A;
            }
            QPushButton:hover {
                background-color: #FAF4E6;
                border: 1px solid #B08D3A;
                color: #785F23;
            }
            QPushButton:pressed {
                background-color: #F5EACB;
            }
        """)


class NavItem(QPushButton):
    """Single navigation item with icon, dark charcoal text, and gold indicator on selection."""

    def __init__(self, page_id: str, display_text: str, icon_name: str, parent=None):
        super().__init__(parent)
        self.page_id = page_id
        self.display_text = display_text
        self.icon_name = icon_name

        self.setText(display_text)
        self.setIcon(get_icon(icon_name, "#475569"))
        self.setIconSize(QSize(16, 16))
        self.setCheckable(True)
        self.setFixedHeight(36)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setStyleSheet(self._make_style())
        self.toggled.connect(self._on_toggled)

    def _on_toggled(self, checked: bool):
        color = "#B08D3A" if checked else "#475569"
        self.setIcon(get_icon(self.icon_name, color))

    def _make_style(self):
        return """
            QPushButton {
                background: transparent;
                border: none;
                border-left: 3px solid transparent;
                text-align: left;
                padding: 0 12px 0 12px;
                font-size: 12px;
                font-weight: 500;
                color: #334155;
            }
            QPushButton:hover {
                background-color: #F1F5F9;
                color: #0F172A;
            }
            QPushButton:checked {
                background-color: #FAF4E6;
                border-left: 3px solid #B08D3A;
                color: #0F172A;
                font-weight: 600;
            }
        """


class NavigationPanel(QWidget):
    """Left navigation sidebar organized into logical forensic groups."""

    page_selected = pyqtSignal(str)  # Emits NavPage.value
    add_image_clicked = pyqtSignal()
    add_pdf_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(230)
        self.setStyleSheet("""
            NavigationPanel {
                background-color: #FFFFFF;
                border-right: 1px solid #E2E8F0;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── App Branding Header ───────────────────────────────
        brand = QWidget()
        brand.setFixedHeight(68)
        brand.setStyleSheet("""
            background-color: #FFFFFF;
            border-bottom: 1px solid #F1F5F9;
        """)
        brand_layout = QVBoxLayout(brand)
        brand_layout.setContentsMargins(16, 12, 16, 8)
        brand_layout.setSpacing(2)

        app_title = QLabel("অন্তর্দৃষ্টি | ANTORDRISHTI")
        app_title.setStyleSheet("""
            font-size: 13px;
            font-weight: 800;
            color: #0F172A;
            letter-spacing: 0.8px;
        """)
        brand_layout.addWidget(app_title)

        app_sub = QLabel("Document Forensic & Authenticity Suite")
        app_sub.setStyleSheet("""
            font-size: 9px;
            color: #64748B;
            font-weight: 500;
            letter-spacing: 0.4px;
        """)
        brand_layout.addWidget(app_sub)

        layout.addWidget(brand)

        # ── Quick Add Document Section ────────────────────────
        quick_sec = QWidget()
        quick_sec.setStyleSheet("""
            background-color: #FFFFFF;
            border-bottom: 1px solid #F1F5F9;
        """)
        quick_layout = QVBoxLayout(quick_sec)
        quick_layout.setContentsMargins(12, 8, 12, 8)
        quick_layout.setSpacing(6)

        sec_title = QLabel("ADD EVIDENCE")
        sec_title.setStyleSheet("""
            font-size: 9px;
            font-weight: 700;
            color: #94A3B8;
            letter-spacing: 0.8px;
        """)
        quick_layout.addWidget(sec_title)

        btn_img = QuickAccessCard("Open Image", "JPG, PNG, TIFF, BMP", Icons.IMAGE_FORENSICS)
        btn_img.clicked.connect(self.add_image_clicked.emit)
        quick_layout.addWidget(btn_img)

        btn_pdf = QuickAccessCard("Open PDF", "Multi-page Scanned / Vector", Icons.DOCUMENT)
        btn_pdf.clicked.connect(self.add_pdf_clicked.emit)
        quick_layout.addWidget(btn_pdf)

        layout.addWidget(quick_sec)

        # ── Grouped Navigation Items ──────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background-color: #FFFFFF;")

        container = QWidget()
        container.setStyleSheet("background-color: #FFFFFF;")
        self._nav_layout = QVBoxLayout(container)
        self._nav_layout.setContentsMargins(0, 6, 0, 10)
        self._nav_layout.setSpacing(1)

        self._button_group = QButtonGroup(self)
        self._button_group.setExclusive(True)

        groups = [
            ("CASE", [
                (NavPage.DASHBOARD, "Dashboard", Icons.DASHBOARD),
                (NavPage.EVIDENCE_MANAGER, "Evidence Manager", Icons.EVIDENCE),
            ]),
            ("EXAMINATION", [
                (NavPage.DOCUMENT_ANALYSIS, "Document Analysis", Icons.DOCUMENT),
                (NavPage.IMAGE_FORENSICS, "Image Forensics", Icons.IMAGE_FORENSICS),
                (NavPage.DOCUMENT_FORENSICS, "Document Forensics", Icons.DOC_FORENSICS),
                (NavPage.ELA, "Error Level Analysis", Icons.ELA),
                (NavPage.METADATA, "Metadata", Icons.METADATA),
                (NavPage.OCR, "OCR & Text Extraction", Icons.OCR),
                (NavPage.WATERMARK, "Watermark Detection", Icons.WATERMARK),
                (NavPage.FORGERY_DETECTION, "Forgery Detection", Icons.FORGERY),
                (NavPage.HISTOGRAM, "Histogram Analysis", Icons.ANALYSIS),
            ]),
            ("OUTPUT", [
                (NavPage.EVIDENCE_FUSION, "Evidence Fusion", Icons.ANALYSIS),
                (NavPage.REPORT_GENERATOR, "Report Generator", Icons.REPORT),
                (NavPage.BATCH_PROCESSING, "Batch Processing", Icons.BATCH),
            ]),
            ("SYSTEM", [
                (NavPage.SETTINGS, "Settings", Icons.SETTINGS),
            ]),
        ]

        self._buttons = {}
        btn_id = 0

        for grp_idx, (group_name, items) in enumerate(groups):
            if grp_idx > 0:
                sep = QFrame()
                sep.setFrameShape(QFrame.Shape.HLine)
                sep.setStyleSheet("background-color: #F1F5F9; max-height: 1px; margin: 6px 12px; border: none;")
                self._nav_layout.addWidget(sep)

            lbl = QLabel(group_name)
            lbl.setStyleSheet("""
                font-size: 9px;
                font-weight: 700;
                color: #94A3B8;
                letter-spacing: 0.8px;
                padding: 6px 14px 2px 14px;
            """)
            self._nav_layout.addWidget(lbl)

            for page_enum, display_text, icon_name in items:
                btn = NavItem(page_enum.value, display_text, icon_name)
                self._button_group.addButton(btn, btn_id)
                self._nav_layout.addWidget(btn)
                self._buttons[page_enum.value] = btn
                btn_id += 1

        self._nav_layout.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll)

        # Connect
        self._button_group.buttonClicked.connect(self._on_click)

        # Default selection
        if NavPage.DASHBOARD.value in self._buttons:
            self._buttons[NavPage.DASHBOARD.value].setChecked(True)

    def _on_click(self, button):
        if hasattr(button, "page_id"):
            self.page_selected.emit(button.page_id)
        else:
            self.page_selected.emit(button.text())

    def select_page(self, page_name: str):
        """Programmatically select a page."""
        btn = self._buttons.get(page_name)
        if btn and not btn.isChecked():
            btn.setChecked(True)
