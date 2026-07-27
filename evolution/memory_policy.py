"""
L4 memory policy helpers.

This module keeps memory writeback and retrieval rules deterministic. The goal is
to make verified case memory useful without letting low-quality, artifact-driven,
or contradictory memories dominate later predictions.
"""
from __future__ import annotations

import re
import json
from collections import Counter
from copy import deepcopy
from typing import Any, Dict, Iterable, List, Optional, Tuple


ARTIFACT_KEYWORDS = {
    "brightness", "brightness_mean", "contrast", "contrast_proxy", "sharpness",
    "sharpness_proxy", "blur", "possible_blur", "low_contrast", "image_quality",
    "quality metric", "metadata_summarizer", "visible_metadata_summarizer",
    "illumination", "lighting", "光照", "亮度", "对比度", "清晰度", "模糊",
    "图像质量",
}

STRUCTURED_EVIDENCE_KEYWORDS = {
    "tsh", "t3", "tt4", "t4u", "fti", "thyroid", "hba1c", "ldl", "hdl",
    "prs", "mutation", "variant", "protein", "gene",
}

WEAK_ULTRASOUND_KEYWORDS = {
    "mild echogenicity", "increased echogenicity", "echogenicity", "brightness",
    "coarse echo", "轻度", "回声增强", "回声",
}

CONSERVATIVE_POSITIVE_TASKS = {
    "structured_thyroid_diagnosis",
    "structured_readmission_prediction",
    "structured_severity_prediction",
    "omics_prediction",
}

CONFLICT_SENSITIVE_TASKS = {
    "liver_ultrasound_classification",
    "ct_nodule_classification",
}


def normalize_episode(episode: Dict[str, Any]) -> Dict[str, Any]:
    """Return a schema-enriched copy of an episode."""
    ep = deepcopy(episode) if isinstance(episode, dict) else {}

    raw_dataset = ep.get("dataset")
    raw_modality = ep.get("modality") or (ep.get("visible_metadata") or {}).get("modality") if isinstance(ep.get("visible_metadata"), dict) else ep.get("modality")
    raw_task_family = ep.get("task_family")
    dataset = infer_dataset(ep)
    modality = infer_modality(ep)
    task_family = infer_task_family(ep, dataset=dataset, modality=modality)
    polarity = infer_memory_polarity(ep)
    if ep.get("outcome_correct") is None:
        if polarity.startswith("positive"):
            ep["outcome_correct"] = True
        elif polarity.startswith("negative"):
            ep["outcome_correct"] = False
    artifact_risk, artifact_notes = detect_artifact_risk(ep)
    evidence_strength = estimate_evidence_strength(ep, artifact_risk=artifact_risk)
    memory_quality = estimate_memory_quality(
        ep,
        task_family=task_family,
        modality=modality,
        artifact_risk=artifact_risk,
    )
    retrieval_policy, retrieval_notes = decide_retrieval_policy(
        ep,
        polarity=polarity,
        memory_quality=memory_quality,
        evidence_strength=evidence_strength,
        artifact_risk=artifact_risk,
        task_family=task_family,
    )

    if raw_dataset and dataset and str(raw_dataset) != dataset:
        ep.setdefault("raw_dataset", raw_dataset)
    if raw_modality and modality and str(raw_modality) != modality:
        ep.setdefault("raw_modality", raw_modality)
    if raw_task_family and task_family and str(raw_task_family) != task_family:
        ep.setdefault("raw_task_family", raw_task_family)

    ep["dataset"] = dataset
    ep["task_family"] = task_family
    ep["modality"] = modality
    ep["memory_polarity"] = polarity
    ep["memory_quality"] = memory_quality
    ep["evidence_strength"] = evidence_strength
    ep["artifact_risk"] = artifact_risk
    ep["retrieval_policy"] = retrieval_policy
    ep["retrieval_notes"] = list(dict.fromkeys(artifact_notes + retrieval_notes))
    if not ep.get("evidence_tags"):
        ep["evidence_tags"] = extract_evidence_tags(ep)
    return ep


