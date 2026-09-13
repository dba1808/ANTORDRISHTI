"""
Antordrishti — Forensic Histogram Analysis Service
Provides real pixel extraction, 256-bin exact channel histogram calculation,
numerical invariant validation, statistics, tonal analysis, clipping analysis,
CDF calculation, and export functions for images and PDFs.
"""

import os
import csv
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, Tuple, List
import numpy as np
import cv2
from PIL import Image

try:
    import pymupdf as fitz
except Exception:
    try:
        import fitz
    except Exception:
        fitz = None

IST_TZ = timezone(timedelta(hours=5, minutes=30))


@dataclass
class HistogramData:
    """Forensic histogram record for an evidence file or PDF page."""
    file_path: str = ""
    file_name: str = ""
    sha256: str = ""
    case_id: str = ""
    evidence_id: str = ""
    page_num: int = 1
    total_pages: int = 1
    render_dpi: int = 150
    source_label: str = "Original Evidence"
    color_space: str = "RGB"
    width: int = 0
    height: int = 0
    total_pixels: int = 0
    bit_depth: int = 8
    has_alpha: bool = False
    
    # 256-bin histograms (np.ndarray of int64)
    channel_mode: str = "rgb"  # 'rgb', 'grayscale', 'red', 'green', 'blue', 'luminance', 'alpha'
    hist_red: Optional[np.ndarray] = None
    hist_green: Optional[np.ndarray] = None
    hist_blue: Optional[np.ndarray] = None
    hist_gray: Optional[np.ndarray] = None
    hist_alpha: Optional[np.ndarray] = None
    
    # CDF (Cumulative Distribution Function 0.0 - 100.0%)
    cdf_red: Optional[np.ndarray] = None
    cdf_green: Optional[np.ndarray] = None
    cdf_blue: Optional[np.ndarray] = None
    cdf_gray: Optional[np.ndarray] = None
    
    # Numerical Statistics
    stats: Dict[str, Any] = field(default_factory=dict)
    channel_stats: Dict[str, Dict[str, float]] = field(default_factory=dict)
    clipping: Dict[str, Any] = field(default_factory=dict)
    tonal: Dict[str, Any] = field(default_factory=dict)
    
    # Invariant and validation flags
    invariant_passed: bool = True
    invariant_notes: str = ""
    timestamp_ist: str = ""
    error_message: str = ""


def get_ist_timestamp() -> str:
    return datetime.now(IST_TZ).strftime("%Y-%m-%d %H:%M:%S IST")


