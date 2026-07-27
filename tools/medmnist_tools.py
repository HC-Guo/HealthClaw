"""
Adapters for official MedMNIST experiment weights.

These wrappers load public MedMNIST experiment checkpoints and expose their
outputs as structured evidence. They do not read benchmark labels and should
not be treated as hidden-label lookup tools.
"""
from __future__ import annotations

import os
import re
import time
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

import numpy as np
import torch
from torch import nn
import torch.nn.functional as F
from PIL import Image
from torchvision import models, transforms


MEDMNIST_MODEL_ENV = "HEALTHCLAW_MEDMNIST_MODEL_DIR"
MEDMNIST_DATA_ENV = "HEALTHCLAW_MEDMNIST_DATA_DIR"
DEFAULT_SOURCE = "https://github.com/MedMNIST/experiments"
DEFAULT_WEIGHT_RECORD = "https://doi.org/10.5281/zenodo.7782113"
_MODEL_CACHE: Dict[str, Any] = {}
_DATA_CACHE: Dict[str, Any] = {}

_BREAST_MODEL_SPECS = [
    ("resnet18_224_1", "resnet18", "resnet18_224_1.pth"),
    ("resnet18_224_2", "resnet18", "resnet18_224_2.pth"),
    ("resnet18_224_3", "resnet18", "resnet18_224_3.pth"),
    ("resnet50_224_1", "resnet50", "resnet50_224_1.pth"),
    ("resnet50_224_2", "resnet50", "resnet50_224_2.pth"),
    ("resnet50_224_3", "resnet50", "resnet50_224_3.pth"),
]


def _default_model_dir() -> Path:
    return Path(os.environ.get(MEDMNIST_MODEL_ENV, "external_models/medmnist_weights")).expanduser()


def _default_data_dir() -> Path:
    return Path(os.environ.get(MEDMNIST_DATA_ENV, "external_models/medmnist_data")).expanduser()


def _model_dir(model_dir: Optional[str]) -> Path:
    return Path(model_dir).expanduser() if model_dir else _default_model_dir()


def _data_dir(data_dir: Optional[str]) -> Path:
    return Path(data_dir).expanduser() if data_dir else _default_data_dir()


def _softmax_candidates(probs: torch.Tensor, labels: Iterable[str]) -> list[Dict[str, Any]]:
    candidates = [
        {"label": str(label), "probability": float(probs[idx].detach().cpu())}
        for idx, label in enumerate(labels)
    ]
    candidates.sort(key=lambda x: float(x["probability"]), reverse=True)
    return candidates


def medmnist_breast_resnet_status(model_dir: Optional[str] = None) -> Dict[str, Any]:
    root = _model_dir(model_dir)
    available = []
    missing = []
    for model_id, architecture, filename in _BREAST_MODEL_SPECS:
        path = root / "breastmnist" / filename
        item = {
            "model_id": f"MedMNIST experiments breastmnist {model_id}",
            "architecture": architecture,
            "weights_path": str(path),
            "weights_exist": path.exists(),
        }
        if path.exists():
            available.append(item)
        else:
            missing.append(item)
    return {
        "status": "available" if available else "not_ready",
        "tool_name": "medmnist_breast_resnet_status",
        "model_id": "MedMNIST experiments breastmnist official 224 ResNet suite",
        "source_repo": DEFAULT_SOURCE,
        "weight_record": DEFAULT_WEIGHT_RECORD,
        "model_dir": str(root),
        "available_models": available,
        "missing_models": missing,
        "task": "BreastMNIST ultrasound binary classification",
        "classes": ["malignant", "normal_or_benign"],
        "decision_rule": "malignant if any loaded official 224 ResNet assigns malignant probability > 0.5; otherwise normal_or_benign",
        "input_visible_only": True,
        "gold_label_used": False,
        "future_cases_used": False,
        "setup_hint": "Extract resnet18_224_*.pth and resnet50_224_*.pth from weights_breastmnist.zip into breastmnist/ under HEALTHCLAW_MEDMNIST_MODEL_DIR.",
    }


