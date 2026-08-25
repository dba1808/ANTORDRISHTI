"""
Antordrishti — Professional Startup Splash Screen
Animated splash with progressive text reveal, smooth hue gradient,
and loading progress bar.
"""

import math
from PyQt5.QtWidgets import QSplashScreen, QApplication
from PyQt5.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve,
    pyqtProperty, QRectF, QPointF
)
from PyQt5.QtGui import (
    QPainter, QColor, QFont, QLinearGradient,
    QPen, QFontMetrics, QPixmap
)


class AntordrishtiSplash(QSplashScreen):
    """Professional animated splash screen with text reveal and hue animation."""

    _TITLE_BENGALI = "অন্তর্দৃষ্টি"
    _TITLE_SEPARATOR = "|"
    _TITLE = "ANTORDRISHTI"
    _SUBTITLE = "DOCUMENT FORENSIC & AUTHENTICITY ANALYSIS SUITE"
    _VERSION = "v1.0.0"

    # Hue stops for the gradient sweep (teal → blue → violet → cyan)
    _HUE_STOPS = [175, 210, 260, 190]

    def __init__(self):
        # Create a blank white pixmap as base
        pixmap = QPixmap(620, 400)
        pixmap.fill(QColor("#FFFFFF"))
        super().__init__(pixmap, Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)

        # Animation state
        self._progress = 0.0       # 0.0 → 1.0 overall progress
        self._text_reveal = 0.0    # 0.0 → 1.0 letter reveal
        self._hue_offset = 0.0     # 0.0 → 360.0 hue sweep
        self._opacity = 0.0        # 0.0 → 1.0 fade in

        # Timers
        self._frame_timer = QTimer(self)
        self._frame_timer.setInterval(16)  # ~60fps
        self._frame_timer.timeout.connect(self._tick)

        self._elapsed = 0
        self._duration_ms = 2500
        self._done_callback = None

    # ── Animated properties ────────────────────────────────────

    def _get_progress(self):
        return self._progress

    def _set_progress(self, val):
        self._progress = val
        self.repaint()

    progress = pyqtProperty(float, _get_progress, _set_progress)

    def _get_hue_offset(self):
        return self._hue_offset

    def _set_hue_offset(self, val):
        self._hue_offset = val
        self.repaint()

    hue_offset = pyqtProperty(float, _get_hue_offset, _set_hue_offset)

    # ── Lifecycle ──────────────────────────────────────────────

    def start(self, done_callback=None):
        """Show splash and begin animation. Calls done_callback when finished."""
        self._done_callback = done_callback
        self._elapsed = 0
        self.show()

        # Hue animation — continuous loop
        self._hue_anim = QPropertyAnimation(self, b"hue_offset")
        self._hue_anim.setDuration(self._duration_ms)
        self._hue_anim.setStartValue(0.0)
        self._hue_anim.setEndValue(360.0)
        self._hue_anim.setEasingCurve(QEasingCurve.Type.Linear)
        self._hue_anim.start()

        # Start frame timer
        self._frame_timer.start()

    def _tick(self):
        """Per-frame update."""
        self._elapsed += 16

        t = min(self._elapsed / self._duration_ms, 1.0)

        # Phase 1: Fade in (0 → 0.15)
        if t < 0.15:
            self._opacity = t / 0.15
            self._text_reveal = 0.0
        # Phase 2: Text reveal (0.15 → 0.65)
        elif t < 0.65:
            self._opacity = 1.0
            self._text_reveal = (t - 0.15) / 0.50
        # Phase 3: Full display (0.65 → 0.85)
        elif t < 0.85:
            self._opacity = 1.0
            self._text_reveal = 1.0
        # Phase 4: Fade out (0.85 → 1.0)
        else:
            fade_t = (t - 0.85) / 0.15
            self._opacity = 1.0 - fade_t
            self._text_reveal = 1.0

        self._progress = t
        self.repaint()

        if t >= 1.0:
            self._frame_timer.stop()
            self.close()
            if self._done_callback:
                self._done_callback()

    # ── Paint ──────────────────────────────────────────────────

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        w = self.width()
        h = self.height()

        # Background — pure white
        painter.fillRect(0, 0, w, h, QColor("#FFFFFF"))

        # Apply global opacity
        painter.setOpacity(self._opacity)

        # ── Subtle border ──
        painter.setPen(QPen(QColor("#E2E8F0"), 1))
        painter.drawRect(0, 0, w - 1, h - 1)

        # ── Bengali title: "অন্তর্দৃষ্টি" ──
        bengali_y = h * 0.28
        if self._text_reveal > 0.0:
            bengali_opacity = min(1.0, self._text_reveal / 0.2)
            painter.setOpacity(self._opacity * bengali_opacity)

            bengali_font = QFont("Nirmala UI", 18, QFont.Weight.Normal)
            painter.setFont(bengali_font)
            painter.setPen(QColor("#0F766E"))

            bfm = QFontMetrics(bengali_font)
            b_w = bfm.horizontalAdvance(self._TITLE_BENGALI)
            painter.drawText(QPointF((w - b_w) / 2, bengali_y), self._TITLE_BENGALI)

        painter.setOpacity(self._opacity)

        # ── Separator: "|" ──
        sep_y = bengali_y + 20
        if self._text_reveal > 0.1:
            sep_opacity = min(1.0, (self._text_reveal - 0.1) / 0.15)
            painter.setOpacity(self._opacity * sep_opacity)

            sep_font = QFont("Segoe UI", 14, QFont.Weight.Thin)
            painter.setFont(sep_font)
            painter.setPen(QColor("#CBD5E1"))

            sfm = QFontMetrics(sep_font)
            # Draw a thin horizontal line instead of pipe for elegance
            line_w = 60
            line_x = (w - line_w) / 2
            painter.drawLine(int(line_x), int(sep_y), int(line_x + line_w), int(sep_y))

        painter.setOpacity(self._opacity)

        # ── Title: "ANTORDRISHTI" with hue gradient ──
        title_font = QFont("Segoe UI", 32, QFont.Weight.Bold)
        title_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 4.0)
        painter.setFont(title_font)

        fm = QFontMetrics(title_font)
        title = self._TITLE
        visible_count = max(0, int(self._text_reveal * len(title) + 0.99))
        visible_text = title[:visible_count]

        # Calculate starting x for centering full title
        full_width = fm.horizontalAdvance(title)
        start_x = (w - full_width) / 2
        title_y = sep_y + 42

        # Draw each visible letter with shifted hue color
        x = start_x
        for i, char in enumerate(visible_text):
            # Calculate hue for this character
            char_phase = (i / len(title)) * 360.0
            hue = (self._hue_offset + char_phase) % 360.0

            # Map hue to our palette stops
            color = self._hue_to_color(hue)

            # Slight entrance animation for the newest letter
            if i == visible_count - 1 and self._text_reveal < 1.0:
                frac = (self._text_reveal * len(title)) % 1.0
                letter_opacity = frac
                painter.setOpacity(self._opacity * letter_opacity)
            else:
                painter.setOpacity(self._opacity)

            painter.setPen(color)
            char_w = fm.horizontalAdvance(char)
            painter.drawText(QPointF(x, title_y), char)
            x += char_w

        painter.setOpacity(self._opacity)

        # ── Subtitle ──
        if self._text_reveal > 0.3:
            sub_opacity = min(1.0, (self._text_reveal - 0.3) / 0.3)
            painter.setOpacity(self._opacity * sub_opacity)

            sub_font = QFont("Segoe UI", 9, QFont.Weight.DemiBold)
            sub_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 2.5)
            painter.setFont(sub_font)
            painter.setPen(QColor("#64748B"))

            sub_fm = QFontMetrics(sub_font)
            sub_w = sub_fm.horizontalAdvance(self._SUBTITLE)
            painter.drawText(QPointF((w - sub_w) / 2, title_y + 32), self._SUBTITLE)

        # ── Version ──
        if self._text_reveal > 0.6:
            ver_opacity = min(1.0, (self._text_reveal - 0.6) / 0.2)
            painter.setOpacity(self._opacity * ver_opacity)

            ver_font = QFont("Segoe UI", 9, QFont.Weight.Normal)
            painter.setFont(ver_font)
            painter.setPen(QColor("#94A3B8"))

            ver_fm = QFontMetrics(ver_font)
            ver_w = ver_fm.horizontalAdvance(self._VERSION)
            painter.drawText(QPointF((w - ver_w) / 2, title_y + 54), self._VERSION)

        painter.setOpacity(self._opacity)

        # ── Progress bar at bottom ──
        bar_h = 3
        bar_y = h - bar_h - 20
        bar_margin = 80

        # Track
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#F1F5F9"))
        painter.drawRoundedRect(
            int(bar_margin), int(bar_y),
            int(w - 2 * bar_margin), bar_h,
            1, 1
        )

        # Fill
        fill_w = int((w - 2 * bar_margin) * self._progress)
        if fill_w > 0:
            gradient = QLinearGradient(bar_margin, 0, w - bar_margin, 0)
            gradient.setColorAt(0.0, QColor("#0D9488"))   # teal
            gradient.setColorAt(0.4, QColor("#1A73B5"))   # blue
            gradient.setColorAt(0.7, QColor("#7C3AED"))   # violet
            gradient.setColorAt(1.0, QColor("#06B6D4"))   # cyan
            painter.setBrush(gradient)
            painter.drawRoundedRect(
                int(bar_margin), int(bar_y),
                fill_w, bar_h,
                1, 1
            )

        # ── "Loading..." text ──
        if self._progress < 0.95:
            load_font = QFont("Segoe UI", 9)
            painter.setFont(load_font)
            painter.setPen(QColor("#94A3B8"))
            load_text = "Initializing forensic workspace..."
            lfm = QFontMetrics(load_font)
            lw = lfm.horizontalAdvance(load_text)
            painter.drawText(QPointF((w - lw) / 2, bar_y - 10), load_text)

        painter.end()

    def _hue_to_color(self, hue: float) -> QColor:
        """Map a 0-360 hue value to our curated palette."""
        # Normalize hue to 0-360
        hue = hue % 360.0

        # Blend between our palette stops
        stops = [
            (0,   QColor("#0D9488")),   # teal
            (90,  QColor("#1A73B5")),   # blue
            (180, QColor("#7C3AED")),   # violet
            (270, QColor("#06B6D4")),   # cyan
            (360, QColor("#0D9488")),   # back to teal
        ]

        for i in range(len(stops) - 1):
            h0, c0 = stops[i]
            h1, c1 = stops[i + 1]
            if h0 <= hue <= h1:
                t = (hue - h0) / (h1 - h0) if h1 != h0 else 0
                r = int(c0.red() + t * (c1.red() - c0.red()))
                g = int(c0.green() + t * (c1.green() - c0.green()))
                b = int(c0.blue() + t * (c1.blue() - c0.blue()))
                return QColor(r, g, b)

        return QColor("#0D9488")
