"""
Antordrishti Theme Configuration
Centralized color palette, font configuration, and spacing constants.
"""


class Colors:
    """Application color palette — professional light theme."""

    # Backgrounds
    BACKGROUND = "#F5F6F8"
    PANEL = "#FFFFFF"
    PANEL_ALT = "#FAFBFC"
    CANVAS = "#FFFFFF"
    HOVER = "#EDF0F4"
    SELECTED = "#E3EBF3"
    PRESSED = "#D6DEE8"

    # Borders
    BORDER = "#D9DDE3"
    BORDER_LIGHT = "#E8EAED"
    BORDER_DARK = "#BFC4CC"
    SEPARATOR = "#E0E3E8"

    # Text
    TEXT_PRIMARY = "#202124"
    TEXT_SECONDARY = "#5F6368"
    TEXT_TERTIARY = "#80868B"
    TEXT_DISABLED = "#B0B5BD"
    TEXT_INVERSE = "#FFFFFF"

    # Accent
    ACCENT = "#1A73B5"
    ACCENT_HOVER = "#155E96"
    ACCENT_LIGHT = "#E8F0F8"
    ACCENT_TEAL = "#0D7C7C"
    ACCENT_TEAL_LIGHT = "#E6F4F4"

    # Navigation
    NAV_INDICATOR = "#0D8A8A"
    NAV_SELECTED_BG = "#EFF8F8"

    # Status
    SUCCESS = "#2E7D32"
    SUCCESS_LIGHT = "#E8F5E9"
    WARNING = "#E65100"
    WARNING_LIGHT = "#FFF3E0"
    ERROR = "#C62828"
    ERROR_LIGHT = "#FFEBEE"
    INFO = "#1565C0"
    INFO_LIGHT = "#E3F2FD"

    # Evidence States
    EVIDENCE_ORIGINAL = "#1565C0"
    EVIDENCE_WORKING = "#E65100"
    EVIDENCE_FINDING = "#C62828"
    EVIDENCE_VERIFIED = "#2E7D32"

    # Toolbar
    TOOLBAR_BG = "#FFFFFF"
    TOOLBAR_BORDER = "#E0E3E8"

    # Status Bar
    STATUSBAR_BG = "#F0F1F3"
    STATUSBAR_BORDER = "#D9DDE3"


class Fonts:
    """Font configuration."""

    FAMILY = "Segoe UI"
    FALLBACK = "Arial"
    FAMILY_MONO = "Consolas"
    FALLBACK_MONO = "Courier New"

    # Sizes (px)
    SIZE_TITLE = 17
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
    PANEL_PADDING = 16
    SECTION_GAP = 20
    WIDGET_GAP = 8
    TOOLBAR_PADDING = 4
    STATUS_PADDING = 6


class Sizes:
    """Widget and icon sizing."""

    # Icons
    ICON_SM = 16
    ICON_MD = 20
    ICON_LG = 24
    ICON_XL = 32

    # Toolbar
    TOOLBAR_HEIGHT = 40
    TOOLBAR_ICON = 20

    # Navigation
    NAV_WIDTH = 220
    NAV_ITEM_HEIGHT = 36
    NAV_INDICATOR_WIDTH = 3

    # Inspector
    INSPECTOR_WIDTH = 280

    # Buttons
    BUTTON_HEIGHT = 30
    BUTTON_HEIGHT_SM = 26
    BUTTON_RADIUS = 4

    # Inputs
    INPUT_HEIGHT = 28
    COMBO_HEIGHT = 28

    # Scrollbar
    SCROLLBAR_WIDTH = 8

    # Status bar
    STATUSBAR_HEIGHT = 26
