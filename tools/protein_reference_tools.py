"""
Wrappers for real protein language-model tools.

The initial implementation uses FAIR ESM for local missense variant scoring.
It adapts the standard log-probability delta idea from ESM variant prediction;
it does not implement hand-written biochemical pathogenicity rules.
"""
from __future__ import annotations

import importlib.util
import math
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

import torch


ESM_SOURCE_ENV = "HEALTHCLAW_ESM_SOURCE_DIR"
DEFAULT_ESM_MODEL = "esm2_t6_8M_UR50D"
_ESM_CACHE: Dict[str, Any] = {}


def _maybe_add_esm_source(source_dir: Optional[str]) -> Optional[Path]:
    source = source_dir or os.environ.get(ESM_SOURCE_ENV)
    if not source:
        return None
    path = Path(source).expanduser().resolve()
    if path.exists() and str(path) not in sys.path:
        sys.path.insert(0, str(path))
    return path


def _esm_import_available(source_dir: Optional[str] = None) -> bool:
    _maybe_add_esm_source(source_dir)
    return importlib.util.find_spec("esm") is not None


def esm_variant_effect_status(source_dir: Optional[str] = None, model_name: str = DEFAULT_ESM_MODEL) -> Dict[str, Any]:
    source = _maybe_add_esm_source(source_dir)
    return {
        "status": "available_if_weights_downloadable" if _esm_import_available(source_dir) else "not_ready",
        "tool_name": "esm_variant_effect_status",
        "model_name": model_name,
        "source_repo": "https://github.com/facebookresearch/esm",
        "paper": "Language models enable zero-shot prediction of the effects of mutations on protein function",
        "input_visible_only": True,
        "gold_label_used": False,
        "future_cases_used": False,
        "source_dir": str(source) if source else None,
        "setup_hint": "Set HEALTHCLAW_ESM_SOURCE_DIR to a local FAIR ESM checkout or install fair-esm.",
    }


def _load_esm_model(model_name: str, source_dir: Optional[str] = None):
    cache_key = f"{model_name}::{source_dir or os.environ.get(ESM_SOURCE_ENV, '')}"
    if cache_key in _ESM_CACHE:
        return _ESM_CACHE[cache_key]
    _maybe_add_esm_source(source_dir)
    from esm import pretrained

    model, alphabet = pretrained.load_model_and_alphabet(model_name)
    model.eval()
    if torch.cuda.is_available():
        model = model.cuda()
    _ESM_CACHE[cache_key] = (model, alphabet)
    return model, alphabet


def _parse_mutation(mutation: str) -> tuple[str, int, str] | None:
    match = re.search(r"\b([A-Z])(\d+)([A-Z])\b", str(mutation or "").upper())
    if not match:
        return None
    return match.group(1), int(match.group(2)), match.group(3)


def _extract_mutation_from_text(text: str) -> str:
    match = re.search(r"\b[A-Z]\d+[A-Z]\b", str(text or "").upper())
    return match.group(0) if match else ""


def _parse_visible_window(local_window: str, mutation: str) -> tuple[str, int, str, str] | None:
    parsed = _parse_mutation(mutation)
    if not parsed:
        return None
    wt, _pos, mt = parsed
    text = str(local_window or "")
    bracket = re.search(r"([A-Z]+)\[([A-Z])\]([A-Z]+)", text.upper())
    if bracket:
        seq = bracket.group(1) + bracket.group(2) + bracket.group(3)
        idx = len(bracket.group(1))
        return seq, idx, wt, mt
    clean = re.sub(r"[^A-Z]", "", text.upper())
    if not clean:
        return None
    center = len(clean) // 2
    return clean, center, wt, mt


def _extract_local_window_from_text(text: str) -> str:
    match = re.search(r"Local wild-type sequence window:\s*([^\n]+)", str(text or ""), flags=re.I)
    return match.group(1).strip() if match else ""


