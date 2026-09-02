"""
Antordrishti — Language Identifier Service
Script detection via Unicode analysis and language identification
for the 22 scheduled Indian languages.

IMPORTANT: Script ≠ Language. Multiple Indian languages share the same script.
This module distinguishes between script identification (Unicode block analysis)
and language identification (word-level statistical analysis).
"""

import logging
import re
import unicodedata
from collections import Counter
from typing import Dict, List, Optional, Tuple

from models.ocr_models import (
    ScriptDetectionResult,
    LanguageIdentificationResult,
    LanguageCandidate,
)

logger = logging.getLogger("antordrishti.ocr.language")


# ═══════════════════════════════════════════════════════════════════
# UNICODE BLOCK → SCRIPT MAPPING
# ═══════════════════════════════════════════════════════════════════

# Each entry: (start, end, script_name)
UNICODE_SCRIPT_BLOCKS: List[Tuple[int, int, str]] = [
    (0x0900, 0x097F, "Devanagari"),
    (0x0980, 0x09FF, "Bengali"),
    (0x0A00, 0x0A7F, "Gurmukhi"),
    (0x0A80, 0x0AFF, "Gujarati"),
    (0x0B00, 0x0B7F, "Odia"),
    (0x0B80, 0x0BFF, "Tamil"),
    (0x0C00, 0x0C7F, "Telugu"),
    (0x0C80, 0x0CFF, "Kannada"),
    (0x0D00, 0x0D7F, "Malayalam"),
    (0x0600, 0x06FF, "Perso-Arabic"),
    (0x0750, 0x077F, "Perso-Arabic"),    # Arabic Supplement
    (0xFB50, 0xFDFF, "Perso-Arabic"),    # Arabic Presentation A
    (0xFE70, 0xFEFF, "Perso-Arabic"),    # Arabic Presentation B
    (0xABC0, 0xABFF, "Meitei Mayek"),
    (0xAAE0, 0xAAFF, "Meitei Mayek"),    # Meitei Mayek Extensions
    (0x1C50, 0x1C7F, "Ol Chiki"),
    (0x0000, 0x007F, "Latin"),           # Basic Latin (English)
    (0x0080, 0x00FF, "Latin"),           # Latin-1 Supplement
    (0x0100, 0x024F, "Latin"),           # Latin Extended A+B
]

# Script → Possible languages mapping
SCRIPT_TO_LANGUAGES: Dict[str, List[str]] = {
    "Devanagari":   ["Hindi", "Marathi", "Sanskrit", "Nepali", "Konkani",
                     "Maithili", "Bodo", "Dogri"],
    "Bengali":      ["Bengali", "Assamese"],
    "Gurmukhi":     ["Punjabi"],
    "Gujarati":     ["Gujarati"],
    "Odia":         ["Odia"],
    "Tamil":        ["Tamil"],
    "Telugu":       ["Telugu"],
    "Kannada":      ["Kannada"],
    "Malayalam":    ["Malayalam"],
    "Perso-Arabic": ["Urdu", "Kashmiri", "Sindhi"],
    "Meitei Mayek": ["Manipuri"],
    "Ol Chiki":     ["Santali"],
    "Latin":        ["English"],
}


# ═══════════════════════════════════════════════════════════════════
# LANGUAGE-SPECIFIC WORD MARKERS
# ═══════════════════════════════════════════════════════════════════
# High-frequency function words, postpositions, and conjunctions
# that help distinguish languages sharing the same script.

# Devanagari-family discriminators
HINDI_MARKERS = {
    "है", "हैं", "था", "थे", "थी", "का", "के", "की", "में", "से",
    "को", "पर", "और", "एक", "यह", "वह", "इस", "उस", "कि", "जो",
    "ने", "नहीं", "हो", "कर", "तो", "अपने", "सकता", "होता", "करता",
    "भी", "जब", "तक", "या", "लेकिन", "मगर", "अगर", "क्योंकि",
    "उनका", "उनकी", "उनके", "हमारा", "उसका", "उसकी", "यहाँ", "वहाँ",
}

MARATHI_MARKERS = {
    "आहे", "आहेत", "होता", "होती", "होते", "चा", "ची", "चे", "ला",
    "ना", "मध्ये", "वर", "आणि", "एक", "हा", "ही", "हे", "या", "त्या",
    "केला", "केली", "केले", "करतो", "करते", "नाही", "असे", "पण",
    "म्हणून", "किंवा", "परंतु", "तर", "जर", "कारण", "त्यांचा",
    "आमचा", "त्यांना", "यांना", "सुद्धा", "म्हणजे",
}

