"""
Antordrishti — Finding Data Model
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class FindingModel:
    """Represents a forensic finding."""

    finding_id: str = ""
    module: str = ""
    description: str = ""
    severity: str = "Medium"
    confidence: float = 0.0
    region: str = ""
    examiner_note: str = ""
    timestamp: Optional[datetime] = None
    status: str = "Potential Anomaly"

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
