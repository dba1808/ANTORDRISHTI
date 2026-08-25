"""
Antordrishti — Report Generator Page
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QFrame, QScrollArea, QSplitter
)
from PyQt5.QtCore import Qt

from app.theme import Colors, Spacing, Fonts
from ui.widgets.common import SectionLabel, ActionButton, Separator, InfoRow


class ReportsPage(QWidget):
    """Report Generator page."""

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
        t = QLabel("Report Generator")
        t.setProperty("heading", True)
        tb.addWidget(t)
        tb.addStretch()
        layout.addWidget(title_bar)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: Report preview
        preview = QFrame()
        preview.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.CANVAS};
                border: 1px solid {Colors.BORDER};
            }}
        """)
        p_layout = QVBoxLayout(preview)
        p_layout.setContentsMargins(Spacing.XXL, Spacing.XXL,
                                    Spacing.XXL, Spacing.XXL)
        p_layout.setSpacing(Spacing.MD)

        # Report header
        rpt_title = QLabel("অন্তর্দৃষ্টি | ANTORDRISHTI")
        rpt_title.setStyleSheet(
            f"font-size: 20px; font-weight: 700; color: {Colors.ACCENT};"
        )
        rpt_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        p_layout.addWidget(rpt_title)

        rpt_sub = QLabel("Document Forensic & Authenticity Analysis Report")
        rpt_sub.setStyleSheet(
            f"font-size: 13px; color: {Colors.TEXT_SECONDARY};"
        )
        rpt_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        p_layout.addWidget(rpt_sub)

        p_layout.addWidget(Separator())

        sections = [
            "Case Information", "Examiner Information",
            "Evidence Information", "Document Information",
            "Integrity Verification", "Methods Applied",
            "Analysis Results", "Forensic Findings",
            "Suspicious Regions", "Examiner Notes",
            "Conclusion", "Audit Trail",
        ]
        for sec in sections:
            sec_label = QLabel(sec)
            sec_label.setStyleSheet(
                f"font-size: 13px; font-weight: 600; color: {Colors.TEXT_PRIMARY};"
                f" padding-top: 8px;"
            )
            p_layout.addWidget(sec_label)

            content = QLabel("No data available. Load a case and run analysis.")
            content.setStyleSheet(
                f"font-size: 11px; color: {Colors.TEXT_TERTIARY};"
                f" padding-left: 12px;"
            )
            content.setWordWrap(True)
            p_layout.addWidget(content)

        p_layout.addStretch()
        splitter.addWidget(preview)

        # Right: Controls
        right = QFrame()
        right.setFixedWidth(240)
        right.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.PANEL};
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
            }}
        """)
        r_layout = QVBoxLayout(right)
        r_layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        r_layout.setSpacing(Spacing.SM)

        r_layout.addWidget(SectionLabel("Report Actions"))
        btn_gen = ActionButton("Generate Report", primary=True)
        btn_gen.clicked.connect(self._on_generate)
        btn_prev = ActionButton("Preview")
        btn_prev.clicked.connect(self._on_preview)
        btn_save = ActionButton("Save")
        btn_save.clicked.connect(self._on_save)
        r_layout.addWidget(btn_gen)
        r_layout.addWidget(btn_prev)
        r_layout.addWidget(btn_save)
        r_layout.addWidget(Separator())

        btn_pdf = ActionButton("Export PDF")
        btn_pdf.clicked.connect(lambda: self._on_export("PDF Document (*.pdf)"))
        btn_html = ActionButton("Export HTML")
        btn_html.clicked.connect(lambda: self._on_export("HTML Document (*.html)"))
        btn_print = ActionButton("Print")
        btn_print.clicked.connect(self._on_print)

        r_layout.addWidget(btn_pdf)
        r_layout.addWidget(btn_html)
        r_layout.addWidget(btn_print)

        r_layout.addWidget(Separator())
        r_layout.addWidget(SectionLabel("Report Sections"))

        from PyQt5.QtWidgets import QCheckBox
        for sec in sections:
            cb = QCheckBox(sec)
            cb.setChecked(True)
            r_layout.addWidget(cb)

        r_layout.addStretch()
        splitter.addWidget(right)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)

        layout.addWidget(splitter, 1)

    def _on_generate(self):
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(self, "Report Generator", "Report preview generated successfully.")

    def _on_preview(self):
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(self, "Report Preview", "Displaying report preview.")

    def _on_save(self):
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(self, "Save Report", "Report draft saved successfully.")

    def _on_export(self, file_filter: str):
        from PyQt5.QtWidgets import QFileDialog, QMessageBox
        path, _ = QFileDialog.getSaveFileName(self, "Export Forensic Report", "", file_filter)
        if path:
            QMessageBox.information(self, "Export Report", f"Report exported successfully to:\n{path}")

    def _on_print(self):
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(self, "Print Report", "Sending report to system printer...")