def extract_pixel_array_from_evidence(
    file_path: str,
    page_num: int = 0,
    dpi: int = 150
) -> Tuple[Optional[np.ndarray], Dict[str, Any]]:
    """Extract raw decoded pixel array from evidence image or PDF page at deterministic DPI.
    
    Returns:
        (image_array, info_dict)
        image_array is RGB (H, W, 3), RGBA (H, W, 4), or Grayscale (H, W).
    """
    if not os.path.exists(file_path):
        return None, {"error": f"File does not exist: {file_path}"}
    
    ext = os.path.splitext(file_path)[1].lower()
    info = {
        "file_path": file_path,
        "file_name": os.path.basename(file_path),
        "ext": ext,
        "page_num": page_num + 1,
        "total_pages": 1,
        "render_dpi": dpi,
        "bit_depth": 8,
        "has_alpha": False,
        "color_space": "Unknown"
    }

    # PDF rendering
    if ext == ".pdf":
        if fitz is None:
            return None, {"error": "PyMuPDF (fitz) library is not installed."}
        try:
            doc = fitz.open(file_path)
            info["total_pages"] = len(doc)
            page_idx = max(0, min(page_num, len(doc) - 1))
            info["page_num"] = page_idx + 1

            page = doc[page_idx]
            zoom = dpi / 72.0
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, alpha=False)  # Force RGB without alpha for document page
            
            # Convert PyMuPDF pixmap to numpy RGB array
            img_np = np.frombuffer(pix.samples, dtype=np.uint8).reshape((pix.height, pix.width, 3))
            info["color_space"] = "RGB"
            info["has_alpha"] = False
            return img_np, info
        except Exception as e:
            return None, {"error": f"Failed to render PDF page: {str(e)}"}

    # Raster Images (JPEG, PNG, TIFF, BMP, WEBP)
    try:
        pil_img = Image.open(file_path)
        info["bit_depth"] = 8
        mode = pil_img.mode

        if mode in ("RGBA", "LA") or (mode == "P" and "transparency" in pil_img.info):
            info["has_alpha"] = True

        if mode == "1" or mode == "L":
            info["color_space"] = "Grayscale"
            img_np = np.array(pil_img.convert("L"))
        elif mode == "RGBA":
            info["color_space"] = "RGBA"
            img_np = np.array(pil_img)
        elif mode == "LA":
            info["color_space"] = "LA (Grayscale + Alpha)"
            img_np = np.array(pil_img)
        elif mode == "I;16" or mode == "I":
            info["color_space"] = "16-bit Grayscale"
            info["bit_depth"] = 16
            img_np = np.array(pil_img)
        else:
            info["color_space"] = "RGB"
            img_np = np.array(pil_img.convert("RGB"))

        return img_np, info
    except Exception as e:
        # Fallback to OpenCV
        try:
            cv_img = cv2.imread(file_path, cv2.IMREAD_UNCHANGED)
            if cv_img is None:
                return None, {"error": f"Could not decode image file: {file_path}"}
            
            if len(cv_img.shape) == 2:
                info["color_space"] = "Grayscale"
                return cv_img, info
            elif cv_img.shape[2] == 4:
                info["color_space"] = "BGRA"
                info["has_alpha"] = True
                rgb_img = cv2.cvtColor(cv_img, cv2.COLOR_BGRA2RGBA)
                return rgb_img, info
            else:
                info["color_space"] = "BGR"
                rgb_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
                return rgb_img, info
        except Exception as ex:
            return None, {"error": f"Failed to load image: {str(ex)}"}


