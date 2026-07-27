"""
Adapters for DeepLoc-style protein subcellular localization tools.

The available HealthClaw DeepLoc stream exposes sequence excerpts and summary
features, not the full amino-acid sequence. This wrapper therefore reports its
prediction as partial-sequence evidence when only N/C-terminal excerpts are
available.
"""
from __future__ import annotations

import os
import re
import time
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

import torch
from torch import nn


DEEPLOC_MODEL_ENV = "HEALTHCLAW_DEEPLOC_MODEL_DIR"
DEFAULT_MODEL_ID = "zq233/deeploc-esm2-lora"
DEFAULT_BASE_MODEL = "facebook/esm2_t6_8M_UR50D"
DEFAULT_LABELS = [
    "Nucleus",
    "Cytoplasm",
    "Extracellular",
    "Mitochondrion",
    "Cell.membrane",
    "Endoplasmic.reticulum",
    "Plastid",
    "Golgi.apparatus",
    "Lysosome/Vacuole",
    "Peroxisome",
]
_MODEL_CACHE: Dict[str, Any] = {}


def _default_model_dir() -> Path:
    return Path(os.environ.get(DEEPLOC_MODEL_ENV, "external_models/deeploc/zq233_deeploc_esm2_lora")).expanduser()


def _model_dir(model_dir: Optional[str]) -> Path:
    return Path(model_dir).expanduser() if model_dir else _default_model_dir()


class _DeepLocEsm2LoraClassifier(nn.Module):
    def __init__(self, base_model: str = DEFAULT_BASE_MODEL):
        super().__init__()
        from peft import LoraConfig, get_peft_model
        from transformers import AutoModel

        encoder = AutoModel.from_pretrained(base_model)
        lora = LoraConfig(
            r=8,
            lora_alpha=16,
            target_modules=["query", "key", "value"],
            lora_dropout=0.0,
            bias="none",
        )
        self.encoder = get_peft_model(encoder, lora)
        self.head = nn.Sequential(
            nn.Linear(320, 256),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(256, len(DEFAULT_LABELS)),
        )

    def forward(self, input_ids: torch.Tensor, attention_mask: torch.Tensor):
        out = self.encoder(input_ids=input_ids, attention_mask=attention_mask).last_hidden_state
        mask = attention_mask.unsqueeze(-1)
        pooled = (out * mask).sum(1) / mask.sum(1).clamp_min(1)
        return self.head(pooled)


def _extract_visible_sequence(visible_input: str) -> tuple[str, Dict[str, Any]]:
    text = str(visible_input or "")
    length = None
    m = re.search(r"Sequence length:\s*(\d+)", text, flags=re.I)
    if m:
        length = int(m.group(1))
    parts = []
    for pattern in [
        r"N-terminal sequence excerpt \(first \d+ aa\):\s*([A-Z]+)",
        r"C-terminal sequence excerpt \(last \d+ aa\):\s*([A-Z]+)",
        r"Full sequence:\s*([A-Z]+)",
        r"Sequence:\s*([A-Z]+)",
    ]:
        match = re.search(pattern, text, flags=re.I)
        if match:
            parts.append(match.group(1).upper())
    sequence = "".join(parts)
    sequence = re.sub(r"[^ACDEFGHIKLMNPQRSTVWYBXZUO]", "", sequence)
    coverage = None
    if length and sequence:
        coverage = min(1.0, len(sequence) / float(length))
    meta = {
        "reported_sequence_length": length,
        "visible_sequence_length": len(sequence),
        "estimated_visible_sequence_coverage": coverage,
        "partial_sequence_only": bool(length and len(sequence) < length),
    }
    return sequence, meta


def deeploc_esm2_lora_status(model_dir: Optional[str] = None) -> Dict[str, Any]:
    root = _model_dir(model_dir)
    weights = root / "best_classification.pt"
    missing = []
    try:
        import peft  # noqa: F401
        import transformers  # noqa: F401
    except Exception as exc:
        missing.append(f"peft/transformers import failed: {exc}")
    return {
        "status": "available" if weights.exists() and not missing else "not_ready",
        "tool_name": "deeploc_esm2_lora_status",
        "model_id": DEFAULT_MODEL_ID,
        "base_model": DEFAULT_BASE_MODEL,
        "source_repo": "https://huggingface.co/zq233/deeploc-esm2-lora",
        "model_dir": str(root),
        "weights_path": str(weights),
        "weights_exist": weights.exists(),
        "missing_requirements": missing,
        "classes": DEFAULT_LABELS,
        "input_visible_only": True,
        "gold_label_used": False,
        "future_cases_used": False,
        "setup_hint": "Download best_classification.pt from HuggingFace, preferably with HF_ENDPOINT=https://hf-mirror.com.",
    }