SANSKRIT_MARKERS = {
    "अस्ति", "भवति", "तस्य", "तस्याः", "तेषाम्", "एषः", "एषा",
    "यस्य", "यत्", "इति", "एव", "अपि", "तथा", "यथा", "किम्",
    "कथम्", "अत्र", "तत्र", "सर्वे", "सर्वम्", "च", "वा", "तु",
    "हि", "नाम", "देवः", "श्री", "ॐ", "धर्म", "कर्म", "अर्थ",
}

NEPALI_MARKERS = {
    "छ", "छन्", "थियो", "थिए", "थिइन्", "को", "का", "की", "मा",
    "बाट", "लाई", "र", "एउटा", "यो", "त्यो", "यस", "उस", "कि",
    "जो", "ले", "छैन", "हुन्छ", "गर्छ", "त", "आफ्नो", "सक्छ",
    "हुन्छ", "गर्छ", "पनि", "जब", "सम्म", "वा", "तर", "यदि",
    "किनभने", "उनीहरूको", "हाम्रो", "गरे", "भने",
}

KONKANI_MARKERS = {
    "आसा", "आसात", "केलो", "केली", "केलें", "चो", "ची", "चें",
    "क", "ल", "मदें", "आनी", "एक", "हो", "ही", "हें", "त्या",
    "ना", "करता", "करतात", "ना", "पूण", "म्हणून", "वा", "जर",
}

MAITHILI_MARKERS = {
    "अछि", "छल", "छली", "छलाह", "के", "मे", "सँ", "आ", "एक",
    "ई", "ओ", "ओकर", "जे", "नहि", "भेल", "करैत", "रहल",
    "सेहो", "जखन", "तक", "वा", "मुदा", "अगर", "कारण",
}

# Bengali vs Assamese discriminators
BENGALI_MARKERS = {
    "হয়", "হচ্ছে", "ছিল", "ছিলেন", "এর", "তার", "যার", "এটি",
    "সেটি", "করা", "হওয়া", "থাকা", "এবং", "একটি", "তিনি", "আমি",
    "তুমি", "সে", "যে", "কিন্তু", "তবে", "কারণ", "যদি", "অথবা",
    "নয়", "নেই", "আছে", "দিয়ে", "থেকে", "জন্য", "পরে", "আগে",
    "ওপরে", "নীচে", "ভালো", "মন্দ",
}

ASSAMESE_MARKERS = {
    "হয়", "হৈছে", "আছিল", "আছিলে", "ৰ", "তাৰ", "যাৰ", "এইটো",
    "সেইটো", "কৰা", "হোৱা", "থকা", "আৰু", "এটা", "তেওঁ", "মই",
    "তুমি", "সি", "যি", "কিন্তু", "তথাপি", "কাৰণ", "যদি", "অথবা",
    "নহয়", "নাই", "আছে", "দি", "ৰ পৰা", "বাবে", "পিছত", "আগত",
}

# Perso-Arabic family discriminators
URDU_MARKERS = {
    "ہے", "ہیں", "تھا", "تھی", "تھے", "کا", "کے", "کی", "میں",
    "سے", "کو", "پر", "اور", "ایک", "یہ", "وہ", "اس", "جو",
    "نے", "نہیں", "ہو", "کر", "تو", "اپنے", "سکتا", "بھی", "لیکن",
}

KASHMIRI_MARKERS = {
    "چھُ", "آسِ", "کَرُن", "تہِ", "مَنز", "سُنز", "پَنَنِس",
    "یِتھ", "تِتھ", "مگر", "اگر",
}

SINDHI_MARKERS = {
    "آهي", "آهن", "هو", "هئي", "هئا", "جو", "جي", "۾", "مان",
    "تي", "هن", "هنن", "ڪري", "ٿي", "اهو", "۽", "پر", "جيڪو",
}


# ═══════════════════════════════════════════════════════════════════
# SCRIPT DETECTION
# ═══════════════════════════════════════════════════════════════════


