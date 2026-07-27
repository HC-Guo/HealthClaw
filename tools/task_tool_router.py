"""
Task-specific tool router for HealthClaw benchmark/evaluation tasks.

The router separates task selection from tool implementation. It may select
wrappers around external tools, but it should not invent diagnostic rules as a
replacement for a domain tool.
"""
from __future__ import annotations

import re
import os
from typing import Any, Dict, List

from tools.deeploc_tools import deeploc_esm2_lora_classify, deeploc_esm2_lora_status
from tools.fundus_tools import flair_fundus_status, flair_fundus_zero_shot
from tools.gene_reference_tools import geneturing_reference_answer_tool
from tools.liver_ultrasound_tools import liver_ultrasound_steatosis_classify, liver_ultrasound_steatosis_status
from tools.medical_image_slice_tools import (
    brain_mri_siglip_tumor_classify,
    brain_mri_siglip_tumor_status,
    lung_ct_vit_slice_classify,
    lung_ct_vit_slice_status,
)
from tools.medmnist_tools import (
    medmnist_breast_resnet_classify,
    medmnist_breast_resnet_status,
    medmnist_nodule3d_resnet_classify,
    medmnist_nodule3d_resnet_status,
)
from tools.monai_imaging_tools import monai_bundle_status
from tools.multiomics_tools import (
    mlomics_cmob_status,
    mlomics_synthetic_brca_xgb_classify,
    mlomics_synthetic_brca_xgb_status,
)
from tools.protein_reference_tools import esm_local_variant_effect_score, esm_variant_effect_status
from tools.readmission_tools import (
    pyhealth_readmission_status,
    uci_diabetes_xgb_readmission_classify,
    uci_diabetes_xgb_readmission_status,
)
from tools.skin_tools import (
    rg_dermnet_pad_classify,
    rg_dermnet_pad_status,
    skin_isic_efficientnet_classify,
    skin_isic_efficientnet_status,
)
from tools.stage4_ehr_tools import execute_tool as execute_stage4_ehr_tool
from tools.stage4_ehr_tools import route_tools as route_stage4_ehr_tools


ROUTER_VERSION = "healthclaw_task_tool_router_v1"


def _text(case: Dict[str, Any], task_key: str = "") -> str:
    pieces = [
        task_key,
        str(case.get("dataset", "")),
        str(case.get("domain", "")),
        str(case.get("task_name", "")),
        str(case.get("case_id", "")),
        str(case.get("question", "")),
        str(case.get("visible_input", "")),
    ]
    ctx = case.get("visible_clinical_context")
    if isinstance(ctx, dict):
        pieces.extend(str(v) for v in ctx.values() if isinstance(v, (str, int, float)))
    return " ".join(pieces).lower()


def infer_task_family(task_key: str, case: Dict[str, Any]) -> str:
    text = _text(case, task_key)
    domain = str(case.get("domain", "")).lower()
    dataset = str(case.get("dataset", "")).lower()
    task_name = str(case.get("task_name", "")).lower()

    if "geneturing" in text or "genegpt" in text:
        return "gene_qa"
    if "protein" in text or "deeploc" in text or "proteingym" in text:
        return "protein_sequence"
    if "omics" in text or "multiomics" in text or "methylation" in text or "mlo" in dataset:
        return "multiomics"
    if "odir" in text or "fundus" in text or "retina" in text or "ocular" in text:
        return "fundus"
    if "isic" in text or "derma" in text or "pad-ufes" in text or "skin" in text or "lesion" in text:
        return "skin"
    if "breastmnist" in text or "behs" in text or "ultrasound" in text or "超声" in text:
        return "ultrasound"
    if "brain" in text or "mri" in text or "magnetic" in text:
        return "mri"
    if "nodule" in text or "lung ct" in text or "ct_lung" in text or re.search(r"\bct\b|\bcomputed tomography\b", text):
        return "ct"
    if "thyroid" in text or "sofa" in text or "diabetes" in text or "readmission" in text:
        return "ehr"
    if (
        "geneturing" in text
        or "genegpt" in text
        or domain in {"genetics", "genomics", "gene"}
        or re.search(r"\brs\d+\b", text)
        or "snp" in task_name
        or task_name.startswith("gene ")
    ):
        return "gene_qa"
    return "unknown"


