"""
Antordrishti — Base Engine Interface
Abstract base for all forensic analysis engines.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseEngine(ABC):
    """Abstract base class for forensic analysis engines.

    All engines report their connection status. At the UI stage,
    engines return 'not connected' so the UI can display the
    appropriate placeholder state.
    """

    def __init__(self):
        self._connected = False

    @property
    def is_connected(self) -> bool:
        """Whether the engine backend is available."""
        return self._connected

    @property
    def status_message(self) -> str:
        """Human-readable status for display."""
        if self._connected:
            return "Engine connected"
        return "Analysis engine not connected"

    @abstractmethod
    def name(self) -> str:
        """Engine display name."""
        ...

    @abstractmethod
    def run(self, **kwargs) -> Dict[str, Any]:
        """Run analysis. Raises NotImplementedError at UI stage."""
        ...