def infer_dataset(ep: Dict[str, Any]) -> str:
    if ep.get("dataset"):
        return canonicalize_dataset(ep["dataset"])
    visible = ep.get("visible_metadata")
    if isinstance(visible, dict) and visible.get("dataset"):
        return canonicalize_dataset(visible["dataset"])

    text = _episode_text(ep)
    tags = " ".join(_as_list(ep.get("tags")))
    combined = f"{text} {tags}".lower()
    if "uci_dia" in combined or "diabetes_30day_readmission" in combined:
        return "UCI_Diabetes_Readmission"
    if "physionet" in combined or "sofa" in combined:
        return "PhysioNet2012_SOFA"
    if "deeploc" in combined:
        return "DeepLoc"
    if "geneturing" in combined or "genegpt" in combined:
        return "GeneTuring"
    if "mlomics" in combined or "gs-brca" in combined:
        return "MLOmics"
    if "proteingym" in combined:
        return "ProteinGym"
    if "isic" in combined:
        return "ISIC2019"
    if "pad-ufes" in combined or "pad_ufes" in combined:
        return "PAD-UFES-20"
    if "dermamnist" in combined:
        return "MedMNIST_DermaMNIST"
    if "breastmnist" in combined:
        return "MedMNIST_BreastMNIST"
    if "msd_task01" in combined or "braintumour" in combined or "brain tumour" in combined:
        return "MSD_Task01_BrainTumour"
    if "msd_task06" in combined or "lung" in combined:
        return "MSD_Task06_Lung"
    if "odir" in combined:
        return "ODIR-5K"
    if "behsof" in combined or "nafld" in combined:
        return "BEHSOF"
    if "nodulemnist" in combined:
        return "MedMNIST_NoduleMNIST3D"
    if "thyroid" in combined:
        return "UCI_Thyroid"
    return ""


def infer_modality(ep: Dict[str, Any]) -> str:
    dataset = infer_dataset(ep)
    dataset_low = dataset.lower()
    if dataset in {"UCI_Thyroid", "UCI_Diabetes_Readmission", "PhysioNet2012_SOFA"}:
        return "structured_ehr"
    if dataset_low in {"deeploc", "geneturing", "mlomics", "proteingym"}:
        return "omics"
    if dataset in {"ISIC2019", "PAD-UFES-20", "MedMNIST_DermaMNIST"}:
        return "dermatology_image"
    if dataset == "ODIR-5K":
        return "fundus_image"
    if dataset in {"BEHSOF", "MedMNIST_BreastMNIST"}:
        return "ultrasound_image"
    if dataset in {"MedMNIST_NoduleMNIST3D", "MSD_Task06_Lung"}:
        return "ct_image"
    if dataset == "MSD_Task01_BrainTumour":
        return "mri_image"

    if ep.get("modality"):
        return canonicalize_modality(ep["modality"])
    visible = ep.get("visible_metadata")
    if isinstance(visible, dict) and visible.get("modality"):
        return canonicalize_modality(visible["modality"])

    text = _episode_text(ep).lower()
    if "fundus" in text or "odir" in text or "眼底" in text:
        return "fundus_image"
    if "ultrasound" in text or "behsof" in text or "超声" in text:
        return "ultrasound_image"
    if "thyroid" in text or "tsh" in text or "甲状腺" in text:
        return "structured_ehr"
    if _has_token(text, "ct") or "computed tomography" in text or "nodule" in text or "结节" in text:
        return "ct_image"
    if "mri" in text or "magnetic resonance" in text or "核磁" in text:
        return "mri_image"
    if "dermoscopy" in text or "dermatology" in text or "skin lesion" in text or "皮肤" in text:
        return "dermatology_image"
    if "protein" in text or "gene" in text or "variant" in text or "组学" in text:
        return "omics"
    return ""


