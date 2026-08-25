"""Stub forgery detection engine — not connected at UI stage."""
from engines.base_engine import BaseEngine
from typing import Any, Dict

class ForgeryEngine(BaseEngine):
    def name(self) -> str:
        return "Forgery Detection Engine"
    def run(self, **kwargs) -> Dict[str, Any]:
        raise NotImplementedError(self.status_message)

class OCREngine(BaseEngine):
    def name(self) -> str:
        return "OCR Engine"
    def run(self, **kwargs) -> Dict[str, Any]:
        raise NotImplementedError(self.status_message)

class MetadataEngine(BaseEngine):
    def name(self) -> str:
        return "Metadata Analysis Engine"
    def run(self, **kwargs) -> Dict[str, Any]:
        raise NotImplementedError(self.status_message)

class ReportEngine(BaseEngine):
    def name(self) -> str:
        return "Report Generation Engine"
    def run(self, **kwargs) -> Dict[str, Any]:
        raise NotImplementedError(self.status_message)
