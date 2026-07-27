"""
Wrappers for real skin-lesion image classification models.

This module adapts an external ISIC2019 EfficientNet-B1 model from HuggingFace.
It maps model classes to benchmark label options and explicitly reports labels
that are not covered by the model.
"""
from __future__ import annotations

import importlib.util
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

import torch
from torch import nn
from PIL import Image
from torchvision import models, transforms


SKIN_MODEL_ENV = "HEALTHCLAW_SKIN_MODEL_DIR"
RG_DERMNET_ENV = "HEALTHCLAW_RG_DERMNET_DIR"
DEFAULT_SKIN_MODEL_ID = "conan17970/efficientnet-b1-skin-cancer-isic2019"
DEFAULT_CLASSES = ["ACK", "BCC", "MEL", "NEV", "SCC", "SEK"]
_MODEL_CACHE: Dict[str, Any] = {}

CLASS_TO_LABELS = {
    "ACK": ["actinic keratosis", "actinic keratoses and intraepithelial carcinoma"],
    "BCC": ["basal cell carcinoma"],
    "MEL": ["melanoma"],
    "NEV": ["melanocytic nevus", "melanocytic nevi"],
    "SCC": ["squamous cell carcinoma"],
    "SEK": ["seborrheic keratosis", "benign keratosis-like lesion", "benign keratosis-like lesions"],
}
LABEL_TO_CLASS = {label: cls for cls, labels in CLASS_TO_LABELS.items() for label in labels}
PAD_LABELS = [
    ("ACK", "actinic keratosis"),
    ("BCC", "basal cell carcinoma"),
    ("MEL", "melanoma"),
    ("NEV", "melanocytic nevus"),
    ("SCC", "squamous cell carcinoma"),
    ("SEK", "seborrheic keratosis"),
]


def _default_model_dir() -> Path:
    return Path(os.environ.get(SKIN_MODEL_ENV, "external_models/skin/efficientnet-b1-skin-cancer-isic2019")).expanduser()


def _default_rg_dermnet_dir() -> Path:
    return Path(os.environ.get(RG_DERMNET_ENV, "external_models/skin/rg-dermnet")).expanduser()


def _timm_available() -> bool:
    return importlib.util.find_spec("timm") is not None


def _model_dir(model_dir: Optional[str]) -> Path:
    return Path(model_dir).expanduser() if model_dir else _default_model_dir()


def _rg_dermnet_dir(model_dir: Optional[str]) -> Path:
    return Path(model_dir).expanduser() if model_dir else _default_rg_dermnet_dir()


def skin_isic_efficientnet_status(model_dir: Optional[str] = None) -> Dict[str, Any]:
    root = _model_dir(model_dir)
    weights = root / "best_weights.pth"
    model_info = root / "model_info.json"
    return {
        "status": "available" if _timm_available() and weights.exists() else "not_ready",
        "tool_name": "skin_isic_efficientnet_status",
        "model_id": DEFAULT_SKIN_MODEL_ID,
        "source_repo": "https://huggingface.co/conan17970/efficientnet-b1-skin-cancer-isic2019",
        "license": "apache-2.0 per HuggingFace model card",
        "model_dir": str(root),
        "weights_exist": weights.exists(),
        "model_info_exists": model_info.exists(),
        "timm_available": _timm_available(),
        "classes": DEFAULT_CLASSES,
        "covered_label_aliases": CLASS_TO_LABELS,
        "input_visible_only": True,
        "gold_label_used": False,
        "future_cases_used": False,
        "setup_hint": "Download best_weights.pth/model_info.json from the HuggingFace model card or set HEALTHCLAW_SKIN_MODEL_DIR.",
    }


def _load_model(model_dir: Optional[str] = None):
    root = _model_dir(model_dir)
    cache_key = str(root.resolve())
    if cache_key in _MODEL_CACHE:
        return _MODEL_CACHE[cache_key]
    if not _timm_available():
        raise RuntimeError("timm is not installed")
    import timm

    weights = root / "best_weights.pth"
    if not weights.exists():
        raise FileNotFoundError(f"missing skin model weights: {weights}")
    model = timm.create_model("efficientnet_b1", pretrained=False, num_classes=len(DEFAULT_CLASSES))
    state = torch.load(weights, map_location="cpu", weights_only=True)
    model.load_state_dict(state)
    model.eval()
    if torch.cuda.is_available():
        model = model.cuda()
    transform = transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ]
    )
    info = {}
    info_path = root / "model_info.json"
    if info_path.exists():
        try:
            info = json.loads(info_path.read_text(encoding="utf-8"))
        except Exception:
            info = {}
    _MODEL_CACHE[cache_key] = (model, transform, info)
    return _MODEL_CACHE[cache_key]