def infer_task_family(ep: Dict[str, Any], dataset: str = "", modality: str = "") -> str:
    text = f"{dataset} {modality} {_episode_text(ep)}".lower()
    dataset_low = str(dataset or "").lower()
    if dataset_low in {"isic2019", "pad-ufes-20", "medmnist_dermamnist"}:
        return "dermatology_image_classification"
    if dataset_low == "uci_diabetes_readmission" or "diabetes_30day_readmission" in text:
        return "structured_readmission_prediction"
    if dataset_low == "physionet2012_sofa" or "sofa" in text:
        return "structured_severity_prediction"
    if dataset_low in {"deeploc", "geneturing", "mlomics", "proteingym"}:
        return "omics_prediction"
    if "odir" in text or "fundus" in text:
        return "fundus_classification"
    if "behsof" in text or "nafld" in text or "abdominal_ultrasound" in text:
        return "liver_ultrasound_classification"
    if "thyroid" in text or "tsh" in text:
        return "structured_thyroid_diagnosis"
    if "nodulemnist" in text or "nodule" in text:
        return "ct_nodule_classification"
    if "ultrasound" in text:
        return "ultrasound_classification"
    if _has_token(text, "ct") or "computed tomography" in text:
        return "ct_classification"
    if "mri" in text:
        return "mri_classification"
    if "protein" in text or "gene" in text or "variant" in text:
        return "omics_prediction"
    return "medical_case"


def canonicalize_dataset(value: Any) -> str:
    text = str(value or "").strip()
    low = text.lower()
    if "uci_dia" in low or "diabetes_30day_readmission" in low or "readmission" in low:
        return "UCI_Diabetes_Readmission"
    if "physionet" in low or "sofa" in low:
        return "PhysioNet2012_SOFA"
    if "deeploc" in low:
        return "DeepLoc"
    if "geneturing" in low or "genegpt" in low:
        return "GeneTuring"
    if "mlomics" in low or "gs-brca" in low:
        return "MLOmics"
    if "proteingym" in low:
        return "ProteinGym"
    if "isic" in low:
        return "ISIC2019"
    if "pad-ufes" in low or "pad_ufes" in low:
        return "PAD-UFES-20"
    if "dermamnist" in low:
        return "MedMNIST_DermaMNIST"
    if "breastmnist" in low:
        return "MedMNIST_BreastMNIST"
    if "msd_task01" in low or "braintumour" in low or "brain tumour" in low:
        return "MSD_Task01_BrainTumour"
    if "msd_task06" in low or "lung" in low:
        return "MSD_Task06_Lung"
    if "odir" in low:
        return "ODIR-5K"
    if "behsof" in low or "nafld" in low:
        return "BEHSOF"
    if "nodulemnist" in low:
        return "MedMNIST_NoduleMNIST3D"
    if "thyroid" in low or "uci_thyroid" in low:
        return "UCI_Thyroid"
    return text


def canonicalize_modality(value: Any) -> str:
    text = str(value or "").strip()
    low = text.lower()
    if "fundus" in low or "眼底" in low:
        return "fundus_image"
    if "ultrasound" in low or "超声" in low:
        return "ultrasound_image"
    if _has_token(low, "ct") or "computed tomography" in low:
        return "ct_image"
    if "mri" in low or "magnetic resonance" in low or "核磁" in low:
        return "mri_image"
    if "dermoscopy" in low or "dermatology" in low or "skin" in low or "皮肤" in low:
        return "dermatology_image"
    if "protein" in low or "gene" in low or "variant" in low or "omics" in low or "组学" in low:
        return "omics"
    if "structured" in low or "ehr" in low or "clinical" in low or "thyroid" in low:
        return "structured_ehr"
    return text


def infer_memory_polarity(ep: Dict[str, Any]) -> str:
    polarity = str(ep.get("memory_polarity") or "").strip()
    if polarity:
        return polarity
    outcome = ep.get("outcome_correct")
    if outcome is True:
        return "positive_success"
    if outcome is False:
        return "negative_failure"
    outcome_text = str(ep.get("outcome") or "").strip().lower()
    if outcome_text in {"correct", "success", "true", "matched"}:
        return "positive_success"
    if outcome_text in {"wrong", "incorrect", "failure", "false", "mismatch"}:
        return "negative_failure"
    predicted = ep.get("predicted_label")
    verified = ep.get("verified_label") or ep.get("gold_label") or ep.get("label")
    if predicted not in (None, "") and verified not in (None, ""):
        return "positive_success" if str(predicted).strip() == str(verified).strip() else "negative_failure"
    return "unverified"