def calculate_forensic_histogram(
    pixel_array: np.ndarray,
    info: Dict[str, Any],
    channel_mode: str = "rgb",
    source_label: str = "Original Evidence",
    case_id: str = "",
    evidence_id: str = "",
    sha256: str = ""
) -> HistogramData:
    """Calculate 256-bin exact histograms and numerical statistics from pixel array.
    
    Args:
        pixel_array: numpy array of shape (H, W, C) or (H, W).
        info: metadata dictionary from extract_pixel_array_from_evidence.
        channel_mode: 'rgb', 'grayscale', 'red', 'green', 'blue', 'luminance', 'alpha'.
        source_label: Label indicating data source ('Original Evidence', 'PDF Page X', etc.).
    """
    hist_data = HistogramData(
        file_path=info.get("file_path", ""),
        file_name=info.get("file_name", ""),
        sha256=sha256,
        case_id=case_id,
        evidence_id=evidence_id,
        page_num=info.get("page_num", 1),
        total_pages=info.get("total_pages", 1),
        render_dpi=info.get("render_dpi", 150),
        source_label=source_label,
        color_space=info.get("color_space", "RGB"),
        bit_depth=info.get("bit_depth", 8),
        has_alpha=info.get("has_alpha", False),
        channel_mode=channel_mode.lower(),
        timestamp_ist=get_ist_timestamp()
    )

    if pixel_array is None or pixel_array.size == 0:
        hist_data.error_message = "Pixel array is empty or None."
        hist_data.invariant_passed = False
        return hist_data

    h, w = pixel_array.shape[:2]
    hist_data.width = w
    hist_data.height = h
    total_pixels = h * w
    hist_data.total_pixels = total_pixels

    # Separate RGB and Alpha if 4-channel RGBA
    alpha_channel = None
    if len(pixel_array.shape) == 3 and pixel_array.shape[2] == 4:
        alpha_channel = pixel_array[:, :, 3]
        rgb_array = pixel_array[:, :, :3]
    elif len(pixel_array.shape) == 3 and pixel_array.shape[2] == 3:
        rgb_array = pixel_array
    else:
        rgb_array = None  # Grayscale

    # Ensure 8-bit array for 256-bin indexing
    if pixel_array.dtype != np.uint8 and info.get("bit_depth") == 16:
        scaled_array = (pixel_array / 256.0).astype(np.uint8)
    else:
        scaled_array = pixel_array

    # 1. Compute Channel Histograms (Exact 256 bins via np.bincount)
    if rgb_array is not None:
        r_flat = scaled_array[:, :, 0].ravel() if scaled_array.shape[2] >= 3 else scaled_array.ravel()
        g_flat = scaled_array[:, :, 1].ravel() if scaled_array.shape[2] >= 3 else scaled_array.ravel()
        b_flat = scaled_array[:, :, 2].ravel() if scaled_array.shape[2] >= 3 else scaled_array.ravel()

        hist_data.hist_red = np.bincount(r_flat, minlength=256).astype(np.int64)
        hist_data.hist_green = np.bincount(g_flat, minlength=256).astype(np.int64)
        hist_data.hist_blue = np.bincount(b_flat, minlength=256).astype(np.int64)

        # Grayscale from RGB using standard BT.601 weights
        gray_flat = (0.299 * r_flat + 0.587 * g_flat + 0.114 * b_flat).astype(np.uint8)
        hist_data.hist_gray = np.bincount(gray_flat, minlength=256).astype(np.int64)

        # Cumulative Distribution Functions (CDF %)
        hist_data.cdf_red = (np.cumsum(hist_data.hist_red) / float(total_pixels)) * 100.0
        hist_data.cdf_green = (np.cumsum(hist_data.hist_green) / float(total_pixels)) * 100.0
        hist_data.cdf_blue = (np.cumsum(hist_data.hist_blue) / float(total_pixels)) * 100.0
        hist_data.cdf_gray = (np.cumsum(hist_data.hist_gray) / float(total_pixels)) * 100.0

        # RGB Invariant Check: sum(red) == sum(green) == sum(blue) == total_pixels
        r_sum = int(np.sum(hist_data.hist_red))
        g_sum = int(np.sum(hist_data.hist_green))
        b_sum = int(np.sum(hist_data.hist_blue))
        if r_sum != total_pixels or g_sum != total_pixels or b_sum != total_pixels:
            hist_data.invariant_passed = False
            hist_data.invariant_notes = f"RGB channel bin sums ({r_sum}, {g_sum}, {b_sum}) do not match total pixels ({total_pixels})."

    else:
        # Single channel grayscale
        gray_flat = scaled_array.ravel()
        hist_data.hist_gray = np.bincount(gray_flat, minlength=256).astype(np.int64)
        hist_data.cdf_gray = (np.cumsum(hist_data.hist_gray) / float(total_pixels)) * 100.0

        # Grayscale Invariant Check: sum(gray) == total_pixels
        g_sum = int(np.sum(hist_data.hist_gray))
        if g_sum != total_pixels:
            hist_data.invariant_passed = False
            hist_data.invariant_notes = f"Grayscale bin sum ({g_sum}) does not match total pixels ({total_pixels})."

    if alpha_channel is not None:
        a_flat = alpha_channel.ravel()
        hist_data.hist_alpha = np.bincount(a_flat, minlength=256).astype(np.int64)

    # 2. Compute Statistics from Actual Pixel Values
    target_flat = gray_flat
    if channel_mode == "red" and hist_data.hist_red is not None:
        target_flat = r_flat
    elif channel_mode == "green" and hist_data.hist_green is not None:
        target_flat = g_flat
    elif channel_mode == "blue" and hist_data.hist_blue is not None:
        target_flat = b_flat
    elif channel_mode == "alpha" and alpha_channel is not None:
        target_flat = a_flat

    mean_v = float(np.mean(target_flat))
    std_v = float(np.std(target_flat))
    median_v = float(np.median(target_flat))
    min_v = int(np.min(target_flat))
    max_v = int(np.max(target_flat))

    percentiles = {
        "P1": float(np.percentile(target_flat, 1)),
        "P5": float(np.percentile(target_flat, 5)),
        "P25": float(np.percentile(target_flat, 25)),
        "P50": float(np.percentile(target_flat, 50)),
        "P75": float(np.percentile(target_flat, 75)),
        "P95": float(np.percentile(target_flat, 95)),
        "P99": float(np.percentile(target_flat, 99)),
    }

    hist_data.stats = {
        "pixel_count": total_pixels,
        "mean": round(mean_v, 2),
        "median": round(median_v, 2),
        "std_dev": round(std_v, 2),
        "min": min_v,
        "max": max_v,
        "dynamic_range": max_v - min_v,
        "percentiles": percentiles,
    }

    # Per-Channel Statistics if RGB
    if rgb_array is not None:
        hist_data.channel_stats = {
            "Red": {
                "mean": round(float(np.mean(r_flat)), 2),
                "std_dev": round(float(np.std(r_flat)), 2),
                "min": int(np.min(r_flat)),
                "max": int(np.max(r_flat)),
            },
            "Green": {
                "mean": round(float(np.mean(g_flat)), 2),
                "std_dev": round(float(np.std(g_flat)), 2),
                "min": int(np.min(g_flat)),
                "max": int(np.max(g_flat)),
            },
            "Blue": {
                "mean": round(float(np.mean(b_flat)), 2),
                "std_dev": round(float(np.std(b_flat)), 2),
                "min": int(np.min(b_flat)),
                "max": int(np.max(b_flat)),
            },
        }

    # 3. Saturated Clipping Analysis (Black == 0, White == 255)
    active_hist = hist_data.hist_gray
    if channel_mode == "red" and hist_data.hist_red is not None:
        active_hist = hist_data.hist_red
    elif channel_mode == "green" and hist_data.hist_green is not None:
        active_hist = hist_data.hist_green
    elif channel_mode == "blue" and hist_data.hist_blue is not None:
        active_hist = hist_data.hist_blue

    black_clip_count = int(active_hist[0])
    white_clip_count = int(active_hist[255])
    black_clip_pct = round((black_clip_count / float(total_pixels)) * 100.0, 2)
    white_clip_pct = round((white_clip_count / float(total_pixels)) * 100.0, 2)

    hist_data.clipping = {
        "black_count": black_clip_count,
        "black_pct": black_clip_pct,
        "white_count": white_clip_count,
        "white_pct": white_clip_pct,
    }

    if rgb_array is not None:
        hist_data.clipping["red_black_pct"] = round((int(hist_data.hist_red[0]) / float(total_pixels)) * 100.0, 2)
        hist_data.clipping["red_white_pct"] = round((int(hist_data.hist_red[255]) / float(total_pixels)) * 100.0, 2)
        hist_data.clipping["green_black_pct"] = round((int(hist_data.hist_green[0]) / float(total_pixels)) * 100.0, 2)
        hist_data.clipping["green_white_pct"] = round((int(hist_data.hist_green[255]) / float(total_pixels)) * 100.0, 2)
        hist_data.clipping["blue_black_pct"] = round((int(hist_data.hist_blue[0]) / float(total_pixels)) * 100.0, 2)
        hist_data.clipping["blue_white_pct"] = round((int(hist_data.hist_blue[255]) / float(total_pixels)) * 100.0, 2)

    # 4. Tonal Distribution (Shadows 0-84, Midtones 85-170, Highlights 171-255)
    shadows_count = int(np.sum(active_hist[0:85]))
    midtones_count = int(np.sum(active_hist[85:171]))
    highlights_count = int(np.sum(active_hist[171:256]))

    hist_data.tonal = {
        "shadows_count": shadows_count,
        "shadows_pct": round((shadows_count / float(total_pixels)) * 100.0, 2),
        "midtones_count": midtones_count,
        "midtones_pct": round((midtones_count / float(total_pixels)) * 100.0, 2),
        "highlights_count": highlights_count,
        "highlights_pct": round((highlights_count / float(total_pixels)) * 100.0, 2),
    }

    return hist_data


