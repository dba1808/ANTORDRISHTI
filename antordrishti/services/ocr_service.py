"""
Antordrishti — OCR Service
High-level OCR pipeline orchestrator with QThread worker for non-blocking UI.
Ties together: image loading → quality analysis → preprocessing →
OCR → script detection → language identification → result assembly.
"""

import os
import time
import logging
from typing import Optional, List, Dict, Any, Tuple

import numpy as np
import cv2

from PyQt5.QtCore import QThread, pyqtSignal

try:
    import pymupdf as fitz  # type: ignore[import-not-found]
except Exception:
    try:
        import fitz  # type: ignore[import-not-found]
    except Exception:
        fitz = None

from PIL import Image

from models.ocr_models import (
    ImageQualityReport,
    PreprocessingStep,
    ScriptDetectionResult,
    LanguageIdentificationResult,
    OCRPageResult,
    OCRDocumentResult,
)
from engines.ocr_manager import get_ocr_manager
from services.ocr_preprocessing import (
    analyze_image_quality,
    preprocess_for_ocr,
    generate_ocr_variants,
)
from services.language_identifier import (
    detect_script,
    identify_language,
    detect_mixed_languages,
)
from services.hash_service import calculate_hashes
from services.file_service import is_supported_image, is_supported_pdf

logger = logging.getLogger("antordrishti.ocr.service")


