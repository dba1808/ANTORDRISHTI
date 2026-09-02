"""
Antordrishti — Tesseract OCR Engine
Concrete OCR engine implementation using pytesseract.
Honestly reports available languages based on installed tessdata models.
"""

import logging
import subprocess
from typing import Dict, List, Optional, Any

import numpy as np

try:
    import pytesseract
except ImportError:
    pytesseract = None  # type: ignore[assignment]

from engines.ocr_engine_base import OCREngineBase

logger = logging.getLogger("antordrishti.ocr.tesseract")

# ── Language mapping: Indian language name → Tesseract code ──────────
# Only maps languages where Tesseract has official tessdata models.
# Languages without a model are intentionally excluded.
INDIAN_LANGUAGE_TO_TESS_CODE: Dict[str, str] = {
    "Assamese": "asm",
    "Bengali": "ben",
    "Gujarati": "guj",
    "Hindi": "hin",
    "Kannada": "kan",
    "Malayalam": "mal",
    "Manipuri": "mni",       # Meitei Mayek script
    "Marathi": "mar",
    "Nepali": "nep",
    "Odia": "ori",
    "Punjabi": "pan",
    "Sanskrit": "san",
    "Santali": "sat",
    "Sindhi": "snd",         # Arabic/Perso-Arabic script
    "Tamil": "tam",
    "Telugu": "tel",
    "Urdu": "urd",
    "English": "eng",
}

# Reverse mapping for result lookup
TESS_CODE_TO_LANGUAGE: Dict[str, str] = {v: k for k, v in INDIAN_LANGUAGE_TO_TESS_CODE.items()}

# Languages that share Devanagari script — Tesseract may use Hindi model as fallback
DEVANAGARI_FALLBACK_LANGUAGES: Dict[str, str] = {
    "Konkani": "hin",     # No dedicated Tesseract model; use Hindi/Devanagari
    "Maithili": "hin",
    "Bodo": "hin",
    "Dogri": "hin",
}