def detect_script(text: str) -> ScriptDetectionResult:
    """Detect the writing script(s) used in the given text.

    Uses Unicode block analysis to classify characters.
    This is an intermediate step — script ≠ language.

    Args:
        text: OCR-extracted text string.

    Returns:
        ScriptDetectionResult with primary script and alternatives.
    """
    result = ScriptDetectionResult()

    if not text or not text.strip():
        result.script = "Unknown"
        result.confidence = 0.0
        return result

    # Count characters per script
    script_counts: Counter = Counter()
    total_script_chars = 0

    for char in text:
        cp = ord(char)

        # Skip whitespace, digits, punctuation
        if char.isspace() or char.isdigit():
            continue
        category = unicodedata.category(char)
        if category.startswith("P") or category.startswith("S"):
            continue

        for start, end, script_name in UNICODE_SCRIPT_BLOCKS:
            if start <= cp <= end:
                script_counts[script_name] += 1
                total_script_chars += 1
                break

    result.char_count = total_script_chars

    if total_script_chars == 0:
        result.script = "Unknown"
        result.confidence = 0.0
        return result

    # Sort by frequency
    sorted_scripts = script_counts.most_common()

    # Primary script
    primary_script, primary_count = sorted_scripts[0]
    primary_confidence = primary_count / total_script_chars

    # Skip Latin if it's secondary (mixed Indian + English docs)
    if primary_script == "Latin" and len(sorted_scripts) > 1:
        second_script, second_count = sorted_scripts[1]
        second_confidence = second_count / total_script_chars
        if second_confidence > 0.15:  # Significant presence of non-Latin
            primary_script = second_script
            primary_count = second_count
            primary_confidence = second_confidence

    result.script = primary_script
    result.confidence = round(primary_confidence * 100, 1)

    # Build alternatives
    for script_name, count in sorted_scripts:
        if script_name != primary_script:
            conf = round((count / total_script_chars) * 100, 1)
            if conf >= 1.0:
                result.alternatives.append({
                    "script": script_name,
                    "confidence": conf,
                })

    return result


# ═══════════════════════════════════════════════════════════════════
# LANGUAGE IDENTIFICATION
# ═══════════════════════════════════════════════════════════════════


def identify_language(
    text: str,
    script_result: ScriptDetectionResult,
) -> LanguageIdentificationResult:
    """Identify the specific Indian language from OCR text.

    For unique-script languages, script directly determines language.
    For shared-script languages (Devanagari, Bengali, Perso-Arabic),
    uses word-level statistical analysis to distinguish.

    Args:
        text: OCR-extracted text.
        script_result: Previously detected script.

    Returns:
        LanguageIdentificationResult with language, confidence, alternatives.
    """
    result = LanguageIdentificationResult()
    result.script = script_result.script

    if not text or not text.strip():
        result.language = "Unknown"
        result.confidence = 0.0
        result.confidence_level = "Inconclusive"
        result.method = "No text available"
        return result

    script = script_result.script
    possible_languages = SCRIPT_TO_LANGUAGES.get(script, [])

    if not possible_languages:
        result.language = "Unknown"
        result.confidence = 0.0
        result.confidence_level = "Inconclusive"
        result.method = f"Unknown script: {script}"
        return result

    # ── Unique-script languages: script = language ───────
    if len(possible_languages) == 1:
        result.language = possible_languages[0]
        # Confidence is based on script detection confidence
        result.confidence = min(99.0, script_result.confidence)
        result.confidence_level = _get_confidence_level(result.confidence)
        result.method = "Unique script identification"
        result.ocr_quality = "Good" if result.confidence > 80 else "Moderate"
        return result

    # ── Shared-script languages: need word-level analysis ───
    if script == "Devanagari":
        return _identify_devanagari_language(text, script_result)
    elif script == "Bengali":
        return _identify_bengali_assamese(text, script_result)
    elif script == "Perso-Arabic":
        return _identify_perso_arabic_language(text, script_result)
    else:
        # Fallback: first language for the script
        result.language = possible_languages[0]
        result.confidence = min(80.0, script_result.confidence * 0.8)
        result.confidence_level = _get_confidence_level(result.confidence)
        result.method = "Script-based default"
        return result


