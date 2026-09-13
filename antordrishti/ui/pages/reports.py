"""
Antordrishti — Report Generator Page
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QFrame, QScrollArea, QSplitter
)
from PyQt5.QtCore import Qt

from app.theme import Colors, Spacing, Fonts, Bg, Text, Border, Brand
from ui.widgets.common import SectionLabel, ActionButton, Separator, InfoRow


class ReportsPage(QWidget):
    """Report Generator page with document preview and export tools."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_context = None
        self._ocr_result = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Title Bar
        title_bar = QWidget()
        title_bar.setFixedHeight(48)
        title_bar.setStyleSheet(f"""
            background-color: {Bg.WHITE};
            border-bottom: 1px solid {Border.DEFAULT};
        """)
        tb = QHBoxLayout(title_bar)
        tb.setContentsMargins(Spacing.LG, 0, Spacing.LG, 0)
        t = QLabel("Forensic Examination Report Generator")
        t.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {Text.PRIMARY};")
        tb.addWidget(t)
        tb.addStretch()
        layout.addWidget(title_bar)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background-color: {Border.DEFAULT};
                width: 1px;
            }}
        """)

        # Left: Report Document Preview Sheet
        preview_container = QWidget()
        preview_container.setStyleSheet(f"background-color: {Bg.SECONDARY};")
        pc_layout = QVBoxLayout(preview_container)
        pc_layout.setContentsMargins(Spacing.XL, Spacing.XL, Spacing.XL, Spacing.XL)

        self.preview = QFrame()
        self.preview.setStyleSheet(f"""
            QFrame#ReportSheet {{
                background-color: {Bg.WHITE};
                border: 1px solid {Border.DEFAULT};
                border-radius: 8px;
            }}
        """)
        self.preview.setObjectName("ReportSheet")
        p_layout = QVBoxLayout(self.preview)
        p_layout.setContentsMargins(Spacing.XXL, Spacing.XXL,
                                    Spacing.XXL, Spacing.XXL)
        p_layout.setSpacing(Spacing.MD)

        # Report header
        rpt_title = QLabel("অন্তর্দৃষ্টি  |  ANTORDRISHTI")
        rpt_title.setStyleSheet(f"font-size: 18px; font-weight: 800; color: {Brand.GOLD}; letter-spacing: 1px;")
        rpt_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        p_layout.addWidget(rpt_title)

        rpt_sub = QLabel("QUESTIONED DOCUMENT FORENSIC EXAMINATION & AUTHENTICITY REPORT")
        rpt_sub.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {Text.MUTED}; letter-spacing: 0.8px;")
        rpt_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        p_layout.addWidget(rpt_sub)

        p_layout.addWidget(Separator())

        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setStyleSheet(f"""
            QTextEdit {{
                border: 1px solid {Border.DEFAULT};
                border-radius: 4px;
                background-color: {Bg.INPUT};
                color: {Text.PRIMARY};
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
                line-height: 1.5;
                padding: 16px;
            }}
        """)
        self.preview_text.setPlaceholderText("No report generated yet. Click 'Generate Report' in the actions panel to synthesize current case findings.")
        p_layout.addWidget(self.preview_text, 1)

        pc_layout.addWidget(self.preview, 1)
        splitter.addWidget(preview_container)

        # Right: Controls
        right = QFrame()
        right.setFixedWidth(260)
        right.setStyleSheet(f"""
            QFrame#ReportControls {{
                background-color: {Bg.WHITE};
                border-left: 1px solid {Border.DEFAULT};
            }}
        """)
        right.setObjectName("ReportControls")
        r_layout = QVBoxLayout(right)
        r_layout.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        r_layout.setSpacing(Spacing.MD)

        r_layout.addWidget(SectionLabel("Forensic Report Actions"))
        btn_gen = ActionButton("Generate Full Report", primary=True)
        btn_gen.clicked.connect(self._on_generate)
        r_layout.addWidget(btn_gen)
        
        btn_pdf = ActionButton("Export PDF Document")
        btn_pdf.clicked.connect(lambda: self._on_export("PDF Document (*.pdf)"))
        btn_text = ActionButton("Export Plaintext (.txt)")
        btn_text.clicked.connect(lambda: self._on_export("Text Document (*.txt)"))
        btn_html = ActionButton("Export HTML Document")
        btn_html.clicked.connect(lambda: self._on_export("HTML Document (*.html)"))
        btn_print = ActionButton("Print Document")
        btn_print.clicked.connect(self._on_print)

        r_layout.addWidget(btn_pdf)
        r_layout.addWidget(btn_text)
        r_layout.addWidget(btn_html)
        r_layout.addWidget(btn_print)

        r_layout.addWidget(Separator())
        r_layout.addWidget(SectionLabel("Included Sections"))

        # Scrollable sections area
        sec_scroll = QScrollArea()
        sec_scroll.setWidgetResizable(True)
        sec_scroll.setFrameShape(QFrame.Shape.NoFrame)
        sec_scroll.setStyleSheet("background: transparent;")
        sec_container = QWidget()
        sec_container_layout = QVBoxLayout(sec_container)
        sec_container_layout.setContentsMargins(0, 0, 0, 0)
        sec_container_layout.setSpacing(6)

        from PyQt5.QtWidgets import QCheckBox
        sections = [
            "Case Information", "Examiner Information",
            "Evidence Information", "Document Information",
            "Integrity Verification", "Methods Applied",
            "Analysis Results", "Forensic Findings",
            "Suspicious Regions", "Examiner Notes",
            "Conclusion", "Audit Trail",
        ]
        self._section_cbs = []
        for sec in sections:
            cb = QCheckBox(sec)
            cb.setChecked(True)
            cb.setStyleSheet(f"""
                QCheckBox {{
                    font-size: 11px;
                    color: {Text.PRIMARY};
                }}
            """)
            sec_container_layout.addWidget(cb)
            self._section_cbs.append(cb)
            
        sec_scroll.setWidget(sec_container)
        r_layout.addWidget(sec_scroll, 1)

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

