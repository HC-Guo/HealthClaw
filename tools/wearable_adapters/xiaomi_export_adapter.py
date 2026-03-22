from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from .base_adapter import BaseWearableAdapter


class XiaomiExportAdapter(BaseWearableAdapter):
    source_type = "xiaomi_export_dir"

    def import_data(self, path: str) -> Dict:
        export_dir = Path(path)
        csv_files = list(export_dir.glob("*.csv"))

        records: List[Dict] = []
        sessions: List[Dict] = []
        profile: Dict = {}
        sources: List[Dict] = []
        notes: List[str] = []

        for csv_file in csv_files:
            name = csv_file.name.lower()
            rows = self._read_csv(csv_file)
            if not rows:
                continue

            if "hlth_center_fitness_data" in name:
                records.extend(self._parse_fitness_rows(rows, csv_file.name))
            elif "hlth_center_aggregated_fitness_data" in name:
                records.extend(self._parse_aggregated_rows(rows, csv_file.name))
            elif "hlth_center_sport_record" in name:
                sessions.extend(self._parse_sport_sessions(rows, csv_file.name))
            elif "hlth_center_data_source" in name:
                sources = rows
            elif "user_member_profile" in name:
                profile["member_profile"] = rows[0] if rows else {}
            elif "user_fitness_profile" in name:
                profile["fitness_profile"] = self._normalize_fitness_profile(rows[0]) if rows else {}
            elif "hlth_center_sport_track_data" in name:
                profile.setdefault("track_exports", []).extend(self._normalize_track_exports(rows))
            elif "user_device_setting" in name:
                profile.setdefault("device_settings", []).extend(rows)
            elif "user_health_plan_records" in name:
                profile.setdefault("health_plans", []).extend(rows)
            elif "user_fitness_data_records" in name or "user_fitness_with_uuid_data_records" in name:
                notes.append(f"Metadata file parsed but not converted into metric rows: {csv_file.name}")
            else:
                notes.append(f"Skipped unsupported Xiaomi export file: {csv_file.name}")

        notes.append(f"Parsed Xiaomi export directory with {len(csv_files)} csv files")
        return {
            "records": records,
            "sessions": sessions,
            "profile": profile,
            "sources": sources,
            "notes": notes,
        }

    def _read_csv(self, path: Path) -> List[Dict]:
        for encoding in ("utf-8-sig", "utf-8", "gbk", "gb18030"):
            try:
                with open(path, "r", encoding=encoding, newline="") as handle:
                    reader = csv.DictReader(handle)
                    rows = []
                    for row in reader:
                        normalized = {}
                        for key, value in row.items():
                            if key is None:
                                continue
                            normalized[key.strip().lower()] = value.strip() if isinstance(value, str) else value
                        rows.append(normalized)
                    return rows
            except UnicodeDecodeError:
                continue
        raise UnicodeDecodeError("utf-8", b"", 0, 1, f"Unable to decode {path}")

    def _parse_fitness_rows(self, rows: List[Dict], origin: str) -> List[Dict]:
        records = []
        for row in rows:
            key = (row.get("key") or "").lower()
            timestamp = self._to_iso(row.get("time"))
            payload = self._loads_json(row.get("value"))
            if not timestamp:
                continue
            record = self._record_from_payload(key, payload, timestamp, origin)
            if record:
                records.append(record)
        return records

    def _parse_aggregated_rows(self, rows: List[Dict], origin: str) -> List[Dict]:
        records = []
        for row in rows:
            tag = (row.get("tag") or "").lower()
            key = (row.get("key") or "").lower()
            payload = self._loads_json(row.get("value"))
            timestamp = self._to_iso(row.get("time"))
            if not timestamp:
                continue
            if tag == "daily_report" and isinstance(payload, dict):
                record = {
                    "timestamp": timestamp,
                    "metric_type": f"aggregated_{key or 'daily'}",
                    "heart_rate": self._pick_first_number(payload, ["avg_hr", "avg_heart_rate"]),
                    "steps": self._pick_first_number(payload, ["steps", "daily_steps", "step"]),
                    "sleep_duration": self._pick_sleep_hours(payload),
                    "deep_sleep_ratio": self._pick_deep_sleep_ratio(payload),
                    "spo2": self._valid_spo2(self._pick_first_number(payload, ["avg_spo2", "spo2", "oxygen"])),
                    "stress_level": self._pick_first_number(payload, ["avg_stress", "stress"]),
                    "calories": self._pick_first_number(payload, ["calories", "daily_calories"]),
                    "distance": self._pick_first_number(payload, ["distance", "daily_distance"]),
                    "activity_type": None,
                    "lat": None,
                    "lon": None,
                    "raw_key": key,
                    "raw_value_json": payload,
                    "source_brand": "xiaomi",
                    "source_type": self.source_type,
                    "data_origin": origin,
                    "quality_flag": "good",
                }
                if self._has_value(record):
                    records.append(record)
        return records

    def _parse_sport_sessions(self, rows: List[Dict], origin: str) -> List[Dict]:
        sessions = []
        for row in rows:
            payload = self._loads_json(row.get("value"))
            if not isinstance(payload, dict):
                continue
            start_time = self._to_iso(payload.get("start_time") or row.get("time"))
            end_time = self._to_iso(payload.get("end_time"))
            duration = self._pick_first_number(payload, ["duration"])
            distance = self._pick_first_number(payload, ["distance"])
            steps = self._pick_first_number(payload, ["steps"])
            calories = self._pick_first_number(payload, ["calories"])
            pace = None
            if duration and distance and distance > 0:
                pace = round(float(duration) / (float(distance) / 1000.0), 2)
            sessions.append(
                {
                    "activity_type": (row.get("category") or row.get("key") or payload.get("sport_type") or "exercise"),
                    "start_time": start_time,
                    "end_time": end_time,
                    "duration_sec": int(duration) if duration is not None else None,
                    "distance_m": float(distance) if distance is not None else None,
                    "steps": int(steps) if steps is not None else None,
                    "calories": int(calories) if calories is not None else None,
                    "avg_pace_sec_per_km": pace,
                    "gpx_file": None,
                    "raw_payload_json": payload,
                    "source_brand": "xiaomi",
                    "source_type": self.source_type,
                    "data_origin": origin,
                }
            )
        return sessions

    def _record_from_payload(self, key: str, payload: Dict, timestamp: str, origin: str) -> Dict:
        if not isinstance(payload, dict):
            return {}
        record = {
            "timestamp": timestamp,
            "metric_type": key or "xiaomi_metric",
            "heart_rate": self._pick_heart_rate(key, payload),
            "steps": self._pick_first_number(payload, ["steps", "step", "step_count"]),
            "sleep_duration": self._pick_sleep_hours(payload),
            "deep_sleep_ratio": self._pick_deep_sleep_ratio(payload),
            "spo2": self._valid_spo2(self._pick_first_number(payload, ["spo2", "oxygen", "blood_oxygen", "avg_spo2"])),
            "stress_level": self._pick_first_number(payload, ["stress", "avg_stress"]),
            "calories": self._pick_first_number(payload, ["calories", "kcal"]),
            "distance": self._pick_first_number(payload, ["distance"]),
            "activity_type": None,
            "lat": None,
            "lon": None,
            "raw_key": key,
            "raw_value_json": payload,
            "source_brand": "xiaomi",
            "source_type": self.source_type,
            "data_origin": origin,
            "quality_flag": "good",
        }
        return record if self._has_value(record) else {}

    def _normalize_fitness_profile(self, row: Dict) -> Dict:
        profile = dict(row)
        for key in ["recordmaxhrm", "initialweight", "regulargoallist"]:
            value = profile.get(key)
            if value:
                profile[key] = self._loads_json(value)
        for key in ["vo2max", "maximalmet", "maxhrm", "minhrm", "dailycalgoal", "dailystepgoal", "dailysleepgoal"]:
            if profile.get(key) not in (None, ""):
                try:
                    profile[key] = float(profile[key])
                except (TypeError, ValueError):
                    pass
        return profile

    def _normalize_track_exports(self, rows: List[Dict]) -> List[Dict]:
        normalized = []
        for row in rows:
            normalized.append(
                {
                    "uid": row.get("uid"),
                    "did": row.get("did"),
                    "key": row.get("key"),
                    "time": self._to_iso(row.get("time")),
                    "gpx": row.get("gpx"),
                }
            )
        return normalized

    def _pick_heart_rate(self, key: str, payload: Dict):
        if "heart" in key:
            return self._pick_first_number(payload, ["bpm", "heart_rate", "avg_hr", "avg_heart_rate"])
        return self._pick_first_number(payload, ["bpm"])

    def _pick_sleep_hours(self, payload: Dict):
        value = self._pick_first_number(payload, ["sleep_duration", "total_sleep", "sleep_minutes", "duration"])
        if value is None:
            return None
        value = float(value)
        if value > 24:
            return round(value / 60.0, 2)
        return round(value, 2)

    def _pick_deep_sleep_ratio(self, payload: Dict):
        deep = self._pick_first_number(payload, ["deep_sleep_ratio"])
        if deep is not None:
            return float(deep)
        deep_minutes = self._pick_first_number(payload, ["deep_sleep", "deep_sleep_minutes"])
        total_minutes = self._pick_first_number(payload, ["sleep_minutes", "total_sleep"])
        if deep_minutes is not None and total_minutes:
            return round(float(deep_minutes) / float(total_minutes), 3)
        return None

    def _valid_spo2(self, value):
        if value is None:
            return None
        value = float(value)
        return value if value > 0 else None

    def _pick_first_number(self, payload: Dict, keys: List[str]):
        for key in keys:
            if key in payload and payload[key] not in (None, ""):
                try:
                    return float(payload[key])
                except (TypeError, ValueError):
                    continue
        return None

    def _has_value(self, record: Dict) -> bool:
        fields = ["heart_rate", "steps", "sleep_duration", "deep_sleep_ratio", "spo2", "stress_level", "calories", "distance"]
        return any(record.get(field) is not None for field in fields)

    def _loads_json(self, value):
        if not value:
            return {}
        if isinstance(value, dict):
            return value
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return {}

    def _to_iso(self, value):
        if value in (None, ""):
            return None
        try:
            ts = float(value)
            if ts > 1e12:
                ts = ts / 1000.0
            return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
        except (TypeError, ValueError, OSError):
            return None
