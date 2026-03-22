from __future__ import annotations

import math
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from .base_adapter import BaseWearableAdapter


class GPXAdapter(BaseWearableAdapter):
    source_type = "gpx_file"

    def import_data(self, path: str) -> Dict:
        file_path = Path(path)
        tree = ET.parse(file_path)
        root = tree.getroot()
        ns = {"gpx": "http://www.topografix.com/GPX/1/1"}

        points: List[Dict] = []
        for trkpt in root.findall(".//gpx:trkpt", ns):
            lat = float(trkpt.attrib.get("lat"))
            lon = float(trkpt.attrib.get("lon"))
            time_node = trkpt.find("gpx:time", ns)
            ts = self._parse_time(time_node.text if time_node is not None else None)
            points.append({"lat": lat, "lon": lon, "timestamp": ts})

        if not points:
            return {
                "records": [],
                "sessions": [],
                "profile": {},
                "sources": [],
                "notes": [f"No track points found in {file_path.name}"],
            }

        total_distance = self._distance_from_extension(root, ns)
        if total_distance is None:
            total_distance = self._compute_distance(points)

        start_ts = points[0]["timestamp"]
        end_ts = points[-1]["timestamp"]
        duration_sec = None
        if start_ts and end_ts:
            duration_sec = int(
                (datetime.fromisoformat(end_ts) - datetime.fromisoformat(start_ts)).total_seconds()
            )

        activity_type = self._guess_activity_type(file_path.name)
        records = []
        for point in points:
            records.append(
                {
                    "timestamp": point["timestamp"],
                    "metric_type": "gps_trackpoint",
                    "distance": None,
                    "activity_type": activity_type,
                    "lat": point["lat"],
                    "lon": point["lon"],
                    "source_brand": "xiaomi",
                    "source_type": self.source_type,
                    "data_origin": file_path.name,
                    "quality_flag": "good",
                }
            )

        pace = None
        if duration_sec and total_distance and total_distance > 0:
            pace = round(duration_sec / (total_distance / 1000.0), 2)

        session = {
            "activity_type": activity_type,
            "start_time": start_ts,
            "end_time": end_ts,
            "duration_sec": duration_sec,
            "distance_m": round(total_distance, 2) if total_distance is not None else None,
            "steps": None,
            "calories": None,
            "avg_pace_sec_per_km": pace,
            "gpx_file": str(file_path),
            "raw_payload_json": {"point_count": len(points)},
            "source_brand": "xiaomi",
            "source_type": self.source_type,
        }

        return {
            "records": records,
            "sessions": [session],
            "profile": {},
            "sources": [],
            "notes": [f"Imported GPX with {len(points)} points"],
        }

    def _parse_time(self, value: Optional[str]) -> Optional[str]:
        if not value:
            return None
        value = value.replace("Z", "+00:00")
        return datetime.fromisoformat(value).astimezone(timezone.utc).isoformat()

    def _distance_from_extension(self, root, ns) -> Optional[float]:
        node = root.find(".//gpx:extensions/totalDistance", ns)
        if node is not None and node.text:
            try:
                return float(node.text)
            except ValueError:
                return None
        return None

    def _compute_distance(self, points: List[Dict]) -> float:
        total = 0.0
        for prev, cur in zip(points, points[1:]):
            total += self._haversine(prev["lat"], prev["lon"], cur["lat"], cur["lon"])
        return total

    def _haversine(self, lat1, lon1, lat2, lon2) -> float:
        radius = 6371000
        p1 = math.radians(lat1)
        p2 = math.radians(lat2)
        d_lat = math.radians(lat2 - lat1)
        d_lon = math.radians(lon2 - lon1)
        a = math.sin(d_lat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(d_lon / 2) ** 2
        return 2 * radius * math.asin(math.sqrt(a))

    def _guess_activity_type(self, file_name: str) -> str:
        name = file_name.lower()
        if "run" in name:
            return "running"
        if "walk" in name:
            return "walking"
        if "ride" in name or "bike" in name:
            return "cycling"
        return "exercise"
