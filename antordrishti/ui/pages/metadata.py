"""
Antordrishti — Metadata Sanitization Page
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QScrollArea, QMessageBox
)
from PyQt5.QtCore import Qt

from app.theme import Colors, Spacing, Bg, Border, Text, Brand
from ui.widgets.common import (
    SectionLabel, ActionButton, EngineNotConnectedWidget, Separator
)


class _MetadataTable(QTableWidget):
    """Metadata property-value-source table with professional forensic styling."""

    def __init__(self, headers=None, parent=None):
        super().__init__(parent)
        if headers is None:
            headers = ["Property", "Value", "Category"]
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
                border-radius: 6px;
                gridline-color: transparent;
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
    """Metadata sanitization and deep structural examination page."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._all_rows = {}  # tab_name -> list of (prop, val, cat)
        self._current_doc = None
        
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
        tb_layout = QHBoxLayout(title_bar)
        tb_layout.setContentsMargins(Spacing.LG, 0, Spacing.LG, 0)
        
        title = QLabel("Metadata Analysis & Sanitization")
        title.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {Text.PRIMARY};")
        tb_layout.addWidget(title)
        
        tb_layout.addSpacing(16)
        # Search Filter
        from PyQt5.QtWidgets import QLineEdit
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Filter metadata properties or values...")
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
        layout.addWidget(title_bar)

        # Content
        content = QHBoxLayout()
        content.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        content.setSpacing(Spacing.LG)

        # Left: Metadata tabs
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(Spacing.MD)

        # Software trace banner
        self._software_banner = QFrame()
        self._software_banner.setStyleSheet(f"""
            QFrame {{
                background-color: {Bg.SECONDARY};
                border: 1px solid {Border.DEFAULT};
                border-radius: 6px;
                padding: 4px 8px;
            }}
        """)
        sb_layout = QHBoxLayout(self._software_banner)
        sb_layout.setContentsMargins(Spacing.MD, Spacing.SM, Spacing.MD, Spacing.SM)
        self._software_icon_lbl = QLabel("ℹ")
        self._software_icon_lbl.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {Brand.GOLD};")
        self._software_trace_lbl = QLabel("Software Trace: No editing tool signatures detected.")
        self._software_trace_lbl.setStyleSheet(f"font-size: 12px; font-weight: 500; color: {Text.PRIMARY};")
        sb_layout.addWidget(self._software_icon_lbl)
        sb_layout.addWidget(self._software_trace_lbl, 1)
        left_layout.addWidget(self._software_banner)

        self._tabs = QTabWidget()
        self._tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {Border.DEFAULT};
                background-color: {Bg.WHITE};
                border-radius: 6px;
            }}
            QTabBar::tab {{
                background-color: {Bg.SECONDARY};
                color: {Text.SECONDARY};
                padding: 7px 16px;
                border: 1px solid {Border.DEFAULT};
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
                font-weight: 500;
            }}
            QTabBar::tab:selected {{
                background-color: {Bg.WHITE};
                color: {Brand.GOLD};
                font-weight: 700;
                border-bottom: 2px solid {Brand.GOLD};
            }}
        """)
        self._tables = {}

        for tab_name in ["EXIF", "XMP", "IPTC", "PDF Metadata", "Software Info"]:
            table = _MetadataTable()
            placeholder_data = [
                ("Status", "No document loaded", "General"),
            ]
            self._tables[tab_name] = table
            self._all_rows[tab_name] = placeholder_data
            self._render_table(tab_name, placeholder_data)
            self._tabs.addTab(table, tab_name)

        left_layout.addWidget(self._tabs, 1)
        content.addWidget(left_container, 1)

        # Right: Actions and Forensic Warnings
        actions_panel = QFrame()
        actions_panel.setFixedWidth(280)
        actions_panel.setStyleSheet(f"""
            QFrame#ActionsPanel {{
                background-color: {Bg.WHITE};
                border: 1px solid {Border.DEFAULT};
                border-radius: 8px;
            }}
        """)
        actions_panel.setObjectName("ActionsPanel")
        act_layout = QVBoxLayout(actions_panel)
        act_layout.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        act_layout.setSpacing(Spacing.MD)

        act_layout.addWidget(SectionLabel("Forensic Operations"))
        
        self._btn_detect = ActionButton("Detect Anomalies", primary=True)
        self._btn_sanitize = ActionButton("Sanitize Metadata (Strip)")
        self._btn_export = ActionButton("Export Metadata Report")
        
        act_layout.addWidget(self._btn_detect)
        act_layout.addWidget(self._btn_sanitize)
        act_layout.addWidget(self._btn_export)
        
        self._btn_detect.clicked.connect(self._on_detect_anomalies)
        self._btn_sanitize.clicked.connect(self._on_sanitize)
        self._btn_export.clicked.connect(self._on_export_report)
        
        act_layout.addWidget(Separator())

        # Safe Forensic Warning Card
        warn_card = QFrame()
        warn_card.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.WARNING_LIGHT};
                border: 1px solid #FCD34D;
                border-radius: 6px;
                padding: 6px;
            }}
        """)
        wc_layout = QVBoxLayout(warn_card)
        wc_layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        wc_layout.setSpacing(4)
        
        wc_title = QLabel("Forensic Integrity Notice")
        wc_title.setStyleSheet("font-weight: 700; font-size: 11px; color: #92400E;")
        wc_msg = QLabel(
            "Sanitization creates a derivative sanitized copy. "
            "The original primary evidence file remains strictly read-only and immutable."
        )
        wc_msg.setWordWrap(True)
        wc_msg.setStyleSheet("font-size: 10.5px; color: #78350F; line-height: 14px;")
        wc_layout.addWidget(wc_title)
        wc_layout.addWidget(wc_msg)
        act_layout.addWidget(warn_card)

        # Hash Comparison Container
        self._hash_card = QFrame()
        self._hash_card.setStyleSheet(f"""
            QFrame {{
                background-color: {Bg.SECONDARY};
                border: 1px solid {Border.DEFAULT};
                border-radius: 6px;
            }}
        """)
        hc_layout = QVBoxLayout(self._hash_card)
        hc_layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        hc_layout.setSpacing(4)
        
        hc_title = QLabel("Integrity Hashes")
        hc_title.setStyleSheet(f"font-weight: 700; font-size: 11px; color: {Text.PRIMARY};")
        hc_layout.addWidget(hc_title)
        
        self._lbl_orig_hash = QLabel("Original SHA-256:\n—")
        self._lbl_orig_hash.setStyleSheet(f"font-family: monospace; font-size: 10px; color: {Text.SECONDARY};")
        self._lbl_orig_hash.setWordWrap(True)
        hc_layout.addWidget(self._lbl_orig_hash)
        
        self._lbl_san_hash = QLabel("Sanitized SHA-256:\n—")
        self._lbl_san_hash.setStyleSheet(f"font-family: monospace; font-size: 10px; color: {Colors.SUCCESS};")
        self._lbl_san_hash.setWordWrap(True)
        hc_layout.addWidget(self._lbl_san_hash)
        
        act_layout.addWidget(self._hash_card)

        act_layout.addStretch()
        content.addWidget(actions_panel)

        layout.addLayout(content, 1)

    def set_current_context(self, context):
        """Update metadata view from the shared active document context."""
        if context and context.document:
            self.load_document(context.document.file_path)
        else:
            self._current_doc = None
            for tab_name in ["EXIF", "XMP", "IPTC", "PDF Metadata", "Software Info"]:
                self._all_rows[tab_name] = [("Status", "No document loaded", "General")]
                self._render_table(tab_name, self._all_rows[tab_name])
            self._lbl_orig_hash.setText("Original SHA-256:\n—")
            self._lbl_san_hash.setText("Sanitized SHA-256:\n—")
            self._software_trace_lbl.setText("Software Trace: No document loaded.")

    def load_document(self, file_path: str):
        """Load metadata from the already-open active document."""
        from services.document_service import load_document

        doc = load_document(file_path)
        self._current_doc = doc
        if not doc:
            for tab_name in self._tables:
                self._all_rows[tab_name] = [("Status", "Metadata unavailable", "Error")]
                self._render_table(tab_name, self._all_rows[tab_name])
            return

        # Original Hash
        self._lbl_orig_hash.setText(f"Original SHA-256:\n{doc.sha256 or '—'}")
        self._lbl_san_hash.setText("Sanitized SHA-256:\n—")

        # 1. EXIF & Basic
        basic_rows = [
            ("Filename", doc.file_name, "File System"),
            ("File Type", doc.file_type, "File System"),
            ("File Size", f"{doc.file_size:,} bytes", "File System"),
            ("Resolution", doc.resolution or "Not Available", "Image Header"),
            ("Color Space", doc.color_space or "Not Available", "Image Header"),
            ("Pages", str(doc.page_count), "Document"),
            ("Last Modified", doc.last_modified or "Not Available", "File System"),
            ("SHA-256", doc.sha256 or "Not Available", "Integrity"),
            ("Integrity", doc.integrity_status, "Integrity"),
        ]
        raw_exif_rows = []
        if hasattr(doc, 'raw_metadata') and isinstance(doc.raw_metadata, dict):
            for k, v in sorted(doc.raw_metadata.items())[:120]:
                raw_exif_rows.append((str(k), str(v), "EXIF Header"))

        self._all_rows["EXIF"] = basic_rows + raw_exif_rows

        # 2. XMP
        xmp_rows = []
        if hasattr(doc, 'raw_metadata') and isinstance(doc.raw_metadata, dict):
            for k, v in doc.raw_metadata.items():
                if any(x in str(k).lower() for x in ["xmp", "adobe", "photoshop", "history", "stevt"]):
                    xmp_rows.append((str(k), str(v), "XMP Data"))
        if not xmp_rows:
            xmp_rows = [("XMP Status", "No standalone XMP packet detected", "XMP")]
        self._all_rows["XMP"] = xmp_rows

        # 3. IPTC
        iptc_rows = []
        if hasattr(doc, 'raw_metadata') and isinstance(doc.raw_metadata, dict):
            for k, v in doc.raw_metadata.items():
                if any(x in str(k).lower() for x in ["caption", "headline", "byline", "credit", "copyright", "source"]):
                    iptc_rows.append((str(k), str(v), "IPTC / Rights"))
        if not iptc_rows:
            iptc_rows = [("IPTC Status", "No IPTC legacy records found", "IPTC")]
        self._all_rows["IPTC"] = iptc_rows

        # 4. PDF Metadata
        self._all_rows["PDF Metadata"] = [
            ("PDF Version", doc.pdf_version or "Not Available", "PDF Header"),
            ("Author", doc.author or "Not Available", "PDF Info"),
            ("Creator", doc.creator or "Not Available", "PDF Info"),
            ("Producer", doc.producer or "Not Available", "PDF Info"),
            ("Creation Date", doc.creation_date or "Not Available", "PDF Info"),
            ("Objects", str(doc.pdf_objects or 0), "PDF Structure"),
            ("Linearized", "Yes" if doc.pdf_linearized else "No", "PDF Structure"),
        ]

        # 5. Software Info & Trace
        software_rows = [
            ("Camera Make", doc.camera_make or "Not Available", "Hardware"),
            ("Camera Model", doc.camera_model or "Not Available", "Hardware"),
            ("Software", doc.software or "Not Available", "Software"),
            ("Creator", doc.creator or "Not Available", "Software"),
            ("Producer", doc.producer or "Not Available", "Software"),
        ]
        self._all_rows["Software Info"] = software_rows

        # Evaluate Software Trace
        traces = []
        combined_software_text = f"{doc.software or ''} {doc.creator or ''} {doc.producer or ''}".lower()
        editing_keywords = [
            ("photoshop", "Adobe Photoshop"),
            ("gimp", "GIMP"),
            ("canva", "Canva"),
            ("corel", "CorelDRAW/Paint"),
            ("paint.net", "Paint.NET"),
            ("photopea", "Photopea"),
            ("affinity", "Affinity Photo"),
            ("illustrator", "Adobe Illustrator"),
            ("lightroom", "Adobe Lightroom"),
            ("snapseed", "Snapseed"),
        ]
        for kw, display_name in editing_keywords:
            if kw in combined_software_text:
                traces.append(display_name)

        if traces:
            detected_str = ", ".join(traces)
            self._software_trace_lbl.setText(
                f"Software Signature Detected: {detected_str} (Indicates post-processing or digital modification)"
            )
            self._software_icon_lbl.setText("⚠")
            self._software_icon_lbl.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {Colors.WARNING};")
            self._software_banner.setStyleSheet(f"""
                QFrame {{
                    background-color: #FEF3C7;
                    border: 1px solid #F59E0B;
                    border-radius: 6px;
                }}
            """)
        else:
            if doc.camera_make or doc.camera_model:
                self._software_trace_lbl.setText(
                    f"Hardware Capture Signatures: {doc.camera_make or ''} {doc.camera_model or ''} (No editing software signatures found)"
                )
            else:
                self._software_trace_lbl.setText("Software Trace: Clean metadata, no known editing signatures detected.")
            self._software_icon_lbl.setText("✓")
            self._software_icon_lbl.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {Colors.SUCCESS};")
            self._software_banner.setStyleSheet(f"""
                QFrame {{
                    background-color: #ECFDF5;
                    border: 1px solid #10B981;
                    border-radius: 6px;
                }}
            """)

        self._apply_filter(self._search_input.text())

    def _render_table(self, tab_name: str, rows):
        table = self._tables.get(tab_name)
        if not table:
            return
        table.setRowCount(len(rows))
        for row_idx, item in enumerate(rows):
            prop = str(item[0])
            val = str(item[1]) if len(item) > 1 else ""
            cat = str(item[2]) if len(item) > 2 else "General"
            
            p_item = QTableWidgetItem(prop)
            v_item = QTableWidgetItem(val)
            c_item = QTableWidgetItem(cat)
            
            c_item.setForeground(Qt.gray)
            table.setItem(row_idx, 0, p_item)
            table.setItem(row_idx, 1, v_item)
            table.setItem(row_idx, 2, c_item)

    def _apply_filter(self, filter_text: str):
        query = (filter_text or "").strip().lower()
        for tab_name, rows in self._all_rows.items():
            if not query:
                filtered = rows
            else:
                filtered = [
                    r for r in rows
                    if query in str(r[0]).lower() or query in str(r[1]).lower() or (len(r) > 2 and query in str(r[2]).lower())
                ]
            self._render_table(tab_name, filtered)

    def _on_detect_anomalies(self):
        from services.app_state import get_app_state
        ctx = get_app_state().context
        if not ctx or not ctx.document:
            QMessageBox.warning(self, "No Document", "Please load a document first.")
            return
            
        from services.metadata_service import detect_anomalies
        anomalies = detect_anomalies(ctx.document)
        if anomalies:
            msg = "Forensic Anomalies Identified:\n\n"
            for a in anomalies:
                msg += f"• [{a['severity'].upper()}] {a['finding']}\n"
            QMessageBox.information(self, "Metadata Anomaly Analysis", msg)
        else:
            QMessageBox.information(self, "Metadata Anomaly Analysis", "No suspicious metadata discrepancies or anomalies detected.")

    def _on_sanitize(self):
        from services.app_state import get_app_state
        ctx = get_app_state().context
        if not ctx or not ctx.document:
            QMessageBox.warning(self, "No Document", "Please load a document first.")
            return
            
        from PyQt5.QtWidgets import QFileDialog
        out_path, _ = QFileDialog.getSaveFileName(self, "Save Derivative Sanitized Copy", "", "All Files (*.*)")
        if out_path:
            from services.metadata_service import sanitize_metadata
            success = sanitize_metadata(ctx.document.file_path, out_path)
            if success:
                from services.hash_service import calculate_sha256
                san_hash = calculate_sha256(out_path) or "Calculated"
                self._lbl_san_hash.setText(f"Sanitized SHA-256:\n{san_hash}")
                
                QMessageBox.information(
                    self, "Sanitization Complete",
                    f"Metadata stripped successfully.\n\n"
                    f"Saved derivative copy to:\n{out_path}\n\n"
                    f"New SHA-256:\n{san_hash}\n\n"
                    f"Original evidence remains intact and unchanged."
                )
                from services.db_service import get_db
                if ctx.evidence:
                    get_db().add_processing_history(
                        ctx.evidence.evidence_id,
                        "Metadata Sanitization",
                        f"Derivative copy created at {out_path} with SHA-256: {san_hash}"
                    )
            else:
                QMessageBox.warning(self, "Sanitization Failed", "Could not strip metadata from this document format.")

    def _on_export_report(self):
        if not self._current_doc:
            QMessageBox.warning(self, "No Data", "No metadata loaded to export.")
            return
        from PyQt5.QtWidgets import QFileDialog
        out_path, _ = QFileDialog.getSaveFileName(self, "Export Metadata Report", "metadata_report.txt", "Text Files (*.txt);;All Files (*.*)")
        if not out_path:
            return
        try:
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(f"ANTORDRISHTI FORENSIC METADATA REPORT\n")
                f.write(f"Document: {self._current_doc.file_name}\n")
                f.write(f"Original SHA-256: {self._current_doc.sha256}\n")
                f.write("="*60 + "\n\n")
                for tab_name, rows in self._all_rows.items():
                    f.write(f"[{tab_name}]\n")
                    for r in rows:
                        prop = r[0]
                        val = r[1] if len(r) > 1 else ""
                        cat = r[2] if len(r) > 2 else ""
                        f.write(f"  {prop:30} : {val:40} ({cat})\n")
                    f.write("\n")
            QMessageBox.information(self, "Report Exported", f"Metadata report exported to:\n{out_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Failed to export report: {str(e)}")

