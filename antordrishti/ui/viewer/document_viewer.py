"""
Antordrishti — Document Viewer
Professional forensic document viewer featuring:
- PDF page thumbnails panel with click-to-jump
- Before / After Comparison Modes: Original, Processed, Split View (Side-by-Side), Overlay with Opacity
- First / Prev / Next / Last page navigation and direct jump
- Zoom In, Out, 100%, Fit Window, Fit Width, Rotation, and Panning
- Analysis History stack with Undo, Redo, and Reset
"""

from typing import Optional, List, Tuple
from PyQt5.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QWidget,
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QMenu, QAction, QFileDialog, QStackedWidget,
    QScrollArea, QFrame, QSplitter, QSlider, QSizePolicy
)
from PyQt5.QtCore import (
    Qt, pyqtSignal, QRectF, QPointF, QSize, QRect
)
from PyQt5.QtGui import (
    QPixmap, QImage, QPainter, QWheelEvent, QDragEnterEvent,
    QDropEvent, QKeyEvent, QCursor, QColor, QIcon
)

from app.theme import Colors, Spacing, Sizes
from app.resources import get_icon, Icons
from ui.widgets.common import DocumentDropZoneWidget, ActionButton


class ThumbnailButton(QPushButton):
    """Clickable page thumbnail button in the PDF filmstrip."""

    def __init__(self, page_num: int, pixmap: QPixmap, parent=None):
        super().__init__(parent)
        self.page_num = page_num
        self.setCheckable(True)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFixedSize(110, 135)
        self.setIcon(QIcon(pixmap))
        self.setIconSize(QSize(90, 100))
        self.setText(f"Page {page_num + 1}")
        self.setStyleSheet("""
            ThumbnailButton {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 4px;
                font-size: 10px;
                font-weight: 600;
                color: #475569;
                text-align: center;
                padding-top: 4px;
                padding-bottom: 4px;
            }
            ThumbnailButton:hover {
                border-color: #CBD5E1;
                background-color: #F8FAFC;
                color: #0F172A;
            }
            ThumbnailButton:checked {
                border: 2px solid #B08D3A;
                background-color: #FAF4E6;
                color: #785F23;
                font-weight: 700;
            }
        """)


class SingleGraphicsView(QGraphicsView):
    """Custom graphics view with zoom, pan, and context menu."""

    zoom_changed = pyqtSignal(int)
    context_menu_requested = pyqtSignal(QPointF)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)

        self._pixmap_item: Optional[QGraphicsPixmapItem] = None
        self._current_image: Optional[QImage] = None
        self._zoom_factor = 1.0
        self._panning = False
        self._pan_start = QPointF()

        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.setStyleSheet("background-color: #F8FAFC; border: none;")

    def set_image(self, image: QImage, preserve_zoom: bool = False):
        self._scene.clear()
        self._current_image = image
        if image and not image.isNull():
            pixmap = QPixmap.fromImage(image)
            self._pixmap_item = self._scene.addPixmap(pixmap)
            self._scene.setSceneRect(QRectF(pixmap.rect()))
            if not preserve_zoom:
                self.fit_to_window()
        else:
            self._pixmap_item = None

    def get_image(self) -> Optional[QImage]:
        return self._current_image

    def clear(self):
        self._scene.clear()
        self._pixmap_item = None
        self._current_image = None
        self._zoom_factor = 1.0

    def fit_to_window(self):
        if self._pixmap_item and self.viewport().width() > 0 and self.viewport().height() > 0:
            self.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
            self._update_zoom_factor()

    def fit_to_width(self):
        if self._pixmap_item and self.viewport().width() > 0:
            scale = self.viewport().width() / max(1.0, self._scene.sceneRect().width())
            self.resetTransform()
            self.scale(scale, scale)
            self._update_zoom_factor()

    def zoom_to_actual(self):
        self.resetTransform()
        self._zoom_factor = 1.0
        self.zoom_changed.emit(100)

    def zoom_in(self):
        factor = 1.25
        self._zoom_factor *= factor
        self.scale(factor, factor)
        self.zoom_changed.emit(int(self._zoom_factor * 100))

    def zoom_out(self):
        factor = 0.8
        self._zoom_factor *= factor
        self.scale(factor, factor)
        self.zoom_changed.emit(int(self._zoom_factor * 100))

    def rotate_cw(self):
        self.rotate(90)

    def rotate_ccw(self):
        self.rotate(-90)

    def _update_zoom_factor(self):
        transform = self.transform()
        self._zoom_factor = transform.m11()
        self.zoom_changed.emit(int(self._zoom_factor * 100))

    def wheelEvent(self, event: QWheelEvent):
        if event.angleDelta().y() > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = True
            self._pan_start = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        elif event.button() == Qt.MouseButton.RightButton:
            self.context_menu_requested.emit(self.mapToScene(event.pos()))
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._panning:
            delta = event.pos() - self._pan_start
            self._pan_start = event.pos()
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - int(delta.x())
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - int(delta.y())
            )
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
        else:
            super().mouseReleaseEvent(event)


