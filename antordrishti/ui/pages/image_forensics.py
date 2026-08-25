"""
Antordrishti — Image Forensics Page (Tabbed)
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget, QFrame
)
from PyQt5.QtCore import Qt

from app.theme import Colors, Spacing
from ui.widgets.common import (
    SectionLabel, ActionButton, EngineNotConnectedWidget, LabeledSlider,
    Separator, InfoRow
)


def _make_tab_content(title: str, items: list) -> QWidget:
    """Create a standard analysis tab with info rows and action button."""
    w = QWidget()
    layout = QVBoxLayout(w)
    layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
    layout.setSpacing(Spacing.SM)

    layout.addWidget(SectionLabel(title))

    for label in items:
        row = InfoRow(label, "Not Analysed")
        layout.addWidget(row)

    layout.addWidget(Separator())
    layout.addWidget(ActionButton(f"Run {title}", primary=True))
    layout.addWidget(ActionButton("Add Finding"))
    layout.addStretch()
    return w


class ImageForensicsPage(QWidget):
    """Image Forensics tabbed page."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Title
        title_bar = QWidget()
        title_bar.setFixedHeight(36)
        title_bar.setStyleSheet(f"""
            background-color: {Colors.PANEL};
            border-bottom: 1px solid {Colors.BORDER_LIGHT};
        """)
        tb_layout = QHBoxLayout(title_bar)
        tb_layout.setContentsMargins(Spacing.MD, 0, Spacing.MD, 0)
        title = QLabel("Image Forensics")
        title.setProperty("heading", True)
        tb_layout.addWidget(title)
        tb_layout.addStretch()
        layout.addWidget(title_bar)

        # Tabs
        tabs = QTabWidget()
        tabs.addTab(
            _make_tab_content("Image Quality", [
                "Overall Quality", "Blur Score", "Noise Level",
                "Dynamic Range", "Sharpness"
            ]),
            "Image Quality"
        )
        tabs.addTab(
            _make_tab_content("Compression Analysis", [
                "JPEG Quality", "Quantization Table", "Double Compression",
                "Compression History", "Block Artifacts"
            ]),
            "Compression"
        )
        tabs.addTab(
            _make_tab_content("Noise Pattern", [
                "Global Noise", "Local Noise Variance",
                "Noise Consistency", "Noise Residual"
            ]),
            "Noise Pattern"
        )
        tabs.addTab(
            _make_tab_content("Spatial Analysis", [
                "Edge Consistency", "Texture Consistency",
                "Resampling Artifacts", "Interpolation Artifacts"
            ]),
            "Spatial"
        )
        tabs.addTab(
            _make_tab_content("Frequency Analysis", [
                "DCT Coefficients", "FFT Spectrum", "DWT Decomposition",
                "Spectral Anomalies", "Frequency Residual"
            ]),
            "Frequency"
        )
        tabs.addTab(
            _make_tab_content("Image Statistics", [
                "Histogram", "Mean / Std Dev", "Channel Statistics",
                "Color Distribution", "Entropy"
            ]),
            "Statistics"
        )

        layout.addWidget(tabs, 1)
