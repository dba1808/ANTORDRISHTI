"""
Antordrishti — OCR Manager
Central orchestrator for OCR engines. Selects the best available engine
for each language, manages fallback, and provides a unified interface.
"""

import logging
from typing import Dict, List, Optional, Any, Type

import numpy as np

from engines.ocr_engine_base import OCREngineBase
from engines.tesseract_engine import (
    TesseractEngine,
    INDIAN_LANGUAGE_TO_TESS_CODE,
    DEVANAGARI_FALLBACK_LANGUAGES,
)
from engines.paddle_engine import PaddleOCREngine

logger = logging.getLogger("antordrishti.ocr.manager")


# ── All 22 scheduled Indian languages ────────────────────────────
ALL_INDIAN_LANGUAGES: Dict[str, Dict[str, str]] = {
    "Assamese":    {"script": "Bengali",       "family": "Indo-Aryan"},
    "Bengali":     {"script": "Bengali",       "family": "Indo-Aryan"},
    "Bodo":        {"script": "Devanagari",    "family": "Sino-Tibetan"},
    "Dogri":       {"script": "Devanagari",    "family": "Indo-Aryan"},
    "Gujarati":    {"script": "Gujarati",      "family": "Indo-Aryan"},
    "Hindi":       {"script": "Devanagari",    "family": "Indo-Aryan"},
    "Kannada":     {"script": "Kannada",       "family": "Dravidian"},
    "Kashmiri":    {"script": "Perso-Arabic",  "family": "Indo-Aryan"},
    "Konkani":     {"script": "Devanagari",    "family": "Indo-Aryan"},
    "Maithili":    {"script": "Devanagari",    "family": "Indo-Aryan"},
    "Malayalam":   {"script": "Malayalam",     "family": "Dravidian"},
    "Manipuri":    {"script": "Meitei Mayek",  "family": "Sino-Tibetan"},
    "Marathi":     {"script": "Devanagari",    "family": "Indo-Aryan"},
    "Nepali":      {"script": "Devanagari",    "family": "Indo-Aryan"},
    "Odia":        {"script": "Odia",          "family": "Indo-Aryan"},
    "Punjabi":     {"script": "Gurmukhi",      "family": "Indo-Aryan"},
    "Sanskrit":    {"script": "Devanagari",    "family": "Indo-Aryan"},
    "Santali":     {"script": "Ol Chiki",      "family": "Austroasiatic"},
    "Sindhi":      {"script": "Perso-Arabic",  "family": "Indo-Aryan"},
    "Tamil":       {"script": "Tamil",         "family": "Dravidian"},
    "Telugu":      {"script": "Telugu",        "family": "Dravidian"},
    "Urdu":        {"script": "Perso-Arabic",  "family": "Indo-Aryan"},
}


