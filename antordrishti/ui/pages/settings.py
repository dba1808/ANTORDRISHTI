"""
Antordrishti — Settings Page
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget,
    QComboBox, QSpinBox, QCheckBox, QFrame, QLineEdit, QFileDialog
)
from PyQt5.QtCore import Qt, QSettings

from app.theme import Colors, Spacing
from ui.widgets.common import SectionLabel, ActionButton, Separator, InfoRow


def _make_settings_tab(title: str, settings: list) -> QWidget:
    w = QWidget()
    layout = QVBoxLayout(w)
    layout.setContentsMargins(Spacing.XL, Spacing.MD, Spacing.XL, Spacing.MD)
    layout.setSpacing(Spacing.MD)
    layout.addWidget(SectionLabel(title))

    for item in settings:
        if item is None:
            layout.addWidget(Separator())
        elif len(item) == 2:
            label_text, widget = item
            row = QHBoxLayout()
            row.setSpacing(Spacing.MD)
            label = QLabel(label_text)
            label.setStyleSheet(f"font-size: 12px; color: {Colors.TEXT_PRIMARY};")
            label.setMinimumWidth(160)
            row.addWidget(label)
            row.addWidget(widget, 1)
            layout.addLayout(row)
        else:
            label = QLabel(item[0])
            label.setStyleSheet(f"font-size: 12px; color: {Colors.TEXT_SECONDARY};")
            layout.addWidget(label)

    layout.addStretch()
    return w


class SettingsPage(QWidget):
    """Settings page with tabbed sections."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        title_bar = QWidget()
        title_bar.setFixedHeight(36)
        title_bar.setStyleSheet(f"""
            background-color: {Colors.PANEL};
            border-bottom: 1px solid {Colors.BORDER_LIGHT};
        """)
        tb = QHBoxLayout(title_bar)
        tb.setContentsMargins(Spacing.MD, 0, Spacing.MD, 0)
        t = QLabel("Settings")
        t.setProperty("heading", True)
        tb.addWidget(t)
        tb.addStretch()
        layout.addWidget(title_bar)

        tabs = QTabWidget()

        # General
        lang_combo = QComboBox()
        lang_combo.addItems(["English", "Bengali", "Hindi"])
        auto_save = QCheckBox("Enable auto-save")
        auto_save.setChecked(True)
        save_interval = QSpinBox()
        save_interval.setRange(1, 60)
        save_interval.setValue(5)
        save_interval.setSuffix(" min")
        tabs.addTab(_make_settings_tab("General", [
            ("Language", lang_combo),
            ("Auto-save", auto_save),
            ("Save Interval", save_interval),
            None,
            ("Default Working Directory",
             QLineEdit("C:/Users/Documents/Antordrishti")),
        ]), "General")

        # Appearance
        theme = QComboBox()
        theme.addItems(["Light"])
        accent = QComboBox()
        accent.addItems(["Blue / Teal", "Blue", "Teal", "Gray"])
        font_size = QComboBox()
        font_size.addItems(["Small", "Medium", "Large"])
        font_size.setCurrentIndex(1)
        tabs.addTab(_make_settings_tab("Appearance", [
            ("Theme", theme),
            ("Accent Color", accent),
            ("Font Size", font_size),
        ]), "Appearance")

        # Workspace
        tabs.addTab(_make_settings_tab("Workspace", [
            ("Default Layout", QComboBox()),
            ("Remember Window Position", QCheckBox("Enabled")),
            ("Show Navigation Panel", QCheckBox("Enabled")),
            ("Show Inspector Panel", QCheckBox("Enabled")),
        ]), "Workspace")

        # Document Viewer
        tabs.addTab(_make_settings_tab("Document Viewer", [
            ("Default Zoom", QComboBox()),
            ("Background Color", QComboBox()),
            ("Rendering Quality", QComboBox()),
            ("PDF Resolution DPI", QSpinBox()),
        ]), "Document Viewer")

        # Analysis
        self._settings = QSettings("Antordrishti", "Antordrishti")
        self._tesseract_path = QLineEdit(
            str(self._settings.value("ocr/tesseract_path", ""))
        )
        browse_tess = ActionButton("Browse...")
        browse_tess.clicked.connect(self._browse_tesseract)
        tess_row = QWidget()
        tess_layout = QHBoxLayout(tess_row)
        tess_layout.setContentsMargins(0, 0, 0, 0)
        tess_layout.setSpacing(6)
        tess_layout.addWidget(self._tesseract_path, 1)
        tess_layout.addWidget(browse_tess)
        self._tesseract_path.editingFinished.connect(self._save_tesseract_path)

        tabs.addTab(_make_settings_tab("Analysis", [
            ("Default ELA Quality", QSpinBox()),
            ("Default Analysis Profile", QComboBox()),
            ("Auto-hash on Import", QCheckBox("Enabled")),
            None,
            ("Tesseract Executable", tess_row),
        ]), "Analysis")

        # Evidence
        tabs.addTab(_make_settings_tab("Evidence", [
            ("Evidence Storage", QLineEdit()),
            ("Auto-verify Integrity", QCheckBox("Enabled")),
            ("Preserve Originals", QCheckBox("Enabled")),
        ]), "Evidence")

        # Reports
        tabs.addTab(_make_settings_tab("Reports", [
            ("Default Report Format", QComboBox()),
            ("Include Examiner Signature", QCheckBox("Enabled")),
            ("Include Audit Trail", QCheckBox("Enabled")),
        ]), "Reports")

        # Shortcuts
        tabs.addTab(_make_settings_tab("Shortcuts", [
            ("New Case", QLabel("Ctrl+N")),
            ("Open Document", QLabel("Ctrl+O")),
            ("Save", QLabel("Ctrl+S")),
            ("Run Analysis", QLabel("Ctrl+Shift+A")),
            ("Generate Report", QLabel("Ctrl+Shift+R")),
            ("Full Screen", QLabel("F11")),
        ]), "Shortcuts")

        # Performance
        tabs.addTab(_make_settings_tab("Performance", [
            ("Max Threads", QSpinBox()),
            ("GPU Acceleration", QCheckBox("Enabled")),
            ("Cache Size (MB)", QSpinBox()),
        ]), "Performance")

        layout.addWidget(tabs, 1)

    def _browse_tesseract(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Tesseract Executable",
            "",
            "Executable (*.exe);;All Files (*.*)",
        )
        if path:
            self._tesseract_path.setText(path)
            self._save_tesseract_path()

    def _save_tesseract_path(self):
        self._settings.setValue("ocr/tesseract_path", self._tesseract_path.text().strip())
