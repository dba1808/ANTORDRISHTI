"""
Antordrishti — Analysis Data Model
"""

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class AnalysisModel:
    """Represents an analysis configuration and result stub."""

    analysis_type: str = ""
    status: str = "Not Analysed"
    confidence: float = 0.0
    evidence_strength: str = "N/A"
    parameters: Dict[str, object] = field(default_factory=dict)
    result_summary: str = ""
    is_engine_connected: bool = False
