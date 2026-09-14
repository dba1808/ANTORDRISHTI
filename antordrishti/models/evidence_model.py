"""
Antordrishti — Evidence Data Model
With SQLite serialization and auto-generated evidence IDs.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any


@dataclass
class EvidenceModel:
    """Represents an evidence item linked to a forensic case."""

    evidence_id: str = ""
    case_id: str = ""
    name: str = ""
    evidence_type: str = "Original Evidence"
    source: str = ""
    file_path: str = ""
    sha256: str = ""
    md5: str = ""
    created: Optional[datetime] = None
    status: str = "Pending"
    notes: str = ""
    reviewed: bool = False
    relevant: bool = False

    file_type: str = ""
    file_size: int = 0
    mime_type: str = ""
    page_count: int = 1
    width: int = 0
    height: int = 0
    imported_at: Optional[datetime] = None
    ocr_runs: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self):
        if self.created is None:
            self.created = datetime.now()
        if self.imported_at is None:
            self.imported_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for SQLite storage."""
        return {
            "evidence_id": self.evidence_id,
            "case_id": self.case_id,
            "name": self.name,
            "evidence_type": self.evidence_type,
            "source": self.source,
            "file_path": self.file_path,
            "sha256": self.sha256,
            "md5": self.md5,
            "status": self.status,
            "notes": self.notes,
            "reviewed": self.reviewed,
            "relevant": self.relevant,
            "file_type": self.file_type,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "page_count": self.page_count,
            "width": self.width,
            "height": self.height,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvidenceModel":
        """Deserialize from a SQLite row dictionary."""
        created = None
        imported_at = None
        if data.get("created_at"):
            try:
                created = datetime.fromisoformat(data["created_at"])
            except (ValueError, TypeError):
                pass
        if data.get("imported_at"):
            try:
                imported_at = datetime.fromisoformat(data["imported_at"])
            except (ValueError, TypeError):
                pass

        return cls(
            evidence_id=str(data.get("evidence_id") or ""),
            case_id=str(data.get("case_id") or ""),
            name=str(data.get("name") or ""),
            evidence_type=str(data.get("evidence_type") or "Original Evidence"),
            source=str(data.get("source") or ""),
            file_path=str(data.get("file_path") or ""),
            sha256=str(data.get("sha256") or ""),
            md5=str(data.get("md5") or ""),
            status=str(data.get("status") or "Pending"),
            notes=str(data.get("notes") or ""),
            reviewed=bool(data.get("reviewed", False)),
            relevant=bool(data.get("relevant", False)),
            file_type=str(data.get("file_type") or ""),
            file_size=int(data.get("file_size", 0) or 0),
            mime_type=str(data.get("mime_type") or ""),
            page_count=int(data.get("page_count", 1) or 1),
            width=int(data.get("width", 0) or 0),
            height=int(data.get("height", 0) or 0),
            created=created,
            imported_at=imported_at,
        )
