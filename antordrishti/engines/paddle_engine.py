"""
Antordrishti — PaddleOCR Engine
Optional multilingual OCR backend with lazy model initialization.
"""

import logging
import os
from typing import Dict, Optional, Any, List

import numpy as np

# Fix for PaddlePaddle 3.x oneDNN crash on Windows
os.environ["FLAGS_enable_pir_api"] = "0"
os.environ["FLAGS_use_mkldnn"] = "0"

from engines.ocr_engine_base import OCREngineBase

logger = logging.getLogger("antordrishti.ocr.paddle")

try:
    from paddleocr import PaddleOCR  # type: ignore[import-not-found]
except Exception:
    PaddleOCR = None  # type: ignore[assignment]


PADDLE_LANG_MAP = {
    "Hindi": {"script": "Devanagari", "code": "hi"},
    "Marathi": {"script": "Devanagari", "code": "mr"},
    "Nepali": {"script": "Devanagari", "code": "ne"},
    "Sanskrit": {"script": "Devanagari", "code": "sa"},
    "Bhojpuri": {"script": "Devanagari", "code": "bho"},
    "Bengali": {"script": "Bengali", "code": "bn"},
    "Assamese": {"script": "Bengali", "code": "bn"},
    "Gujarati": {"script": "Gujarati", "code": "gu"},
    "Punjabi": {"script": "Gurmukhi", "code": "pa"},
    "Tamil": {"script": "Tamil", "code": "ta"},
    "Telugu": {"script": "Telugu", "code": "te"},
    "Kannada": {"script": "Kannada", "code": "kn"},
    "Malayalam": {"script": "Malayalam", "code": "ml"},
    "Odia": {"script": "Oriya", "code": "or"},
    "Urdu": {"script": "Arabic", "code": "ur"},
    "English": {"script": "Latin", "code": "en"}
}

class PaddleOCREngine(OCREngineBase):
    """PaddleOCR wrapper.

    The package is optional. The heavy OCR model is created only when OCR is
    actually requested so the normal Antordrishti startup path stays quick.
    """

    def __init__(self):
        self._available: Optional[bool] = None
        self._ocr_models = {}
        self._version = "Unknown"
        self._verified_support = {}

    def name(self) -> str:
        return "PaddleOCR"

    def version(self) -> str:
        if PaddleOCR is None:
            return "Unavailable"
        try:
            import paddleocr  # type: ignore[import-not-found]
            return getattr(paddleocr, "__version__", self._version)
        except Exception:
            return self._version

    def is_available(self) -> bool:
        if self._available is None:
            self._available = PaddleOCR is not None
        return bool(self._available)

    def supported_languages(self) -> Dict[str, str]:
        if not self.is_available():
            return {}
        return {k: f"Mapped to {v['code']}" for k, v in PADDLE_LANG_MAP.items()}

    def verify_language_support(self, lang_name: str) -> bool:
        """Verifies actual model availability for a given Antordrishti language."""
        if not self.is_available():
            return False
        if lang_name not in PADDLE_LANG_MAP:
            logger.warning(f"PaddleOCR: Not available for this language/model ({lang_name})")
            return False
            
        paddle_code = PADDLE_LANG_MAP[lang_name]["code"]
        if paddle_code in self._verified_support:
            return self._verified_support[paddle_code]
            
        # Try initializing the model for this code
        try:
            # We don't save it here to save memory, just initialize it once if possible.
            # PaddleOCR handles downloading. If it fails, it raises an exception.
            if PaddleOCR is None:
                return False
            temp_ocr = PaddleOCR(use_angle_cls=False, lang=paddle_code)
            self._verified_support[paddle_code] = True
            return True
        except Exception as e:
            logger.warning(f"PaddleOCR: Not available for {lang_name} ({paddle_code}): {e}")
            self._verified_support[paddle_code] = False
            return False

    def _ensure_model(self, lang_code="en") -> Optional[Any]:
        if not self.is_available():
            return None
            
        if lang_code in self._ocr_models:
            return self._ocr_models[lang_code]

        try:
            if PaddleOCR is None:
                return None
            ocr = PaddleOCR(use_angle_cls=False, lang=lang_code)
            self._ocr_models[lang_code] = ocr
            self._verified_support[lang_code] = True
            return ocr
        except Exception as e:
            logger.warning(f"PaddleOCR model initialization failed for {lang_code}: {e}")
            self._verified_support[lang_code] = False
            return None

    def recognize(self, image: np.ndarray, lang_code: str = "",
                  config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "text": "",
            "confidence": 0.0,
            "word_confidences": [],
            "engine": self.name(),
            "lang_code": lang_code,
            "error": "",
        }
        if not self.is_available():
            result["error"] = "PaddleOCR package is not installed"
            return result

        paddle_code = "en"
        # Map Indian language name to paddle code if possible
        if lang_code and lang_code in PADDLE_LANG_MAP:
            paddle_code = PADDLE_LANG_MAP[lang_code]["code"]
        elif lang_code:
            paddle_code = lang_code 
            
        ocr = self._ensure_model(lang_code=paddle_code)
        if not ocr:
            result["error"] = f"PaddleOCR model unavailable for {lang_code} (code {paddle_code})"
            return result

        try:
            rgb = image
            if len(image.shape) == 3:
                import cv2
                rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

            try:
                raw = ocr.ocr(rgb, cls=False)
            except TypeError:
                raw = ocr.predict(rgb)
                
            lines: List[str] = []
            confidences: List[float] = []
            word_regions: List[Dict[str, Any]] = []

            for page in raw or []:
                for item in page or []:
                    if not item or len(item) < 2:
                        continue
                    box = item[0]
                    text_conf = item[1]
                    if isinstance(text_conf, (list, tuple)) and text_conf:
                        text = str(text_conf[0]).strip()
                        conf = float(text_conf[1]) * 100 if len(text_conf) > 1 else 0.0
                        if text:
                            lines.append(text)
                            confidences.append(conf)
                            
                            if isinstance(box, (list, tuple)) and len(box) == 4:
                                xs = [p[0] for p in box]
                                ys = [p[1] for p in box]
                                x = int(min(xs))
                                y = int(min(ys))
                                w = int(max(xs) - min(xs))
                                h = int(max(ys) - min(ys))
                                word_regions.append({
                                    "text": text,
                                    "confidence": conf,
                                    "box": (x, y, w, h),
                                    "engine": self.name()
                                })

            result["text"] = "\n".join(lines).strip()
            result["word_confidences"] = confidences
            result["word_regions"] = word_regions
            result["confidence"] = sum(confidences) / len(confidences) if confidences else 0.0
        except Exception as e:
            result["error"] = f"PaddleOCR error: {str(e)}"
            logger.error(f"PaddleOCR failed: {e}")

        return result
