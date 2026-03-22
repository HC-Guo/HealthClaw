from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from .base_adapter import BaseWearableAdapter


class HuaweiExportAdapter(BaseWearableAdapter):
    source_type = "huawei_export_dir"

    def import_data(self, path: str) -> Dict:
        export_dir = Path(path)
        huawei_root = self._resolve_root(export_dir)

        records: List[Dict] = []
        sessions: List[Dict] = []
        profile: Dict = {"source_brand": "huawei"}
        sources: List[Dict] = []
        notes: List[str] = []

        records.extend(self._parse_sport_per_minute(huawei_root, notes))
        records.extend(self._parse_health_details(huawei_root, profile, notes))
        sessions.extend(self._parse_motion_paths(huawei_root, notes))
        records.extend(self._records_from_sessions(sessions))
        profile.update(self._optional_xls_profile(huawei_root, notes))

        notes.append(f"Parsed Huawei export directory at {huawei_root}")
        return {
            "records": records,
            "sessions": sessions,
            "profile": profile,
            "sources": sources,
            "notes": notes,
        }

    def _resolve_root(self, export_dir: Path) -> Path:
        if (export_dir / "Sport per minute merged data & description").exists():
            return export_dir
        child = export_dir / "HUAWEI_HEALTH"
        if child.exists():
            return child
        return export_dir

    def _parse_sport_per_minute(self, root: Path, notes: List[str]) -> List[Dict]:
        path = root / "Sport per minute merged data & description" / "sport per minute merged data.json"
        payload = self._load_json(path, notes)
        records: List[Dict] = []
        for day_item in payload if isinstance(payload, list) else []:
            segments = day_item.get("sportDataUserData") or []
            for segment in segments:
                basic_infos = segment.get("sportBasicInfos") or [{}]
                basic = basic_infos[0] if basic_infos else {}
                timestamp = self._to_iso(segment.get("endTime") or segment.get("startTime"))
                if not timestamp:
                    continue
                record = {
                    "timestamp": timestamp,
                    "metric_type": f"huawei_sport_minute_{segment.get('sportType', 'unknown')}",
                    "heart_rate": None,
                    "steps": self._safe_float(basic.get("steps")),
                    "sleep_duration": None,
                    "deep_sleep_ratio": None,
                    "spo2": None,
                    "stress_level": None,
                    "calories": self._normalize_calories(basic.get("calorie")),
                    "distance": self._safe_float(basic.get("distance")),
                    "activity_type": self._sport_type_name(segment.get("sportType")),
                    "lat": None,
                    "lon": None,
                    "raw_key": "sport_per_minute",
                    "raw_value_json": segment,
                    "source_brand": "huawei",
                    "source_type": self.source_type,
                    "data_origin": path.name,
                    "quality_flag": "good",
                }
                if self._has_value(record):
                    records.append(record)
        notes.append(f"Parsed sport-per-minute rows from {path.name}: {len(records)} records")
        return records

    def _parse_health_details(self, root: Path, profile: Dict, notes: List[str]) -> List[Dict]:
        detail_dir = root / "Health detail data & description"
        records: List[Dict] = []
        for path in sorted(detail_dir.glob("health detail data*.json")):
            payload = self._load_json(path, notes)
            if not isinstance(payload, list):
                continue
            for item in payload:
                sample_points = item.get("samplePoints") or []
                for point in sample_points:
                    key = point.get("key")
                    value = self._parse_json_string(point.get("value"))
                    metadata = self._parse_json_string(point.get("fieldsMetadata"))
                    timestamp = self._to_iso(point.get("endTime") or point.get("startTime") or item.get("endTime"))
                    if not timestamp:
                        continue
                    record = self._record_from_health_point(key, value, metadata, timestamp, path.name)
                    if record:
                        records.append(record)
                        if key == "WEIGHT_BODYFAT_BROAD":
                            profile["member_profile"] = {
                                "height_cm": self._safe_float(value.get("height")),
                                "weight_kg": self._safe_float(value.get("bodyWeight")),
                                "age": self._safe_float(value.get("age")),
                                "gender": value.get("gender"),
                            }
                            profile["source_identifier"] = str(item.get("deviceCode") or "")
        notes.append(f"Parsed health-detail files from {detail_dir.name}: {len(records)} records")
        return records

    def _record_from_health_point(self, key: Optional[str], value, metadata, timestamp: str, origin: str) -> Dict:
        key = key or "huawei_health_metric"
        metric_type = key.lower()
        raw_payload = value if value not in ("", None) else metadata
        if key == "WEIGHT_BODYFAT_BROAD" and isinstance(value, dict):
            return {
                "timestamp": timestamp,
                "metric_type": "body_composition",
                "heart_rate": None,
                "steps": None,
                "sleep_duration": None,
                "deep_sleep_ratio": None,
                "spo2": None,
                "stress_level": None,
                "calories": None,
                "distance": None,
                "activity_type": "body_measurement",
                "lat": None,
                "lon": None,
                "raw_key": key,
                "raw_value_json": value,
                "source_brand": "huawei",
                "source_type": self.source_type,
                "data_origin": origin,
                "quality_flag": "good",
            }
        if key == "BASAL_METABOLISM" and isinstance(value, dict):
            return {
                "timestamp": timestamp,
                "metric_type": metric_type,
                "heart_rate": None,
                "steps": None,
                "sleep_duration": None,
                "deep_sleep_ratio": None,
                "spo2": None,
                "stress_level": None,
                "calories": self._normalize_calories(value.get("basalMetabolism")),
                "distance": None,
                "activity_type": "metabolic_profile",
                "lat": None,
                "lon": None,
                "raw_key": key,
                "raw_value_json": value,
                "source_brand": "huawei",
                "source_type": self.source_type,
                "data_origin": origin,
                "quality_flag": "good",
            }
        if key == "ACTIVE_HOUR" and isinstance(value, dict):
            return {
                "timestamp": timestamp,
                "metric_type": metric_type,
                "heart_rate": None,
                "steps": None,
                "sleep_duration": None,
                "deep_sleep_ratio": None,
                "spo2": None,
                "stress_level": None,
                "calories": None,
                "distance": None,
                "activity_type": "active_hour",
                "lat": None,
                "lon": None,
                "raw_key": key,
                "raw_value_json": value,
                "source_brand": "huawei",
                "source_type": self.source_type,
                "data_origin": origin,
                "quality_flag": "good" if value.get("isActive") in (0, 1) else "fair",
            }
        if key == "SPORT_GOAL_ACHIEVEMENT_DATA" and isinstance(value, dict):
            return {
                "timestamp": timestamp,
                "metric_type": metric_type,
                "heart_rate": None,
                "steps": self._safe_float(value.get("stepUserValue")),
                "sleep_duration": self._safe_float(value.get("durationUserValue")),
                "deep_sleep_ratio": None,
                "spo2": None,
                "stress_level": None,
                "calories": self._normalize_calories(value.get("calorieUserValue")),
                "distance": None,
                "activity_type": "goal_achievement",
                "lat": None,
                "lon": None,
                "raw_key": key,
                "raw_value_json": value,
                "source_brand": "huawei",
                "source_type": self.source_type,
                "data_origin": origin,
                "quality_flag": "good",
            }
        if key == "NUTRITION_RECORD" and isinstance(value, dict):
            return {
                "timestamp": timestamp,
                "metric_type": metric_type,
                "heart_rate": None,
                "steps": None,
                "sleep_duration": None,
                "deep_sleep_ratio": None,
                "spo2": None,
                "stress_level": None,
                "calories": self._safe_float(value.get("dietaryEnergy")),
                "distance": None,
                "activity_type": "nutrition",
                "lat": None,
                "lon": None,
                "raw_key": key,
                "raw_value_json": value,
                "source_brand": "huawei",
                "source_type": self.source_type,
                "data_origin": origin,
                "quality_flag": "good",
            }
        if key == "DIET_RECORD":
            return {
                "timestamp": timestamp,
                "metric_type": metric_type,
                "heart_rate": None,
                "steps": None,
                "sleep_duration": None,
                "deep_sleep_ratio": None,
                "spo2": None,
                "stress_level": None,
                "calories": self._diet_overview_calories(metadata),
                "distance": None,
                "activity_type": "diet_record",
                "lat": None,
                "lon": None,
                "raw_key": key,
                "raw_value_json": metadata,
                "source_brand": "huawei",
                "source_type": self.source_type,
                "data_origin": origin,
                "quality_flag": "good",
            }
        if isinstance(raw_payload, dict):
            return {
                "timestamp": timestamp,
                "metric_type": metric_type,
                "heart_rate": None,
                "steps": None,
                "sleep_duration": None,
                "deep_sleep_ratio": None,
                "spo2": None,
                "stress_level": None,
                "calories": None,
                "distance": None,
                "activity_type": None,
                "lat": None,
                "lon": None,
                "raw_key": key,
                "raw_value_json": raw_payload,
                "source_brand": "huawei",
                "source_type": self.source_type,
                "data_origin": origin,
                "quality_flag": "good",
            }
        return {}

    def _parse_motion_paths(self, root: Path, notes: List[str]) -> List[Dict]:
        motion_dir = root / "Motion path detail data & description"
        sessions: List[Dict] = []
        for path in sorted(motion_dir.glob("motion path detail data*.json")):
            payload = self._load_json(path, notes)
            if not isinstance(payload, list):
                continue
            for item in payload:
                start_time = self._to_iso(item.get("startTime"))
                end_time = self._to_iso(item.get("endTime"))
                first_point = self._extract_first_track_point(item.get("attribute"))
                sessions.append(
                    {
                        "activity_type": self._sport_type_name(item.get("sportType")),
                        "start_time": start_time,
                        "end_time": end_time,
                        "duration_sec": self._safe_float(item.get("totalTime")),
                        "distance_m": self._safe_float(item.get("totalDistance")),
                        "steps": self._safe_float(item.get("totalSteps") or item.get("realSteps")),
                        "calories": self._normalize_calories(item.get("totalCalories")),
                        "avg_pace_sec_per_km": self._pace_from_item(item),
                        "gpx_file": None,
                        "raw_payload_json": item,
                        "source_brand": "huawei",
                        "source_type": self.source_type,
                        "data_origin": path.name,
                        "lat": first_point.get("lat") if first_point else None,
                        "lon": first_point.get("lon") if first_point else None,
                    }
                )
        notes.append(f"Parsed motion-path files from {motion_dir.name}: {len(sessions)} sessions")
        return sessions

    def _records_from_sessions(self, sessions: List[Dict]) -> List[Dict]:
        records: List[Dict] = []
        for session in sessions:
            timestamp = session.get("end_time") or session.get("start_time")
            if not timestamp:
                continue
            record = {
                "timestamp": timestamp,
                "metric_type": f"session_{session.get('activity_type') or 'exercise'}",
                "heart_rate": None,
                "steps": session.get("steps"),
                "sleep_duration": None,
                "deep_sleep_ratio": None,
                "spo2": None,
                "stress_level": None,
                "calories": session.get("calories"),
                "distance": session.get("distance_m"),
                "activity_type": session.get("activity_type"),
                "lat": session.get("lat"),
                "lon": session.get("lon"),
                "raw_key": "motion_path_detail",
                "raw_value_json": session.get("raw_payload_json"),
                "source_brand": "huawei",
                "source_type": self.source_type,
                "data_origin": session.get("data_origin"),
                "quality_flag": "good",
            }
            if self._has_value(record):
                records.append(record)
        return records

    def _optional_xls_profile(self, root: Path, notes: List[str]) -> Dict:
        try:
            import pandas as pd
        except ImportError:
            notes.append("Skipped Huawei xls profile parsing because pandas is unavailable")
            return {}

        stats_dir = root / "SportsHealth data & desciption"
        profile = {}
        try:
            basic_path = stats_dir / "user basic info.xls"
            if basic_path.exists():
                df = pd.read_excel(basic_path)
                if not df.empty:
                    profile["extra"] = {"user_basic_info": df.iloc[0].to_dict()}
            daily_path = stats_dir / "user health daily statistics.xls"
            if daily_path.exists():
                df = pd.read_excel(daily_path)
                if not df.empty:
                    profile.setdefault("extra", {})["daily_statistics_columns"] = list(df.columns)
        except Exception as exc:
            notes.append(f"Skipped Huawei xls profile parsing: {exc}")
        return profile

    def _load_json(self, path: Path, notes: List[str]):
        if not path.exists():
            notes.append(f"Missing Huawei export file: {path}")
            return []
        try:
            text = path.read_text(encoding="utf-8")
            return json.loads(text)
        except json.JSONDecodeError:
            notes.append(f"Skipped invalid JSON file: {path.name}")
            return []

    def _parse_json_string(self, value):
        if not value:
            return {}
        if isinstance(value, dict):
            return value
        if isinstance(value, list):
            return value
        try:
            return json.loads(value)
        except (TypeError, json.JSONDecodeError):
            return {}

    def _diet_overview_calories(self, metadata: Dict) -> Optional[float]:
        if not isinstance(metadata, dict):
            return None
        diet_record = metadata.get("dietRecord")
        if isinstance(diet_record, str):
            try:
                diet_record = json.loads(diet_record)
            except json.JSONDecodeError:
                return None
        if not isinstance(diet_record, dict):
            return None
        overview = diet_record.get("overview") or {}
        return self._safe_float(overview.get("inTake"))

    def _normalize_calories(self, value) -> Optional[float]:
        value = self._safe_float(value)
        if value is None:
            return None
        return round(value / 1000.0, 3) if value > 100 else round(value, 3)

    def _extract_first_track_point(self, attribute: Optional[str]) -> Optional[Dict]:
        if not attribute:
            return None
        for line in attribute.splitlines():
            if "lat=" not in line or "lon=" not in line:
                continue
            data = {}
            for part in line.split(";"):
                if "=" not in part:
                    continue
                key, value = part.split("=", 1)
                data[key.strip()] = value.strip()
            lat = self._safe_float(data.get("lat"))
            lon = self._safe_float(data.get("lon"))
            if lat is not None and lon is not None:
                return {"lat": lat, "lon": lon}
        return None

    def _pace_from_item(self, item: Dict) -> Optional[float]:
        pace_map = item.get("paceMap") or {}
        if isinstance(pace_map, dict) and pace_map:
            try:
                return round(float(next(iter(pace_map.values()))), 2)
            except (TypeError, ValueError, StopIteration):
                return None
        duration = self._safe_float(item.get("totalTime"))
        distance_m = self._safe_float(item.get("totalDistance"))
        if duration and distance_m and distance_m > 0:
            return round(float(duration) / (float(distance_m) / 1000.0), 2)
        return None

    def _to_iso(self, value) -> Optional[str]:
        if value in (None, ""):
            return None
        try:
            ts = float(value)
            if ts > 1e12:
                ts /= 1000.0
            return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
        except (TypeError, ValueError, OSError):
            return None

    def _safe_float(self, value) -> Optional[float]:
        if value in (None, ""):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _sport_type_name(self, sport_type) -> str:
        mapping = {
            4: "run",
            5: "walk",
            6: "cycling",
            7: "climb",
        }
        return mapping.get(sport_type, f"sport_{sport_type}" if sport_type is not None else "exercise")

    def _has_value(self, record: Dict) -> bool:
        fields = ["heart_rate", "steps", "sleep_duration", "deep_sleep_ratio", "spo2", "stress_level", "calories", "distance"]
        return any(record.get(field) is not None for field in fields)
