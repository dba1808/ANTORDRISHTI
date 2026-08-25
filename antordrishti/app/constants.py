"""
Antordrishti Application Constants
Enums, status codes, supported formats, version information.
"""

from enum import Enum, auto

# ── Version ──────────────────────────────────────────────────
APP_NAME = "ANTORDRISHTI"
APP_NAME_BENGALI = "অন্তর্দৃষ্টি"
APP_TITLE = "অন্তর্দৃষ্টি | ANTORDRISHTI — Document Forensic & Authenticity Analysis Suite"
APP_SUBTITLE = "Document Forensic & Authenticity Analysis Suite"
APP_VERSION = "1.0.0"
APP_ORGANIZATION = "Antordrishti"
APP_BUILD = "Development Build"
APP_DESCRIPTION = (
    "A Robust Framework for Image Forgery Detection "
    "in Questioned Document Analysis"
)

# ── Supported file formats ───────────────────────────────────
IMAGE_FORMATS = ("*.jpg", "*.jpeg", "*.png", "*.tiff", "*.tif", "*.bmp")
PDF_FORMATS = ("*.pdf",)
ALL_DOCUMENT_FORMATS = IMAGE_FORMATS + PDF_FORMATS
IMAGE_FILTER = "Images (*.jpg *.jpeg *.png *.tiff *.tif *.bmp)"
PDF_FILTER = "PDF Files (*.pdf)"
ALL_FILTER = "All Supported (*.jpg *.jpeg *.png *.tiff *.tif *.bmp *.pdf)"
TIFF_FILTER = "TIFF Files (*.tiff *.tif)"
ANY_FILTER = "All Files (*.*)"

# ── Enums ────────────────────────────────────────────────────

class AppStatus(Enum):
    READY = "Ready"
    LOADING = "Loading"
    DOCUMENT_LOADED = "Document Loaded"
    PROCESSING = "Processing"
    ANALYSIS_PENDING = "Analysis Pending"
    ANALYSIS_COMPLETE = "Analysis Complete"
    WARNING = "Warning"
    ERROR = "Error"


class EvidenceType(Enum):
    ORIGINAL = "Original Evidence"
    WORKING_COPY = "Working Copy"
    PROCESSED = "Processed Result"
    FINDING = "Forensic Finding"


class EvidenceStatus(Enum):
    PENDING = "Pending"
    VERIFIED = "Verified"
    NOT_VERIFIED = "Not Verified"
    REVIEWED = "Reviewed"
    RELEVANT = "Marked Relevant"


class AnalysisStatus(Enum):
    NOT_CONNECTED = "Analysis engine not connected"
    PENDING = "Analysis Pending"
    RUNNING = "Running"
    COMPLETE = "Complete"
    FAILED = "Failed"
    NOT_ANALYSED = "Not Analysed"


class FindingSeverity(Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class IntegrityStatus(Enum):
    VERIFIED = "Verified"
    NOT_VERIFIED = "Not Verified"
    PENDING = "Pending"
    INVALID = "Invalid"


# ── Navigation Pages ────────────────────────────────────────

class NavPage(Enum):
    DASHBOARD = "Dashboard"
    DOCUMENT_ANALYSIS = "Document Analysis"
    IMAGE_FORENSICS = "Image Forensics"
    DOCUMENT_FORENSICS = "Document Forensics"
    ELA = "Error Level Analysis"
    METADATA = "Metadata"
    OCR = "OCR & Text Extraction"
    WATERMARK = "Watermark Detection"
    FORGERY_DETECTION = "Forgery Detection"
    NOISE_ANALYSIS = "Noise Analysis"
    EVIDENCE_MANAGER = "Evidence Manager"
    EVIDENCE_FUSION = "Evidence Fusion"
    REPORT_GENERATOR = "Report Generator"
    BATCH_PROCESSING = "Batch Processing"
    SETTINGS = "Settings"


# ── Analysis Layer Names ────────────────────────────────────

ANALYSIS_LAYERS = [
    "Original Image",
    "Processed Image",
    "OCR Text",
    "ELA",
    "Copy-Move",
    "Splicing",
    "Noise Map",
    "DCT",
    "DWT",
    "FFT",
    "Illumination",
    "Resampling",
    "Forgery Localization",
    "Annotations",
]
