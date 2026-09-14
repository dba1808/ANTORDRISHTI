import os
import json
import logging
from typing import Dict, Any, Tuple, List
from PIL import Image

from services.forensic_metadata_service import (
    examine_evidence_metadata,
    detect_file_signature,
    extract_filesystem_metadata,
    extract_image_exif,
    extract_xmp_metadata,
    extract_iptc_metadata,
    inspect_jpeg_structure,
    inspect_png_structure,
    inspect_tiff_structure,
    inspect_webp_structure,
    inspect_pdf_forensics,
    check_metadata_consistency,
    build_metadata_timeline,
    export_metadata_to_json,
    export_metadata_to_txt,
)

logger = logging.getLogger("antordrishti.metadata")


def sanitize_metadata(file_path: str, output_path: str) -> bool:
    """
    Create a sanitized derivative copy with metadata stripped.
    FORENSIC REQUIREMENT: The original evidence file remains strictly immutable.
    """
    if not os.path.exists(file_path):
        return False
        
    # Prevent accidental overwrite of original evidence
    if os.path.abspath(file_path) == os.path.abspath(output_path):
        logger.error("Refusing to sanitize in-place: original evidence must remain immutable.")
        return False

    try:
        if file_path.lower().endswith('.pdf'):
            try:
                try:
                    import pymupdf as fitz
                except Exception:
                    import fitz  # type: ignore
                doc = fitz.open(file_path)
                doc.set_metadata({})
                doc.save(output_path, garbage=4, clean=True)
                doc.close()
                return True
            except Exception as e:
                logger.error(f"Failed to sanitize PDF: {e}")
                return False
        else:
            with Image.open(file_path) as img:
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                
                # Save without exif or metadata
                data = list(img.getdata())
                image_without_exif = Image.new(img.mode, img.size)
                image_without_exif.putdata(data)
                image_without_exif.save(output_path)
                return True
    except Exception as e:
        logger.error(f"Failed to sanitize {file_path}: {e}")
        return False


def detect_anomalies(doc_model) -> list:
    """Analyze DocumentModel for metadata anomalies using forensic consistency engine."""
    anomalies = []
    
    if not doc_model:
        return anomalies

    # If document has forensic metadata record, use its detected inconsistencies
    if hasattr(doc_model, "metadata_record") and doc_model.metadata_record:
        rec = doc_model.metadata_record
        incons = rec.get("consistency", {}).get("inconsistencies", [])
        for inc in incons:
            anomalies.append({
                "severity": "High" if "FORMAT" in inc.get("reason", "") or "DIMENSION" in inc.get("reason", "") else "Medium",
                "finding": f"{inc.get('field')}: {inc.get('reason')}",
                "tag": inc.get("source", "Metadata")
            })

    # Software check (factual observation)
    software = doc_model.software.lower() if doc_model.software else ""
    editing_tools = ["photoshop", "gimp", "lightroom", "canva", "illustrator", "paint", "snapseed"]
    for tool in editing_tools:
        if tool in software:
            anomalies.append({
                "severity": "Medium",
                "finding": f"Document contains editing tool signature in metadata: {doc_model.software}",
                "tag": "Software"
            })
            break

    # Creator / Producer check in PDF
    if getattr(doc_model, "file_type", "") == "PDF":
        if getattr(doc_model, "creator", "") and getattr(doc_model, "producer", ""):
            if doc_model.creator != "Not Available" and doc_model.creator != doc_model.producer:
                anomalies.append({
                    "severity": "Low",
                    "finding": f"PDF Creator ({doc_model.creator}) and Producer ({doc_model.producer}) differ.",
                    "tag": "Creator/Producer"
                })

    return anomalies