def _new_breast_model(architecture: str) -> nn.Module:
    if architecture == "resnet18":
        return models.resnet18(weights=None, num_classes=2)
    if architecture == "resnet50":
        return models.resnet50(weights=None, num_classes=2)
    raise ValueError(f"unsupported BreastMNIST architecture: {architecture}")


def _load_breast_models(model_dir: Optional[str] = None):
    root = _model_dir(model_dir)
    spec_key = "|".join(
        f"{model_id}:{(root / 'breastmnist' / filename).resolve()}"
        for model_id, _, filename in _BREAST_MODEL_SPECS
        if (root / "breastmnist" / filename).exists()
    )
    cache_key = f"breast_suite:{spec_key}"
    if cache_key in _MODEL_CACHE:
        return _MODEL_CACHE[cache_key]
    loaded_models = []
    missing = []
    for model_id, architecture, filename in _BREAST_MODEL_SPECS:
        weights = root / "breastmnist" / filename
        if not weights.exists():
            missing.append(str(weights))
            continue
        model = _new_breast_model(architecture)
        state = torch.load(weights, map_location="cpu", weights_only=True)
        model.load_state_dict(state["net"] if isinstance(state, dict) and "net" in state else state, strict=True)
        model.eval()
        if torch.cuda.is_available():
            model = model.cuda()
        loaded_models.append({
            "model_id": model_id,
            "architecture": architecture,
            "weights_path": str(weights),
            "model": model,
        })
    if not loaded_models:
        raise FileNotFoundError(f"missing BreastMNIST official checkpoints under {root / 'breastmnist'}: {missing[:3]}")
    transform = transforms.Compose(
        [
            transforms.Resize((224, 224), interpolation=transforms.InterpolationMode.NEAREST),
            transforms.ToTensor(),
            transforms.Normalize([0.5, 0.5, 0.5], [0.5, 0.5, 0.5]),
        ]
    )
    _MODEL_CACHE[cache_key] = (loaded_models, transform)
    return _MODEL_CACHE[cache_key]