def _mapped_scores(probs: torch.Tensor, label_options: Optional[Iterable[str]]) -> list[Dict[str, Any]]:
    class_scores = {cls: float(probs[idx].detach().cpu()) for idx, cls in enumerate(DEFAULT_CLASSES)}
    candidates = []
    labels = [str(x) for x in (label_options or []) if str(x).strip()]
    if labels:
        for label in labels:
            cls = LABEL_TO_CLASS.get(label)
            if cls is None:
                candidates.append({"label": label, "probability": None, "covered_by_model": False})
            else:
                candidates.append({
                    "label": label,
                    "model_class": cls,
                    "probability": class_scores[cls],
                    "covered_by_model": True,
                })
    else:
        for cls in DEFAULT_CLASSES:
            candidates.append({
                "label": CLASS_TO_LABELS[cls][0],
                "model_class": cls,
                "probability": class_scores[cls],
                "covered_by_model": True,
            })
    candidates.sort(key=lambda x: -1.0 if x.get("probability") is None else float(x["probability"]), reverse=True)
    return candidates


def skin_isic_efficientnet_classify(
    image_path: str,
    label_options: Optional[Iterable[str]] = None,
    model_dir: Optional[str] = None,
) -> Dict[str, Any]:
    started = time.time()
    status = skin_isic_efficientnet_status(model_dir)
    if status["status"] != "available":
        return {**status, "tool_name": "skin_isic_efficientnet_classify"}
    path = Path(image_path).expanduser()
    if not path.exists():
        return {
            "status": "error",
            "tool_name": "skin_isic_efficientnet_classify",
            "message": f"image_path does not exist: {image_path}",
            "input_visible_only": True,
        }
    try:
        model, transform, info = _load_model(model_dir)
        image = Image.open(path).convert("RGB")
        tensor = transform(image).unsqueeze(0)
        if torch.cuda.is_available():
            tensor = tensor.cuda()
        with torch.no_grad():
            probs = torch.softmax(model(tensor), dim=-1)[0]
        class_scores = [
            {"model_class": cls, "probability": float(probs[idx].detach().cpu()), "mapped_labels": CLASS_TO_LABELS[cls]}
            for idx, cls in enumerate(DEFAULT_CLASSES)
        ]
        class_scores.sort(key=lambda x: x["probability"], reverse=True)
        candidates = _mapped_scores(probs, label_options)
        covered = [x for x in candidates if x.get("covered_by_model")]
        return {
            "status": "success",
            "tool_name": "skin_isic_efficientnet_classify",
            "model_id": DEFAULT_SKIN_MODEL_ID,
            "source_repo": "https://huggingface.co/conan17970/efficientnet-b1-skin-cancer-isic2019",
            "license": "apache-2.0 per HuggingFace model card",
            "image_path": str(path),
            "model_card_metrics": {
                "best_f1": info.get("best_f1"),
                "best_accuracy_percent": info.get("best_accuracy"),
                "num_classes": info.get("num_classes"),
            },
            "class_scores": class_scores,
            "label_candidates": candidates,
            "top_label_candidate": covered[0] if covered else None,
            "uncovered_labels": [x["label"] for x in candidates if not x.get("covered_by_model")],
            "input_visible_only": True,
            "gold_label_used": False,
            "future_cases_used": False,
            "latency_ms": int((time.time() - started) * 1000),
            "warning": "This ISIC2019 model covers six classes; missing benchmark labels must not be inferred from this tool alone.",
        }
    except Exception as exc:
        return {
            "status": "error",
            "tool_name": "skin_isic_efficientnet_classify",
            "message": str(exc)[:800],
            "input_visible_only": True,
            "gold_label_used": False,
            "future_cases_used": False,
            "latency_ms": int((time.time() - started) * 1000),
        }


class _RGDermMetaBlock(nn.Module):
    def __init__(self, visual_dim: int, metadata_dim: int):
        super().__init__()
        self.fb = nn.Sequential(nn.Linear(metadata_dim, visual_dim), nn.LayerNorm(visual_dim))
        self.gb = nn.Sequential(nn.Linear(metadata_dim, visual_dim), nn.LayerNorm(visual_dim))

    def forward(self, visual: torch.Tensor, metadata: torch.Tensor) -> torch.Tensor:
        return torch.sigmoid(torch.tanh(visual * self.fb(metadata)) + self.gb(metadata))


