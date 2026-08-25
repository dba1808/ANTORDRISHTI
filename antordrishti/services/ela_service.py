"""
Antordrishti — Error Level Analysis Service
Basic ELA implementation using Pillow and OpenCV.

NOTE: ELA alone does NOT prove forgery. It is one indicator among many
that should be considered as part of a comprehensive forensic analysis.
"""

import os
import io
import tempfile
import numpy as np
import cv2
from typing import Optional

from PIL import Image


def generate_ela(image_path: str, quality: int = 75,
                 scale: int = 10) -> Optional[np.ndarray]:
    """Generate an Error Level Analysis image.

    Process:
        1. Open original image
        2. Re-save as JPEG at specified quality
        3. Compute absolute pixel-level difference
        4. Scale the difference for visibility

    Args:
        image_path: Path to the original image file.
        quality: JPEG re-save quality (1-100). Lower quality
                 amplifies ELA differences.
        scale: Multiplier for the difference image (1-50).

    Returns:
        ELA result as a BGR numpy array, or None on error.
    """
    try:
        # Open original
        original = Image.open(image_path).convert("RGB")
        original_np = np.array(original)

        # Re-save at specified JPEG quality
        buffer = io.BytesIO()
        original.save(buffer, format="JPEG", quality=quality)
        buffer.seek(0)

        # Open re-saved version
        resaved = Image.open(buffer).convert("RGB")
        resaved_np = np.array(resaved)

        # Compute absolute difference
        diff = cv2.absdiff(original_np, resaved_np)

        # Scale the difference for visibility
        ela = np.clip(diff.astype(np.float32) * scale, 0, 255).astype(np.uint8)

        # Convert RGB to BGR for OpenCV consistency
        ela_bgr = cv2.cvtColor(ela, cv2.COLOR_RGB2BGR)

        return ela_bgr

    except Exception:
        return None


def generate_ela_from_array(image_array: np.ndarray, quality: int = 75,
                            scale: int = 10) -> Optional[np.ndarray]:
    """Generate ELA from a numpy array (BGR format).

    Args:
        image_array: BGR numpy array of the image.
        quality: JPEG re-save quality (1-100).
        scale: Multiplier for the difference image.

    Returns:
        ELA result as a BGR numpy array, or None on error.
    """
    try:
        # Convert BGR to RGB for Pillow
        rgb = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)
        original = Image.fromarray(rgb)

        # Re-save
        buffer = io.BytesIO()
        original.save(buffer, format="JPEG", quality=quality)
        buffer.seek(0)

        resaved = Image.open(buffer).convert("RGB")
        resaved_np = np.array(resaved)
        original_np = np.array(original)

        diff = cv2.absdiff(original_np, resaved_np)
        ela = np.clip(diff.astype(np.float32) * scale, 0, 255).astype(np.uint8)
        ela_bgr = cv2.cvtColor(ela, cv2.COLOR_RGB2BGR)

        return ela_bgr

    except Exception:
        return None
