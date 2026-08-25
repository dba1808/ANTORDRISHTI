"""
Antordrishti — Error Level Analysis (ELA) Page
Functional ELA inspection with JPEG quality & scale parameters,
disclaimer banner, and save/export capabilities.
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
    """Error Level Analysis page."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self._current_path = ""
        self._original_image: Optional[QImage] = None
        self._ela_image: Optional[QImage] = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Center: ELA Workspace ────────────────────────────
        center = QWidget()
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(0)

        # Title bar
        title_bar = QWidget()
        title_bar.setFixedHeight(36)
        title_bar.setStyleSheet(f"""
            background-color: {Colors.PANEL};
            border-bottom: 1px solid {Colors.BORDER_LIGHT};
        """)
        tb_layout = QHBoxLayout(title_bar)
        tb_layout.setContentsMargins(Spacing.MD, 0, Spacing.MD, 0)
        title = QLabel("Error Level Analysis (ELA)")
        title.setProperty("heading", True)
        tb_layout.addWidget(title)
        tb_layout.addStretch()
        center_layout.addWidget(title_bar)

        # Main viewer
        self.viewer = DocumentViewer()
        center_layout.addWidget(self.viewer, 1)

        layout.addWidget(center, 1)

        # ── Right: ELA Controls ──────────────────────────────
        right_panel = QScrollArea()
        right_panel.setWidgetResizable(True)
        right_panel.setFixedWidth(270)
        right_panel.setFrameShape(QFrame.Shape.NoFrame)
        right_panel.setStyleSheet(f"""
            background-color: {Colors.PANEL};
            border-left: 1px solid {Colors.BORDER};
        """)

        controls = QWidget()
        controls.setStyleSheet("background: transparent;")
        ctrl_layout = QVBoxLayout(controls)
        ctrl_layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        ctrl_layout.setSpacing(Spacing.MD)

        # Disclaimer banner
        disclaimer = QFrame()
        disclaimer.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.INFO_LIGHT};
                border: 1px solid #BBDEFB;
                border-radius: 4px;
                padding: 6px;
            }}
        """)
        disc_layout = QVBoxLayout(disclaimer)
        disc_layout.setContentsMargins(4, 4, 4, 4)
        disc_text = QLabel(
            "Note: ELA highlights JPEG compression rate differences across image regions. "
            "It is a forensic indicator and alone does not prove forgery."
        )
        disc_text.setStyleSheet(f"font-size: 10px; color: {Colors.INFO};")
        disc_text.setWordWrap(True)
        disc_layout.addWidget(disc_text)
        ctrl_layout.addWidget(disclaimer)

        ctrl_layout.addWidget(SectionLabel("ELA Settings"))

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

        btn_save = ActionButton("Save ELA Result")
        btn_save.clicked.connect(self.save_ela_result)
        ctrl_layout.addWidget(btn_save)

        ctrl_layout.addStretch()
        right_panel.setWidget(controls)
        layout.addWidget(right_panel)

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

        current_img = self._original_image or self.viewer.get_current_image()
        if not current_img:
            QMessageBox.information(
                self, "No Image Loaded", "Please open an image or PDF document first."
            )
            return

        ela_bgr = None
        if self._current_path:
            ela_bgr = generate_ela(self._current_path, quality, scale)

        if ela_bgr is None and current_img:
            # Fallback to in-memory array
            cv_img = ip.qimage_to_cv(current_img)
            if cv_img is not None:
                ela_bgr = generate_ela_from_array(cv_img, quality, scale)

        if ela_bgr is not None:
            out_qimage = ip.cv_to_qimage(ela_bgr)
            if out_qimage:
                self._ela_image = out_qimage
                self.viewer.set_qimage(out_qimage, f"ELA (Q={quality}, S={scale}x)")
        else:
            QMessageBox.warning(
                self, "ELA Error", "Failed to compute Error Level Analysis for this image."
            )

    def reset_to_original(self):
        """Restore original image."""
        if self._original_image:
            self.viewer.set_qimage(self._original_image.copy(), "Original")

    def save_ela_result(self):
        """Save the generated ELA image."""
        img_to_save = self._ela_image or self.viewer.get_current_image()
        if not img_to_save:
            QMessageBox.information(
                self, "No Result", "No ELA analysis image available to save."
            )
            return

        out_path, _ = QFileDialog.getSaveFileName(
            self, "Save ELA Result Image", "ela_analysis.png",
            "PNG Image (*.png);;JPEG Image (*.jpg);;TIFF Image (*.tiff)"
        )
        if out_path:
            success = img_to_save.save(out_path)
            if success:
                QMessageBox.information(
                    self, "Saved", f"ELA result saved successfully:\n{out_path}"
                )
            else:
                QMessageBox.critical(
                    self, "Save Error", "Failed to save ELA result file."
                )
