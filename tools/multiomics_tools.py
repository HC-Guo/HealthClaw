"""
Availability wrappers for multi-omics benchmark tools.

The MLOmics/CMOB repository provides datasets, baselines, and downstream
analysis scripts. The current HealthClaw stream exposes compressed feature
summaries, so pretrained sample-level subtype inference is only available if a
compatible checkpoint/pipeline is supplied.
"""
from __future__ import annotations

import os
import re
import time
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

try:
    import joblib
except Exception:  # pragma: no cover
    joblib = None


MLOMICS_SOURCE_ENV = "HEALTHCLAW_MLOMICS_SOURCE_DIR"
MLOMICS_MODEL_ENV = "HEALTHCLAW_MLOMICS_MODEL_DIR"
MLOMICS_RAW_ENV = "HEALTHCLAW_MLOMICS_RAW_DIR"
MLOMICS_SYNTHETIC_MODEL_ENV = "HEALTHCLAW_MLOMICS_SYNTHETIC_MODEL_DIR"
_MODEL_CACHE: Dict[str, Any] = {}
_RAW_CACHE: Dict[str, pd.DataFrame] = {}


def _source_dir(source_dir: Optional[str]) -> Path:
    return Path(source_dir or os.environ.get(MLOMICS_SOURCE_ENV, "external_models/mlomics/Cancer-Multi-Omics-Benchmark")).expanduser()


def _model_dir(model_dir: Optional[str]) -> Path:
    return Path(model_dir or os.environ.get(MLOMICS_MODEL_ENV, "external_models/mlomics/checkpoints")).expanduser()


def _synthetic_model_dir(model_dir: Optional[str]) -> Path:
    return Path(
        model_dir
        or os.environ.get(MLOMICS_SYNTHETIC_MODEL_ENV, "external_models/mlomics/synthetic_brca_xgb")
    ).expanduser()


def _raw_dir(raw_dir: Optional[str]) -> Path:
    return Path(
        raw_dir
        or os.environ.get(MLOMICS_RAW_ENV, "external_models/mlomics/GS-BRCA-Top")
    ).expanduser()


def _checkpoint_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    found: list[Path] = []
    for pattern in ["*.pt", "*.pth", "*.ckpt", "*.pkl", "*.joblib", "*.h5", "*.onnx"]:
        found.extend(root.rglob(pattern))
    return sorted(found)


def mlomics_cmob_status(source_dir: Optional[str] = None, model_dir: Optional[str] = None) -> Dict[str, Any]:
    source = _source_dir(source_dir)
    model_root = _model_dir(model_dir)
    checkpoints = _checkpoint_files(model_root)
    readme_exists = (source / "README.md").exists()
    baseline_dir_exists = (source / "Baseline_and_Metric").exists()
    return {
        "status": "available_if_adapter_completed" if readme_exists and checkpoints else "framework_available_no_checkpoint",
        "tool_name": "mlomics_cmob_status",
        "source_repo": "https://github.com/chenzRG/Cancer-Multi-Omics-Benchmark",
        "paper": "MLOmics: Cancer Multi-Omics Database for Machine Learning, Scientific Data 2025",
        "source_dir": str(source),
        "model_dir": str(model_root),
        "source_checkout_detected": readme_exists,
        "baseline_dir_exists": baseline_dir_exists,
        "checkpoint_files": [str(p) for p in checkpoints[:20]],
        "checkpoints_exist": bool(checkpoints),
        "task": "GS-BRCA subtype classification from multi-omics features",
        "current_benchmark_input": "compressed visible top-deviating feature summaries, not full omics matrices",
        "classes": ["0", "1", "2", "3", "4"],
        "input_visible_only": True,
        "gold_label_used": False,
        "future_cases_used": False,
        "limitation": (
            "The local CMOB/MLOmics checkout provides datasets, baseline scripts, and downstream "
            "analysis utilities, but no compatible pretrained subtype classifier checkpoint is "
            "present. Current HealthClaw cases expose compressed feature summaries rather than "
            "the full matrices expected by most CMOB baselines."
        ),
        "setup_hint": (
            "Provide full GS-BRCA Top matrices with a strict split and train a CMOB baseline, "
            "or place a validated pretrained subtype checkpoint under HEALTHCLAW_MLOMICS_MODEL_DIR."
        ),
    }


