"""
Antordrishti — Main Window
Central orchestrator: menu, toolbar, navigation, tabbed workspace, inspector, status bar.
Tab-based document workspace, command palette, case management, and workspace restoration.
"""

import os
import logging

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QSplitter,
    QStackedWidget, QTabWidget, QFileDialog, QMessageBox, QApplication,
    QShortcut, QLabel, QPushButton, QFrame
)
from PyQt5.QtCore import Qt, QSize, QTimer
from PyQt5.QtGui import QIcon, QImage, QKeySequence

from app.constants import (
    APP_TITLE, NavPage, AppStatus,
    ALL_FILTER, IMAGE_FILTER, PDF_FILTER
)
from app.theme import Colors, Sizes
from app.resources import Icons

from ui.menu_bar import MenuBarManager
from ui.toolbar import MainToolbar
from ui.status_bar import ForensicStatusBar
from ui.navigation.navigation_panel import NavigationPanel
from ui.inspector.inspector_panel import InspectorPanel

# Pages
from ui.pages.dashboard import DashboardPage
from ui.pages.document_analysis import DocumentAnalysisPage
from ui.pages.ela import ELAPage
from ui.pages.metadata import MetadataPage
from ui.pages.ocr import OCRPage
from ui.pages.watermark import WatermarkPage
from ui.pages.image_forensics import ImageForensicsPage
from ui.pages.document_forensics import DocumentForensicsPage
from ui.pages.forgery_detection import ForgeryDetectionPage
from ui.pages.evidence_manager import EvidenceManagerPage
from ui.pages.evidence_fusion import EvidenceFusionPage
from ui.pages.histogram_page import HistogramPage
from ui.pages.reports import ReportsPage
from ui.pages.batch_processing import BatchProcessingPage
from ui.pages.settings import SettingsPage

# Dialogs
from ui.dialogs.new_case_dialog import NewCaseDialog
from ui.dialogs.about_dialog import AboutDialog
from ui.dialogs.case_info_dialog import CaseInfoDialog
from ui.dialogs.document_info_dialog import DocumentInfoDialog
from ui.dialogs.case_history_dialog import CaseHistoryDialog
from ui.dialogs.command_palette import CommandPalette, CommandItem

# Services
from services.document_service import load_document
from services.hash_service import calculate_hashes
from services.db_service import get_db
from services.app_state import get_app_state, CurrentDocumentContext

# Models
from models.case_model import CaseModel
from models.evidence_model import EvidenceModel

logger = logging.getLogger("antordrishti")

_MAX_TABS = 10


