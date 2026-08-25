"""
Antordrishti — Image Processing Service
Comprehensive OpenCV-based image processing tools for forensic document analysis.
All operations take numpy arrays (BGR format) and return numpy arrays, preserving the source evidence.
"""

import numpy as np
import cv2
from typing import Optional, Tuple, Dict, Any

from PyQt5.QtGui import QImage


def qimage_to_cv(qimage: QImage) -> Optional[np.ndarray]:
    """Convert a QImage to a numpy array (BGR format for OpenCV)."""
    try:
        qimage = qimage.convertToFormat(QImage.Format.Format_RGB888)
        width = qimage.width()
        height = qimage.height()
        bytes_per_line = qimage.bytesPerLine()
        ptr = qimage.bits()
        ptr.setsize(height * bytes_per_line)
        arr = np.array(ptr).reshape(height, bytes_per_line)
        arr = arr[:, :width * 3].reshape(height, width, 3)
        return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
    except Exception:
        return None


def cv_to_qimage(cv_image: np.ndarray) -> Optional[QImage]:
    """Convert a numpy array (BGR, BGRA, or Grayscale) to QImage."""
    try:
        if cv_image is None:
            return None
        if len(cv_image.shape) == 2:
            h, w = cv_image.shape
            bytes_per_line = w
            return QImage(cv_image.data, w, h, bytes_per_line,
                          QImage.Format.Format_Grayscale8).copy()
        elif len(cv_image.shape) == 3:
            h, w, ch = cv_image.shape
            if ch == 3:
                rgb = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
                bytes_per_line = 3 * w
                return QImage(rgb.data, w, h, bytes_per_line,
                              QImage.Format.Format_RGB888).copy()
            elif ch == 4:
                rgba = cv2.cvtColor(cv_image, cv2.COLOR_BGRA2RGBA)
                bytes_per_line = 4 * w
                return QImage(rgba.data, w, h, bytes_per_line,
                              QImage.Format.Format_RGBA8888).copy()
        return None
    except Exception:
        return None


# ── 1. ENHANCEMENT TOOLS ───────────────────────────────────────

def to_grayscale(image: np.ndarray) -> np.ndarray:
    """Convert image to grayscale."""
    if len(image.shape) == 2:
        return image.copy()
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def resize_image(image: np.ndarray, width: int, height: int) -> np.ndarray:
    """Resize image to given dimensions."""
    w = max(10, width)
    h = max(10, height)
    return cv2.resize(image, (w, h), interpolation=cv2.INTER_AREA)


def adjust_brightness(image: np.ndarray, value: int = 0) -> np.ndarray:
    """Adjust brightness. value: -100 to +100."""
    return cv2.convertScaleAbs(image, alpha=1.0, beta=value)


def adjust_contrast(image: np.ndarray, value: float = 1.0) -> np.ndarray:
    """Adjust contrast. value: 0.1 to 3.0 (1.0 = normal)."""
    return cv2.convertScaleAbs(image, alpha=max(0.1, float(value)), beta=0)


def sharpen_image(image: np.ndarray) -> np.ndarray:
    """Apply high-pass sharpening kernel."""
    kernel = np.array([
        [0, -1, 0],
        [-1, 5, -1],
        [0, -1, 0]
    ], dtype=np.float32)
    return cv2.filter2D(image, -1, kernel)


# ── 2. BLUR & NOISE TOOLS ─────────────────────────────────────

def blur_image(image: np.ndarray, kernel_size: int = 5) -> np.ndarray:
    """Apply box blur."""
    k = max(1, kernel_size)
    return cv2.blur(image, (k, k))


def gaussian_blur(image: np.ndarray, kernel_size: int = 5) -> np.ndarray:
    """Apply Gaussian blur with odd kernel."""
    k = max(1, kernel_size)
    if k % 2 == 0:
        k += 1
    return cv2.GaussianBlur(image, (k, k), 0)


def median_blur(image: np.ndarray, kernel_size: int = 5) -> np.ndarray:
    """Apply Median blur (effective for salt-and-pepper noise)."""
    k = max(1, kernel_size)
    if k % 2 == 0:
        k += 1
    return cv2.medianBlur(image, k)


def add_noise(image: np.ndarray, amount: int = 25) -> np.ndarray:
    """Add simulated Gaussian noise to image."""
    noise = np.random.normal(0, max(1, amount), image.shape).astype(np.float32)
    noisy = np.clip(image.astype(np.float32) + noise, 0, 255)
    return noisy.astype(np.uint8)


def generate_noise_map(image: np.ndarray, scale: int = 8) -> np.ndarray:
    """Generate high-pass noise residual map via median subtraction."""
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    denoised = cv2.medianBlur(gray, 3)
    diff = cv2.absdiff(gray, denoised)
    noise_map = np.clip(diff.astype(np.float32) * scale, 0, 255).astype(np.uint8)
    return cv2.applyColorMap(noise_map, cv2.COLORMAP_VIRIDIS)


def estimate_noise_variance(image: np.ndarray) -> float:
    """Estimate global noise level using fast Laplacian standard deviation."""
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


# ── 3. THRESHOLD & EDGE TOOLS ─────────────────────────────────

def threshold_image(image: np.ndarray, value: int = 128) -> np.ndarray:
    """Apply binary threshold."""
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    _, result = cv2.threshold(gray, value, 255, cv2.THRESH_BINARY)
    return result


def adaptive_threshold(image: np.ndarray, block_size: int = 11, c_val: int = 2) -> np.ndarray:
    """Apply adaptive Gaussian thresholding (ideal for uneven document illumination)."""
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    bs = max(3, block_size)
    if bs % 2 == 0:
        bs += 1
    return cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, bs, c_val
    )


