"""
Antordrishti — Scanner Dialog
Full-featured scanner integration dialog with USB, IP, and Network scanner tabs.
Follows the application's forensic gold-accent theme.
"""

import os
import logging

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QPushButton, QComboBox, QLineEdit, QGroupBox,
    QListWidget, QListWidgetItem, QProgressBar, QFrame,
    QMessageBox, QFileDialog, QSizePolicy, QGridLayout,
    QSpinBox, QScrollArea, QApplication
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QTimer
from PyQt5.QtGui import QImage, QPixmap, QIcon, QFont

from app.theme import Colors, Spacing, Fonts
from app.resources import get_icon, Icons

from services.scanner_service import (
    ScannerService, ScannerDevice, ScanSettings, ScanResult,
    ScannerType, ColorMode, PaperSize, ScanSource,
    DPI_OPTIONS, get_scanner_service
)

logger = logging.getLogger("antordrishti.scanner")


# ── Reusable styled widgets ────────────────────────────────

def _styled_label(text: str, bold: bool = False, size: int = 12,
                  color: str = Colors.TEXT_PRIMARY) -> QLabel:
    """Create a consistently styled label."""
    lbl = QLabel(text)
    weight = "700" if bold else "400"
    lbl.setStyleSheet(f"font-size: {size}px; font-weight: {weight}; color: {color};")
    return lbl


def _styled_combo(items: list) -> QComboBox:
    """Create a themed combo box."""
    combo = QComboBox()
    combo.addItems(items)
    combo.setFixedHeight(32)
    combo.setStyleSheet(f"""
        QComboBox {{
            background-color: #FFFFFF;
            border: 1px solid {Colors.BORDER};
            border-radius: 4px;
            padding: 4px 10px;
            font-size: 12px;
            color: {Colors.TEXT_PRIMARY};
        }}
        QComboBox:hover {{
            border-color: {Colors.ACCENT};
        }}
        QComboBox::drop-down {{
            border: none;
            width: 24px;
        }}
        QComboBox QAbstractItemView {{
            background-color: #FFFFFF;
            border: 1px solid {Colors.BORDER};
            selection-background-color: {Colors.ACCENT_LIGHT};
            selection-color: {Colors.TEXT_PRIMARY};
        }}
    """)
    return combo


def _action_button(text: str, primary: bool = False, icon_name: str = "") -> QPushButton:
    """Create a themed action button."""
    btn = QPushButton(text)
    if icon_name:
        color = "#FFFFFF" if primary else Colors.ACCENT
        btn.setIcon(get_icon(icon_name, color))
    btn.setFixedHeight(34)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)

    if primary:
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.ACCENT};
                border: 1px solid {Colors.ACCENT_DARK};
                border-radius: 4px;
                padding: 6px 18px;
                font-size: 12px;
                font-weight: 600;
                color: #FFFFFF;
            }}
            QPushButton:hover {{
                background-color: {Colors.ACCENT_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {Colors.ACCENT_DARK};
            }}
            QPushButton:disabled {{
                background-color: {Colors.TEXT_DISABLED};
                border-color: {Colors.BORDER};
                color: #FFFFFF;
            }}
        """)
    else:
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #FFFFFF;
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
                padding: 6px 18px;
                font-size: 12px;
                font-weight: 500;
                color: {Colors.TEXT_PRIMARY};
            }}
            QPushButton:hover {{
                background-color: {Colors.HOVER};
                border-color: {Colors.ACCENT};
            }}
            QPushButton:pressed {{
                background-color: {Colors.PRESSED};
            }}
            QPushButton:disabled {{
                background-color: {Colors.PANEL_ALT};
                color: {Colors.TEXT_DISABLED};
            }}
        """)
    return btn


def _section_header(text: str) -> QLabel:
    """Create a section header label."""
    lbl = QLabel(text)
    lbl.setStyleSheet(f"""
        font-size: 9px;
        font-weight: 700;
        color: {Colors.TEXT_TERTIARY};
        letter-spacing: 0.8px;
        padding: 8px 0 4px 0;
    """)
    return lbl


