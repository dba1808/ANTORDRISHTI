"""
Antordrishti — OCR Preprocessing Service
Image quality analysis and adaptive preprocessing pipeline for OCR.
Analyzes image characteristics and conditionally applies enhancements
without destroying manuscript details.
"""

import logging
import math
from typing import Tuple, List, Optional

import numpy as np
import cv2

from models.ocr_models import ImageQualityReport, PreprocessingStep

logger = logging.getLogger("antordrishti.ocr.preprocessing")


# ═══════════════════════════════════════════════════════════════════
# IMAGE QUALITY ANALYZER
# ═══════════════════════════════════════════════════════════════════


def analyze_image_quality(image: np.ndarray) -> ImageQualityReport:
    """Perform comprehensive image quality analysis for OCR readiness.

    Analyzes resolution, sharpness, blur, brightness, contrast, noise,
    skew, background quality, and text visibility.

    Args:
        image: BGR numpy array.

    Returns:
        ImageQualityReport with all metrics and ratings.
    """
    report = ImageQualityReport()

    if image is None or image.size == 0:
        report.ocr_readiness = "Poor"
        return report

    h, w = image.shape[:2]
    report.width = w
    report.height = h

    # ── Resolution Assessment ────────────────────────────
    total_pixels = w * h
    if total_pixels >= 2_000_000:  # ≥ ~1400x1400 or similar
        report.resolution_rating = "Good"
        report.dpi_estimate = 300
    elif total_pixels >= 500_000:  # ≥ ~700x700
        report.resolution_rating = "Low"
        report.dpi_estimate = 150
    else:
        report.resolution_rating = "Very Low"
        report.dpi_estimate = 72

    # ── Convert to grayscale for analysis ────────────────
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()

    # ── Sharpness / Blur Detection ───────────────────────
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    report.sharpness_score = float(laplacian_var)

    if laplacian_var > 500:
        report.sharpness_rating = "Good"
        report.blur_detected = False
    elif laplacian_var > 100:
        report.sharpness_rating = "Moderate"
        report.blur_detected = False
    else:
        report.sharpness_rating = "Poor"
        report.blur_detected = True

    # ── Brightness Analysis ──────────────────────────────
    mean_brightness = float(np.mean(gray))
    report.brightness_mean = mean_brightness

    if 80 <= mean_brightness <= 200:
        report.brightness_rating = "Good"
    elif mean_brightness < 80:
        report.brightness_rating = "Dark"
    else:
        report.brightness_rating = "Bright"

    # ── Contrast Analysis ────────────────────────────────
    contrast_std = float(np.std(gray))
    report.contrast_std = contrast_std

    if contrast_std > 60:
        report.contrast_rating = "Good"
    elif contrast_std > 35:
        report.contrast_rating = "Moderate"
    else:
        report.contrast_rating = "Poor"

    # ── Noise Estimation ─────────────────────────────────
    # Using median-difference method
    denoised = cv2.medianBlur(gray, 3)
    noise_diff = cv2.absdiff(gray, denoised)
    noise_level = float(np.mean(noise_diff))
    report.noise_level = noise_level

    if noise_level < 3:
        report.noise_rating = "Low"
    elif noise_level < 8:
        report.noise_rating = "Moderate"
    else:
        report.noise_rating = "High"

    # ── Skew Detection ───────────────────────────────────
    skew_angle = _detect_skew(gray)
    report.skew_angle = skew_angle

    if abs(skew_angle) < 0.5:
        report.orientation_status = "Normal"
    elif abs(skew_angle) < 5.0:
        report.orientation_status = "Skewed"
    else:
        report.orientation_status = "Heavily Skewed"

    # ── Background Quality ───────────────────────────────
    # Analyze the border regions for background uniformity
    border_size = max(10, min(h, w) // 20)
    borders = np.concatenate([
        gray[:border_size, :].ravel(),
        gray[-border_size:, :].ravel(),
        gray[:, :border_size].ravel(),
        gray[:, -border_size:].ravel(),
    ])
    bg_std = float(np.std(borders))

    if bg_std < 15:
        report.background_quality = "Clean"
    elif bg_std < 35:
        report.background_quality = "Noisy"
    else:
        report.background_quality = "Uneven"

    # ── Text Visibility ──────────────────────────────────
    # Use adaptive threshold to find text regions, then assess density
    binary = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV, 15, 10
    )
    text_pixel_ratio = float(np.count_nonzero(binary)) / max(1, binary.size)

    if 0.05 <= text_pixel_ratio <= 0.4:
        report.text_visibility = "Good"
    elif 0.02 <= text_pixel_ratio <= 0.5:
        report.text_visibility = "Moderate"
    else:
        report.text_visibility = "Poor"

    # ── Handwriting Detection (heuristic) ────────────────
    is_hw, hw_conf = _detect_handwriting(gray, binary)
    report.is_handwritten = is_hw
    report.handwriting_confidence = hw_conf

    # ── Overall OCR Readiness ────────────────────────────
    issues = 0
    if report.resolution_rating == "Very Low":
        issues += 2
    elif report.resolution_rating == "Low":
        issues += 1
    if report.sharpness_rating == "Poor":
        issues += 2
    elif report.sharpness_rating == "Moderate":
        issues += 1
    if report.contrast_rating == "Poor":
        issues += 1
    if report.noise_rating == "High":
        issues += 1
    if report.text_visibility == "Poor":
        issues += 2

    if issues == 0:
        report.ocr_readiness = "Good"
    elif issues <= 2:
        report.ocr_readiness = "Needs Enhancement"
    else:
        report.ocr_readiness = "Poor"

    return report


