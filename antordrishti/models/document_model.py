"""
Antordrishti — Document Data Model
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any


@dataclass
class DocumentModel:
    """Represents a loaded document with forensic metadata."""

    file_path: str = ""
    file_name: str = ""
    file_type: str = ""
    file_size: int = 0
    mime_type: str = ""
    last_modified: str = ""
    resolution: str = ""
    color_space: str = ""
    page_count: int = 1
    current_page: int = 1
    width: int = 0
    height: int = 0
    dpi: int = 0
    bit_depth: int = 0
    sha256: str = ""
    md5: str = ""
    integrity_status: str = "Pending"
    evidence_type: str = "Original Evidence"
    loaded_at: Optional[datetime] = None

    # Metadata
    author: str = "Not Available"
    creator: str = "Not Available"
    producer: str = "Not Available"
    creation_date: str = "Not Available"
    camera_make: str = "Not Available"
    camera_model: str = "Not Available"
    software: str = "Not Available"
    raw_metadata: Dict[str, Any] = field(default_factory=dict)

    # PDF-specific
    pdf_version: str = ""
    pdf_objects: int = 0
    pdf_streams: int = 0
    pdf_has_trailer: bool = False
    pdf_linearized: bool = False

    def __post_init__(self):
        if self.loaded_at is None:
            self.loaded_at = datetime.now()
