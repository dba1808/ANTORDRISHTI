"""
Antordrishti — Real-Time Forensic Histogram Analysis Page
Provides complete forensic histogram examination with real-time context synchronization,
deterministic PDF rendering, 256-bin channel modes, log-scale visualization, CDF overlay,
saturated clipping analysis, tonal distribution, and CSV/PNG/TXT export capabilities.
"""

import os
from typing import Optional, Dict, Any
import numpy as np

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QFrame, QScrollArea, QSplitter, QMessageBox, QFileDialog,
    QCheckBox, QPushButton, QGridLayout
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt5.QtGui import QFont, QCursor

from ui.widgets.common import (
    SectionLabel, ActionButton, Separator, InfoRow
)
from ui.widgets.histogram_widget import ForensicHistogramWidget
from services.histogram_service import (
    HistogramData, extract_pixel_array_from_evidence, calculate_forensic_histogram,
    export_histogram_csv, export_histogram_txt, render_histogram_plot_image
)
from services.db_service import get_db
import services.image_processing as ip


class HistogramWorker(QThread):
    """Background worker thread for high-resolution histogram calculation."""
    finished_signal = pyqtSignal(object)  # Emits HistogramData

    def __init__(self, file_path: str, page_num: int, dpi: int, channel_mode: str, source_label: str, case_id: str, evidence_id: str, sha256: str):
        super().__init__()
        self.file_path = file_path
        self.page_num = page_num
        self.dpi = dpi
        self.channel_mode = channel_mode
        self.source_label = source_label
        self.case_id = case_id
        self.evidence_id = evidence_id
        self.sha256 = sha256

    def run(self):
        img_np, info = extract_pixel_array_from_evidence(self.file_path, self.page_num, self.dpi)
        if img_np is None:
            hist_data = HistogramData(
                file_path=self.file_path,
                error_message=info.get("error", "Failed to load evidence array."),
                invariant_passed=False
            )
        else:
            hist_data = calculate_forensic_histogram(
                pixel_array=img_np,
                info=info,
                channel_mode=self.channel_mode,
                source_label=self.source_label,
                case_id=self.case_id,
                evidence_id=self.evidence_id,
                sha256=self.sha256
            )
        self.finished_signal.emit(hist_data)


