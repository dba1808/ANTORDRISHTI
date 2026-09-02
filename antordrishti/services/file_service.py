"""
Antordrishti — File Service
File I/O, type detection, and utility functions.
"""

import os
import mimetypes
from datetime import datetime
from typing import Optional, Tuple


def get_file_info(file_path: str) -> dict:
    """Return basic file information for the given path."""
    if not os.path.exists(file_path):
        return {}

    stat = os.stat(file_path)
    mime, _ = mimetypes.guess_type(file_path)

    return {
        "file_path": file_path,
        "file_name": os.path.basename(file_path),
        "file_type": os.path.splitext(file_path)[1].upper().lstrip("."),
        "file_size": stat.st_size,
        "mime_type": mime or "Unknown",
        "last_modified": datetime.fromtimestamp(stat.st_mtime).strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
    }


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable form."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def is_supported_image(file_path: str) -> bool:
    """Check if the file is a supported image format."""
    ext = os.path.splitext(file_path)[1].lower()
    return ext in (".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp", ".webp")


def is_supported_pdf(file_path: str) -> bool:
    """Check if the file is a PDF."""
    ext = os.path.splitext(file_path)[1].lower()
    return ext == ".pdf"


def is_supported_document(file_path: str) -> bool:
    """Check if the file is any supported document format."""
    return is_supported_image(file_path) or is_supported_pdf(file_path)