DocumentGraphicsView = SingleGraphicsView


class ComparisonWorkspace(QWidget):
    """Workspace with Single View, Split View, and Overlay comparison modes."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._mode = "processed"  # "original", "processed", "split", "overlay"
        self._original_img: Optional[QImage] = None
        self._processed_img: Optional[QImage] = None
        self._overlay_opacity: float = 0.5

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.stack = QStackedWidget()

        # 0: Single View
        self.single_view = SingleGraphicsView()
        self.stack.addWidget(self.single_view)

        # 1: Split View (Side-by-Side)
        self.split_widget = QWidget()
        split_layout = QHBoxLayout(self.split_widget)
        split_layout.setContentsMargins(0, 0, 0, 0)
        split_layout.setSpacing(0)

        # Left: Original View
        left_box = QWidget()
        left_layout = QVBoxLayout(left_box)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        lbl_left = QLabel("  ORIGINAL EVIDENCE")
        lbl_left.setFixedHeight(24)
        lbl_left.setStyleSheet("background-color: #F8FAFC; border-bottom: 1px solid #E2E8F0; font-size: 10px; font-weight: 700; color: #475569;")
        left_layout.addWidget(lbl_left)
        self.split_left_view = SingleGraphicsView()
        left_layout.addWidget(self.split_left_view)
        split_layout.addWidget(left_box, 1)

        # Thin divider
        div = QFrame()
        div.setFrameShape(QFrame.Shape.VLine)
        div.setStyleSheet("background-color: #E2E8F0; max-width: 1px; border: none;")
        split_layout.addWidget(div)

        # Right: Processed View
        right_box = QWidget()
        right_layout = QVBoxLayout(right_box)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        lbl_right = QLabel("  PROCESSED / FILTERED")
        lbl_right.setFixedHeight(24)
        lbl_right.setStyleSheet("background-color: #FAF4E6; border-bottom: 1px solid #F5EACB; font-size: 10px; font-weight: 700; color: #785F23;")
        right_layout.addWidget(lbl_right)
        self.split_right_view = SingleGraphicsView()
        right_layout.addWidget(self.split_right_view)
        split_layout.addWidget(right_box, 1)

        # Synchronize scrollbars between left & right views for synchronous panning
        self.split_left_view.horizontalScrollBar().valueChanged.connect(
            self.split_right_view.horizontalScrollBar().setValue
        )
        self.split_right_view.horizontalScrollBar().valueChanged.connect(
            self.split_left_view.horizontalScrollBar().setValue
        )
        self.split_left_view.verticalScrollBar().valueChanged.connect(
            self.split_right_view.verticalScrollBar().setValue
        )
        self.split_right_view.verticalScrollBar().valueChanged.connect(
            self.split_left_view.verticalScrollBar().setValue
        )

        self.stack.addWidget(self.split_widget)
        layout.addWidget(self.stack, 1)

    def set_original(self, image: Optional[QImage]):
        self._original_img = image
        self._update_views()

    def set_processed(self, image: Optional[QImage]):
        self._processed_img = image
        self._update_views()

    def set_mode(self, mode: str):
        """Mode: 'original', 'processed', 'split', 'overlay'."""
        self._mode = mode
        if mode == "split":
            self.stack.setCurrentIndex(1)
        else:
            self.stack.setCurrentIndex(0)
        self._update_views()

    def set_overlay_opacity(self, opacity: float):
        self._overlay_opacity = max(0.0, min(1.0, opacity))
        if self._mode == "overlay":
            self._update_views()

    def _update_views(self):
        def _is_valid(img):
            return img is not None and not img.isNull()

        if self._mode == "original":
            if _is_valid(self._original_img):
                self.single_view.set_image(self._original_img)
        elif self._mode == "processed":
            img = self._processed_img if _is_valid(self._processed_img) else self._original_img
            if _is_valid(img):
                self.single_view.set_image(img)
        elif self._mode == "split":
            if _is_valid(self._original_img):
                self.split_left_view.set_image(self._original_img)
            img_right = self._processed_img if _is_valid(self._processed_img) else self._original_img
            if _is_valid(img_right):
                self.split_right_view.set_image(img_right)
        elif self._mode == "overlay":
            if _is_valid(self._original_img) and _is_valid(self._processed_img):
                base = self._original_img.convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)
                overlay = self._processed_img.scaled(base.size(), Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
                overlay = overlay.convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)

                blended = QImage(base.size(), QImage.Format.Format_ARGB32_Premultiplied)
                painter = QPainter()
                if base.size().width() > 0 and base.size().height() > 0 and painter.begin(blended):
                    painter.drawImage(0, 0, base)
                    painter.setOpacity(self._overlay_opacity)
                    painter.drawImage(0, 0, overlay)
                    painter.end()
                    self.single_view.set_image(blended)
                else:
                    self.single_view.set_image(self._processed_img)
            elif _is_valid(self._processed_img):
                self.single_view.set_image(self._processed_img)
            elif _is_valid(self._original_img):
                self.single_view.set_image(self._original_img)

    def clear(self):
        self._original_img = None
        self._processed_img = None
        self.single_view.clear()
        self.split_left_view.clear()
        self.split_right_view.clear()
        self._mode = "processed"
        self.stack.setCurrentIndex(0)


class DocumentViewer(QWidget):
    """Complete document viewer with PDF filmstrip, comparison toolbar, canvas, and navigation."""

    document_loaded = pyqtSignal(str)
    page_changed = pyqtSignal(int)
    zoom_changed = pyqtSignal(int)
    file_dropped = pyqtSignal(str)
    open_image_requested = pyqtSignal()
    open_pdf_requested = pyqtSignal()
    history_updated = pyqtSignal(list, int)  # (list_of_names, current_index)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)

        self._current_path = ""
        self._current_page = 0
        self._total_pages = 1

        # History stack: [(step_name, QImage)]
        self._history: List[Tuple[str, QImage]] = []
        self._history_index: int = -1

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Top Control & Comparison Bar
        self._top_bar = self._build_top_bar()
        layout.addWidget(self._top_bar)

        # Center Area: Splitter between PDF Filmstrip and Canvas Workspace
        self._main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left Thumbnail Filmstrip
        self._filmstrip_widget = self._build_filmstrip()
        self._main_splitter.addWidget(self._filmstrip_widget)
        self._filmstrip_widget.setVisible(False)  # Hidden when no PDF

        # Center Canvas / Comparison Workspace
        self._comparison_ws = ComparisonWorkspace()
        self._comparison_ws.single_view.zoom_changed.connect(self._on_zoom_changed)
        self._comparison_ws.single_view.context_menu_requested.connect(self._show_context_menu)

        # Dropzone for empty state
        self._drop_zone = DocumentDropZoneWidget()
        self._drop_zone.file_dropped.connect(self.file_dropped.emit)

        self._stack = QStackedWidget()
        self._stack.addWidget(self._drop_zone)
        self._stack.addWidget(self._comparison_ws)
        self._stack.setCurrentIndex(0)

        self._main_splitter.addWidget(self._stack)
        self._main_splitter.setStretchFactor(0, 0)
        self._main_splitter.setStretchFactor(1, 1)

        layout.addWidget(self._main_splitter, 1)

        # Bottom Navigation & Zoom Bar
        self._bottom_bar = self._build_bottom_bar()
        layout.addWidget(self._bottom_bar)

    def _build_top_bar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(36)
        bar.setStyleSheet("""
            background-color: #FFFFFF;
            border-bottom: 1px solid #E2E8F0;
        """)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(8)

        # Document Title
        self._doc_name_label = QLabel("No Document")
        self._doc_name_label.setStyleSheet("font-size: 12px; font-weight: 700; color: #0F172A;")
        layout.addWidget(self._doc_name_label)

        layout.addStretch()

        # Comparison Mode Selector
        comp_label = QLabel("VIEW:")
        comp_label.setStyleSheet("font-size: 10px; font-weight: 700; color: #64748B; letter-spacing: 0.5px;")
        layout.addWidget(comp_label)

        self.btn_view_proc = QPushButton("Processed")
        self.btn_view_proc.setCheckable(True)
        self.btn_view_proc.setChecked(True)
        self.btn_view_orig = QPushButton("Original")
        self.btn_view_orig.setCheckable(True)
        self.btn_view_split = QPushButton("Split View")
        self.btn_view_split.setCheckable(True)
        self.btn_view_overlay = QPushButton("Overlay")
        self.btn_view_overlay.setCheckable(True)

        for btn, mode in [
            (self.btn_view_proc, "processed"),
            (self.btn_view_orig, "original"),
            (self.btn_view_split, "split"),
            (self.btn_view_overlay, "overlay")
        ]:
            btn.setFixedHeight(24)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #FFFFFF;
                    border: 1px solid #CBD5E1;
                    border-radius: 4px;
                    padding: 2px 10px;
                    font-size: 11px;
                    font-weight: 500;
                    color: #334155;
                }
                QPushButton:hover {
                    background-color: #F8FAFC;
                    color: #0F172A;
                }
                QPushButton:checked {
                    background-color: #FAF4E6;
                    border: 1px solid #B08D3A;
                    color: #785F23;
                    font-weight: 600;
                }
            """)
            btn.clicked.connect(lambda _, m=mode, b=btn: self._on_mode_button_clicked(m, b))
            layout.addWidget(btn)

        # Overlay Opacity Slider
        self.overlay_slider = QSlider(Qt.Orientation.Horizontal)
        self.overlay_slider.setRange(0, 100)
        self.overlay_slider.setValue(50)
        self.overlay_slider.setFixedWidth(70)
        self.overlay_slider.setToolTip("Overlay Opacity")
        self.overlay_slider.setVisible(False)
        self.overlay_slider.valueChanged.connect(lambda v: self._comparison_ws.set_overlay_opacity(v / 100.0))
        layout.addWidget(self.overlay_slider)

        return bar

    def _on_mode_button_clicked(self, mode: str, clicked_btn: QPushButton):
        for btn in [self.btn_view_proc, self.btn_view_orig, self.btn_view_split, self.btn_view_overlay]:
            btn.setChecked(btn == clicked_btn)
        self.overlay_slider.setVisible(mode == "overlay")
        self._comparison_ws.set_mode(mode)

    def set_mode(self, mode: str):
        """Set active view mode ('processed', 'original', 'split', 'overlay')."""
        mode_btn_map = {
            "processed": self.btn_view_proc,
            "original": self.btn_view_orig,
            "split": self.btn_view_split,
            "overlay": self.btn_view_overlay,
        }
        btn = mode_btn_map.get(mode, self.btn_view_proc)
        self._on_mode_button_clicked(mode, btn)

    def _build_filmstrip(self) -> QWidget:
        strip = QWidget()
        strip.setFixedWidth(130)
        strip.setStyleSheet("background-color: #F8FAFC; border-right: 1px solid #E2E8F0;")
        strip_layout = QVBoxLayout(strip)
        strip_layout.setContentsMargins(4, 4, 4, 4)
        strip_layout.setSpacing(4)

        strip_title = QLabel("PAGES")
        strip_title.setStyleSheet("font-size: 10px; font-weight: 800; color: #64748B; padding: 2px 4px;")
        strip_layout.addWidget(strip_title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent;")

        self._thumb_container = QWidget()
        self._thumb_container.setStyleSheet("background: transparent;")
        self._thumb_layout = QVBoxLayout(self._thumb_container)
        self._thumb_layout.setContentsMargins(0, 0, 0, 0)
        self._thumb_layout.setSpacing(6)
        self._thumb_layout.addStretch()

        scroll.setWidget(self._thumb_container)
        strip_layout.addWidget(scroll)
        return strip

    def _build_bottom_bar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(34)
        bar.setStyleSheet("background-color: #FFFFFF; border-top: 1px solid #E2E8F0;")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(4)

        # Toggle Filmstrip
        self.btn_thumbs = self._make_tool_btn(Icons.LAYERS, "Toggle Page Thumbnails")
        self.btn_thumbs.clicked.connect(self._toggle_filmstrip)
        layout.addWidget(self.btn_thumbs)

        layout.addWidget(self._make_vseparator())

        # Page navigation controls
        btn_first = self._make_tool_btn(Icons.PREV_PAGE, "First Page")
        btn_first.setText("|<")
        btn_first.clicked.connect(self.first_page)
        layout.addWidget(btn_first)

        btn_prev = self._make_tool_btn(Icons.PREV_PAGE, "Previous Page")
        btn_prev.clicked.connect(self.prev_page)
        layout.addWidget(btn_prev)

        self._page_label = QLabel("Page 1 / 1")
        self._page_label.setStyleSheet("font-size: 11px; font-weight: 600; color: #0F172A; min-width: 75px;")
        self._page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._page_label)

        btn_next = self._make_tool_btn(Icons.NEXT_PAGE, "Next Page")
        btn_next.clicked.connect(self.next_page)
        layout.addWidget(btn_next)

        btn_last = self._make_tool_btn(Icons.NEXT_PAGE, "Last Page")
        btn_last.setText(">|")
        btn_last.clicked.connect(self.last_page)
        layout.addWidget(btn_last)

        layout.addWidget(self._make_vseparator())
        layout.addStretch()

        # Zoom controls
        zm_out = self._make_tool_btn(Icons.ZOOM_OUT, "Zoom Out (Ctrl+-)")
        zm_out.clicked.connect(self.zoom_out)
        layout.addWidget(zm_out)

        self._zoom_label = QLabel("100%")
        self._zoom_label.setStyleSheet("font-size: 11px; font-weight: 600; color: #475569; min-width: 44px;")
        self._zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._zoom_label)

        zm_in = self._make_tool_btn(Icons.ZOOM_IN, "Zoom In (Ctrl++)")
        zm_in.clicked.connect(self.zoom_in)
        layout.addWidget(zm_in)

        zm_100 = QPushButton("100%")
        zm_100.setFixedSize(40, 24)
        zm_100.setToolTip("Zoom to Actual Size 100% (Ctrl+1)")
        zm_100.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        zm_100.setStyleSheet("""
            QPushButton {
                background: #FFFFFF;
                border: 1px solid #CBD5E1;
                border-radius: 3px;
                font-size: 10px;
                font-weight: 600;
                color: #334155;
            }
            QPushButton:hover {
                background-color: #F8FAFC;
                color: #0F172A;
            }
        """)
        zm_100.clicked.connect(self.zoom_to_actual)
        layout.addWidget(zm_100)

        fit_btn = self._make_tool_btn(Icons.FIT, "Fit to Window (Ctrl+0)")
        fit_btn.clicked.connect(self.fit_to_window)
        layout.addWidget(fit_btn)

        fit_w_btn = QPushButton("Fit W")
        fit_w_btn.setFixedSize(40, 24)
        fit_w_btn.setToolTip("Fit to Width")
        fit_w_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        fit_w_btn.setStyleSheet(zm_100.styleSheet())
        fit_w_btn.clicked.connect(self.fit_to_width)
        layout.addWidget(fit_w_btn)

        layout.addWidget(self._make_vseparator())

        rot_ccw = self._make_tool_btn(Icons.ROTATE_CCW, "Rotate Left 90°")
        rot_ccw.clicked.connect(self.rotate_ccw)
        layout.addWidget(rot_ccw)

        rot_cw = self._make_tool_btn(Icons.ROTATE_CW, "Rotate Right 90°")
        rot_cw.clicked.connect(self.rotate_cw)
        layout.addWidget(rot_cw)

        return bar

    def _make_tool_btn(self, icon_name: str, tooltip: str) -> QPushButton:
        btn = QPushButton()
        btn.setIcon(get_icon(icon_name, "#334155"))
        btn.setIconSize(QSize(16, 16))
        btn.setFixedSize(26, 26)
        btn.setToolTip(tooltip)
        btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: 1px solid transparent;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #F1F5F9;
                border-color: #CBD5E1;
            }
        """)
        return btn

    def _make_vseparator(self) -> QFrame:
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet("background-color: #E2E8F0; max-width: 1px; margin: 4px 2px;")
        return sep

    # ── Document & Page Loading ───────────────────────────────

    def load_file(self, file_path: str):
        from services.document_service import load_document, render_page_image, render_thumbnail

        doc = load_document(file_path)
        if not doc:
            return

        self._current_path = file_path
        self._total_pages = max(1, doc.page_count)
        self._current_page = 0

        # Render first page
        image = render_page_image(file_path, 0)
        if image and not image.isNull():
            self._history = [("Original Evidence", image.copy())]
            self._history_index = 0
            self._comparison_ws.set_original(image.copy())
            self._comparison_ws.set_processed(image.copy())
            self._stack.setCurrentIndex(1)
            self._emit_history()
        else:
            self._stack.setCurrentIndex(0)

        # Build Thumbnails if multi-page PDF
        self._load_thumbnails()
        self._update_labels(doc.file_name)
        self.document_loaded.emit(file_path)

    def _load_thumbnails(self):
        from services.document_service import render_thumbnail

        # Clear existing thumbnails
        while self._thumb_layout.count() > 1:
            item = self._thumb_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if self._total_pages > 1 and self._current_path:
            self._filmstrip_widget.setVisible(True)
            for p in range(min(self._total_pages, 30)):  # load first 30 pages
                thumb = render_thumbnail(self._current_path, p, 100)
                if thumb and not thumb.isNull():
                    pix = QPixmap.fromImage(thumb)
                    btn = ThumbnailButton(p, pix)
                    btn.setChecked(p == self._current_page)
                    btn.clicked.connect(lambda _, page=p: self.go_to_page(page))
                    self._thumb_layout.insertWidget(p, btn)
        else:
            self._filmstrip_widget.setVisible(False)

    def _toggle_filmstrip(self):
        self._filmstrip_widget.setVisible(not self._filmstrip_widget.isVisible())

    def go_to_page(self, page_num: int):
        if 0 <= page_num < self._total_pages:
            self._current_page = page_num
            self._render_current_page()

    def first_page(self):
        self.go_to_page(0)

    def last_page(self):
        self.go_to_page(self._total_pages - 1)

    def prev_page(self):
        if self._current_page > 0:
            self.go_to_page(self._current_page - 1)

    def next_page(self):
        if self._current_page < self._total_pages - 1:
            self.go_to_page(self._current_page + 1)

    def _render_current_page(self):
        from services.document_service import render_page_image
        image = render_page_image(self._current_path, self._current_page)
        if image and not image.isNull():
            self._history = [("Original Evidence", image.copy())]
            self._history_index = 0
            self._comparison_ws.set_original(image.copy())
            self._comparison_ws.set_processed(image.copy())
            self._emit_history()

        self._update_page_label()
        self.page_changed.emit(self._current_page + 1)

    def clear(self):
        """Clear all content and reset viewer state."""
        self._current_path = ""
        self._current_page = 0
        self._total_pages = 1
        self._history.clear()
        self._history_index = -1
        self._comparison_ws.clear()
        self._update_labels("No Document")
        
        while self._thumb_layout.count() > 1:
            item = self._thumb_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._filmstrip_widget.setVisible(False)
        
        self._stack.setCurrentIndex(0)
        self._emit_history()

    def _update_labels(self, name: str):
        self._doc_name_label.setText(name)
        self._update_page_label()

    def _update_page_label(self):
        p = self._current_page + 1
        t = self._total_pages
        self._page_label.setText(f"Page {p} / {t}")

        # Update thumbnail active state
        for i in range(self._thumb_layout.count() - 1):
            item = self._thumb_layout.itemAt(i)
            if item and item.widget() and isinstance(item.widget(), ThumbnailButton):
                item.widget().setChecked(item.widget().page_num == self._current_page)

    # ── Processed Image & History Management ──────────────────

    def push_processed_step(self, step_name: str, image: QImage):
        """Add a new processing operation to history."""
        if image is None or image.isNull():
            return
        if self._history_index < len(self._history) - 1:
            self._history = self._history[:self._history_index + 1]

        self._history.append((step_name, image.copy()))
        self._history_index = len(self._history) - 1
        self._comparison_ws.set_processed(image.copy())
        self._emit_history()

    def set_qimage(self, image: QImage, label_suffix: str = ""):
        """Directly set processed QImage."""
        if image and not image.isNull():
            self.push_processed_step(label_suffix or "Processed", image)
            self._stack.setCurrentIndex(1)
        else:
            self._stack.setCurrentIndex(0)

    def undo(self):
        if self._history_index > 0:
            self._history_index -= 1
            name, img = self._history[self._history_index]
            self._comparison_ws.set_processed(img.copy())
            self._emit_history()

    def redo(self):
        if self._history_index < len(self._history) - 1:
            self._history_index += 1
            name, img = self._history[self._history_index]
            self._comparison_ws.set_processed(img.copy())
            self._emit_history()

    def reset_to_original(self):
        if len(self._history) > 0:
            self._history_index = 0
            name, img = self._history[0]
            self._comparison_ws.set_processed(img.copy())
            self._emit_history()

    def get_current_image(self) -> Optional[QImage]:
        if 0 <= self._history_index < len(self._history):
            return self._history[self._history_index][1]
        return self._comparison_ws.single_view.get_image()

    def get_original_image(self) -> Optional[QImage]:
        if len(self._history) > 0:
            return self._history[0][1]
        return None

    def _emit_history(self):
        names = [item[0] for item in self._history]
        self.history_updated.emit(names, self._history_index)

    # ── View Helpers ──────────────────────────────────────────

    def zoom_in(self):
        self._comparison_ws.single_view.zoom_in()
        self._comparison_ws.split_left_view.zoom_in()
        self._comparison_ws.split_right_view.zoom_in()

    def zoom_out(self):
        self._comparison_ws.single_view.zoom_out()
        self._comparison_ws.split_left_view.zoom_out()
        self._comparison_ws.split_right_view.zoom_out()

    def zoom_to_actual(self):
        self._comparison_ws.single_view.zoom_to_actual()
        self._comparison_ws.split_left_view.zoom_to_actual()
        self._comparison_ws.split_right_view.zoom_to_actual()

    def fit_to_window(self):
        self._comparison_ws.single_view.fit_to_window()
        self._comparison_ws.split_left_view.fit_to_window()
        self._comparison_ws.split_right_view.fit_to_window()

    def fit_to_width(self):
        self._comparison_ws.single_view.fit_to_width()
        self._comparison_ws.split_left_view.fit_to_width()
        self._comparison_ws.split_right_view.fit_to_width()

    def rotate_cw(self):
        self._comparison_ws.single_view.rotate_cw()
        self._comparison_ws.split_left_view.rotate_cw()
        self._comparison_ws.split_right_view.rotate_cw()

    def rotate_ccw(self):
        self._comparison_ws.single_view.rotate_ccw()
        self._comparison_ws.split_left_view.rotate_ccw()
        self._comparison_ws.split_right_view.rotate_ccw()

    def _on_zoom_changed(self, pct: int):
        self._zoom_label.setText(f"{pct}%")
        self.zoom_changed.emit(pct)

    def _show_context_menu(self, scene_pos: QPointF):
        menu = QMenu(self)
        actions = [
            ("Zoom In", self.zoom_in),
            ("Zoom Out", self.zoom_out),
            ("Fit to Window", self.fit_to_window),
            ("Zoom 100%", self.zoom_to_actual),
            None,
            ("Rotate Left", self.rotate_ccw),
            ("Rotate Right", self.rotate_cw),
        ]
        for item in actions:
            if item is None:
                menu.addSeparator()
            else:
                text, callback = item
                act = menu.addAction(text)
                act.triggered.connect(callback)
        menu.exec_(self._comparison_ws.single_view.viewport().mapToGlobal(
            self._comparison_ws.single_view.mapFromScene(scene_pos)
        ))

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                path = url.toLocalFile().lower()
                if any(path.endswith(ext) for ext in
                       ['.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp']):
                    event.acceptProposedAction()
                    return

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path:
                self.load_file(path)
                self.file_dropped.emit(path)
                break
