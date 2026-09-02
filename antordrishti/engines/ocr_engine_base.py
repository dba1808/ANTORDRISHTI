"""
Antordrishti — OCR Engine Base Interface
Abstract base class for all OCR engine implementations.
Engines report their availability and supported languages honestly.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any

import numpy as np


class OCREngineBase(ABC):
    """Abstract base class for OCR engines.

    All concrete engines must:
    - Report which languages they genuinely support
    - Report whether they are installed and available
    - Return honest confidence scores from the actual OCR model
    - Never fabricate support for unsupported languages
    """

    @abstractmethod
    def name(self) -> str:
        """Human-readable engine name."""
        ...

    @abstractmethod
    def version(self) -> str:
        """Engine version string."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Whether the engine is installed and functional."""
        ...

    @abstractmethod
    def supported_languages(self) -> Dict[str, str]:
        """Return dict of {language_code: language_name} for genuinely supported languages.

        Only include languages where the OCR model is actually installed
        and can produce meaningful results.
        """
        ...

    @abstractmethod
    def recognize(self, image: np.ndarray, lang_code: str = "",
                  config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Run OCR on an image.

        Args:
            image: BGR or grayscale numpy array.
            lang_code: Language code hint (engine-specific).
            config: Optional engine-specific configuration.

        Returns:
            Dict containing at minimum:
            - "text": str — extracted text
            - "confidence": float — mean OCR confidence (0.0–100.0)
            - "word_confidences": list — per-word confidence scores
            - "engine": str — engine name
            - "lang_code": str — language code used
            - "error": str — error message if any, empty on success
        """
        ...

    def supports_language(self, lang_code: str) -> bool:
        """Check if a specific language code is supported."""
        return lang_code in self.supported_languages()

    def get_status_message(self) -> str:
        """Human-readable status message."""
        if self.is_available():
            langs = self.supported_languages()
            return f"{self.name()} v{self.version()} — {len(langs)} languages available"
        return f"{self.name()} — not installed or not available"
