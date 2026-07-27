#!/usr/bin/env python3
"""Stage-4 EHR tool implementations used by the HealthClaw tool-call benchmark.

This file is copied into each fresh HealthClaw clone under tools/stage4_ehr_tools.py.
The benchmark runner imports route_tools/execute_tool from the cloned repository so
tool execution is part of the repo artifact rather than an external ad hoc L0-L4 mock.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple


def flatten_numeric(obj: Any, prefix: str = "") -> Dict[str, float]:
    out: Dict[str, float] = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.update(flatten_numeric(v, f"{prefix}.{k}" if prefix else str(k)))
    elif isinstance(obj, (int, float)) and not isinstance(obj, bool) and math.isfinite(float(obj)):
        out[prefix] = float(obj)
    return out


def flatten_values(obj: Any, prefix: str = "") -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.update(flatten_values(v, f"{prefix}.{k}" if prefix else str(k)))
    else:
        out[prefix] = obj
    return out


def band(value: float, q: Optional[Tuple[float, float]]) -> str:
    if q is None:
        return "unknown"
    q1, q2 = q
    return "low" if value <= q1 else ("high" if value >= q2 else "mid")


def _ctx(case: Dict[str, Any]) -> Dict[str, Any]:
    return case.get("visible_clinical_context", {}) or {}


def _get_path(ctx: Dict[str, Any], suffix: str) -> Optional[float]:
    for k, v in flatten_numeric(ctx).items():
        if k.lower().endswith(suffix.lower()):
            return float(v)
    return None


def route_tools(task_key: str, case: Dict[str, Any], max_tool_calls: int = 3) -> Dict[str, Any]:
    if task_key == "uci_thyroid_diagnosis":
        candidates = [
            "thyroid_axis_diagnosis",
            "interpret_indicator",
            "structured_feature_analysis",
            "suggest_icd_codes",
            "check_pathway_compliance",
        ]
        selected = ["thyroid_axis_diagnosis"]
        skipped = [
            {"tool_name": "interpret_indicator", "reason": "auxiliary bands only; direct thyroid-axis diagnosis is more useful for benchmark labels"},
            {"tool_name": "structured_feature_analysis", "reason": "axis scores are embedded in thyroid_axis_diagnosis output"},
            {"tool_name": "suggest_icd_codes", "reason": "diagnosis label classification, not ICD coding"},
            {"tool_name": "check_pathway_compliance", "reason": "no treatment pathway is visible in the current input"},
        ]
    elif task_key == "physionet2012_sofa_severity":
        candidates = [
            "interpret_indicator",
            "compare_checkup_history",
            "code_run.sofa_like_proxy",
            "check_drug_interaction",
        ]
        selected = ["interpret_indicator", "compare_checkup_history"]
        skipped = [
            {"tool_name": "code_run.sofa_like_proxy", "reason": "direct physiology proxy score can miscalibrate the benchmark label; keep raw indicators/trends instead"},
            {"tool_name": "check_drug_interaction", "reason": "current visible input has no medication list"},
        ]
    else:
        candidates = ["interpret_indicator"]
        selected = ["interpret_indicator"]
        skipped = []
    selected = selected[:max_tool_calls]
    return {
        "enabled": True,
        "policy_version": "HealthClaw/tools/stage4_ehr_tools.py::route_tools_v1",
        "task_family": "ehr",
        "candidate_tools": candidates,
        "selected_tools": selected,
        "skipped_tools": skipped,
        "selection_reasons": [
            {"tool_name": t, "reason": "applicable to current visible observation and HealthClaw health/tools schema"}
            for t in selected
        ],
        "max_tool_calls": max_tool_calls,
    }


def execute_tool(task_key: str, tool_name: str, case: Dict[str, Any], bins: Dict[str, Tuple[float, float]]) -> Dict[str, Any]:
    if tool_name == "interpret_indicator":
        return _interpret_indicator(task_key, case, bins)
    if tool_name == "compare_checkup_history":
        return _compare_checkup_history(case)
    if tool_name == "code_run.sofa_like_proxy":
        return _sofa_like_proxy(case)
    if tool_name in {"code_run.structured_feature_analysis", "structured_feature_analysis"}:
        return _thyroid_feature_analysis(case, bins)
    if tool_name == "thyroid_axis_diagnosis":
        return _thyroid_axis_diagnosis(case, bins)
    return {
        "summary": "Tool selected by router but no stage4 EHR implementation is available.",
        "findings": [],
        "tags": ["tool_unimplemented"],
    }


def _interpret_indicator(task_key: str, case: Dict[str, Any], bins: Dict[str, Tuple[float, float]]) -> Dict[str, Any]:
    ctx = _ctx(case)
    findings: List[Dict[str, Any]] = []
    tags: List[str] = []
    if task_key == "uci_thyroid_diagnosis":
        for key, val in flatten_numeric(ctx).items():
            lk = key.lower()
            if any(x in lk for x in ["tsh", "t3", "tt4", "t4u", "fti"]):
                b = band(val, bins.get(key))
                findings.append({
                    "indicator": key,
                    "value": val,
                    "relative_band": b,
                    "interpretation": f"{key} is {b} relative to this benchmark distribution",
                })
                tags.append(f"{key}_{b}"[:120])
        summary = "Interpreted thyroid-function indicators using distributional low/mid/high bands from visible features only."
    else:
        rules = [
            ("GCS", lambda x: x <= 8, "low GCS suggests neurologic dysfunction"),
            ("Creatinine", lambda x: x >= 1.5, "high creatinine suggests renal dysfunction"),
            ("BUN", lambda x: x >= 30, "high BUN suggests renal stress"),
            ("Platelets", lambda x: x < 100, "low platelets suggests coagulation dysfunction"),
            ("Urine", lambda x: x < 50, "low urine output suggests renal/circulatory risk"),
            ("MAP", lambda x: x < 65, "low MAP suggests circulatory dysfunction"),
            ("HR", lambda x: x >= 120, "tachycardia suggests physiologic stress"),
            ("Temp", lambda x: x >= 39 or x <= 35, "temperature abnormality suggests systemic stress"),
        ]
        for key, val in flatten_numeric(ctx).items():
            for needle, fn, msg in rules:
                if key.lower().endswith(needle.lower()) and fn(float(val)):
                    findings.append({"indicator": key, "value": val, "interpretation": msg})
                    tags.append(msg.split()[0].lower() + "_" + needle.lower())
        summary = "Interpreted ICU indicators for organ-dysfunction and physiologic stress signals from visible first-48h summaries."
    return {"summary": summary, "findings": findings[:20], "tags": tags[:30]}


def _thyroid_feature_analysis(case: Dict[str, Any], bins: Dict[str, Tuple[float, float]]) -> Dict[str, Any]:
    ctx = _ctx(case)
    vals = flatten_numeric(ctx)
    bands: Dict[str, str] = {}
    for key, val in vals.items():
        lk = key.lower()
        if any(x in lk for x in ["tsh", "t3", "tt4", "t4u", "fti"]):
            bands[key] = band(val, bins.get(key))
    tsh = next((b for k, b in bands.items() if k.lower().endswith("tsh_scaled")), None)
    t3 = next((b for k, b in bands.items() if k.lower().endswith("t3_scaled")), None)
    tt4 = next((b for k, b in bands.items() if k.lower().endswith("tt4_scaled")), None)
    fti = next((b for k, b in bands.items() if k.lower().endswith("fti_scaled")), None)
    axis_signals = {"suppressed_tsh_axis": 0.0, "elevated_tsh_axis": 0.0, "balanced_axis": 0.0}
    if tsh == "low":
        axis_signals["suppressed_tsh_axis"] += 1.0
    if tsh == "high":
        axis_signals["elevated_tsh_axis"] += 1.0
    for b in [t3, tt4, fti]:
        if b == "high":
            axis_signals["suppressed_tsh_axis"] += 0.7
        elif b == "low":
            axis_signals["elevated_tsh_axis"] += 0.7
        elif b == "mid":
            axis_signals["balanced_axis"] += 0.25
    if all(b == "mid" for b in [tsh, t3, tt4, fti] if b):
        axis_signals["balanced_axis"] += 1.5
    findings = [{"feature_bands": bands}, {"thyroid_axis_signal_scores": axis_signals}]
    tags = []
    for key, value in bands.items():
        short = key.split(".")[-1].replace("_scaled", "").lower()
        tags.append(f"tool_thyroid_{short}_{value}")
    return {
        "summary": "Structured thyroid-axis feature analysis computed relative bands and axis-signal scores from visible scaled thyroid tests; it does not output a diagnosis label.",
        "findings": findings,
        "tags": tags[:30],
    }


def _thyroid_axis_diagnosis(case: Dict[str, Any], bins: Dict[str, Tuple[float, float]]) -> Dict[str, Any]:
    ctx = _ctx(case)
    tests = ctx.get("thyroid_function_tests_scaled") if isinstance(ctx.get("thyroid_function_tests_scaled"), dict) else {}
    flags = ctx.get("demographics_and_history_flags") if isinstance(ctx.get("demographics_and_history_flags"), dict) else {}
    vals = {
        "TSH_scaled": float(tests.get("TSH_scaled") or 0.0),
        "T3_scaled": float(tests.get("T3_scaled") or 0.0),
        "TT4_scaled": float(tests.get("TT4_scaled") or 0.0),
        "T4U_scaled": float(tests.get("T4U_scaled") or 0.0),
        "FTI_scaled": float(tests.get("FTI_scaled") or 0.0),
    }
    tsh = vals["TSH_scaled"]
    t3 = vals["T3_scaled"]
    tt4 = vals["TT4_scaled"]
    fti = vals["FTI_scaled"]
    query_hypo = int(flags.get("query_hypothyroid") or 0)
    query_hyper = int(flags.get("query_hyperthyroid") or 0)
    antithyroid = int(flags.get("on_antithyroid_medication") or 0)
    on_thyroxine = int(flags.get("on_thyroxine") or 0)

    hypo_score = 0.0
    hyper_score = 0.0
    normal_score = 0.35

    if tsh >= 0.04:
        hypo_score += 1.2
    elif tsh >= 0.02:
        hypo_score += 0.6
    elif tsh <= 0.001:
        hyper_score += 0.5

    if tt4 <= 0.045:
        hypo_score += 0.6
    if fti <= 0.055:
        hypo_score += 0.6
    if t3 <= 0.008:
        hypo_score += 0.25

    if tt4 >= 0.14:
        hyper_score += 0.55
    if fti >= 0.14:
        hyper_score += 0.55
    if t3 >= 0.03:
        hyper_score += 0.35
    if 0.004 <= tsh <= 0.018 and (tt4 >= 0.075 or fti >= 0.085):
        hyper_score += 0.35

    hypo_score += 0.5 * query_hypo
    hyper_score += 0.5 * query_hyper
    hyper_score += 0.2 * antithyroid
    normal_score += 0.15 * on_thyroxine

    scores = {
        "normal": normal_score,
        "hyperthyroid": hyper_score,
        "hypothyroid": hypo_score,
    }
    label = max(scores, key=scores.get)
    ranked = [
        {"label": k, "score": round(v, 4), "covered_by_tool": True}
        for k, v in sorted(scores.items(), key=lambda item: item[1], reverse=True)
    ]
    confidence = max(0.34, min(0.9, 0.34 + ranked[0]["score"] * 0.18))
    return {
        "summary": "Local thyroid-axis diagnostic heuristic from visible scaled thyroid-function tests and visible history flags.",
        "findings": [
            {"thyroid_function_tests_scaled": vals},
            {"history_flags_used": {
                "query_hypothyroid": query_hypo,
                "query_hyperthyroid": query_hyper,
                "on_antithyroid_medication": antithyroid,
                "on_thyroxine": on_thyroxine,
            }},
            {"label_scores": scores},
        ],
        "tags": [f"tool_thyroid_axis_{label}", f"tool_thyroid_conf_{confidence:.2f}"],
        "predicted_label": label,
        "recommended_final_label": label,
        "recommended_final_confidence": round(confidence, 4),
        "label_candidates": ranked,
        "evidence_strength": "moderate",
        "label_coverage": "exact",
        "domain_match": "ehr_thyroid",
        "recommended_use": "primary_if_consistent",
        "calibration_note": "Heuristic thyroid-axis classifier; useful as local evidence but not externally calibrated.",
        "class_bias_risk": "uses visible scaled features and history flags only; monitor normal-class overuse",
        "input_visible_only": True,
        "gold_label_used": False,
        "future_cases_used": False,
    }


def _compare_checkup_history(case: Dict[str, Any]) -> Dict[str, Any]:
    ctx = _ctx(case)
    findings: List[Dict[str, Any]] = []
    tags: List[str] = []
    for key, v in flatten_values(ctx).items():
        if not key.lower().endswith("trend_last_minus_first"):
            continue
        try:
            trend = float(v)
        except Exception:
            continue
        base = key.rsplit(".", 1)[0]
        direction = "increasing" if trend > 0 else ("decreasing" if trend < 0 else "stable")
        magnitude = abs(trend)
        findings.append({
            "indicator": base,
            "trend_last_minus_first": trend,
            "direction": direction,
            "magnitude": magnitude,
        })
        if magnitude > 0:
            tags.append(f"trend_{base}_{direction}"[:120])
    return {
        "summary": "Compared first-to-last values in visible first-48h summaries to identify physiologic trends.",
        "findings": findings[:20],
        "tags": tags[:30],
    }


def _sofa_like_proxy(case: Dict[str, Any]) -> Dict[str, Any]:
    ctx = _ctx(case)
    vals = flatten_values(ctx)
    points = 0
    components: List[Dict[str, Any]] = []

    def add(name: str, pts: int, evidence: str) -> None:
        nonlocal points
        points += pts
        components.append({"component": name, "points": pts, "evidence": evidence})

    for key, v in vals.items():
        lk = key.lower()
        try:
            fv = float(v)
        except Exception:
            continue
        if lk.endswith("gcs.min") or lk.endswith("gcs.mean") or lk.endswith("gcs.last"):
            if fv <= 8:
                add("neurologic", 2, f"{key}={fv} <= 8")
                break
    cr = _get_path(ctx, "Creatinine.last") or _get_path(ctx, "Creatinine.max") or _get_path(ctx, "Creatinine.mean")
    bun = _get_path(ctx, "BUN.last") or _get_path(ctx, "BUN.max") or _get_path(ctx, "BUN.mean")
    urine_last = _get_path(ctx, "Urine.last")
    urine_min = _get_path(ctx, "Urine.min")
    if cr is not None and cr >= 2.0:
        add("renal", 2, f"creatinine={cr} >= 2.0")
    elif (bun is not None and bun >= 30) or (urine_last is not None and urine_last < 50) or (urine_min is not None and urine_min < 30):
        add("renal", 1, f"BUN={bun}, urine_last={urine_last}, urine_min={urine_min}")
    platelets = _get_path(ctx, "Platelets.last") or _get_path(ctx, "Platelets.min") or _get_path(ctx, "Platelets.mean")
    if platelets is not None and platelets < 100:
        add("coagulation", 2, f"platelets={platelets} < 100")
    elif platelets is not None and platelets < 150:
        add("coagulation", 1, f"platelets={platelets} < 150")
    map_min = _get_path(ctx, "MAP.min")
    if map_min is not None and map_min < 65:
        add("circulation", 1, f"MAP.min={map_min} < 65")
    hr_mean = _get_path(ctx, "HR.mean")
    temp_max = _get_path(ctx, "Temp.max")
    if (hr_mean is not None and hr_mean >= 120) or (temp_max is not None and temp_max >= 39):
        add("systemic_stress", 1, f"HR.mean={hr_mean}, Temp.max={temp_max}")
    tags = [f"tool_sofa_points_{points}"]
    tags.extend([f"tool_sofa_component_{c['component']}" for c in components])
    return {
        "summary": f"SOFA-like organ-dysfunction component score={points}; this is a visible physiology summary, not a direct low/moderate/high label.",
        "findings": components,
        "tags": tags[:30],
        "proxy_points": points,
    }
