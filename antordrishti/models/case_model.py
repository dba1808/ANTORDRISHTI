"""
Antordrishti — Case Data Model
In-memory case data structure with SQLite serialization support.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any

# Indian Standard Time (UTC+05:30)
IST_TZ = timezone(timedelta(hours=5, minutes=30))


@dataclass
class CaseModel:
    """Represents a forensic case."""

    case_id: str = ""
    case_name: str = ""
    title: str = ""
    examiner_name: str = ""
    organization: str = ""
    description: str = ""
    date: str = ""
    reference_number: str = ""
    notes: str = ""
    created: Optional[datetime] = None
    modified: Optional[datetime] = None
    status: str = "OPEN"
    document_ids: List[str] = field(default_factory=list)
    events: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self):
        # Synchronize canonical case_name and legacy title
        if not self.case_name and self.title:
            self.case_name = self.title
        elif not self.title and self.case_name:
            self.title = self.case_name

        if self.created is None:
            self.created = datetime.now(IST_TZ)
        elif self.created.tzinfo is None:
            self.created = self.created.replace(tzinfo=IST_TZ)

        if self.modified is None:
            self.modified = datetime.now(IST_TZ)
        elif self.modified.tzinfo is None:
            self.modified = self.modified.replace(tzinfo=IST_TZ)

        if not self.date:
            self.date = datetime.now(IST_TZ).strftime("%Y-%m-%d")

        # Standardize status to uppercase
        valid_statuses = {"OPEN", "IN PROGRESS", "COMPLETED", "ARCHIVED"}
        curr_status = (self.status or "OPEN").upper()
        if curr_status in valid_statuses:
            self.status = curr_status
        elif curr_status == "OPEN":
            self.status = "OPEN"

    @property
    def case_number(self) -> str:
        """Alias for case_id."""
        return self.case_id

    @property
    def examiner(self) -> str:
        """Alias for examiner_name."""
        return self.examiner_name

    def created_ist_str(self) -> str:
        """Return formatted creation time in IST."""
        if not self.created:
            return ""
        ist_time = self.created.astimezone(IST_TZ)
        return ist_time.strftime("%Y-%m-%d %H:%M:%S IST (UTC+05:30)")

    def modified_ist_str(self) -> str:
        """Return formatted modification time in IST."""
        if not self.modified:
            return ""
        ist_time = self.modified.astimezone(IST_TZ)
        return ist_time.strftime("%Y-%m-%d %H:%M:%S IST (UTC+05:30)")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for SQLite storage."""
        canonical_name = self.case_name or self.title
        return {
            "case_id": self.case_id,
            "case_name": canonical_name,
            "title": canonical_name,
            "examiner": self.examiner_name,
            "examiner_name": self.examiner_name,
            "organization": self.organization,
            "description": self.description,
            "date": self.date,
            "reference_number": self.reference_number,
            "notes": self.notes,
            "status": self.status,
            "created_at": self.created.isoformat() if self.created else "",
            "modified_at": self.modified.isoformat() if self.modified else "",
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

        name = str(data.get("case_name") or data.get("title") or "")
        return cls(
            case_id=str(data.get("case_id") or ""),
            case_name=name,
            title=name,
            examiner_name=str(data.get("examiner") or data.get("examiner_name") or ""),
            organization=str(data.get("organization") or ""),
            description=str(data.get("description") or ""),
            date=str(data.get("date") or ""),
            reference_number=str(data.get("reference_number") or ""),
            notes=str(data.get("notes") or ""),
            status=str(data.get("status") or "OPEN").upper(),
            created=created,
            modified=modified,
        )
