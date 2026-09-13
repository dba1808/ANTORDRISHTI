"""
Antordrishti — Dashboard Page
Professional dashboard with recent cases, clickable recent documents, and quick document import cards.
"""

from typing import Optional, List
import os

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGridLayout, QSizePolicy, QScrollArea
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QCursor

from app.theme import Colors, Fonts, Spacing, Sizes, Bg, Text, Border, Brand
from app.resources import get_icon, Icons
from ui.widgets.common import SectionLabel, ActionButton, DocumentTypeCard


class _QuickActionCard(QPushButton):
    """Compact quick action button with subtle workstation hover."""

    def __init__(self, text: str, icon_name: str, tooltip: str, parent=None):
        super().__init__(parent)
        self.setText(text)
        self.setIcon(get_icon(icon_name, Brand.GOLD))
        self.setIconSize(QSize(18, 18))
        self.setToolTip(tooltip)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(38)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {Bg.WHITE};
                border: 1px solid {Border.DEFAULT};
                border-radius: 6px;
                text-align: left;
                padding: 4px 14px;
                font-size: 12px;
                font-weight: 500;
                color: {Text.PRIMARY};
            }}
            QPushButton:hover {{
                background-color: {Bg.SECONDARY};
                border-color: {Brand.GOLD};
                color: {Brand.GOLD};
            }}
        """)


class _InfoCard(QFrame):
    """Refined info card for dashboard workstation sections."""

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            _InfoCard {{
                background-color: {Bg.WHITE};
                border: 1px solid {Border.DEFAULT};
                border-radius: 8px;
            }}
        """)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(Spacing.LG, Spacing.LG,
                                        Spacing.LG, Spacing.LG)
        self._layout.setSpacing(Spacing.SM)

        title_label = QLabel(title.upper())
        title_label.setStyleSheet(f"""
            font-size: 10px; font-weight: 700;
            color: {Text.MUTED};
            letter-spacing: 0.8px;
        """)
        self._layout.addWidget(title_label)

    def add_widget(self, widget):
        self._layout.addWidget(widget)

    def add_content_label(self, text: str, color: Optional[str] = None):
        label = QLabel(text)
        label.setStyleSheet(
            f"font-size: 12px; color: {color or Text.PRIMARY}; font-weight: 500;"
        )
        label.setWordWrap(True)
        self._layout.addWidget(label)
        return label