def export_histogram_csv(hist_data: HistogramData, output_path: str) -> bool:
    """Export raw 256-bin histogram counts to CSV format."""
    try:
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["# ANTORDRISHTI Forensic Histogram Export"])
            writer.writerow(["# File", hist_data.file_name])
            writer.writerow(["# Case ID", hist_data.case_id or "Unassigned"])
            writer.writerow(["# Evidence ID", hist_data.evidence_id or "Unassigned"])
            writer.writerow(["# SHA-256", hist_data.sha256 or "N/A"])
            writer.writerow(["# Source", hist_data.source_label])
            writer.writerow(["# Page", f"{hist_data.page_num} of {hist_data.total_pages}"])
            writer.writerow(["# Resolution", f"{hist_data.width}x{hist_data.height}"])
            writer.writerow(["# Total Pixels", hist_data.total_pixels])
            writer.writerow(["# Generated At", hist_data.timestamp_ist])
            writer.writerow([])

            if hist_data.hist_red is not None and hist_data.hist_green is not None and hist_data.hist_blue is not None:
                writer.writerow(["Intensity", "Red_Count", "Green_Count", "Blue_Count", "Grayscale_Count"])
                for i in range(256):
                    r_c = hist_data.hist_red[i]
                    g_c = hist_data.hist_green[i]
                    b_c = hist_data.hist_blue[i]
                    gr_c = hist_data.hist_gray[i] if hist_data.hist_gray is not None else 0
                    writer.writerow([i, r_c, g_c, b_c, gr_c])
            else:
                writer.writerow(["Intensity", "Grayscale_Count"])
                for i in range(256):
                    gr_c = hist_data.hist_gray[i] if hist_data.hist_gray is not None else 0
                    writer.writerow([i, gr_c])
        return True
    except Exception as e:
        return False


