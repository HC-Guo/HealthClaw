"""
Wrappers for real retinal/fundus foundation-model tools.

The first implementation targets FLAIR, a retina vision-language foundation
model. This module only adapts external model outputs into structured evidence;
it does not implement hand-written ocular disease rules.
"""
from __future__ import annotations

import importlib.util
import contextlib
import io
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import numpy as np
from PIL import Image


FLAIR_MODEL_ID = "jusiro2/FLAIR"
FLAIR_SOURCE_ENV = "HEALTHCLAW_FLAIR_SOURCE_DIR"
_FLAIR_MODEL = None
_FLAIR_TEXT_EMBED_CACHE: Dict[Any, Any] = {}

ODIR_LABEL_PROMPTS = {
    "normal fundus": "normal",
    "diabetic retinopathy": "diabetic retinopathy",
    "glaucoma": "glaucoma",
    "cataract": "cataract",
    "age-related macular degeneration": "age related macular degeneration",
    "hypertensive retinopathy": "hypertensive retinopathy",
    "pathological myopia": "pathologic myopia",
    "other ocular disease or abnormality": "retinal lesion or ocular abnormality",
}

FUNDUS_FEATURE_PROMPTS = [
    "normal healthy retina",
    "diabetic retinopathy",
    "hard exudates",
    "retinal hemorrhage",
    "microaneurysms",
    "glaucoma",
    "optic disc cupping",
    "cataract",
    "age-related macular degeneration",
    "drusen",
    "hypertensive retinopathy",
    "retinal vessel narrowing",
    "pathological myopia",
    "myopic fundus",
    "retinal lesion or ocular abnormality",
]


def _maybe_add_source_dir(source_dir: Optional[str]) -> Optional[Path]:
    source = source_dir or os.environ.get(FLAIR_SOURCE_ENV)
    if not source:
        return None
    path = Path(source).expanduser().resolve()
    if path.exists() and str(path) not in sys.path:
        sys.path.insert(0, str(path))
    return path


def _flair_import_available(source_dir: Optional[str] = None) -> bool:
    _maybe_add_source_dir(source_dir)
    return importlib.util.find_spec("flair") is not None


def flair_fundus_status(source_dir: Optional[str] = None, model_id: str = FLAIR_MODEL_ID) -> Dict[str, Any]:
    """Return whether FLAIR can be imported and what setup is still needed."""
    source = _maybe_add_source_dir(source_dir)
    imported = _flair_import_available(source_dir)
    return {
        "status": "available_if_weights_downloadable" if imported else "not_ready",
        "tool_name": "flair_fundus_status",
        "model_id": model_id,
        "source_repo": "https://github.com/jusiro/FLAIR",
        "paper": "FLAIR: A Foundation LAnguage Image model of the Retina, Medical Image Analysis 2025",
        "license": "Apache-2.0 for code and model weights per upstream README",
        "flair_import_available": imported,
        "source_dir": str(source) if source else None,
        "input_visible_only": True,
        "gold_label_used": False,
        "future_cases_used": False,
        "setup_hint": (
            "Install or expose FLAIR with: pip install git+https://github.com/jusiro/FLAIR.git "
            "or set HEALTHCLAW_FLAIR_SOURCE_DIR to a local FLAIR checkout. "
            "The model loads weights with FLAIRModel.from_pretrained('jusiro2/FLAIR')."
        ),
    }


def _load_flair_model(source_dir: Optional[str] = None, model_id: str = FLAIR_MODEL_ID):
    global _FLAIR_MODEL
    if _FLAIR_MODEL is not None:
        return _FLAIR_MODEL
    _maybe_add_source_dir(source_dir)
    from flair import FLAIRModel

    _FLAIR_MODEL = FLAIRModel.from_pretrained(model_id)
    return _FLAIR_MODEL


def _rank_scores(prompts: List[str], probs: np.ndarray, logits: np.ndarray) -> List[Dict[str, Any]]:
    scores = []
    flat_probs = probs.reshape(-1)
    flat_logits = logits.reshape(-1)
    for prompt, prob, logit in zip(prompts, flat_probs, flat_logits):
        scores.append({"prompt": prompt, "probability": float(prob), "logit": float(logit)})
    scores.sort(key=lambda x: float(x["probability"]), reverse=True)
    return scores