def extract_evidence_tags(ep: Dict[str, Any]) -> List[str]:
    tags = []
    for key in ("evidence_tags", "tags"):
        tags.extend(_as_list(ep.get(key)))

    visible = ep.get("visible_metadata")
    if isinstance(visible, dict):
        for key, value in visible.items():
            if value in (None, "", False):
                continue
            tags.append(f"{key}={value}")

    text = _episode_text(ep).lower()
    for token in STRUCTURED_EVIDENCE_KEYWORDS:
        if _keyword_in_text(text, token):
            tags.append(token)

    return _dedupe_clean(tags)


def estimate_memory_quality(
    ep: Dict[str, Any],
    task_family: str = "",
    modality: str = "",
    artifact_risk: str = "low",
) -> float:
    existing = _safe_float(ep.get("memory_quality"))
    if existing is not None:
        return _clamp(existing)

    writeback_quality = _safe_float(ep.get("writeback_quality"))
    if writeback_quality is not None:
        quality = writeback_quality
    else:
        quality = 0.45
        if ep.get("outcome_correct") is not None:
            quality += 0.20
        if _main_lesson(ep):
            quality += 0.12
        if task_family and task_family != "medical_case":
            quality += 0.08
        if modality:
            quality += 0.05
        if len(extract_evidence_tags(ep)) >= 3:
            quality += 0.10

    if not _main_lesson(ep):
        if task_family in CONSERVATIVE_POSITIVE_TASKS and ep.get("outcome_correct") is not None:
            quality -= 0.08
        else:
            quality -= 0.20
    if artifact_risk == "high":
        quality -= 0.20
    elif artifact_risk == "medium":
        quality -= 0.08
    if get_tool_helpfulness(ep) in {"harmful", "harmful_or_unhelpful"}:
        quality -= 0.10

    return round(_clamp(quality), 3)


def estimate_evidence_strength(ep: Dict[str, Any], artifact_risk: str = "low") -> str:
    existing = str(ep.get("evidence_strength") or "").strip().lower()
    if existing in {"weak", "medium", "strong"}:
        return existing

    text = _episode_text(ep).lower()
    tags = [str(t).lower() for t in extract_evidence_tags(ep)]
    tag_text = " ".join(tags)

    if artifact_risk == "high":
        return "weak"
    if any(_keyword_in_text(tag_text, k) or _keyword_in_text(text, k) for k in STRUCTURED_EVIDENCE_KEYWORDS):
        return "strong"
    if any(k in text for k in WEAK_ULTRASOUND_KEYWORDS):
        return "weak"
    if len(tags) >= 5:
        return "medium"
    if _main_lesson(ep):
        return "medium"
    return "weak"


def detect_artifact_risk(ep: Dict[str, Any]) -> Tuple[str, List[str]]:
    text = _episode_text(ep).lower()
    tools = [str(t).lower() for t in _as_list(ep.get("tools_used")) + _as_list(ep.get("tool_calls_used"))]
    notes = []

    artifact_hits = [kw for kw in ARTIFACT_KEYWORDS if kw.lower() in text]
    if any("image_quality" in t for t in tools):
        artifact_hits.append("image_quality_tool")

    tool_helpfulness = get_tool_helpfulness(ep)
    if artifact_hits and tool_helpfulness in {"harmful", "harmful_or_unhelpful"}:
        notes.append("artifact-linked tool evidence was harmful or unhelpful")
        return "high", notes
    if artifact_hits and _is_artifact_only_lesson(ep):
        notes.append("lesson appears dominated by image-quality or metadata features")
        return "high", notes
    if artifact_hits:
        notes.append("contains image-quality or metadata artifact cues")
        return "medium", notes
    return "low", notes


