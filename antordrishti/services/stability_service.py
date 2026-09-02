"""
Antordrishti — Stability Service
Computes forensic stability profile by running OCR across multiple image variants.
"""

import logging
from typing import Dict, Any, List

import numpy as np

from engines.ocr_manager import OCRManager
from services.ocr_preprocessing import generate_ocr_variants
from models.ocr_models import ImageQualityReport, OCRRunRecord

logger = logging.getLogger("antordrishti.stability")


def analyze_stability(
    image: np.ndarray,
    quality: ImageQualityReport,
    ocr_manager: OCRManager,
    lang_candidate: str = ""
) -> Dict[str, Any]:
    """Run OCR on original and variants to determine stability profile."""
    variants = generate_ocr_variants(image, quality)
    variants.insert(0, ("ORIGINAL", image))
    
    runs = []
    texts = []
    
    for variant_name, variant_img in variants:
        try:
            if lang_candidate:
                result = ocr_manager.recognize(variant_img, language_name=lang_candidate)
            else:
                result = ocr_manager.recognize_auto(variant_img)
                
            text = result.get("text", "")
            runs.append({
                "variant": variant_name,
                "text": text,
                "confidence": result.get("confidence", 0.0),
                "engine": result.get("engine", "None")
            })
            if text.strip():
                texts.append(text.strip())
        except Exception as e:
            logger.error(f"Stability analysis failed for variant {variant_name}: {e}")
            runs.append({
                "variant": variant_name,
                "text": "",
                "confidence": 0.0,
                "engine": "Error"
            })
            
    if not texts:
        return {
            "stability_score": 0.0,
            "profile": "Unstable (No Text)",
            "runs": runs,
            "agreement": 0.0
        }
        
    # Calculate agreement (Jaccard similarity style approximation)
    if len(texts) == 1:
        return {
            "stability_score": 50.0,
            "profile": "Weak (Only one variant produced text)",
            "runs": runs,
            "agreement": 50.0
        }
        
    base_set = set(texts[0].split())
    if not base_set:
        base_set = set(texts[1].split()) if len(texts) > 1 else set()
        
    total_similarity = 0.0
    valid_comparisons = 0
    
    for t in texts[1:]:
        t_set = set(t.split())
        if not t_set:
            continue
        intersection = len(base_set.intersection(t_set))
        union = len(base_set.union(t_set))
        if union > 0:
            total_similarity += intersection / union
            valid_comparisons += 1
            
    avg_similarity = (total_similarity / valid_comparisons) * 100 if valid_comparisons > 0 else 0.0
    
    if avg_similarity >= 85:
        profile = "Highly Stable"
    elif avg_similarity >= 60:
        profile = "Moderately Stable"
    elif avg_similarity >= 30:
        profile = "Variable"
    else:
        profile = "Highly Unstable"
        
    return {
        "stability_score": avg_similarity,
        "profile": profile,
        "runs": runs,
        "agreement": avg_similarity
    }
