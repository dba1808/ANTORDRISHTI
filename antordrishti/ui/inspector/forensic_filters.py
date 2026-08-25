"""
Antordrishti — Forensic Filters Inspector Section
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QComboBox

from ui.widgets.common import CollapsibleSection, LabeledSlider, SectionLabel


class ForensicFiltersPanel(QWidget):
    """Forensic filter controls for the inspector."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._section = CollapsibleSection("FORENSIC FILTERS")

        # Visual Analysis Mode
        self._section.add_widget(SectionLabel("Visual Analysis Mode"))
        self._view_mode = QComboBox()
        self._view_mode.addItems([
            "Standard View (RGB)", "Grayscale", "Red Channel",
            "Green Channel", "Blue Channel", "Luminance",
            "Edge Detection", "ELA View"
        ])
        self._section.add_widget(self._view_mode)

        # Color Space
        self._section.add_widget(SectionLabel("Color Space"))
        self._color_space = QComboBox()
        self._color_space.addItems(["RGB", "HSV", "LAB", "YCbCr", "Grayscale"])
        self._section.add_widget(self._color_space)

        # Channel
        self._section.add_widget(SectionLabel("Channel"))
        self._channel = QComboBox()
        self._channel.addItems(["All", "Red", "Green", "Blue", "Alpha"])
        self._section.add_widget(self._channel)

        # Sliders
        self._ela_quality = LabeledSlider("ELA Resave Quality", 1, 100, 75)
        self._section.add_widget(self._ela_quality)

        self._contrast = LabeledSlider("Contrast", 0, 200, 100)
        self._section.add_widget(self._contrast)

        self._brightness = LabeledSlider("Brightness", 0, 200, 100)
        self._section.add_widget(self._brightness)

        self._noise_viz = LabeledSlider("Noise Visualization", 0, 100, 0)
        self._section.add_widget(self._noise_viz)

        # Frequency Band
        self._section.add_widget(SectionLabel("Frequency Band"))
        self._freq_band = QComboBox()
        self._freq_band.addItems(["All", "Low", "Mid", "High"])
        self._section.add_widget(self._freq_band)

        layout.addWidget(self._section)