class DashboardPage(QWidget):
    """Main dashboard page."""

    new_case_clicked = pyqtSignal()
    open_case_clicked = pyqtSignal()
    import_document_clicked = pyqtSignal()
    open_image_clicked = pyqtSignal()
    open_pdf_clicked = pyqtSignal()
    scan_document_clicked = pyqtSignal()
    capture_camera_clicked = pyqtSignal()
    run_analysis_clicked = pyqtSignal()
    generate_report_clicked = pyqtSignal()
    document_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)  # type: ignore[arg-type]
        self.setStyleSheet("background-color: #FFFFFF;")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background-color: #FFFFFF;")

        container = QWidget()
        container.setStyleSheet("background-color: #FFFFFF;")
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(Spacing.XXL, Spacing.XL,
                                       Spacing.XXL, Spacing.XL)
        main_layout.setSpacing(Spacing.XL)

        # Header
        header = QLabel("Dashboard")
        header.setStyleSheet(
            "font-size: 20px; font-weight: 800; color: #0F172A;"
        )
        main_layout.addWidget(header)

        # ── Quick Evidence Import Section (Dual Hover Boxes) ──
        quick_import_title = SectionLabel("Add & Inspect Documents")
        main_layout.addWidget(quick_import_title)

        dual_boxes_layout = QHBoxLayout()
        dual_boxes_layout.setSpacing(16)

        img_card = DocumentTypeCard(
            title="Open Image Document",
            description="Forensic questioned image file",
            formats="JPG  •  PNG  •  TIFF  •  BMP",
            icon_name=Icons.IMAGE_FORENSICS
        )
        img_card.clicked.connect(self.open_image_clicked.emit)
        dual_boxes_layout.addWidget(img_card)

        pdf_card = DocumentTypeCard(
            title="Open PDF Document",
            description="Multi-page vector or scanned document",
            formats="PDF Files (.pdf)",
            icon_name=Icons.DOCUMENT
        )
        pdf_card.clicked.connect(self.open_pdf_clicked.emit)
        dual_boxes_layout.addWidget(pdf_card)

        dual_boxes_layout.addStretch()
        main_layout.addLayout(dual_boxes_layout)

        # Quick Actions
        qa_label = SectionLabel("Quick Actions")
        main_layout.addWidget(qa_label)

        qa_grid = QGridLayout()
        qa_grid.setSpacing(Spacing.SM)

        quick_actions = [
            ("New Case", Icons.NEW_CASE, "Create a new forensic case",
             self.new_case_clicked),
            ("Open Case", Icons.OPEN, "Open an existing case",
             self.open_case_clicked),
            ("Import Document", Icons.IMPORT, "Import a document for analysis",
             self.import_document_clicked),
            ("Scan Document", Icons.SCAN, "Scan a physical document",
             self.scan_document_clicked),
            ("Capture from Camera", Icons.CAMERA_CAPTURE, "Capture document image",
             self.capture_camera_clicked),
            ("Run Analysis", Icons.ANALYSIS, "Run forensic analysis",
             self.run_analysis_clicked),
            ("Generate Report", Icons.REPORT_GEN, "Generate forensic report",
             self.generate_report_clicked),
        ]

        for i, (text, icon, tip, signal) in enumerate(quick_actions):
            btn = _QuickActionCard(text, icon, tip)
            btn.clicked.connect(signal.emit)
            qa_grid.addWidget(btn, i // 4, i % 4)

        main_layout.addLayout(qa_grid)

        # Cards row
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(Spacing.MD)

        # Current Case
        self.case_card = _InfoCard("Current Case")
        self._case_name_lbl = self.case_card.add_content_label("No active case")
        self._case_details_lbl = self.case_card.add_content_label(
            "Create or open a case to begin examination.", Text.MUTED
        )
        cards_layout.addWidget(self.case_card)

        # Recent Documents (Dynamic)
        self.docs_card = _InfoCard("Recent Documents")
        self._doc_items_layout = QVBoxLayout()
        self._doc_items_layout.setSpacing(6)
        self.docs_card.add_widget(QWidget())  # placeholder
        self.docs_card._layout.addLayout(self._doc_items_layout)
        self._update_recent_doc_views([])
        cards_layout.addWidget(self.docs_card)

        # Analysis Status
        self.analysis_card = _InfoCard("Analysis Engine Status")
        self._analysis_title_lbl = self.analysis_card.add_content_label("Analysis Engine Active")
        self._analysis_detail_lbl = self.analysis_card.add_content_label(
            "OpenCV & PyMuPDF ready for processing.", Brand.GOLD
        )
        cards_layout.addWidget(self.analysis_card)

        main_layout.addLayout(cards_layout)

        # System Status
        sys_card = _InfoCard("System Forensic Services")

        status_items = [
            ("Application Core", "Ready", Colors.SUCCESS),
            ("Document & PDF Engine", "PyMuPDF & Pillow Connected", Colors.SUCCESS),
            ("Image Processing Engine", "OpenCV Connected", Colors.SUCCESS),
            ("Hash & Integrity Engine", "SHA-256 / MD5 Active", Colors.SUCCESS),
            ("Error Level Analysis", "Pillow / OpenCV Active", Colors.SUCCESS),
            ("Noise Pattern Analyzer", "Active", Colors.SUCCESS),
        ]
        for name, status, color in status_items:
            row = QHBoxLayout()
            n_label = QLabel(name)
            n_label.setStyleSheet(f"font-size: 11px; color: {Text.PRIMARY}; font-weight: 500;")
            s_label = QLabel(f"●  {status}")
            s_label.setStyleSheet(f"font-size: 11px; color: {color}; font-weight: 600;")
            row.addWidget(n_label)
            row.addStretch()
            row.addWidget(s_label)
            sys_card._layout.addLayout(row)

        main_layout.addWidget(sys_card)
        main_layout.addStretch()

        scroll.setWidget(container)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def set_current_context(self, context):
        """Update dashboard display when active case or evidence changes."""
        if context and context.case:
            case_title = context.case.case_name or "Untitled Case"
            case_num = context.case.case_number or "—"
            examiner = context.case.examiner_name or "Unknown Examiner"
            self._case_name_lbl.setText(f"{case_title} ({case_num})")
            self._case_details_lbl.setText(f"Examiner: {examiner}")
        else:
            self._case_name_lbl.setText("No active case")
            self._case_details_lbl.setText("Create or open a case to begin examination.")

        if context and context.document:
            self.add_recent_document(context.document.file_path)

    def add_recent_document(self, path: str):
        if not hasattr(self, "_recent_paths"):
            self._recent_paths: List[str] = []
        if path in self._recent_paths:
            self._recent_paths.remove(path)
        self._recent_paths.insert(0, path)
        self._update_recent_doc_views(self._recent_paths[:4])

    def _update_recent_doc_views(self, paths: List[str]):
        while self._doc_items_layout.count() > 0:
            item = self._doc_items_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not paths:
            lbl = QLabel("No recent documents")
            lbl.setStyleSheet(f"font-size: 11px; color: {Text.MUTED};")
            self._doc_items_layout.addWidget(lbl)
        else:
            for p in paths:
                btn = QPushButton(f"📄  {os.path.basename(p)}")
                btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                btn.setToolTip(p)
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: {Bg.SECONDARY};
                        border: 1px solid {Border.DEFAULT};
                        border-radius: 4px;
                        text-align: left;
                        font-size: 11px;
                        color: {Text.PRIMARY};
                        font-weight: 500;
                        padding: 4px 8px;
                    }}
                    QPushButton:hover {{
                        border-color: {Brand.GOLD};
                        color: {Brand.GOLD};
                        background: {Bg.WHITE};
                    }}
                """)
                btn.clicked.connect(lambda _, path_to_open=p: self.document_selected.emit(path_to_open))
                self._doc_items_layout.addWidget(btn)
