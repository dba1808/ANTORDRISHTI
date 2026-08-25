"""
Antordrishti — UI Pages Package
All 17 forensic workspace pages.
"""

from ui.pages.dashboard import DashboardPage
from ui.pages.document_analysis import DocumentAnalysisPage
from ui.pages.ela import ELAPage
from ui.pages.metadata import MetadataPage
from ui.pages.ocr import OCRPage
from ui.pages.watermark import WatermarkPage
from ui.pages.image_forensics import ImageForensicsPage
from ui.pages.document_forensics import DocumentForensicsPage
from ui.pages.camera_analysis import CameraAnalysisPage
from ui.pages.noise_analysis import NoiseAnalysisPage
from ui.pages.forgery_detection import ForgeryDetectionPage
from ui.pages.illumination import IlluminationPage
from ui.pages.evidence_manager import EvidenceManagerPage
from ui.pages.evidence_fusion import EvidenceFusionPage
from ui.pages.reports import ReportsPage
from ui.pages.batch_processing import BatchProcessingPage
from ui.pages.settings import SettingsPage

__all__ = [
    "DashboardPage",
    "DocumentAnalysisPage",
    "ELAPage",
    "MetadataPage",
    "OCRPage",
    "WatermarkPage",
    "ImageForensicsPage",
    "DocumentForensicsPage",
    "CameraAnalysisPage",
    "NoiseAnalysisPage",
    "ForgeryDetectionPage",
    "IlluminationPage",
    "EvidenceManagerPage",
    "EvidenceFusionPage",
    "ReportsPage",
    "BatchProcessingPage",
    "SettingsPage",
]