def mlomics_synthetic_brca_xgb_status(
    model_dir: Optional[str] = None,
    raw_dir: Optional[str] = None,
) -> Dict[str, Any]:
    model_root = _synthetic_model_dir(model_dir)
    raw_root = _raw_dir(raw_dir)
    model_path = model_root / "xgb_synthetic_brca.joblib"
    features_path = model_root / "feature_names.json"
    metrics_path = model_root / "metrics.json"
    raw_files = {omic: _raw_file(raw_root, omic) for omic in ["mrna", "mirna", "methy", "cnv"]}
    return {
        "status": "available" if joblib is not None and model_path.exists() and features_path.exists() and all(p.exists() for p in raw_files.values()) else "not_ready",
        "tool_name": "mlomics_synthetic_brca_xgb_status",
        "source_repo": "https://github.com/deaneeth/multi-omics-cancer-subtype-classifier",
        "license": "MIT",
        "model_dir": str(model_root),
        "raw_dir": str(raw_root),
        "model_path": str(model_path),
        "feature_names_path": str(features_path),
        "metrics_path": str(metrics_path),
        "raw_files_exist": {k: p.exists() for k, p in raw_files.items()},
        "joblib_available": joblib is not None,
        "task": "GS-BRCA multi-omics subtype classification",
        "classes": ["0", "1", "2", "3", "4"],
        "class_names": {
            "0": "Basal-like",
            "1": "HER2-enriched",
            "2": "Luminal A",
            "3": "Luminal B",
            "4": "Normal-like",
        },
        "training_source": "External synthetic BRCA samples from deaneeth/multi-omics-cancer-subtype-classifier; HealthClaw evaluation labels are not used.",
        "input_visible_only": True,
        "gold_label_used": False,
        "future_cases_used": False,
        "limitation": (
            "The adapter is trained on external synthetic BRCA samples because no no-leakage public pretrained "
            "CMOB GS-BRCA checkpoint was available. Treat probabilities as auxiliary multi-omics evidence; "
            "gate or disable if task-level validation shows regression."
        ),
    }


def _load_synthetic_brca_model(model_dir: Optional[str] = None):
    model_root = _synthetic_model_dir(model_dir)
    cache_key = f"synthetic_brca:{model_root.resolve()}"
    if cache_key in _MODEL_CACHE:
        return _MODEL_CACHE[cache_key]
    status = mlomics_synthetic_brca_xgb_status(model_dir=model_dir, raw_dir=None)
    if not (model_root / "xgb_synthetic_brca.joblib").exists():
        raise FileNotFoundError(f"missing synthetic BRCA XGB model under {model_root}")
    assert joblib is not None
    import json

    model = joblib.load(model_root / "xgb_synthetic_brca.joblib")
    feature_names = json.loads((model_root / "feature_names.json").read_text(encoding="utf-8"))
    metrics = {}
    metrics_path = model_root / "metrics.json"
    if metrics_path.exists():
        metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    _MODEL_CACHE[cache_key] = (model, feature_names, metrics, status)
    return _MODEL_CACHE[cache_key]


def _load_raw_matrix(raw_root: Path, omic: str) -> pd.DataFrame:
    path = _raw_file(raw_root, omic)
    if not path.exists():
        raise FileNotFoundError(f"missing {omic} raw matrix under {raw_root}")
    cache_key = f"{omic}:{path.resolve()}"
    if cache_key not in _RAW_CACHE:
        _RAW_CACHE[cache_key] = pd.read_csv(path, index_col=0)
        _RAW_CACHE[cache_key].index = _RAW_CACHE[cache_key].index.astype(str)
        _RAW_CACHE[cache_key].columns = _RAW_CACHE[cache_key].columns.astype(str)
    return _RAW_CACHE[cache_key]