class TesseractEngine(OCREngineBase):
    """Tesseract OCR engine via pytesseract.

    Auto-detects installation and installed language models.
    Only reports languages whose tessdata files are actually present.
    """

    def __init__(self):
        self._available: Optional[bool] = None
        self._version_str: str = ""
        self._installed_langs: List[str] = []
        self._checked = False

    def _check_availability(self) -> None:
        """Probe Tesseract installation (lazy, one-time)."""
        if self._checked:
            return
        self._checked = True

        if pytesseract is None:
            self._available = False
            logger.warning("pytesseract package not installed")
            return

        try:
            try:
                from PyQt5.QtCore import QSettings
                configured = QSettings("Antordrishti", "Antordrishti").value("ocr/tesseract_path", "")
                if configured:
                    pytesseract.pytesseract.tesseract_cmd = str(configured)
            except Exception:
                pass

            ver = pytesseract.get_tesseract_version()
            self._version_str = str(ver)
            self._available = True
        except Exception:
            # Try common Windows paths
            for path in [
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            ]:
                try:
                    pytesseract.pytesseract.tesseract_cmd = path
                    ver = pytesseract.get_tesseract_version()
                    self._version_str = str(ver)
                    self._available = True
                    break
                except Exception:
                    continue

            if not self._available:
                self._available = False
                logger.warning("Tesseract OCR not found on this system")
                return

        # Discover installed language packs
        try:
            self._installed_langs = pytesseract.get_languages(config="")
            logger.info(
                f"Tesseract {self._version_str} found with "
                f"{len(self._installed_langs)} language packs"
            )
        except Exception as e:
            logger.warning(f"Could not query Tesseract languages: {e}")
            self._installed_langs = []

    # ── Interface implementation ─────────────────────────────────

    def name(self) -> str:
        return "Tesseract OCR"

    def version(self) -> str:
        self._check_availability()
        return self._version_str or "Unknown"

    def is_available(self) -> bool:
        self._check_availability()
        return bool(self._available)

    def supported_languages(self) -> Dict[str, str]:
        """Return only Indian languages whose tessdata is actually installed."""
        self._check_availability()
        if not self._available:
            return {}

        result: Dict[str, str] = {}

        # Direct-model languages
        for lang_name, tess_code in INDIAN_LANGUAGE_TO_TESS_CODE.items():
            if tess_code in self._installed_langs:
                result[tess_code] = lang_name

        # Fallback languages (Devanagari via Hindi model)
        if "hin" in self._installed_langs:
            for lang_name, fallback_code in DEVANAGARI_FALLBACK_LANGUAGES.items():
                # Use a prefixed code to distinguish
                result[f"hin_as_{lang_name.lower()}"] = f"{lang_name} (via Hindi model)"

        return result

    def get_tess_code_for_language(self, language_name: str) -> Optional[str]:
        """Get the Tesseract language code for a given Indian language name.

        Returns None if unsupported.
        """
        self._check_availability()

        # Direct mapping
        if language_name in INDIAN_LANGUAGE_TO_TESS_CODE:
            code = INDIAN_LANGUAGE_TO_TESS_CODE[language_name]
            if code in self._installed_langs:
                return code

        # Fallback mapping
        if language_name in DEVANAGARI_FALLBACK_LANGUAGES:
            code = DEVANAGARI_FALLBACK_LANGUAGES[language_name]
            if code in self._installed_langs:
                return code

        return None

    def get_installed_indian_languages(self) -> List[str]:
        """Return list of Indian language names with installed models."""
        self._check_availability()
        names = []
        for lang_name, tess_code in INDIAN_LANGUAGE_TO_TESS_CODE.items():
            if tess_code in self._installed_langs:
                names.append(lang_name)
        for lang_name in DEVANAGARI_FALLBACK_LANGUAGES:
            if DEVANAGARI_FALLBACK_LANGUAGES[lang_name] in self._installed_langs:
                names.append(f"{lang_name} (fallback)")
        return names

    def recognize(self, image: np.ndarray, lang_code: str = "",
                  config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Run Tesseract OCR on an image.

        Args:
            image: BGR or grayscale numpy array.
            lang_code: Tesseract language code (e.g., 'ben', 'hin').
                       If empty, uses Tesseract default auto-detect.
            config: Optional dict with keys:
                    - "psm": page segmentation mode (int, default 3)
                    - "oem": OCR engine mode (int, default 3)

        Returns:
            Dict with text, confidence, word_confidences, engine, error.
        """
        self._check_availability()

        result: Dict[str, Any] = {
            "text": "",
            "confidence": 0.0,
            "word_confidences": [],
            "engine": self.name(),
            "lang_code": lang_code,
            "error": "",
        }

        if not self._available:
            result["error"] = "Tesseract OCR is not installed or not available"
            return result

        if pytesseract is None:
            result["error"] = "pytesseract package not installed"
            return result

        # Build config string
        psm = 3
        oem = 3
        if config:
            psm = config.get("psm", 3)
            oem = config.get("oem", 3)

        tess_config = f"--oem {oem} --psm {psm}"

        # Determine language parameter
        lang_param = lang_code if lang_code else None

        # Validate language is installed
        if lang_param:
            langs = lang_param.split("+")
            mapped_langs = []
            for l in langs:
                if l not in self._installed_langs:
                    if l.startswith("hin_as_"):
                        mapped_langs.append("hin")
                    else:
                        result["error"] = (
                            f"Language model '{lang_param}' not installed. "
                            f"Install the tessdata file for this language."
                        )
                        return result
                else:
                    mapped_langs.append(l)
            lang_param = "+".join(mapped_langs)

        try:
            import cv2
            # Ensure image is in correct format for pytesseract
            if len(image.shape) == 3:
                pil_compatible = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            else:
                pil_compatible = image

            # Get full text
            text = pytesseract.image_to_string(
                pil_compatible,
                lang=lang_param,
                config=tess_config,
            )
            result["text"] = text.strip()

            # Get detailed data with confidence scores
            try:
                data = pytesseract.image_to_data(
                    pil_compatible,
                    lang=lang_param,
                    config=tess_config,
                    output_type=pytesseract.Output.DICT,
                )

                word_confs = []
                word_regions = []
                for i, conf in enumerate(data.get("conf", [])):
                    try:
                        c = int(conf)
                    except (ValueError, TypeError):
                        continue
                    word = data.get("text", [""])[i].strip()
                    if c >= 0 and word:
                        word_confs.append(c)
                        x = data.get("left", [])[i] if i < len(data.get("left", [])) else 0
                        y = data.get("top", [])[i] if i < len(data.get("top", [])) else 0
                        w = data.get("width", [])[i] if i < len(data.get("width", [])) else 0
                        h = data.get("height", [])[i] if i < len(data.get("height", [])) else 0
                        word_regions.append({
                            "text": word,
                            "confidence": float(c),
                            "box": (x, y, w, h),
                            "engine": self.name()
                        })

                result["word_confidences"] = word_confs
                result["word_regions"] = word_regions
                if word_confs:
                    result["confidence"] = sum(word_confs) / len(word_confs)
                else:
                    result["confidence"] = 0.0

            except Exception as e:
                logger.warning(f"Could not get per-word confidence: {e}")
                # Still have the text, just no confidence breakdown
                result["confidence"] = 50.0  # Unknown confidence

        except Exception as e:
            result["error"] = f"Tesseract OCR error: {str(e)}"
            logger.error(f"Tesseract OCR failed: {e}")

        return result

    def recognize_multi_lang(self, image: np.ndarray,
                              lang_codes: List[str]) -> Dict[str, Any]:
        """Run Tesseract with multiple language hints (e.g., 'ben+eng').

        Useful for mixed-language documents.
        """
        available = [lc for lc in lang_codes if lc in self._installed_langs]
        if not available:
            return {
                "text": "",
                "confidence": 0.0,
                "word_confidences": [],
                "engine": self.name(),
                "lang_code": "+".join(lang_codes),
                "error": "None of the specified language models are installed",
            }
        combined_lang = "+".join(available)
        return self.recognize(image, lang_code=combined_lang)
