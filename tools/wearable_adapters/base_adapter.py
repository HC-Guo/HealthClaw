from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict


class BaseWearableAdapter(ABC):
    """Base adapter for all wearable data sources."""

    source_type = "unknown"

    @abstractmethod
    def import_data(self, path: str) -> Dict:
        """Read upstream source and normalize it into the shared schema."""

    def authenticate(self, credentials: Dict) -> bool:
        return False

    def fetch_recent_snapshot(self, *args, **kwargs):
        raise NotImplementedError

    def fetch_history(self, *args, **kwargs):
        raise NotImplementedError
