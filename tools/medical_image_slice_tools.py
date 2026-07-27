"""
2D medical image classifier adapters for CT/MRI benchmark slices.

These wrappers use public task-specific image models and expose their outputs
as auxiliary evidence. They are intentionally separated from MONAI 3D bundle
tools because the current MSD benchmark streams expose PNG slices/panels rather
than raw NIfTI volumes.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

import torch
from PIL import Image


MEDICAL_IMAGE_MODEL_ENV = "HEALTHCLAW_MEDICAL_IMAGE_MODEL_DIR"
DEFAULT_MODEL_SOURCE = "https://huggingface.co"
LUNG_CT_REPO = "sukhmani1303/lung-cancer-vit-model"
BRAIN_MRI_REPO = "prithivMLmods/BrainTumor-Classification-Mini"
_MODEL_CACHE: Dict[str, Any] = {}


def _default_model_dir() -> Path:
    return Path(os.environ.get(MEDICAL_IMAGE_MODEL_ENV, "external_models/medical_image_models")).expanduser()


def _model_dir(model_dir: Optional[str]) -> Path:
    return Path(model_dir).expanduser() if model_dir else _default_model_dir()


def _softmax_candidates(probs: torch.Tensor, labels: Iterable[str]) -> list[Dict[str, Any]]:
    candidates = [
        {"label": str(label), "probability": float(probs[idx].detach().cpu())}
        for idx, label in enumerate(labels)
    ]
    candidates.sort(key=lambda x: float(x["probability"]), reverse=True)
    return candidates


def lung_ct_vit_slice_status(model_dir: Optional[str] = None) -> Dict[str, Any]:
    root = _model_dir(model_dir) / "lung-cancer-vit-model"
    weights = root / "pytorch_model.bin"
    config = root / "config.json"
    return {
        "status": "available" if weights.exists() and config.exists() else "not_ready",
        "tool_name": "lung_ct_vit_slice_status",
        "model_id": LUNG_CT_REPO,
        "source": f"{DEFAULT_MODEL_SOURCE}/{LUNG_CT_REPO}",
        "model_dir": str(root),
        "weights_exist": weights.exists(),
        "config_exists": config.exists(),
        "task": "2D lung CT image cancer/normal classification",
        "classes": ["Cancer", "Normal"],
        "mapped_labels": ["visible_lung_tumor", "no_visible_lung_tumor"],
        "input_visible_only": True,
        "gold_label_used": False,
        "future_cases_used": False,
        "warning": "This is a 2D CT image classifier trained on IQ-OTH/NCCD lung CT images; use as auxiliary slice evidence, not as a calibrated MSD tumor-segmentation model.",
    }


def _load_lung_ct_model(model_dir: Optional[str] = None):
    import timm
    from torchvision import transforms

    root = _model_dir(model_dir) / "lung-cancer-vit-model"
    weights = root / "pytorch_model.bin"
    cache_key = f"lung_ct:{weights.resolve()}"
    if cache_key in _MODEL_CACHE:
        return _MODEL_CACHE[cache_key]
    if not weights.exists():
        raise FileNotFoundError(f"missing lung CT ViT checkpoint: {weights}")

    model = timm.create_model("vit_base_patch16_224", pretrained=False, num_classes=2)
    state = torch.load(weights, map_location="cpu", weights_only=True)
    model.load_state_dict(state, strict=True)
    model.eval()
    if torch.cuda.is_available():
        model = model.cuda()
    transform = transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
        ]
    )
    _MODEL_CACHE[cache_key] = (model, transform)
    return _MODEL_CACHE[cache_key]


def lung_ct_vit_slice_classify(
    image_path: str,
    label_options: Optional[Iterable[str]] = None,
    model_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """Run the public lung CT ViT image classifier on the visible PNG slice."""
    started = time.time()
    status = lung_ct_vit_slice_status(model_dir)
    if status["status"] != "available":
        return {**status, "tool_name": "lung_ct_vit_slice_classify"}
    path = Path(image_path).expanduser()
    if not path.exists():
        return {
            "status": "error",
            "tool_name": "lung_ct_vit_slice_classify",
            "message": f"image_path does not exist: {image_path}",
            "input_visible_only": True,
            "gold_label_used": False,
            "future_cases_used": False,
        }
    try:
        model, transform = _load_lung_ct_model(model_dir)
        image = Image.open(path).convert("RGB")
        tensor = transform(image).unsqueeze(0)
        if torch.cuda.is_available():
            tensor = tensor.cuda()
        with torch.no_grad():
            probs = torch.softmax(model(tensor), dim=-1)[0]

        model_classes = ["Cancer", "Normal"]
        mapped_probs = {
            "visible_lung_tumor": float(probs[0].detach().cpu()),
            "no_visible_lung_tumor": float(probs[1].detach().cpu()),
        }
        labels = [str(x) for x in (label_options or mapped_probs.keys()) if str(x).strip()]
        option_scores = []
        for label in labels:
            probability = mapped_probs.get(label)
            option_scores.append({
                "label": label,
                "probability": probability,
                "covered_by_model": probability is not None,
                "model_mapping": "Cancer->visible_lung_tumor, Normal->no_visible_lung_tumor" if probability is not None else None,
            })
        option_scores.sort(key=lambda x: -1.0 if x.get("probability") is None else float(x["probability"]), reverse=True)
        covered = [x for x in option_scores if x.get("covered_by_model")]
        return {
            "status": "success",
            "tool_name": "lung_ct_vit_slice_classify",
            "model_id": LUNG_CT_REPO,
            "source": f"{DEFAULT_MODEL_SOURCE}/{LUNG_CT_REPO}",
            "image_path": str(path),
            "class_scores": _softmax_candidates(probs, model_classes),
            "label_candidates": option_scores,
            "top_label_candidate": covered[0] if covered else None,
            "evidence_strength": "medium",
            "recommended_use": "auxiliary_slice_evidence",
            "class_bias_risk": "unknown",
            "input_visible_only": True,
            "gold_label_used": False,
            "future_cases_used": False,
            "latency_ms": int((time.time() - started) * 1000),
            "warning": status["warning"],
        }
    except Exception as exc:
        return {
            "status": "error",
            "tool_name": "lung_ct_vit_slice_classify",
            "message": str(exc)[:800],
            "input_visible_only": True,
            "gold_label_used": False,
            "future_cases_used": False,
            "latency_ms": int((time.time() - started) * 1000),
        }


def brain_mri_siglip_tumor_status(model_dir: Optional[str] = None) -> Dict[str, Any]:
    root = _model_dir(model_dir) / "BrainTumor-Classification-Mini"
    config = root / "config.json"
    weights = root / "model.safetensors"
    preprocessor = root / "preprocessor_config.json"
    return {
        "status": "available" if config.exists() and weights.exists() and preprocessor.exists() else "not_ready",
        "tool_name": "brain_mri_siglip_tumor_status",
        "model_id": BRAIN_MRI_REPO,
        "source": f"{DEFAULT_MODEL_SOURCE}/{BRAIN_MRI_REPO}",
        "model_dir": str(root),
        "config_exists": config.exists(),
        "weights_exist": weights.exists(),
        "preprocessor_exists": preprocessor.exists(),
        "task": "2D brain MRI no-tumor/glioma/meningioma/pituitary classification",
        "classes": ["No Tumor", "Glioma", "Meningioma", "Pituitary"],
        "mapped_labels": ["no_visible_tumor", "edema_or_infiltration", "non_enhancing_tumor_core", "enhancing_tumor"],
        "input_visible_only": True,
        "gold_label_used": False,
        "future_cases_used": False,
        "warning": "This public brain MRI classifier detects tumor presence/type, not BraTS/MSD tumor subregions; non-no-tumor classes are weak evidence for visible tumor only.",
    }


def _load_brain_mri_model(model_dir: Optional[str] = None):
    from transformers import AutoImageProcessor, SiglipForImageClassification

    root = _model_dir(model_dir) / "BrainTumor-Classification-Mini"
    cache_key = f"brain_mri:{root.resolve()}"
    if cache_key in _MODEL_CACHE:
        return _MODEL_CACHE[cache_key]
    if not (root / "model.safetensors").exists():
        raise FileNotFoundError(f"missing brain MRI SigLIP checkpoint: {root / 'model.safetensors'}")
    processor = AutoImageProcessor.from_pretrained(root)
    model = SiglipForImageClassification.from_pretrained(root)
    model.eval()
    if torch.cuda.is_available():
        model = model.cuda()
    _MODEL_CACHE[cache_key] = (model, processor)
    return _MODEL_CACHE[cache_key]


def brain_mri_siglip_tumor_classify(
    image_path: str,
    label_options: Optional[Iterable[str]] = None,
    model_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """Run a public 2D brain MRI tumor classifier on the visible MRI panel."""
    started = time.time()
    status = brain_mri_siglip_tumor_status(model_dir)
    if status["status"] != "available":
        return {**status, "tool_name": "brain_mri_siglip_tumor_classify"}
    path = Path(image_path).expanduser()
    if not path.exists():
        return {
            "status": "error",
            "tool_name": "brain_mri_siglip_tumor_classify",
            "message": f"image_path does not exist: {image_path}",
            "input_visible_only": True,
            "gold_label_used": False,
            "future_cases_used": False,
        }
    try:
        model, processor = _load_brain_mri_model(model_dir)
        image = Image.open(path).convert("RGB")
        inputs = processor(images=image, return_tensors="pt")
        if torch.cuda.is_available():
            inputs = {k: v.cuda() for k, v in inputs.items()}
        with torch.no_grad():
            probs = torch.softmax(model(**inputs).logits, dim=-1)[0]

        id2label = getattr(model.config, "id2label", None) or {0: "No Tumor", 1: "Glioma", 2: "Meningioma", 3: "Pituitary"}
        model_classes = [str(id2label.get(i, i)) for i in range(len(probs))]
        no_tumor_prob = float(probs[0].detach().cpu())
        tumor_prob = max(0.0, min(1.0, 1.0 - no_tumor_prob))

        labels = [str(x) for x in (label_options or ["no_visible_tumor", "edema_or_infiltration", "non_enhancing_tumor_core", "enhancing_tumor"]) if str(x).strip()]
        brats_component_labels = {"edema_or_infiltration", "non_enhancing_tumor_core", "enhancing_tumor"}
        is_brats_component_task = any(label in brats_component_labels for label in labels)
        option_scores = []
        tumor_component_labels = [x for x in labels if x != "no_visible_tumor"]
        denominator = max(1, len(tumor_component_labels))
        for label in labels:
            if label == "no_visible_tumor":
                probability = no_tumor_prob
                covered = not is_brats_component_task
                mapping = "No Tumor->no_visible_tumor"
            elif label in {"edema_or_infiltration", "non_enhancing_tumor_core", "enhancing_tumor"}:
                probability = tumor_prob / denominator
                covered = False
                mapping = "Glioma/Meningioma/Pituitary->visible tumor presence; component unresolved"
            else:
                probability = None
                covered = False
                mapping = None
            option_scores.append({
                "label": label,
                "probability": probability,
                "covered_by_model": covered,
                "model_mapping": mapping,
            })
        option_scores.sort(key=lambda x: -1.0 if x.get("probability") is None else float(x["probability"]), reverse=True)
        covered_items = [x for x in option_scores if x.get("covered_by_model")]
        top_label_candidate = None if is_brats_component_task else (covered_items[0] if covered_items else None)
        return {
            "status": "success",
            "tool_name": "brain_mri_siglip_tumor_classify",
            "model_id": BRAIN_MRI_REPO,
            "source": f"{DEFAULT_MODEL_SOURCE}/{BRAIN_MRI_REPO}",
            "image_path": str(path),
            "class_scores": _softmax_candidates(probs, model_classes),
            "tumor_presence_probability": tumor_prob,
            "label_candidates": option_scores,
            "top_label_candidate": top_label_candidate,
            "evidence_strength": "weak",
            "label_coverage": "none_or_mismatch" if is_brats_component_task else "exact_or_mapped",
            "recommended_use": (
                "auxiliary_presence_only_do_not_override_visual_evidence"
                if is_brats_component_task
                else "warning_only_tumor_presence_evidence"
            ),
            "component_resolution": "unresolved",
            "do_not_use_as_component_classifier": True,
            "input_visible_only": True,
            "gold_label_used": False,
            "future_cases_used": False,
            "latency_ms": int((time.time() - started) * 1000),
            "warning": status["warning"],
        }
    except Exception as exc:
        return {
            "status": "error",
            "tool_name": "brain_mri_siglip_tumor_classify",
            "message": str(exc)[:800],
            "input_visible_only": True,
            "gold_label_used": False,
            "future_cases_used": False,
            "latency_ms": int((time.time() - started) * 1000),
        }