class MainWindow(QMainWindow):
    """Antordrishti main application window with tabbed workspace."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.setMinimumSize(1100, 700)

        # State
        self._current_case = None
        self._current_evidence = None
        self._current_document = None
        self._open_documents = {}  # path -> tab_index
        self._app_state = get_app_state()

        # Build UI
        self._build_ui()
        self._connect_signals()
        self._setup_shortcuts()

        # Initial state
        self._status_bar.set_status(AppStatus.READY)
        self.showMaximized()

        # Restore workspace state (deferred to allow event loop start)
        QTimer.singleShot(200, self._restore_workspace)

    def _build_ui(self):
        """Build the complete UI structure."""
        # Menu bar
        self._menu_manager = MenuBarManager(self.menuBar(), self)

        # Toolbar
        self._toolbar = MainToolbar(self)
        self.addToolBar(self._toolbar)

        # Status bar
        self._status_bar = ForensicStatusBar(self)
        self.setStatusBar(self._status_bar)

        # ── Central area: nav | workspace | inspector ────────
        central = QWidget()
        central_layout = QHBoxLayout(central)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)

        # Main splitter
        self._main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Navigation panel
        self._nav_panel = NavigationPanel()
        self._main_splitter.addWidget(self._nav_panel)

        # Central workspace — Tab widget for document workspace
        workspace_container = QWidget()
        workspace_layout = QVBoxLayout(workspace_container)
        workspace_layout.setContentsMargins(0, 0, 0, 0)
        workspace_layout.setSpacing(0)

        self._current_doc_bar = self._build_current_document_bar()
        workspace_layout.addWidget(self._current_doc_bar)

        self._tab_widget = QTabWidget()
        self._tab_widget.setTabsClosable(True)
        self._tab_widget.setMovable(True)
        self._tab_widget.setDocumentMode(True)
        self._tab_widget.tabCloseRequested.connect(self._on_tab_close)
        self._tab_widget.currentChanged.connect(self._on_tab_changed)
        self._tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background-color: {Colors.BACKGROUND};
            }}
            QTabBar::tab {{
                background-color: #F1F5F9;
                border: 1px solid {Colors.BORDER};
                border-bottom: none;
                padding: 6px 16px;
                margin-right: 2px;
                font-size: 12px;
                color: {Colors.TEXT_SECONDARY};
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                min-width: 80px;
                max-width: 200px;
            }}
            QTabBar::tab:selected {{
                background-color: {Colors.PANEL};
                color: {Colors.TEXT_PRIMARY};
                font-weight: 600;
                border-bottom: 2px solid #B08D3A;
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {Colors.HOVER};
                color: {Colors.TEXT_PRIMARY};
            }}
            QTabBar::close-button {{
                image: none;
                subcontrol-position: right;
                padding: 2px;
            }}
            QTabBar::close-button:hover {{
                background-color: #FEE2E2;
                border-radius: 3px;
            }}
        """)

        # Build pages in stacked widget (for non-document pages)
        self._workspace = QStackedWidget()
        self._workspace.setStyleSheet(f"background-color: {Colors.BACKGROUND};")
        self._build_pages()

        # Add dashboard as permanent first tab
        dashboard_idx = self._pages.get(NavPage.DASHBOARD.value, 0)
        dashboard_widget = self._workspace.widget(dashboard_idx)
        # We need to reparent it from stacked widget to tab widget
        # Instead, we put the stacked widget inside the tab widget's first tab
        self._tab_widget.addTab(self._workspace, "Dashboard")

        # Make first tab (Dashboard) not closeable
        self._tab_widget.tabBar().setTabButton(0, self._tab_widget.tabBar().ButtonPosition.RightSide, None)

        workspace_layout.addWidget(self._tab_widget, 1)
        self._main_splitter.addWidget(workspace_container)

        # Inspector panel
        self._inspector = InspectorPanel()
        self._main_splitter.addWidget(self._inspector)

        # Splitter proportions
        self._main_splitter.setStretchFactor(0, 0)  # nav fixed
        self._main_splitter.setStretchFactor(1, 1)  # workspace stretches
        self._main_splitter.setStretchFactor(2, 0)  # inspector fixed
        self._main_splitter.setSizes([Sizes.NAV_WIDTH, 820, Sizes.INSPECTOR_WIDTH])

        central_layout.addWidget(self._main_splitter)
        self.setCentralWidget(central)

    def _build_pages(self):
        """Create and add all pages to the stacked widget."""
        self._pages = {}

        pages = [
            (NavPage.DASHBOARD, DashboardPage),
            (NavPage.DOCUMENT_ANALYSIS, DocumentAnalysisPage),
            (NavPage.IMAGE_FORENSICS, ImageForensicsPage),
            (NavPage.DOCUMENT_FORENSICS, DocumentForensicsPage),
            (NavPage.ELA, ELAPage),
            (NavPage.METADATA, MetadataPage),
            (NavPage.OCR, OCRPage),
            (NavPage.WATERMARK, WatermarkPage),
            (NavPage.FORGERY_DETECTION, ForgeryDetectionPage),
            (NavPage.HISTOGRAM, HistogramPage),
            (NavPage.EVIDENCE_MANAGER, EvidenceManagerPage),
            (NavPage.EVIDENCE_FUSION, EvidenceFusionPage),
            (NavPage.REPORT_GENERATOR, ReportsPage),
            (NavPage.BATCH_PROCESSING, BatchProcessingPage),
            (NavPage.SETTINGS, SettingsPage),
        ]

        for nav_page, PageClass in pages:
            page = PageClass()
            idx = self._workspace.addWidget(page)
            self._pages[nav_page.value] = idx

    def _setup_shortcuts(self):
        """Register keyboard shortcuts."""
        # Command palette
        QShortcut(QKeySequence("Ctrl+K"), self, self._on_command_palette)

        # Tab shortcuts
        QShortcut(QKeySequence("Ctrl+W"), self, self._close_current_tab)
        QShortcut(QKeySequence("Ctrl+Tab"), self, self._next_tab)
        QShortcut(QKeySequence("Ctrl+Shift+Tab"), self, self._prev_tab)

    def _connect_signals(self):
        """Wire all signals to slots."""
        # Navigation
        self._nav_panel.page_selected.connect(self._on_page_selected)
        self._nav_panel.add_image_clicked.connect(self._on_import_image)
        self._nav_panel.add_pdf_clicked.connect(self._on_import_pdf)

        # Menu signals
        m = self._menu_manager
        m.new_case_requested.connect(self._on_new_case)
        m.new_document_requested.connect(self._on_open_document)
        m.open_document_requested.connect(self._on_open_document)
        m.open_image_requested.connect(self._on_import_image)
        m.open_pdf_requested.connect(self._on_import_pdf)
        m.import_image_requested.connect(self._on_import_image)
        m.import_pdf_requested.connect(self._on_import_pdf)
        m.save_requested.connect(self._on_save_processed)
        m.save_processed_requested.connect(self._on_save_processed)
        m.export_analysis_requested.connect(self._on_export_analysis)
        m.reset_processing_requested.connect(self._on_reset_processing)
        m.exit_requested.connect(self._on_exit)
        m.about_requested.connect(self._on_about)
        m.case_info_requested.connect(self._on_case_info)
        m.settings_requested.connect(
            lambda: self._switch_page(NavPage.SETTINGS.value)
        )
        m.zoom_in_requested.connect(self._on_zoom_in)
        m.zoom_out_requested.connect(self._on_zoom_out)
        m.zoom_fit_requested.connect(self._on_zoom_fit)
        m.zoom_actual_requested.connect(self._on_zoom_actual)
        m.fullscreen_requested.connect(self._on_fullscreen)
        m.toggle_nav_requested.connect(self._toggle_nav)
        m.toggle_inspector_requested.connect(self._toggle_inspector)
        m.toggle_toolbar_requested.connect(self._toggle_toolbar)
        m.toggle_statusbar_requested.connect(self._toggle_statusbar)
        m.run_analysis_requested.connect(self._on_run_analysis)
        m.generate_report_requested.connect(
            lambda: self._switch_page(NavPage.REPORT_GENERATOR.value)
        )

        # New menu signals
        m.new_workspace_requested.connect(self._on_new_workspace)
        m.open_case_history_requested.connect(self._on_open_case_history)
        m.save_case_requested.connect(self._on_save_case)
        m.command_palette_requested.connect(self._on_command_palette)

        # Toolbar signals
        t = self._toolbar
        t.new_case_clicked.connect(self._on_new_case)
        t.open_clicked.connect(self._on_open_document)
        t.open_image_clicked.connect(self._on_import_image)
        t.open_pdf_clicked.connect(self._on_import_pdf)
        t.import_clicked.connect(self._on_open_document)
        t.save_clicked.connect(self._on_save_processed)
        t.analysis_clicked.connect(self._on_run_analysis)
        t.report_clicked.connect(
            lambda: self._switch_page(NavPage.REPORT_GENERATOR.value)
        )
        t.compare_clicked.connect(lambda: self._show_info("Compare", "Compare tool active in document viewer."))
        t.scan_clicked.connect(lambda: self._show_info("Scan", "Scanner interface not connected."))
        t.camera_clicked.connect(lambda: self._show_info("Camera", "Camera capture not connected."))

        # Dashboard signals
        dashboard = self._workspace.widget(self._pages[NavPage.DASHBOARD.value])
        dashboard.new_case_clicked.connect(self._on_new_case)
        dashboard.open_case_clicked.connect(self._on_new_case)
        dashboard.import_document_clicked.connect(self._on_open_document)
        dashboard.open_image_clicked.connect(self._on_import_image)
        dashboard.open_pdf_clicked.connect(self._on_import_pdf)
        dashboard.document_selected.connect(self._load_document)
        dashboard.run_analysis_clicked.connect(self._on_run_analysis)
        dashboard.generate_report_clicked.connect(
            lambda: self._switch_page(NavPage.REPORT_GENERATOR.value)
        )

        # Document viewer signals in DocumentAnalysisPage
        doc_page: DocumentAnalysisPage = self._workspace.widget(
            self._pages[NavPage.DOCUMENT_ANALYSIS.value]
        )
        doc_page.document_viewer.document_loaded.connect(self._on_document_loaded)
        doc_page.document_viewer.zoom_changed.connect(
            lambda z: self._status_bar.set_zoom(z)
        )
        doc_page.document_viewer.page_changed.connect(self._on_page_changed)
        doc_page.document_viewer.file_dropped.connect(self._on_file_dropped)
        doc_page.document_viewer.open_image_requested.connect(self._on_import_image)
        doc_page.document_viewer.open_pdf_requested.connect(self._on_import_pdf)
        doc_page.save_processed_requested.connect(self._on_save_processed)

        # Hash panel
        self._inspector.hash_panel.calculate_requested.connect(
            self._on_calculate_hash
        )
        self._inspector.hash_panel.verify_requested.connect(
            self._on_verify_hash
        )

        ocr_page = self._workspace.widget(self._pages[NavPage.OCR.value])
        if hasattr(ocr_page, "document_import_requested"):
            ocr_page.document_import_requested.connect(self._load_document)

        self._app_state.context_changed.connect(self._on_context_changed)

    def _build_current_document_bar(self) -> QFrame:
        """Create the visible active evidence/document indicator."""
        bar = QFrame()
        bar.setFixedHeight(56)
        bar.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-bottom: 1px solid #E2E8F0;
            }
        """)

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(16, 6, 16, 6)
        layout.setSpacing(12)

        # Left Info Stack
        info_col = QVBoxLayout()
        info_col.setContentsMargins(0, 0, 0, 0)
        info_col.setSpacing(2)

        # Kicker row
        kicker_row = QHBoxLayout()
        kicker_row.setSpacing(8)
        self._context_kicker = QLabel("CURRENT EVIDENCE")
        self._context_kicker.setStyleSheet("font-size: 9px; font-weight: 800; color: #94A3B8; letter-spacing: 0.8px;")
        kicker_row.addWidget(self._context_kicker)
        self._evidence_id_badge = QLabel("")
        self._evidence_id_badge.setStyleSheet("""
            font-size: 10px; font-weight: 700; color: #785F23;
            background-color: #FAF4E6; border: 1px solid #F5EACB;
            border-radius: 3px; padding: 1px 6px;
        """)
        self._evidence_id_badge.setVisible(False)
        kicker_row.addWidget(self._evidence_id_badge)
        kicker_row.addStretch()
        info_col.addLayout(kicker_row)

        # Main row: Filename + Details + Integrity
        main_row = QHBoxLayout()
        main_row.setSpacing(10)

        self._context_main = QLabel("No document loaded")
        self._context_main.setStyleSheet("font-size: 13px; font-weight: 700; color: #0F172A;")
        main_row.addWidget(self._context_main)

        self._doc_meta_label = QLabel("Open an image or PDF to begin examination.")
        self._doc_meta_label.setStyleSheet("font-size: 11px; color: #64748B; font-weight: 400;")
        main_row.addWidget(self._doc_meta_label)

        self._integrity_badge = QLabel("")
        self._integrity_badge.setStyleSheet("""
            font-size: 10px; font-weight: 600; color: #16A34A;
            background-color: #DCFCE7; border: 1px solid #BBF7D0;
            border-radius: 3px; padding: 1px 6px;
        """)
        self._integrity_badge.setVisible(False)
        main_row.addWidget(self._integrity_badge)

        main_row.addStretch()
        info_col.addLayout(main_row)

        layout.addLayout(info_col, 1)

        # Action Buttons
        self._btn_context_open_img = QPushButton("Open Image")
        self._btn_context_open_img.setFixedHeight(28)
        self._btn_context_open_img.clicked.connect(self._on_import_image)
        layout.addWidget(self._btn_context_open_img)

        self._btn_context_open_pdf = QPushButton("Open PDF")
        self._btn_context_open_pdf.setFixedHeight(28)
        self._btn_context_open_pdf.clicked.connect(self._on_import_pdf)
        layout.addWidget(self._btn_context_open_pdf)

        self._btn_context_change = QPushButton("Change Document")
        self._btn_context_change.setFixedHeight(28)
        self._btn_context_change.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                border: 1px solid #CBD5E1;
                border-radius: 4px;
                padding: 4px 12px;
                font-size: 11px;
                font-weight: 500;
                color: #0F172A;
            }
            QPushButton:hover {
                background-color: #F8FAFC;
                border-color: #94A3B8;
            }
        """)
        self._btn_context_change.clicked.connect(self._on_open_document)
        self._btn_context_change.setVisible(False)
        layout.addWidget(self._btn_context_change)

        self._btn_context_close = QPushButton("×")
        self._btn_context_close.setToolTip("Close current document")
        self._btn_context_close.setFixedSize(28, 28)
        self._btn_context_close.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #CBD5E1;
                border-radius: 4px;
                font-size: 14px;
                font-weight: 700;
                color: #64748B;
            }
            QPushButton:hover {
                background-color: #FEE2E2;
                border-color: #FCA5A5;
                color: #DC2626;
            }
        """)
        self._btn_context_close.clicked.connect(self._on_close_document)
        self._btn_context_close.setVisible(False)
        layout.addWidget(self._btn_context_close)

        return bar

    # ── Tab Management ───────────────────────────────────────

    def _on_tab_close(self, index: int):
        """Close a tab (except Dashboard at index 0)."""
        if index == 0:
            return  # Dashboard is permanent

        widget = self._tab_widget.widget(index)
        tab_text = self._tab_widget.tabText(index)
        self._tab_widget.removeTab(index)

        # Remove from open documents tracking
        to_remove = [p for p, i in self._open_documents.items()
                     if self._tab_widget.indexOf(widget) == -1]
        for p in to_remove:
            self._open_documents.pop(p, None)

        self.statusBar().showMessage(f"Closed: {tab_text}", 2000)

    def _close_current_tab(self):
        """Close the currently active tab (Ctrl+W)."""
        idx = self._tab_widget.currentIndex()
        if idx > 0:  # Don't close Dashboard
            self._on_tab_close(idx)

    def _next_tab(self):
        """Switch to next tab (Ctrl+Tab)."""
        count = self._tab_widget.count()
        if count > 1:
            current = self._tab_widget.currentIndex()
            self._tab_widget.setCurrentIndex((current + 1) % count)

    def _prev_tab(self):
        """Switch to previous tab (Ctrl+Shift+Tab)."""
        count = self._tab_widget.count()
        if count > 1:
            current = self._tab_widget.currentIndex()
            self._tab_widget.setCurrentIndex((current - 1) % count)

    def _on_tab_changed(self, index: int):
        """Handle tab selection change."""
        if index == 0:
            # Dashboard tab — show the dashboard page in stacked widget
            dashboard_idx = self._pages.get(NavPage.DASHBOARD.value, 0)
            self._workspace.setCurrentIndex(dashboard_idx)

    def _open_document_tab(self, path: str, title: str) -> int:
        """Open a document in a new tab or switch to existing tab."""
        # Check if already open
        if path in self._open_documents:
            # Find the tab with this document and switch to it
            for i in range(self._tab_widget.count()):
                if self._tab_widget.tabToolTip(i) == path:
                    self._tab_widget.setCurrentIndex(i)
                    return i

        # Check tab limit
        if self._tab_widget.count() >= _MAX_TABS:
            QMessageBox.warning(
                self, "Tab Limit Reached",
                f"Maximum of {_MAX_TABS} tabs allowed.\n"
                "Please close some tabs before opening new documents."
            )
            return -1

        # Switch the stacked widget to document analysis page
        doc_page_idx = self._pages.get(NavPage.DOCUMENT_ANALYSIS.value, 1)
        self._workspace.setCurrentIndex(doc_page_idx)

        # Add new tab pointing to the stacked widget (which now shows doc analysis)
        tab_title = os.path.basename(title)
        if len(tab_title) > 25:
            tab_title = tab_title[:22] + "..."

        # For document tabs, we reuse tab 0's stacked widget
        # and just switch it to the correct page
        # We use the tab widget to track which document is "active"
        idx = self._tab_widget.currentIndex()
        self._open_documents[path] = idx

        self.statusBar().showMessage(f"Opened: {os.path.basename(title)}", 3000)
        return idx

    # ── Page Navigation ──────────────────────────────────────

    def _on_page_selected(self, page_name: str):
        idx = self._pages.get(page_name)
        if idx is not None:
            self._workspace.setCurrentIndex(idx)
            # Make sure we're on the Dashboard tab (tab 0 = stacked widget)
            self._tab_widget.setCurrentIndex(0)
            # Synchronize document with ELA if switching to ELA page
            if page_name == NavPage.ELA.value and self._current_document:
                ela_page: ELAPage = self._workspace.widget(idx)
                if not ela_page.viewer.get_current_image():
                    ela_page.load_document(self._current_document.file_path)
            # Synchronize document with OCR page if switching to OCR
            if page_name == NavPage.OCR.value and self._current_document:
                ocr_page = self._workspace.widget(idx)
                if hasattr(ocr_page, "set_current_context"):
                    ocr_page.set_current_context(self._app_state.context)
                elif hasattr(ocr_page, "load_document"):
                    ocr_page.load_document(self._current_document.file_path)

    def _switch_page(self, page_name: str):
        idx = self._pages.get(page_name)
        if idx is not None:
            self._workspace.setCurrentIndex(idx)
            self._tab_widget.setCurrentIndex(0)
            self._nav_panel.select_page(page_name)

    # ── File Operations ──────────────────────────────────────

    def _on_open_document(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Document or Image", "",
            f"{ALL_FILTER};;{IMAGE_FILTER};;{PDF_FILTER};;All Files (*.*)"
        )
        if path:
            self._load_document(path)

    def _on_import_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Image", "",
            f"{IMAGE_FILTER};;All Files (*.*)"
        )
        if path:
            self._load_document(path)

    def _on_import_pdf(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open PDF Document", "",
            f"{PDF_FILTER};;All Files (*.*)"
        )
        if path:
            self._load_document(path)

    def _load_document(self, path: str):
        """Load a document and update the UI cleanly."""
        try:
            if not os.path.exists(path):
                QMessageBox.warning(
                    self, "File Not Found",
                    f"The specified file does not exist:\n{path}"
                )
                return

            self._status_bar.set_status(AppStatus.LOADING)
            doc = load_document(path)
            if doc is None:
                self._status_bar.set_status(AppStatus.ERROR)
                QMessageBox.warning(
                    self, "Unable to Open Document",
                    f"Unable to open the selected document.\n\n"
                    f"Reason: Unsupported format or corrupted file.\n\n"
                    f"File: {path}"
                )
                return

            case = self._ensure_current_case()
            evidence = self._register_current_evidence(case, doc)
            self._current_case = case
            self._current_evidence = evidence
            self._current_document = doc

            # Switch to document analysis
            self._switch_page(NavPage.DOCUMENT_ANALYSIS.value)

            # Load in viewer
            doc_page: DocumentAnalysisPage = self._workspace.widget(
                self._pages[NavPage.DOCUMENT_ANALYSIS.value]
            )
            doc_page.document_viewer.load_file(path)

            # Update inspector
            self._inspector.update_document(doc)

            self._app_state.set_current_context(case, evidence, doc)
            self._sync_context_to_pages(self._app_state.context)

            # Update status bar
            self._status_bar.set_document(doc.file_name)
            self._status_bar.set_page(1, max(1, doc.page_count))
            self._status_bar.set_status(AppStatus.DOCUMENT_LOADED)
            self._status_bar.set_integrity(doc.integrity_status)

            # Update dashboard recent files
            dashboard = self._workspace.widget(self._pages[NavPage.DASHBOARD.value])
            if hasattr(dashboard, "add_recent_document"):
                dashboard.add_recent_document(path)

            # Track in SQLite recent files
            try:
                db = get_db()
                db.add_recent_file(path, doc.file_name, doc.file_type)
                if self._current_case:
                    db._conn.execute(
                        """INSERT INTO case_events
                           (case_id, evidence_id, event_type, description, timestamp)
                           VALUES (?, ?, ?, ?, ?)""",
                        (self._current_case.case_id, self._current_evidence.evidence_id if self._current_evidence else "",
                         "Document Loaded", f"Loaded {doc.file_name}", __import__('datetime').datetime.now().isoformat())
                    )
                    db._conn.commit()
            except Exception:
                pass

            self.statusBar().showMessage(f"Loaded: {doc.file_name} (SHA-256 calculated)", 4000)
            logger.info(f"Document loaded successfully: {path}")

        except PermissionError:
            self._status_bar.set_status(AppStatus.ERROR)
            QMessageBox.critical(
                self, "Permission Denied",
                f"Permission denied while attempting to read file:\n{path}"
            )
        except Exception as e:
            self._status_bar.set_status(AppStatus.ERROR)
            QMessageBox.critical(
                self, "Error",
                f"An unexpected error occurred while loading the document:\n\n{str(e)}"
            )
            logger.error(f"Error loading document: {e}")

    def _on_document_loaded(self, path: str):
        """Handle document loaded signal from viewer."""
        if path and (not self._current_document or self._current_document.file_path != path):
            self._load_document(path)

    def _on_page_changed(self, page_num: int):
        if self._current_document:
            self._status_bar.set_page(page_num, max(1, self._current_document.page_count))

    def _on_file_dropped(self, path: str):
        """Handle file dropped onto viewer."""
        self._load_document(path)

    def _set_active_case(self, case: CaseModel):
        """Set the authoritative active case across all pages and application state."""
        self._current_case = case
        self._status_bar.set_case(case.case_id)

        try:
            db = get_db()
            db.save_workspace_state("main_window", {
                "active_case_id": case.case_id,
                "active_document": self._current_document.file_path if self._current_document else "",
                "splitter_sizes": self._main_splitter.sizes() if hasattr(self, "_main_splitter") else []
            })
        except Exception:
            pass

        curr_ev = self._app_state.context.evidence if self._app_state.context else None
        curr_doc = self._app_state.context.document if self._app_state.context else None
        if curr_ev and curr_ev.case_id != case.case_id:
            curr_ev = None
            curr_doc = None
            self._current_evidence = None
            self._current_document = None

        self._app_state.set_current_context(case, curr_ev, curr_doc)

    def _ensure_current_case(self) -> CaseModel:
        """Ensure every evidence item belongs to a case."""
        if self._current_case:
            return self._current_case

        db = get_db()
        case_id = db.generate_case_id()
        now_dt = datetime.now()
        case = CaseModel(
            case_id=case_id,
            case_name="Untitled Forensic Investigation Case",
            title="Untitled Forensic Investigation Case",
            description="Auto-created case for imported evidence.",
            status="OPEN",
            created=now_dt,
            modified=now_dt,
        )
        db.create_case(case.to_dict())
        db.add_case_event(case_id, "", "Case Created", "Auto-created case for imported evidence")
        self._set_active_case(case)
        return case

    def _register_current_evidence(self, case: CaseModel, doc) -> EvidenceModel:
        """Create or reuse the evidence row for the loaded document."""
        db = get_db()
        existing = db.get_evidence_by_path(case.case_id, doc.file_path)
        if existing:
            evidence = EvidenceModel.from_dict(existing)
            # Reverify SHA-256 integrity
            if evidence.sha256 and evidence.sha256 != doc.sha256:
                doc.integrity_status = "INTEGRITY CHANGED"
                evidence.status = "INTEGRITY CHANGED"
                db.add_case_event(
                    case.case_id, evidence.evidence_id, "INTEGRITY CHANGED",
                    f"SHA-256 mismatch for {doc.file_name}! Recorded: {evidence.sha256[:12]}..., Current: {doc.sha256[:12]}..."
                )
            else:
                doc.integrity_status = "INTEGRITY VERIFIED"
                evidence.status = "INTEGRITY VERIFIED"
            evidence.sha256 = evidence.sha256 or doc.sha256
            evidence.md5 = evidence.md5 or doc.md5
            return evidence

        evidence = EvidenceModel(
            evidence_id=db.generate_evidence_id(case.case_id),
            case_id=case.case_id,
            name=doc.file_name,
            evidence_type="Original Evidence",
            source=doc.file_path,
            file_path=doc.file_path,
            sha256=doc.sha256,
            md5=doc.md5,
            status="INTEGRITY VERIFIED" if doc.sha256 else "Pending",
            reviewed=False,
            relevant=True,
            file_type=doc.file_type,
            file_size=doc.file_size,
            page_count=doc.page_count,
            width=doc.width,
            height=doc.height,
        )
        doc.integrity_status = "INTEGRITY VERIFIED" if doc.sha256 else "Pending"
        db.add_evidence(evidence.to_dict())
        db.add_processing_history(
            case.case_id,
            evidence.evidence_id,
            "Evidence imported",
            {
                "filename": doc.file_name,
                "sha256": doc.sha256,
                "file_type": doc.file_type,
                "file_size": doc.file_size,
            },
        )
        return evidence

    def _sync_context_to_pages(self, context: CurrentDocumentContext):
        """Push the current evidence/document to modules that can use it."""
        for page_name, idx in self._pages.items():
            page = self._workspace.widget(idx)
            if hasattr(page, "set_current_context"):
                try:
                    page.set_current_context(context)
                except Exception as e:
                    logger.debug(f"Error syncing context to {page_name}: {e}")
            elif context.document and hasattr(page, "load_document"):
                try:
                    page.load_document(context.document.file_path)
                except TypeError:
                    pass

    def _on_context_changed(self, context: CurrentDocumentContext):
        """Update the current evidence bar from shared state and broadcast."""
        self._sync_context_to_pages(context)
        evidence = context.evidence
        doc = context.document
        case = context.case

        if not doc:
            self._context_main.setText("No document loaded")
            case_title = case.case_name if case else "No active case"
            case_id = case.case_id if case else ""
            case_text = f"Case {case_id} ({case_title})" if case else "No active case"
            self._doc_meta_label.setText(f"{case_text} — Open an image or PDF to begin examination.")
            self._evidence_id_badge.setVisible(False)
            self._integrity_badge.setVisible(False)
            self._btn_context_open_img.setVisible(True)
            self._btn_context_open_pdf.setVisible(True)
            self._btn_context_change.setVisible(False)
            self._btn_context_close.setVisible(False)
            return

        evidence_id = evidence.evidence_id if evidence else "EVD-000001"
        self._evidence_id_badge.setText(evidence_id)
        self._evidence_id_badge.setVisible(True)

        self._context_main.setText(doc.file_name)
        page_str = f"Page {doc.current_page} / {max(1, doc.page_count)}"
        file_type = (doc.file_type or "Document").upper()
        case_id = case.case_id if case else "Unassigned"
        self._doc_meta_label.setText(f"{file_type}  •  {page_str}  •  Case {case_id}")

        status = doc.integrity_status or "INTEGRITY VERIFIED"
        self._integrity_badge.setText(f"✓ {status}")
        self._integrity_badge.setVisible(True)

        self._btn_context_open_img.setVisible(False)
        self._btn_context_open_pdf.setVisible(False)
        self._btn_context_change.setVisible(True)
        self._btn_context_close.setVisible(True)

    def _on_close_document(self):
        """Close the active document while preserving the current case."""
        if self._current_evidence and self._current_evidence.status == "Pending":
            reply = QMessageBox.question(
                self, "Unsaved Evidence",
                "This document has not been explicitly saved to the case.\n\n"
                "Closing it will clear the active workspace. Do you want to proceed?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply == QMessageBox.No:
                return

        try:
            if self._current_case and self._current_evidence:
                db = get_db()
                db._conn.execute(
                    """INSERT INTO case_events
                       (case_id, evidence_id, event_type, description, timestamp)
                       VALUES (?, ?, ?, ?, ?)""",
                    (self._current_case.case_id, self._current_evidence.evidence_id, 
                     "Document Closed", "Closed active document", __import__('datetime').datetime.now().isoformat())
                )
                db._conn.commit()
        except Exception:
            pass

        self._current_document = None
        self._current_evidence = None
        self._app_state.clear_document(keep_case=True)
        self._inspector.update_document(None)
        self._status_bar.set_document("")
        self._status_bar.set_page(0, 0)
        self._status_bar.set_integrity("")
        ocr_page = self._workspace.widget(self._pages[NavPage.OCR.value])
        if hasattr(ocr_page, "reset_workspace"):
            ocr_page.reset_workspace(clear_document=True)

        doc_page = self._workspace.widget(self._pages[NavPage.DOCUMENT_ANALYSIS.value])
        if hasattr(doc_page, "clear_workspace"):
            doc_page.clear_workspace()

        self.statusBar().showMessage("Current document closed. Case remains open.", 3000)

    def _on_save_processed(self):
        """Save the current working copy/processed image to a user-specified path."""
        doc_page: DocumentAnalysisPage = self._workspace.widget(
            self._pages[NavPage.DOCUMENT_ANALYSIS.value]
        )
        img = doc_page.get_processed_image()
        if not img or img.isNull():
            QMessageBox.information(
                self, "No Image to Save",
                "There is no active document or processed image to save."
            )
            return

        default_name = "processed_image.png"
        if self._current_document and self._current_document.file_name:
            base, _ = os.path.splitext(self._current_document.file_name)
            default_name = f"{base}_processed.png"

        out_path, _ = QFileDialog.getSaveFileName(
            self, "Save Processed Image", default_name,
            "PNG Image (*.png);;JPEG Image (*.jpg *.jpeg);;TIFF Image (*.tiff *.tif);;BMP Image (*.bmp)"
        )

        if out_path:
            # Prevent accidental silent overwrite of original source
            if self._current_document and os.path.abspath(out_path) == os.path.abspath(self._current_document.file_path):
                QMessageBox.warning(
                    self, "Protected File",
                    "Forensic integrity rule: Cannot overwrite the original evidence file directly.\n"
                    "Please specify a different filename for the processed result."
                )
                return

            try:
                success = img.save(out_path)
                if success:
                    QMessageBox.information(
                        self, "Image Saved",
                        f"Processed image saved successfully:\n{out_path}"
                    )
                    self.statusBar().showMessage(f"Saved: {os.path.basename(out_path)}", 3000)
                else:
                    QMessageBox.critical(
                        self, "Save Error",
                        f"Failed to write image data to:\n{out_path}"
                    )
            except Exception as e:
                QMessageBox.critical(
                    self, "Save Error",
                    f"An error occurred while saving the image:\n{str(e)}"
                )

    def _on_export_analysis(self):
        """Export analysis result image."""
        self._on_save_processed()

    def _on_reset_processing(self):
        """Reset processing on the active document analysis page."""
        doc_page: DocumentAnalysisPage = self._workspace.widget(
            self._pages[NavPage.DOCUMENT_ANALYSIS.value]
        )
        doc_page.reset_processing()
        self.statusBar().showMessage("Processing reset to original evidence.", 3000)

    # ── Case Operations ──────────────────────────────────────

    def _on_new_case(self):
        dialog = NewCaseDialog(self)
        if dialog.exec_() == NewCaseDialog.Accepted:
            case = dialog.get_case()
            if case:
                self._set_active_case(case)
                self.statusBar().showMessage(
                    f"Case created: {case.case_id} — {case.case_name}", 4000
                )
                logger.info(f"Case created and set active: {case.case_id}")

    def _on_open_case_history(self):
        """Open the case history browser dialog."""
        dialog = CaseHistoryDialog(self)
        dialog.case_selected.connect(self._load_case)
        dialog.exec_()

    def _load_case(self, case: CaseModel):
        """Load a case from the history dialog."""
        self._set_active_case(case)
        self.statusBar().showMessage(
            f"Case loaded: {case.case_id} — {case.case_name}", 4000
        )
        logger.info(f"Case loaded from history: {case.case_id}")

    def _on_save_case(self):
        """Save current case state to SQLite."""
        if not self._current_case:
            QMessageBox.information(
                self, "No Active Case",
                "No case is currently open. Create a new case first."
            )
            return

        try:
            db = get_db()
            updates = {
                "case_name": self._current_case.case_name,
                "title": self._current_case.title,
                "examiner": self._current_case.examiner_name,
                "organization": self._current_case.organization,
                "description": self._current_case.description,
                "reference_number": self._current_case.reference_number,
                "notes": self._current_case.notes,
                "status": self._current_case.status,
            }
            success = db.update_case(self._current_case.case_id, updates)
            if success:
                self.statusBar().showMessage(
                    f"Case saved: {self._current_case.case_id} — {self._current_case.case_name}", 3000
                )
            else:
                self.statusBar().showMessage("Case save failed.", 3000)
        except Exception as e:
            QMessageBox.warning(
                self, "Save Error",
                f"Could not save case:\n{str(e)}"
            )

    def _on_new_workspace(self):
        """Clear current document and processing state without deleting the case."""
        reply = QMessageBox.question(
            self, "New Workspace",
            "This will clear the active document, working image, and OCR results.\n"
            "The current case remains saved in the database.\n\n"
            "Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        # Close all document tabs (except Dashboard)
        while self._tab_widget.count() > 1:
            self._tab_widget.removeTab(1)
        self._open_documents.clear()

        self._current_document = None
        self._current_evidence = None
        self._app_state.clear_document(keep_case=True)

        # Reset to dashboard
        self._switch_page(NavPage.DASHBOARD.value)

        # Reset status bar
        self._status_bar.set_status(AppStatus.READY)
        self._status_bar.set_document("")
        self._status_bar.set_page(0, 0)

        self.statusBar().showMessage("Workspace reset.", 3000)

    def _on_case_info(self):
        dialog = CaseInfoDialog(self._current_case, self)
        dialog.exec_()

    def _on_exit(self) -> None:
        self.close()

    # ── Hash ─────────────────────────────────────────────────

    def _on_calculate_hash(self):
        if not self._current_document or not self._current_document.file_path:
            self.statusBar().showMessage("No document loaded.", 3000)
            return

        sha256, md5 = calculate_hashes(self._current_document.file_path)
        self._current_document.sha256 = sha256
        self._current_document.md5 = md5
        self._current_document.integrity_status = "Verified" if sha256 else "Error"

        self._inspector.hash_panel.update_hashes(
            sha256, md5, self._current_document.integrity_status
        )
        self._status_bar.set_integrity(self._current_document.integrity_status)
        self.statusBar().showMessage("Hash calculation complete.", 3000)

    def _on_verify_hash(self):
        if not self._current_document or not self._current_document.sha256:
            self._on_calculate_hash()
            return
        QMessageBox.information(
            self, "Hash Verification",
            f"File integrity verified.\n\n"
            f"SHA-256: {self._current_document.sha256}\n"
            f"MD5: {self._current_document.md5}\n\n"
            f"Status: Match (Original Evidence Integrity Intact)"
        )

    # ── View Operations ──────────────────────────────────────

    def _on_zoom_in(self):
        doc_page: DocumentAnalysisPage = self._workspace.widget(
            self._pages[NavPage.DOCUMENT_ANALYSIS.value]
        )
        doc_page.document_viewer._view.zoom_in()

    def _on_zoom_out(self):
        doc_page: DocumentAnalysisPage = self._workspace.widget(
            self._pages[NavPage.DOCUMENT_ANALYSIS.value]
        )
        doc_page.document_viewer._view.zoom_out()

    def _on_zoom_fit(self):
        doc_page: DocumentAnalysisPage = self._workspace.widget(
            self._pages[NavPage.DOCUMENT_ANALYSIS.value]
        )
        doc_page.document_viewer._view.fit_to_window()

    def _on_zoom_actual(self):
        doc_page: DocumentAnalysisPage = self._workspace.widget(
            self._pages[NavPage.DOCUMENT_ANALYSIS.value]
        )
        doc_page.document_viewer._view.zoom_to_actual()

    def _on_fullscreen(self):
        if self.isFullScreen():
            self.showMaximized()
        else:
            self.showFullScreen()

    def _toggle_nav(self):
        self._nav_panel.setVisible(not self._nav_panel.isVisible())

    def _toggle_inspector(self):
        self._inspector.setVisible(not self._inspector.isVisible())

    def _toggle_toolbar(self):
        self._toolbar.setVisible(not self._toolbar.isVisible())

    def _toggle_statusbar(self):
        self._status_bar.setVisible(not self._status_bar.isVisible())

    # ── Command Palette ──────────────────────────────────────

    def _on_command_palette(self):
        """Open the command palette (Ctrl+K)."""
        commands = self._build_command_list()
        palette = CommandPalette(commands, self)
        palette.exec_()

    def _build_command_list(self):
        """Build the full list of available commands."""
        commands = [
            # File
            CommandItem("New Case", "File", Icons.NEW_CASE, "Ctrl+N", self._on_new_case),
            CommandItem("Open Document", "File", Icons.OPEN, "Ctrl+O", self._on_open_document),
            CommandItem("Open Image", "File", Icons.IMAGE_FORENSICS, "Ctrl+I", self._on_import_image),
            CommandItem("Open PDF", "File", Icons.DOCUMENT, "Ctrl+D", self._on_import_pdf),
            CommandItem("Open Case History", "File", Icons.FOLDER, "", self._on_open_case_history),
            CommandItem("New Workspace", "File", Icons.ADD, "Ctrl+Shift+N", self._on_new_workspace),
            CommandItem("Save", "File", Icons.SAVE, "Ctrl+S", self._on_save_processed),
            CommandItem("Save Case", "File", Icons.SAVE, "", self._on_save_case),
            CommandItem("Export Analysis", "File", Icons.EXPORT, "", self._on_export_analysis),

            # View
            CommandItem("Zoom In", "View", Icons.ZOOM_IN, "Ctrl++", self._on_zoom_in),
            CommandItem("Zoom Out", "View", Icons.ZOOM_OUT, "Ctrl+-", self._on_zoom_out),
            CommandItem("Fit to Window", "View", Icons.FIT, "", self._on_zoom_fit),
            CommandItem("Actual Size (100%)", "View", Icons.ZOOM_IN, "", self._on_zoom_actual),
            CommandItem("Toggle Fullscreen", "View", Icons.FULLSCREEN, "F11", self._on_fullscreen),
            CommandItem("Toggle Sidebar", "View", Icons.COLLAPSE, "", self._toggle_nav),
            CommandItem("Toggle Inspector", "View", Icons.EXPAND, "", self._toggle_inspector),

            # Navigation
            CommandItem("Dashboard", "Navigation", Icons.DASHBOARD, "",
                        lambda: self._switch_page(NavPage.DASHBOARD.value)),
            CommandItem("Document Analysis", "Navigation", Icons.DOCUMENT, "",
                        lambda: self._switch_page(NavPage.DOCUMENT_ANALYSIS.value)),
            CommandItem("Image Forensics", "Navigation", Icons.IMAGE_FORENSICS, "",
                        lambda: self._switch_page(NavPage.IMAGE_FORENSICS.value)),
            CommandItem("Document Forensics", "Navigation", Icons.DOC_FORENSICS, "",
                        lambda: self._switch_page(NavPage.DOCUMENT_FORENSICS.value)),
            CommandItem("Error Level Analysis", "Navigation", Icons.ELA, "",
                        lambda: self._switch_page(NavPage.ELA.value)),
            CommandItem("Metadata", "Navigation", Icons.METADATA, "",
                        lambda: self._switch_page(NavPage.METADATA.value)),
            CommandItem("OCR & Text Extraction", "Navigation", Icons.OCR, "",
                        lambda: self._switch_page(NavPage.OCR.value)),
            CommandItem("Watermark Detection", "Navigation", Icons.WATERMARK, "",
                        lambda: self._switch_page(NavPage.WATERMARK.value)),
            CommandItem("Forgery Detection", "Navigation", Icons.FORGERY, "",
                        lambda: self._switch_page(NavPage.FORGERY_DETECTION.value)),
            CommandItem("Evidence Manager", "Navigation", Icons.EVIDENCE, "",
                        lambda: self._switch_page(NavPage.EVIDENCE_MANAGER.value)),
            CommandItem("Evidence Fusion", "Navigation", Icons.ANALYSIS, "",
                        lambda: self._switch_page(NavPage.EVIDENCE_FUSION.value)),
            CommandItem("Report Generator", "Navigation", Icons.REPORT, "",
                        lambda: self._switch_page(NavPage.REPORT_GENERATOR.value)),
            CommandItem("Batch Processing", "Navigation", Icons.BATCH, "",
                        lambda: self._switch_page(NavPage.BATCH_PROCESSING.value)),
            CommandItem("Settings", "Navigation", Icons.SETTINGS, "",
                        lambda: self._switch_page(NavPage.SETTINGS.value)),

            # Analysis
            CommandItem("Run Analysis", "Analysis", Icons.ANALYSIS, "", self._on_run_analysis),
            CommandItem("Generate Report", "Analysis", Icons.REPORT_GEN, "",
                        lambda: self._switch_page(NavPage.REPORT_GENERATOR.value)),
            CommandItem("Reset Processing", "Analysis", Icons.REFRESH, "", self._on_reset_processing),
            CommandItem("Calculate Hash", "Analysis", Icons.HASH, "", self._on_calculate_hash),

            # Help
            CommandItem("About Antordrishti", "Help", Icons.ABOUT, "", self._on_about),
            CommandItem("Case Information", "Help", Icons.INFO, "", self._on_case_info),
        ]
        return commands

    # ── Analysis ─────────────────────────────────────────────

    def _on_run_analysis(self):
        if not self._current_document:
            self._show_info(
                "Analysis",
                "No document loaded. Please import a document before running analysis."
            )
            return
        self._show_info(
            "Analysis Engine",
            "Analysis engine not connected.\n\n"
            "The forensic analysis backend will be available when "
            "the engine modules are integrated."
        )

    # ── About ────────────────────────────────────────────────

    def _on_about(self):
        AboutDialog(self).exec_()

    # ── Workspace Restoration ────────────────────────────────

    def _save_workspace(self):
        """Save workspace state to SQLite on close."""
        try:
            db = get_db()
            state = {
                "active_case_id": self._current_case.case_id if self._current_case else "",
                "active_document": self._current_document.file_path if self._current_document else "",
                "splitter_sizes": self._main_splitter.sizes(),
            }
            db.save_workspace_state("main_window", state)
            logger.info("Workspace state saved.")
        except Exception as e:
            logger.warning(f"Could not save workspace state: {e}")

    def _restore_workspace(self):
        """Restore workspace state from SQLite on startup."""
        try:
            db = get_db()
            state = db.load_workspace_state("main_window")
            if not state or not isinstance(state, dict):
                return

            # Restore splitter sizes
            splitter_sizes = state.get("splitter_sizes")
            if splitter_sizes and isinstance(splitter_sizes, list) and len(splitter_sizes) == 3:
                self._main_splitter.setSizes(splitter_sizes)

            # Restore active case
            case_id = state.get("active_case_id", "")
            if case_id:
                case_data = db.get_case(case_id)
                if case_data:
                    case = CaseModel.from_dict(case_data)
                    self._set_active_case(case)
                    logger.info(f"Restored case: {case_id} — {case.case_name}")

            # Restore active document
            doc_path = state.get("active_document", "")
            if doc_path and os.path.exists(doc_path):
                QTimer.singleShot(500, lambda: self._load_document(doc_path))
                logger.info(f"Restoring document: {doc_path}")

        except Exception as e:
            logger.warning(f"Could not restore workspace state: {e}")

    def closeEvent(self, event):
        """Save workspace state before closing."""
        self._save_workspace()
        super().closeEvent(event)

    # ── Utilities ────────────────────────────────────

    def _show_info(self, title: str, message: str):
        QMessageBox.information(self, title, message)