def _load_model(model_dir: Optional[str] = None):
    root = _model_dir(model_dir)
    weights = root / "best_classification.pt"
    cache_key = f"deeploc:{weights.resolve()}"
    if cache_key in _MODEL_CACHE:
        return _MODEL_CACHE[cache_key]
    if not weights.exists():
        raise FileNotFoundError(f"missing DeepLoc ESM2 LoRA checkpoint: {weights}")

    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(DEFAULT_BASE_MODEL)
    model = _DeepLocEsm2LoraClassifier(DEFAULT_BASE_MODEL)
    state = torch.load(weights, map_location="cpu", weights_only=True)
    model.load_state_dict(state, strict=True)
    model.eval()
    if torch.cuda.is_available():
        model = model.cuda()
    _MODEL_CACHE[cache_key] = (model, tokenizer)
    return _MODEL_CACHE[cache_key]


def deeploc_esm2_lora_classify(
    visible_input: str,
    label_options: Optional[Iterable[str]] = None,
    model_dir: Optional[str] = None,
) -> Dict[str, Any]:
    started = time.time()
    status = deeploc_esm2_lora_status(model_dir)
    if status["status"] != "available":
        return {**status, "tool_name": "deeploc_esm2_lora_classify"}
    sequence, seq_meta = _extract_visible_sequence(visible_input)
    if not sequence:
        return {
            "status": "error",
            "tool_name": "deeploc_esm2_lora_classify",
            "message": "No visible amino-acid sequence excerpt found.",
            "input_visible_only": True,
            "gold_label_used": False,
            "future_cases_used": False,
        }
    try:
        model, tokenizer = _load_model(model_dir)
        inputs = tokenizer(sequence, return_tensors="pt", truncation=True, max_length=1024)
        if torch.cuda.is_available():
            inputs = {k: v.cuda() for k, v in inputs.items()}
        with torch.no_grad():
            probs = torch.softmax(model(**inputs), dim=-1)[0]
        class_scores = [
            {"label": label, "probability": float(probs[idx].detach().cpu())}
            for idx, label in enumerate(DEFAULT_LABELS)
        ]
        class_scores.sort(key=lambda x: float(x["probability"]), reverse=True)
        labels = [str(x) for x in (label_options or DEFAULT_LABELS) if str(x).strip()]
        option_scores = []
        for label in labels:
            if label in DEFAULT_LABELS:
                idx = DEFAULT_LABELS.index(label)
                option_scores.append({"label": label, "probability": float(probs[idx].detach().cpu()), "covered_by_model": True})
            else:
                option_scores.append({"label": label, "probability": None, "covered_by_model": False})
        option_scores.sort(key=lambda x: -1.0 if x.get("probability") is None else float(x["probability"]), reverse=True)
        covered = [x for x in option_scores if x.get("covered_by_model")]
        return {
            "status": "success",
            "tool_name": "deeploc_esm2_lora_classify",
            "model_id": DEFAULT_MODEL_ID,
            "base_model": DEFAULT_BASE_MODEL,
            "source_repo": "https://huggingface.co/zq233/deeploc-esm2-lora",
            "sequence_evidence": seq_meta,
            "class_scores": class_scores,
            "label_candidates": option_scores,
            "top_label_candidate": covered[0] if covered else None,
            "input_visible_only": True,
            "gold_label_used": False,
            "future_cases_used": False,
            "latency_ms": int((time.time() - started) * 1000),
            "warning": "Current HealthClaw DeepLoc cases expose N/C-terminal excerpts and summary features, not complete sequences; treat this as partial-sequence evidence.",
        }
    except Exception as exc:
        return {
            "status": "error",
            "tool_name": "deeploc_esm2_lora_classify",
            "message": str(exc)[:800],
            "input_visible_only": True,
            "gold_label_used": False,
            "future_cases_used": False,
            "latency_ms": int((time.time() - started) * 1000),
        }