class HistogramPage(QWidget):
    """Standalone Forensic Histogram Analysis Workspace."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_context = None
        self._current_path = ""
        self._current_page = 0
        self._total_pages = 1
        self._hist_data: Optional[HistogramData] = None
        self._worker: Optional[HistogramWorker] = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Top Header Banner ────────────────────────────────
        header_bar = QWidget()
        header_bar.setFixedHeight(42)
        header_bar.setStyleSheet("background-color: #FFFFFF; border-bottom: 1px solid #E2E8F0;")
        hb_layout = QHBoxLayout(header_bar)
        hb_layout.setContentsMargins(16, 0, 16, 0)

        self._lbl_header_title = QLabel("REAL-TIME HISTOGRAM ANALYZER")
        self._lbl_header_title.setStyleSheet("font-size: 13px; font-weight: 800; color: #0F172A; letter-spacing: 0.5px;")
        hb_layout.addWidget(self._lbl_header_title)

        hb_layout.addStretch()

        self._lbl_header_meta = QLabel("No document loaded")
        self._lbl_header_meta.setStyleSheet("font-size: 11px; font-weight: 500; color: #64748B;")
        hb_layout.addWidget(self._lbl_header_meta)
        layout.addWidget(header_bar)

        # ── Main Splitter: Canvas vs Controls ────────────────
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet("QSplitter::handle { background-color: #E2E8F0; width: 1px; }")

        # ── Left: Main Histogram Plot Canvas Workspace ───────
        left_area = QWidget()
        left_area.setStyleSheet("background-color: #F8FAFC;")
        la_layout = QVBoxLayout(left_area)
        la_layout.setContentsMargins(16, 14, 16, 14)
        la_layout.setSpacing(12)

        # Toolbar controls above chart
        tb_card = QFrame()
        tb_card.setStyleSheet("background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 6px; padding: 4px;")
        tb_layout = QHBoxLayout(tb_card)
        tb_layout.setContentsMargins(10, 6, 10, 6)
        tb_layout.setSpacing(12)

        tb_layout.addWidget(QLabel("Mode:"))
        self._combo_mode = QComboBox()
        self._combo_mode.addItems(["RGB Overlay", "Grayscale", "Red Channel", "Green Channel", "Blue Channel", "Luminance", "Alpha Channel"])
        self._combo_mode.currentIndexChanged.connect(self._on_mode_changed)
        tb_layout.addWidget(self._combo_mode)

        tb_layout.addWidget(QLabel("Source:"))
        self._combo_source = QComboBox()
        self._combo_source.addItems(["Original Evidence", "OCR Preprocessed", "ELA Result"])
        self._combo_source.currentIndexChanged.connect(self._on_source_changed)
        tb_layout.addWidget(self._combo_source)

        self._chk_log_scale = QCheckBox("Log Scale (Y)")
        self._chk_log_scale.setToolTip("Toggle Logarithmic Y-axis scaling for peak visualization")
        self._chk_log_scale.stateChanged.connect(self._on_visualization_option_changed)
        tb_layout.addWidget(self._chk_log_scale)

        self._chk_cdf = QCheckBox("CDF Overlay")
        self._chk_cdf.setToolTip("Toggle Cumulative Distribution Function curve")
        self._chk_cdf.stateChanged.connect(self._on_visualization_option_changed)
        tb_layout.addWidget(self._chk_cdf)

        tb_layout.addWidget(QLabel("PDF DPI:"))
        self._combo_dpi = QComboBox()
        self._combo_dpi.addItems(["72 DPI", "150 DPI (Standard)", "300 DPI (High)"])
        self._combo_dpi.setCurrentIndex(1)
        self._combo_dpi.currentIndexChanged.connect(self._on_dpi_changed)
        tb_layout.addWidget(self._combo_dpi)

        tb_layout.addStretch()
        la_layout.addWidget(tb_card)

        # Interactive Histogram Canvas Widget
        self._hist_widget = ForensicHistogramWidget()
        self._hist_widget.bin_hovered.connect(self._on_bin_hovered)
        la_layout.addWidget(self._hist_widget, 1)

        # Live Hover Footer Inspection Line
        self._lbl_hover_info = QLabel("Hover cursor over graph to inspect exact intensity frequencies.")
        self._lbl_hover_info.setStyleSheet("font-size: 11px; font-weight: 600; color: #475569; padding: 4px 8px; background: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 4px;")
        la_layout.addWidget(self._lbl_hover_info)

        splitter.addWidget(left_area)

        # ── Right: Analytical Statistics Panel ──────────────
        right_panel = QScrollArea()
        right_panel.setWidgetResizable(True)
        right_panel.setFixedWidth(340)
        right_panel.setFrameShape(QFrame.Shape.NoFrame)
        right_panel.setStyleSheet("QScrollArea { background-color: #FFFFFF; border-left: 1px solid #E2E8F0; }")

        right_widget = QWidget()
        right_widget.setStyleSheet("background: #FFFFFF;")
        rw_layout = QVBoxLayout(right_widget)
        rw_layout.setContentsMargins(14, 14, 14, 14)
        rw_layout.setSpacing(12)

        # Provenance Invariant Badge Card
        self._card_invariant = QFrame()
        self._card_invariant.setStyleSheet("background: #FAF4E6; border: 1px solid #B08D3A; border-radius: 6px; padding: 6px;")
        ci_layout = QVBoxLayout(self._card_invariant)
        ci_layout.setContentsMargins(8, 6, 8, 6)
        self._lbl_invariant_status = QLabel("INVARIANT: VERIFIED")
        self._lbl_invariant_status.setStyleSheet("font-size: 11px; font-weight: 700; color: #785F23;")
        self._lbl_invariant_desc = QLabel("Pixel count exactly matches sum of histogram bins (width × height).")
        self._lbl_invariant_desc.setStyleSheet("font-size: 10px; color: #5C4717;")
        self._lbl_invariant_desc.setWordWrap(True)
        ci_layout.addWidget(self._lbl_invariant_status)
        ci_layout.addWidget(self._lbl_invariant_desc)
        rw_layout.addWidget(self._card_invariant)

        # Statistics Card
        rw_layout.addWidget(SectionLabel("Numerical Statistics"))
        stats_card = QFrame()
        stats_card.setStyleSheet("background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; padding: 6px;")
        sc_layout = QGridLayout(stats_card)
        sc_layout.setContentsMargins(8, 6, 8, 6)
        sc_layout.setSpacing(6)

        self._info_pixels = InfoRow("Pixels", "—")
        self._info_mean = InfoRow("Mean", "—")
        self._info_median = InfoRow("Median", "—")
        self._info_std = InfoRow("Std Dev", "—")
        self._info_minmax = InfoRow("Min / Max", "—")
        self._info_drange = InfoRow("Dyn Range", "—")

        sc_layout.addWidget(self._info_pixels, 0, 0)
        sc_layout.addWidget(self._info_mean, 0, 1)
        sc_layout.addWidget(self._info_median, 1, 0)
        sc_layout.addWidget(self._info_std, 1, 1)
        sc_layout.addWidget(self._info_minmax, 2, 0)
        sc_layout.addWidget(self._info_drange, 2, 1)
        rw_layout.addWidget(stats_card)

        # Clipping / Saturation Card
        rw_layout.addWidget(SectionLabel("Clipping & Saturation"))
        clip_card = QFrame()
        clip_card.setStyleSheet("background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; padding: 6px;")
        cc_layout = QVBoxLayout(clip_card)
        cc_layout.setContentsMargins(8, 6, 8, 6)
        cc_layout.setSpacing(4)

        self._info_black_clip = InfoRow("Black Clip (0)", "—")
        self._info_white_clip = InfoRow("White Clip (255)", "—")
        self._info_channel_clip = InfoRow("R/G/B Clipping", "—")
        cc_layout.addWidget(self._info_black_clip)
        cc_layout.addWidget(self._info_white_clip)
        cc_layout.addWidget(self._info_channel_clip)
        rw_layout.addWidget(clip_card)

        # Tonal Distribution Card
        rw_layout.addWidget(SectionLabel("Tonal Distribution"))
        tonal_card = QFrame()
        tonal_card.setStyleSheet("background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; padding: 6px;")
        tc_layout = QVBoxLayout(tonal_card)
        tc_layout.setContentsMargins(8, 6, 8, 6)
        tc_layout.setSpacing(4)

        self._info_shadows = InfoRow("Shadows (0–84)", "—")
        self._info_midtones = InfoRow("Midtones (85–170)", "—")
        self._info_highlights = InfoRow("Highlights (171–255)", "—")
        tc_layout.addWidget(self._info_shadows)
        tc_layout.addWidget(self._info_midtones)
        tc_layout.addWidget(self._info_highlights)
        rw_layout.addWidget(tonal_card)

        # Actions Row
        rw_layout.addWidget(Separator())
        rw_layout.addWidget(SectionLabel("Export Actions"))

        btn_refresh = ActionButton("Refresh Analysis")
        btn_refresh.clicked.connect(self._recalculate_histogram)
        rw_layout.addWidget(btn_refresh)

        btn_csv = ActionButton("Export Raw CSV", primary=True)
        btn_csv.clicked.connect(self._export_csv)
        rw_layout.addWidget(btn_csv)

        btn_png = ActionButton("Export High-Res Plot")
        btn_png.clicked.connect(self._export_png)
        rw_layout.addWidget(btn_png)

        btn_txt = ActionButton("Export Forensic Summary TXT")
        btn_txt.clicked.connect(self._export_txt)
        rw_layout.addWidget(btn_txt)

        rw_layout.addStretch()
        right_panel.setWidget(right_widget)
        splitter.addWidget(right_panel)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)
        layout.addWidget(splitter, 1)

    def set_current_context(self, context):
        """Update histogram workspace automatically when context/evidence/page changes."""
        self._current_context = context
        doc = context.document if context else None
        case = context.case if context else None
        evidence = context.evidence if context else None

        if not doc or not doc.file_path or not os.path.exists(doc.file_path):
            self._current_path = ""
            self._hist_data = None
            self._hist_widget.clear()
            self._lbl_header_meta.setText("No document loaded")
            self._reset_statistics_ui()
            return

        # Check if page changed or path changed
        current_page = getattr(doc, "current_page", 1) - 1
        if current_page < 0:
            current_page = 0

        case_info = f"Case: {case.case_name} ({case.case_id})" if case else "No active case"
        evd_info = f"Evidence: {evidence.evidence_id}" if evidence else "Evidence: Unassigned"
        page_info = f"Page {current_page + 1} / {doc.page_count}"
        self._lbl_header_meta.setText(f"{doc.file_name}  •  {page_info}  •  {evd_info}  •  {case_info}")

        if doc.file_path != self._current_path or current_page != self._current_page or self._hist_data is None:
            self._current_path = doc.file_path
            self._current_page = current_page
            self._total_pages = doc.page_count
            self._recalculate_histogram()

    def load_document(self, file_path: str, page_num: int = 0):
        """Direct file loading helper."""
        self._current_path = file_path
        self._current_page = page_num
        self._recalculate_histogram()

    def _recalculate_histogram(self):
        """Launch background worker thread to calculate histogram for current path and page."""
        if not self._current_path or not os.path.exists(self._current_path):
            self._hist_widget.clear()
            self._reset_statistics_ui()
            return

        case_id = ""
        evidence_id = ""
        sha256 = ""
        if self._current_context:
            if self._current_context.case:
                case_id = self._current_context.case.case_id
            if self._current_context.evidence:
                evidence_id = self._current_context.evidence.evidence_id
            if self._current_context.document:
                sha256 = self._current_context.document.sha256

        mode_map = {0: "rgb", 1: "grayscale", 2: "red", 3: "green", 4: "blue", 5: "luminance", 6: "alpha"}
        channel_mode = mode_map.get(self._combo_mode.currentIndex(), "rgb")
        source_label = self._combo_source.currentText()

        dpi_map = {0: 72, 1: 150, 2: 300}
        dpi = dpi_map.get(self._combo_dpi.currentIndex(), 150)

        # Cancel active worker if running
        if self._worker and self._worker.isRunning():
            self._worker.terminate()
            self._worker.wait()

        self._worker = HistogramWorker(
            file_path=self._current_path,
            page_num=self._current_page,
            dpi=dpi,
            channel_mode=channel_mode,
            source_label=source_label,
            case_id=case_id,
            evidence_id=evidence_id,
            sha256=sha256
        )
        self._worker.finished_signal.connect(self._on_histogram_calculated)
        self._worker.start()

    def _on_histogram_calculated(self, hist_data: HistogramData):
        """Receive worker result on main Qt GUI thread."""
        self._hist_data = hist_data
        log_scale = self._chk_log_scale.isChecked()
        show_cdf = self._chk_cdf.isChecked()
        mode_map = {0: "rgb", 1: "grayscale", 2: "red", 3: "green", 4: "blue", 5: "luminance", 6: "alpha"}
        channel_mode = mode_map.get(self._combo_mode.currentIndex(), "rgb")

        self._hist_widget.set_data(hist_data, mode=channel_mode, log_scale=log_scale, show_cdf=show_cdf)
        self._update_statistics_ui(hist_data)

    def _update_statistics_ui(self, hist_data: HistogramData):
        if not hist_data or not hist_data.invariant_passed:
            self._reset_statistics_ui()
            return

        stats = hist_data.stats
        clip = hist_data.clipping
        tonal = hist_data.tonal

        self._info_pixels.set_value(f"{stats.get('pixel_count', 0):,}")
        self._info_mean.set_value(str(stats.get('mean', '—')))
        self._info_median.set_value(str(stats.get('median', '—')))
        self._info_std.set_value(str(stats.get('std_dev', '—')))
        self._info_minmax.set_value(f"{stats.get('min')} / {stats.get('max')}")
        self._info_drange.set_value(str(stats.get('dynamic_range', '—')))

        self._info_black_clip.set_value(f"{clip.get('black_count', 0):,} ({clip.get('black_pct', 0)}%)")
        self._info_white_clip.set_value(f"{clip.get('white_count', 0):,} ({clip.get('white_pct', 0)}%)")

        if "red_black_pct" in clip:
            self._info_channel_clip.set_value(f"R:{clip.get('red_white_pct')}% G:{clip.get('green_white_pct')}% B:{clip.get('blue_white_pct')}%")
        else:
            self._info_channel_clip.set_value("N/A")

        self._info_shadows.set_value(f"{tonal.get('shadows_count', 0):,} ({tonal.get('shadows_pct', 0)}%)")
        self._info_midtones.set_value(f"{tonal.get('midtones_count', 0):,} ({tonal.get('midtones_pct', 0)}%)")
        self._info_highlights.set_value(f"{tonal.get('highlights_count', 0):,} ({tonal.get('highlights_pct', 0)}%)")

        if hist_data.invariant_passed:
            self._card_invariant.setStyleSheet("background: #F0FDF4; border: 1px solid #86EFAC; border-radius: 6px; padding: 6px;")
            self._lbl_invariant_status.setText("INVARIANT: VERIFIED ✓")
            self._lbl_invariant_status.setStyleSheet("font-size: 11px; font-weight: 700; color: #166534;")
            self._lbl_invariant_desc.setText("Bin count sum exactly equals total evidence pixels (W × H).")
        else:
            self._card_invariant.setStyleSheet("background: #FEF2F2; border: 1px solid #FCA5A5; border-radius: 6px; padding: 6px;")
            self._lbl_invariant_status.setText("INVARIANT: FAILED ✕")
            self._lbl_invariant_status.setStyleSheet("font-size: 11px; font-weight: 700; color: #991B1B;")
            self._lbl_invariant_desc.setText(hist_data.invariant_notes or "Pixel count mismatch.")

    def _reset_statistics_ui(self):
        self._info_pixels.set_value("—")
        self._info_mean.set_value("—")
        self._info_median.set_value("—")
        self._info_std.set_value("—")
        self._info_minmax.set_value("—")
        self._info_drange.set_value("—")
        self._info_black_clip.set_value("—")
        self._info_white_clip.set_value("—")
        self._info_channel_clip.set_value("—")
        self._info_shadows.set_value("—")
        self._info_midtones.set_value("—")
        self._info_highlights.set_value("—")

        self._card_invariant.setStyleSheet("background: #FAF4E6; border: 1px solid #B08D3A; border-radius: 6px; padding: 6px;")
        self._lbl_invariant_status.setText("INVARIANT: PENDING")
        self._lbl_invariant_status.setStyleSheet("font-size: 11px; font-weight: 700; color: #785F23;")
        self._lbl_invariant_desc.setText("Awaiting evidence document loading.")

    def _on_mode_changed(self):
        mode_map = {0: "rgb", 1: "grayscale", 2: "red", 3: "green", 4: "blue", 5: "luminance", 6: "alpha"}
        channel_mode = mode_map.get(self._combo_mode.currentIndex(), "rgb")
        self._hist_widget.set_mode(channel_mode)
        if self._hist_data:
            self._recalculate_histogram()

    def _on_source_changed(self):
        self._recalculate_histogram()

    def _on_dpi_changed(self):
        self._recalculate_histogram()

    def _on_visualization_option_changed(self):
        log_scale = self._chk_log_scale.isChecked()
        show_cdf = self._chk_cdf.isChecked()
        self._hist_widget.set_log_scale(log_scale)
        self._hist_widget.set_show_cdf(show_cdf)

    def _on_bin_hovered(self, bin_idx: int):
        if bin_idx < 0 or not self._hist_data or not self._hist_data.invariant_passed:
            self._lbl_hover_info.setText("Hover cursor over graph to inspect exact intensity frequencies.")
            return

        if self._hist_data.hist_red is not None and self._combo_mode.currentIndex() == 0:
            r_c = self._hist_data.hist_red[bin_idx]
            g_c = self._hist_data.hist_green[bin_idx]
            b_c = self._hist_data.hist_blue[bin_idx]
            pct_r = round((r_c / float(self._hist_data.total_pixels)) * 100.0, 2)
            self._lbl_hover_info.setText(f"Intensity {bin_idx}/255  •  Red: {r_c:,} ({pct_r}%)  •  Green: {g_c:,}  •  Blue: {b_c:,}")
        else:
            g_c = self._hist_data.hist_gray[bin_idx] if self._hist_data.hist_gray is not None else 0
            pct_g = round((g_c / float(self._hist_data.total_pixels)) * 100.0, 2)
            self._lbl_hover_info.setText(f"Intensity {bin_idx}/255  •  Pixel Frequency: {g_c:,} ({pct_g}% of total pixels)")

    def _export_csv(self):
        if not self._hist_data or not self._hist_data.invariant_passed:
            QMessageBox.warning(self, "No Histogram Data", "Please load active evidence to export histogram CSV.")
            return

        default_name = f"histogram_{os.path.splitext(self._hist_data.file_name)[0]}_page{self._hist_data.page_num}.csv"
        out_path, _ = QFileDialog.getSaveFileName(self, "Export Histogram Raw CSV", default_name, "CSV Files (*.csv)")
        if out_path:
            if export_histogram_csv(self._hist_data, out_path):
                QMessageBox.information(self, "Export Successful", f"Histogram raw CSV exported cleanly:\n{out_path}")
            else:
                QMessageBox.critical(self, "Export Failed", f"Could not write CSV to path:\n{out_path}")

    def _export_png(self):
        if not self._hist_data or not self._hist_data.invariant_passed:
            QMessageBox.warning(self, "No Histogram Data", "Please load active evidence to export histogram plot.")
            return

        default_name = f"histogram_plot_{os.path.splitext(self._hist_data.file_name)[0]}_page{self._hist_data.page_num}.png"
        out_path, _ = QFileDialog.getSaveFileName(self, "Export High-Res Plot Image", default_name, "PNG Image (*.png);;JPEG Image (*.jpg)")
        if out_path:
            mode_map = {0: "rgb", 1: "grayscale", 2: "red", 3: "green", 4: "blue", 5: "luminance", 6: "alpha"}
            channel_mode = mode_map.get(self._combo_mode.currentIndex(), "rgb")
            bgr = render_histogram_plot_image(
                self._hist_data,
                mode=channel_mode,
                log_scale=self._chk_log_scale.isChecked(),
                show_cdf=self._chk_cdf.isChecked(),
                width=1200,
                height=650
            )
            qimg = ip.cv_to_qimage(bgr)
            if qimg and qimg.save(out_path):
                QMessageBox.information(self, "Export Successful", f"High-res histogram plot saved successfully:\n{out_path}")
            else:
                QMessageBox.critical(self, "Export Failed", f"Failed to save plot image to:\n{out_path}")

    def _export_txt(self):
        if not self._hist_data or not self._hist_data.invariant_passed:
            QMessageBox.warning(self, "No Histogram Data", "Please load active evidence to export forensic report.")
            return

        default_name = f"histogram_report_{os.path.splitext(self._hist_data.file_name)[0]}_page{self._hist_data.page_num}.txt"
        out_path, _ = QFileDialog.getSaveFileName(self, "Export Forensic Summary TXT", default_name, "Text Files (*.txt)")
        if out_path:
            if export_histogram_txt(self._hist_data, out_path):
                QMessageBox.information(self, "Export Successful", f"Forensic summary report exported successfully:\n{out_path}")
            else:
                QMessageBox.critical(self, "Export Failed", f"Could not write text report to:\n{out_path}")
