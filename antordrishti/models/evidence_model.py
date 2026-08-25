"""
Antordrishti — Evidence Data Model
With SQLite serialization and auto-generated evidence IDs.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any


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

    def __post_init__(self):
        if self.created is None:
            self.created = datetime.now()

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
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvidenceModel":
        """Deserialize from a SQLite row dictionary."""
        created = None
        if data.get("created_at"):
            try:
                created = datetime.fromisoformat(data["created_at"])
            except (ValueError, TypeError):
                pass

        return cls(
            evidence_id=data.get("evidence_id", ""),
            case_id=data.get("case_id", ""),
            name=data.get("name", ""),
            evidence_type=data.get("evidence_type", "Original Evidence"),
            source=data.get("source", ""),
            file_path=data.get("file_path", ""),
            sha256=data.get("sha256", ""),
            md5=data.get("md5", ""),
            status=data.get("status", "Pending"),
            notes=data.get("notes", ""),
            reviewed=bool(data.get("reviewed", False)),
            relevant=bool(data.get("relevant", False)),
            created=created,
        )
