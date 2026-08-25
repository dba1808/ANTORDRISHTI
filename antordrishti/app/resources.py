"""
Antordrishti Resource Manager
Icon loading via qtawesome, resource path resolution.
"""

import os
import qtawesome as qta
from PyQt5.QtGui import QIcon, QColor
from app.theme import Colors, Sizes


_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(_BASE_DIR, "assets")
ICONS_DIR = os.path.join(ASSETS_DIR, "icons")
STYLES_DIR = os.path.join(_BASE_DIR, "styles")


def get_icon(name: str, color: str = Colors.TEXT_SECONDARY,
             size: int = Sizes.ICON_MD) -> QIcon:
    """Return a qtawesome icon with the specified color."""
    try:
        return qta.icon(name, color=color)
    except Exception:
        return QIcon()


def get_accent_icon(name: str) -> QIcon:
    """Return an icon in accent color."""
    return get_icon(name, color=Colors.ACCENT)


def get_nav_icon(name: str, selected: bool = False) -> QIcon:
    """Return a navigation icon, optionally in selected state."""
    color = Colors.NAV_INDICATOR if selected else Colors.TEXT_SECONDARY
    return get_icon(name, color=color)


# ── Centralized icon mapping ────────────────────────────────

class Icons:
    """Named icon constants using qtawesome identifiers."""

    # Navigation
    DASHBOARD = "mdi.view-dashboard-outline"
    DOCUMENT = "mdi.file-document-outline"
    ELA = "mdi.image-filter-hdr"
    METADATA = "mdi.tag-text-outline"
    OCR = "mdi.text-recognition"
    WATERMARK = "mdi.watermark"
    IMAGE_FORENSICS = "mdi.image-search-outline"
    DOC_FORENSICS = "mdi.file-search-outline"
    CAMERA = "mdi.camera-outline"
    NOISE = "mdi.waveform"
    FORGERY = "mdi.shield-search"
    EVIDENCE = "mdi.archive-outline"
    REPORT = "mdi.file-chart-outline"
    BATCH = "mdi.folder-multiple-outline"
    SETTINGS = "mdi.cog-outline"

    # Toolbar
    NEW_CASE = "mdi.briefcase-plus-outline"
    OPEN = "mdi.folder-open-outline"
    IMPORT = "mdi.application-import"
    SCAN = "mdi.scanner"
    CAMERA_CAPTURE = "mdi.camera"
    SAVE = "mdi.content-save-outline"
    COMPARE = "mdi.compare"
    REPORT_GEN = "mdi.file-chart"
    ANALYSIS = "mdi.magnify-scan"

    # Viewer
    SELECT = "mdi.cursor-default-outline"
    PAN = "mdi.hand-back-right-outline"
    ZOOM_IN = "mdi.magnify-plus-outline"
    ZOOM_OUT = "mdi.magnify-minus-outline"
    ROI = "mdi.selection"
    MEASURE = "mdi.ruler"
    ANNOTATE = "mdi.draw"
    ROTATE_CW = "mdi.rotate-right"
    ROTATE_CCW = "mdi.rotate-left"
    FIT = "mdi.fit-to-screen-outline"
    PREV_PAGE = "mdi.chevron-left"
    NEXT_PAGE = "mdi.chevron-right"
    LAYERS = "mdi.layers-outline"

    # General
    ADD = "mdi.plus"
    REMOVE = "mdi.minus"
    DELETE = "mdi.delete-outline"
    EDIT = "mdi.pencil-outline"
    SEARCH = "mdi.magnify"
    FILTER = "mdi.filter-outline"
    COPY = "mdi.content-copy"
    PASTE = "mdi.content-paste"
    UNDO = "mdi.undo"
    REDO = "mdi.redo"
    CLOSE = "mdi.close"
    CHECK = "mdi.check"
    INFO = "mdi.information-outline"
    WARNING = "mdi.alert-outline"
    ERROR = "mdi.alert-circle-outline"
    HASH = "mdi.shield-check-outline"
    LOCK = "mdi.lock-outline"
    EXPORT = "mdi.export"
    PRINT = "mdi.printer-outline"
    HELP = "mdi.help-circle-outline"
    ABOUT = "mdi.information"
    FULLSCREEN = "mdi.fullscreen"
    PLAY = "mdi.play"
    PAUSE = "mdi.pause"
    STOP = "mdi.stop"
    FOLDER = "mdi.folder-outline"
    FILE = "mdi.file-outline"
    REFRESH = "mdi.refresh"
    GRID = "mdi.grid"
    LIST = "mdi.format-list-bulleted"
    EXPAND = "mdi.chevron-down"
    COLLAPSE = "mdi.chevron-up"
    EYE = "mdi.eye-outline"
    EYE_OFF = "mdi.eye-off-outline"


def load_stylesheet() -> str:
    """Load the QSS stylesheet from the styles directory."""
    qss_path = os.path.join(STYLES_DIR, "antordrishti.qss")
    if os.path.exists(qss_path):
        with open(qss_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""
