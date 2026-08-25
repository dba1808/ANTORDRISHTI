"""
Antordrishti — Application Package
Application setup, constants, resource management, and theming.
"""

from app.application import AntordrishtiApp
from app.constants import (
    APP_TITLE,
    APP_VERSION,
    APP_ORGANIZATION,
    NavPage,
    AppStatus,
)
from app.resources import get_icon, get_accent_icon, get_nav_icon, Icons, load_stylesheet
from app.theme import Colors, Fonts, Sizes, Spacing

__all__ = [
    "AntordrishtiApp",
    "APP_TITLE",
    "APP_VERSION",
    "APP_ORGANIZATION",
    "NavPage",
    "AppStatus",
    "get_icon",
    "get_accent_icon",
    "get_nav_icon",
    "Icons",
    "load_stylesheet",
    "Colors",
    "Fonts",
    "Sizes",
    "Spacing",
]
