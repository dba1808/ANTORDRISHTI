"""
Antordrishti — Noise Pattern Analysis Page
Functional high-pass noise analysis, noise residual colormap visualization,
local variance calculation, and image export.
"""

from typing import Optional
import numpy as np

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea,
    QMessageBox, QFileDialog, QComboBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage

from app.theme import Colors, Spacing
from ui.widgets.common import (
    SectionLabel, ActionButton, InfoRow, Separator, LabeledSlider
)
from ui.viewer.document_viewer import DocumentViewer
import services.image_processing as ip


class NoiseAnalysisPage(QWidget):
    """Noise Pattern Analysis page."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)  # type: ignore[arg-type]
        self.setStyleSheet("background-color: #FFFFFF;")

        self._current_path = ""
        self._original_img: Optional[QImage] = None
        self._noise_map_img: Optional[QImage] = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Center Workspace with DocumentViewer
        center = QWidget()
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(0)

        title_bar = QWidget()
        title_bar.setFixedHeight(48)
        title_bar.setStyleSheet(f"background-color: #FFFFFF; border-bottom: 1px solid {Colors.BORDER_LIGHT};")
        tb = QHBoxLayout(title_bar)
        tb.setContentsMargins(Spacing.LG, 0, Spacing.LG, 0)
        t = QLabel("Noise Pattern & Sensor Variance Analysis")
        t.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {Colors.TEXT_PRIMARY};")
        tb.addWidget(t)
        tb.addStretch()
        center_layout.addWidget(title_bar)

        self.viewer = DocumentViewer()
        center_layout.addWidget(self.viewer, 1)

        layout.addWidget(center, 1)

        # Right Controls Panel
        right_panel = QScrollArea()
        right_panel.setWidgetResizable(True)
        right_panel.setFixedWidth(270)
        right_panel.setFrameShape(QFrame.Shape.NoFrame)
        right_panel.setStyleSheet("background-color: #FFFFFF; border-left: 1px solid #E2E8F0;")

        ctrl = QWidget()
        ctrl.setStyleSheet("background-color: #FFFFFF;")
        c_layout = QVBoxLayout(ctrl)
        c_layout.setContentsMargins(12, 12, 12, 12)
        c_layout.setSpacing(8)

        # Disclaimer
        disclaimer = QFrame()
        disclaimer.setStyleSheet("background-color: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 4px; padding: 6px;")
        disc_layout = QVBoxLayout(disclaimer)
        disc_layout.setContentsMargins(4, 4, 4, 4)
        disc_text = QLabel(
            "Noise analysis visualizes high-frequency noise variance across document regions. "
            "Inconsistencies may indicate splicing or multiple source origins."
        )
        disc_text.setStyleSheet("font-size: 10px; color: #1E40AF;")
        disc_text.setWordWrap(True)
        disc_layout.addWidget(disc_text)
        c_layout.addWidget(disclaimer)

        c_layout.addWidget(SectionLabel("Noise Metrics"))
        self.row_variance = InfoRow("Noise Variance", "—")
        self.row_level = InfoRow("Noise Level", "—")
        self.row_status = InfoRow("Status", "Not Analyzed")
        c_layout.addWidget(self.row_variance)
        c_layout.addWidget(self.row_level)
        c_layout.addWidget(self.row_status)

        c_layout.addWidget(Separator())
        c_layout.addWidget(SectionLabel("Noise Map Controls"))

        self.scale_slider = LabeledSlider("Amplification Scale", 1, 30, 8)
        c_layout.addWidget(self.scale_slider)

        btn_extract = ActionButton("Generate Noise Map", primary=True)
        btn_extract.clicked.connect(self.generate_noise_analysis)
        c_layout.addWidget(btn_extract)

        btn_reset = ActionButton("Reset to Original")
        btn_reset.clicked.connect(self.reset_to_original)
        c_layout.addWidget(btn_reset)

        btn_export = ActionButton("Export Noise Map")
        btn_export.clicked.connect(self.export_noise_map)
        c_layout.addWidget(btn_export)

        c_layout.addStretch()
        right_panel.setWidget(ctrl)
        layout.addWidget(right_panel)

    def load_document(self, file_path: str):
        self._current_path = file_path
        self.viewer.load_file(file_path)
        img = self.viewer.get_current_image()
        if img:
            self._original_img = img.copy()
            self._noise_map_img = None
            self._calculate_metrics(img)

    def _calculate_metrics(self, qimg: QImage):
        cv_img = ip.qimage_to_cv(qimg)
        if cv_img is not None:
            var = ip.estimate_noise_variance(cv_img)
            self.row_variance.set_value(f"{var:.2f}")
            if var < 50:
                level_str = "Low Noise (Smooth/Compressed)"
            elif var < 200:
                level_str = "Moderate Noise"
            else:
                level_str = "High Noise / Detailed Texture"
            self.row_level.set_value(level_str)
            self.row_status.set_value("Analysis Available")

    def generate_noise_analysis(self):
        current_img = self._original_img or self.viewer.get_current_image()
        if not current_img:
            QMessageBox.information(self, "No Document", "Please load an image or PDF document first.")
            return

        cv_img = ip.qimage_to_cv(current_img)
        if cv_img is None:
            return

        scale = self.scale_slider.value()
        noise_map = ip.generate_noise_map(cv_img, scale=scale)
        out_qimg = ip.cv_to_qimage(noise_map)
        if out_qimg:
            self._noise_map_img = out_qimg
            self.viewer.set_qimage(out_qimg, f"Noise Map ({scale}x)")
            self.row_status.set_value("Noise Map Generated")

    def reset_to_original(self):
        if self._original_img:
            self.viewer.set_qimage(self._original_img.copy(), "Original")
            self.row_status.set_value("Original View")

    def export_noise_map(self):
        img_to_save = self._noise_map_img or self.viewer.get_current_image()
        if not img_to_save:
            QMessageBox.information(self, "Export", "No noise map image available to export.")
            return

        out_path, _ = QFileDialog.getSaveFileName(
            self, "Export Noise Map Image", "noise_map_analysis.png",
            "PNG Image (*.png);;JPEG Image (*.jpg);;TIFF Image (*.tiff)"
        )
        if out_path:
            if img_to_save.save(out_path):
                QMessageBox.information(self, "Saved", f"Noise map saved successfully:\n{out_path}")
