"""
Antordrishti — Error Level Analysis (ELA) Page
Professional ELA examination with synchronized view modes (Processed, Original, Split, Overlay),
JPEG quality & scale controls, forensic disclaimer, and export capabilities.
"""

from typing import Optional
import numpy as np

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QTabBar, QStackedWidget, QSplitter, QFrame, QScrollArea,
    QMessageBox, QFileDialog
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage

from app.theme import Colors, Spacing
from ui.widgets.common import (
    LabeledSlider, SectionLabel, ActionButton, Separator
)
from ui.viewer.document_viewer import DocumentViewer
from services.ela_service import generate_ela, generate_ela_from_array
import services.image_processing as ip


class ELAPage(QWidget):
    """Error Level Analysis page with large viewer and clean controls."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self._current_path = ""
        self._original_image: Optional[QImage] = None
        self._ela_image: Optional[QImage] = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet("QSplitter::handle { background-color: #E2E8F0; width: 1px; }")

        # ── Center: ELA Workspace ────────────────────────────
        center = QWidget()
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(0)

        # Title bar
        title_bar = QWidget()
        title_bar.setFixedHeight(38)
        title_bar.setStyleSheet("""
            background-color: #FFFFFF;
            border-bottom: 1px solid #E2E8F0;
        """)
        tb_layout = QHBoxLayout(title_bar)
        tb_layout.setContentsMargins(16, 0, 16, 0)
        title = QLabel("ELA EXAMINATION")
        title.setStyleSheet("font-size: 13px; font-weight: 700; color: #0F172A; letter-spacing: 0.5px;")
        tb_layout.addWidget(title)
        tb_layout.addStretch()
        center_layout.addWidget(title_bar)

        # Main viewer (with Processed / Original / Split / Overlay built-in)
        self.viewer = DocumentViewer()
        center_layout.addWidget(self.viewer, 1)

        splitter.addWidget(center)

        # ── Right: ELA Controls Panel ────────────────────────
        right_panel = QScrollArea()
        right_panel.setWidgetResizable(True)
        right_panel.setFixedWidth(280)
        right_panel.setFrameShape(QFrame.Shape.NoFrame)
        right_panel.setStyleSheet("""
            QScrollArea {
                background-color: #FFFFFF;
                border-left: 1px solid #E2E8F0;
            }
        """)

        controls = QWidget()
        controls.setStyleSheet("background: #FFFFFF;")
        ctrl_layout = QVBoxLayout(controls)
        ctrl_layout.setContentsMargins(14, 14, 14, 14)
        ctrl_layout.setSpacing(12)

        # Explanatory Forensic Note (Clean soft container)
        disclaimer = QFrame()
        disclaimer.setStyleSheet("""
            QFrame {
                background-color: #FAF4E6;
                border: 1px solid #F5EACB;
                border-radius: 6px;
                padding: 4px;
            }
        """)
        disc_layout = QVBoxLayout(disclaimer)
        disc_layout.setContentsMargins(8, 8, 8, 8)
        disc_text = QLabel(
            "Forensic Note: Error Level Analysis highlights JPEG compression rate differences. "
            "Higher error levels indicate potential resaving, splicing, or localized editing."
        )
        disc_text.setStyleSheet("font-size: 10px; color: #785F23; line-height: 1.3;")
        disc_text.setWordWrap(True)
        disc_layout.addWidget(disc_text)
        ctrl_layout.addWidget(disclaimer)

        ctrl_layout.addWidget(SectionLabel("ELA Parameters"))

        self._quality = LabeledSlider("JPEG Quality", 1, 100, 75)
        ctrl_layout.addWidget(self._quality)

        self._scale = LabeledSlider("ELA Scale Multiplier", 1, 50, 15)
        ctrl_layout.addWidget(self._scale)

        ctrl_layout.addWidget(Separator())
        ctrl_layout.addWidget(SectionLabel("Actions"))

        btn_gen = ActionButton("Generate ELA", primary=True)
        btn_gen.clicked.connect(self.generate_ela_analysis)
        ctrl_layout.addWidget(btn_gen)

        btn_reset = ActionButton("Reset to Original")
        btn_reset.clicked.connect(self.reset_to_original)
        ctrl_layout.addWidget(btn_reset)

        btn_save = ActionButton("Save Result")
        btn_save.clicked.connect(self.save_ela_result)
        ctrl_layout.addWidget(btn_save)

        ctrl_layout.addStretch()
        right_panel.setWidget(controls)
        splitter.addWidget(right_panel)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)
        layout.addWidget(splitter)

    def load_document(self, file_path: str):
        """Load a file for ELA inspection."""
        self._current_path = file_path
        self.viewer.load_file(file_path)
        img = self.viewer.get_current_image()
        if img:
            self._original_image = img.copy()
            self._ela_image = None

    def set_qimage(self, image: QImage, file_path: str = ""):
        """Set an in-memory image for ELA."""
        self._current_path = file_path
        self._original_image = image.copy()
        self._ela_image = None
        self.viewer.set_qimage(image, "Original")

    def generate_ela_analysis(self):
        """Generate ELA on current document/image."""
        quality = self._quality.value()
        scale = self._scale.value()

        current_img = self.viewer.get_current_image()
        if not current_img or current_img.isNull():
            QMessageBox.information(
                self, "No Document Loaded",
                "Please load an image document first to generate ELA."
            )
            return

        cv_img = ip.qimage_to_cv(current_img)
        if cv_img is None:
            QMessageBox.warning(self, "Conversion Error", "Failed to process image buffer.")
            return

        ela_cv = generate_ela_from_array(cv_img, quality=quality, scale=scale)
        if ela_cv is not None:
            out_qimg = ip.cv_to_qimage(ela_cv)
            if out_qimg and not out_qimg.isNull():
                self._ela_image = out_qimg
                self.viewer.push_processed_step(f"ELA (Q={quality}, S={scale})", out_qimg)
                self.viewer.set_mode("processed")
                return

        QMessageBox.warning(self, "ELA Error", "Failed to compute Error Level Analysis.")

    def reset_to_original(self):
        """Reset the ELA viewer back to the original source evidence."""
        self.viewer.reset_to_original()

    def save_ela_result(self):
        """Export current ELA result image."""
        img = self.viewer.get_current_image()
        if not img or img.isNull():
            QMessageBox.information(self, "Nothing to Save", "No active ELA result available to save.")
            return

        out_path, _ = QFileDialog.getSaveFileName(
            self, "Save ELA Result Image", "ela_result.png",
            "PNG Image (*.png);;JPEG Image (*.jpg);;TIFF Image (*.tiff)"
        )
        if out_path:
            if img.save(out_path):
                QMessageBox.information(self, "Result Saved", f"ELA result saved successfully:\n{out_path}")