def _identify_devanagari_language(
    text: str,
    script_result: ScriptDetectionResult,
) -> LanguageIdentificationResult:
    """Distinguish among Devanagari-script languages using word markers."""
    result = LanguageIdentificationResult()
    result.script = "Devanagari"

    words = _extract_words(text)

    if not words:
        result.language = "Hindi"  # Most common Devanagari language
        result.confidence = 30.0
        result.confidence_level = "Low"
        result.method = "Default (insufficient text)"
        return result

    # Score each language by marker word matches
    scores: Dict[str, float] = {}

    lang_markers = {
        "Hindi": HINDI_MARKERS,
        "Marathi": MARATHI_MARKERS,
        "Sanskrit": SANSKRIT_MARKERS,
        "Nepali": NEPALI_MARKERS,
        "Konkani": KONKANI_MARKERS,
        "Maithili": MAITHILI_MARKERS,
    }

    total_words = len(words)
    word_set = set(words)

    for lang_name, markers in lang_markers.items():
        matches = word_set.intersection(markers)
        # Count frequency of matches in text
        match_count = sum(1 for w in words if w in markers)
        if total_words > 0:
            frequency_score = match_count / total_words
            coverage_score = len(matches) / max(1, len(markers))
            scores[lang_name] = (frequency_score * 0.7 + coverage_score * 0.3) * 100
        else:
            scores[lang_name] = 0.0

    # Also try langdetect as a secondary signal
    langdetect_result = _try_langdetect(text)
    if langdetect_result:
        ld_lang, ld_conf = langdetect_result
        mapped = _map_langdetect_to_indian(ld_lang)
        if mapped and mapped in scores:
            # Boost the langdetect result
            scores[mapped] += ld_conf * 30

    # Find winner
    if scores:
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        best_lang, best_score = sorted_scores[0]

        # Normalize confidence
        total_score = sum(s for _, s in sorted_scores) or 1.0
        confidence = min(99.0, (best_score / total_score) * 100)

        # If scores are too close, lower confidence
        if len(sorted_scores) > 1:
            second_score = sorted_scores[1][1]
            if best_score > 0 and second_score / best_score > 0.7:
                confidence *= 0.7  # Ambiguous result

        result.language = best_lang
        result.confidence = round(confidence, 1)
        result.confidence_level = _get_confidence_level(confidence)
        result.method = "Word marker analysis + statistical"

        # Add alternatives
        for lang_name, score in sorted_scores[1:4]:
            if score > 0:
                alt_conf = round(min(99.0, (score / total_score) * 100), 1)
                result.alternatives.append(LanguageCandidate(
                    language=lang_name,
                    confidence=alt_conf,
                    method="Word marker analysis",
                ))
    else:
        result.language = "Hindi"
        result.confidence = 30.0
        result.confidence_level = "Low"
        result.method = "Default (no marker matches)"

    # Check for mixed language (English + Devanagari)
    if script_result.alternatives:
        for alt in script_result.alternatives:
            if alt.get("script") == "Latin" and alt.get("confidence", 0) > 10:
                result.is_mixed_language = True
                result.secondary_languages = ["English"]

    return result


def _identify_bengali_assamese(
    text: str,
    script_result: ScriptDetectionResult,
) -> LanguageIdentificationResult:
    """Distinguish Bengali from Assamese.

    Key differentiator: Assamese uses 'ৰ' (U+09F0) and 'ৱ' (U+09F1)
    which Bengali does not. Also uses different function words.
    """
    result = LanguageIdentificationResult()
    result.script = "Bengali"

    words = _extract_words(text)

    # Check for Assamese-specific characters
    assamese_chars = sum(1 for c in text if c in ("ৰ", "ৱ"))
    total_script_chars = sum(1 for c in text if 0x0980 <= ord(c) <= 0x09FF)

    # Word marker analysis
    bengali_score = 0
    assamese_score = 0

    word_set = set(words)
    for w in words:
        if w in BENGALI_MARKERS:
            bengali_score += 1
        if w in ASSAMESE_MARKERS:
            assamese_score += 1

    # Assamese-specific characters are a strong signal
    if total_script_chars > 0:
        assamese_char_ratio = assamese_chars / total_script_chars
        if assamese_char_ratio > 0.01:  # Even a few ৰ/ৱ chars signal Assamese
            assamese_score += 20

    total = bengali_score + assamese_score
    if total > 0:
        if assamese_score > bengali_score:
            result.language = "Assamese"
            result.confidence = round(min(99.0, (assamese_score / total) * 100), 1)
            result.alternatives.append(LanguageCandidate(
                language="Bengali",
                confidence=round((bengali_score / total) * 100, 1),
                method="Word marker analysis",
            ))
        else:
            result.language = "Bengali"
            result.confidence = round(min(99.0, (bengali_score / total) * 100), 1)
            result.alternatives.append(LanguageCandidate(
                language="Assamese",
                confidence=round((assamese_score / total) * 100, 1),
                method="Word marker analysis",
            ))
    else:
        # Default to Bengali (more common)
        result.language = "Bengali"
        result.confidence = 60.0

    # Apply langdetect as secondary signal
    langdetect_result = _try_langdetect(text)
    if langdetect_result:
        ld_lang, ld_conf = langdetect_result
        if ld_lang == "bn":
            result.confidence = min(99.0, result.confidence + ld_conf * 10)
        elif ld_lang == "as":
            if result.language == "Assamese":
                result.confidence = min(99.0, result.confidence + ld_conf * 10)
            else:
                result.language = "Assamese"
                result.confidence = 65.0

    result.confidence_level = _get_confidence_level(result.confidence)
    result.method = "Character analysis + word markers"

    return result