class OCRWorker(QThread):
    """Background worker for OCR processing.

    Emits real progress signals for each processing stage.
    Does NOT fake a progress bar — emits actual step completions.
    """

    # Signals
    step_started = pyqtSignal(str)            # Step name starting
    step_completed = pyqtSignal(str)          # Step name completed
    quality_ready = pyqtSignal(object)        # ImageQualityReport
    page_result_ready = pyqtSignal(int, object)  # page_num, OCRPageResult
    progress_text = pyqtSignal(str)           # Status message
    finished = pyqtSignal(object)             # OCRDocumentResult
    error = pyqtSignal(str)                   # Error message

    def __init__(self, file_path: str, engine_name: str = "", parent=None):
        super().__init__(parent)
        self._file_path = file_path
        self._engine_name = engine_name
        self._cancelled = False

    def cancel(self):
        """Request cancellation of the processing."""
        self._cancelled = True

    def run(self):
        """Execute the full OCR pipeline."""
        try:
            start_time = time.time()
            result = OCRDocumentResult()
            result.file_path = self._file_path
            result.file_name = os.path.basename(self._file_path)
            
            from datetime import datetime
            result.examination_started = datetime.now().isoformat()

            # ── Step 1: Calculate evidence hash ──────────────
            self.step_started.emit("Calculating evidence hash")
            sha256, _ = calculate_hashes(self._file_path)
            result.original_sha256 = sha256
            self.step_completed.emit("Calculating evidence hash")

            if self._cancelled:
                return

            # ── Step 2: Load document ────────────────────────
            self.step_started.emit("Loading document")
            pages = self._load_pages()
            if not pages:
                self.error.emit("Failed to load document. Unsupported or corrupted file.")
                return
            result.total_pages = len(pages)
            self.step_completed.emit("Loading document")
            self.progress_text.emit(f"Document loaded: {len(pages)} page(s)")

            if self._cancelled:
                return

            # ── Process each page ────────────────────────────
            ocr_manager = get_ocr_manager()
            ocr_manager.initialize()

            if not ocr_manager.has_engines:
                self.error.emit(
                    "No OCR engines available.\n\n"
                    "Please install Tesseract OCR:\n"
                    "  Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki\n"
                    "  Make sure to install Indian language data packs."
                )
                return

            all_steps: List[PreprocessingStep] = []

            for page_idx, page_image in enumerate(pages):
                if self._cancelled:
                    return

                page_num = page_idx + 1
                self.progress_text.emit(
                    f"Processing page {page_num} of {len(pages)}..."
                )

                page_result = self._process_page(
                    page_image, page_num, ocr_manager
                )
                result.page_results.append(page_result)
                all_steps.extend(page_result.processing_steps)

                self.page_result_ready.emit(page_num, page_result)

            # ── Assemble document-level results ──────────────
            self.step_started.emit("Assembling results")
            self._assemble_document_result(result)
            result.processing_steps = all_steps
            result.processing_time_seconds = time.time() - start_time
            
            from datetime import datetime
            result.examination_completed = datetime.now().isoformat()
            
            # Use specific engine name if we captured it
            engine_used = "None"
            if result.page_results and result.page_results[0].ocr_engine_used:
                engine_used = result.page_results[0].ocr_engine_used
            else:
                engine_used = ocr_manager.get_primary_engine().name() if ocr_manager.get_primary_engine() else "None"
            result.ocr_engine_used = engine_used
            
            # Save to Database
            try:
                from services.db_service import get_db
                db = get_db()
                from services.app_state import get_app_state
                ctx = get_app_state().context
                
                evidence_id = ctx.evidence.evidence_id if ctx.has_document and ctx.evidence else None
                case_id = ctx.case.case_id if ctx.has_document and ctx.case else None
                
                if case_id is not None and evidence_id is not None:
                    db.save_ocr_result(case_id, evidence_id, result)
                    db.add_processing_history(case_id, evidence_id, "OCR & Language ID", f"Engine: {engine_used}, Lang: {result.overall_language}")
            except Exception as e:
                logger.error(f"Failed to save OCR result to DB: {e}")
            
            self.step_completed.emit("Assembling results")

            self.finished.emit(result)

        except Exception as e:
            logger.error(f"OCR processing error: {e}", exc_info=True)
            self.error.emit(f"OCR processing failed:\n{str(e)}")

    def _load_pages(self) -> List[np.ndarray]:
        """Load document pages as numpy arrays.

        Images: single page.
        PDFs: render each page at 300 DPI.
        """
        pages: List[np.ndarray] = []

        if is_supported_image(self._file_path):
            try:
                img = cv2.imread(self._file_path, cv2.IMREAD_COLOR)
                if img is not None:
                    pages.append(img)
                else:
                    # Try Pillow fallback
                    pil_img = Image.open(self._file_path).convert("RGB")
                    arr = np.array(pil_img)
                    pages.append(cv2.cvtColor(arr, cv2.COLOR_RGB2BGR))
            except Exception as e:
                logger.error(f"Failed to load image: {e}")

        elif is_supported_pdf(self._file_path):
            if fitz is None:
                logger.error("PyMuPDF not available for PDF processing")
                return pages

            try:
                pdf = fitz.open(self._file_path)
                for page_idx in range(len(pdf)):
                    if self._cancelled:
                        pdf.close()
                        return pages

                    page = pdf[page_idx]
                    # Render at 300 DPI for OCR quality
                    zoom = 300 / 72  # 72 is default PDF DPI
                    mat = fitz.Matrix(zoom, zoom)
                    pix = page.get_pixmap(matrix=mat, alpha=False)

                    # Convert to numpy array
                    arr = np.frombuffer(pix.samples, dtype=np.uint8)
                    arr = arr.reshape(pix.height, pix.width, 3)
                    # PyMuPDF returns RGB, convert to BGR for OpenCV
                    bgr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
                    pages.append(bgr)

                pdf.close()
            except Exception as e:
                logger.error(f"Failed to load PDF: {e}")

        return pages


    def _process_page(
        self,
        image: np.ndarray,
        page_num: int,
        ocr_manager: Any
    ) -> OCRPageResult:
        page_result = OCRPageResult(page_number=page_num)

        # ── Quality Analysis ─────────────────────────────
        self.step_started.emit("Analyzing image quality")
        quality = analyze_image_quality(image)
        page_result.quality_report = quality
        self.step_completed.emit("Analyzing image quality")

        if self._cancelled:
            return page_result

        # ── Preprocessing ────────────────────────────────
        self.step_started.emit("Preprocessing image")
        processed, steps = preprocess_for_ocr(image, quality)
        page_result.processed_image = processed
        page_result.processing_steps = steps
        self.step_completed.emit("Preprocessing image")

        if self._cancelled:
            return page_result

        # ── Script Detection & Candidate Generation ──────
        self.step_started.emit("Detecting script")
        
        # 1. Broad Pass to get script evidence
        broad_result = ocr_manager.recognize_auto(processed, script_hint="")
        broad_text = broad_result.get("text", "")
        
        # Detect script from broad text
        script_result = detect_script(broad_text)
        
        # If it fell back to English/Latin but it's an Indian app context, 
        # we still try to generate major Indian candidates if quality is bad.
        detected_script = script_result.script
        
        from services.language_identifier import SCRIPT_TO_LANGUAGES
        candidates = SCRIPT_TO_LANGUAGES.get(detected_script, [])
        
        if detected_script == "Latin" and broad_result.get("confidence", 0) < 60:
             # Assume Latin is a failure of default OCR. Try major Indian scripts, but also re-evaluate English individually.
             candidates = ["English", "Bengali", "Hindi", "Marathi", "Tamil", "Telugu", "Gujarati", "Malayalam", "Kannada", "Odia", "Punjabi", "Urdu", "Assamese"]
             script_result.script = "Unknown / Evaluating"
             
        if not candidates:
             candidates = ["English"]
             
        page_result.script_result = script_result
        self.step_completed.emit("Detecting script")
        
        if self._cancelled:
            return page_result

        # ── Multilingual OCR Evaluation ──────────────────
        self.step_started.emit("Running OCR")
        
        best_ocr_result = broad_result
        best_lang_candidate = "English" if detected_script == "Latin" else candidates[0]
        best_score = broad_result.get("confidence", 0)
        
        eval_results = {}
        ocr_runs = []
        
        if len(candidates) > 1 or detected_script == "Unknown / Evaluating":
            for candidate in candidates:
                if self._cancelled: break
                
                # Use dual engine (Tesseract + Paddle)
                cand_results = ocr_manager.run_dual_engine(processed, language_name=candidate)
                
                for cand_result in cand_results:
                    conf = cand_result.get("confidence", 0)
                    text_len = len(cand_result.get("text", "").strip())
                    score = conf if text_len > 3 else conf * 0.5
                    
                    engine_name = cand_result.get("engine", "None")
                    from models.ocr_models import OCRRunRecord
                    import time
                    ocr_runs.append(OCRRunRecord(
                        engine=engine_name,
                        language_model=candidate,
                        preprocessing_variant="Standard",
                        confidence=conf,
                        text=cand_result.get("text", ""),
                        status="Success" if text_len > 0 else "Empty"
                    ))
                    
                    if score > best_score:
                        best_score = score
                        best_ocr_result = cand_result
                        best_lang_candidate = candidate
                    
        if quality.ocr_readiness == "Poor" and best_score < 50:
             variant_result, runs = self._run_multi_variant_ocr(image, processed, quality, ocr_manager, best_lang_candidate)
             ocr_runs.extend(runs)
             if variant_result.get("confidence", 0) > best_score:
                 best_ocr_result = variant_result
                 
        ocr_result = best_ocr_result
        
        if ocr_result.get("error"):
            page_result.error = ocr_result["error"]
            logger.warning(f"OCR error on page {page_num}: {ocr_result['error']}")

        import unicodedata
        raw_text = ocr_result.get("text", "")
        norm_text = unicodedata.normalize("NFC", raw_text)
        
        page_result.text = norm_text
        page_result.raw_text = raw_text
        page_result.normalized_text = norm_text
        page_result.ocr_confidence = ocr_result.get("confidence", 0.0)
        page_result.ocr_engine_used = ocr_result.get("engine", "Unknown")
        page_result.ocr_model_used = ocr_result.get("lang_code", "")
        page_result.word_count = len(page_result.text.split()) if page_result.text else 0
        page_result.char_count = len(page_result.text) if page_result.text else 0
        
        from models.ocr_models import WordRegion
        word_regions_dicts = ocr_result.get("word_regions", [])
        word_regions = [WordRegion(text=r["text"], confidence=r["confidence"], box=r["box"], engine=r["engine"]) for r in word_regions_dicts]
        page_result.word_regions = word_regions
        
        page_result.ocr_runs = ocr_runs
        
        if ocr_runs:
            consensus_result = ocr_manager.calculate_consensus([{"text": r.text, "confidence": r.confidence} for r in ocr_runs])
            page_result.engine_comparison_results = consensus_result
            
        page_result.ocr_provenance = {
            "engine": page_result.ocr_engine_used,
            "model": page_result.ocr_model_used,
            "resolution": f"{quality.processed_width}x{quality.processed_height}" if hasattr(quality, "processed_width") else "Unknown",
            "preprocessing": [s.name for s in steps if s.applied],
        }
        
        self.step_completed.emit("Running OCR")

        if self._cancelled:
            return page_result

        # ── Language Identification ──────────────────────
        self.step_started.emit("Identifying language")
        
        # Re-detect script on best OCR text
        final_script_result = detect_script(page_result.text)
        if final_script_result.script != "Unknown":
            page_result.script_result = final_script_result
            
        lang_result = identify_language(page_result.text, page_result.script_result)
        
        # Override with our evaluated candidate if language identifier failed to find one
        if lang_result.language == "Unknown" and best_lang_candidate != "English":
            lang_result.language = best_lang_candidate + " (Candidate)"
            lang_result.method = "Multilingual Evaluation Pass"
            lang_result.confidence = page_result.ocr_confidence
            
        # Set OCR quality based on confidence
        if page_result.ocr_confidence >= 70:
            lang_result.ocr_quality = "Good"
        elif page_result.ocr_confidence >= 40:
            lang_result.ocr_quality = "Moderate"
        else:
            lang_result.ocr_quality = "Poor"

        if quality.is_handwritten:
            lang_result.method += " (handwritten document detected)"

        page_result.language_result = lang_result
        self.step_completed.emit("Identifying language")

        # ── Validation ───────────────────────────────────
        self.step_started.emit("Validating result")
        self._validate_result(page_result)
        self.step_completed.emit("Validating result")

        return page_result


    def _run_multi_variant_ocr(
        self,
        original: np.ndarray,
        preprocessed: np.ndarray,
        quality: ImageQualityReport,
        ocr_manager: Any,
        lang_candidate: str = ""
    ) -> Tuple[Dict[str, Any], List[Any]]:
        """Try multiple preprocessing variants and collect OCR runs."""
        import time
        from models.ocr_models import OCRRunRecord
        variants = generate_ocr_variants(original, quality)
        variants.insert(0, ("Adaptive", preprocessed))
        
        runs = []
        raw_results = []
        best_result = None
        best_confidence = -1.0
        
        for variant_name, variant_img in variants:
            if self._cancelled: break
            start_t = time.time()
            if lang_candidate:
                result = ocr_manager.recognize(variant_img, language_name=lang_candidate)
            else:
                result = ocr_manager.recognize_auto(variant_img, script_hint="")
            proc_time = time.time() - start_t
            
            conf = result.get("confidence", 0.0)
            text = result.get("text", "")
            engine = result.get("engine", "None")
            model = result.get("lang_code", "")
            
            run = OCRRunRecord(
                engine=engine,
                language_model=model,
                preprocessing_variant=variant_name,
                confidence=conf,
                text=text,
                processing_time=proc_time,
                status="Success" if text else "Empty"
            )
            runs.append(run)
            raw_results.append(result)
            
            text_score = min(1.0, len(text.strip()) / 50.0) * 20
            effective_score = conf + text_score
            if effective_score > best_confidence:
                best_confidence = effective_score
                best_result = result
                
        if not best_result:
            best_result = {"text": "", "confidence": 0.0, "word_confidences": [], "engine": "None", "lang_code": "", "error": "All variants failed"}
            
        return best_result, runs

    def _validate_result(self, page_result: OCRPageResult) -> None:
        """Validate and sanity-check the OCR and language results."""
        lang = page_result.language_result
        if lang is None:
            return

        # If very little text was extracted, lower confidence
        if page_result.char_count < 10:
            lang.confidence = min(lang.confidence, 30.0)
            lang.confidence_level = "Inconclusive"
            if not lang.method.endswith("(insufficient text)"):
                lang.method += " (insufficient text)"

        # If OCR confidence is very low, mark language as uncertain
        if page_result.ocr_confidence < 35:
            lang.confidence = min(lang.confidence, page_result.ocr_confidence)
            lang.confidence_level = "Inconclusive"
            lang.ocr_quality = "Poor"
            if "Candidate" in lang.language:
                lang.language = lang.language.replace(" (Candidate)", "") + " (Candidate) / Inconclusive"
            if not "(poor OCR)" in lang.method:
                lang.method += " (poor OCR)"
        elif page_result.ocr_confidence < 50:
            lang.confidence = min(lang.confidence, 40.0)
            lang.confidence_level = _get_confidence_level_from_value(lang.confidence)
            lang.ocr_quality = "Poor"

    def _assemble_document_result(self, result: OCRDocumentResult) -> None:
        """Compute document-level summaries from page results."""
        if not result.page_results:
            return

        # Aggregate text
        texts = []
        total_words = 0
        total_chars = 0

        for pr in result.page_results:
            if pr.text:
                texts.append(pr.text)
            total_words += pr.word_count
            total_chars += pr.char_count

        result.total_text = "\n\n--- Page Break ---\n\n".join(texts)
        result.total_words = total_words
        result.total_chars = total_chars

        # Determine overall language
        lang_votes: Dict[str, List[float]] = {}
        script_votes: Dict[str, int] = {}

        for pr in result.page_results:
            if pr.language_result and pr.language_result.language != "Unknown":
                lang = pr.language_result.language
                conf = pr.language_result.confidence
                if lang not in lang_votes:
                    lang_votes[lang] = []
                lang_votes[lang].append(conf)

            if pr.script_result and pr.script_result.script != "Unknown":
                script = pr.script_result.script
                script_votes[script] = script_votes.get(script, 0) + 1

        if lang_votes:
            # Pick language with highest average confidence × page count
            best_lang = max(
                lang_votes.keys(),
                key=lambda l: sum(lang_votes[l]) / len(lang_votes[l]) * len(lang_votes[l])
            )
            confs = lang_votes[best_lang]
            result.overall_language = best_lang
            result.overall_confidence = round(sum(confs) / len(confs), 1)
            result.overall_confidence_level = _get_confidence_level_from_value(
                result.overall_confidence
            )

            # Check for multi-language
            result.detected_languages = list(lang_votes.keys())
            if len(lang_votes) > 1:
                result.is_multi_language = True
        else:
            result.overall_language = "Unknown"
            result.overall_confidence = 0.0
            result.overall_confidence_level = "Inconclusive"

        # Overall script
        if script_votes:
            result.overall_script = max(script_votes.keys(),
                                        key=lambda s: script_votes[s])

        import hashlib
        # Integrity snapshot must include hashes of text + config for forensic tracking
        snapshot_data = result.total_text + result.original_sha256 + result.ocr_engine_used
        result.integrity_sha256 = hashlib.sha256(snapshot_data.encode('utf-8')).hexdigest()
        result.integrity_snapshot = result.integrity_sha256


