"""
Antordrishti Theme Configuration
Centralized color palette, font configuration, and spacing constants.
Light / White Forensic Workstation Aesthetic with Restrained Gold Accents.
"""


class Colors:
    """Application color palette — professional light forensic theme."""

    # Backgrounds
    BACKGROUND = "#F8FAFC"
    CANVAS = "#F8FAFC"
    PANEL = "#FFFFFF"
    PANEL_ALT = "#F1F5F9"
    HOVER = "#F1F5F9"
    SELECTED = "#FAF4E6"
    PRESSED = "#F5EACB"

    # Borders & Separators (Subtle & clean, eliminating harsh 2px black boxes)
    BORDER = "#E2E8F0"
    BORDER_LIGHT = "#F1F5F9"
    BORDER_DARK = "#CBD5E1"
    BORDER_FOCUS = "#B08D3A"
    SEPARATOR = "#E2E8F0"

    # Text (Dark Charcoal hierarchy)
    TEXT_PRIMARY = "#0F172A"
    TEXT_SECONDARY = "#475569"
    TEXT_TERTIARY = "#94A3B8"
    TEXT_DISABLED = "#CBD5E1"
    TEXT_INVERSE = "#FFFFFF"

    # Restrained Forensic Gold Accent System
    ACCENT = "#B08D3A"
    ACCENT_GOLD = "#B08D3A"
    ACCENT_HOVER = "#9E7B2F"
    ACCENT_LIGHT = "#FAF4E6"
    ACCENT_SUBTLE = "#F5EACB"
    ACCENT_DARK = "#785F23"

    # Navigation
    NAV_INDICATOR = "#B08D3A"
    NAV_SELECTED_BG = "#FAF4E6"

    # Status Indicators (Forensic Precision)
    SUCCESS = "#16A34A"
    SUCCESS_LIGHT = "#DCFCE7"
    WARNING = "#D97706"
    WARNING_LIGHT = "#FEF3C7"
    ERROR = "#DC2626"
    ERROR_LIGHT = "#FEE2E2"
    INFO = "#2563EB"
    INFO_LIGHT = "#EFF6FF"

    # Evidence States
    EVIDENCE_ORIGINAL = "#2563EB"
    EVIDENCE_WORKING = "#D97706"
    EVIDENCE_FINDING = "#DC2626"
    EVIDENCE_VERIFIED = "#16A34A"

    # Toolbar & Menus
    TOOLBAR_BG = "#FFFFFF"
    TOOLBAR_BORDER = "#E2E8F0"

    # Status Bar
    STATUSBAR_BG = "#F8FAFC"
    STATUSBAR_BORDER = "#E2E8F0"

    # Backward compatibility aliases
    ACCENT_TEAL = "#B08D3A"
    ACCENT_TEAL_LIGHT = "#FAF4E6"


class Fonts:
    """Font configuration."""

    FAMILY = "Segoe UI"
    FALLBACK = "Arial"
    FAMILY_MONO = "Consolas"
    FALLBACK_MONO = "Courier New"

    # Sizes (px)
    SIZE_TITLE = 18
    SIZE_HEADING = 14
    SIZE_SUBHEADING = 13
    SIZE_BODY = 12
    SIZE_SMALL = 11
    SIZE_TINY = 10

    # Weights
    WEIGHT_NORMAL = "normal"
    WEIGHT_MEDIUM = "500"
    WEIGHT_SEMIBOLD = "600"
    WEIGHT_BOLD = "bold"


class Spacing:
    """Consistent spacing values (px)."""

    XXS = 2
    XS = 4
    SM = 8
    MD = 12
    LG = 16
    XL = 20
    XXL = 24
    XXXL = 32

    # Specific contexts
    PANEL_PADDING = 14
    SECTION_GAP = 16
    WIDGET_GAP = 8
    TOOLBAR_PADDING = 4
    STATUS_PADDING = 6


class Sizes:
    """Widget and icon sizing."""

    # Icons
    ICON_SM = 16
    ICON_MD = 18
    ICON_LG = 22
    ICON_XL = 28

    # Toolbar
    TOOLBAR_HEIGHT = 42
    TOOLBAR_ICON = 18

    # Navigation
    NAV_WIDTH = 230
    NAV_ITEM_HEIGHT = 38
    NAV_INDICATOR_WIDTH = 3

    # Inspector
    INSPECTOR_WIDTH = 260

    # Buttons
    BUTTON_HEIGHT = 30
    BUTTON_HEIGHT_SM = 26
    BUTTON_RADIUS = 4

    # Inputs
    INPUT_HEIGHT = 30
    COMBO_HEIGHT = 30

    # Scrollbar
    SCROLLBAR_WIDTH = 8

    # Status bar
    STATUSBAR_HEIGHT = 28


class Bg:
    WHITE = "#FFFFFF"
    PRIMARY = "#F8FAFC"
    SECONDARY = "#F1F5F9"
    INPUT = "#FFFFFF"
    CARD = "#FFFFFF"
    HOVER = "#F1F5F9"
    SELECTED = "#FAF4E6"


class Border:
    DEFAULT = "#E2E8F0"
    SUBTLE = "#F1F5F9"
    LIGHT = "#F1F5F9"
    DARK = "#CBD5E1"
    FOCUS = "#B08D3A"
    HOVER = "#B08D3A"


class Text:
    PRIMARY = "#0F172A"
    SECONDARY = "#475569"
    MUTED = "#94A3B8"
    TERTIARY = "#94A3B8"
    INVERSE = "#FFFFFF"


class Brand:
    GOLD = "#B08D3A"
    GOLD_LIGHT = "#FAF4E6"
    GOLD_HOVER = "#9E7B2F"
    GOLD_DARK = "#785F23"