def canny_edge(image: np.ndarray, low: int = 50, high: int = 150) -> np.ndarray:
    """Apply Canny edge detection."""
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    return cv2.Canny(gray, low, high)


def sobel_edge(image: np.ndarray) -> np.ndarray:
    """Apply Sobel gradient magnitude filter (combining horizontal and vertical)."""
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    magnitude = cv2.magnitude(grad_x, grad_y)
    return cv2.convertScaleAbs(magnitude)


def laplacian_edge(image: np.ndarray) -> np.ndarray:
    """Apply 2nd order Laplacian derivative edge filter."""
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    lap = cv2.Laplacian(gray, cv2.CV_64F)
    return cv2.convertScaleAbs(lap)


# ── 4. COLOR & CHANNEL TOOLS ──────────────────────────────────

def to_hsv(image: np.ndarray) -> np.ndarray:
    """Convert BGR image to HSV color space."""
    if len(image.shape) == 2:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    return cv2.cvtColor(image, cv2.COLOR_BGR2HSV)


def isolate_channel(image: np.ndarray, channel: str) -> np.ndarray:
    """Extract isolated color channel (Red, Green, Blue) as color or grayscale."""
    if len(image.shape) == 2:
        return image.copy()

    b, g, r = cv2.split(image)
    zeros = np.zeros_like(b)

    ch = channel.lower()
    if ch == "red":
        return cv2.merge([zeros, zeros, r])
    elif ch == "green":
        return cv2.merge([zeros, g, zeros])
    elif ch == "blue":
        return cv2.merge([b, zeros, zeros])
    elif ch == "red_gray":
        return r
    elif ch == "green_gray":
        return g
    elif ch == "blue_gray":
        return b
    return image


# ── 5. HISTOGRAM GENERATOR ────────────────────────────────────

def compute_histogram(image: np.ndarray, mode: str = "all",
                      width: int = 420, height: int = 240) -> np.ndarray:
    """Render a publication-quality histogram graph.

    Args:
        image: BGR or grayscale numpy array.
        mode: 'all' (RGB overlay), 'red', 'green', 'blue', or 'grayscale'.
        width: Image width.
        height: Image height.

    Returns:
        BGR image containing styled histogram plot with axes and grid.
    """
    canvas = np.ones((height, width, 3), dtype=np.uint8) * 255

    # Margins
    pad_left = 36
    pad_right = 16
    pad_top = 24
    pad_bottom = 28
    plot_w = width - pad_left - pad_right
    plot_h = height - pad_top - pad_bottom

    # Draw grid background
    cv2.rectangle(canvas, (pad_left, pad_top), (pad_left + plot_w, pad_top + plot_h),
                  (245, 247, 250), -1)
    for y_val in range(4):
        gy = int(pad_top + y_val * plot_h / 4)
        cv2.line(canvas, (pad_left, gy), (pad_left + plot_w, gy), (226, 232, 240), 1)

    is_gray = len(image.shape) == 2 or mode.lower() == "grayscale"

    if is_gray:
        gray_img = image if len(image.shape) == 2 else cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        hist = cv2.calcHist([gray_img], [0], None, [256], [0, 256])
        cv2.normalize(hist, hist, 0, plot_h - 4, cv2.NORM_MINMAX)
        hist = hist.flatten()

        pts = []
        for i in range(256):
            x = int(pad_left + i * plot_w / 256)
            y = int(pad_top + plot_h - hist[i])
            pts.append((x, y))

        for j in range(1, len(pts)):
            cv2.line(canvas, pts[j - 1], pts[j], (71, 85, 105), 2, cv2.LINE_AA)
            cv2.line(canvas, (pts[j][0], pad_top + plot_h), pts[j], (203, 213, 225), 1)
    else:
        # Channels to draw
        channel_configs = []
        mode_l = mode.lower()
        if mode_l == "red":
            channel_configs = [(2, (220, 38, 38))]     # Red
        elif mode_l == "green":
            channel_configs = [(1, (22, 163, 74))]     # Green
        elif mode_l == "blue":
            channel_configs = [(0, (37, 99, 235))]     # Blue
        else:
            channel_configs = [
                (0, (37, 99, 235)),  # Blue
                (1, (22, 163, 74)),  # Green
                (2, (220, 38, 38))   # Red
            ]

        for ch_idx, color in channel_configs:
            hist = cv2.calcHist([image], [ch_idx], None, [256], [0, 256])
            cv2.normalize(hist, hist, 0, plot_h - 4, cv2.NORM_MINMAX)
            hist = hist.flatten()
            pts = []
            for i in range(256):
                x = int(pad_left + i * plot_w / 256)
                y = int(pad_top + plot_h - hist[i])
                pts.append((x, y))
            for j in range(1, len(pts)):
                cv2.line(canvas, pts[j - 1], pts[j], color, 2, cv2.LINE_AA)

    # Outer border & axes
    cv2.rectangle(canvas, (pad_left, pad_top), (pad_left + plot_w, pad_top + plot_h),
                  (203, 213, 225), 1)

    # Labels
    cv2.putText(canvas, "0", (pad_left - 4, height - 12),
                cv2.FONT_HERSHEY_SIMPLEX, 0.35, (100, 116, 139), 1)
    cv2.putText(canvas, "128", (pad_left + int(plot_w / 2) - 10, height - 12),
                cv2.FONT_HERSHEY_SIMPLEX, 0.35, (100, 116, 139), 1)
    cv2.putText(canvas, "255", (pad_left + plot_w - 20, height - 12),
                cv2.FONT_HERSHEY_SIMPLEX, 0.35, (100, 116, 139), 1)

    title_text = f"Histogram [{mode.upper()}]"
    cv2.putText(canvas, title_text, (pad_left + 4, 16),
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (15, 23, 42), 1)

    return canvas