class OCRManager:
    """Manages OCR engine registration, selection, and execution.

    Designed to support multiple engines. Currently ships with Tesseract;
    PaddleOCR and other engines can be added by registering them.
    """

    def __init__(self):
        self._engines: List[OCREngineBase] = []
        self._initialized = False

    def initialize(self) -> None:
        """Discover and register available OCR engines."""
        if self._initialized:
            return
        self._initialized = True

        # Register Tesseract (always try)
        try:
            tess = TesseractEngine()
            if tess.is_available():
                self._engines.append(tess)
                logger.info(f"Registered: {tess.get_status_message()}")
            else:
                logger.warning("Tesseract OCR not available")
        except Exception as e:
            logger.error(f"Failed to initialize Tesseract: {e}")

        # Register PaddleOCR when the optional package is present. The heavy
        # model itself is still initialized lazily by the engine.
        try:
            paddle = PaddleOCREngine()
            if paddle.is_available():
                self._engines.append(paddle)
                logger.info(f"Registered: {paddle.get_status_message()}")
            else:
                logger.warning("PaddleOCR package not available")
        except Exception as e:
            logger.error(f"Failed to initialize PaddleOCR: {e}")

        if not self._engines:
            logger.warning("No OCR engines available")

    def register_engine(self, engine: OCREngineBase) -> None:
        """Register an additional OCR engine."""
        if engine.is_available():
            self._engines.append(engine)
            logger.info(f"Registered engine: {engine.name()}")

    @property
    def available_engines(self) -> List[OCREngineBase]:
        """List of registered and available engines."""
        self.initialize()
        return list(self._engines)

    @property
    def has_engines(self) -> bool:
        self.initialize()
        return len(self._engines) > 0

    def get_primary_engine(self) -> Optional[OCREngineBase]:
        """Return the primary (first available) engine."""
        self.initialize()
        return self._engines[0] if self._engines else None

    def get_engine_for_language(self, language_name: str) -> Optional[OCREngineBase]:
        """Select the best engine for a given language.

        Tries engines in registration order — first engine that supports
        the language wins.
        """
        self.initialize()

        # Get Tesseract code for the language
        tess_code = INDIAN_LANGUAGE_TO_TESS_CODE.get(language_name)
        fallback_code = DEVANAGARI_FALLBACK_LANGUAGES.get(language_name)

        for engine in self._engines:
            if isinstance(engine, TesseractEngine):
                if tess_code and engine.supports_language(tess_code):
                    return engine
                if fallback_code and engine.supports_language(fallback_code):
                    return engine
            elif isinstance(engine, PaddleOCREngine):
                if engine.verify_language_support(language_name):
                    return engine
            else:
                # Generic check for other engines
                supported = engine.supported_languages()
                if language_name.lower() in [v.lower() for v in supported.values()]:
                    return engine

        return None

    def get_tess_code(self, language_name: str) -> Optional[str]:
        """Get the Tesseract language code for an Indian language."""
        code = INDIAN_LANGUAGE_TO_TESS_CODE.get(language_name)
        if code:
            return code
        return DEVANAGARI_FALLBACK_LANGUAGES.get(language_name)

    def get_supported_languages(self) -> Dict[str, Dict[str, Any]]:
        """Return all 22 Indian languages with their support status.

        Returns dict: {language_name: {"supported": bool, "engine": str,
                       "script": str, "model_type": "direct"|"fallback"|"none"}}
        """
        self.initialize()
        result: Dict[str, Dict[str, Any]] = {}

        for lang_name, info in ALL_INDIAN_LANGUAGES.items():
            entry: Dict[str, Any] = {
                "supported": False,
                "engine": "",
                "script": info["script"],
                "family": info["family"],
                "model_type": "none",
            }

            engine = self.get_engine_for_language(lang_name)
            if engine:
                entry["supported"] = True
                entry["engine"] = engine.name()
                if lang_name in INDIAN_LANGUAGE_TO_TESS_CODE:
                    entry["model_type"] = "direct"
                elif lang_name in DEVANAGARI_FALLBACK_LANGUAGES:
                    entry["model_type"] = "fallback"
                else:
                    entry["model_type"] = "direct" # PaddleOCR

            result[lang_name] = entry

        return result

    def run_dual_engine(self, image: np.ndarray, language_name: str = "", config: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Run OCR using both Tesseract and PaddleOCR if available for the given language."""
        self.initialize()
        results = []
        
        # Get Tesseract code for the language
        tess_code = INDIAN_LANGUAGE_TO_TESS_CODE.get(language_name)
        fallback_code = DEVANAGARI_FALLBACK_LANGUAGES.get(language_name)

        tesseract = None
        paddle = None
        
        for engine in self._engines:
            if isinstance(engine, TesseractEngine):
                if tess_code and engine.supports_language(tess_code):
                    tesseract = engine
                elif fallback_code and engine.supports_language(fallback_code):
                    tesseract = engine
            elif isinstance(engine, PaddleOCREngine):
                if engine.verify_language_support(language_name):
                    paddle = engine
                    
        # If no explicit engine found for language, try to get primary engine
        if not tesseract and not paddle:
            primary = self.get_primary_engine()
            if primary:
                if isinstance(primary, TesseractEngine):
                    tesseract = primary
                elif isinstance(primary, PaddleOCREngine):
                    paddle = primary
                    
        if tesseract:
            lang = tess_code or fallback_code or ""
            res = tesseract.recognize(image, lang_code=lang, config=config)
            if res and res.get("text"):
                results.append(res)
                
        if paddle:
            # paddle maps language_name internally in its recognize method
            res = paddle.recognize(image, lang_code=language_name, config=config)
            if res and res.get("text"):
                results.append(res)
                
        if not results:
            # Return empty result with primary engine name for UI fallback
            return [{
                "text": "",
                "confidence": 0.0,
                "word_confidences": [],
                "engine": self.get_primary_engine().name() if self.get_primary_engine() else "None",
                "lang_code": language_name,
                "error": "No text detected by any engine.",
            }]
            
        return results

    def recognize(self, image: np.ndarray, language_name: str = "",
                  config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Run OCR using the best available engine for the given language.

        If language_name is empty, uses the primary engine with auto-detect.
        """
        self.initialize()

        if not self._engines:
            return {
                "text": "",
                "confidence": 0.0,
                "word_confidences": [],
                "engine": "None",
                "lang_code": "",
                "error": "No OCR engines available. Please install Tesseract OCR.",
            }

        # Determine engine and language code
        engine = None
        lang_code = ""

        if language_name:
            engine = self.get_engine_for_language(language_name)
            if engine and isinstance(engine, TesseractEngine):
                lang_code = engine.get_tess_code_for_language(language_name) or ""
        else:
            engine = self.get_primary_engine()

        if engine is None:
            engine = self.get_primary_engine()

        if engine is None:
            return {
                "text": "",
                "confidence": 0.0,
                "word_confidences": [],
                "engine": "None",
                "lang_code": "",
                "error": "No suitable OCR engine found for this language.",
            }

        return engine.recognize(image, lang_code=lang_code, config=config)

    def recognize_auto(self, image: np.ndarray,
                       script_hint: str = "") -> Dict[str, Any]:
        """Run OCR with auto language detection based on script hint.

        Maps script to likely languages and tries multi-language OCR.
        """
        self.initialize()
        engine = self.get_primary_engine()
        if engine is None:
            return {
                "text": "",
                "confidence": 0.0,
                "word_confidences": [],
                "engine": "None",
                "lang_code": "",
                "error": "No OCR engines available.",
            }

        # Map script hint to Tesseract codes
        script_to_codes: Dict[str, List[str]] = {
            "Bengali":      ["ben", "asm"],
            "Devanagari":   ["hin", "mar", "san", "nep"],
            "Gujarati":     ["guj"],
            "Gurmukhi":     ["pan"],
            "Kannada":      ["kan"],
            "Malayalam":    ["mal"],
            "Odia":         ["ori"],
            "Tamil":        ["tam"],
            "Telugu":       ["tel"],
            "Perso-Arabic": ["urd", "snd"],
            "Meitei Mayek": ["mni"],
            "Ol Chiki":     ["sat"],
        }

        if script_hint and script_hint in script_to_codes:
            codes = script_to_codes[script_hint]
            if isinstance(engine, TesseractEngine):
                return engine.recognize_multi_lang(image, codes)

        # No hint — run a broad pass to gather script evidence
        if isinstance(engine, TesseractEngine):
            # Try to run with some major script representatives to grab characters
            broad_langs = [c for c in ["hin", "ben", "tam", "tel", "kan", "mal", "guj", "pan", "ori", "eng"] if c in engine._installed_langs]
            if broad_langs:
                return engine.recognize_multi_lang(image, broad_langs)
        return engine.recognize(image, lang_code="", config=None)

    def get_status_summary(self) -> str:
        """Return a human-readable summary of OCR engine status."""
        self.initialize()
        if not self._engines:
            return "No OCR engines available. Install Tesseract OCR to enable text extraction."

        lines = []
        for eng in self._engines:
            lines.append(eng.get_status_message())
        return "\n".join(lines)

    def detect_garbage_ocr(self, text: str, expected_script: str, confidence: float, symbol_ratio_threshold: float = 0.4) -> bool:
        """Detect if the OCR output is likely garbage."""
        if not text.strip():
            return True
            
        if confidence > 0 and confidence < 15.0:
            return True
            
        import string
        import unicodedata
        
        chars = len(text)
        symbols = sum(1 for c in text if c in string.punctuation)
        if chars > 0 and (symbols / chars) > symbol_ratio_threshold:
            return True
            
        script_map = {
            "Devanagari": "DEVANAGARI",
            "Bengali": "BENGALI",
            "Gujarati": "GUJARATI",
            "Gurmukhi": "GURMUKHI",
            "Kannada": "KANNADA",
            "Malayalam": "MALAYALAM",
            "Odia": "ORIYA",
            "Tamil": "TAMIL",
            "Telugu": "TELUGU",
        }
        expected_block = script_map.get(expected_script, "")
        if expected_block:
            script_chars = 0
            letters = 0
            for c in text:
                if c.isalpha():
                    letters += 1
                    try:
                        if expected_block in unicodedata.name(c):
                            script_chars += 1
                    except ValueError:
                        pass
            if letters > 5 and script_chars < (letters * 0.1):
                return True

        return False

    def calculate_consensus(self, runs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compare multiple OCR runs and calculate consensus."""
        if not runs:
            return {"overall_confidence": 0.0, "agreement_level": "None", "overlap_score": 0.0}
            
        texts = [r.get("text", "").strip() for r in runs if r.get("text", "").strip()]
        if not texts:
            return {"overall_confidence": 0.0, "agreement_level": "Low", "overlap_score": 0.0}
            
        if len(texts) == 1:
            return {"overall_confidence": runs[0].get("confidence", 0.0), "agreement_level": "N/A (Single Run)", "overlap_score": 1.0}
            
        t1 = set(texts[0].split())
        t2 = set(texts[1].split())
        
        if not t1 or not t2:
            avg_conf = sum(r.get("confidence", 0.0) for r in runs) / len(runs)
            return {"overall_confidence": avg_conf, "agreement_level": "Low", "overlap_score": 0.0}
            
        overlap = len(t1.intersection(t2)) / max(len(t1), len(t2))
        
        if overlap > 0.8:
            agreement = "High"
        elif overlap > 0.4:
            agreement = "Medium"
        else:
            agreement = "Low"
            
        avg_conf = sum(r.get("confidence", 0.0) for r in runs) / len(runs)
        return {
            "overall_confidence": avg_conf,
            "agreement_level": agreement,
            "overlap_score": overlap
        }


# ── Module-level singleton ─────────────────────────────────────
_ocr_manager: Optional[OCRManager] = None


def get_ocr_manager() -> OCRManager:
    """Get or create the singleton OCR manager."""
    global _ocr_manager
    if _ocr_manager is None:
        _ocr_manager = OCRManager()
    return _ocr_manager
