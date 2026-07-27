"""
Availability wrappers for readmission-prediction tools.

PyHealth is a real clinical ML framework, but it does not provide a pretrained
UCI Diabetes readmission model for the current flattened benchmark cases. This
module reports that status explicitly instead of substituting hand-written
readmission rules.
"""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

try:
    import joblib
except Exception:  # pragma: no cover - dependency availability is reported in status
    joblib = None


PYHEALTH_SOURCE_ENV = "HEALTHCLAW_PYHEALTH_SOURCE_DIR"
DIABETES_MODEL_ENV = "HEALTHCLAW_DIABETES_MODEL_DIR"
_DIABETES_CACHE: Dict[str, Any] = {}


def _source_dir(source_dir: Optional[str]) -> Optional[Path]:
    source = source_dir or os.environ.get(PYHEALTH_SOURCE_ENV)
    return Path(source).expanduser() if source else None


def pyhealth_readmission_status(source_dir: Optional[str] = None) -> Dict[str, Any]:
    source = _source_dir(source_dir)
    pyhealth_importable = importlib.util.find_spec("pyhealth") is not None
    source_detected = bool(source and (source / "pyhealth").exists())
    return {
        "status": "framework_available_pipeline_required" if pyhealth_importable or source_detected else "not_ready",
        "tool_name": "pyhealth_readmission_status",
        "source_repo": "https://github.com/sunlabuiuc/PyHealth",
        "paper": "PyHealth: A Deep Learning Toolkit for Healthcare Predictive Modeling; PyHealth 2.0",
        "source_dir": str(source) if source else None,
        "pyhealth_importable": pyhealth_importable,
        "source_checkout_detected": source_detected,
        "task": "readmission prediction",
        "current_benchmark": "UCI Diabetes 130-US hospitals flattened encounter summaries",
        "input_visible_only": True,
        "gold_label_used": False,
        "future_cases_used": False,
        "limitation": (
            "PyHealth provides readmission task pipelines for datasets such as MIMIC/eICU/OMOP, "
            "but no pretrained UCI Diabetes readmission checkpoint is present in this workspace. "
            "Using PyHealth here requires a strict train/validation/test pipeline over the UCI "
            "features; it should not be treated as a ready zero-shot tool."
        ),
        "setup_hint": (
            "Build a dedicated UCI Diabetes readmission pipeline with fixed splits and train only "
            "on allowed training data, or provide a validated pretrained checkpoint."
        ),
    }


def _diabetes_model_dir(model_dir: Optional[str] = None) -> Path:
    return Path(
        model_dir
        or os.environ.get(DIABETES_MODEL_ENV, "external_models/diabetes_readmission/hospital-readmission-prediction")
    ).expanduser()


def uci_diabetes_xgb_readmission_status(model_dir: Optional[str] = None) -> Dict[str, Any]:
    root = _diabetes_model_dir(model_dir)
    paths = {
        "model": root / "models" / "xgb_tuned_model.pkl",
        "scaler": root / "models" / "scaler.pkl",
        "threshold": root / "models" / "best_threshold.pkl",
        "feature_names": root / "models" / "feature_names.json",
    }
    exists = {k: p.exists() for k, p in paths.items()}
    return {
        "status": "available" if all(exists.values()) and joblib is not None else "not_ready",
        "tool_name": "uci_diabetes_xgb_readmission_status",
        "source_repo": "https://github.com/analyst-ted/hospital-readmission-prediction",
        "license": "MIT",
        "model_dir": str(root),
        "artifact_paths": {k: str(v) for k, v in paths.items()},
        "artifact_exists": exists,
        "joblib_available": joblib is not None,
        "task": "UCI Diabetes 30-day hospital readmission prediction",
        "model": "XGBoost classifier with fitted scaler and optimized threshold",
        "reported_auc_roc": 0.653,
        "reported_recall": 0.53,
        "input_visible_only": True,
        "gold_label_used": False,
        "future_cases_used": False,
        "limitation": (
            "This is an external public project checkpoint trained on the same UCI Diabetes source dataset. "
            "It is useful as task-specific evidence, but should be audited for preprocessing/version mismatch "
            "and demographic bias before being treated as a final clinical decision model."
        ),
    }