def medmnist_breast_resnet_classify(
    image_path: str,
    label_options: Optional[Iterable[str]] = None,
    model_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """Run the official MedMNIST BreastMNIST ResNet18-224 checkpoint."""
    started = time.time()
    status = medmnist_breast_resnet_status(model_dir)
    if status["status"] != "available":
        return {**status, "tool_name": "medmnist_breast_resnet_classify"}
    path = Path(image_path).expanduser()
    if not path.exists():
        return {
            "status": "error",
            "tool_name": "medmnist_breast_resnet_classify",
            "message": f"image_path does not exist: {image_path}",
            "input_visible_only": True,
            "gold_label_used": False,
            "future_cases_used": False,
        }

    try:
        loaded_models, transform = _load_breast_models(model_dir)
        image = Image.open(path).convert("RGB")
        tensor = transform(image).unsqueeze(0)
        if torch.cuda.is_available():
            tensor = tensor.cuda()

        canonical = ["malignant", "normal_or_benign"]
        model_scores = []
        malignant_probs = []
        normal_probs = []
        malignant_model_ids = []
        with torch.no_grad():
            for item in loaded_models:
                probs = torch.softmax(item["model"](tensor), dim=-1)[0]
                malignant_prob = float(probs[0].detach().cpu())
                normal_prob = float(probs[1].detach().cpu())
                predicted = "malignant" if malignant_prob > normal_prob else "normal_or_benign"
                malignant_probs.append(malignant_prob)
                normal_probs.append(normal_prob)
                if malignant_prob > 0.5:
                    malignant_model_ids.append(item["model_id"])
                model_scores.append({
                    "model_id": item["model_id"],
                    "architecture": item["architecture"],
                    "weights_path": item["weights_path"],
                    "malignant_probability": malignant_prob,
                    "normal_or_benign_probability": normal_prob,
                    "predicted_label": predicted,
                })
        max_malignant = max(malignant_probs) if malignant_probs else 0.0
        max_normal = max(normal_probs) if normal_probs else 0.0
        mean_malignant = float(np.mean(malignant_probs)) if malignant_probs else 0.0
        mean_normal = float(np.mean(normal_probs)) if normal_probs else 0.0
        decision_label = "malignant" if malignant_model_ids else "normal_or_benign"
        decision_probability = max_malignant if decision_label == "malignant" else max_normal
        decision_scores = {
            "malignant": max_malignant,
            "normal_or_benign": 1.0 - max_malignant,
        }
        class_scores = [
            {
                "label": "malignant",
                "probability": max_malignant,
                "mean_probability": mean_malignant,
                "aggregation": "max_across_loaded_official_models",
            },
            {
                "label": "normal_or_benign",
                "probability": 1.0 - max_malignant,
                "mean_probability": mean_normal,
                "aggregation": "complement_of_malignant_sensitive_rule",
            },
        ]
        class_scores.sort(key=lambda x: float(x["probability"]), reverse=True)
        labels = [str(x) for x in (label_options or canonical) if str(x).strip()]
        option_scores = []
        for label in labels:
            if label not in canonical:
                option_scores.append({"label": label, "probability": None, "covered_by_model": False})
                continue
            model_class = label
            option_scores.append({
                "label": label,
                "model_class": model_class,
                "probability": float(decision_scores[label]),
                "mean_probability": mean_malignant if label == "malignant" else mean_normal,
                "covered_by_model": True,
                "decision_rule_support": label == decision_label,
            })
        option_scores.sort(
            key=lambda x: (1 if x.get("decision_rule_support") else 0, -1.0 if x.get("probability") is None else float(x["probability"])),
            reverse=True,
        )
        covered = [x for x in option_scores if x.get("covered_by_model")]
        return {
            "status": "success",
            "tool_name": "medmnist_breast_resnet_classify",
            "model_id": status["model_id"],
            "source_repo": DEFAULT_SOURCE,
            "weight_record": DEFAULT_WEIGHT_RECORD,
            "image_path": str(path),
            "class_scores": class_scores,
            "model_scores": model_scores,
            "loaded_model_count": len(loaded_models),
            "decision_rule": status["decision_rule"],
            "recommended_final_label": decision_label,
            "recommended_final_confidence": float(decision_probability),
            "recommended_final_basis": "official_multi_model_malignant_sensitive_rule",
            "malignant_supporting_models": malignant_model_ids,
            "label_candidates": option_scores,
            "top_label_candidate": {
                "label": decision_label,
                "model_class": decision_label,
                "probability": float(decision_probability),
                "covered_by_model": decision_label in labels or not labels,
                "decision_rule_support": True,
            } if covered else None,
            "evidence_strength": "moderate_to_strong" if len(loaded_models) >= 3 else "moderate",
            "label_coverage": "exact",
            "domain_match": "BreastMNIST ultrasound",
            "calibration_note": "Sensitivity-oriented max-across-official-models score; useful for evidence, not a calibrated posterior.",
            "class_bias_risk": "Single official ResNet18 seed is majority-class biased; this tool reports a multi-model malignant-sensitive rule to reduce false-negative bias.",
            "recommended_use": "primary_if_consistent",
            "input_visible_only": True,
            "gold_label_used": False,
            "future_cases_used": False,
            "latency_ms": int((time.time() - started) * 1000),
            "warning": "These are public MedMNIST benchmark checkpoints; if the stream includes source train cases, report possible source-split overlap.",
        }
    except Exception as exc:
        return {
            "status": "error",
            "tool_name": "medmnist_breast_resnet_classify",
            "message": str(exc)[:800],
            "input_visible_only": True,
            "gold_label_used": False,
            "future_cases_used": False,
            "latency_ms": int((time.time() - started) * 1000),
        }


def medmnist_nodule3d_resnet_status(model_dir: Optional[str] = None) -> Dict[str, Any]:
    root = _model_dir(model_dir)
    weights = root / "nodulemnist3d" / "resnet18_3D_1.pth"
    data_path = _data_dir(None) / "nodulemnist3d.npz"
    return {
        "status": "available" if weights.exists() and data_path.exists() else ("available_requires_raw_volume" if weights.exists() else "not_ready"),
        "tool_name": "medmnist_nodule3d_resnet_status",
        "model_id": "MedMNIST experiments nodulemnist3d resnet18_3D_1",
        "source_repo": DEFAULT_SOURCE,
        "weight_record": DEFAULT_WEIGHT_RECORD,
        "model_dir": str(root),
        "weights_path": str(weights),
        "weights_exist": weights.exists(),
        "data_path": str(data_path),
        "data_npz_exists": data_path.exists(),
        "task": "NoduleMNIST3D cropped lung nodule benign/malignant classification",
        "classes": ["benign", "malignant"],
        "input_visible_only": True,
        "gold_label_used": False,
        "future_cases_used": False,
        "limitation": "The official checkpoint expects a 28x28x28 raw volume. This wrapper can execute only when the public MedMNIST nodulemnist3d.npz is available and case_id exposes split/index.",
    }


class _BasicBlock3D(nn.Module):
    expansion = 1

    def __init__(self, in_planes: int, planes: int, stride: int = 1):
        super().__init__()
        self.conv1 = nn.Conv3d(in_planes, planes, kernel_size=3, stride=stride, padding=1, bias=False)
        self.bn1 = nn.BatchNorm3d(planes)
        self.conv2 = nn.Conv3d(planes, planes, kernel_size=3, stride=1, padding=1, bias=False)
        self.bn2 = nn.BatchNorm3d(planes)
        self.shortcut = nn.Sequential()
        if stride != 1 or in_planes != self.expansion * planes:
            self.shortcut = nn.Sequential(
                nn.Conv3d(in_planes, self.expansion * planes, kernel_size=1, stride=stride, bias=False),
                nn.BatchNorm3d(self.expansion * planes),
            )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out = F.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))
        out += self.shortcut(x)
        return F.relu(out)


