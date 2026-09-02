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
        self._current_context = None
        self._ocr_result = None
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
        self.preview = QFrame()
        self.preview.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.CANVAS};
                border: 2px solid #2B2B2B;
                border-radius: 4px;
            }}
        """)
        p_layout = QVBoxLayout(self.preview)
        p_layout.setContentsMargins(Spacing.XXL, Spacing.XXL,
                                    Spacing.XXL, Spacing.XXL)
        p_layout.setSpacing(Spacing.MD)

        # Report header
        rpt_title = QLabel("অন্তর্দৃষ্টি | ANTORDRISHTI")
        rpt_title.setStyleSheet("font-size: 20px; font-weight: 700; color: #B08D3A; border: none;")
        rpt_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        p_layout.addWidget(rpt_title)

        rpt_sub = QLabel("Document Forensic & Authenticity Analysis Report")
        rpt_sub.setStyleSheet("font-size: 13px; color: #2B2B2B; border: none;")
        rpt_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        p_layout.addWidget(rpt_sub)

        p_layout.addWidget(Separator())

        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #B08D3A;
                background-color: #FFFFFF;
                color: #2B2B2B;
                font-family: monospace;
                padding: 10px;
            }
        """)
        self.preview_text.setPlaceholderText("No data available. Click Generate Report to preview.")
        p_layout.addWidget(self.preview_text, 1)

        splitter.addWidget(self.preview)

        # Right: Controls
        right = QFrame()
        right.setFixedWidth(240)
        right.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.PANEL};
                border: 2px solid #2B2B2B;
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
        btn_text = ActionButton("Export Text")
        btn_text.clicked.connect(lambda: self._on_export("Text Document (*.txt)"))
        btn_html = ActionButton("Export HTML")
        btn_html.clicked.connect(lambda: self._on_export("HTML Document (*.html)"))
        btn_print = ActionButton("Print")
        btn_print.clicked.connect(self._on_print)

        r_layout.addWidget(btn_pdf)
        r_layout.addWidget(btn_text)
        r_layout.addWidget(btn_html)
        r_layout.addWidget(btn_print)

        r_layout.addWidget(Separator())
        r_layout.addWidget(SectionLabel("Report Sections"))

        from PyQt5.QtWidgets import QCheckBox
        sections = [
            "Case Information", "Examiner Information",
            "Evidence Information", "Document Information",
            "Integrity Verification", "Methods Applied",
            "Analysis Results", "Forensic Findings",
            "Suspicious Regions", "Examiner Notes",
            "Conclusion", "Audit Trail",
        ]
        for sec in sections:
            cb = QCheckBox(sec)
            cb.setChecked(True)
            r_layout.addWidget(cb)

        r_layout.addStretch()
        splitter.addWidget(right)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)

        layout.addWidget(splitter, 1)

    def set_current_context(self, context):
        """Receive the global current case/evidence/document context."""
        self._current_context = context
        if context and context.case and context.evidence:
            try:
                from services.db_service import get_db
                db = get_db()
                runs = db.get_ocr_runs_for_evidence(context.evidence.evidence_id)
                if runs:
                    self._ocr_result = runs[0]
            except Exception as e:
                import logging
                logging.getLogger("antordrishti.reports").warning(f"Could not load OCR results for report: {e}")

    def _on_generate(self):
        from PyQt5.QtWidgets import QMessageBox
        if not self._current_context or not self._current_context.case or not self._current_context.evidence:
            QMessageBox.information(self, "Report Generator", "Please load a case and evidence first.")
            return
            
        try:
            from services.report_service import generate_case_report
            import os
            output_dir = os.path.join(os.path.expanduser("~"), "Documents", "Antordrishti_Reports")
            path = generate_case_report(self._current_context.case, self._current_context.evidence, output_dir)
            
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
                
            self.preview_text.setText(content)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate report: {e}")

    def _on_preview(self):
        self._on_generate()

    def _on_save(self):
        self._on_generate()

    def _on_export(self, file_filter: str):
        from PyQt5.QtWidgets import QFileDialog, QMessageBox
        
        if not self._current_context or not self._current_context.case or not self._current_context.evidence:
            QMessageBox.information(self, "Export Report", "Please load a case and evidence first.")
            return
            
        path, _ = QFileDialog.getSaveFileName(self, "Export Forensic Report", "", file_filter)
        if path:
            try:
                from services.report_service import ReportGenerator
                import os
                
                output_dir = os.path.dirname(path)
                gen = ReportGenerator(output_dir)
                
                if path.endswith(".pdf"):
                    final_path = gen.generate_pdf_report(self._current_context.case, self._current_context.evidence, self._ocr_result)
                elif path.endswith(".txt"):
                    final_path = gen.generate_text_report(self._current_context.case, self._current_context.evidence, self._ocr_result)
                else:
                    final_path = gen.generate_text_report(self._current_context.case, self._current_context.evidence, self._ocr_result)
                
                if final_path != path:
                    import shutil
                    shutil.move(final_path, path)
                    
                QMessageBox.information(self, "Export Report", f"Report exported successfully to:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export report: {e}")

    def _on_print(self):
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(self, "Print Report", "Sending report to system printer...")

