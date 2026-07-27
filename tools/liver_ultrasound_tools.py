"""
Availability wrappers for liver-ultrasound steatosis tools.

This module does not implement hand-written NAFLD image rules. It records the
most relevant external B-mode ultrasound steatosis classifier candidate and
reports whether a local checkout plus weights are available for inference.
"""
from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any, Dict, Iterable, Optional


LIVER_STEATOSIS_MODEL_ENV = "HEALTHCLAW_LIVER_STEATOSIS_MODEL_DIR"
DEFAULT_SOURCE_REPO = "https://github.com/LCTI-AnTang/binary_steatosis_classifier"
DEFAULT_PAPER = "Radiology 2023 liver steatosis B-mode ultrasound deep learning classifier"
FALLBACK_DATASET = "https://zenodo.org/records/1009146"
FALLBACK_PAPER = "Byra et al., IJCARS 2018 liver steatosis B-mode ultrasound dataset"
_MODEL_CACHE: Dict[str, Any] = {}


def _default_model_dir() -> Path:
    return Path(os.environ.get(LIVER_STEATOSIS_MODEL_ENV, "external_models/liver_ultrasound/binary_steatosis_classifier")).expanduser()


def _model_dir(model_dir: Optional[str]) -> Path:
    return Path(model_dir).expanduser() if model_dir else _default_model_dir()


def _weight_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    patterns = ["*.h5", "*.keras", "*.ckpt", "*.pth", "*.pt", "*.onnx"]
    found: list[Path] = []
    for pattern in patterns:
        found.extend(root.rglob(pattern))
    return sorted(found)


def _fallback_files(root: Path) -> tuple[Path, Path]:
    model_path = root / "model.joblib"
    if not model_path.exists():
        model_path = root / "resnet18_logreg.joblib"
    return model_path, root / "metrics.json"


def _read_metrics(root: Path) -> Optional[Dict[str, Any]]:
    _, metrics_path = _fallback_files(root)
    if not metrics_path.exists():
        return None
    try:
        import json

        return json.loads(metrics_path.read_text(encoding="utf-8"))
    except Exception:
        return None


