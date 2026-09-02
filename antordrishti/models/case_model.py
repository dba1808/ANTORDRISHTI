"""
Antordrishti — Case Data Model
In-memory case data structure with SQLite serialization support.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any


@dataclass
class CaseModel:
    """Represents a forensic case."""

    case_id: str = ""
    title: str = ""
    examiner_name: str = ""
    organization: str = ""
    description: str = ""
    date: str = ""
    reference_number: str = ""
    notes: str = ""
    created: Optional[datetime] = None
    modified: Optional[datetime] = None
    status: str = "Open"
    document_ids: List[str] = field(default_factory=list)
    events: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self):
        if self.created is None:
            self.created = datetime.now()
        if self.modified is None:
            self.modified = datetime.now()
        if not self.date:
            self.date = datetime.now().strftime("%Y-%m-%d")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for SQLite storage."""
        return {
            "case_id": self.case_id,
            "title": self.title,
            "examiner_name": self.examiner_name,
            "organization": self.organization,
            "description": self.description,
            "date": self.date,
            "reference_number": self.reference_number,
            "notes": self.notes,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CaseModel":
        """Deserialize from a SQLite row dictionary."""
        created = None
        modified = None
        if data.get("created_at"):
            try:
                created = datetime.fromisoformat(data["created_at"])
            except (ValueError, TypeError):
                pass
        if data.get("modified_at"):
            try:
                modified = datetime.fromisoformat(data["modified_at"])
            except (ValueError, TypeError):
                pass

        return cls(
            case_id=data.get("case_id", ""),
            title=data.get("title", ""),
            examiner_name=str(data.get("examiner") or data.get("examiner_name") or ""),
            organization=data.get("organization", ""),
            description=data.get("description", ""),
            date=data.get("date", ""),
            reference_number=data.get("reference_number", ""),
            notes=data.get("notes", ""),
            status=data.get("status", "Open"),
            created=created,
            modified=modified,
        )
