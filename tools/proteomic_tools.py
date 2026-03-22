"""
Proteomic analysis utilities for Olink-like text tables.

Supported input formats:
- .txt
- .tsv
- .csv

Supported capabilities:
- sample/protein lookup by multiple aliases
- per-protein value, z-score, percentile, status
- annotation mapping by protein id / abbreviation / full name
- top abnormal proteins summary
- panel statistics for a queried sample
"""
from __future__ import annotations

import csv
import math
import os
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional


class ProteomicAnalyzer:
    """Proteomic backend with Olink-style long-table parsing."""

    def __init__(self):
        from config import UKB_DATA_CONFIG

        self.proteomics_file = UKB_DATA_CONFIG.get("proteomics_file", "")
        self.annotation_file = os.environ.get("UKB_PROTEIN_ANNOTATION_FILE", "")

        self._rows: Optional[List[dict]] = None
        self._samples: Optional[Dict[str, Dict[str, float]]] = None
        self._protein_stats: Optional[Dict[str, dict]] = None
        self._annotation_by_id: Optional[Dict[str, dict]] = None
        self._annotation_aliases: Optional[Dict[str, str]] = None

    def query(self, eid: str, proteins: list, return_format: str = "z_score") -> dict:
        """
        Query proteomic measurements for one sample.

        Return schema stays compatible with the existing handler/interpreter.
        """
        try:
            self._ensure_loaded()
            sample_key = self._resolve_sample_id(eid)
        except Exception as exc:
            return {
                "eid": str(eid),
                "results": [],
                "proteins_missing": list(proteins or []),
                "_note": str(exc),
            }

        requested = list(proteins or [])
        sample_map = self._samples.get(sample_key, {})
        results = []
        missing = []

        for token in requested:
            protein_id = self._resolve_protein_id(token)
            if not protein_id:
                missing.append(token)
                continue
            if protein_id not in sample_map:
                missing.append(token)
                continue
            result = self._build_result_row(sample_key, protein_id, sample_map[protein_id], return_format)
            result["query"] = token
            results.append(result)

        results.sort(key=lambda item: abs(item.get("z_score") or 0.0), reverse=True)
        panel_summary = self.summarize_panel(sample_key, requested)
        return {
            "eid": str(sample_key),
            "results": results,
            "proteins_missing": missing,
            "panel_summary": panel_summary,
            "dataset_info": self.get_dataset_summary(),
        }

    def summarize_panel(self, eid: str, proteins: Optional[Iterable[str]] = None) -> dict:
        """Return a compact structured summary for one queried panel."""
        self._ensure_loaded()
        sample_key = self._resolve_sample_id(eid)
        sample_map = self._samples.get(sample_key, {})

        selected_ids = []
        for token in proteins or []:
            protein_id = self._resolve_protein_id(token)
            if protein_id and protein_id in sample_map:
                selected_ids.append(protein_id)
        if not selected_ids:
            selected_ids = list(sample_map.keys())

        values = [sample_map[pid] for pid in selected_ids if pid in sample_map]
        if not values:
            return {"status": "empty"}

        abnormal = []
        for pid in selected_ids:
            row = self._build_result_row(sample_key, pid, sample_map[pid], "z_score")
            if row["status"] != "normal":
                abnormal.append(row)

        abnormal.sort(key=lambda item: abs(item.get("z_score") or 0.0), reverse=True)
        return {
            "status": "success",
            "sample_id": sample_key,
            "protein_count": len(selected_ids),
            "mean_value": round(sum(values) / len(values), 4),
            "min_value": round(min(values), 4),
            "max_value": round(max(values), 4),
            "abnormal_count": len(abnormal),
            "top_abnormal": abnormal[:10],
        }

    def top_abnormal_proteins(self, eid: str, top_n: int = 20) -> dict:
        """Expose a top-abnormal helper for future tool expansion."""
        self._ensure_loaded()
        sample_key = self._resolve_sample_id(eid)
        sample_map = self._samples.get(sample_key, {})
        rows = [self._build_result_row(sample_key, pid, value, "z_score") for pid, value in sample_map.items()]
        rows.sort(key=lambda item: abs(item.get("z_score") or 0.0), reverse=True)
        return {
            "eid": sample_key,
            "top_abnormal": rows[:top_n],
            "total_proteins": len(rows),
        }

    def get_dataset_summary(self) -> dict:
        """Return dataset counts and file paths."""
        try:
            self._ensure_loaded()
        except Exception as exc:
            return {"status": "error", "message": str(exc)}

        return {
            "status": "success",
            "proteomics_file": self.proteomics_file,
            "annotation_file": self._resolved_annotation_file() or "",
            "samples": len(self._samples),
            "proteins": len(self._protein_stats),
            "format": "long_table",
        }

    def _ensure_loaded(self):
        if self._samples is not None:
            return
        rows = self._read_proteomics_rows()
        if not rows:
            raise ValueError("Proteomics file contains no usable rows.")

        sample_map = defaultdict(dict)
        protein_values = defaultdict(list)
        for row in rows:
            sample = row["sample_id"]
            protein_id = row["protein_id"]
            value = row["value"]
            sample_map[sample][protein_id] = value
            protein_values[protein_id].append(value)

        stats = {}
        for protein_id, values in protein_values.items():
            mean = sum(values) / len(values)
            if len(values) > 1:
                var = sum((item - mean) ** 2 for item in values) / (len(values) - 1)
                std = math.sqrt(var) if var > 0 else 0.0
            else:
                std = 1.0
            stats[protein_id] = {"mean": mean, "std": std, "n": len(values)}

        self._rows = rows
        self._samples = dict(sample_map)
        self._protein_stats = stats
        self._load_annotations()

    def _read_proteomics_rows(self) -> List[dict]:
        if not self.proteomics_file:
            raise FileNotFoundError("UKB_PROTEOMICS_FILE is not configured.")

        path = Path(self.proteomics_file)
        if not path.exists():
            raise FileNotFoundError(f"Proteomics file '{self.proteomics_file}' does not exist.")

        delimiter = self._guess_delimiter(path)
        with path.open("r", encoding="utf-8", errors="ignore") as handle:
            reader = csv.DictReader(handle, delimiter=delimiter)
            rows = []
            for row in reader:
                normalized = self._normalize_proteomics_row(row)
                if normalized:
                    rows.append(normalized)
        return rows

    def _normalize_proteomics_row(self, row: dict) -> Optional[dict]:
        sample = (
            row.get("eid")
            or row.get("sample_id")
            or row.get("sample")
            or row.get("participant_id")
            or row.get("id")
        )
        protein_id = (
            row.get("protein_id")
            or row.get("protein")
            or row.get("protein_code")
            or row.get("coding")
            or row.get("abbreviation")
        )
        value = row.get("result") or row.get("value") or row.get("npx") or row.get("NPX")
        if sample in (None, "") or protein_id in (None, "") or value in (None, ""):
            return None
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return None
        return {
            "sample_id": str(sample),
            "protein_id": str(protein_id),
            "value": numeric,
            "ins_index": row.get("ins_index", ""),
        }

    def _load_annotations(self):
        if self._annotation_by_id is not None:
            return

        by_id = {}
        aliases = {}
        annotation_path = self._resolved_annotation_file()
        if annotation_path and Path(annotation_path).exists():
            delimiter = self._guess_delimiter(Path(annotation_path))
            with Path(annotation_path).open("r", encoding="utf-8", errors="ignore") as handle:
                reader = csv.DictReader(handle, delimiter=delimiter)
                for row in reader:
                    protein_id = (
                        row.get("protein_id")
                        or row.get("coding")
                        or row.get("id")
                        or row.get("index")
                    )
                    if not protein_id:
                        continue
                    protein_id = str(protein_id)
                    item = {
                        "protein_id": protein_id,
                        "abbreviation": str(row.get("abbreviation") or row.get("symbol") or row.get("protein") or ""),
                        "full_name": str(row.get("full_name") or row.get("name") or row.get("description") or ""),
                    }
                    by_id[protein_id] = item
                    for alias in {protein_id, item["abbreviation"], item["full_name"]}:
                        if alias:
                            aliases.setdefault(alias.lower(), protein_id)

        for protein_id in self._protein_stats.keys():
            by_id.setdefault(protein_id, {"protein_id": protein_id, "abbreviation": protein_id, "full_name": ""})
            aliases.setdefault(protein_id.lower(), protein_id)
            aliases.setdefault(by_id[protein_id]["abbreviation"].lower(), protein_id)

        self._annotation_by_id = by_id
        self._annotation_aliases = aliases

    def _resolved_annotation_file(self) -> str:
        if self.annotation_file:
            return self.annotation_file
        if not self.proteomics_file:
            return ""
        data_path = Path(self.proteomics_file)
        candidates = [
            data_path.with_name("protein_coding.tsv"),
            data_path.with_name("protein_coding.txt"),
            data_path.with_name("protein_coding.csv"),
        ]
        for candidate in candidates:
            if candidate.exists():
                return str(candidate)
        return ""

    def _resolve_sample_id(self, eid: str) -> str:
        key = str(eid)
        if key in self._samples:
            return key
        compact = str(int(key)) if key.isdigit() else key
        if compact in self._samples:
            return compact
        raise KeyError(f"Sample '{eid}' not found in proteomics dataset.")

    def _resolve_protein_id(self, token) -> Optional[str]:
        self._load_annotations()
        key = str(token).strip()
        if not key:
            return None
        if key in self._protein_stats:
            return key
        return self._annotation_aliases.get(key.lower())

    def _build_result_row(self, sample_id: str, protein_id: str, value: float, return_format: str) -> dict:
        stats = self._protein_stats.get(protein_id, {"mean": 0.0, "std": 1.0, "n": 1})
        if stats["n"] > 1 and stats["std"] > 0:
            z_score = (value - stats["mean"]) / stats["std"]
        else:
            # Single-sample fallback: keep NPX as pseudo-z so downstream logic still works.
            z_score = value
        percentile = self._z_to_percentile(z_score)
        status = self._status_from_z(z_score)
        annotation = self._annotation_by_id.get(protein_id, {})

        output_value = value
        if return_format == "percentile":
            output_value = percentile
        elif return_format == "raw":
            output_value = value
        elif return_format == "z_score":
            output_value = z_score

        return {
            "sample_id": sample_id,
            "protein": annotation.get("abbreviation") or protein_id,
            "protein_id": protein_id,
            "full_name": annotation.get("full_name") or "",
            "value": round(value, 5),
            "returned_value": round(output_value, 5),
            "z_score": round(z_score, 4),
            "percentile": round(percentile, 2),
            "status": status,
            "population_mean": round(stats["mean"], 5),
            "population_std": round(stats["std"], 5),
            "n_samples_reference": stats["n"],
        }

    def _guess_delimiter(self, path: Path) -> str:
        suffix = path.suffix.lower()
        if suffix == ".csv":
            return ","
        if suffix in {".tsv", ".txt"}:
            with path.open("r", encoding="utf-8", errors="ignore") as handle:
                sample = "".join(handle.readline() for _ in range(3))
            if sample.count("\t") >= sample.count(","):
                return "\t"
            return ","
        return "\t"

    def _status_from_z(self, z_score: float) -> str:
        if z_score >= 2.0:
            return "elevated"
        if z_score <= -2.0:
            return "reduced"
        return "normal"

    def _z_to_percentile(self, z_score: float) -> float:
        return 100.0 * 0.5 * (1.0 + math.erf(float(z_score) / math.sqrt(2.0)))