def _load_diabetes_artifacts(model_dir: Optional[str] = None):
    status = uci_diabetes_xgb_readmission_status(model_dir)
    root = _diabetes_model_dir(model_dir)
    cache_key = str(root.resolve())
    if cache_key in _DIABETES_CACHE:
        return _DIABETES_CACHE[cache_key]
    if status["status"] != "available":
        raise FileNotFoundError(f"Diabetes XGB model artifacts are not ready under {root}")
    assert joblib is not None
    import json

    model = joblib.load(root / "models" / "xgb_tuned_model.pkl")
    scaler = joblib.load(root / "models" / "scaler.pkl")
    threshold = float(joblib.load(root / "models" / "best_threshold.pkl"))
    feature_names = json.loads((root / "models" / "feature_names.json").read_text(encoding="utf-8"))
    _DIABETES_CACHE[cache_key] = (model, scaler, threshold, feature_names)
    return _DIABETES_CACHE[cache_key]


def _age_to_index(age: Any) -> int:
    text = str(age or "").strip()
    bins = {
        "[0-10)": 0,
        "[10-20)": 1,
        "[20-30)": 2,
        "[30-40)": 3,
        "[40-50)": 4,
        "[50-60)": 5,
        "[60-70)": 6,
        "[70-80)": 7,
        "[80-90)": 8,
        "[90-100)": 9,
    }
    return bins.get(text, 0)


def _diag_category(code: Any) -> str:
    text = str(code or "").strip()
    if not text or text.lower() in {"nan", "none"}:
        return "Other"
    if text[0].upper() in {"E", "V"}:
        return "External_Supplementary"
    try:
        value = float(text)
    except ValueError:
        return "Other"
    if 1 <= value <= 139:
        return "Infectious"
    if 140 <= value <= 239:
        return "Cancer"
    if 240 <= value <= 279:
        return "Diabetes_Metabolic"
    if 290 <= value <= 319:
        return "Mental_Health"
    if 320 <= value <= 389:
        return "Nervous_System"
    if 390 <= value <= 459 or int(value) == 785:
        return "Circulatory"
    if 460 <= value <= 519 or int(value) == 786:
        return "Respiratory"
    if 520 <= value <= 579 or int(value) == 787:
        return "Digestive"
    if 580 <= value <= 629 or int(value) == 788:
        return "Genitourinary"
    if 630 <= value <= 679:
        return "Pregnancy"
    if 680 <= value <= 709:
        return "Skin_Disease"
    if 710 <= value <= 739:
        return "Musculoskeletal"
    if 740 <= value <= 759:
        return "Congenital"
    if 780 <= value <= 799:
        return "Symptoms"
    if 800 <= value <= 999:
        return "Injury_Poisoning"
    return "Other"


def _case_to_diabetes_features(case: Dict[str, Any], feature_names: list[str]) -> pd.DataFrame:
    ctx = case.get("visible_clinical_context") if isinstance(case.get("visible_clinical_context"), dict) else {}
    demographics = ctx.get("demographics") if isinstance(ctx.get("demographics"), dict) else {}
    admission = ctx.get("admission") if isinstance(ctx.get("admission"), dict) else {}
    clinical = ctx.get("clinical_signals") if isinstance(ctx.get("clinical_signals"), dict) else {}
    medication = ctx.get("medication_summary") if isinstance(ctx.get("medication_summary"), dict) else {}

    row: Dict[str, Any] = {feat: 0 for feat in feature_names}
    numeric = {
        "age": _age_to_index(demographics.get("age")),
        "admission_type_id": admission.get("admission_type_id") or 0,
        "discharge_disposition_id": admission.get("discharge_disposition_id") or 0,
        "admission_source_id": admission.get("admission_source_id") or 0,
        "time_in_hospital": admission.get("time_in_hospital") or 0,
        "num_lab_procedures": clinical.get("num_lab_procedures") or 0,
        "num_procedures": clinical.get("num_procedures") or 0,
        "num_medications": clinical.get("num_medications") or 0,
        "number_outpatient": clinical.get("number_outpatient") or 0,
        "number_emergency": clinical.get("number_emergency") or 0,
        "number_inpatient": clinical.get("number_inpatient") or 0,
        "number_diagnoses": clinical.get("number_diagnoses") or 0,
    }
    numeric["service_utilization"] = (
        numeric["number_outpatient"] + numeric["number_emergency"] + numeric["number_inpatient"]
    )
    for key, value in numeric.items():
        if key in row:
            row[key] = float(value)

    race = str(demographics.get("race") or "Other").strip().replace(" ", "")
    race_col = f"race_{race}"
    if race_col in row:
        row[race_col] = 1
    elif "race_Other" in row:
        row["race_Other"] = 1
    gender = str(demographics.get("gender") or "").strip()
    if gender == "Male" and "gender_Male" in row:
        row["gender_Male"] = 1
    if gender == "Unknown/Invalid" and "gender_Unknown/Invalid" in row:
        row["gender_Unknown/Invalid"] = 1

    active_changes = medication.get("active_changes") if isinstance(medication.get("active_changes"), list) else []
    insulin = "No"
    for item in active_changes:
        if isinstance(item, dict) and str(item.get("drug") or "").lower() == "insulin":
            insulin = str(item.get("status") or "No")
            break
    if insulin == "Down":
        insulin = "Steady"
    insulin_col = f"insulin_{insulin}"
    if insulin_col in row:
        row[insulin_col] = 1

    if str(medication.get("diabetesMed") or "").lower() == "yes" and "diabetesMed_Yes" in row:
        row["diabetesMed_Yes"] = 1
    if str(medication.get("change") or "").lower() == "no" and "change_No" in row:
        row["change_No"] = 1

    diagnoses = clinical.get("diagnosis_codes") if isinstance(clinical.get("diagnosis_codes"), list) else []
    for idx in range(1, 4):
        category = _diag_category(diagnoses[idx - 1] if idx <= len(diagnoses) else None)
        col = f"diag_{idx}_{category}"
        if col in row:
            row[col] = 1

    max_glu = str(clinical.get("max_glu_serum") or "").strip()
    if max_glu in {">300", "Norm"} and f"max_glu_serum_{max_glu}" in row:
        row[f"max_glu_serum_{max_glu}"] = 1
    a1c = str(clinical.get("A1Cresult") or "").strip()
    if a1c in {">8", "Norm"} and f"A1Cresult_{a1c}" in row:
        row[f"A1Cresult_{a1c}"] = 1
    return pd.DataFrame([row], columns=feature_names)