def _infer_ehr_task_key(task_key: str, case: Dict[str, Any]) -> str:
    text = _text(case, task_key)
    if "thyroid" in text:
        return "uci_thyroid_diagnosis"
    if "sofa" in text or "physionet" in text or "icu" in text:
        return "physionet2012_sofa_severity"
    if "diabetes" in text or "readmission" in text:
        return "uci_diabetes_readmission"
    return task_key or "ehr"


def route_tools(task_key: str, case: Dict[str, Any], max_tool_calls: int = 3) -> Dict[str, Any]:
    family = infer_task_family(task_key, case)
    text = _text(case, task_key)
    selected: List[str] = []
    candidates: List[Dict[str, Any]] = []
    skipped: List[Dict[str, str]] = []

    def add_candidate(tool_name: str, status: str, source: str, reason: str) -> None:
        candidates.append({
            "tool_name": tool_name,
            "status": status,
            "source": source,
            "reason": reason,
        })

    if family == "gene_qa":
        add_candidate(
            "geneturing_reference_answer_tool",
            "blocked_external_database_lookup",
            "tools.gene_reference_tools + MyGene/MyVariant/Ensembl/HGNC/NCBI",
            "GeneTuring-style questions would benefit from external gene/variant reference lookup, but formal benchmark policy forbids runtime database/search lookup.",
        )
        skipped.append({
            "tool_name": "geneturing_reference_answer_tool",
            "reason": "external database/reference lookup is disabled for no-leakage formal evaluation",
        })
        selected = []
    elif family == "fundus":
        add_candidate("flair_fundus_zero_shot", "available_if_flair_ready", "FLAIR retina vision-language foundation model", "Fundus tasks need retinal foundation-model evidence instead of generic image quality statistics.")
        add_candidate("retfound_fundus_adapter", "planned_external_model", "RETFound/RET-CLIP", "RETFound is a strong retinal foundation model but weights are gated and require HuggingFace access before inference.")
        skipped.append({"tool_name": "code_run.image_quality_metadata", "reason": "Image quality can be fallback evidence but is not disease-specific retinal evidence."})
        selected = ["flair_fundus_zero_shot"]
    elif family == "skin":
        if "pad-ufes" in text or "pad_ufes" in text:
            add_candidate("rg_dermnet_pad_classify", "available_if_weights_ready", "HuggingFace wyctorfogos/rg-dermnet no-metadata PAD-UFES-20 model", "PAD-UFES-20 uses clinical skin photographs; RG-DermNet is PAD-domain-specific and exact-label, but must report source-overlap risk.")
            selected = ["rg_dermnet_pad_classify"]
        else:
            add_candidate("skin_isic_efficientnet_classify", "available_partial_label_overlap", "HuggingFace conan17970/efficientnet-b1-skin-cancer-isic2019", "Skin tasks need lesion classifier evidence; this ISIC2019 EfficientNet covers six common classes but not dermatofibroma/vascular lesion.")
            selected = ["skin_isic_efficientnet_classify"]
        skipped.append({"tool_name": "code_run.visible_metadata_summarizer", "reason": "Metadata summary is supportive only and should not replace a lesion classifier."})
    elif family == "ct":
        text = _text(case, task_key)
        if "nodulemnist" in text:
            add_candidate("medmnist_nodule3d_resnet_classify", "available_if_public_npz_ready", "MedMNIST official experiment weights, NoduleMNIST3D ResNet18-3D", "NoduleMNIST3D case IDs expose split/index, so the public nodulemnist3d.npz raw volume can be used without gold labels when available.")
            add_candidate("monai_bundle_status:ct_lung_nodule_detection", "limited_auxiliary_if_monai_ready", "MONAI Model Zoo lung_nodule_ct_detection", "This real MONAI bundle detects nodules in full CT volumes but is not a direct NoduleMNIST3D malignancy classifier.")
            selected = ["medmnist_nodule3d_resnet_classify"]
        else:
            add_candidate("lung_ct_vit_slice_classify", "available_if_model_ready", "sukhmani1303/lung-cancer-vit-model", "The current MSD lung stream exposes 2D PNG CT slices, so a public 2D lung CT cancer/normal ViT can provide visible-tumor auxiliary evidence.")
            add_candidate("monai_bundle_status:ct_lung_nodule_detection", "available_if_monai_bundle_ready", "MONAI Model Zoo lung_nodule_ct_detection", "Full CT lung tasks can use 3D nodule detection evidence from a real MONAI bundle when the input format matches LUNA16/LIDC-style volumes.")
            selected = ["lung_ct_vit_slice_classify", "monai_bundle_status:ct_lung_nodule_detection"]
        skipped.append({"tool_name": "tools.imaging_tools.ImagingAnalyzer.query", "reason": "Current ImagingAnalyzer is a UKB placeholder and has no task-specific CT inference."})
    elif family == "mri":
        add_candidate("brain_mri_siglip_tumor_classify", "available_if_model_ready", "prithivMLmods/BrainTumor-Classification-Mini", "The current MSD BrainTumour stream exposes 2D multi-sequence PNG panels, so a public 2D brain MRI tumor classifier can provide tumor-presence auxiliary evidence.")
        add_candidate("monai_bundle_status:mri_brats_segmentation", "available_if_monai_bundle_ready", "MONAI Model Zoo brats_mri_segmentation", "Brain MRI tasks need tumor/edema segmentation evidence from a real MONAI bundle.")
        selected = []
        skipped.append({"tool_name": "brain_mri_siglip_tumor_classify", "reason": "This public model predicts no-tumor/tumor type, not BraTS/MSD subregions, and probe evidence showed its probabilities mislead mri_braintumour predictions."})
        skipped.append({"tool_name": "monai_bundle_status:mri_brats_segmentation", "reason": "Current route only exposes bundle availability status, not segmentation inference; 10-case MRI probe showed this status-only context reduced prediction quality."})
        skipped.append({"tool_name": "tools.imaging_tools.ImagingAnalyzer.query", "reason": "Current ImagingAnalyzer is a UKB placeholder and has no task-specific MRI inference."})
    elif family == "ultrasound":
        text = _text(case, task_key)
        if "breastmnist" in text:
            add_candidate("medmnist_breast_resnet_classify", "available_if_weights_ready", "MedMNIST official experiment weights, BreastMNIST ResNet18-224", "BreastMNIST ultrasound can use the official public MedMNIST experiment checkpoint as lesion evidence.")
            selected = ["medmnist_breast_resnet_classify"]
        elif "behs" in text or "nafld" in text or "fatty liver" in text:
            add_candidate("liver_ultrasound_steatosis_classify", "available_if_external_fallback_ready", "Zenodo 1009146 B-mode liver ultrasound dataset + ResNet18 embedding logistic fallback", "No public BEHSOF-compatible checkpoint was found, so use an external-data-only fallback when available; treat it as weak auxiliary evidence.")
            add_candidate("liver_ultrasound_steatosis_status", "status_for_public_checkpoint_search", "LCTI-AnTang/binary_steatosis_classifier candidate", "A stronger B-mode steatosis checkpoint would still be preferable if public weights become available.")
            selected = ["liver_ultrasound_steatosis_classify"]
        else:
            add_candidate("ultrasound_task_adapter", "planned_external_model", "Breast ultrasound / liver ultrasound model candidate", "Ultrasound tasks need modality-specific lesion or steatosis evidence.")
        skipped.append({"tool_name": "code_run.image_qc", "reason": "Quality statistics are not sufficient ultrasound evidence."})
    elif family == "ehr":
        ehr_task_key = _infer_ehr_task_key(task_key, case)
        stage4_routing = route_stage4_ehr_tools(ehr_task_key, case, max_tool_calls=max_tool_calls)
        selected = [f"stage4_ehr:{name}" for name in (stage4_routing.get("selected_tools") or [])]
        add_candidate("stage4_ehr:interpret_indicator", "available_partial", "tools.stage4_ehr_tools", "Existing HealthClaw structured EHR tool; useful for thyroid/SOFA visible indicators and limited diabetes feature summaries.")
        for tool_name in stage4_routing.get("selected_tools") or []:
            if tool_name != "interpret_indicator":
                add_candidate(f"stage4_ehr:{tool_name}", "available_partial", "tools.stage4_ehr_tools", "Existing HealthClaw structured EHR auxiliary tool.")
        if ehr_task_key == "uci_diabetes_readmission":
            add_candidate("uci_diabetes_xgb_readmission_classify", "available_if_model_ready", "analyst-ted/hospital-readmission-prediction XGBoost checkpoint", "Public MIT-licensed UCI Diabetes 30-day readmission XGBoost model with fitted scaler and threshold.")
            selected = ["uci_diabetes_xgb_readmission_classify"]
            add_candidate("pyhealth_readmission_status", "framework_available_pipeline_required", "PyHealth / validated UCI diabetes readmission pipeline", "PyHealth is a framework, not a pretrained readmission model; a strict train/validation/test pipeline is still needed.")
            skipped.append({
                "tool_name": "stage4_ehr:interpret_indicator",
                "reason": "visible EHR indicator summary is auxiliary only and distracted the full-agent diabetes diagnosis",
            })
            skipped.append({
                "tool_name": "pyhealth_readmission_status",
                "reason": "framework status is not a pretrained UCI readmission classifier",
            })
    elif family == "protein_sequence":
        text = _text(case, task_key)
        if "proteingym" in text or "variant" in text or re.search(r"\b[A-Z]\d+[A-Z]\b", text.upper()):
            add_candidate("esm_local_variant_effect_score", "available_if_esm_ready", "FAIR ESM local-window variant effect scoring", "ProteinGym clinical substitutions need protein language-model variant effect evidence; current benchmark exposes local sequence windows, not full proteins.")
            selected = ["esm_local_variant_effect_score"]
        elif "deeploc" in text or "localization" in text:
            add_candidate("deeploc_esm2_lora_classify", "available_partial_sequence", "HuggingFace zq233/deeploc-esm2-lora over facebook/esm2_t6_8M_UR50D", "DeepLoc stream exposes visible N/C-terminal excerpts, so this real ESM2-LoRA classifier can provide partial-sequence localization evidence.")
            selected = ["deeploc_esm2_lora_classify"]
        else:
            add_candidate("deeploc2_or_esm_adapter", "planned_external_model", "DeepLoc 2.x / ESM / ProteinGym", "Protein sequence tasks need localization or variant-effect model evidence.")
    elif family == "multiomics":
        add_candidate("mlomics_synthetic_brca_xgb_classify", "available_if_synthetic_model_ready", "deaneeth/multi-omics-cancer-subtype-classifier synthetic BRCA XGBoost adapter", "No-leakage fallback trained on external synthetic BRCA multi-omics samples when no public compatible CMOB checkpoint is available.")
        add_candidate("mlomics_cmob_status", "framework_available_no_checkpoint", "MLOmics / Cancer-Multi-Omics-Benchmark", "CMOB provides datasets and baselines, but current workspace lacks a compatible pretrained GS-BRCA subtype checkpoint for compressed summaries.")
        selected = ["mlomics_synthetic_brca_xgb_classify", "mlomics_cmob_status"]
    else:
        add_candidate("no_task_specific_tool", "unavailable", "router", "No confident task family detected.")

    selected = selected[:max_tool_calls]
    return {
        "enabled": bool(selected),
        "policy_version": ROUTER_VERSION,
        "task_family": family,
        "candidate_tools": candidates,
        "selected_tools": selected,
        "skipped_tools": skipped,
        "max_tool_calls": max_tool_calls,
        "input_visible_only": True,
    }


