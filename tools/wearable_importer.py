from __future__ import annotations

from pathlib import Path
from typing import Dict

from .wearable_adapters import GPXAdapter, HuaweiAPIAdapter, HuaweiExportAdapter, XiaomiAPIAdapter, XiaomiExportAdapter


class WearableDataImporter:
    """Facade that keeps all upstream data sources behind adapters."""

    def __init__(self, store):
        self.store = store
        self.adapters = {
            "xiaomi_export_dir": XiaomiExportAdapter(),
            "huawei_export_dir": HuaweiExportAdapter(),
            "gpx_file": GPXAdapter(),
            "huawei_api": HuaweiAPIAdapter(),
            "xiaomi_api": XiaomiAPIAdapter(),
        }

    def import_source(self, eid: str, source_type: str, path: str) -> Dict:
        if source_type not in self.adapters:
            return {"status": "error", "message": f"Unsupported source_type: {source_type}"}
        if source_type in {"xiaomi_export_dir", "huawei_export_dir", "gpx_file"} and not Path(path).exists():
            return {"status": "error", "message": f"Path not found: {path}"}

        payload = self.adapters[source_type].import_data(path)
        if payload.get("status") == "placeholder":
            return payload

        result = self.store.store_import_result(
            eid=eid,
            source_type=source_type,
            source_path=path,
            import_result=payload,
        )
        result["source_type"] = source_type
        result["path"] = path
        return result
