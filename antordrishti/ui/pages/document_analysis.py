"""
Antordrishti — Document Analysis Workspace
Primary forensic workspace integrating:
- Full categorized OpenCV tool panels (Enhancement, Blur/Noise, Threshold/Edges, Color/Channels)
- Dynamic Histogram analyzer with channel switcher and image export
- Analysis History stack with Undo, Redo, and Reset
- Document viewer with Split View & Overlay comparisons
"""

from typing import Optional, List
import numpy as np

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QSplitter, QTabWidget,
    QLabel, QPushButton, QSlider, QSpinBox, QScrollArea, QFrame,
    QMessageBox, QInputDialog, QComboBox, QFileDialog, QListWidget,
    QListWidgetItem
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QImage, QPixmap, QCursor

from app.theme import Colors, Spacing, Sizes
from app.resources import get_icon, Icons
from ui.viewer.document_viewer import DocumentViewer
from ui.viewer.viewer_toolbar import ViewerToolbar
from ui.viewer.layers_panel import LayersPanel
from ui.widgets.common import SectionLabel, ActionButton, LabeledSlider, Separator

import services.image_processing as ip


class ForensicToolsPanel(QWidget):
    """Categorized forensic processing tools side panel."""

    apply_operation = pyqtSignal(str, dict)  # (operation_name, parameters)
    export_histogram_requested = pyqtSignal()
    undo_requested = pyqtSignal()
    redo_requested = pyqtSignal()
    reset_requested = pyqtSignal()
    save_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: #FFFFFF;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Tab Widget for organized categories
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #E2E8F0;
                background-color: #FFFFFF;
            }
            QTabBar::tab {
                background-color: #F8FAFC;
                border: 1px solid #E2E8F0;
                border-bottom: none;
                padding: 6px 10px;
                font-size: 11px;
                font-weight: 600;
                color: #475569;
            }
            QTabBar::tab:selected {
                background-color: #FFFFFF;
                color: #0D7C7C;
                border-bottom: 2px solid #0D7C7C;
            }
        """)

        # Tab 1: OpenCV Tools (Enhancement, Blur, Edges, Channels)
        self.tools_tab = self._build_tools_tab()
        self.tabs.addTab(self.tools_tab, "OpenCV Tools")

        # Tab 2: Histogram Tool
        self.hist_tab = self._build_histogram_tab()
        self.tabs.addTab(self.hist_tab, "Histogram")

        # Tab 3: History & Undo/Redo
        self.history_tab = self._build_history_tab()
        self.tabs.addTab(self.history_tab, "History")

        layout.addWidget(self.tabs, 1)

    def _build_tools_tab(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background-color: #FFFFFF;")

        container = QWidget()
        container.setStyleSheet("background-color: #FFFFFF;")
        c_layout = QVBoxLayout(container)
        c_layout.setContentsMargins(10, 10, 10, 10)
        c_layout.setSpacing(8)

        # ── 1. Enhancement ──
        c_layout.addWidget(SectionLabel("Image Enhancement"))

        btn_gray = ActionButton("Grayscale")
        btn_gray.clicked.connect(lambda: self.apply_operation.emit("grayscale", {}))
        c_layout.addWidget(btn_gray)

        btn_sharp = ActionButton("Sharpen (High-Pass)")
        btn_sharp.clicked.connect(lambda: self.apply_operation.emit("sharpen", {}))
        c_layout.addWidget(btn_sharp)

        btn_resize = ActionButton("Resize...")
        btn_resize.clicked.connect(lambda: self.apply_operation.emit("resize", {}))
        c_layout.addWidget(btn_resize)

        self.bright_slider = LabeledSlider("Brightness", -100, 100, 0)
        self.bright_slider.value_changed.connect(lambda v: self.apply_operation.emit("brightness", {"val": v}))
        c_layout.addWidget(self.bright_slider)

        self.contrast_slider = LabeledSlider("Contrast (%)", 10, 300, 100)
        self.contrast_slider.value_changed.connect(lambda v: self.apply_operation.emit("contrast", {"val": v / 100.0}))
        c_layout.addWidget(self.contrast_slider)

        c_layout.addWidget(Separator())

        # ── 2. Blur & Noise ──
        c_layout.addWidget(SectionLabel("Blur & Noise Analysis"))

        self.gblur_slider = LabeledSlider("Gaussian Blur Kernel", 1, 31, 5)
        btn_gblur = ActionButton("Apply Gaussian Blur")
        btn_gblur.clicked.connect(lambda: self.apply_operation.emit("gaussian_blur", {"k": self.gblur_slider.value()}))
        c_layout.addWidget(self.gblur_slider)
        c_layout.addWidget(btn_gblur)

        self.mblur_slider = LabeledSlider("Median Blur Kernel", 1, 31, 5)
        btn_mblur = ActionButton("Apply Median Blur")
        btn_mblur.clicked.connect(lambda: self.apply_operation.emit("median_blur", {"k": self.mblur_slider.value()}))
        c_layout.addWidget(self.mblur_slider)
        c_layout.addWidget(btn_mblur)

        btn_boxblur = ActionButton("Box Blur")
        btn_boxblur.clicked.connect(lambda: self.apply_operation.emit("box_blur", {"k": 5}))
        c_layout.addWidget(btn_boxblur)

        self.noise_slider = LabeledSlider("Add Noise Amount", 5, 80, 25)
        btn_noise = ActionButton("Add Simulated Noise")
        btn_noise.clicked.connect(lambda: self.apply_operation.emit("add_noise", {"amount": self.noise_slider.value()}))
        c_layout.addWidget(self.noise_slider)
        c_layout.addWidget(btn_noise)

        btn_noise_map = ActionButton("Generate Noise Map (Residual)")
        btn_noise_map.clicked.connect(lambda: self.apply_operation.emit("noise_map", {}))
        c_layout.addWidget(btn_noise_map)

        c_layout.addWidget(Separator())

        # ── 3. Threshold & Edges ──
        c_layout.addWidget(SectionLabel("Threshold & Edge Filters"))

        self.thresh_slider = LabeledSlider("Binary Threshold", 0, 255, 128)
        btn_thresh = ActionButton("Apply Binary Threshold")
        btn_thresh.clicked.connect(lambda: self.apply_operation.emit("binary_threshold", {"thresh": self.thresh_slider.value()}))
        c_layout.addWidget(self.thresh_slider)
        c_layout.addWidget(btn_thresh)

        btn_adapt = ActionButton("Adaptive Gaussian Threshold")
        btn_adapt.clicked.connect(lambda: self.apply_operation.emit("adaptive_threshold", {}))
        c_layout.addWidget(btn_adapt)

        self.canny_low = LabeledSlider("Canny Min Thresh", 0, 255, 50)
        self.canny_high = LabeledSlider("Canny Max Thresh", 0, 255, 150)
        btn_canny = ActionButton("Canny Edge Detection")
        btn_canny.clicked.connect(lambda: self.apply_operation.emit("canny", {
            "low": self.canny_low.value(), "high": self.canny_high.value()
        }))
        c_layout.addWidget(self.canny_low)
        c_layout.addWidget(self.canny_high)
        c_layout.addWidget(btn_canny)

        btn_sobel = ActionButton("Sobel Gradient Magnitude")
        btn_sobel.clicked.connect(lambda: self.apply_operation.emit("sobel", {}))
        c_layout.addWidget(btn_sobel)

        btn_lap = ActionButton("Laplacian 2nd Derivative")
        btn_lap.clicked.connect(lambda: self.apply_operation.emit("laplacian", {}))
        c_layout.addWidget(btn_lap)

        c_layout.addWidget(Separator())

        # ── 4. Color & Channels ──
        c_layout.addWidget(SectionLabel("Color Spaces & Channels"))

        btn_hsv = ActionButton("Convert to HSV")
        btn_hsv.clicked.connect(lambda: self.apply_operation.emit("hsv", {}))
        c_layout.addWidget(btn_hsv)

        ch_layout = QHBoxLayout()
        ch_layout.setSpacing(4)
        btn_r = ActionButton("Red")
        btn_r.clicked.connect(lambda: self.apply_operation.emit("channel", {"ch": "red"}))
        btn_g = ActionButton("Green")
        btn_g.clicked.connect(lambda: self.apply_operation.emit("channel", {"ch": "green"}))
        btn_b = ActionButton("Blue")
        btn_b.clicked.connect(lambda: self.apply_operation.emit("channel", {"ch": "blue"}))
        ch_layout.addWidget(btn_r)
        ch_layout.addWidget(btn_g)
        ch_layout.addWidget(btn_b)
        c_layout.addLayout(ch_layout)

        c_layout.addStretch()
        scroll.setWidget(container)
        return scroll

    def _build_histogram_tab(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background-color: #FFFFFF;")
        layout = QVBoxLayout(w)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        layout.addWidget(SectionLabel("Histogram Channel"))

        self.hist_combo = QComboBox()
        self.hist_combo.addItems(["RGB Overlay", "Red Channel", "Green Channel", "Blue Channel", "Grayscale"])
        self.hist_combo.currentIndexChanged.connect(self._on_hist_channel_changed)
        layout.addWidget(self.hist_combo)

        # Histogram Chart Display Label
        self.hist_chart_label = QLabel()
        self.hist_chart_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hist_chart_label.setStyleSheet("background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 4px;")
        self.hist_chart_label.setFixedHeight(220)
        layout.addWidget(self.hist_chart_label)

        btn_export_hist = ActionButton("Export Histogram Image...", primary=True)
        btn_export_hist.clicked.connect(self.export_histogram_requested.emit)
        layout.addWidget(btn_export_hist)

        btn_refresh_hist = ActionButton("Refresh Histogram")
        btn_refresh_hist.clicked.connect(self._refresh_hist_chart)
        layout.addWidget(btn_refresh_hist)

        layout.addStretch()
        return w

    def _build_history_tab(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background-color: #FFFFFF;")
        layout = QVBoxLayout(w)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        layout.addWidget(SectionLabel("Analysis History"))

        self.history_list = QListWidget()
        self.history_list.setStyleSheet("""
            QListWidget {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 4px;
                font-size: 11px;
            }
            QListWidget::item {
                padding: 6px 8px;
                border-bottom: 1px solid #F1F5F9;
                color: #0F172A;
            }
            QListWidget::item:selected {
                background-color: #E6F4F8;
                color: #0D7C7C;
                font-weight: 700;
            }
        """)
        layout.addWidget(self.history_list, 1)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)
        btn_undo = ActionButton("Undo (Ctrl+Z)")
        btn_undo.clicked.connect(self.undo_requested.emit)
        btn_redo = ActionButton("Redo (Ctrl+Y)")
        btn_redo.clicked.connect(self.redo_requested.emit)
        btn_row.addWidget(btn_undo)
        btn_row.addWidget(btn_redo)
        layout.addLayout(btn_row)

        btn_reset = ActionButton("Reset to Original Evidence", danger=True)
        btn_reset.clicked.connect(self.reset_requested.emit)
        layout.addWidget(btn_reset)

        btn_save = ActionButton("Save Processed Evidence", primary=True)
        btn_save.clicked.connect(self.save_requested.emit)
        layout.addWidget(btn_save)

        return w

    def update_history_list(self, steps: List[str], current_idx: int):
        self.history_list.clear()
        for i, step in enumerate(steps):
            item = QListWidgetItem(f"{i + 1}. {step}")
            self.history_list.addItem(item)
            if i == current_idx:
                self.history_list.setCurrentItem(item)

    def set_histogram_image(self, hist_img: Optional[np.ndarray]):
        if hist_img is not None:
            qimg = ip.cv_to_qimage(hist_img)
            if qimg:
                pix = QPixmap.fromImage(qimg)
                self.hist_chart_label.setPixmap(pix.scaled(
                    self.hist_chart_label.width() - 10, 200,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                ))

    def _on_hist_channel_changed(self):
        self.apply_operation.emit("update_hist", {})

    def _refresh_hist_chart(self):
        self.apply_operation.emit("update_hist", {})


class DocumentAnalysisPage(QWidget):
    """Primary document analysis workspace."""

    save_processed_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: #FFFFFF;")

        self._last_hist_image: Optional[np.ndarray] = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Vertical Tool Strip
        self.viewer_toolbar = ViewerToolbar()
        layout.addWidget(self.viewer_toolbar)

        # Splitter between central DocumentViewer and right ForensicToolsPanel
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Main Document Viewer with Filmstrip & Comparisons
        self.document_viewer = DocumentViewer()
        self.document_viewer.history_updated.connect(self._on_history_updated)
        splitter.addWidget(self.document_viewer)

        # Right Tools Panel (OpenCV Tools, Histogram, History, Layers)
        self.tools_panel = ForensicToolsPanel()
        self.tools_panel.apply_operation.connect(self._execute_operation)
        self.tools_panel.export_histogram_requested.connect(self._export_histogram)
        self.tools_panel.undo_requested.connect(self.document_viewer.undo)
        self.tools_panel.redo_requested.connect(self.document_viewer.redo)
        self.tools_panel.reset_requested.connect(self.document_viewer.reset_to_original)
        self.tools_panel.save_requested.connect(self.save_processed_requested.emit)

        splitter.addWidget(self.tools_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)
        splitter.setSizes([850, 280])

        layout.addWidget(splitter, 1)

        self.viewer_toolbar.tool_selected.connect(self._on_toolbar_selected)

    def _on_history_updated(self, steps: List[str], current_idx: int):
        self.tools_panel.update_history_list(steps, current_idx)
        self._update_histogram()

    def _execute_operation(self, op_name: str, params: dict):
        current_img = self.document_viewer.get_current_image()
        if not current_img:
            if op_name != "update_hist":
                QMessageBox.information(self, "No Document", "Please load an image or PDF document first.")
            return

        cv_img = ip.qimage_to_cv(current_img)
        if cv_img is None:
            return

        res_cv = None
        label = op_name.title()

        try:
            if op_name == "grayscale":
                res_cv = ip.to_grayscale(cv_img)
                label = "Grayscale"
            elif op_name == "sharpen":
                res_cv = ip.sharpen_image(cv_img)
                label = "Sharpen"
            elif op_name == "brightness":
                val = params.get("val", 0)
                res_cv = ip.adjust_brightness(cv_img, val)
                label = f"Brightness ({val:+d})"
            elif op_name == "contrast":
                val = params.get("val", 1.0)
                res_cv = ip.adjust_contrast(cv_img, val)
                label = f"Contrast ({val:.1f}x)"
            elif op_name == "gaussian_blur":
                k = params.get("k", 5)
                res_cv = ip.gaussian_blur(cv_img, k)
                label = f"Gaussian Blur (k={k})"
            elif op_name == "median_blur":
                k = params.get("k", 5)
                res_cv = ip.median_blur(cv_img, k)
                label = f"Median Blur (k={k})"
            elif op_name == "box_blur":
                k = params.get("k", 5)
                res_cv = ip.blur_image(cv_img, k)
                label = f"Box Blur (k={k})"
            elif op_name == "add_noise":
                amount = params.get("amount", 25)
                res_cv = ip.add_noise(cv_img, amount)
                label = f"Add Noise (σ={amount})"
            elif op_name == "noise_map":
                res_cv = ip.generate_noise_map(cv_img)
                label = "Noise Residual Map"
            elif op_name == "binary_threshold":
                t = params.get("thresh", 128)
                res_cv = ip.threshold_image(cv_img, t)
                label = f"Threshold ({t})"
            elif op_name == "adaptive_threshold":
                res_cv = ip.adaptive_threshold(cv_img)
                label = "Adaptive Threshold"
            elif op_name == "canny":
                low = params.get("low", 50)
                high = params.get("high", 150)
                res_cv = ip.canny_edge(cv_img, low, high)
                label = f"Canny ({low}-{high})"
            elif op_name == "sobel":
                res_cv = ip.sobel_edge(cv_img)
                label = "Sobel Edge"
            elif op_name == "laplacian":
                res_cv = ip.laplacian_edge(cv_img)
                label = "Laplacian Edge"
            elif op_name == "hsv":
                res_cv = ip.to_hsv(cv_img)
                label = "HSV Color Space"
            elif op_name == "channel":
                ch = params.get("ch", "red")
                res_cv = ip.isolate_channel(cv_img, ch)
                label = f"{ch.title()} Channel"
            elif op_name == "resize":
                h, w = cv_img.shape[:2]
                pct, ok = QInputDialog.getInt(
                    self, "Resize Image", "Enter scale percentage (10 - 400%):",
                    100, 10, 400, 5
                )
                if ok and pct != 100:
                    new_w = max(10, int(w * pct / 100.0))
                    new_h = max(10, int(h * pct / 100.0))
                    res_cv = ip.resize_image(cv_img, new_w, new_h)
                    label = f"Resize ({new_w}×{new_h})"
                else:
                    return
            elif op_name == "update_hist":
                self._update_histogram()
                return

            if res_cv is not None:
                out_qimg = ip.cv_to_qimage(res_cv)
                if out_qimg:
                    self.document_viewer.push_processed_step(label, out_qimg)

        except Exception as e:
            QMessageBox.critical(self, "Processing Error", f"Operation failed: {str(e)}")

    def _update_histogram(self):
        current_img = self.document_viewer.get_current_image()
        if current_img:
            cv_img = ip.qimage_to_cv(current_img)
            if cv_img is not None:
                mode_idx = self.tools_panel.hist_combo.currentIndex()
                mode_map = {0: "all", 1: "red", 2: "green", 3: "blue", 4: "grayscale"}
                mode = mode_map.get(mode_idx, "all")
                self._last_hist_image = ip.compute_histogram(cv_img, mode=mode)
                self.tools_panel.set_histogram_image(self._last_hist_image)

    def _export_histogram(self):
        if self._last_hist_image is None:
            QMessageBox.information(self, "Histogram", "No histogram image available to export.")
            return

        out_path, _ = QFileDialog.getSaveFileName(
            self, "Export Histogram Plot", "histogram_plot.png",
            "PNG Image (*.png);;JPEG Image (*.jpg);;TIFF Image (*.tiff)"
        )
        if out_path:
            qimg = ip.cv_to_qimage(self._last_hist_image)
            if qimg and qimg.save(out_path):
                QMessageBox.information(self, "Histogram Exported", f"Histogram saved successfully:\n{out_path}")

    def _on_toolbar_selected(self, tool_name: str):
        if tool_name == "Layers":
            self.tools_panel.setVisible(not self.tools_panel.isVisible())
        elif tool_name == "Compare":
            self.document_viewer.set_mode("split")
        elif tool_name == "Zoom":
            self.document_viewer.zoom_in()

    def get_processed_image(self) -> Optional[QImage]:
        return self.document_viewer.get_current_image()

    def get_original_image(self) -> Optional[QImage]:
        return self.document_viewer.get_original_image()

    def reset_processing(self):
        self.document_viewer.reset_to_original()