def export_histogram_txt(hist_data: HistogramData, output_path: str) -> bool:
    """Export forensic histogram summary report to TXT format."""
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("========================================================\n")
            f.write("       ANTORDRISHTI FORENSIC HISTOGRAM REPORT          \n")
            f.write("========================================================\n\n")
            f.write(f"Case Name / ID     : {hist_data.case_id or 'Unassigned'}\n")
            f.write(f"Evidence ID        : {hist_data.evidence_id or 'Unassigned'}\n")
            f.write(f"File Name          : {hist_data.file_name}\n")
            f.write(f"File Path          : {hist_data.file_path}\n")
            f.write(f"SHA-256 Hash       : {hist_data.sha256 or 'N/A'}\n")
            f.write(f"Source             : {hist_data.source_label}\n")
            f.write(f"Page Number        : Page {hist_data.page_num} of {hist_data.total_pages}\n")
            f.write(f"Render DPI         : {hist_data.render_dpi} DPI\n")
            f.write(f"Dimensions         : {hist_data.width} x {hist_data.height} pixels\n")
            f.write(f"Total Pixel Count  : {hist_data.total_pixels:,}\n")
            f.write(f"Color Space        : {hist_data.color_space} ({hist_data.bit_depth}-bit)\n")
            f.write(f"Timestamp (IST)    : {hist_data.timestamp_ist}\n\n")

            f.write("--------------------------------------------------------\n")
            f.write("1. STATISTICAL METRICS\n")
            f.write("--------------------------------------------------------\n")
            stats = hist_data.stats
            f.write(f"Mean Intensity     : {stats.get('mean', 'N/A')}\n")
            f.write(f"Median Intensity   : {stats.get('median', 'N/A')}\n")
            f.write(f"Std Deviation      : {stats.get('std_dev', 'N/A')}\n")
            f.write(f"Min Intensity      : {stats.get('min', 'N/A')}\n")
            f.write(f"Max Intensity      : {stats.get('max', 'N/A')}\n")
            f.write(f"Dynamic Range      : {stats.get('dynamic_range', 'N/A')}\n\n")

            pcts = stats.get("percentiles", {})
            f.write("Percentiles:\n")
            f.write(f"  P1: {pcts.get('P1')}  | P5: {pcts.get('P5')}  | P25: {pcts.get('P25')}\n")
            f.write(f"  P50: {pcts.get('P50')} | P75: {pcts.get('P75')} | P95: {pcts.get('P95')} | P99: {pcts.get('P99')}\n\n")

            f.write("--------------------------------------------------------\n")
            f.write("2. CLIPPING & SATURATION ANALYSIS\n")
            f.write("--------------------------------------------------------\n")
            clip = hist_data.clipping
            f.write(f"Black Clipping (Intensity 0)   : {clip.get('black_count', 0):,} pixels ({clip.get('black_pct', 0)}%)\n")
            f.write(f"White Clipping (Intensity 255) : {clip.get('white_count', 0):,} pixels ({clip.get('white_pct', 0)}%)\n\n")

            if hist_data.channel_stats:
                f.write("Per-Channel Clipping:\n")
                f.write(f"  Red   -> Black: {clip.get('red_black_pct', 0)}% | White: {clip.get('red_white_pct', 0)}%\n")
                f.write(f"  Green -> Black: {clip.get('green_black_pct', 0)}% | White: {clip.get('green_white_pct', 0)}%\n")
                f.write(f"  Blue  -> Black: {clip.get('blue_black_pct', 0)}% | White: {clip.get('blue_white_pct', 0)}%\n\n")

            f.write("--------------------------------------------------------\n")
            f.write("3. TONAL DISTRIBUTION\n")
            f.write("--------------------------------------------------------\n")
            tonal = hist_data.tonal
            f.write(f"Shadows (0-84)     : {tonal.get('shadows_count', 0):,} pixels ({tonal.get('shadows_pct', 0)}%)\n")
            f.write(f"Midtones (85-170)  : {tonal.get('midtones_count', 0):,} pixels ({tonal.get('midtones_pct', 0)}%)\n")
            f.write(f"Highlights (171-255): {tonal.get('highlights_count', 0):,} pixels ({tonal.get('highlights_pct', 0)}%)\n\n")

            f.write("--------------------------------------------------------\n")
            f.write("4. NUMERICAL INVARIANT & PROVENANCE\n")
            f.write("--------------------------------------------------------\n")
            f.write(f"Invariant Verification : {'PASSED (Sum == Total Pixels)' if hist_data.invariant_passed else 'FAILED'}\n")
            if not hist_data.invariant_passed:
                f.write(f"Invariant Notes        : {hist_data.invariant_notes}\n")
            f.write("\n========================================================\n")
            f.write("      END OF ANTORDRISHTI HISTOGRAM EXAMINATION REPORT  \n")
            f.write("========================================================\n")
        return True
    except Exception as e:
        return False