def decide_retrieval_policy(
    ep: Dict[str, Any],
    polarity: str,
    memory_quality: float,
    evidence_strength: str,
    artifact_risk: str,
    task_family: str = "",
) -> Tuple[str, List[str]]:
    notes = []
    if memory_quality < 0.25:
        return "do_not_retrieve", ["memory quality below retrieval threshold"]

    if polarity.startswith("negative"):
        if artifact_risk == "high":
            notes.append("negative memory should only warn against artifact-driven reasoning")
        return "warning_only", notes

    if polarity.startswith("positive"):
        if artifact_risk == "high":
            return "warning_only", ["positive memory is artifact dominated; do not use as label evidence"]
        if task_family in CONSERVATIVE_POSITIVE_TASKS and memory_quality >= 0.45:
            if evidence_strength == "weak":
                notes.append("verified structured/omics positive retained despite weak extracted lesson")
            return "positive_precedent", notes
        if evidence_strength == "weak" and memory_quality < 0.60:
            return "warning_only", ["weak evidence; use only as soft context"]
        return "positive_precedent", notes

    return "reference_only", ["unverified memory; do not use as decisive evidence"]


def get_tool_helpfulness(ep: Dict[str, Any]) -> str:
    explicit = str(ep.get("tool_helpfulness") or "").strip().lower()
    if explicit:
        return explicit

    tools_useful = ep.get("tools_useful")
    if not isinstance(tools_useful, dict) or not tools_useful:
        return "unknown"

    values = list(tools_useful.values())
    if any(v is True for v in values):
        return "helpful"
    if all(v is False for v in values):
        if ep.get("outcome_correct") is False:
            return "harmful_or_unhelpful"
        return "neutral"
    return "unknown"


def score_memory_for_query(ep: Dict[str, Any], query_context: Dict[str, Any]) -> Tuple[float, List[str]]:
    ep = normalize_episode(ep)
    if ep.get("retrieval_policy") == "do_not_retrieve":
        return 0.0, ["filtered: do_not_retrieve"]

    reasons = []
    score = 0.0

    query_dataset = str(query_context.get("dataset") or "").lower()
    query_modality = str(query_context.get("modality") or "").lower()
    query_task_family = str(query_context.get("task_family") or "").lower()
    query_disease = str(query_context.get("disease") or "").lower()
    key_features = {str(x).lower() for x in _as_list(query_context.get("key_features"))}

    ep_dataset = str(ep.get("dataset") or "").lower()
    ep_modality = str(ep.get("modality") or "").lower()
    ep_task_family = str(ep.get("task_family") or "").lower()
    ep_disease = str(ep.get("disease") or "").lower()

    if query_task_family and ep_task_family == query_task_family:
        score += 8
        reasons.append("same_task_family")
    elif query_task_family and ep_task_family and ep_task_family != query_task_family:
        score -= 6
        reasons.append("different_task_family")

    if query_dataset and ep_dataset == query_dataset:
        score += 6
        reasons.append("same_dataset")
    if query_modality and ep_modality == query_modality:
        score += 4
        reasons.append("same_modality")
    if query_disease and ep_disease == query_disease:
        score += 5
        reasons.append("same_disease")

    ep_tags = {str(x).lower() for x in extract_evidence_tags(ep)}
    overlap = key_features & ep_tags
    if overlap:
        score += min(len(overlap), 5) * 2
        reasons.append(f"tag_overlap={len(overlap)}")

    if ep.get("outcome_correct") is not None:
        score += 2
        reasons.append("verified")

    cc = ep.get("confidence_change") if isinstance(ep.get("confidence_change"), dict) else {}
    before = _safe_float(cc.get("before_tools"))
    after = _safe_float(cc.get("after_tools"))
    if before is not None and after is not None:
        conf_lift = abs(after - before)
        if conf_lift >= 0.30:
            score += 2
            reasons.append(f"legacy_confidence_lift={conf_lift:.2f}")

    quality = _safe_float(ep.get("memory_quality")) or 0.0
    score += quality * 4
    reasons.append(f"quality={quality:.2f}")

    strength_bonus = {"strong": 3, "medium": 1.5, "weak": 0}.get(ep.get("evidence_strength"), 0)
    score += strength_bonus
    if strength_bonus:
        reasons.append(f"evidence={ep.get('evidence_strength')}")

    if ep.get("artifact_risk") == "high":
        score -= 3
        reasons.append("artifact_high")
    elif ep.get("artifact_risk") == "medium":
        score -= 1
        reasons.append("artifact_medium")

    if get_tool_helpfulness(ep) in {"harmful", "harmful_or_unhelpful"}:
        score -= 1
        reasons.append("tool_unhelpful")

    if ep.get("retrieval_policy") == "warning_only":
        score -= 0.5
        reasons.append("warning_only")

    return round(max(score, 0.0), 3), reasons


