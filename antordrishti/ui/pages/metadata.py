"""
Antordrishti — Metadata Sanitization Page
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QScrollArea, QMessageBox
)
from PyQt5.QtCore import Qt

from app.theme import Colors, Spacing
from ui.widgets.common import (
    SectionLabel, ActionButton, EngineNotConnectedWidget, Separator
)


class _MetadataTable(QTableWidget):
    """Metadata key-value table."""

    def __init__(self, headers=None, parent=None):
        super().__init__(parent)
        if headers is None:
            headers = ["Property", "Value"]
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.verticalHeader().setVisible(False)
        self.setAlternatingRowColors(True)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.setSelectionBehavior(QTableWidget.SelectRows)


class MetadataPage(QWidget):
    """Metadata sanitization page."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Title
        title_bar = QWidget()
        title_bar.setFixedHeight(36)
        title_bar.setStyleSheet(f"""
            background-color: {Colors.PANEL};
            border-bottom: 1px solid {Colors.BORDER_LIGHT};
        """)
        tb_layout = QHBoxLayout(title_bar)
        tb_layout.setContentsMargins(Spacing.MD, 0, Spacing.MD, 0)
        title = QLabel("Metadata Sanitization")
        title.setProperty("heading", True)
        tb_layout.addWidget(title)
        tb_layout.addStretch()
        layout.addWidget(title_bar)

        # Content
        content = QHBoxLayout()
        content.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        content.setSpacing(Spacing.MD)

        # Left: Metadata tabs
        tabs = QTabWidget()

        for tab_name in ["EXIF", "XMP", "IPTC", "PDF Metadata", "Software Info"]:
            table = _MetadataTable()
            # Placeholder rows
            placeholder_data = [
                ("Status", "No document loaded"),
            ]
            table.setRowCount(len(placeholder_data))
            for row, (key, val) in enumerate(placeholder_data):
                table.setItem(row, 0, QTableWidgetItem(key))
                table.setItem(row, 1, QTableWidgetItem(val))
            tabs.addTab(table, tab_name)

        content.addWidget(tabs, 1)

        # Right: Actions
        actions_panel = QFrame()
        actions_panel.setFixedWidth(220)
        actions_panel.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.PANEL};
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
            }}
        """)
        act_layout = QVBoxLayout(actions_panel)
        act_layout.setContentsMargins(Spacing.MD, Spacing.MD,
                                      Spacing.MD, Spacing.MD)
        act_layout.setSpacing(Spacing.SM)

        act_layout.addWidget(SectionLabel("Actions"))
        act_layout.addWidget(ActionButton("View Metadata", primary=True))
        act_layout.addWidget(ActionButton("Detect Anomalies"))
        act_layout.addWidget(ActionButton("Sanitize Metadata"))
        act_layout.addWidget(ActionButton("Export Metadata Report"))
        act_layout.addWidget(Separator())

        # Warning
        warn = QLabel(
            "⚠ Sanitization creates a new output file. "
            "Original evidence remains unchanged."
        )
        warn.setWordWrap(True)
        warn.setStyleSheet(f"""
            font-size: 10px; color: {Colors.WARNING};
            padding: 8px;
            background-color: {Colors.WARNING_LIGHT};
            border: 1px solid {Colors.WARNING};
            border-radius: 4px;
        """)
        act_layout.addWidget(warn)

        act_layout.addStretch()
        content.addWidget(actions_panel)

        layout.addLayout(content, 1)
