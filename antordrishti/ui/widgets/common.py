"""
Antordrishti — Reusable Widgets
Collapsible section, status indicator, labeled slider, info row, document dropzone.
All components use a professional white/light forensic theme.
"""

from typing import Optional

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLayout, QLabel, QPushButton,
    QFrame, QSlider, QSizePolicy, QGridLayout
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QCursor

from app.theme import Colors, Fonts, Spacing
from app.resources import get_icon, Icons


class CollapsibleSection(QWidget):
    """A collapsible section with a clean light header and white content area."""

    def __init__(self, title: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._expanded = True

        self.setStyleSheet("""
            CollapsibleSection {
                background-color: #FFFFFF;
                border-bottom: 1px solid #F1F5F9;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        self._header = QPushButton(f"  {title}")
        self._header.setIcon(get_icon(Icons.EXPAND, "#334155"))
        self._header.setIconSize(QSize(14, 14))
        self._header.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._header.setStyleSheet("""
            QPushButton {
                background-color: #F8FAFC;
                border: none;
                border-bottom: 1px solid #E2E8F0;
                text-align: left;
                padding: 7px 10px;
                font-size: 11px;
                font-weight: 700;
                color: #0F172A;
                letter-spacing: 0.5px;
            }
            QPushButton:hover {
                background-color: #F1F5F9;
                color: #0D7C7C;
            }
        """)
        self._header.clicked.connect(self._toggle)
        layout.addWidget(self._header)

        # Content Container
        self._content = QWidget()
        self._content.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._content.setStyleSheet("background-color: #FFFFFF;")
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(12, 10, 12, 12)
        self._content_layout.setSpacing(8)
        layout.addWidget(self._content)

    def add_widget(self, widget: QWidget):
        """Add a widget to the content area."""
        self._content_layout.addWidget(widget)

    def add_layout(self, layout: QLayout):
        """Add a layout to the content area."""
        self._content_layout.addLayout(layout)

    def content_layout(self) -> QVBoxLayout:
        return self._content_layout

    def _toggle(self):
        self._expanded = not self._expanded
        self._content.setVisible(self._expanded)
        icon = Icons.EXPAND if self._expanded else Icons.COLLAPSE
        self._header.setIcon(get_icon(icon, "#334155"))


class StatusIndicator(QWidget):
    """A colored dot with label for status display."""

    def __init__(self, text: str = "", status: str = "ready", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: transparent;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self._dot = QLabel("●")
        self._dot.setFixedWidth(12)
        self._label = QLabel(text)
        self._label.setStyleSheet("font-size: 11px; color: #1E293B; font-weight: 600;")

        layout.addWidget(self._dot)
        layout.addWidget(self._label)
        layout.addStretch()

        self.set_status(status)

    def set_status(self, status: str):
        """Set status: 'ready', 'warning', 'error', 'pending', 'verified'."""
        color_map = {
            "ready": Colors.SUCCESS,
            "verified": Colors.SUCCESS,
            "warning": Colors.WARNING,
            "error": Colors.ERROR,
            "pending": "#64748B",
            "processing": Colors.ACCENT,
        }
        color = color_map.get(status, "#64748B")
        self._dot.setStyleSheet(f"color: {color}; font-size: 10px;")

    def set_text(self, text: str):
        self._label.setText(text)


class LabeledSlider(QWidget):
    """A clean slider with label and current value display."""

    value_changed = pyqtSignal(int)

    def __init__(self, label: str, min_val: int = 0, max_val: int = 100,
                 default: int = 50, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: transparent;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 4)
        layout.setSpacing(3)

        # Top row: label + value
        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        self._label = QLabel(label)
        self._label.setStyleSheet("font-size: 11px; color: #334155; font-weight: 600;")

        self._value_label = QLabel(str(default))
        self._value_label.setStyleSheet("font-size: 11px; color: #0D7C7C; font-weight: 700;")
        self._value_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        top.addWidget(self._label)
        top.addWidget(self._value_label)
        layout.addLayout(top)

        # Slider with clean styling
        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setMinimum(min_val)
        self._slider.setMaximum(max_val)
        self._slider.setValue(default)
        self._slider.setFixedHeight(22)
        self._slider.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 4px;
                background-color: #CBD5E1;
                border-radius: 2px;
            }
            QSlider::sub-page:horizontal {
                background-color: #0D7C7C;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background-color: #0D7C7C;
                border: 2px solid #FFFFFF;
                width: 14px;
                height: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }
            QSlider::handle:horizontal:hover {
                background-color: #0A6666;
            }
        """)
        self._slider.valueChanged.connect(self._on_change)
        layout.addWidget(self._slider)

    def _on_change(self, value: int):
        self._value_label.setText(str(value))
        self.value_changed.emit(value)

    def value(self) -> int:
        return self._slider.value()

    def set_value(self, value: int):
        self._slider.setValue(value)


class InfoRow(QWidget):
    """A key-value display row for inspector panels with high contrast."""

    def __init__(self, key: str, value: str = "—", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: transparent;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(8)

        self._key_label = QLabel(key)
        self._key_label.setStyleSheet("font-size: 11px; color: #64748B; font-weight: 500;")
        self._key_label.setMinimumWidth(85)

        self._value_label = QLabel(value)
        self._value_label.setStyleSheet("font-size: 11px; color: #0F172A; font-weight: 600;")
        self._value_label.setWordWrap(True)

        layout.addWidget(self._key_label)
        layout.addWidget(self._value_label, 1)

    def set_value(self, value: str):
        self._value_label.setText(value)

    def set_mono(self):
        """Use monospace font for hashes."""
        self._value_label.setStyleSheet(
            f"font-size: 10px; color: #0D7C7C; font-weight: 600; "
            f"font-family: '{Fonts.FAMILY_MONO}', '{Fonts.FALLBACK_MONO}';"
        )


class SectionLabel(QLabel):
    """Uppercase section label for panel headers."""

    def __init__(self, text: str, parent: Optional[QWidget] = None):
        super().__init__(text.upper(), parent)
        self.setStyleSheet("""
            font-size: 10px;
            font-weight: 700;
            color: #475569;
            letter-spacing: 0.6px;
            padding: 4px 0px;
        """)


class Separator(QFrame):
    """Horizontal line separator."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.HLine)
        self.setStyleSheet("background-color: #E2E8F0; max-height: 1px; margin: 4px 0px;")


class ActionButton(QPushButton):
    """A styled action button with crisp text contrast and states."""

    def __init__(self, text: str, primary: bool = False,
                 danger: bool = False, parent: Optional[QWidget] = None):
        super().__init__(text, parent)
        self.setFixedHeight(30)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        if primary:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #0D7C7C;
                    color: #FFFFFF;
                    border: 1px solid #0B6B6B;
                    border-radius: 4px;
                    padding: 4px 12px;
                    font-size: 12px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: #0A6666;
                }
                QPushButton:pressed {
                    background-color: #085555;
                }
            """)
        elif danger:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #FFFFFF;
                    color: #DC2626;
                    border: 1px solid #FCA5A5;
                    border-radius: 4px;
                    padding: 4px 12px;
                    font-size: 12px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: #FEF2F2;
                    border-color: #DC2626;
                }
                QPushButton:pressed {
                    background-color: #FEE2E2;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #FFFFFF;
                    color: #0F172A;
                    border: 1px solid #CBD5E1;
                    border-radius: 4px;
                    padding: 4px 12px;
                    font-size: 12px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: #F1F5F9;
                    border-color: #94A3B8;
                    color: #000000;
                }
                QPushButton:pressed {
                    background-color: #E2E8F0;
                }
            """)


class DocumentTypeCard(QFrame):
    """Interactive hover box for document type selection & opening."""

    clicked = pyqtSignal()

    def __init__(self, title: str, description: str, formats: str, icon_name: str, parent=None):
        super().__init__(parent)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFixedSize(260, 160)
        self.setStyleSheet("""
            DocumentTypeCard {
                background-color: #FFFFFF;
                border: 2px dashed #CBD5E1;
                border-radius: 8px;
                padding: 12px;
            }
            DocumentTypeCard:hover {
                background-color: #F0FDFA;
                border: 2px solid #0D9488;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(6)

        # Icon
        icon_lbl = QLabel()
        icon_lbl.setPixmap(get_icon(icon_name, "#0D7C7C", 36).pixmap(QSize(36, 36)))
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_lbl)

        # Title
        t_lbl = QLabel(title)
        t_lbl.setStyleSheet("font-size: 14px; font-weight: 700; color: #0F172A;")
        t_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(t_lbl)

        # Description
        d_lbl = QLabel(description)
        d_lbl.setStyleSheet("font-size: 11px; color: #475569;")
        d_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(d_lbl)

        # Formats badge
        f_lbl = QLabel(formats)
        f_lbl.setStyleSheet("""
            font-size: 10px; font-weight: 600;
            color: #0D7C7C;
            background-color: #E6F4F8;
            border-radius: 3px;
            padding: 2px 6px;
        """)
        f_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(f_lbl)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        else:
            super().mousePressEvent(event)