def _detect_skew(gray: np.ndarray) -> float:
    """Estimate document skew angle using Hough line transform.

    Returns angle in degrees. Positive = clockwise skew.
    """
    try:
        # Edge detection
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)

        # Hough lines
        lines = cv2.HoughLinesP(
            edges, 1, np.pi / 180, threshold=100,
            minLineLength=gray.shape[1] // 4,
            maxLineGap=20
        )

        if lines is None or len(lines) == 0:
            return 0.0

        angles = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            dx = x2 - x1
            dy = y2 - y1
            if abs(dx) < 1:
                continue
            angle = math.degrees(math.atan2(dy, dx))
            # Filter to near-horizontal lines (text lines)
            if -45 < angle < 45:
                angles.append(angle)

        if not angles:
            return 0.0

        # Use median to be robust against outliers
        return float(np.median(angles))

    except Exception as e:
        logger.debug(f"Skew detection failed: {e}")
        return 0.0


def _detect_handwriting(gray: np.ndarray,
                        binary: np.ndarray) -> Tuple[bool, float]:
    """Heuristic handwriting detection based on stroke characteristics.

    Returns (is_handwritten, confidence).
    """
    try:
        # Find contours of text elements
        contours, _ = cv2.findContours(
            binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        if len(contours) < 10:
            return False, 0.0

        # Analyze contour properties
        areas = []
        aspect_ratios = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < 20:
                continue
            areas.append(area)
            x, y, w, h = cv2.boundingRect(cnt)
            if h > 0:
                aspect_ratios.append(w / h)

        if len(areas) < 10:
            return False, 0.0

        # Handwriting indicators:
        # 1. High variation in character sizes
        area_cv = float(np.std(areas) / max(1.0, np.mean(areas)))

        # 2. Irregular aspect ratios
        ar_cv = float(np.std(aspect_ratios) / max(0.01, np.mean(aspect_ratios)))

        # Combined heuristic score
        hw_score = (area_cv * 0.5 + ar_cv * 0.5)

        if hw_score > 1.2:
            return True, min(0.9, hw_score / 2.0)
        elif hw_score > 0.8:
            return True, min(0.7, hw_score / 2.0)
        else:
            return False, max(0.0, 0.3 - (0.8 - hw_score))

    except Exception:
        return False, 0.0


# ═══════════════════════════════════════════════════════════════════
# ADAPTIVE PREPROCESSING PIPELINE
# ═══════════════════════════════════════════════════════════════════


def preprocess_for_ocr(
    image: np.ndarray,
    quality_report: ImageQualityReport,
) -> Tuple[np.ndarray, List[PreprocessingStep]]:
    """Apply adaptive preprocessing based on image quality analysis.

    Only applies operations that are actually needed.
    Preserves the original — returns a processed copy.

    Args:
        image: BGR numpy array (original).
        quality_report: Result from analyze_image_quality().

    Returns:
        Tuple of (processed_image, list_of_steps).
    """
    processed = image.copy()
    steps: List[PreprocessingStep] = []

    # ── 1. Orientation / Deskew ──────────────────────────
    if abs(quality_report.skew_angle) >= 1.0:
        processed = _deskew(processed, quality_report.skew_angle)
        steps.append(PreprocessingStep(
            name="Deskew",
            applied=True,
            reason=f"Skew angle: {quality_report.skew_angle:.1f}°",
            details=f"Corrected {quality_report.skew_angle:.1f}° rotation",
        ))
    else:
        steps.append(PreprocessingStep(
            name="Deskew",
            applied=False,
            reason="Not Required",
            details=f"Skew angle {quality_report.skew_angle:.1f}° within tolerance",
        ))

    # ── 2. Resolution Enhancement ────────────────────────
    if quality_report.resolution_rating == "Very Low":
        processed = _upscale(processed, factor=2.0)
        steps.append(PreprocessingStep(
            name="Resolution Enhancement",
            applied=True,
            reason=f"Very low resolution ({quality_report.width}×{quality_report.height})",
            details="Upscaled 2× with cubic interpolation",
        ))
    elif quality_report.resolution_rating == "Low":
        processed = _upscale(processed, factor=1.5)
        steps.append(PreprocessingStep(
            name="Resolution Enhancement",
            applied=True,
            reason=f"Low resolution ({quality_report.width}×{quality_report.height})",
            details="Upscaled 1.5× with cubic interpolation",
        ))
    else:
        steps.append(PreprocessingStep(
            name="Resolution Enhancement",
            applied=False,
            reason="Not Required",
            details=f"Resolution adequate ({quality_report.width}×{quality_report.height})",
        ))

    # ── 3. Noise Reduction ───────────────────────────────
    if quality_report.noise_rating == "High":
        processed = _denoise(processed, strength=10)
        steps.append(PreprocessingStep(
            name="Noise Reduction",
            applied=True,
            reason=f"High noise level ({quality_report.noise_level:.1f})",
            details="Applied fast non-local means denoising (strength=10)",
        ))
    elif quality_report.noise_rating == "Moderate":
        processed = _denoise(processed, strength=5)
        steps.append(PreprocessingStep(
            name="Noise Reduction",
            applied=True,
            reason=f"Moderate noise level ({quality_report.noise_level:.1f})",
            details="Applied mild non-local means denoising (strength=5)",
        ))
    else:
        steps.append(PreprocessingStep(
            name="Noise Reduction",
            applied=False,
            reason="Not Required",
            details=f"Noise level acceptable ({quality_report.noise_level:.1f})",
        ))

    # ── 4. Contrast Enhancement ──────────────────────────
    if quality_report.contrast_rating == "Poor":
        processed = _enhance_contrast(processed, clip_limit=3.0)
        steps.append(PreprocessingStep(
            name="Contrast Enhancement",
            applied=True,
            reason=f"Poor contrast (σ={quality_report.contrast_std:.1f})",
            details="Applied CLAHE with clip_limit=3.0",
        ))
    elif quality_report.contrast_rating == "Moderate":
        processed = _enhance_contrast(processed, clip_limit=2.0)
        steps.append(PreprocessingStep(
            name="Contrast Enhancement",
            applied=True,
            reason=f"Moderate contrast (σ={quality_report.contrast_std:.1f})",
            details="Applied CLAHE with clip_limit=2.0",
        ))
    else:
        steps.append(PreprocessingStep(
            name="Contrast Enhancement",
            applied=False,
            reason="Not Required",
            details=f"Contrast adequate (σ={quality_report.contrast_std:.1f})",
        ))

    # ── 5. Brightness Normalization ──────────────────────
    if quality_report.brightness_rating == "Dark":
        processed = _adjust_brightness(processed, delta=40)
        steps.append(PreprocessingStep(
            name="Brightness Normalization",
            applied=True,
            reason=f"Image too dark (mean={quality_report.brightness_mean:.0f})",
            details="Increased brightness by +40",
        ))
    elif quality_report.brightness_rating == "Bright":
        processed = _adjust_brightness(processed, delta=-30)
        steps.append(PreprocessingStep(
            name="Brightness Normalization",
            applied=True,
            reason=f"Image too bright (mean={quality_report.brightness_mean:.0f})",
            details="Decreased brightness by -30",
        ))
    else:
        steps.append(PreprocessingStep(
            name="Brightness Normalization",
            applied=False,
            reason="Not Required",
            details=f"Brightness adequate (mean={quality_report.brightness_mean:.0f})",
        ))

    # ── 6. Background Normalization ──────────────────────
    if quality_report.background_quality == "Uneven":
        processed = _normalize_background(processed)
        steps.append(PreprocessingStep(
            name="Background Normalization",
            applied=True,
            reason="Uneven background detected",
            details="Applied morphological background subtraction",
        ))
    else:
        steps.append(PreprocessingStep(
            name="Background Normalization",
            applied=False,
            reason="Not Required",
            details=f"Background quality: {quality_report.background_quality}",
        ))

    quality_report.processed_width = processed.shape[1]
    quality_report.processed_height = processed.shape[0]

    return processed, steps


# ═══════════════════════════════════════════════════════════════════
# MULTI-VARIANT GENERATOR (for difficult documents)
# ═══════════════════════════════════════════════════════════════════


def generate_ocr_variants(
    image: np.ndarray,
    quality_report: ImageQualityReport,
) -> List[Tuple[str, np.ndarray]]:
    """Generate multiple preprocessing variants for difficult documents.

    Only generates variants when quality is not "Good".
    Returns list of (variant_name, processed_image) tuples.
    """
    if quality_report.ocr_readiness == "Good":
        return [("Original", image.copy())]

    variants: List[Tuple[str, np.ndarray]] = []

    # Variant A: Original + mild CLAHE
    variant_a = image.copy()
    variant_a = _enhance_contrast(variant_a, clip_limit=1.5)
    variants.append(("Mild Enhancement", variant_a))

    # Variant B: Grayscale + strong contrast
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    variant_b = _enhance_contrast_gray(gray, clip_limit=3.0)
    # Convert back to BGR for consistent processing
    variant_b = cv2.cvtColor(variant_b, cv2.COLOR_GRAY2BGR)
    variants.append(("Grayscale + Contrast", variant_b))

    # Variant C: Denoised + adaptive threshold (only for severe cases)
    if quality_report.ocr_readiness == "Poor":
        variant_c = _denoise(image.copy(), strength=8)
        variants.append(("Denoised", variant_c))

    return variants


# ═══════════════════════════════════════════════════════════════════
# INTERNAL OPERATIONS
# ═══════════════════════════════════════════════════════════════════


def _deskew(image: np.ndarray, angle: float) -> np.ndarray:
    """Rotate image to correct skew."""
    h, w = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)

    # Calculate new bounding dimensions
    cos = abs(M[0, 0])
    sin = abs(M[0, 1])
    new_w = int(h * sin + w * cos)
    new_h = int(h * cos + w * sin)
    M[0, 2] += (new_w - w) / 2
    M[1, 2] += (new_h - h) / 2

    # Use white background for document images
    border_value = (255, 255, 255) if len(image.shape) == 3 else 255
    return cv2.warpAffine(
        image, M, (new_w, new_h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=border_value,
    )


def _upscale(image: np.ndarray, factor: float = 2.0) -> np.ndarray:
    """Upscale image using cubic interpolation."""
    h, w = image.shape[:2]
    new_w = int(w * factor)
    new_h = int(h * factor)
    return cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_CUBIC)


