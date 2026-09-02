"""
Antordrishti — OCR Data Models
Dataclasses for image quality analysis, preprocessing steps,
script detection, language identification, and OCR results.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime


@dataclass
class ImageQualityReport:
    """Result of image quality analysis before OCR."""

    width: int = 0
    height: int = 0
    processed_width: int = 0
    processed_height: int = 0
    dpi_estimate: int = 0
    resolution_rating: str = "Unknown"       # Good / Low / Very Low
    sharpness_score: float = 0.0
    sharpness_rating: str = "Unknown"        # Good / Moderate / Poor
    blur_detected: bool = False
    brightness_mean: float = 0.0
    brightness_rating: str = "Unknown"       # Good / Dark / Bright
    contrast_std: float = 0.0
    contrast_rating: str = "Unknown"         # Good / Moderate / Poor
    noise_level: float = 0.0
    noise_rating: str = "Unknown"            # Low / Moderate / High
    skew_angle: float = 0.0
    orientation_status: str = "Normal"       # Normal / Corrected / Skewed
    background_quality: str = "Unknown"      # Clean / Noisy / Uneven
    text_visibility: str = "Unknown"         # Good / Moderate / Poor
    ocr_readiness: str = "Unknown"           # Good / Needs Enhancement / Poor
    is_handwritten: bool = False
    handwriting_confidence: float = 0.0


@dataclass
class PreprocessingStep:
    """Record of a single preprocessing operation."""

    name: str = ""
    applied: bool = False
    reason: str = ""
    details: str = ""


@dataclass
class WordRegion:
    """Bounding box and confidence for a detected word."""
    region_id: str = ""
    page_number: int = 1
    text: str = ""
    confidence: float = 0.0
    box: Tuple[int, int, int, int] = (0, 0, 0, 0)  # x, y, w, h
    engine: str = ""


@dataclass
class OCRRunRecord:
    """Record of a single OCR execution pass."""
    evidence_id: str = ""
    case_id: str = ""
    engine: str = ""
    language_model: str = ""
    preprocessing_variant: str = ""
    preprocessing_config: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    text: str = ""
    processing_time: float = 0.0
    status: str = ""  # e.g., "Success", "Failed", "Empty"
    started_at: str = ""
    completed_at: str = ""


@dataclass
class ScriptDetectionResult:
    """Result of script (writing system) detection."""

    script: str = "Unknown"
    confidence: float = 0.0
    char_count: int = 0
    alternatives: List[Dict[str, Any]] = field(default_factory=list)
    # Each alternative: {"script": str, "confidence": float}


@dataclass
class LanguageCandidate:
    """A candidate language with its confidence score."""

    language: str = ""
    confidence: float = 0.0
    method: str = ""  # How this candidate was identified


@dataclass
class LanguageIdentificationResult:
    """Result of language identification from OCR text."""

    language: str = "Unknown"
    confidence: float = 0.0
    confidence_level: str = "Unknown"  # High / Medium / Low / Inconclusive
    script: str = "Unknown"
    alternatives: List[LanguageCandidate] = field(default_factory=list)
    ocr_quality: str = "Unknown"       # Good / Moderate / Poor
    method: str = ""                   # How the identification was made
    is_mixed_language: bool = False
    secondary_languages: List[str] = field(default_factory=list)


@dataclass
class OCRPageResult:
    """OCR result for a single page."""

    page_number: int = 1
    text: str = ""  # Main extracted text
    raw_text: str = ""  # Untouched raw text from the engine
    normalized_text: str = ""  # Unicode normalized text
    language_result: Optional[LanguageIdentificationResult] = None
    script_result: Optional[ScriptDetectionResult] = None
    quality_report: Optional[ImageQualityReport] = None
    ocr_confidence: float = 0.0       # Raw OCR engine confidence
    word_count: int = 0
    char_count: int = 0
    ocr_engine_used: str = ""
    ocr_model_used: str = ""
    processing_steps: List[PreprocessingStep] = field(default_factory=list)
    word_regions: List[WordRegion] = field(default_factory=list)
    ocr_runs: List[OCRRunRecord] = field(default_factory=list)
    engine_comparison_results: Dict[str, Any] = field(default_factory=dict)
    ocr_provenance: Dict[str, Any] = field(default_factory=dict)
    is_handwritten: bool = False
    error: str = ""


@dataclass
class OCRDocumentResult:
    """Complete OCR result for an entire document (potentially multi-page)."""

    file_path: str = ""
    file_name: str = ""
    original_sha256: str = ""
    page_results: List[OCRPageResult] = field(default_factory=list)

    # Document-level summaries
    overall_language: str = "Unknown"
    overall_confidence: float = 0.0
    overall_confidence_level: str = "Unknown"
    overall_script: str = "Unknown"
    is_multi_language: bool = False
    detected_languages: List[str] = field(default_factory=list)
    integrity_snapshot: str = ""  # SHA-256 hash of raw OCR text + configuration + evidence ID
    integrity_sha256: str = ""    # New field to match DB properly

    # Aggregates
    total_pages: int = 0
    total_words: int = 0
    total_chars: int = 0
    total_text: str = ""

    # Processing metadata
    processing_time_seconds: float = 0.0
    processing_steps: List[PreprocessingStep] = field(default_factory=list)
    ocr_engine_used: str = ""
    examination_started: str = ""
    examination_completed: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