class DocumentDropZoneWidget(QWidget):
    """Spacious dual-box dropzone showing Image Document and PDF Document options."""

    open_image_clicked = pyqtSignal()
    open_pdf_clicked = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: #F8FAFC;")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)

        # Header Title
        title_box = QVBoxLayout()
        title_box.setSpacing(4)

        main_title = QLabel("Add Evidence Document")
        main_title.setStyleSheet("font-size: 18px; font-weight: 800; color: #0F172A;")
        main_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_box.addWidget(main_title)

        sub_title = QLabel("Select a document type to open or drag and drop files anywhere")
        sub_title.setStyleSheet("font-size: 12px; color: #64748B;")
        sub_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_box.addWidget(sub_title)

        layout.addLayout(title_box)

        # Dual Hover Boxes
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(24)
        cards_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Box 1: Image Document
        self.img_card = DocumentTypeCard(
            title="Image Document",
            description="Forensic questioned image",
            formats="JPG  •  PNG  •  TIFF  •  BMP",
            icon_name=Icons.IMAGE_FORENSICS
        )
        self.img_card.clicked.connect(self.open_image_clicked.emit)
        cards_layout.addWidget(self.img_card)

        # Box 2: PDF Document
        self.pdf_card = DocumentTypeCard(
            title="PDF Document",
            description="Multi-page vector or scan",
            formats="PDF Files (.pdf)",
            icon_name=Icons.DOCUMENT
        )
        self.pdf_card.clicked.connect(self.open_pdf_clicked.emit)
        cards_layout.addWidget(self.pdf_card)

        layout.addLayout(cards_layout)


class EmptyStateWidget(QWidget):
    """Placeholder widget for empty/disconnected states."""

    def __init__(self, title: str = "No Document Loaded",
                 message: str = "", icon_name: Optional[str] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: #F8FAFC;")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(Spacing.MD)

        if icon_name:
            icon_label = QLabel()
            icon_label.setPixmap(
                get_icon(icon_name, "#64748B", 48).pixmap(QSize(48, 48))
            )
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(icon_label)

        title_label = QLabel(title)
        title_label.setStyleSheet(
            "font-size: 16px; font-weight: 700; color: #0F172A;"
        )
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        if message:
            msg_label = QLabel(message)
            msg_label.setStyleSheet("font-size: 12px; color: #475569;")
            msg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            msg_label.setWordWrap(True)
            layout.addWidget(msg_label)


class EngineNotConnectedWidget(EmptyStateWidget):
    """Standard 'engine not connected' placeholder."""

    def __init__(self, engine_name: str = "Analysis", parent: Optional[QWidget] = None):
        super().__init__(
            title=f"{engine_name} Engine Not Connected",
            message=(
                "The analysis backend is not available at this stage.\n"
                "This module will be functional when the forensic engine is integrated."
            ),
            icon_name=Icons.INFO,
            parent=parent,
        )