def render_histogram_plot_image(
    hist_data: HistogramData,
    mode: str = "rgb",
    log_scale: bool = False,
    show_cdf: bool = False,
    width: int = 800,
    height: int = 420,
    hover_bin: Optional[int] = None
) -> np.ndarray:
    """Render a publication-grade high-resolution forensic histogram plot image (BGR format).
    
    Supports:
    - RGB overlay mode
    - Grayscale / Red / Green / Blue / Luminance / Alpha modes
    - Logarithmic scale option (log10(1 + count))
    - Cumulative Distribution Function (CDF) overlay option
    - Hover intensity cursor inspection
    """
    canvas = np.ones((height, width, 3), dtype=np.uint8) * 255

    pad_left = 60
    pad_right = 50
    pad_top = 45
    pad_bottom = 45
    plot_w = width - pad_left - pad_right
    plot_h = height - pad_top - pad_bottom

    # Background grid
    cv2.rectangle(canvas, (pad_left, pad_top), (pad_left + plot_w, pad_top + plot_h), (248, 250, 252), -1)
    
    # Grid lines (Horizontal)
    for y_idx in range(5):
        gy = int(pad_top + y_idx * plot_h / 4)
        cv2.line(canvas, (pad_left, gy), (pad_left + plot_w, gy), (226, 232, 240), 1)

    # Grid lines (Vertical intensity markers: 0, 64, 128, 192, 255)
    for x_val in [0, 64, 128, 192, 255]:
        gx = int(pad_left + (x_val * plot_w / 255.0))
        cv2.line(canvas, (gx, pad_top), (gx, pad_top + plot_h), (226, 232, 240), 1)

    mode_clean = mode.lower()
    
    # Select channels to draw
    channels_to_draw = []  # [(hist_array, cdf_array, color_bgr, label)]
    if mode_clean == "rgb" and hist_data.hist_red is not None:
        channels_to_draw = [
            (hist_data.hist_blue, hist_data.cdf_blue, (235, 99, 37), "B"),    # Blue
            (hist_data.hist_green, hist_data.cdf_green, (74, 163, 22), "G"),  # Green
            (hist_data.hist_red, hist_data.cdf_red, (38, 38, 220), "R"),      # Red
        ]
    elif mode_clean == "red" and hist_data.hist_red is not None:
        channels_to_draw = [(hist_data.hist_red, hist_data.cdf_red, (38, 38, 220), "Red")]
    elif mode_clean == "green" and hist_data.hist_green is not None:
        channels_to_draw = [(hist_data.hist_green, hist_data.cdf_green, (74, 163, 22), "Green")]
    elif mode_clean == "blue" and hist_data.hist_blue is not None:
        channels_to_draw = [(hist_data.hist_blue, hist_data.cdf_blue, (235, 99, 37), "Blue")]
    elif mode_clean == "alpha" and hist_data.hist_alpha is not None:
        channels_to_draw = [(hist_data.hist_alpha, None, (160, 160, 160), "Alpha")]
    else:
        # Grayscale
        ghist = hist_data.hist_gray if hist_data.hist_gray is not None else np.zeros(256, dtype=np.int64)
        gcdf = hist_data.cdf_gray
        channels_to_draw = [(ghist, gcdf, (71, 85, 105), "Grayscale")]

    # Calculate max peak for scaling
    max_count = 1
    for h_arr, _, _, _ in channels_to_draw:
        if h_arr is not None and len(h_arr) > 0:
            m = np.max(h_arr)
            if m > max_count:
                max_count = m

    # Plot scale transformation
    def scale_y(val):
        if log_scale:
            log_max = np.log10(max_count + 1.0)
            log_val = np.log10(val + 1.0)
            scaled = (log_val / log_max) if log_max > 0 else 0
        else:
            scaled = val / float(max_count)
        return int(pad_top + plot_h - (scaled * (plot_h - 10)))

    # Draw Channel Curves
    for h_arr, cdf_arr, color, _ in channels_to_draw:
        if h_arr is None:
            continue
        pts = []
        for i in range(256):
            x = int(pad_left + (i * plot_w / 255.0))
            y = scale_y(h_arr[i])
            pts.append((x, y))

        # Fill subtle area underneath single channel
        if len(channels_to_draw) == 1:
            poly_pts = [(pad_left, pad_top + plot_h)] + pts + [(pad_left + plot_w, pad_top + plot_h)]
            cv2.fillPoly(canvas, [np.array(poly_pts, dtype=np.int32)], (241, 245, 249))

        # Draw line segments
        for j in range(1, len(pts)):
            cv2.line(canvas, pts[j - 1], pts[j], color, 2, cv2.LINE_AA)

        # Draw CDF overlay if requested
        if show_cdf and cdf_arr is not None:
            cdf_pts = []
            for i in range(256):
                cx = int(pad_left + (i * plot_w / 255.0))
                cy = int(pad_top + plot_h - ((cdf_arr[i] / 100.0) * (plot_h - 10)))
                cdf_pts.append((cx, cy))
            for j in range(1, len(cdf_pts)):
                cv2.line(canvas, cdf_pts[j - 1], cdf_pts[j], (180, 83, 9), 1, cv2.LINE_AA)

    # Outer border
    cv2.rectangle(canvas, (pad_left, pad_top), (pad_left + plot_w, pad_top + plot_h), (203, 213, 225), 1)

    # Hover Cursor Inspection Line & Tooltip Box
    if hover_bin is not None and 0 <= hover_bin <= 255:
        hx = int(pad_left + (hover_bin * plot_w / 255.0))
        cv2.line(canvas, (hx, pad_top), (hx, pad_top + plot_h), (180, 83, 9), 1, cv2.LINE_AA)
        
        # Build live hover text
        hover_text = f"Intensity: {hover_bin}"
        if mode_clean == "rgb" and hist_data.hist_red is not None:
            r_c = hist_data.hist_red[hover_bin]
            g_c = hist_data.hist_green[hover_bin]
            b_c = hist_data.hist_blue[hover_bin]
            hover_sub = f"R:{r_c:,}  G:{g_c:,}  B:{b_c:,}"
        else:
            g_c = hist_data.hist_gray[hover_bin] if hist_data.hist_gray is not None else 0
            hover_sub = f"Count: {g_c:,}"

        # Draw tooltip card in graph top right
        box_w = 170
        box_h = 42
        bx = pad_left + plot_w - box_w - 10
        by = pad_top + 10
        cv2.rectangle(canvas, (bx, by), (bx + box_w, by + box_h), (250, 244, 230), -1)
        cv2.rectangle(canvas, (bx, by), (bx + box_w, by + box_h), (176, 141, 58), 1)
        cv2.putText(canvas, hover_text, (bx + 8, by + 16), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (120, 95, 35), 1, cv2.LINE_AA)
        cv2.putText(canvas, hover_sub, (bx + 8, by + 32), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (15, 23, 42), 1, cv2.LINE_AA)

    # Axes Tick Labels (X Axis)
    x_ticks = [0, 64, 128, 192, 255]
    for x_val in x_ticks:
        gx = int(pad_left + (x_val * plot_w / 255.0))
        cv2.putText(canvas, str(x_val), (gx - 10, pad_top + plot_h + 16),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, (100, 116, 139), 1, cv2.LINE_AA)
    cv2.putText(canvas, "Pixel Intensity (0 - 255)", (pad_left + int(plot_w / 2) - 60, height - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (71, 85, 105), 1, cv2.LINE_AA)

    # Y Axis Labels (Peak Count)
    y_label_top = f"Log({max_count:,})" if log_scale else f"{max_count:,}"
    cv2.putText(canvas, y_label_top, (8, pad_top + 12), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (100, 116, 139), 1, cv2.LINE_AA)
    cv2.putText(canvas, "0", (35, pad_top + plot_h), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (100, 116, 139), 1, cv2.LINE_AA)

    # Header Title Banner
    scale_label = "[LOG SCALE]" if log_scale else "[LINEAR SCALE]"
    cdf_label = "[CDF OVERLAY]" if show_cdf else ""
    title = f"HISTOGRAM ANALYZER  •  {hist_data.source_label}  •  {mode_clean.upper()} MODE  {scale_label} {cdf_label}"
    cv2.putText(canvas, title, (pad_left, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (15, 23, 42), 1, cv2.LINE_AA)

    return canvas