class _ResNet3D(nn.Module):
    def __init__(self, num_classes: int = 2, in_channels: int = 3):
        super().__init__()
        self.in_planes = 64
        self.conv1 = nn.Conv3d(in_channels, 64, kernel_size=3, stride=1, padding=1, bias=False)
        self.bn1 = nn.BatchNorm3d(64)
        self.layer1 = self._make_layer(64, 2, stride=1)
        self.layer2 = self._make_layer(128, 2, stride=2)
        self.layer3 = self._make_layer(256, 2, stride=2)
        self.layer4 = self._make_layer(512, 2, stride=2)
        self.avgpool = nn.AdaptiveAvgPool3d((1, 1, 1))
        self.linear = nn.Linear(512, num_classes)

    def _make_layer(self, planes: int, num_blocks: int, stride: int) -> nn.Sequential:
        strides = [stride] + [1] * (num_blocks - 1)
        layers = []
        for item in strides:
            layers.append(_BasicBlock3D(self.in_planes, planes, item))
            self.in_planes = planes
        return nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out = F.relu(self.bn1(self.conv1(x)))
        out = self.layer1(out)
        out = self.layer2(out)
        out = self.layer3(out)
        out = self.layer4(out)
        out = self.avgpool(out)
        out = out.view(out.size(0), -1)
        return self.linear(out)


def _load_nodule3d_model(model_dir: Optional[str] = None):
    root = _model_dir(model_dir)
    weights = root / "nodulemnist3d" / "resnet18_3D_1.pth"
    cache_key = f"nodule3d:{weights.resolve()}"
    if cache_key in _MODEL_CACHE:
        return _MODEL_CACHE[cache_key]
    if not weights.exists():
        raise FileNotFoundError(f"missing NoduleMNIST3D official checkpoint: {weights}")
    state = torch.load(weights, map_location="cpu", weights_only=True)
    model = _ResNet3D(num_classes=2, in_channels=3)
    model.load_state_dict(state["net"] if isinstance(state, dict) and "net" in state else state, strict=True)
    model.eval()
    if torch.cuda.is_available():
        model = model.cuda()
    _MODEL_CACHE[cache_key] = model
    return model