def uci_diabetes_xgb_readmission_classify(
    case: Dict[str, Any],
    model_dir: Optional[str] = None,
) -> Dict[str, Any]:
    started = os.times()[4]
    status = uci_diabetes_xgb_readmission_status(model_dir)
    if status["status"] != "available":
        return {**status, "tool_name": "uci_diabetes_xgb_readmission_classify"}
    try:
        model, scaler, threshold, feature_names = _load_diabetes_artifacts(model_dir)
        frame = _case_to_diabetes_features(case, feature_names)
        numerical_cols = [
            "age",
            "time_in_hospital",
            "num_lab_procedures",
            "num_procedures",
            "num_medications",
            "number_outpatient",
            "number_emergency",
            "number_inpatient",
            "number_diagnoses",
            "service_utilization",
        ]
        frame.loc[:, numerical_cols] = scaler.transform(frame[numerical_cols])
        prob_yes = float(model.predict_proba(frame)[0][1])
        prob_no = 1.0 - prob_yes
        threshold_prediction = "yes" if prob_yes >= threshold else "no"
        probability_ranked = [
            {"label": "yes", "probability": prob_yes, "covered_by_model": True},
            {"label": "no", "probability": prob_no, "covered_by_model": True},
        ]
        probability_ranked.sort(key=lambda x: float(x["probability"]), reverse=True)
        return {
            "status": "success",
            "tool_name": "uci_diabetes_xgb_readmission_classify",
            "source_repo": status["source_repo"],
            "license": "MIT",
            "model": status["model"],
            "probability_readmission_30d": prob_yes,
            "decision_threshold": threshold,
            "threshold_decision": {
                "label": threshold_prediction,
                "probability_readmission_30d": prob_yes,
                "threshold": threshold,
            },
            "label_candidates": probability_ranked,
            "top_label_candidate": probability_ranked[0] if probability_ranked else None,
            "input_visible_only": True,
            "gold_label_used": False,
            "future_cases_used": False,
            "latency_ms": int((os.times()[4] - started) * 1000),
            "warning": (
                status["limitation"]
                + " The original app uses a low recall-optimized threshold; HealthClaw ranks label candidates "
                "by calibrated probability and exposes the threshold decision separately."
            ),
        }
    except Exception as exc:
        return {
            "status": "error",
            "tool_name": "uci_diabetes_xgb_readmission_classify",
            "message": str(exc)[:800],
            "input_visible_only": True,
            "gold_label_used": False,
            "future_cases_used": False,
            "latency_ms": int((os.times()[4] - started) * 1000),
        }
