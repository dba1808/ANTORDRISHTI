"""
Antordrishti — Command Palette (Ctrl+K)
Searchable command overlay with fuzzy filtering and keyboard navigation.
"""

from typing import List, Tuple, Callable, Optional

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QWidget, QApplication
)
from PyQt5.QtCore import Qt, QSize, QEvent
from PyQt5.QtGui import QFont, QCursor, QKeyEvent, QIcon

from app.theme import Colors, Spacing
from app.resources import get_icon, Icons


class CommandItem:
    """Represents a single command in the palette."""

    def __init__(self, name: str, category: str, icon_name: str,
                 shortcut: str = "", callback: Optional[Callable] = None):
        self.name = name
        self.category = category
        self.icon_name = icon_name
        self.shortcut = shortcut
        self.callback = callback


class CommandPalette(QDialog):
    """Professional command palette overlay with search and keyboard nav."""

    def __init__(self, commands: List[CommandItem], parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Dialog
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)

        self._commands = commands
        self._filtered = list(commands)

        # Size and position
        self.setFixedWidth(520)
        self.setMinimumHeight(100)
        self.setMaximumHeight(480)

        self._build_ui()
        self._populate_list(self._commands)

        # Center on parent
        if parent:
            pg = parent.geometry()
            self.move(
                pg.x() + (pg.width() - self.width()) // 2,
                pg.y() + int(pg.height() * 0.2)
            )

    def _build_ui(self):
        """Build the palette UI."""
        # Outer layout with translucent backdrop
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        # Main container
        container = QWidget()
        container.setObjectName("commandPaletteContainer")
        container.setStyleSheet(f"""
            #commandPaletteContainer {{
                background-color: {Colors.PANEL};
                border: 1px solid {Colors.BORDER};
                border-radius: 10px;
            }}
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # Search bar
        search_row = QWidget()
        search_row.setStyleSheet(f"""
            background-color: {Colors.PANEL};
            border-bottom: 1px solid {Colors.BORDER_LIGHT};
            border-top-left-radius: 10px;
            border-top-right-radius: 10px;
        """)
        search_layout = QHBoxLayout(search_row)
        search_layout.setContentsMargins(14, 10, 14, 10)
        search_layout.setSpacing(8)

        # Search icon
        search_icon = QLabel()
        search_icon.setPixmap(
            get_icon(Icons.SEARCH, "#94A3B8").pixmap(QSize(18, 18))
        )
        search_layout.addWidget(search_icon)

        # Search input
        self._search = QLineEdit()
        self._search.setPlaceholderText("Type a command...")
        self._search.setStyleSheet(f"""
            QLineEdit {{
                background: transparent;
                border: none;
                font-size: 14px;
                color: {Colors.TEXT_PRIMARY};
                padding: 4px 0;
            }}
            QLineEdit::placeholder {{
                color: {Colors.TEXT_TERTIARY};
            }}
        """)
        self._search.textChanged.connect(self._on_search)
        self._search.installEventFilter(self)
        search_layout.addWidget(self._search)

        # ESC hint
        esc_label = QLabel("ESC")
        esc_label.setStyleSheet(f"""
            background-color: #F1F5F9;
            color: {Colors.TEXT_TERTIARY};
            font-size: 10px;
            font-weight: 600;
            padding: 2px 6px;
            border-radius: 3px;
            border: 1px solid {Colors.BORDER_LIGHT};
        """)
        search_layout.addWidget(esc_label)

        container_layout.addWidget(search_row)

        # Results list
        self._list = QListWidget()
        self._list.setStyleSheet(f"""
            QListWidget {{
                background-color: {Colors.PANEL};
                border: none;
                border-bottom-left-radius: 10px;
                border-bottom-right-radius: 10px;
                outline: none;
                padding: 4px 0;
            }}
            QListWidget::item {{
                padding: 8px 16px;
                border: none;
                color: {Colors.TEXT_PRIMARY};
                font-size: 13px;
            }}
            QListWidget::item:hover {{
                background-color: {Colors.HOVER};
            }}
            QListWidget::item:selected {{
                background-color: {Colors.ACCENT_LIGHT};
                color: {Colors.ACCENT};
            }}
        """)
        self._list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._list.itemActivated.connect(self._on_activate)
        self._list.itemDoubleClicked.connect(self._on_activate)
        container_layout.addWidget(self._list)

        outer.addWidget(container)

        # Focus search
        self._search.setFocus()

    def _populate_list(self, commands: List[CommandItem]):
        """Populate the list widget with commands."""
        self._list.clear()
        current_category = None

        for cmd in commands:
            # Category separator
            if cmd.category != current_category:
                current_category = cmd.category
                sep_item = QListWidgetItem(f"  {current_category.upper()}")
                sep_item.setFlags(Qt.ItemFlag.NoItemFlags)
                sep_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                sep_item.setForeground(Qt.GlobalColor.gray)
                sep_item.setSizeHint(QSize(0, 28))
                self._list.addItem(sep_item)

            item = QListWidgetItem()
            item.setIcon(get_icon(cmd.icon_name, "#475569"))
            display = cmd.name
            if cmd.shortcut:
                display = f"{cmd.name}    {cmd.shortcut}"
            item.setText(display)
            item.setData(Qt.ItemDataRole.UserRole, cmd)
            item.setSizeHint(QSize(0, 36))
            self._list.addItem(item)

        # Select first selectable item
        for i in range(self._list.count()):
            item = self._list.item(i)
            if item and item.flags() & Qt.ItemFlag.ItemIsSelectable:
                self._list.setCurrentItem(item)
                break

    def _on_search(self, text: str):
        """Filter commands by search text (fuzzy match)."""
        query = text.strip().lower()
        if not query:
            self._populate_list(self._commands)
            return

        filtered = []
        for cmd in self._commands:
            # Match against name and category
            if (query in cmd.name.lower() or
                    query in cmd.category.lower()):
                filtered.append(cmd)

        self._populate_list(filtered)

    def _on_activate(self, item: QListWidgetItem):
        """Execute the selected command."""
        cmd = item.data(Qt.ItemDataRole.UserRole)
        if cmd and isinstance(cmd, CommandItem) and cmd.callback:
            self.accept()
            cmd.callback()

    def eventFilter(self, obj, event):
        """Handle keyboard navigation in search field."""
        if obj == self._search and event.type() == QEvent.Type.KeyPress:
            key = event.key()
            if key == Qt.Key.Key_Escape:
                self.reject()
                return True
            elif key == Qt.Key.Key_Down:
                self._move_selection(1)
                return True
            elif key == Qt.Key.Key_Up:
                self._move_selection(-1)
                return True
            elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                current = self._list.currentItem()
                if current and current.flags() & Qt.ItemFlag.ItemIsSelectable:
                    self._on_activate(current)
                return True
        return super().eventFilter(obj, event)

    def _move_selection(self, direction: int):
        """Move list selection up or down, skipping category headers."""
        current = self._list.currentRow()
        count = self._list.count()
        if count == 0:
            return

        new_row = current + direction
        # Skip non-selectable items
        while 0 <= new_row < count:
            item = self._list.item(new_row)
            if item and item.flags() & Qt.ItemFlag.ItemIsSelectable:
                self._list.setCurrentRow(new_row)
                return
            new_row += direction

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)
