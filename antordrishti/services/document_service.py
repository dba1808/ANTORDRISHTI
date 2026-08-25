"""
Antordrishti — Document Service
Document loading, rich metadata extraction (EXIF + PDF), hash calculation,
page rendering, and thumbnail generation.
"""

import os
import logging
from typing import Optional, List

from PyQt5.QtGui import QImage
from PyQt5.QtCore import QSize

try:
    import pymupdf as fitz  # type: ignore[import-not-found]
except Exception:
    try:
        import fitz  # type: ignore[import-not-found]
    except Exception:
        fitz = None

from services.file_service import is_supported_image, is_supported_pdf
from services.hash_service import calculate_hashes
from models.document_model import DocumentModel

logger = logging.getLogger("antordrishti")


def load_document(file_path: str) -> Optional[DocumentModel]:
    """Load a document and populate the DocumentModel with metadata and SHA-256."""
    if not os.path.exists(file_path):
        return None

    try:
        from services.file_service import get_file_info
        info = get_file_info(file_path)

        doc = DocumentModel(
            file_path=file_path,
            file_name=info.get("file_name", os.path.basename(file_path)),
            file_type=info.get("file_type", ""),
            file_size=info.get("file_size", 0),
            mime_type=info.get("mime_type", ""),
            last_modified=info.get("last_modified", ""),
        )

        # Calculate integrity hashes automatically
        sha256, md5 = calculate_hashes(file_path)
        doc.sha256 = sha256
        doc.md5 = md5
        doc.integrity_status = "Verified" if sha256 else "Error"

        if is_supported_image(file_path):
            success = _populate_image_info(doc)
            if not success:
                return None
        elif is_supported_pdf(file_path):
            success = _populate_pdf_info(doc)
            if not success:
                return None
        else:
            return None

        return doc
    except Exception as e:
        logger.error(f"Failed to load document '{file_path}': {e}")
        return None


def _populate_image_info(doc: DocumentModel) -> bool:
    """Fill image-specific metadata including EXIF tags."""
    try:
        from PIL import Image, ExifTags
        with Image.open(doc.file_path) as img:
            doc.width, doc.height = img.size
            doc.resolution = f"{doc.width} × {doc.height} px"
            doc.color_space = img.mode or "RGB"
            doc.page_count = getattr(img, "n_frames", 1)
            doc.file_type = (img.format or doc.file_type or "IMAGE").upper()
            dpi_info = img.info.get("dpi")
            if dpi_info:
                doc.dpi = int(dpi_info[0])

            # EXIF extraction
            exif_data = img.getexif()
            if exif_data:
                tag_map = {ExifTags.TAGS.get(k, str(k)): v for k, v in exif_data.items()}
                doc.raw_metadata = {str(k): str(v) for k, v in tag_map.items()}
                doc.camera_make = str(tag_map.get("Make", "Not Available"))
                doc.camera_model = str(tag_map.get("Model", "Not Available"))
                doc.software = str(tag_map.get("Software", "Not Available"))
                doc.creation_date = str(tag_map.get("DateTime", tag_map.get("DateTimeOriginal", doc.last_modified)))
                doc.author = str(tag_map.get("Artist", tag_map.get("Copyright", "Not Available")))
        return True
    except Exception as e:
        logger.warning(f"Pillow failed to read image info for '{doc.file_path}': {e}")
        # Try fallback using QImage
        try:
            qimg = QImage(doc.file_path)
            if not qimg.isNull():
                doc.width = qimg.width()
                doc.height = qimg.height()
                doc.resolution = f"{doc.width} × {doc.height} px"
                doc.color_space = "RGB"
                doc.page_count = 1
                return True
        except Exception:
            pass
        return False


