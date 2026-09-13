"""
Antordrishti — Batch Processing Page
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QFrame, QProgressBar,
    QCheckBox, QGroupBox, QGridLayout, QFileDialog
)
from PyQt5.QtCore import Qt

from app.theme import Colors, Spacing
from ui.widgets.common import SectionLabel, ActionButton, Separator


class BatchProcessingPage(QWidget):
    """Batch Processing page."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Title Bar
        title_bar = QWidget()
        title_bar.setFixedHeight(48)
        title_bar.setStyleSheet(f"""
            background-color: {Colors.CANVAS};
            border-bottom: 1px solid {Colors.BORDER_LIGHT};
        """)
        tb = QHBoxLayout(title_bar)
        tb.setContentsMargins(Spacing.LG, 0, Spacing.LG, 0)
        t = QLabel("Batch Forensic Examination")
        t.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {Colors.TEXT_PRIMARY};")
        tb.addWidget(t)
        tb.addStretch()
        layout.addWidget(title_bar)

        content = QHBoxLayout()
        content.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        content.setSpacing(Spacing.MD)

        # Left: Files table
        left = QVBoxLayout()
        left.setSpacing(Spacing.SM)

        # File controls
        file_bar = QHBoxLayout()
        file_bar.setSpacing(Spacing.SM)
        btn_add_files = ActionButton("Add Files")
        btn_add_files.clicked.connect(self._on_add_files)
        btn_add_folder = ActionButton("Add Folder")
        btn_add_folder.clicked.connect(self._on_add_folder)
        btn_remove = ActionButton("Remove")
        btn_remove.clicked.connect(self._on_remove)
        btn_clear = ActionButton("Clear")
        btn_clear.clicked.connect(self._on_clear)

        file_bar.addWidget(btn_add_files)
        file_bar.addWidget(btn_add_folder)
        file_bar.addWidget(btn_remove)
        file_bar.addWidget(btn_clear)
        file_bar.addStretch()
        left.addLayout(file_bar)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels([
            "Filename", "Type", "Size", "Status"
        ])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.Stretch
        )
        self._table.verticalHeader().setVisible(False)
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setRowCount(0)
        left.addWidget(self._table, 1)

        # Progress
        prog_layout = QVBoxLayout()
        prog_layout.setSpacing(4)

        self._overall_label = QLabel("Overall Progress: 0%")
        self._overall_label.setStyleSheet(
            f"font-size: 11px; color: {Colors.TEXT_SECONDARY};"
        )
        prog_layout.addWidget(self._overall_label)
        self._overall_bar = QProgressBar()
        self._overall_bar.setValue(0)
        prog_layout.addWidget(self._overall_bar)

        self._current_label = QLabel("Current File: —")
        self._current_label.setStyleSheet(
            f"font-size: 11px; color: {Colors.TEXT_TERTIARY};"
        )
        prog_layout.addWidget(self._current_label)

        left.addLayout(prog_layout)
        content.addLayout(left, 1)

        # Right: Analysis selection
        right = QFrame()
        right.setFixedWidth(260)
        right.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.CANVAS};
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: 8px;
            }}
        """)
        r_layout = QVBoxLayout(right)
        r_layout.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        r_layout.setSpacing(Spacing.MD)

        r_layout.addWidget(SectionLabel("Analysis Selection"))

        analyses = [
            "ELA", "Metadata", "OCR", "Compression",
            "Copy-Move", "Splicing", "Noise", "Resampling",
        ]
        for a in analyses:
            cb = QCheckBox(a)
            cb.setChecked(True)
            r_layout.addWidget(cb)

        r_layout.addWidget(Separator())
        r_layout.addWidget(SectionLabel("Controls"))
        btn_start = ActionButton("Start", primary=True)
        btn_start.clicked.connect(self._on_start)
        btn_pause = ActionButton("Pause")
        btn_cancel = ActionButton("Cancel")

        r_layout.addWidget(btn_start)
        r_layout.addWidget(btn_pause)
        r_layout.addWidget(btn_cancel)

        r_layout.addWidget(Separator())
        r_layout.addWidget(SectionLabel("Output"))

        from PyQt5.QtWidgets import QLineEdit
        out_layout = QHBoxLayout()
        self._output_path = QLineEdit()
        self._output_path.setPlaceholderText("Select output folder...")
        self._output_path.setReadOnly(True)
        out_layout.addWidget(self._output_path)
        browse_btn = ActionButton("...")
        browse_btn.setFixedWidth(30)
        browse_btn.clicked.connect(self._on_browse_output)
        out_layout.addWidget(browse_btn)
        r_layout.addLayout(out_layout)

        r_layout.addStretch()
        content.addWidget(right)

        layout.addLayout(content, 1)

    def _on_add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Files for Batch Processing", "",
            "Supported Files (*.jpg *.jpeg *.png *.tiff *.tif *.bmp *.pdf);;All Files (*.*)"
        )
        import os
        from services.file_service import format_file_size
        for f in files:
            row = self._table.rowCount()
            self._table.insertRow(row)
            fname = os.path.basename(f)
            ftype = os.path.splitext(f)[1].upper().lstrip(".")
            fsize = format_file_size(os.path.getsize(f)) if os.path.exists(f) else "—"
            self._table.setItem(row, 0, QTableWidgetItem(fname))
            self._table.setItem(row, 1, QTableWidgetItem(ftype))
            self._table.setItem(row, 2, QTableWidgetItem(fsize))
            self._table.setItem(row, 3, QTableWidgetItem("Ready"))

    def _on_add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder for Batch Processing")
        if folder:
            import os
            from services.file_service import is_supported_document, format_file_size
            for root, _, files in os.walk(folder):
                for f in files:
                    full_path = os.path.join(root, f)
                    if is_supported_document(full_path):
                        row = self._table.rowCount()
                        self._table.insertRow(row)
                        fname = f
                        ftype = os.path.splitext(f)[1].upper().lstrip(".")
                        fsize = format_file_size(os.path.getsize(full_path))
                        self._table.setItem(row, 0, QTableWidgetItem(fname))
                        self._table.setItem(row, 1, QTableWidgetItem(ftype))
                        self._table.setItem(row, 2, QTableWidgetItem(fsize))
                        self._table.setItem(row, 3, QTableWidgetItem("Ready"))

    def _on_remove(self):
        rows = sorted([item.row() for item in self._table.selectedItems()], reverse=True)
        distinct_rows = list(dict.fromkeys(rows))
        for r in distinct_rows:
            self._table.removeRow(r)

    def _on_clear(self):
        self._table.setRowCount(0)

    def _on_browse_output(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if folder:
            self._output_path.setText(folder)

    def _on_start(self):
        from PyQt5.QtWidgets import QMessageBox
        if self._table.rowCount() == 0:
            QMessageBox.information(self, "Batch Processing", "Please add files to process.")
            return
        QMessageBox.information(
            self, "Batch Processing",
            "Batch processing engine not connected.\n\n"
            "File queue is ready for processing when backend engine is integrated."
        )

