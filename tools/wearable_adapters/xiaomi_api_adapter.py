from __future__ import annotations

from typing import Dict

from .base_adapter import BaseWearableAdapter


class XiaomiAPIAdapter(BaseWearableAdapter):
    source_type = "xiaomi_api"

    def import_data(self, path: str) -> Dict:
        return {
            "status": "placeholder",
            "message": "Xiaomi API adapter is reserved. Phase 1 uses local exports only.",
            "records": [],
            "sessions": [],
            "profile": {},
            "sources": [],
        }

    def authenticate(self, credentials: Dict) -> bool:
        return False
