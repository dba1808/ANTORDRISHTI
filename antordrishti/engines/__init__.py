"""
Antordrishti — Engines Package
Forensic analysis engines, OCR engines, and base interfaces.
"""

from engines.base_engine import BaseEngine
from engines.forgery_engine import (
    ForgeryEngine,
    OCREngine,
    MetadataEngine,
    ReportEngine,
)
from engines.ocr_engine_base import OCREngineBase
from engines.tesseract_engine import TesseractEngine
from engines.ocr_manager import OCRManager, get_ocr_manager

__all__ = [
    "BaseEngine",
    "ForgeryEngine",
    "OCREngine",
    "MetadataEngine",
    "ReportEngine",
    "OCREngineBase",
    "TesseractEngine",
    "OCRManager",
    "get_ocr_manager",
]