def _identify_perso_arabic_language(
    text: str,
    script_result: ScriptDetectionResult,
) -> LanguageIdentificationResult:
    """Distinguish Urdu, Kashmiri, and Sindhi in Perso-Arabic script."""
    result = LanguageIdentificationResult()
    result.script = "Perso-Arabic"

    words = _extract_words(text)
    word_set = set(words)

    # Score by markers
    urdu_score = sum(1 for w in words if w in URDU_MARKERS)
    kashmiri_score = sum(1 for w in words if w in KASHMIRI_MARKERS)
    sindhi_score = sum(1 for w in words if w in SINDHI_MARKERS)

    # Sindhi-specific characters: ڪ ڳ ڱ ڻ ٺ ٽ ٿ
    sindhi_chars = sum(1 for c in text if c in "ڪڳڱڻٺٽٿ")
    if sindhi_chars > 3:
        sindhi_score += 20

    total = urdu_score + kashmiri_score + sindhi_score
    if total > 0:
        scores = {
            "Urdu": urdu_score,
            "Kashmiri": kashmiri_score,
            "Sindhi": sindhi_score,
        }
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        best_lang, best_score = sorted_scores[0]
        result.language = best_lang
        result.confidence = round(min(99.0, (best_score / total) * 100), 1)

        for lang_name, score in sorted_scores[1:]:
            if score > 0:
                result.alternatives.append(LanguageCandidate(
                    language=lang_name,
                    confidence=round((score / total) * 100, 1),
                    method="Word marker analysis",
                ))
    else:
        result.language = "Urdu"  # Most common Perso-Arabic Indian language
        result.confidence = 50.0

    result.confidence_level = _get_confidence_level(result.confidence)
    result.method = "Character + word marker analysis"

    return result


# ═══════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════


def _extract_words(text: str) -> List[str]:
    """Extract words from text, handling various scripts."""
    # Split on whitespace and common punctuation
    tokens = re.split(r'[\s।॥,.!?;:\-—–\u200c\u200d]+', text)
    return [t.strip() for t in tokens if t.strip() and len(t.strip()) >= 1]


def _get_confidence_level(confidence: float) -> str:
    """Map numeric confidence to categorical level."""
    if confidence >= 85:
        return "High"
    elif confidence >= 60:
        return "Medium"
    elif confidence >= 30:
        return "Low"
    else:
        return "Inconclusive"


def _try_langdetect(text: str) -> Optional[Tuple[str, float]]:
    """Try langdetect library as a secondary signal.

    Returns (iso_code, probability) or None.
    """
    try:
        from langdetect import detect_langs
        results = detect_langs(text)
        if results:
            top = results[0]
            return (str(top.lang), float(top.prob))
    except Exception:
        pass
    return None


def _map_langdetect_to_indian(iso_code: str) -> Optional[str]:
    """Map langdetect ISO 639-1 code to our Indian language name."""
    mapping = {
        "hi": "Hindi",
        "mr": "Marathi",
        "ne": "Nepali",
        "sa": "Sanskrit",
        "bn": "Bengali",
        "as": "Assamese",
        "gu": "Gujarati",
        "pa": "Punjabi",
        "or": "Odia",
        "ta": "Tamil",
        "te": "Telugu",
        "kn": "Kannada",
        "ml": "Malayalam",
        "ur": "Urdu",
        "sd": "Sindhi",
        "ks": "Kashmiri",
        "en": "English",
    }
    return mapping.get(iso_code)


def detect_mixed_languages(text: str) -> List[str]:
    """Detect if a document contains multiple languages.

    Returns list of detected language names.
    """
    script_result = detect_script(text)
    detected = []

    # Primary language from primary script
    lang_result = identify_language(text, script_result)
    if lang_result.language != "Unknown":
        detected.append(lang_result.language)

    # Check for secondary scripts
    for alt in script_result.alternatives:
        alt_script = alt.get("script", "")
        alt_conf = alt.get("confidence", 0)
        if alt_conf > 5.0 and alt_script in SCRIPT_TO_LANGUAGES:
            # Has significant presence of another script
            alt_languages = SCRIPT_TO_LANGUAGES[alt_script]
            if len(alt_languages) == 1:
                if alt_languages[0] not in detected:
                    detected.append(alt_languages[0])
            elif alt_script == "Latin":
                if "English" not in detected:
                    detected.append("English")

    return detected