class _RGDermGatedResidualBlock(nn.Module):
    def __init__(self, dim: int, dropout: float = 0.1):
        super().__init__()
        self.norm = nn.LayerNorm(dim)
        self.attn = nn.MultiheadAttention(embed_dim=dim, num_heads=8, batch_first=False)
        self.dropout = nn.Dropout(dropout)
        self.gate_linear = nn.Linear(dim, dim)

    def forward(self, query: torch.Tensor, key: torch.Tensor, value: torch.Tensor) -> torch.Tensor:
        attn_output, _ = self.attn(query, key, value)
        attn_output = self.dropout(attn_output)
        gate = torch.sigmoid(self.gate_linear(query))
        return self.norm(gate * attn_output + (1 - gate) * query)


class _RGDermNoMetadataModel(nn.Module):
    """Minimal RG-DermNet no-metadata inference graph matching released weights."""

    def __init__(self, num_classes: int = 6, vocab_size: int = 91, common_dim: int = 512):
        super().__init__()
        self.image_encoder = models.resnet50(weights=None)
        self.image_encoder.fc = nn.Identity()
        self.image_projector = nn.Linear(2048, common_dim)
        self.text_fc = nn.Sequential(
            nn.Linear(vocab_size, 256),
            nn.ReLU(),
            nn.Linear(256, 512),
            nn.ReLU(),
            nn.Linear(512, 512),
        )
        self.text_projector = nn.Linear(512, common_dim)
        self.image_self_attention = nn.MultiheadAttention(common_dim, 8, batch_first=False)
        self.text_self_attention = nn.MultiheadAttention(common_dim, 8, batch_first=False)
        self.image_cross_attention = nn.MultiheadAttention(common_dim, 8, batch_first=False)
        self.text_cross_attention = nn.MultiheadAttention(common_dim, 8, batch_first=False)
        self.img_gate = nn.Linear(common_dim, common_dim)
        self.txt_gate = nn.Linear(common_dim, common_dim)
        self.meta_block = _RGDermMetaBlock(2048, 512)
        self.image_residual = _RGDermGatedResidualBlock(common_dim)
        self.text_residual = _RGDermGatedResidualBlock(common_dim)
        self.fc_fusion = nn.Sequential(
            nn.Linear(common_dim, common_dim),
            nn.LayerNorm(common_dim),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(common_dim, common_dim // 2),
            nn.LayerNorm(common_dim // 2),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(common_dim // 2, num_classes),
        )
        self.fc_visual_only = nn.Linear(2048, num_classes)
        self.fc_mlp_module_after_metablock_fusion_module = nn.Sequential(
            nn.Linear(2048, common_dim),
            nn.LayerNorm(common_dim),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(common_dim, common_dim // 2),
            nn.LayerNorm(common_dim // 2),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(common_dim // 2, num_classes),
        )

    def forward(self, image: torch.Tensor) -> torch.Tensor:
        image_features = self.image_encoder(image)
        if image_features.dim() == 4:
            image_features = image_features.mean(dim=(-2, -1))
        projected = self.image_projector(image_features)
        return self.fc_fusion(projected)


def rg_dermnet_pad_status(model_dir: Optional[str] = None) -> Dict[str, Any]:
    root = _rg_dermnet_dir(model_dir)
    weights = root / "weights" / "no-metadata" / "model_resnet-50_with_one-hot-encoder_512_with_best_architecture" / "resnet-50_fold_2" / "model.pth"
    return {
        "status": "available" if weights.exists() else "not_ready",
        "tool_name": "rg_dermnet_pad_status",
        "model_id": "wyctorfogos/rg-dermnet no-metadata resnet-50 fold 2",
        "source_repo": "https://huggingface.co/wyctorfogos/rg-dermnet",
        "github_repo": "https://github.com/wyctorfogos/rg-dermnet",
        "license": "MIT per HuggingFace model card",
        "model_dir": str(root),
        "weights_path": str(weights),
        "weights_exist": weights.exists(),
        "classes": [label for _, label in PAD_LABELS],
        "task": "PAD-UFES-20 clinical skin lesion photograph classification",
        "input_visible_only": True,
        "gold_label_used": False,
        "future_cases_used": False,
        "setup_hint": "Download wyctorfogos/rg-dermnet weights/no-metadata/.../model.pth under HEALTHCLAW_RG_DERMNET_DIR.",
    }


def _load_rg_dermnet_pad_model(model_dir: Optional[str] = None):
    root = _rg_dermnet_dir(model_dir)
    weights = root / "weights" / "no-metadata" / "model_resnet-50_with_one-hot-encoder_512_with_best_architecture" / "resnet-50_fold_2" / "model.pth"
    cache_key = f"rg_dermnet_pad:{weights.resolve()}"
    if cache_key in _MODEL_CACHE:
        return _MODEL_CACHE[cache_key]
    if not weights.exists():
        raise FileNotFoundError(f"missing RG-DermNet PAD checkpoint: {weights}")
    model = _RGDermNoMetadataModel(num_classes=len(PAD_LABELS), vocab_size=91, common_dim=512)
    state = torch.load(weights, map_location="cpu", weights_only=True)
    model.load_state_dict(state, strict=True)
    model.eval()
    if torch.cuda.is_available():
        model = model.cuda()
    transform = transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ]
    )
    _MODEL_CACHE[cache_key] = (model, transform)
    return _MODEL_CACHE[cache_key]


def rg_dermnet_pad_classify(
    image_path: str,
    label_options: Optional[Iterable[str]] = None,
    model_dir: Optional[str] = None,
) -> Dict[str, Any]:
    started = time.time()
    status = rg_dermnet_pad_status(model_dir)
    if status["status"] != "available":
        return {**status, "tool_name": "rg_dermnet_pad_classify"}
    path = Path(image_path).expanduser()
    if not path.exists():
        return {
            "status": "error",
            "tool_name": "rg_dermnet_pad_classify",
            "message": f"image_path does not exist: {image_path}",
            "input_visible_only": True,
            "gold_label_used": False,
            "future_cases_used": False,
        }
    try:
        model, transform = _load_rg_dermnet_pad_model(model_dir)
        image = Image.open(path).convert("RGB")
        tensor = transform(image).unsqueeze(0)
        if torch.cuda.is_available():
            tensor = tensor.cuda()
        with torch.no_grad():
            probs = torch.softmax(model(tensor), dim=-1)[0]

        class_scores = []
        for idx, (code, label) in enumerate(PAD_LABELS):
            class_scores.append({
                "model_class": code,
                "label": label,
                "probability": float(probs[idx].detach().cpu()),
            })
        class_scores.sort(key=lambda x: float(x["probability"]), reverse=True)
        label_to_idx = {label: idx for idx, (_, label) in enumerate(PAD_LABELS)}
        labels = [str(x) for x in (label_options or status["classes"]) if str(x).strip()]
        option_scores = []
        for label in labels:
            idx = label_to_idx.get(label)
            if idx is None:
                option_scores.append({"label": label, "probability": None, "covered_by_model": False})
                continue
            option_scores.append({
                "label": label,
                "model_class": PAD_LABELS[idx][0],
                "probability": float(probs[idx].detach().cpu()),
                "covered_by_model": True,
            })
        option_scores.sort(key=lambda x: -1.0 if x.get("probability") is None else float(x["probability"]), reverse=True)
        covered = [x for x in option_scores if x.get("covered_by_model")]
        top = covered[0] if covered else None
        return {
            "status": "success",
            "tool_name": "rg_dermnet_pad_classify",
            "model_id": status["model_id"],
            "source_repo": status["source_repo"],
            "github_repo": status["github_repo"],
            "license": status["license"],
            "image_path": str(path),
            "class_scores": class_scores,
            "label_candidates": option_scores,
            "top_label_candidate": top,
            "recommended_final_label": top.get("label") if isinstance(top, dict) else None,
            "recommended_final_confidence": top.get("probability") if isinstance(top, dict) else None,
            "recommended_final_basis": "rg_dermnet_pad_no_metadata_image_classifier",
            "evidence_strength": "moderate_to_strong",
            "label_coverage": "exact",
            "domain_match": "PAD-UFES-20 clinical skin lesion photograph",
            "calibration_note": "PAD-UFES-20 no-metadata RG-DermNet image classifier; probabilities are softmax scores, not externally calibrated.",
            "class_bias_risk": "Model is trained on PAD-UFES-20 folds and may underpredict basal cell carcinoma in the current fixed-20 probe.",
            "recommended_use": "primary_if_consistent",
            "input_visible_only": True,
            "gold_label_used": False,
            "future_cases_used": False,
            "latency_ms": int((time.time() - started) * 1000),
            "warning": "Released RG-DermNet weights were trained on PAD-UFES-20 cross-validation folds; report source-overlap risk when evaluating PAD-UFES-20 streams.",
        }
    except Exception as exc:
        return {
            "status": "error",
            "tool_name": "rg_dermnet_pad_classify",
            "message": str(exc)[:800],
            "input_visible_only": True,
            "gold_label_used": False,
            "future_cases_used": False,
            "latency_ms": int((time.time() - started) * 1000),
        }