def _get_confidence_level_from_value(confidence: float) -> str:
    """Map numeric confidence to categorical level."""
    if confidence >= 85:
        return "High"
    elif confidence >= 60:
        return "Medium"
    elif confidence >= 30:
        return "Low"
    else:
        return "Inconclusive"


def export_ocr_result_text(result: OCRDocumentResult, output_path: str) -> bool:
    """Export OCR text to a file.

    Args:
        result: The OCR document result.
        output_path: Path for the output file.

    Returns:
        True on success, False on failure.
    """
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"{'='*60}\n")
            f.write(f"ANTORDRISHTI — OCR & Language Identification Report\n")
            f.write(f"{'='*60}\n\n")
            f.write(f"File: {result.file_name}\n")
            f.write(f"Date: {result.timestamp}\n")
            f.write(f"SHA-256: {result.original_sha256}\n\n")
            f.write(f"{'─'*60}\n")
            f.write(f"LANGUAGE IDENTIFICATION\n")
            f.write(f"{'─'*60}\n\n")
            f.write(f"Language: {result.overall_language}\n")
            f.write(f"Confidence: {result.overall_confidence}%\n")
            f.write(f"Assessment: {result.overall_confidence_level}\n")
            f.write(f"Script: {result.overall_script}\n")
            f.write(f"Pages: {result.total_pages}\n")
            f.write(f"Words: {result.total_words}\n")
            f.write(f"Characters: {result.total_chars}\n")
            f.write(f"Processing Time: {result.processing_time_seconds:.1f}s\n")
            f.write(f"OCR Engine: {result.ocr_engine_used}\n")

            if result.is_multi_language:
                f.write(f"\nMultiple languages detected: {', '.join(result.detected_languages)}\n")

            # Per-page details
            if len(result.page_results) > 1:
                f.write(f"\n{'─'*60}\n")
                f.write(f"PER-PAGE RESULTS\n")
                f.write(f"{'─'*60}\n\n")
                for pr in result.page_results:
                    lang = pr.language_result
                    lang_name = lang.language if lang else "Unknown"
                    lang_conf = lang.confidence if lang else 0.0
                    f.write(f"Page {pr.page_number}: {lang_name} — {lang_conf}%\n")

            # Processing steps
            f.write(f"\n{'─'*60}\n")
            f.write(f"PROCESSING STEPS\n")
            f.write(f"{'─'*60}\n\n")
            for step in result.processing_steps:
                status = "✓" if step.applied else "—"
                f.write(f"{status} {step.name}: {step.reason}\n")

            # Extracted text
            f.write(f"\n{'─'*60}\n")
            f.write(f"EXTRACTED TEXT\n")
            f.write(f"{'─'*60}\n\n")
            f.write(result.total_text or "(No text extracted)")
            f.write("\n")

        return True
    except Exception as e:
        logger.error(f"Failed to export OCR result: {e}")
        return False


