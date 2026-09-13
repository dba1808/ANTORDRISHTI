"""
Antordrishti — Forgery Detection Page
Passive and Active forgery detection modules.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QTabWidget, QFrame, QScrollArea, QGroupBox, QRadioButton
)
from PyQt5.QtCore import Qt

from app.theme import Colors, Spacing
from ui.widgets.common import (
    SectionLabel, ActionButton, EngineNotConnectedWidget, InfoRow,
    Separator, LabeledSlider, CollapsibleSection
)


class _CopyMoveModule(QWidget):
    """Copy-Move Detection module."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        layout.setSpacing(Spacing.SM)

        layout.addWidget(SectionLabel("Copy-Move Detection"))

        # Method
        layout.addWidget(QLabel("Method:"))
        self._method = QComboBox()
        self._method.addItems(["Block-Based", "Keypoint-Based"])
        layout.addWidget(self._method)

        # Features
        layout.addWidget(QLabel("Features:"))
        self._features = QComboBox()
        self._features.addItems(["SIFT", "SURF", "ORB"])
        layout.addWidget(self._features)

        layout.addWidget(Separator())
        layout.addWidget(SectionLabel("Analysis"))
        for item in ["Feature Matching", "Geometric Verification",
                      "Transformation Analysis", "Region Localization"]:
            layout.addWidget(InfoRow(item, "Not Analysed"))

        layout.addWidget(Separator())
        layout.addWidget(ActionButton("Run Detection", primary=True))
        layout.addWidget(ActionButton("Show Matches"))
        layout.addWidget(ActionButton("Show Mask"))
        layout.addWidget(ActionButton("Add Finding"))
        layout.addStretch()


class _SplicingModule(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        layout.setSpacing(Spacing.SM)
        layout.addWidget(SectionLabel("Splicing Detection"))
        for item in ["Boundary Analysis", "Color Inconsistency",
                      "Texture Inconsistency", "Spliced Region Localization"]:
            layout.addWidget(InfoRow(item, "Not Analysed"))
        layout.addWidget(Separator())
        layout.addWidget(ActionButton("Run Splicing Detection", primary=True))
        layout.addWidget(ActionButton("Add Finding"))
        layout.addStretch()


class _SimpleModule(QWidget):
    def __init__(self, title: str, items: list, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        layout.setSpacing(Spacing.SM)
        layout.addWidget(SectionLabel(title))
        for item in items:
            layout.addWidget(InfoRow(item, "Not Analysed"))
        layout.addWidget(Separator())
        layout.addWidget(ActionButton(f"Run {title}", primary=True))
        layout.addWidget(ActionButton("Add Finding"))
        layout.addStretch()


class ForgeryDetectionPage(QWidget):
    """Forgery Detection page with passive and active sections."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Title Bar
        title_bar = QWidget()
        title_bar.setFixedHeight(48)
        title_bar.setStyleSheet(f"""
            background-color: {Colors.CANVAS};
            border-bottom: 1px solid {Colors.BORDER_LIGHT};
        """)
        tb = QHBoxLayout(title_bar)
        tb.setContentsMargins(Spacing.LG, 0, Spacing.LG, 0)
        t = QLabel("Forensic Forgery Detection")
        t.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {Colors.TEXT_PRIMARY};")
        tb.addWidget(t)
        tb.addStretch()
        layout.addWidget(title_bar)

        # Two main tabs
        tabs = QTabWidget()
        tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {Colors.BORDER_LIGHT};
                background-color: {Colors.CANVAS};
                border-radius: 6px;
            }}
        """)

        # Passive tab
        passive_tabs = QTabWidget()
        passive_tabs.addTab(_CopyMoveModule(), "Copy-Move")
        passive_tabs.addTab(_SplicingModule(), "Splicing")
        passive_tabs.addTab(
            _SimpleModule("Resampling Detection", [
                "Resampling Artifacts", "Interpolation",
                "Periodic Pattern", "Affine Transform"
            ]), "Resampling"
        )
        passive_tabs.addTab(
            _SimpleModule("Resizing Detection", [
                "Scale Factor", "Interpolation Method",
                "Boundary Artifacts"
            ]), "Resizing"
        )
        passive_tabs.addTab(
            _SimpleModule("Inpainting Detection", [
                "Inpainted Region", "Texture Consistency",
                "Structure Propagation"
            ]), "Inpainting"
        )
        tabs.addTab(passive_tabs, "Passive Forgery Detection")

        # Active tab
        active_tabs = QTabWidget()
        active_tabs.addTab(
            _SimpleModule("Watermark Verification", [
                "Watermark Present", "Watermark Integrity",
                "Modification Detected"
            ]), "Watermark"
        )
        active_tabs.addTab(
            _SimpleModule("Digital Signature", [
                "Signature Present", "Signature Valid",
                "Certificate Chain", "Timestamp"
            ]), "Digital Signature"
        )
        tabs.addTab(active_tabs, "Active Forgery Detection")

        layout.addWidget(tabs, 1)
