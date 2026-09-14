"""
Antordrishti — Forensic Metadata Examination Page
Rigorous digital forensic metadata examination, container analysis, and anomaly detection.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Tuple

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QScrollArea, QMessageBox, QFileDialog, QLineEdit, QTextEdit
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

from app.theme import Colors, Spacing, Bg, Border, Text, Brand
from ui.widgets.common import ActionButton, Separator
from services.forensic_metadata_service import (
    examine_evidence_metadata,
    export_metadata_to_json,
    export_metadata_to_txt,
)
from services.metadata_service import sanitize_metadata
from services.db_service import get_db

logger = logging.getLogger("antordrishti.metadata")


class _MetadataTable(QTableWidget):
    """Forensic metadata Property | Value | Source table with clean, professional styling."""

    def __init__(self, headers=None, parent=None):
        super().__init__(parent)
        if headers is None:
            headers = ["Property", "Value", "Source"]
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)
        self.horizontalHeader().setStretchLastSection(False)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.verticalHeader().setVisible(False)
        self.setAlternatingRowColors(True)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setShowGrid(False)
        self.setStyleSheet(f"""
            QTableWidget {{
                background-color: {Bg.WHITE};
                border: 1px solid {Border.DEFAULT};
                border-radius: 4px;
                gridline-color: transparent;
                font-size: 12px;
            }}
            QTableWidget::item {{
                padding: 6px 10px;
                border-bottom: 1px solid {Border.SUBTLE};
            }}
            QTableWidget::item:selected {{
                background-color: {Bg.HOVER};
                color: {Text.PRIMARY};
            }}
            QHeaderView::section {{
                background-color: {Bg.SECONDARY};
                color: {Text.SECONDARY};
                font-weight: 600;
                font-size: 11px;
                border: none;
                border-bottom: 2px solid {Border.DEFAULT};
                padding: 8px 10px;
            }}
        """)


class MetadataPage(QWidget):
    """Forensic metadata examination and deep container analysis page."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._all_rows: Dict[str, List[Tuple[str, str, str]]] = {}
        self._current_doc = None
        self._current_context = None
        self._current_exam_data: Optional[Dict[str, Any]] = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Title Bar ─────────────────────────────────────────
        title_bar = QWidget()
        title_bar.setFixedHeight(50)
        title_bar.setStyleSheet(f"""
            background-color: {Bg.WHITE};
            border-bottom: 1px solid {Border.DEFAULT};
        """)
        tb_layout = QHBoxLayout(title_bar)
        tb_layout.setContentsMargins(Spacing.LG, 0, Spacing.LG, 0)

        title = QLabel("METADATA EXAMINATION")
        title.setStyleSheet(f"font-size: 14px; font-weight: 700; letter-spacing: 0.5px; color: {Text.PRIMARY};")
        tb_layout.addWidget(title)

        tb_layout.addSpacing(16)
        # Search / Filter
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Filter properties, values, or sources...")
        self._search_input.setClearButtonEnabled(True)
        self._search_input.setFixedWidth(280)
        self._search_input.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {Border.DEFAULT};
                border-radius: 4px;
                padding: 4px 10px;
                background-color: {Bg.INPUT};
                font-size: 12px;
                color: {Text.PRIMARY};
            }}
            QLineEdit:focus {{
                border: 1px solid {Border.FOCUS};
                background-color: {Bg.WHITE};
            }}
        """)
        self._search_input.textChanged.connect(self._apply_filter)
        tb_layout.addWidget(self._search_input)

        tb_layout.addStretch()

        # Action buttons
        self._btn_export_json = ActionButton("Export JSON")
        self._btn_export_txt = ActionButton("Export TXT")
        self._btn_sanitize = ActionButton("Sanitize Derivative Copy")

        self._btn_export_json.clicked.connect(self._on_export_json)
        self._btn_export_txt.clicked.connect(self._on_export_txt)
        self._btn_sanitize.clicked.connect(self._on_sanitize)

        tb_layout.addWidget(self._btn_export_json)
        tb_layout.addWidget(self._btn_export_txt)
        tb_layout.addWidget(self._btn_sanitize)

        layout.addWidget(title_bar)

        # ── Evidence & Summary Header Banner ──────────────────
        summary_panel = QFrame()
        summary_panel.setStyleSheet(f"""
            QFrame {{
                background-color: {Bg.SECONDARY};
                border-bottom: 1px solid {Border.DEFAULT};
                padding: 6px 16px;
            }}
        """)
        sp_layout = QVBoxLayout(summary_panel)
        sp_layout.setContentsMargins(Spacing.LG, Spacing.SM, Spacing.LG, Spacing.SM)
        sp_layout.setSpacing(4)

        # Row 1: Evidence identification line
        self._lbl_evidence_line = QLabel("No document loaded  •  Case: Unassigned")
        self._lbl_evidence_line.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {Text.PRIMARY};")
        sp_layout.addWidget(self._lbl_evidence_line)

        # Row 2: Metadata status pills
        self._pills_layout = QHBoxLayout()
        self._pills_layout.setSpacing(8)

        self._pill_meta_status = self._create_pill("Metadata Status", "NONE", "#64748B", "#F1F5F9")
        self._pill_exif = self._create_pill("EXIF", "Not Available", "#64748B", "#F1F5F9")
        self._pill_xmp = self._create_pill("XMP", "Not Available", "#64748B", "#F1F5F9")
        self._pill_iptc = self._create_pill("IPTC", "Not Available", "#64748B", "#F1F5F9")
        self._pill_gps = self._create_pill("GPS", "Not Available", "#64748B", "#F1F5F9")
        self._pill_software = self._create_pill("Software", "Not Available", "#64748B", "#F1F5F9")
        self._pill_integrity = self._create_pill("Integrity", "—", "#64748B", "#F1F5F9")
        self._pill_consistency = self._create_pill("Consistency", "—", "#64748B", "#F1F5F9")

        self._pills_layout.addWidget(self._pill_meta_status)
        self._pills_layout.addWidget(self._pill_exif)
        self._pills_layout.addWidget(self._pill_xmp)
        self._pills_layout.addWidget(self._pill_iptc)
        self._pills_layout.addWidget(self._pill_gps)
        self._pills_layout.addWidget(self._pill_software)
        self._pills_layout.addWidget(self._pill_integrity)
        self._pills_layout.addWidget(self._pill_consistency)
        self._pills_layout.addStretch()

        sp_layout.addLayout(self._pills_layout)
        layout.addWidget(summary_panel)

        # ── Main Tabs ─────────────────────────────────────────
        self._tabs = QTabWidget()
        self._tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {Border.DEFAULT};
                background-color: {Bg.WHITE};
                margin-top: -1px;
            }}
            QTabBar::tab {{
                background-color: {Bg.SECONDARY};
                color: {Text.SECONDARY};
                padding: 8px 16px;
                border: 1px solid {Border.DEFAULT};
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
                font-weight: 500;
                font-size: 11.5px;
            }}
            QTabBar::tab:selected {{
                background-color: {Bg.WHITE};
                color: {Brand.GOLD};
                font-weight: 700;
                border-bottom: 2px solid {Brand.GOLD};
            }}
        """)

        self._tab_names = [
            "EXIF",
            "XMP",
            "IPTC",
            "PDF",
            "FILE",
            "JPEG / CONTAINER",
            "SOFTWARE",
            "CONSISTENCY",
            "RAW"
        ]

        self._tables: Dict[str, _MetadataTable] = {}

        for tab_name in self._tab_names:
            if tab_name == "RAW":
                raw_container = QWidget()
                rc_layout = QVBoxLayout(raw_container)
                rc_layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
                self._raw_text_view = QTextEdit()
                self._raw_text_view.setReadOnly(True)
                self._raw_text_view.setStyleSheet(f"""
                    QTextEdit {{
                        background-color: #0F172A;
                        color: #E2E8F0;
                        font-family: Consolas, 'Courier New', monospace;
                        font-size: 11.5px;
                        border: 1px solid {Border.DEFAULT};
                        border-radius: 4px;
                        padding: 10px;
                    }}
                """)
                self._raw_text_view.setPlainText("No metadata examination loaded.")
                rc_layout.addWidget(self._raw_text_view)
                self._tabs.addTab(raw_container, tab_name)

            elif tab_name == "CONSISTENCY":
                cons_container = QWidget()
                cc_layout = QVBoxLayout(cons_container)
                cc_layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
                cc_layout.setSpacing(Spacing.SM)

                incons_lbl = QLabel("Observed Discrepancies & Anomaly Indicators")
                incons_lbl.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {Text.PRIMARY};")
                cc_layout.addWidget(incons_lbl)

                self._incons_table = _MetadataTable(headers=["Field", "Observed Value", "Comparison / Reason"])
                cc_layout.addWidget(self._incons_table, 1)

                timeline_lbl = QLabel("Forensic Observed Timeline")
                timeline_lbl.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {Text.PRIMARY}; margin-top: 6px;")
                cc_layout.addWidget(timeline_lbl)

                self._timeline_table = _MetadataTable(headers=["Event / Source", "Observed Timestamp", "Source Context"])
                cc_layout.addWidget(self._timeline_table, 1)

                self._tabs.addTab(cons_container, tab_name)

            else:
                table = _MetadataTable()
                placeholder_data = [("Status", "No document loaded", "General")]
                self._tables[tab_name] = table
                self._all_rows[tab_name] = placeholder_data
                self._render_table(table, placeholder_data)
                self._tabs.addTab(table, tab_name)

        layout.addWidget(self._tabs, 1)

    def _create_pill(self, label: str, value: str, text_color: str, bg_color: str) -> QLabel:
        """Create a summary badge pill."""
        pill = QLabel(f"{label}: {value}")
        pill.setStyleSheet(f"""
            background-color: {bg_color};
            color: {text_color};
            border: 1px solid {Border.DEFAULT};
            border-radius: 4px;
            padding: 2px 8px;
            font-size: 11px;
            font-weight: 600;
        """)
        return pill

    def _update_pill(self, pill: QLabel, label: str, value: str, status_type: str):
        """Update badge text and colors based on status."""
        text_color = "#475569"
        bg_color = "#F1F5F9"

        if status_type in ("PRESENT", "VERIFIED", "NO_ANOMALY", "YES"):
            text_color = "#065F46"
            bg_color = "#D1FAE5"
        elif status_type in ("LIMITED", "WARNING"):
            text_color = "#92400E"
            bg_color = "#FEF3C7"
        elif status_type in ("MISMATCH", "CHANGED", "ERROR", "HIGH"):
            text_color = "#991B1B"
            bg_color = "#FEE2E2"

        pill.setText(f"{label}: {value}")
        pill.setStyleSheet(f"""
            background-color: {bg_color};
            color: {text_color};
            border: 1px solid {Border.DEFAULT};
            border-radius: 4px;
            padding: 2px 8px;
            font-size: 11px;
            font-weight: 600;
        """)

    def _render_table(self, table: QTableWidget, rows: List[Tuple[str, str, str]]):
        """Render Property | Value | Source rows into a table."""
        table.setRowCount(len(rows))
        for r_idx, row in enumerate(rows):
            prop = str(row[0])
            val = str(row[1])
            src = str(row[2]) if len(row) > 2 else ""

            item_p = QTableWidgetItem(prop)
            item_v = QTableWidgetItem(val)
            item_s = QTableWidgetItem(src)

            # Subtle color for Not Available
            if val in ("Not Available", "Not Detected", "No metadata loaded"):
                item_v.setForeground(QColor("#94A3B8"))

            table.setItem(r_idx, 0, item_p)
            table.setItem(r_idx, 1, item_v)
            table.setItem(r_idx, 2, item_s)

    def set_document(self, doc):
        """Convenience method to set current document directly."""
        self._current_doc = doc
        if doc and getattr(doc, "file_path", None):
            self.load_document(doc.file_path)
        else:
            self.set_current_context(None)

    def set_current_context(self, context):
        """Update metadata view strictly from the shared active document context."""
        self._current_context = context
        doc = context.document if context else None
        case = context.case if context else None
        evidence = context.evidence if context else None

        if not doc or not doc.file_path:
            self._current_doc = None
            self._current_exam_data = None
            case_info = f"Case: {case.case_name} ({case.case_id})" if case else "No active case"
            self._lbl_evidence_line.setText(f"No document loaded  •  {case_info}")

            # Reset badges
            self._update_pill(self._pill_meta_status, "Metadata", "NONE", "NONE")
            self._update_pill(self._pill_exif, "EXIF", "Not Available", "NONE")
            self._update_pill(self._pill_xmp, "XMP", "Not Available", "NONE")
            self._update_pill(self._pill_iptc, "IPTC", "Not Available", "NONE")
            self._update_pill(self._pill_gps, "GPS", "Not Available", "NONE")
            self._update_pill(self._pill_software, "Software", "Not Available", "NONE")
            self._update_pill(self._pill_integrity, "Integrity", "—", "NONE")
            self._update_pill(self._pill_consistency, "Consistency", "—", "NONE")

            for tab_name, table in self._tables.items():
                self._all_rows[tab_name] = [("Status", "No document loaded", "General")]
                self._render_table(table, self._all_rows[tab_name])

            if hasattr(self, "_incons_table"):
                self._incons_table.setRowCount(0)
            if hasattr(self, "_timeline_table"):
                self._timeline_table.setRowCount(0)
            if hasattr(self, "_raw_text_view"):
                self._raw_text_view.setPlainText("No document loaded.")
            return

        # Load metadata strictly from original evidence
        self._current_doc = doc
        self.load_document(
            doc.file_path,
            case_id=case.case_id if case else "",
            evidence_id=evidence.evidence_id if evidence else ""
        )

    def load_document(self, file_path: str, case_id: str = "", evidence_id: str = ""):
        """Run deep forensic examination against the original immutable evidence file."""
        if not os.path.exists(file_path):
            QMessageBox.warning(self, "Missing File", f"Evidence file not found on disk:\n{file_path}")
            return

        try:
            exam_data = examine_evidence_metadata(file_path, case_id=case_id, evidence_id=evidence_id)
            self._current_exam_data = exam_data

            # Persist to SQLite linked to Evidence ID
            if evidence_id:
                try:
                    db = get_db()
                    db.save_metadata_examination({
                        "case_id": case_id,
                        "evidence_id": evidence_id,
                        "file_path": file_path,
                        "sha256": self._current_doc.sha256 if self._current_doc else "",
                        "detected_format": exam_data.get("signature", {}).get("detected_format", ""),
                        "status": "EXAMINED",
                        "flags": exam_data.get("summary", {}).get("flags", []),
                        "summary": exam_data.get("summary", {}),
                        "full_data": exam_data
                    })
                except Exception as e:
                    logger.debug(f"Metadata SQLite save notice: {e}")

            # 1. Update Evidence Line
            c_name = self._current_context.case.case_name if self._current_context and self._current_context.case else (case_id or "Unassigned")
            c_id = case_id or "Unassigned"
            e_id = evidence_id or "Unassigned"
            fn = os.path.basename(file_path)
            fmt = exam_data.get("signature", {}).get("detected_format", "UNKNOWN")
            sha_short = (self._current_doc.sha256[:16] + "...") if self._current_doc and self._current_doc.sha256 else "—"

            self._lbl_evidence_line.setText(
                f"Case: {c_name} ({c_id})  •  Evidence: {e_id}  •  File: {fn}  •  Detected: {fmt}  •  SHA-256: {sha_short}"
            )

            # 2. Update Pills
            summ = exam_data.get("summary", {})
            m_stat = summ.get("metadata_status", "LIMITED")
            self._update_pill(self._pill_meta_status, "Metadata", m_stat, m_stat)
            self._update_pill(self._pill_exif, "EXIF", summ.get("exif_present", "Not Available"), "PRESENT" if summ.get("exif_present") == "Present" else "NONE")
            self._update_pill(self._pill_xmp, "XMP", summ.get("xmp_present", "Not Available"), "PRESENT" if summ.get("xmp_present") == "Present" else "NONE")
            self._update_pill(self._pill_iptc, "IPTC", summ.get("iptc_present", "Not Available"), "PRESENT" if summ.get("iptc_present") == "Present" else "NONE")
            self._update_pill(self._pill_gps, "GPS", summ.get("gps_present", "Not Available"), "PRESENT" if summ.get("gps_present") == "Present" else "NONE")
            self._update_pill(self._pill_software, "Software", summ.get("software_present", "Not Available"), "PRESENT" if summ.get("software_present") == "Present" else "NONE")

            integ_status = self._current_doc.integrity_status if self._current_doc else "INTEGRITY VERIFIED"
            self._update_pill(self._pill_integrity, "Integrity", integ_status, "VERIFIED" if "VERIFIED" in integ_status else "CHANGED")

            incons_count = summ.get("inconsistency_count", 0)
            if incons_count == 0:
                self._update_pill(self._pill_consistency, "Consistency", "No Discrepancies", "NO_ANOMALY")
            else:
                self._update_pill(self._pill_consistency, "Consistency", f"{incons_count} Discrepanc{'y' if incons_count==1 else 'ies'}", "WARNING")

            # 3. Populate Tabs
            # EXIF
            exif_rows = exam_data.get("exif", {}).get("rows", [])
            self._all_rows["EXIF"] = exif_rows or [("EXIF Status", "EXIF metadata not present in this document", "EXIF")]
            self._render_table(self._tables["EXIF"], self._all_rows["EXIF"])

            # XMP
            xmp_rows = exam_data.get("xmp", {}).get("rows", [])
            self._all_rows["XMP"] = xmp_rows or [("XMP Status", "No embedded XMP packet detected", "XMP")]
            self._render_table(self._tables["XMP"], self._all_rows["XMP"])

            # IPTC
            iptc_rows = exam_data.get("iptc", {}).get("rows", [])
            self._all_rows["IPTC"] = iptc_rows or [("IPTC Status", "No legacy IPTC records detected", "IPTC")]
            self._render_table(self._tables["IPTC"], self._all_rows["IPTC"])

            # PDF
            pdf_rows = exam_data.get("pdf", {}).get("rows", [])
            self._all_rows["PDF"] = pdf_rows or [("PDF Status", "Not a PDF document", "PDF Engine")]
            self._render_table(self._tables["PDF"], self._all_rows["PDF"])

            # FILE
            fs_rows = exam_data.get("filesystem_rows", [])
            # Prepend signature row
            sig = exam_data.get("signature", {})
            fs_full = [
                ("Declared Extension", f".{sig.get('declared_ext', '')}", "Filesystem Header"),
                ("Detected Magic Bytes", f"{sig.get('detected_format')} (Magic: {sig.get('magic_hex', '')[:16]})", "File Signature"),
                ("Container Consistency", "CONSISTENT" if sig.get("is_consistent") else "FORMAT MISMATCH", "Container Validation")
            ] + fs_rows
            self._all_rows["FILE"] = fs_full
            self._render_table(self._tables["FILE"], self._all_rows["FILE"])

            # JPEG / CONTAINER
            det_fmt = sig.get("detected_format", "")
            if "JPEG" in det_fmt:
                cont_rows = exam_data.get("jpeg", {}).get("rows", [])
            elif "PNG" in det_fmt:
                cont_rows = exam_data.get("png", {}).get("rows", [])
            elif "TIFF" in det_fmt:
                cont_rows = exam_data.get("tiff", {}).get("rows", [])
            elif "WEBP" in det_fmt:
                cont_rows = exam_data.get("webp", {}).get("rows", [])
            else:
                cont_rows = [("Container Analysis", f"Container format: {det_fmt}", "Container Parser")]
            self._all_rows["JPEG / CONTAINER"] = cont_rows
            self._render_table(self._tables["JPEG / CONTAINER"], self._all_rows["JPEG / CONTAINER"])

            # SOFTWARE
            soft_indicators = exam_data.get("consistency", {}).get("software_indicators", [])
            soft_rows = []
            if soft_indicators:
                for ind in soft_indicators:
                    parts = ind.split(":", 1)
                    prop = parts[0].strip()
                    val = parts[1].strip() if len(parts) > 1 else ind
                    soft_rows.append((prop, val, "Observed Metadata"))
            else:
                soft_rows.append(("Software Trace", "No known editing software signatures observed in metadata.", "Software Analysis"))
            self._all_rows["SOFTWARE"] = soft_rows
            self._render_table(self._tables["SOFTWARE"], self._all_rows["SOFTWARE"])

            # CONSISTENCY & TIMELINE
            incons = exam_data.get("consistency", {}).get("inconsistencies", [])
            self._incons_table.setRowCount(len(incons) if incons else 1)
            if incons:
                for idx, inc in enumerate(incons):
                    self._incons_table.setItem(idx, 0, QTableWidgetItem(str(inc.get("field"))))
                    self._incons_table.setItem(idx, 1, QTableWidgetItem(f"Observed: {inc.get('observed_value')} vs {inc.get('comparison_value')}"))
                    self._incons_table.setItem(idx, 2, QTableWidgetItem(str(inc.get("reason"))))
            else:
                self._incons_table.setItem(0, 0, QTableWidgetItem("Consistency Check"))
                self._incons_table.setItem(0, 1, QTableWidgetItem("No major discrepancies or anomalies detected."))
                self._incons_table.setItem(0, 2, QTableWidgetItem("All available properties are mutually consistent."))

            # Timeline
            tline = exam_data.get("timeline", [])
            self._timeline_table.setRowCount(len(tline) if tline else 1)
            if tline:
                for idx, t in enumerate(tline):
                    self._timeline_table.setItem(idx, 0, QTableWidgetItem(f"{t.get('source')}: {t.get('event')}"))
                    self._timeline_table.setItem(idx, 1, QTableWidgetItem(str(t.get("timestamp_str"))))
                    self._timeline_table.setItem(idx, 2, QTableWidgetItem(str(t.get("source"))))
            else:
                self._timeline_table.setItem(0, 0, QTableWidgetItem("Timeline"))
                self._timeline_table.setItem(0, 1, QTableWidgetItem("No timestamps recorded in document."))
                self._timeline_table.setItem(0, 2, QTableWidgetItem("Metadata"))

            # RAW
            raw_copy = dict(exam_data)
            if "exif" in raw_copy and isinstance(raw_copy["exif"], dict):
                raw_c_ex = dict(raw_copy["exif"])
                raw_c_ex.pop("thumbnail_bytes", None)
                raw_copy["exif"] = raw_c_ex
            formatted_json = json.dumps(raw_copy, indent=2, ensure_ascii=False)
            self._raw_text_view.setPlainText(formatted_json)

        except Exception as e:
            logger.error(f"Error during metadata examination of {file_path}: {e}", exc_info=True)
            QMessageBox.critical(self, "Examination Error", f"Metadata examination failed:\n{str(e)}")

    def _apply_filter(self, query: str):
        """Filter rows in the current table by query string."""
        query = query.strip().lower()
        curr_tab = self._tabs.tabText(self._tabs.currentIndex())
        if curr_tab not in self._tables:
            return

        table = self._tables[curr_tab]
        all_data = self._all_rows.get(curr_tab, [])
        if not query:
            self._render_table(table, all_data)
            return

        filtered = [
            row for row in all_data
            if query in str(row[0]).lower() or query in str(row[1]).lower() or (len(row) > 2 and query in str(row[2]).lower())
        ]
        self._render_table(table, filtered)

    def _on_export_json(self):
        """Export metadata examination to JSON."""
        if not self._current_exam_data:
            QMessageBox.information(self, "No Data", "No metadata examination available to export.")
            return

        out_path, _ = QFileDialog.getSaveFileName(
            self, "Export Metadata JSON", "forensic_metadata_report.json",
            "JSON Files (*.json);;All Files (*.*)"
        )
        if not out_path:
            return

        if export_metadata_to_json(self._current_exam_data, out_path):
            QMessageBox.information(self, "Export Complete", f"Metadata examination exported successfully to:\n{out_path}")
        else:
            QMessageBox.warning(self, "Export Failed", "Failed to write metadata JSON file.")

    def _on_export_txt(self):
        """Export metadata examination to formatted TXT."""
        if not self._current_exam_data:
            QMessageBox.information(self, "No Data", "No metadata examination available to export.")
            return

        out_path, _ = QFileDialog.getSaveFileName(
            self, "Export Metadata Report", "forensic_metadata_report.txt",
            "Text Files (*.txt);;All Files (*.*)"
        )
        if not out_path:
            return

        if export_metadata_to_txt(self._current_exam_data, out_path):
            QMessageBox.information(self, "Export Complete", f"Forensic report exported successfully to:\n{out_path}")
        else:
            QMessageBox.warning(self, "Export Failed", "Failed to write metadata report TXT file.")

    def _on_sanitize(self):
        """
        Create a sanitized derivative copy with metadata stripped.
        Original evidence remains strictly immutable.
        """
        if not self._current_doc or not self._current_doc.file_path:
            QMessageBox.information(self, "No Document", "No active evidence document loaded.")
            return

        src_path = self._current_doc.file_path
        ext = os.path.splitext(src_path)[1]
        default_out = os.path.join(
            os.path.dirname(src_path),
            f"{os.path.splitext(os.path.basename(src_path))[0]}_sanitized{ext}"
        )

        out_path, _ = QFileDialog.getSaveFileName(
            self, "Save Sanitized Derivative Copy", default_out,
            f"Supported Files (*{ext});;All Files (*.*)"
        )
        if not out_path:
            return

        if os.path.abspath(out_path) == os.path.abspath(src_path):
            QMessageBox.warning(
                self, "Forensic Safety Restriction",
                "Cannot overwrite original evidence file.\n"
                "Please choose a different destination filename for the sanitized copy."
            )
            return

        success = sanitize_metadata(src_path, out_path)
        if success:
            QMessageBox.information(
                self, "Sanitization Complete",
                f"Derivative sanitized file created successfully:\n{out_path}\n\n"
                "The original evidence file remains completely unaltered and immutable."
            )
        else:
            QMessageBox.warning(
                self, "Sanitization Failed",
                "Could not sanitize metadata for this file format."
            )