def export_ocr_result_json(result: OCRDocumentResult, output_path: str) -> bool:
    """Export OCR result as JSON for programmatic use."""
    import json

    try:
        data = {
            "file_name": result.file_name,
            "file_path": result.file_path,
            "sha256": result.original_sha256,
            "timestamp": result.timestamp,
            "language": result.overall_language,
            "confidence": result.overall_confidence,
            "confidence_level": result.overall_confidence_level,
            "script": result.overall_script,
            "is_multi_language": result.is_multi_language,
            "detected_languages": result.detected_languages,
            "total_pages": result.total_pages,
            "total_words": result.total_words,
            "total_chars": result.total_chars,
            "processing_time_seconds": result.processing_time_seconds,
            "ocr_engine": result.ocr_engine_used,
            "pages": [],
            "text": result.total_text,
        }

        for pr in result.page_results:
            page_data: Dict[str, Any] = {
                "page": pr.page_number,
                "text": pr.text,
                "word_count": pr.word_count,
                "char_count": pr.char_count,
                "ocr_confidence": pr.ocr_confidence,
                "is_handwritten": pr.is_handwritten,
            }
            if pr.language_result:
                page_data["language"] = pr.language_result.language
                page_data["language_confidence"] = pr.language_result.confidence
                page_data["language_level"] = pr.language_result.confidence_level
            if pr.script_result:
                page_data["script"] = pr.script_result.script
                page_data["script_confidence"] = pr.script_result.confidence
            data["pages"].append(page_data)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return True
    except Exception as e:
        logger.error(f"Failed to export OCR result as JSON: {e}")
        return False