def _label_prompts(label_options: Optional[Iterable[str]]) -> List[str]:
    labels = [str(x) for x in (label_options or []) if str(x).strip()]
    return [ODIR_LABEL_PROMPTS.get(label, label) for label in labels]


def _flair_domain_knowledge_scores(model: Any, image: np.ndarray, prompts: List[str]) -> tuple[np.ndarray, np.ndarray]:
    """Score FLAIR labels with the upstream domain-knowledge text prototypes."""
    import torch

    cache_key = (tuple(prompts), True)
    if cache_key in _FLAIR_TEXT_EMBED_CACHE:
        text_embeds = _FLAIR_TEXT_EMBED_CACHE[cache_key]
    else:
        with contextlib.redirect_stdout(io.StringIO()):
            _, text_embeds = model.compute_text_embeddings(prompts, domain_knowledge=True)
        _FLAIR_TEXT_EMBED_CACHE[cache_key] = text_embeds.detach()
        text_embeds = _FLAIR_TEXT_EMBED_CACHE[cache_key]

    with torch.no_grad():
        img = model.preprocess_image(image)
        img_embeds = model.vision_model(img)
        logits = model.compute_logits(img_embeds, text_embeds.to(img_embeds.device))
        probs = logits.softmax(dim=-1)
    return probs.cpu().numpy(), logits.cpu().numpy()


def flair_fundus_zero_shot(
    image_path: str,
    label_options: Optional[Iterable[str]] = None,
    source_dir: Optional[str] = None,
    model_id: str = FLAIR_MODEL_ID,
    prompt_mode: str = "domain_knowledge",
) -> Dict[str, Any]:
    """
    Run FLAIR zero-shot retinal evidence scoring on a visible fundus image.

    The returned label candidates are model evidence, not a hidden label lookup.
    """
    started = time.time()
    if not image_path:
        return {"status": "error", "tool_name": "flair_fundus_zero_shot", "message": "image_path is empty"}
    path = Path(image_path).expanduser()
    if not path.exists():
        return {
            "status": "error",
            "tool_name": "flair_fundus_zero_shot",
            "message": f"image_path does not exist: {image_path}",
            "input_visible_only": True,
        }
    if not _flair_import_available(source_dir):
        status = flair_fundus_status(source_dir=source_dir, model_id=model_id)
        return {**status, "status": "not_ready", "tool_name": "flair_fundus_zero_shot"}

    try:
        image = np.array(Image.open(path).convert("RGB"))
        model = _load_flair_model(source_dir=source_dir, model_id=model_id)
        label_text = _label_prompts(label_options)
        label_scores: List[Dict[str, Any]] = []
        if label_text:
            if prompt_mode == "domain_knowledge":
                probs, logits = _flair_domain_knowledge_scores(model, image, label_text)
            else:
                probs, logits = model(image, label_text)
            prompt_scores = _rank_scores(label_text, probs, logits)
            reverse = {ODIR_LABEL_PROMPTS.get(label, label): label for label in (label_options or [])}
            for score in prompt_scores:
                label_scores.append({
                    "label": reverse.get(score["prompt"], score["prompt"]),
                    "prompt": score["prompt"],
                    "probability": score["probability"],
                    "logit": score["logit"],
                })
        probs, logits = model(image, FUNDUS_FEATURE_PROMPTS)
        feature_scores = _rank_scores(FUNDUS_FEATURE_PROMPTS, probs, logits)
        return {
            "status": "success",
            "tool_name": "flair_fundus_zero_shot",
            "model_id": model_id,
            "prompt_mode": prompt_mode,
            "source_repo": "https://github.com/jusiro/FLAIR",
            "image_path": str(path),
            "label_candidates": label_scores,
            "top_label_candidate": label_scores[0] if label_scores else None,
            "feature_scores": feature_scores,
            "top_feature_scores": feature_scores[:8],
            "latency_ms": int((time.time() - started) * 1000),
            "input_visible_only": True,
            "gold_label_used": False,
            "future_cases_used": False,
            "warning": "FLAIR zero-shot evidence should be combined with current image context; it is not a hidden-label lookup.",
        }
    except Exception as exc:
        return {
            "status": "error",
            "tool_name": "flair_fundus_zero_shot",
            "message": str(exc)[:800],
            "latency_ms": int((time.time() - started) * 1000),
            "input_visible_only": True,
            "gold_label_used": False,
            "future_cases_used": False,
        }