def liver_ultrasound_steatosis_status(model_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Report availability of a real B-mode ultrasound steatosis classifier.

    The current best candidate is not marked executable unless local model
    weights exist. This prevents BEHSOF from silently falling back to generic
    image-quality features and pretending they are NAFLD evidence.
    """
    root = _model_dir(model_dir)
    weights = _weight_files(root)
    fallback_model, fallback_metrics = _fallback_files(root)
    source_complete = (root / "README.md").exists() or (root / "README.rst").exists()
    fallback_ready = fallback_model.exists() and fallback_metrics.exists()
    metrics = _read_metrics(root)
    return {
        "status": "available" if fallback_ready else ("available_if_adapter_completed" if source_complete and weights else "not_ready_requires_weights"),
        "tool_name": "liver_ultrasound_steatosis_status",
        "source_repo": DEFAULT_SOURCE_REPO,
        "paper": DEFAULT_PAPER,
        "fallback_training_source": FALLBACK_DATASET,
        "fallback_paper": FALLBACK_PAPER,
        "model_dir": str(root),
        "source_checkout_detected": source_complete,
        "weight_files": [str(p) for p in weights[:20]],
        "weights_exist": bool(weights),
        "fallback_model_path": str(fallback_model),
        "fallback_model_exists": fallback_model.exists(),
        "fallback_metrics_path": str(fallback_metrics),
        "fallback_metrics": {
            "backbone": (metrics or {}).get("backbone"),
            "test_subject_balanced_accuracy": (((metrics or {}).get("subject_metrics") or {}).get("test") or {}).get("balanced_accuracy"),
            "test_subject_roc_auc": (((metrics or {}).get("subject_metrics") or {}).get("test") or {}).get("roc_auc"),
            "healthclaw_eval_labels_used": (metrics or {}).get("healthclaw_eval_labels_used"),
        } if metrics else None,
        "task": "B-mode liver ultrasound steatosis / NAFLD classification",
        "expected_input": "single visible B-mode liver ultrasound image plus the external model's preprocessing CSV",
        "classes": ["NAFLD", "Non-NAFLD"],
        "input_visible_only": True,
        "gold_label_used": False,
        "future_cases_used": False,
        "limitation": (
            "If the Zenodo fallback model is available, it was trained locally only on an "
            "external CC-BY B-mode liver ultrasound dataset and did not use BEHSOF labels. "
            "Its held-out subject performance is modest and domain-shift risk remains, so "
            "it should be warning/auxiliary evidence rather than a strong final classifier. "
            "The previously cloned Fatty-liver-classifier uses ultrasonic raw-signal derived "
            "IB/Q/HF tabular features and is not compatible with BEHSOF JPG images."
        ),
        "setup_hint": (
            "Place resnet18_logreg.joblib and metrics.json from the Zenodo external-data "
            "training script under HEALTHCLAW_LIVER_STEATOSIS_MODEL_DIR, or provide a "
            "complete public B-mode steatosis checkpoint under the same directory."
        ),
    }


def _load_fallback_model(model_dir: Optional[str] = None):
    import joblib
    import torch
    from torchvision import models, transforms

    root = _model_dir(model_dir)
    model_path, _ = _fallback_files(root)
    metrics = _read_metrics(root) or {}
    backbone = str(metrics.get("backbone") or "resnet18")
    cache_key = f"zenodo_liver:{model_path.resolve()}"
    if cache_key in _MODEL_CACHE:
        return _MODEL_CACHE[cache_key]
    if not model_path.exists():
        raise FileNotFoundError(f"missing external-data liver steatosis model: {model_path}")

    if backbone == "efficientnet_b0":
        weights = models.EfficientNet_B0_Weights.DEFAULT
        feature_extractor = models.efficientnet_b0(weights=weights)
        feature_extractor.classifier = torch.nn.Identity()
    elif backbone == "resnet18":
        weights = models.ResNet18_Weights.DEFAULT
        feature_extractor = models.resnet18(weights=weights)
        feature_extractor.fc = torch.nn.Identity()
    else:
        raise ValueError(f"unsupported liver steatosis fallback backbone: {backbone}")
    feature_extractor.eval()
    if torch.cuda.is_available():
        feature_extractor = feature_extractor.cuda()
    transform = transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=weights.transforms().mean, std=weights.transforms().std),
        ]
    )
    classifier = joblib.load(model_path)
    _MODEL_CACHE[cache_key] = (feature_extractor, transform, classifier, backbone)
    return _MODEL_CACHE[cache_key]


def liver_ultrasound_steatosis_classify(
    image_path: str,
    label_options: Optional[Iterable[str]] = None,
    model_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """Run the external-data Zenodo liver steatosis fallback classifier."""
    started = time.time()
    status = liver_ultrasound_steatosis_status(model_dir)
    if status["status"] != "available":
        return {**status, "tool_name": "liver_ultrasound_steatosis_classify"}
    path = Path(image_path).expanduser()
    if not path.exists():
        return {
            "status": "error",
            "tool_name": "liver_ultrasound_steatosis_classify",
            "message": f"image_path does not exist: {image_path}",
            "input_visible_only": True,
            "gold_label_used": False,
            "future_cases_used": False,
        }
    try:
        import torch
        from PIL import Image

        feature_extractor, transform, classifier, backbone = _load_fallback_model(model_dir)
        image = Image.open(path).convert("RGB")
        tensor = transform(image).unsqueeze(0)
        if torch.cuda.is_available():
            tensor = tensor.cuda()
        with torch.no_grad():
            feature = feature_extractor(tensor).detach().cpu().numpy()
        prob_nafld = float(classifier.predict_proba(feature)[0, 1])
        mapped_probs = {
            "NAFLD": prob_nafld,
            "Non-NAFLD": 1.0 - prob_nafld,
        }
        labels = [str(x) for x in (label_options or mapped_probs.keys()) if str(x).strip()]
        option_scores = []
        for label in labels:
            probability = mapped_probs.get(label)
            option_scores.append({
                "label": label,
                "probability": probability,
                "covered_by_model": probability is not None,
                "model_mapping": "class 1->NAFLD, class 0->Non-NAFLD" if probability is not None else None,
            })
        option_scores.sort(key=lambda x: -1.0 if x.get("probability") is None else float(x["probability"]), reverse=True)
        covered = [x for x in option_scores if x.get("covered_by_model")]
        return {
            "status": "success",
            "tool_name": "liver_ultrasound_steatosis_classify",
            "model_id": f"zenodo_liver_ultrasound_{backbone}_logreg",
            "source": FALLBACK_DATASET,
            "paper": FALLBACK_PAPER,
            "image_path": str(path),
            "label_candidates": option_scores,
            "top_label_candidate": covered[0] if covered else None,
            "probability_nafld": prob_nafld,
            "evidence_strength": "weak",
            "recommended_use": "warning_only_auxiliary_evidence",
            "class_bias_risk": "high",
            "do_not_override_conflicting_memory_or_primary_image_reasoning": True,
            "input_visible_only": True,
            "gold_label_used": False,
            "future_cases_used": False,
            "latency_ms": int((time.time() - started) * 1000),
            "warning": (
                status["limitation"]
                + " In BEHSOF sanity checks this fallback showed a strong NAFLD prediction bias, "
                "so the agent should treat it as weak warning-only evidence."
            ),
        }
    except Exception as exc:
        return {
            "status": "error",
            "tool_name": "liver_ultrasound_steatosis_classify",
            "message": str(exc)[:800],
            "input_visible_only": True,
            "gold_label_used": False,
            "future_cases_used": False,
            "latency_ms": int((time.time() - started) * 1000),
        }
