"""
Antordrishti — Interactive Forensic Histogram Widget
Interactive PyQt5 canvas displaying the histogram plot image with live mouse cursor tracking,
intensity inspection tooltips, and responsive resizing.
"""

from typing import Optional
import numpy as np
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, pyqtSignal, QPoint
from PyQt5.QtGui import QImage, QPixmap, QMouseEvent

from services.histogram_service import HistogramData, render_histogram_plot_image
import services.image_processing as ip


class ForensicHistogramWidget(QLabel):
    """Interactive canvas widget for high-resolution histogram visualization."""
    
    bin_hovered = pyqtSignal(int)  # Emits hovered intensity bin (0-255)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setMinimumSize(450, 240)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("background-color: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 6px;")

        self._hist_data: Optional[HistogramData] = None
        self._mode: str = "rgb"
        self._log_scale: bool = False
        self._show_cdf: bool = False
        self._hover_bin: Optional[int] = None
        self._rendered_bgr: Optional[np.ndarray] = None
        
        self.setText("Histogram will display when evidence is loaded.")

    def set_data(
        self,
        hist_data: Optional[HistogramData],
        mode: str = "rgb",
        log_scale: bool = False,
        show_cdf: bool = False
    ):
        """Update histogram dataset and redraw."""
        self._hist_data = hist_data
        self._mode = mode
        self._log_scale = log_scale
        self._show_cdf = show_cdf
        self._hover_bin = None
        self._redraw()

    def set_mode(self, mode: str):
        self._mode = mode
        self._redraw()

    def set_log_scale(self, log_scale: bool):
        self._log_scale = log_scale
        self._redraw()

    def set_show_cdf(self, show_cdf: bool):
        self._show_cdf = show_cdf
        self._redraw()

    def clear(self):
        self._hist_data = None
        self._rendered_bgr = None
        self._hover_bin = None
        self.setText("NO EVIDENCE LOADED\n\nOpen an image or PDF document to perform forensic histogram analysis.")

    def _redraw(self):
        if self._hist_data is None or not self._hist_data.invariant_passed:
            if self._hist_data and self._hist_data.error_message:
                self.setText(f"HISTOGRAM UNAVAILABLE\n\n{self._hist_data.error_message}")
            else:
                self.setText("NO EVIDENCE LOADED\n\nOpen an image or PDF document to perform forensic histogram analysis.")
            return

        w = max(450, self.width())
        h = max(240, self.height())

        bgr = render_histogram_plot_image(
            self._hist_data,
            mode=self._mode,
            log_scale=self._log_scale,
            show_cdf=self._show_cdf,
            width=w,
            height=h,
            hover_bin=self._hover_bin
        )
        self._rendered_bgr = bgr
        qimg = ip.cv_to_qimage(bgr)
        if qimg and not qimg.isNull():
            self.setPixmap(QPixmap.fromImage(qimg))

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._hist_data is None or self.width() <= 0:
            return

        # Calculate hovered intensity bin (0-255) based on plot padding
        pad_left = 60
        pad_right = 50
        plot_w = self.width() - pad_left - pad_right
        
        pos_x = event.pos().x()
        if pad_left <= pos_x <= pad_left + plot_w and plot_w > 0:
            rel_x = pos_x - pad_left
            bin_idx = int(round((rel_x / float(plot_w)) * 255.0))
            bin_idx = max(0, min(255, bin_idx))
            if bin_idx != self._hover_bin:
                self._hover_bin = bin_idx
                self.bin_hovered.emit(bin_idx)
                self._redraw()
        else:
            if self._hover_bin is not None:
                self._hover_bin = None
                self.bin_hovered.emit(-1)
                self._redraw()

    def leaveEvent(self, event):
        if self._hover_bin is not None:
            self._hover_bin = None
            self.bin_hovered.emit(-1)
            self._redraw()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._redraw()
