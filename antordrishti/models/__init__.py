"""
Antordrishti — Models Package
Data models for cases, documents, analyses, findings, and evidence.
"""

from models.case_model import CaseModel
from models.document_model import DocumentModel
from models.analysis_model import AnalysisModel
from models.evidence_model import EvidenceModel
from models.finding_model import FindingModel
from models.ocr_models import (
    ImageQualityReport,
    PreprocessingStep,
    ScriptDetectionResult,
    LanguageCandidate,
    LanguageIdentificationResult,
    OCRPageResult,
    OCRDocumentResult,
)

# Backwards-compatible aliases
Case = CaseModel
Document = DocumentModel
Analysis = AnalysisModel
Evidence = EvidenceModel
EvidenceItem = EvidenceModel
Finding = FindingModel

__all__ = [
    "CaseModel",
    "DocumentModel",
    "AnalysisModel",
    "EvidenceModel",
    "FindingModel",
    "Case",
    "Document",
    "Analysis",
    "Evidence",
    "EvidenceItem",
    "Finding",
    "ImageQualityReport",
    "PreprocessingStep",
    "ScriptDetectionResult",
    "LanguageCandidate",
    "LanguageIdentificationResult",
    "OCRPageResult",
    "OCRDocumentResult",
]