def select_balanced_memories(scored: List[Tuple[float, Dict[str, Any]]], max_results: int = 8) -> List[Dict[str, Any]]:
    """Select a small set while preserving positive/negative balance."""
    positives = []
    negative_warnings = []
    other_warnings = []
    others = []
    for score, ep in sorted(scored, key=lambda item: item[0], reverse=True):
        ep = deepcopy(ep)
        ep["_retrieval_score"] = score
        if ep.get("retrieval_policy") == "positive_precedent":
            positives.append(ep)
        elif str(ep.get("memory_polarity", "")).startswith("negative"):
            negative_warnings.append(ep)
        elif ep.get("retrieval_policy") == "warning_only":
            other_warnings.append(ep)
        else:
            others.append(ep)

    if max_results <= 0:
        return []

    dominant_task = _dominant_task_family(scored)
    if dominant_task in CONSERVATIVE_POSITIVE_TASKS:
        pos_limit = max(1, int(round(max_results * 0.75)))
    elif dominant_task in CONFLICT_SENSITIVE_TASKS:
        pos_limit = max(1, max_results // 2)
    else:
        pos_limit = max(1, int(round(max_results * 0.65)))
    warn_limit = max(1, max_results - pos_limit)
    warnings = negative_warnings + other_warnings
    selected = _take_label_diverse(positives, pos_limit) + _take_label_diverse(warnings, warn_limit)

    remaining_slots = max_results - len(selected)
    if remaining_slots > 0:
        selected_ids = {id(ep) for ep in selected}
        leftovers = [ep for ep in positives + warnings + others if id(ep) not in selected_ids]
        selected.extend(_take_label_diverse(leftovers, remaining_slots))

    return sorted(selected[:max_results], key=lambda ep: ep.get("_retrieval_score", 0), reverse=True)


def _dominant_task_family(scored: List[Tuple[float, Dict[str, Any]]]) -> str:
    task_counts = Counter()
    for _, ep in scored:
        task = normalize_episode(ep).get("task_family", "")
        if task:
            task_counts[task] += 1
    if not task_counts:
        return ""
    return task_counts.most_common(1)[0][0]


def _take_label_diverse(items: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
    if limit <= 0 or not items:
        return []
    buckets: Dict[str, List[Dict[str, Any]]] = {}
    order = []
    for item in items:
        label = _case_label(item) or "unknown"
        if label not in buckets:
            buckets[label] = []
            order.append(label)
        buckets[label].append(item)

    selected = []
    while len(selected) < limit and any(buckets.values()):
        for label in list(order):
            bucket = buckets.get(label) or []
            if not bucket:
                continue
            selected.append(bucket.pop(0))
            if len(selected) >= limit:
                break
    return selected


def analyze_retrieval_set(cases: Iterable[Dict[str, Any]], bias_threshold: float = 0.75) -> Dict[str, Any]:
    normalized = [normalize_episode(c) for c in cases]
    positives = [c for c in normalized if c.get("retrieval_policy") == "positive_precedent"]
    warnings = [
        c for c in normalized
        if c.get("retrieval_policy") == "warning_only" or str(c.get("memory_polarity", "")).startswith("negative")
    ]

    label_counts = Counter(_case_label(c) for c in normalized if _case_label(c))
    total_labels = sum(label_counts.values())
    class_bias_warning = ""
    if total_labels >= 3:
        label, count = label_counts.most_common(1)[0]
        ratio = count / total_labels
        if ratio >= bias_threshold:
            class_bias_warning = (
                f"召回记忆中 `{label}` 占比 {count}/{total_labels} ({ratio:.0%})，"
                "存在类别偏置风险，不能直接按多数类经验下结论。"
            )

    conflict_warnings = _detect_conflicts(normalized)
    filtered_out = [c for c in normalized if c.get("retrieval_policy") == "do_not_retrieve"]

    return {
        "positive_precedents": positives,
        "failure_warnings": warnings,
        "conflict_warnings": conflict_warnings,
        "class_bias_warning": class_bias_warning,
        "label_distribution": dict(label_counts),
        "filtered_out": filtered_out,
    }


def format_retrieval_context(cases: Iterable[Dict[str, Any]]) -> str:
    analysis = analyze_retrieval_set(cases)
    lines = ["[L4 Memory Retrieval]"]

    positives = analysis["positive_precedents"]
    if positives:
        lines.append("\nPositive precedents（可复用成功经验，只能作为辅助证据）:")
        for idx, case in enumerate(positives, 1):
            lines.append(_format_case_line(idx, case, positive=True))

    warnings = analysis["failure_warnings"]
    if warnings:
        lines.append(
            "\nFailure warnings（历史失败模式；previous_wrong_pred 是历史错误答案，"
            "不能模仿，也不能因为该词频繁出现就选择它）:"
        )
        for idx, case in enumerate(warnings, 1):
            lines.append(_format_case_line(idx, case, positive=False))

    if analysis["conflict_warnings"]:
        lines.append("\nConflict warnings（冲突证据）:")
        for warning in analysis["conflict_warnings"]:
            lines.append(f"- {warning}")

    if analysis["class_bias_warning"]:
        lines.append("\nClass-bias warning（类别偏置）:")
        lines.append(f"- {analysis['class_bias_warning']}")

    if not positives and not warnings and not analysis["conflict_warnings"]:
        lines.append("未找到可安全注入的相似病例经验。")

    return "\n".join(lines)


def is_distillable_episode(ep: Dict[str, Any], min_quality: float = 0.60) -> bool:
    ep = normalize_episode(ep)
    if ep.get("outcome_correct") is None:
        return False
    if ep.get("retrieval_policy") == "do_not_retrieve":
        return False
    if (_safe_float(ep.get("memory_quality")) or 0.0) < min_quality:
        return False
    if ep.get("artifact_risk") == "high":
        return False
    return True


def _detect_conflicts(cases: List[Dict[str, Any]]) -> List[str]:
    warnings = []
    if not cases:
        return warnings

    positive_labels = {_case_label(c) for c in cases if c.get("retrieval_policy") == "positive_precedent"}
    warning_labels = {_case_label(c) for c in cases if c.get("retrieval_policy") == "warning_only"}
    positive_labels.discard("")
    warning_labels.discard("")

    if positive_labels and warning_labels and positive_labels != warning_labels:
        warnings.append(
            "同一批召回记忆同时包含成功经验和失败警告，且 verified label 不一致；"
            "应把重叠特征视为弱证据，必须结合当前样本的独立证据交叉验证。"
        )

    tag_to_labels: Dict[str, set] = {}
    for case in cases:
        label = _case_label(case)
        if not label:
            continue
        for tag in extract_evidence_tags(case):
            key = str(tag).lower()
            if len(key) < 3:
                continue
            tag_to_labels.setdefault(key, set()).add(label)

    for tag, labels in sorted(tag_to_labels.items()):
        if len(labels) >= 2:
            warnings.append(
                f"证据标签 `{tag}` 在历史记忆中指向多个标签 {sorted(labels)}，"
                "该标签不能单独作为诊断依据。"
            )
            if len(warnings) >= 3:
                break
    return warnings


def _format_case_line(idx: int, case: Dict[str, Any], positive: bool) -> str:
    lesson = _main_lesson(case) or "无可复用经验文本"
    label = _case_label(case) or case.get("disease", "unknown")
    pred = case.get("predicted_label") or case.get("prediction_before_verification") or "?"
    score = case.get("_retrieval_score", "?")
    quality = case.get("memory_quality", "?")
    strength = case.get("evidence_strength", "?")
    artifact = case.get("artifact_risk", "?")
    if positive:
        return (
            f"- support#{idx} verified_label={label}, pred={pred}, score={score}, "
            f"quality={quality}, evidence={strength}, artifact={artifact}: {lesson}"
        )
    lesson = _sanitize_warning_lesson(lesson, pred)
    return (
        f"- warning#{idx} verified_label={label}, previous prediction was wrong, score={score}, "
        f"quality={quality}, evidence={strength}, artifact={artifact}; avoid repeating this error: {lesson}"
    )


def _sanitize_warning_lesson(lesson: str, wrong_pred: Any) -> str:
    text = str(lesson or "")
    pred = str(wrong_pred or "").strip()
    for variant in _label_variants(pred):
        text = re.sub(re.escape(variant), "[previous wrong label]", text, flags=re.IGNORECASE)
    return text


def _label_variants(label: str) -> List[str]:
    label = str(label or "").strip()
    variants = [label] if label and label != "?" else []
    low = label.lower()
    aliases = {
        "malignant": ["恶性", "恶性结节", "恶性病变"],
        "benign": ["良性", "良性结节", "良性病变"],
        "seborrheic keratosis": ["脂溢性角化病"],
        "basal cell carcinoma": ["基底细胞癌"],
        "melanocytic nevus": ["黑素细胞痣", "色素痣"],
        "melanoma": ["黑色素瘤"],
    }
    variants.extend(aliases.get(low, []))
    return [v for v in variants if v]


def _case_label(case: Dict[str, Any]) -> str:
    for key in ("verified_label", "gold_label", "label", "disease"):
        value = case.get(key)
        if value not in (None, ""):
            return str(value)
    return ""


def _main_lesson(ep: Dict[str, Any]) -> str:
    for key in ("key_lesson", "reusable_lesson", "evidence_summary", "why_correct_or_wrong"):
        value = ep.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    raw = ep.get("writeback_raw_output")
    if isinstance(raw, str) and raw.strip():
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = None
        if isinstance(parsed, dict):
            for key in ("reusable_lesson", "case_lesson", "evidence_summary", "why_correct_or_wrong"):
                value = parsed.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
    for item in _as_list(ep.get("memory_items_written")):
        if not isinstance(item, dict):
            continue
        for key in ("key_lesson", "reusable_lesson", "content", "evidence_summary"):
            value = item.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return ""


def _is_artifact_only_lesson(ep: Dict[str, Any]) -> bool:
    lesson = _main_lesson(ep).lower()
    if not lesson:
        return False
    artifact_hits = sum(1 for kw in ARTIFACT_KEYWORDS if kw.lower() in lesson)
    clinical_hits = sum(1 for kw in STRUCTURED_EVIDENCE_KEYWORDS if _keyword_in_text(lesson, kw))
    hallmark_terms = [
        "drusen", "microaneurysm", "hemorrhage", "cup", "disc", "lesion",
        "nodule", "rim", "exudate", "tsh", "t3", "tt4", "fti", "病灶",
        "出血", "渗出", "结节", "杯盘比",
    ]
    hallmark_hits = sum(1 for kw in hallmark_terms if kw in lesson)
    return artifact_hits > 0 and clinical_hits == 0 and hallmark_hits == 0


def _keyword_in_text(text: str, keyword: str) -> bool:
    keyword = keyword.lower()
    if len(keyword) <= 4 or keyword in {"prs"}:
        return re.search(r"(?<![a-z0-9])" + re.escape(keyword) + r"(?![a-z0-9])", text) is not None
    return keyword in text


def _has_token(text: str, token: str) -> bool:
    return re.search(r"(?<![a-z0-9])" + re.escape(token.lower()) + r"(?![a-z0-9])", text.lower()) is not None


def _episode_text(ep: Dict[str, Any]) -> str:
    parts = []

    def visit(value: Any, key: str = "", depth: int = 0) -> None:
        if depth > 3 or key in {"image", "image_bytes", "raw_image"}:
            return
        if isinstance(value, (str, int, float, bool)):
            parts.append(str(value))
        elif isinstance(value, dict):
            for child_key, child_value in value.items():
                visit(child_value, str(child_key), depth + 1)
        elif isinstance(value, list):
            for child in value:
                visit(child, key, depth + 1)

    visit(ep)
    return " ".join(parts)


def _as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, set):
        return list(value)
    return [value]


def _dedupe_clean(values: Iterable[Any]) -> List[str]:
    out = []
    seen = set()
    for value in values:
        item = re.sub(r"\s+", " ", str(value)).strip()
        if not item:
            continue
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def _safe_float(value: Any) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))