def _first_tool_label(result: Dict[str, Any]) -> str:
    top = result.get("top_label_candidate")
    if isinstance(top, dict) and top.get("label") is not None:
        return str(top.get("label"))
    for key in ("predicted_label", "label", "prediction", "recommended_label", "class_name", "top_label", "answer"):
        if result.get(key) is not None:
            return str(result.get(key))
    return ""


def _with_evidence_defaults(tool_name: str, case: Dict[str, Any], task_key: str, result: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(result, dict):
        result = {"status": "success", "tool_name": tool_name, "raw_result": result}
    result.setdefault("tool_name", tool_name)
    result.setdefault("input_visible_only", True)
    result.setdefault("gold_label_used", False)
    result.setdefault("future_cases_used", False)

    labels = {str(x).lower().strip() for x in (case.get("label_options") or [])}
    pred = _first_tool_label(result).lower().strip()
    status = str(result.get("status") or "").lower()
    if "error" in status or "not_ready" in status or "not_available" in status or "unavailable" in status:
        default_strength = "unusable"
        default_use = "ignore"
    elif not pred:
        default_strength = "weak"
        default_use = "ignore"
    elif labels and pred not in labels:
        default_strength = "weak"
        default_use = "auxiliary_only"
    else:
        default_strength = "moderate"
        default_use = "auxiliary"
    if task_key in {"isic2019", "behsof_full", "behsof_balanced"} and default_strength == "moderate":
        default_strength = "moderate_to_strong"
        default_use = "primary_if_consistent"
    result.setdefault("evidence_strength", default_strength)
    result.setdefault("label_coverage", "exact_or_mapped" if pred and (not labels or pred in labels) else "none_or_mismatch")
    result.setdefault("domain_match", infer_task_family(task_key, case))
    result.setdefault("calibration_note", "Local task tool evidence; confidence should not be treated as calibrated unless the tool reports calibration explicitly.")
    result.setdefault(
        "class_bias_risk",
        "known_probe_risk_recheck_on_fixed_20"
        if task_key in {"odir5k", "breastmnist", "nodulemnist3d", "pad_ufes20", "thyroid", "diabetes"}
        else "not_yet_flagged",
    )
    result.setdefault("recommended_use", default_use)
    result.setdefault("leakage_audit", {
        "gold_label_used": False,
        "future_cases_used": False,
        "llm_visible_paths_should_be_redacted_by_eval_harness": True,
    })
    return result


def _execute_tool_impl(tool_name: str, case: Dict[str, Any], task_key: str = "") -> Dict[str, Any]:
    if tool_name == "geneturing_reference_answer_tool":
        enable_alignment = str(os.environ.get("HEALTHCLAW_ENABLE_REMOTE_ALIGNMENT", "")).lower() in {"1", "true", "yes", "on"}
        try:
            alignment_wait = int(os.environ.get("HEALTHCLAW_REMOTE_ALIGNMENT_WAIT_SECONDS", "75"))
        except ValueError:
            alignment_wait = 75
        return geneturing_reference_answer_tool(
            question=str(case.get("question") or case.get("visible_input") or ""),
            task_name=str(case.get("task_name") or task_key or ""),
            species="human",
            run_remote_alignment=enable_alignment,
            remote_alignment_max_wait_seconds=alignment_wait,
        )
    if tool_name == "flair_fundus_zero_shot":
        image_path = str(case.get("image_path_abs") or case.get("image_path") or "")
        label_options = case.get("label_options") or []
        if not image_path:
            return flair_fundus_status()
        return flair_fundus_zero_shot(
            image_path=image_path,
            label_options=label_options if isinstance(label_options, list) else [],
            source_dir=str(case.get("flair_source_dir") or "") or None,
            prompt_mode=str(case.get("prompt_mode") or "domain_knowledge"),
        )
    if tool_name == "esm_local_variant_effect_score":
        visible_input = str(case.get("visible_input") or "")
        if not visible_input:
            return esm_variant_effect_status(source_dir=str(case.get("esm_source_dir") or "") or None)
        return esm_local_variant_effect_score(
            visible_input=visible_input,
            source_dir=str(case.get("esm_source_dir") or "") or None,
            model_name=str(case.get("esm_model_name") or "esm2_t6_8M_UR50D"),
        )
    if tool_name == "deeploc_esm2_lora_classify":
        visible_input = str(case.get("visible_input") or "")
        label_options = case.get("label_options") or []
        if not visible_input:
            return deeploc_esm2_lora_status(model_dir=str(case.get("deeploc_model_dir") or "") or None)
        return deeploc_esm2_lora_classify(
            visible_input=visible_input,
            label_options=label_options if isinstance(label_options, list) else [],
            model_dir=str(case.get("deeploc_model_dir") or "") or None,
        )
    if tool_name == "skin_isic_efficientnet_classify":
        image_path = str(case.get("image_path_abs") or case.get("image_path") or "")
        label_options = case.get("label_options") or []
        if not image_path:
            return skin_isic_efficientnet_status(model_dir=str(case.get("skin_model_dir") or "") or None)
        return skin_isic_efficientnet_classify(
            image_path=image_path,
            label_options=label_options if isinstance(label_options, list) else [],
            model_dir=str(case.get("skin_model_dir") or "") or None,
        )
    if tool_name == "rg_dermnet_pad_classify":
        image_path = str(case.get("image_path_abs") or case.get("image_path") or "")
        label_options = case.get("label_options") or []
        if not image_path:
            return rg_dermnet_pad_status(model_dir=str(case.get("rg_dermnet_model_dir") or "") or None)
        return rg_dermnet_pad_classify(
            image_path=image_path,
            label_options=label_options if isinstance(label_options, list) else [],
            model_dir=str(case.get("rg_dermnet_model_dir") or "") or None,
        )
    if tool_name == "medmnist_breast_resnet_classify":
        image_path = str(case.get("image_path_abs") or case.get("image_path") or "")
        label_options = case.get("label_options") or []
        if not image_path:
            return medmnist_breast_resnet_status(model_dir=str(case.get("medmnist_model_dir") or "") or None)
        return medmnist_breast_resnet_classify(
            image_path=image_path,
            label_options=label_options if isinstance(label_options, list) else [],
            model_dir=str(case.get("medmnist_model_dir") or "") or None,
        )
    if tool_name == "medmnist_nodule3d_resnet_status":
        return medmnist_nodule3d_resnet_status(model_dir=str(case.get("medmnist_model_dir") or "") or None)
    if tool_name == "medmnist_nodule3d_resnet_classify":
        return medmnist_nodule3d_resnet_classify(
            case_id=str(case.get("case_id") or ""),
            model_dir=str(case.get("medmnist_model_dir") or "") or None,
            data_dir=str(case.get("medmnist_data_dir") or "") or None,
            label_options=case.get("label_options") if isinstance(case.get("label_options"), list) else [],
        )
    if tool_name == "liver_ultrasound_steatosis_status":
        return liver_ultrasound_steatosis_status(model_dir=str(case.get("liver_steatosis_model_dir") or "") or None)
    if tool_name == "liver_ultrasound_steatosis_classify":
        image_path = str(case.get("image_path_abs") or case.get("image_path") or "")
        label_options = case.get("label_options") or []
        if not image_path:
            return liver_ultrasound_steatosis_status(model_dir=str(case.get("liver_steatosis_model_dir") or "") or None)
        return liver_ultrasound_steatosis_classify(
            image_path=image_path,
            label_options=label_options if isinstance(label_options, list) else [],
            model_dir=str(case.get("liver_steatosis_model_dir") or "") or None,
        )
    if tool_name == "lung_ct_vit_slice_status":
        return lung_ct_vit_slice_status(model_dir=str(case.get("medical_image_model_dir") or "") or None)
    if tool_name == "lung_ct_vit_slice_classify":
        image_path = str(case.get("image_path_abs") or case.get("image_path") or "")
        label_options = case.get("label_options") or []
        if not image_path:
            return lung_ct_vit_slice_status(model_dir=str(case.get("medical_image_model_dir") or "") or None)
        return lung_ct_vit_slice_classify(
            image_path=image_path,
            label_options=label_options if isinstance(label_options, list) else [],
            model_dir=str(case.get("medical_image_model_dir") or "") or None,
        )
    if tool_name == "brain_mri_siglip_tumor_status":
        return brain_mri_siglip_tumor_status(model_dir=str(case.get("medical_image_model_dir") or "") or None)
    if tool_name == "brain_mri_siglip_tumor_classify":
        image_path = str(case.get("image_path_abs") or case.get("image_path") or "")
        label_options = case.get("label_options") or []
        if not image_path:
            return brain_mri_siglip_tumor_status(model_dir=str(case.get("medical_image_model_dir") or "") or None)
        return brain_mri_siglip_tumor_classify(
            image_path=image_path,
            label_options=label_options if isinstance(label_options, list) else [],
            model_dir=str(case.get("medical_image_model_dir") or "") or None,
        )
    if tool_name == "monai_bundle_status:ct_lung_nodule_detection":
        return monai_bundle_status("ct_lung_nodule_detection", bundle_dir=str(case.get("monai_bundle_dir") or "") or None)
    if tool_name == "monai_bundle_status:mri_brats_segmentation":
        return monai_bundle_status("mri_brats_segmentation", bundle_dir=str(case.get("monai_bundle_dir") or "") or None)
    if tool_name.startswith("stage4_ehr:"):
        ehr_task_key = _infer_ehr_task_key(task_key, case)
        stage4_tool_name = tool_name.split(":", 1)[1]
        bins = case.get("ehr_bins") if isinstance(case.get("ehr_bins"), dict) else {}
        out = execute_stage4_ehr_tool(ehr_task_key, stage4_tool_name, case, bins)
        result = {
            "status": "success",
            "tool_name": tool_name,
            "ehr_task_key": ehr_task_key,
            "source_repo": "HealthClaw/tools/stage4_ehr_tools.py",
            "summary": out.get("summary"),
            "findings": out.get("findings", []),
            "tags": out.get("tags", []),
            "input_visible_only": True,
            "gold_label_used": False,
            "future_cases_used": False,
            "warning": "Structured EHR evidence is not a calibrated final outcome classifier.",
        }
        for key in (
            "predicted_label",
            "recommended_final_label",
            "recommended_final_confidence",
            "label_candidates",
            "top_label_candidate",
            "evidence_strength",
            "label_coverage",
            "domain_match",
            "recommended_use",
            "calibration_note",
            "class_bias_risk",
        ):
            if out.get(key) is not None:
                result[key] = out[key]
        return result
    if tool_name == "pyhealth_readmission_status":
        return pyhealth_readmission_status(source_dir=str(case.get("pyhealth_source_dir") or "") or None)
    if tool_name == "uci_diabetes_xgb_readmission_status":
        return uci_diabetes_xgb_readmission_status(model_dir=str(case.get("diabetes_model_dir") or "") or None)
    if tool_name == "uci_diabetes_xgb_readmission_classify":
        return uci_diabetes_xgb_readmission_classify(
            case=case,
            model_dir=str(case.get("diabetes_model_dir") or "") or None,
        )
    if tool_name == "mlomics_cmob_status":
        return mlomics_cmob_status(
            source_dir=str(case.get("mlomics_source_dir") or "") or None,
            model_dir=str(case.get("mlomics_model_dir") or "") or None,
        )
    if tool_name == "mlomics_synthetic_brca_xgb_status":
        return mlomics_synthetic_brca_xgb_status(
            model_dir=str(case.get("mlomics_synthetic_model_dir") or "") or None,
            raw_dir=str(case.get("mlomics_raw_dir") or "") or None,
        )
    if tool_name == "mlomics_synthetic_brca_xgb_classify":
        return mlomics_synthetic_brca_xgb_classify(
            case=case,
            model_dir=str(case.get("mlomics_synthetic_model_dir") or "") or None,
            raw_dir=str(case.get("mlomics_raw_dir") or "") or None,
            label_options=case.get("label_options") if isinstance(case.get("label_options"), list) else [],
        )
    return {
        "status": "not_available",
        "tool_name": tool_name,
        "input_visible_only": True,
        "message": "Tool is not implemented in this HealthClaw checkout yet; use candidate status from route_tools.",
    }


def execute_tool(tool_name: str, case: Dict[str, Any], task_key: str = "") -> Dict[str, Any]:
    return _with_evidence_defaults(tool_name, case, task_key, _execute_tool_impl(tool_name, case, task_key))
