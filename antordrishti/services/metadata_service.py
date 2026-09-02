import os
import json
import logging
from typing import Dict, Any, Tuple
from PIL import Image

logger = logging.getLogger("antordrishti.metadata")

def sanitize_metadata(file_path: str, output_path: str) -> bool:
    """Create a new file with all metadata stripped."""
    if not os.path.exists(file_path):
        return False
        
    try:
        if file_path.lower().endswith(('.pdf')):
            # PyMuPDF metadata stripping
            try:
                import fitz # type: ignore
                doc = fitz.open(file_path)
                doc.set_metadata({})
                doc.save(output_path, garbage=4, clean=True)
                doc.close()
                return True
            except Exception as e:
                logger.error(f"Failed to sanitize PDF: {e}")
                return False
        else:
            # Image metadata stripping
            with Image.open(file_path) as img:
                # Convert to RGB if needed to save without original format specifics
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
    """Analyze DocumentModel for metadata anomalies."""
    anomalies = []
    
    if not doc_model:
        return anomalies
        
    # Check 1: Software implies editing
    software = doc_model.software.lower() if doc_model.software else ""
    editing_tools = ["photoshop", "gimp", "lightroom", "canva", "illustrator", "paint", "snapseed"]
    for tool in editing_tools:
        if tool in software:
            anomalies.append({
                "severity": "High",
                "finding": f"Document was processed with photo editing software: {doc_model.software}",
                "tag": "Software"
            })
            break
            
    # Check 2: Resolution DPI missing
    if not doc_model.dpi and doc_model.file_type != "PDF":
         anomalies.append({
                "severity": "Low",
                "finding": "Standard DPI information is missing, indicating possible re-encoding or stripping.",
                "tag": "DPI"
         })

    # Check 3: Creator / Producer mismatch in PDF
    if doc_model.file_type == "PDF":
        if doc_model.creator and doc_model.producer and doc_model.creator != "Not Available":
            if doc_model.creator != doc_model.producer:
                anomalies.append({
                    "severity": "Medium",
                    "finding": f"PDF Creator ({doc_model.creator}) and Producer ({doc_model.producer}) differ, which may indicate tampering or re-saving.",
                    "tag": "Creator/Producer"
                })
                
    return anomalies
