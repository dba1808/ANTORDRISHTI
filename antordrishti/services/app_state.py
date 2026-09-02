"""
Antordrishti — Shared Application State
Central current case/evidence/document context for all workspaces.
"""

from dataclasses import dataclass
from typing import Optional

from PyQt5.QtCore import QObject, pyqtSignal

from models.case_model import CaseModel
from models.document_model import DocumentModel
from models.evidence_model import EvidenceModel


@dataclass
class CurrentDocumentContext:
    """The active forensic context shared by viewer, OCR, metadata, and tools."""

    case: Optional[CaseModel] = None
    evidence: Optional[EvidenceModel] = None
    document: Optional[DocumentModel] = None
    current_page: int = 1

    @property
    def has_document(self) -> bool:
        return self.document is not None and bool(self.document.file_path)


class ApplicationState(QObject):
    """QObject-backed singleton state manager with update signals."""

    context_changed = pyqtSignal(object)
    document_cleared = pyqtSignal()
    page_changed = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self._context = CurrentDocumentContext()

    @property
    def context(self) -> CurrentDocumentContext:
        return self._context

    def set_current_context(
        self,
        case: Optional[CaseModel],
        evidence: Optional[EvidenceModel],
        document: Optional[DocumentModel],
    ) -> None:
        self._context = CurrentDocumentContext(case, evidence, document, 1)
        self.context_changed.emit(self._context)

    def set_current_page(self, page_number: int) -> None:
        if self._context.current_page != page_number:
            self._context.current_page = page_number
            self.page_changed.emit(page_number)

    def clear_document(self, keep_case: bool = True) -> None:
        case = self._context.case if keep_case else None
        self._context = CurrentDocumentContext(case=case, current_page=1)
        self.document_cleared.emit()
        self.context_changed.emit(self._context)


_app_state: Optional[ApplicationState] = None


def get_app_state() -> ApplicationState:
    """Return the shared application state singleton."""
    global _app_state
    if _app_state is None:
        _app_state = ApplicationState()
    return _app_state