def _raw_file(raw_root: Path, omic: str) -> Path:
    filenames = {
        "mrna": "BRCA_mRNA_top.csv",
        "mirna": "BRCA_miRNA_top.csv",
        "methy": "BRCA_Methy_top.csv",
        "cnv": "BRCA_CNV_top.csv",
    }
    path = raw_root / filenames[omic]
    if path.exists():
        return path
    stem = filenames[omic].replace(".csv", "_toy.csv")
    toy_path = raw_root / stem
    return toy_path if toy_path.exists() else path


def _extract_sample_id(case: Dict[str, Any]) -> str:
    for key in ("sample_id", "case_id", "visible_input", "memory_visible_summary"):
        value = str(case.get(key) or "")
        match = re.search(r"TCGA\.[A-Z0-9]{2}\.[A-Z0-9]{4}\.01", value)
        if match:
            return match.group(0)
    return ""


def _raw_sample_to_features(sample_id: str, feature_names: list[str], raw_dir: Optional[str]) -> pd.DataFrame:
    raw_root = _raw_dir(raw_dir)
    values: Dict[str, float] = {}
    for omic, prefix in [("mrna", "mrna_"), ("mirna", "mirna_"), ("methy", "methy_"), ("cnv", "cnv_")]:
        matrix = _load_raw_matrix(raw_root, omic)
        if sample_id not in matrix.columns:
            continue
        series = pd.to_numeric(matrix[sample_id], errors="coerce")
        for feature, value in series.items():
            values[prefix + str(feature)] = float(value) if pd.notna(value) else 0.0
    row = {name: values.get(name, 0.0) for name in feature_names}
    return pd.DataFrame([row], columns=feature_names)


def mlomics_synthetic_brca_xgb_classify(
    case: Dict[str, Any],
    model_dir: Optional[str] = None,
    raw_dir: Optional[str] = None,
    label_options: Optional[list[str]] = None,
) -> Dict[str, Any]:
    started = time.time()
    status = mlomics_synthetic_brca_xgb_status(model_dir=model_dir, raw_dir=raw_dir)
    if status["status"] != "available":
        return {**status, "tool_name": "mlomics_synthetic_brca_xgb_classify"}
    sample_id = _extract_sample_id(case)
    if not sample_id:
        return {
            "status": "error",
            "tool_name": "mlomics_synthetic_brca_xgb_classify",
            "message": "Could not parse TCGA sample ID from case.",
            "input_visible_only": True,
            "gold_label_used": False,
            "future_cases_used": False,
        }
    try:
        model, feature_names, metrics, _ = _load_synthetic_brca_model(model_dir)
        frame = _raw_sample_to_features(sample_id, feature_names, raw_dir)
        probs = model.predict_proba(frame)[0]
        labels = [str(x) for x in (label_options or status["classes"])]
        candidates = []
        for idx, prob in enumerate(probs):
            label = str(idx)
            if labels and label not in labels:
                continue
            candidates.append({
                "label": label,
                "class_name": status["class_names"].get(label),
                "probability": float(prob),
                "covered_by_model": True,
            })
        candidates.sort(key=lambda x: float(x["probability"]), reverse=True)
        return {
            "status": "success",
            "tool_name": "mlomics_synthetic_brca_xgb_classify",
            "source_repo": status["source_repo"],
            "license": "MIT",
            "sample_id": sample_id,
            "training_source": status["training_source"],
            "class_scores": candidates,
            "label_candidates": candidates,
            "top_label_candidate": candidates[0] if candidates else None,
            "synthetic_holdout_metrics": metrics,
            "input_visible_only": True,
            "gold_label_used": False,
            "future_cases_used": False,
            "latency_ms": int((time.time() - started) * 1000),
            "warning": status["limitation"],
        }
    except Exception as exc:
        return {
            "status": "error",
            "tool_name": "mlomics_synthetic_brca_xgb_classify",
            "message": str(exc)[:800],
            "sample_id": sample_id,
            "input_visible_only": True,
            "gold_label_used": False,
            "future_cases_used": False,
            "latency_ms": int((time.time() - started) * 1000),
        }