def _log_prob_delta(model: Any, alphabet: Any, sequence: str, index: int, wt: str, mt: str) -> tuple[float, float, float]:
    if index < 0 or index >= len(sequence):
        raise ValueError(f"mutation index {index} is outside sequence length {len(sequence)}")
    if sequence[index] != wt:
        raise ValueError(f"wild-type mismatch: visible sequence has {sequence[index]} at local index {index}, mutation says {wt}")
    batch_converter = alphabet.get_batch_converter()
    _, _, tokens = batch_converter([("protein", sequence)])
    if torch.cuda.is_available():
        tokens = tokens.cuda()
    with torch.no_grad():
        logits = model(tokens)["logits"]
        log_probs = torch.log_softmax(logits, dim=-1)
    token_pos = index + 1  # account for BOS token
    wt_logp = float(log_probs[0, token_pos, alphabet.get_idx(wt)].detach().cpu())
    mt_logp = float(log_probs[0, token_pos, alphabet.get_idx(mt)].detach().cpu())
    return mt_logp - wt_logp, wt_logp, mt_logp


def esm_local_variant_effect_score(
    mutation: str = "",
    local_window: str = "",
    visible_input: str = "",
    source_dir: Optional[str] = None,
    model_name: str = DEFAULT_ESM_MODEL,
) -> Dict[str, Any]:
    """Score a visible missense mutation using FAIR ESM on the visible local sequence window."""
    started = time.time()
    if not _esm_import_available(source_dir):
        status = esm_variant_effect_status(source_dir=source_dir, model_name=model_name)
        return {**status, "status": "not_ready", "tool_name": "esm_local_variant_effect_score"}
    mutation = mutation or _extract_mutation_from_text(visible_input)
    local_window = local_window or _extract_local_window_from_text(visible_input)
    parsed = _parse_visible_window(local_window, mutation)
    if not parsed:
        return {
            "status": "error",
            "tool_name": "esm_local_variant_effect_score",
            "message": "Could not parse mutation/local_window from visible input.",
            "input_visible_only": True,
            "gold_label_used": False,
            "future_cases_used": False,
        }
    sequence, index, wt, mt = parsed
    try:
        model, alphabet = _load_esm_model(model_name, source_dir=source_dir)
        delta, wt_logp, mt_logp = _log_prob_delta(model, alphabet, sequence, index, wt, mt)
        candidate = "Pathogenic" if delta < 0 else "Benign"
        confidence_proxy = 1.0 / (1.0 + math.exp(-abs(delta)))
        return {
            "status": "success",
            "tool_name": "esm_local_variant_effect_score",
            "model_name": model_name,
            "source_repo": "https://github.com/facebookresearch/esm",
            "mutation": mutation,
            "visible_sequence_window": sequence,
            "local_mutation_index_0based": index,
            "wt": wt,
            "mt": mt,
            "delta_log_prob_mt_minus_wt": delta,
            "wt_log_prob": wt_logp,
            "mt_log_prob": mt_logp,
            "label_candidates": [
                {"label": candidate, "score": abs(delta), "calibration": "uncalibrated_sign_of_esm_delta"},
                {"label": "Benign" if candidate == "Pathogenic" else "Pathogenic", "score": -abs(delta), "calibration": "uncalibrated_sign_of_esm_delta"},
            ],
            "top_label_candidate": {"label": candidate, "confidence_proxy": confidence_proxy},
            "input_scope": "visible local wild-type sequence window only; full protein sequence was not available",
            "input_visible_only": True,
            "gold_label_used": False,
            "future_cases_used": False,
            "latency_ms": int((time.time() - started) * 1000),
            "warning": "ESM local-window score is zero-shot evidence, not a calibrated clinical pathogenicity classifier.",
        }
    except Exception as exc:
        return {
            "status": "error",
            "tool_name": "esm_local_variant_effect_score",
            "message": str(exc)[:800],
            "input_visible_only": True,
            "gold_label_used": False,
            "future_cases_used": False,
            "latency_ms": int((time.time() - started) * 1000),
        }