def _denoise(image: np.ndarray, strength: int = 10) -> np.ndarray:
    """Apply non-local means denoising."""
    if len(image.shape) == 3:
        return cv2.fastNlMeansDenoisingColored(
            image, None, strength, strength, 7, 21
        )
    else:
        return cv2.fastNlMeansDenoising(image, None, strength, 7, 21)


def _enhance_contrast(image: np.ndarray,
                      clip_limit: float = 2.0) -> np.ndarray:
    """Apply CLAHE contrast enhancement to a color image."""
    if len(image.shape) == 2:
        return _enhance_contrast_gray(image, clip_limit)

    # Convert to LAB, enhance L channel
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l_chan, a_chan, b_chan = cv2.split(lab)

    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(8, 8))
    l_enhanced = clahe.apply(l_chan)

    lab_enhanced = cv2.merge([l_enhanced, a_chan, b_chan])
    return cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)


def _enhance_contrast_gray(gray: np.ndarray,
                           clip_limit: float = 2.0) -> np.ndarray:
    """Apply CLAHE contrast enhancement to a grayscale image."""
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(8, 8))
    return clahe.apply(gray)


def _adjust_brightness(image: np.ndarray, delta: int = 0) -> np.ndarray:
    """Adjust image brightness."""
    return cv2.convertScaleAbs(image, alpha=1.0, beta=delta)


def _normalize_background(image: np.ndarray) -> np.ndarray:
    """Normalize uneven background using morphological operations.

    Uses a large structuring element to estimate and subtract the background.
    """
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()

    # Estimate background with large morphological closing
    kernel_size = max(gray.shape[0], gray.shape[1]) // 10
    if kernel_size % 2 == 0:
        kernel_size += 1
    kernel_size = max(21, min(kernel_size, 101))

    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (kernel_size, kernel_size)
    )
    background = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)

    # Subtract background and normalize
    normalized = cv2.divide(gray, background, scale=255)

    if len(image.shape) == 3:
        return cv2.cvtColor(normalized, cv2.COLOR_GRAY2BGR)
    return normalized
