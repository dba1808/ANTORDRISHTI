"""
Antordrishti — Navigation Panel
Left sidebar with pure white styling, high-contrast dark text,
app branding, quick document access cards, and 14 navigation items.
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
        self.setFixedHeight(48)
        self.setIcon(get_icon(icon_name, "#0D7C7C"))
        self.setIconSize(QSize(20, 20))
        self.setText(f" {title}\n  {subtitle}")
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: #F8FAFC;
                border: 1px solid #E2E8F0;
                border-radius: 6px;
                text-align: left;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: 600;
                color: #0F172A;
            }}
            QPushButton:hover {{
                background-color: #F0FDFA;
                border: 1px solid #0D9488;
                color: #0D7C7C;
            }}
            QPushButton:pressed {{
                background-color: #CCFBF1;
            }}
        """)


class NavItem(QPushButton):
    """Single navigation item with icon, dark black text, and teal indicator on selection."""

    def __init__(self, text: str, icon_name: str, parent=None):
        super().__init__(parent)
        self.setText(text)
        # High contrast icon
        self.setIcon(get_icon(icon_name, "#334155"))
        self.setIconSize(QSize(18, 18))
        self.setCheckable(True)
        self.setFixedHeight(36)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setStyleSheet(self._make_style())

    def _make_style(self):
        return f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-left: 3px solid transparent;
                text-align: left;
                padding: 0 12px 0 12px;
                font-size: 12px;
                font-weight: 500;
                color: #0F172A;
            }}
            QPushButton:hover {{
                background-color: #F1F5F9;
                color: #000000;
                font-weight: 600;
            }}
            QPushButton:checked {{
                background-color: #E6F4F8;
                border-left: 3px solid #0D7C7C;
                color: #0D7C7C;
                font-weight: 600;
            }}
        """


class NavigationPanel(QWidget):
    """Left navigation sidebar with pure white styling and quick document access."""

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
        brand.setFixedHeight(72)
        brand.setStyleSheet("""
            background-color: #FFFFFF;
            border-bottom: 1px solid #F1F5F9;
        """)
        brand_layout = QVBoxLayout(brand)
        brand_layout.setContentsMargins(16, 8, 16, 6)
        brand_layout.setSpacing(1)

        app_bengali = QLabel("অন্তর্দৃষ্টি | ANTORDRISHTI")
        app_bengali.setStyleSheet("""
            font-size: 13px;
            font-weight: 800;
            color: #0D7C7C;
            letter-spacing: 1.2px;
        """)
        brand_layout.addWidget(app_bengali)

        app_sub = QLabel("Document Forensic & Authenticity Analysis Suite")
        app_sub.setStyleSheet("""
            font-size: 8px;
            color: #475569;
            font-weight: 600;
            letter-spacing: 0.8px;
        """)
        app_sub.setWordWrap(True)
        brand_layout.addWidget(app_sub)

        layout.addWidget(brand)

        # ── Quick Add Document Section ────────────────────────
        quick_sec = QWidget()
        quick_sec.setStyleSheet("""
            background-color: #FFFFFF;
            border-bottom: 1px solid #F1F5F9;
        """)
        quick_layout = QVBoxLayout(quick_sec)
        quick_layout.setContentsMargins(12, 10, 12, 10)
        quick_layout.setSpacing(6)

        sec_title = QLabel("ADD DOCUMENTS")
        sec_title.setStyleSheet("""
            font-size: 9px;
            font-weight: 700;
            color: #64748B;
            letter-spacing: 0.8px;
        """)
        quick_layout.addWidget(sec_title)

        # Dual Hover Boxes: Image & PDF
        btn_img = QuickAccessCard("Open Image", "JPG, PNG, TIFF, BMP", Icons.IMAGE_FORENSICS)
        btn_img.clicked.connect(self.add_image_clicked.emit)
        quick_layout.addWidget(btn_img)

        btn_pdf = QuickAccessCard("Open PDF Document", "Multi-page Vector / Scanned", Icons.DOCUMENT)
        btn_pdf.clicked.connect(self.add_pdf_clicked.emit)
        quick_layout.addWidget(btn_pdf)

        layout.addWidget(quick_sec)

        # ── Navigation Items List ─────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background-color: #FFFFFF;")

        container = QWidget()
        container.setStyleSheet("background-color: #FFFFFF;")
        self._nav_layout = QVBoxLayout(container)
        self._nav_layout.setContentsMargins(0, 6, 0, 6)
        self._nav_layout.setSpacing(1)

        self._button_group = QButtonGroup(self)
        self._button_group.setExclusive(True)

        nav_items = [
            (NavPage.DASHBOARD, Icons.DASHBOARD),
            None,
            (NavPage.DOCUMENT_ANALYSIS, Icons.DOCUMENT),
            (NavPage.IMAGE_FORENSICS, Icons.IMAGE_FORENSICS),
            (NavPage.DOCUMENT_FORENSICS, Icons.DOC_FORENSICS),
            (NavPage.ELA, Icons.ELA),
            (NavPage.METADATA, Icons.METADATA),
            (NavPage.OCR, Icons.OCR),
            (NavPage.WATERMARK, Icons.WATERMARK),
            (NavPage.FORGERY_DETECTION, Icons.FORGERY),
            None,
            (NavPage.EVIDENCE_MANAGER, Icons.EVIDENCE),
            (NavPage.EVIDENCE_FUSION, Icons.ANALYSIS),
            (NavPage.REPORT_GENERATOR, Icons.REPORT),
            (NavPage.BATCH_PROCESSING, Icons.BATCH),
            None,
            (NavPage.SETTINGS, Icons.SETTINGS),
        ]

        self._buttons = {}
        btn_id = 0
        for item in nav_items:
            if item is None:
                sep = QFrame()
                sep.setFrameShape(QFrame.Shape.HLine)
                sep.setStyleSheet(
                    "background-color: #E2E8F0; "
                    "max-height: 1px; margin: 4px 12px;"
                )
                self._nav_layout.addWidget(sep)
            else:
                page, icon = item
                btn = NavItem(page.value, icon)
                self._button_group.addButton(btn, btn_id)
                self._nav_layout.addWidget(btn)
                self._buttons[page.value] = btn
                btn_id += 1

        self._nav_layout.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll)

        # Connect
        self._button_group.buttonClicked.connect(self._on_click)

        # Default selection
        self._buttons[NavPage.DASHBOARD.value].setChecked(True)

    def _on_click(self, button):
        self.page_selected.emit(button.text())

    def select_page(self, page_name: str):
        """Programmatically select a page."""
        btn = self._buttons.get(page_name)
        if btn and not btn.isChecked():
            btn.setChecked(True)