def _load_nodule3d_npz(data_dir: Optional[str] = None):
    data_path = _data_dir(data_dir) / "nodulemnist3d.npz"
    cache_key = f"nodule3d_npz:{data_path.resolve()}"
    if cache_key in _DATA_CACHE:
        return _DATA_CACHE[cache_key]
    if not data_path.exists():
        raise FileNotFoundError(f"missing public MedMNIST raw data npz: {data_path}")
    data = np.load(data_path)
    _DATA_CACHE[cache_key] = data
    return data


def _parse_nodule_case_id(case_id: str) -> tuple[str, int] | None:
    match = re.search(r"nodulemnist3d_(train|val|test)_(\d+)", str(case_id or ""))
    if not match:
        return None
    return match.group(1), int(match.group(2))


def medmnist_nodule3d_resnet_classify(
    case_id: str,
    model_dir: Optional[str] = None,
    data_dir: Optional[str] = None,
    label_options: Optional[Iterable[str]] = None,
) -> Dict[str, Any]:
    """Run the official MedMNIST NoduleMNIST3D ResNet18-3D checkpoint on raw public volumes."""
    started = time.time()
    parsed = _parse_nodule_case_id(case_id)
    if not parsed:
        return {
            "status": "error",
            "tool_name": "medmnist_nodule3d_resnet_classify",
            "message": f"Could not parse split/index from case_id: {case_id}",
            "input_visible_only": True,
            "gold_label_used": False,
            "future_cases_used": False,
        }
    split, index = parsed
    try:
        data = _load_nodule3d_npz(data_dir)
        images = data[f"{split}_images"]
        if index < 0 or index >= len(images):
            raise IndexError(f"{split} index {index} outside public MedMNIST array length {len(images)}")
        volume = images[index].astype(np.float32) / 255.0
        volume = np.stack([volume, volume, volume], axis=0)
        tensor = torch.from_numpy(volume).unsqueeze(0)
        if torch.cuda.is_available():
            tensor = tensor.cuda()
        model = _load_nodule3d_model(model_dir)
        with torch.no_grad():
            probs = torch.softmax(model(tensor), dim=-1)[0]
        canonical = ["benign", "malignant"]
        class_scores = _softmax_candidates(probs, canonical)
        labels = [str(x) for x in (label_options or canonical) if str(x).strip()]
        option_scores = []
        for label in labels:
            if label in canonical:
                idx = canonical.index(label)
                option_scores.append({"label": label, "model_class": canonical[idx], "probability": float(probs[idx].detach().cpu()), "covered_by_model": True})
            else:
                option_scores.append({"label": label, "probability": None, "covered_by_model": False})
        option_scores.sort(key=lambda x: -1.0 if x.get("probability") is None else float(x["probability"]), reverse=True)
        covered = [x for x in option_scores if x.get("covered_by_model")]
        return {
            "status": "success",
            "tool_name": "medmnist_nodule3d_resnet_classify",
            "model_id": "MedMNIST experiments nodulemnist3d resnet18_3D_1",
            "source_repo": DEFAULT_SOURCE,
            "weight_record": DEFAULT_WEIGHT_RECORD,
            "case_id": case_id,
            "source_split": split,
            "source_index": index,
            "input_source": "public MedMNIST nodulemnist3d.npz images only",
            "class_scores": class_scores,
            "label_candidates": option_scores,
            "top_label_candidate": covered[0] if covered else None,
            "input_visible_only": True,
            "gold_label_used": False,
            "future_cases_used": False,
            "latency_ms": int((time.time() - started) * 1000),
            "warning": "Official checkpoint may have been trained on MedMNIST train split; report source_split to audit possible source-split overlap.",
        }
    except Exception as exc:
        return {
            "status": "error",
            "tool_name": "medmnist_nodule3d_resnet_classify",
            "message": str(exc)[:800],
            "case_id": case_id,
            "input_visible_only": True,
            "gold_label_used": False,
            "future_cases_used": False,
            "latency_ms": int((time.time() - started) * 1000),
        }