def _separator() -> QFrame:
    """Create a horizontal separator."""
    sep = QFrame()
    sep.setFrameShape(QFrame.Shape.HLine)
    sep.setStyleSheet(f"background-color: {Colors.BORDER_LIGHT}; max-height: 1px; border: none;")
    return sep


# ── Scanner Dialog ──────────────────────────────────────────

class ScannerDialog(QDialog):
    """Full-featured scanner dialog with USB, IP, and Network tabs."""

    document_scanned = pyqtSignal(str)  # Emits file path of scanned document

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Acquire from Scanner — Antordrishti")
        self.setMinimumSize(780, 620)
        self.setModal(True)

        self._scanner_service = get_scanner_service()
        self._selected_device: ScannerDevice = None
        self._scan_result: ScanResult = None

        self._build_ui()
        self._connect_signals()

        # Auto-discover USB scanners on open
        QTimer.singleShot(300, self._on_refresh_usb)

    def _build_ui(self):
        """Build the complete dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Title Bar ──────────────────────────────────────────
        title_bar = QWidget()
        title_bar.setFixedHeight(56)
        title_bar.setStyleSheet(f"""
            background-color: #FFFFFF;
            border-bottom: 1px solid {Colors.BORDER};
        """)
        tb_layout = QHBoxLayout(title_bar)
        tb_layout.setContentsMargins(20, 0, 20, 0)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(get_icon(Icons.SCAN, Colors.ACCENT, 24).pixmap(24, 24))
        tb_layout.addWidget(icon_lbl)

        title_col = QVBoxLayout()
        title_col.setSpacing(1)
        title_text = _styled_label("Document Scanner", bold=True, size=15)
        title_col.addWidget(title_text)
        subtitle_text = _styled_label(
            "Acquire documents from USB, IP, or network scanners for forensic analysis",
            size=11, color=Colors.TEXT_SECONDARY
        )
        title_col.addWidget(subtitle_text)
        tb_layout.addLayout(title_col)
        tb_layout.addStretch()

        # Status indicator
        self._status_badge = QLabel("No scanner selected")
        self._status_badge.setStyleSheet(f"""
            font-size: 10px; font-weight: 600; color: {Colors.WARNING};
            background-color: {Colors.WARNING_LIGHT};
            border: 1px solid #FDE68A;
            border-radius: 10px; padding: 3px 10px;
        """)
        tb_layout.addWidget(self._status_badge)

        layout.addWidget(title_bar)

        # ── Main Content: Tabs + Settings side-by-side ─────────
        content = QWidget()
        content.setStyleSheet(f"background-color: {Colors.BACKGROUND};")
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(16, 12, 16, 12)
        content_layout.setSpacing(12)

        # Left: Scanner Type Tabs
        left_panel = QWidget()
        left_panel.setStyleSheet(f"""
            background-color: #FFFFFF;
            border: 1px solid {Colors.BORDER};
            border-radius: 6px;
        """)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        self._tab_widget = QTabWidget()
        self._tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background-color: #FFFFFF;
            }}
            QTabBar::tab {{
                background-color: {Colors.PANEL_ALT};
                border: 1px solid {Colors.BORDER};
                border-bottom: none;
                padding: 8px 16px;
                margin-right: 2px;
                font-size: 11px;
                font-weight: 600;
                color: {Colors.TEXT_SECONDARY};
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }}
            QTabBar::tab:selected {{
                background-color: #FFFFFF;
                color: {Colors.TEXT_PRIMARY};
                border-bottom: 2px solid {Colors.ACCENT};
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {Colors.HOVER};
            }}
        """)

        # USB Tab
        self._usb_tab = self._build_usb_tab()
        self._tab_widget.addTab(self._usb_tab, get_icon("mdi.usb", Colors.TEXT_SECONDARY), "USB / Standalone")

        # IP Tab
        self._ip_tab = self._build_ip_tab()
        self._tab_widget.addTab(self._ip_tab, get_icon("mdi.ip-network-outline", Colors.TEXT_SECONDARY), "IP Scanner")

        # Network Tab
        self._network_tab = self._build_network_tab()
        self._tab_widget.addTab(self._network_tab, get_icon("mdi.lan", Colors.TEXT_SECONDARY), "Network")

        left_layout.addWidget(self._tab_widget)
        content_layout.addWidget(left_panel, 3)

        # Right: Scan Settings + Preview
        right_panel = QWidget()
        right_panel.setStyleSheet(f"""
            background-color: #FFFFFF;
            border: 1px solid {Colors.BORDER};
            border-radius: 6px;
        """)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(14, 14, 14, 14)
        right_layout.setSpacing(8)

        right_layout.addWidget(_section_header("SCAN SETTINGS"))
        right_layout.addWidget(_separator())

        # DPI
        dpi_row = QHBoxLayout()
        dpi_row.addWidget(_styled_label("Resolution (DPI):", size=11))
        self._dpi_combo = _styled_combo([str(d) for d in DPI_OPTIONS])
        self._dpi_combo.setCurrentText("300")
        dpi_row.addWidget(self._dpi_combo)
        right_layout.addLayout(dpi_row)

        # Color Mode
        color_row = QHBoxLayout()
        color_row.addWidget(_styled_label("Color Mode:", size=11))
        self._color_combo = _styled_combo([m.value for m in ColorMode])
        color_row.addWidget(self._color_combo)
        right_layout.addLayout(color_row)

        # Paper Size
        paper_row = QHBoxLayout()
        paper_row.addWidget(_styled_label("Paper Size:", size=11))
        self._paper_combo = _styled_combo([p.value for p in PaperSize])
        paper_row.addWidget(self._paper_combo)
        right_layout.addLayout(paper_row)

        # Source
        source_row = QHBoxLayout()
        source_row.addWidget(_styled_label("Source:", size=11))
        self._source_combo = _styled_combo([s.value for s in ScanSource])
        source_row.addWidget(self._source_combo)
        right_layout.addLayout(source_row)

        # Output Format
        format_row = QHBoxLayout()
        format_row.addWidget(_styled_label("Output Format:", size=11))
        self._format_combo = _styled_combo(["TIFF", "PNG"])
        format_row.addWidget(self._format_combo)
        right_layout.addLayout(format_row)

        # Output Directory
        right_layout.addWidget(_separator())
        right_layout.addWidget(_section_header("OUTPUT"))

        dir_row = QHBoxLayout()
        self._output_dir_edit = QLineEdit()
        default_dir = os.path.join(os.path.expanduser("~"), ".antordrishti", "scans")
        self._output_dir_edit.setText(default_dir)
        self._output_dir_edit.setFixedHeight(30)
        self._output_dir_edit.setStyleSheet(f"""
            QLineEdit {{
                background-color: #FFFFFF;
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
                color: {Colors.TEXT_PRIMARY};
            }}
            QLineEdit:focus {{
                border-color: {Colors.ACCENT};
            }}
        """)
        dir_row.addWidget(self._output_dir_edit)

        btn_browse = _action_button("...", icon_name=Icons.FOLDER)
        btn_browse.setFixedWidth(40)
        btn_browse.clicked.connect(self._on_browse_output)
        dir_row.addWidget(btn_browse)
        right_layout.addLayout(dir_row)

        # Preview
        right_layout.addWidget(_separator())
        right_layout.addWidget(_section_header("PREVIEW"))

        self._preview_label = QLabel()
        self._preview_label.setFixedHeight(150)
        self._preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._preview_label.setStyleSheet(f"""
            background-color: {Colors.PANEL_ALT};
            border: 1px dashed {Colors.BORDER};
            border-radius: 4px;
            color: {Colors.TEXT_TERTIARY};
            font-size: 11px;
        """)
        self._preview_label.setText("Scan preview will appear here")
        right_layout.addWidget(self._preview_label)

        right_layout.addStretch()
        content_layout.addWidget(right_panel, 2)

        layout.addWidget(content, 1)

        # ── Bottom Bar: Progress + Actions ─────────────────────
        bottom_bar = QWidget()
        bottom_bar.setFixedHeight(64)
        bottom_bar.setStyleSheet(f"""
            background-color: #FFFFFF;
            border-top: 1px solid {Colors.BORDER};
        """)
        bottom_layout = QHBoxLayout(bottom_bar)
        bottom_layout.setContentsMargins(20, 8, 20, 8)
        bottom_layout.setSpacing(10)

        self._progress_bar = QProgressBar()
        self._progress_bar.setFixedHeight(8)
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(False)
        self._progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {Colors.PANEL_ALT};
                border: none;
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background-color: {Colors.ACCENT};
                border-radius: 4px;
            }}
        """)

        self._progress_label = _styled_label("Ready to scan", size=11, color=Colors.TEXT_SECONDARY)

        progress_col = QVBoxLayout()
        progress_col.setSpacing(4)
        progress_col.addWidget(self._progress_label)
        progress_col.addWidget(self._progress_bar)
        bottom_layout.addLayout(progress_col, 1)

        self._btn_cancel = _action_button("Cancel")
        self._btn_cancel.clicked.connect(self._on_cancel)
        bottom_layout.addWidget(self._btn_cancel)

        self._btn_scan = _action_button("Scan Document", primary=True, icon_name=Icons.SCAN)
        self._btn_scan.setEnabled(False)
        self._btn_scan.clicked.connect(self._on_scan)
        bottom_layout.addWidget(self._btn_scan)

        layout.addWidget(bottom_bar)

    # ── Tab Builders ────────────────────────────────────────

    def _build_usb_tab(self) -> QWidget:
        """Build USB/Standalone scanner tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        # Header
        header_row = QHBoxLayout()
        header_row.addWidget(_section_header("DETECTED USB SCANNERS"))
        header_row.addStretch()
        self._btn_refresh_usb = _action_button("Refresh", icon_name=Icons.REFRESH)
        self._btn_refresh_usb.setFixedWidth(100)
        self._btn_refresh_usb.clicked.connect(self._on_refresh_usb)
        header_row.addWidget(self._btn_refresh_usb)
        layout.addLayout(header_row)

        # Scanner list
        self._usb_list = QListWidget()
        self._usb_list.setStyleSheet(f"""
            QListWidget {{
                background-color: #FFFFFF;
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
                font-size: 12px;
                color: {Colors.TEXT_PRIMARY};
            }}
            QListWidget::item {{
                padding: 10px 12px;
                border-bottom: 1px solid {Colors.BORDER_LIGHT};
            }}
            QListWidget::item:selected {{
                background-color: {Colors.ACCENT_LIGHT};
                color: {Colors.TEXT_PRIMARY};
                border-left: 3px solid {Colors.ACCENT};
            }}
            QListWidget::item:hover:!selected {{
                background-color: {Colors.HOVER};
            }}
        """)
        self._usb_list.currentItemChanged.connect(self._on_usb_device_selected)
        layout.addWidget(self._usb_list, 1)

        # Device info
        self._usb_info = QLabel("Select a scanner to view details")
        self._usb_info.setStyleSheet(f"""
            font-size: 11px; color: {Colors.TEXT_SECONDARY};
            background-color: {Colors.PANEL_ALT};
            border: 1px solid {Colors.BORDER_LIGHT};
            border-radius: 4px;
            padding: 8px 12px;
        """)
        self._usb_info.setWordWrap(True)
        layout.addWidget(self._usb_info)

        # WIA status
        self._wia_status = QLabel()
        layout.addWidget(self._wia_status)
        self._update_wia_status()

        return tab

    def _build_ip_tab(self) -> QWidget:
        """Build IP Scanner tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        layout.addWidget(_section_header("IP SCANNER CONNECTION"))
        layout.addWidget(_styled_label(
            "Enter the IP address or hostname of your scanner. Supports eSCL (AirScan) protocol.",
            size=11, color=Colors.TEXT_SECONDARY
        ))

        # IP Address input
        ip_row = QHBoxLayout()
        ip_row.addWidget(_styled_label("IP Address:", size=11))
        self._ip_input = QLineEdit()
        self._ip_input.setPlaceholderText("e.g., 192.168.1.100")
        self._ip_input.setFixedHeight(32)
        self._ip_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: #FFFFFF;
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 12px;
                color: {Colors.TEXT_PRIMARY};
            }}
            QLineEdit:focus {{
                border-color: {Colors.ACCENT};
            }}
        """)
        ip_row.addWidget(self._ip_input, 1)
        layout.addLayout(ip_row)

        # Port input
        port_row = QHBoxLayout()
        port_row.addWidget(_styled_label("Port:", size=11))
        self._port_input = QSpinBox()
        self._port_input.setRange(1, 65535)
        self._port_input.setValue(443)
        self._port_input.setFixedHeight(32)
        self._port_input.setStyleSheet(f"""
            QSpinBox {{
                background-color: #FFFFFF;
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 12px;
                color: {Colors.TEXT_PRIMARY};
            }}
            QSpinBox:focus {{
                border-color: {Colors.ACCENT};
            }}
        """)
        port_row.addWidget(self._port_input)
        port_row.addStretch()

        self._btn_test_ip = _action_button("Test Connection", icon_name="mdi.connection")
        self._btn_test_ip.clicked.connect(self._on_test_ip)
        port_row.addWidget(self._btn_test_ip)
        layout.addLayout(port_row)

        layout.addWidget(_separator())

        # Connection result
        self._ip_status_frame = QFrame()
        self._ip_status_frame.setStyleSheet(f"""
            background-color: {Colors.PANEL_ALT};
            border: 1px solid {Colors.BORDER_LIGHT};
            border-radius: 4px;
            padding: 10px;
        """)
        ip_status_layout = QVBoxLayout(self._ip_status_frame)
        ip_status_layout.setContentsMargins(12, 8, 12, 8)
        self._ip_status_label = _styled_label("Not connected", size=11, color=Colors.TEXT_SECONDARY)
        self._ip_status_label.setWordWrap(True)
        ip_status_layout.addWidget(self._ip_status_label)
        layout.addWidget(self._ip_status_frame)

        layout.addStretch()

        # Tip
        tip = _styled_label(
            "💡 Tip: Most modern scanners support eSCL (AirScan). Check your scanner's "
            "network settings for the IP address.",
            size=10, color=Colors.TEXT_TERTIARY
        )
        tip.setWordWrap(True)
        layout.addWidget(tip)

        return tab

    def _build_network_tab(self) -> QWidget:
        """Build Network Scanner tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        # Header
        header_row = QHBoxLayout()
        header_row.addWidget(_section_header("NETWORK SCANNER DISCOVERY"))
        header_row.addStretch()
        self._btn_discover_net = _action_button("Discover Scanners", primary=True, icon_name=Icons.SEARCH)
        self._btn_discover_net.clicked.connect(self._on_discover_network)
        header_row.addWidget(self._btn_discover_net)
        layout.addLayout(header_row)

        layout.addWidget(_styled_label(
            "Search for scanners on the local network via eSCL/mDNS discovery.",
            size=11, color=Colors.TEXT_SECONDARY
        ))

        layout.addWidget(_separator())

        # Scanner list
        self._network_list = QListWidget()
        self._network_list.setStyleSheet(self._usb_list_style())
        self._network_list.currentItemChanged.connect(self._on_network_device_selected)
        layout.addWidget(self._network_list, 1)

        # Discovery status
        self._network_status = _styled_label(
            "Click 'Discover Scanners' to search the local network.",
            size=11, color=Colors.TEXT_SECONDARY
        )
        self._network_status.setWordWrap(True)
        layout.addWidget(self._network_status)

        return tab

    def _usb_list_style(self) -> str:
        return f"""
            QListWidget {{
                background-color: #FFFFFF;
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
                font-size: 12px;
                color: {Colors.TEXT_PRIMARY};
            }}
            QListWidget::item {{
                padding: 10px 12px;
                border-bottom: 1px solid {Colors.BORDER_LIGHT};
            }}
            QListWidget::item:selected {{
                background-color: {Colors.ACCENT_LIGHT};
                color: {Colors.TEXT_PRIMARY};
                border-left: 3px solid {Colors.ACCENT};
            }}
            QListWidget::item:hover:!selected {{
                background-color: {Colors.HOVER};
            }}
        """

    # ── Signal Connections ──────────────────────────────────

    def _connect_signals(self):
        """Wire scanner service signals."""
        self._scanner_service.scan_progress.connect(self._on_scan_progress)
        self._scanner_service.scan_completed.connect(self._on_scan_completed)
        self._scanner_service.scan_error.connect(self._on_scan_error)

    # ── Event Handlers ──────────────────────────────────────

    def _on_refresh_usb(self):
        """Refresh USB scanner list."""
        self._usb_list.clear()
        self._btn_refresh_usb.setEnabled(False)
        self._usb_info.setText("Scanning for USB devices...")

        QApplication.processEvents()

        devices = self._scanner_service.discover_usb_scanners()

        if devices:
            for dev in devices:
                item = QListWidgetItem(
                    get_icon(Icons.SCAN, Colors.ACCENT),
                    f"{dev.name}\n{dev.manufacturer} — {dev.model}"
                )
                item.setData(Qt.ItemDataRole.UserRole, dev)
                self._usb_list.addItem(item)
            self._usb_info.setText(f"Found {len(devices)} scanner(s)")
        else:
            self._usb_info.setText(
                "No USB scanners detected.\n"
                "Make sure your scanner is connected, powered on, and drivers are installed."
            )

        self._btn_refresh_usb.setEnabled(True)
        self._update_wia_status()

    def _on_usb_device_selected(self, current: QListWidgetItem, previous):
        """Handle USB device selection."""
        if current:
            dev: ScannerDevice = current.data(Qt.ItemDataRole.UserRole)
            self._selected_device = dev
            self._usb_info.setText(
                f"Name: {dev.name}\n"
                f"Manufacturer: {dev.manufacturer}\n"
                f"Model: {dev.model}\n"
                f"Device ID: {dev.device_id}"
            )
            self._btn_scan.setEnabled(True)
            self._update_status_badge("Scanner selected", "success")

    def _on_test_ip(self):
        """Test IP scanner connection."""
        ip = self._ip_input.text().strip()
        if not ip:
            self._ip_status_label.setText("⚠ Please enter an IP address.")
            self._ip_status_label.setStyleSheet(f"font-size: 11px; color: {Colors.WARNING};")
            return

        port = self._port_input.value()
        self._ip_status_label.setText("🔄 Testing connection...")
        self._ip_status_label.setStyleSheet(f"font-size: 11px; color: {Colors.INFO};")
        self._btn_test_ip.setEnabled(False)
        QApplication.processEvents()

        result = self._scanner_service.test_ip_scanner(ip, port)

        if result["connected"]:
            self._selected_device = ScannerDevice(
                device_id=f"ip_{ip}_{port}",
                name=result.get("name", f"IP Scanner @ {ip}"),
                scanner_type=ScannerType.IP,
                ip_address=ip,
                port=port,
                is_available=True,
                capabilities=result.get("capabilities", {}),
            )
            caps_text = ""
            if result.get("capabilities"):
                caps = result["capabilities"]
                if caps.get("color_modes"):
                    caps_text += f"\nColor modes: {', '.join(caps['color_modes'])}"
                if caps.get("resolutions"):
                    caps_text += f"\nResolutions: {', '.join(str(r) for r in caps['resolutions'])} DPI"
                if caps.get("sources"):
                    caps_text += f"\nSources: {', '.join(caps['sources'])}"

            self._ip_status_label.setText(
                f"✅ Connected to {result['name']}{caps_text}"
            )
            self._ip_status_label.setStyleSheet(f"font-size: 11px; color: {Colors.SUCCESS};")
            self._btn_scan.setEnabled(True)
            self._update_status_badge("IP Scanner connected", "success")
        else:
            self._ip_status_label.setText(
                f"❌ Connection failed: {result.get('error', 'Unknown error')}\n\n"
                "Troubleshooting:\n"
                "• Verify the scanner is on the same network\n"
                "• Check if the scanner supports eSCL (AirScan)\n"
                "• Try port 80 or 443"
            )
            self._ip_status_label.setStyleSheet(f"font-size: 11px; color: {Colors.ERROR};")

        self._btn_test_ip.setEnabled(True)

    def _on_discover_network(self):
        """Discover network scanners."""
        self._network_list.clear()
        self._network_status.setText("🔄 Discovering scanners on local network... This may take a moment.")
        self._btn_discover_net.setEnabled(False)
        QApplication.processEvents()

        devices = self._scanner_service.discover_network_scanners()

        if devices:
            for dev in devices:
                item = QListWidgetItem(
                    get_icon("mdi.lan", Colors.ACCENT),
                    f"{dev.name}\n{dev.ip_address}:{dev.port}"
                )
                item.setData(Qt.ItemDataRole.UserRole, dev)
                self._network_list.addItem(item)
            self._network_status.setText(f"Found {len(devices)} network scanner(s).")
        else:
            self._network_status.setText(
                "No network scanners found.\n"
                "Try the IP Scanner tab if you know your scanner's IP address."
            )

        self._btn_discover_net.setEnabled(True)

    def _on_network_device_selected(self, current: QListWidgetItem, previous):
        """Handle network device selection."""
        if current:
            dev: ScannerDevice = current.data(Qt.ItemDataRole.UserRole)
            self._selected_device = dev
            self._btn_scan.setEnabled(True)
            self._update_status_badge("Network scanner selected", "success")

    def _on_browse_output(self):
        """Browse for output directory."""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Output Directory", self._output_dir_edit.text()
        )
        if directory:
            self._output_dir_edit.setText(directory)

    def _on_scan(self):
        """Start scanning."""
        if self._selected_device is None:
            QMessageBox.warning(self, "No Scanner", "Please select a scanner first.")
            return

        settings = self._build_scan_settings()

        self._btn_scan.setEnabled(False)
        self._btn_cancel.setText("Cancel Scan")
        self._progress_bar.setValue(0)
        self._progress_label.setText("Starting scan...")

        self._scanner_service.start_scan(self._selected_device, settings)

    def _on_cancel(self):
        """Cancel or close dialog."""
        if self._scanner_service.is_scanning:
            self._scanner_service.cancel_scan()
            self._progress_label.setText("Scan cancelled.")
            self._btn_scan.setEnabled(True)
            self._btn_cancel.setText("Cancel")
        else:
            self.reject()

    def _on_scan_progress(self, percent: int, message: str):
        """Update scan progress."""
        self._progress_bar.setValue(percent)
        self._progress_label.setText(message)

    def _on_scan_completed(self, result: ScanResult):
        """Handle scan completion."""
        self._btn_scan.setEnabled(True)
        self._btn_cancel.setText("Close")
        self._scan_result = result

        if result.success and result.file_paths:
            self._progress_label.setText(
                f"✅ Scan complete! {result.page_count} page(s) saved."
            )
            self._progress_bar.setValue(100)
            self._update_status_badge("Scan complete", "success")

            # Show preview
            self._show_preview(result.file_paths[0])

            # Emit signal to load the scanned document
            self.document_scanned.emit(result.file_paths[0])

            QMessageBox.information(
                self, "Scan Complete",
                f"Document scanned successfully!\n\n"
                f"Scanner: {result.scanner_name}\n"
                f"Resolution: {result.dpi} DPI\n"
                f"Color: {result.color_mode}\n"
                f"Pages: {result.page_count}\n"
                f"Saved to: {result.file_paths[0]}"
            )
        else:
            self._progress_label.setText(f"❌ Scan failed: {result.error_message}")
            self._progress_bar.setValue(0)
            self._update_status_badge("Scan failed", "error")

            QMessageBox.warning(
                self, "Scan Failed",
                f"The scan operation failed.\n\n{result.error_message}"
            )

    def _on_scan_error(self, error: str):
        """Handle scan error."""
        self._progress_label.setText(f"❌ Error: {error}")
        self._btn_scan.setEnabled(True)
        self._btn_cancel.setText("Close")
        self._update_status_badge("Error", "error")

    # ── Helpers ─────────────────────────────────────────────

    def _build_scan_settings(self) -> ScanSettings:
        """Build ScanSettings from current UI state."""
        dpi = int(self._dpi_combo.currentText())
        color_text = self._color_combo.currentText()
        color_mode = next((m for m in ColorMode if m.value == color_text), ColorMode.COLOR)
        paper_text = self._paper_combo.currentText()
        paper_size = next((p for p in PaperSize if p.value == paper_text), PaperSize.A4)
        source_text = self._source_combo.currentText()
        source = next((s for s in ScanSource if s.value == source_text), ScanSource.FLATBED)

        return ScanSettings(
            dpi=dpi,
            color_mode=color_mode,
            paper_size=paper_size,
            source=source,
            output_format=self._format_combo.currentText(),
            output_dir=self._output_dir_edit.text(),
        )

    def _update_wia_status(self):
        """Update WIA availability status indicator."""
        if self._scanner_service.wia_available:
            self._wia_status.setText("✅ WIA (Windows Image Acquisition) is available")
            self._wia_status.setStyleSheet(f"font-size: 10px; color: {Colors.SUCCESS}; padding: 4px;")
        else:
            self._wia_status.setText(
                "⚠ WIA not available — install scanner drivers or use IP/Network tab"
            )
            self._wia_status.setStyleSheet(f"font-size: 10px; color: {Colors.WARNING}; padding: 4px;")

    def _update_status_badge(self, text: str, status: str = "info"):
        """Update the title bar status badge."""
        color_map = {
            "success": (Colors.SUCCESS, Colors.SUCCESS_LIGHT, "#BBF7D0"),
            "error": (Colors.ERROR, Colors.ERROR_LIGHT, "#FECACA"),
            "warning": (Colors.WARNING, Colors.WARNING_LIGHT, "#FDE68A"),
            "info": (Colors.INFO, Colors.INFO_LIGHT, "#BFDBFE"),
        }
        text_color, bg_color, border_color = color_map.get(status, color_map["info"])
        self._status_badge.setText(text)
        self._status_badge.setStyleSheet(f"""
            font-size: 10px; font-weight: 600; color: {text_color};
            background-color: {bg_color};
            border: 1px solid {border_color};
            border-radius: 10px; padding: 3px 10px;
        """)

    def _show_preview(self, file_path: str):
        """Show a preview of the scanned image."""
        try:
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(
                    self._preview_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self._preview_label.setPixmap(scaled)
            else:
                self._preview_label.setText("Preview not available")
        except Exception:
            self._preview_label.setText("Preview not available")

    def get_scanned_file(self) -> str:
        """Return the path of the last scanned file, if any."""
        if self._scan_result and self._scan_result.file_paths:
            return self._scan_result.file_paths[0]
        return ""