def _populate_pdf_info(doc: DocumentModel) -> bool:
    """Fill PDF-specific metadata via PyMuPDF."""
    if fitz is None:
        logger.error("PyMuPDF (fitz) is not available.")
        return False
    try:
        pdf = fitz.open(doc.file_path)
        doc.page_count = len(pdf)
        meta = pdf.metadata or {}
        doc.raw_metadata = {str(k): str(v) for k, v in meta.items() if v}

        fmt = meta.get("format", "1.7") if meta else "1.7"
        doc.pdf_version = fmt if str(fmt).startswith("PDF") else f"PDF {fmt}"
        doc.file_type = "PDF"
        doc.author = meta.get("author") or "Not Available"
        doc.creator = meta.get("creator") or "Not Available"
        doc.producer = meta.get("producer") or "Not Available"
        doc.software = meta.get("producer") or meta.get("creator") or "Not Available"
        doc.creation_date = meta.get("creationDate") or "Not Available"

        doc.pdf_objects = pdf.xref_length()
        doc.pdf_linearized = bool(pdf.is_fast_webaccess)
        if doc.page_count > 0:
            page = pdf[0]
            rect = page.rect
            doc.width = int(rect.width)
            doc.height = int(rect.height)
            doc.resolution = f"{doc.width} × {doc.height} pt"
            doc.color_space = "RGB (Rendered)"
        pdf.close()
        return True
    except Exception as e:
        logger.error(f"PyMuPDF failed to open PDF '{doc.file_path}': {e}")
        return False


def render_page_image(file_path: str, page_num: int = 0,
                      zoom: float = 1.0) -> Optional[QImage]:
    """Render a document page to QImage."""
    if not os.path.exists(file_path):
        return None

    if is_supported_image(file_path):
        return _render_image(file_path)
    elif is_supported_pdf(file_path):
        return _render_pdf_page(file_path, page_num, zoom)
    return None


def render_thumbnail(file_path: str, page_num: int = 0,
                     thumb_width: int = 120) -> Optional[QImage]:
    """Render a lightweight page thumbnail for the sidebar/filmstrip."""
    if not os.path.exists(file_path):
        return None

    if is_supported_pdf(file_path):
        if fitz is None:
            return None
        try:
            pdf = fitz.open(file_path)
            if page_num < 0 or page_num >= len(pdf):
                pdf.close()
                return None
            page = pdf[page_num]
            rect = page.rect
            scale = thumb_width / max(1.0, rect.width)
            mat = fitz.Matrix(scale, scale)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
            result = img.copy()
            pdf.close()
            return result
        except Exception:
            return None
    elif is_supported_image(file_path):
        img = _render_image(file_path)
        if img:
            return img.scaledToWidth(thumb_width)
    return None


def _render_image(file_path: str) -> Optional[QImage]:
    """Load an image file as QImage."""
    try:
        img = QImage(file_path)
        if img.isNull():
            from PIL import Image
            with Image.open(file_path) as pil_img:
                pil_img = pil_img.convert("RGBA")
                data = pil_img.tobytes("raw", "RGBA")
                return QImage(data, pil_img.size[0], pil_img.size[1], QImage.Format.Format_RGBA8888).copy()
        return img
    except Exception as e:
        logger.error(f"Failed to render image '{file_path}': {e}")
        return None


def _render_pdf_page(file_path: str, page_num: int = 0,
                     zoom: float = 1.0) -> Optional[QImage]:
    """Render a PDF page to QImage via PyMuPDF."""
    if fitz is None:
        return None
    try:
        pdf = fitz.open(file_path)
        if page_num < 0 or page_num >= len(pdf):
            pdf.close()
            return None
        page = pdf[page_num]
        scale = max(1.0, zoom * 2.0)
        mat = fitz.Matrix(scale, scale)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img = QImage(
            pix.samples, pix.width, pix.height,
            pix.stride, QImage.Format.Format_RGB888
        )
        result = img.copy()
        pdf.close()
        return result
    except Exception as e:
        logger.error(f"Failed to render PDF page {page_num} of '{file_path}': {e}")
        return None
