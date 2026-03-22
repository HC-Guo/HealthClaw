from __future__ import annotations

from typing import Dict

from .base_adapter import BaseWearableAdapter


class HuaweiAPIAdapter(BaseWearableAdapter):
    source_type = "huawei_api"

    def import_data(self, path: str) -> Dict:
        return {
            "status": "placeholder",
            "message": "Huawei API adapter is reserved. Phase 1 uses local exports only.",
            "records": [],
            "sessions": [],
            "profile": {},
            "sources": [],
        }

    def authenticate(self, credentials: Dict) -> bool:
        return False
