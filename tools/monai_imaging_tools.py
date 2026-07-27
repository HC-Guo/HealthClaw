"""
Wrappers for real MONAI Model Zoo imaging bundles.

This module intentionally does not implement hand-written diagnostic rules. It
checks and prepares calls to external MONAI bundles such as lung nodule CT
detection and BraTS brain MRI segmentation. Actual inference requires MONAI and
bundle weights/configs to be installed or downloaded by the user.
"""
from __future__ import annotations

import importlib.util
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional


MONAI_BUNDLES = {
    "ct_lung_nodule_detection": {
        "bundle_name": "lung_nodule_ct_detection",
        "task_family": "ct",
        "modality": "ct",
        "evidence_type": "3d_lung_nodule_detection",
        "model_zoo_source": "https://github.com/Project-MONAI/model-zoo/tree/dev/models/lung_nodule_ct_detection",
        "recommended_for": ["LUNA16/LIDC-IDRI style full-volume lung nodule detection"],
        "expected_outputs": ["predicted_box", "classification_label", "classification_score"],
        "limitations": [
            "This bundle detects candidate lung nodules in full CT volumes.",
            "It is not a benign-vs-malignant classifier for cropped NoduleMNIST3D samples.",
        ],
    },
    "mri_brats_segmentation": {
        "bundle_name": "brats_mri_segmentation",
        "task_family": "mri",
        "modality": "mri",
        "evidence_type": "brain_tumor_subregion_segmentation",
        "model_zoo_source": "https://github.com/Project-MONAI/model-zoo/tree/dev/models/brats_mri_segmentation",
        "recommended_for": ["MSD Task01 BrainTumour"],
        "expected_outputs": ["tumor_core", "whole_tumor", "enhancing_tumor"],
        "limitations": ["Requires MONAI runtime and BraTS-like multimodal MRI input formatting."],
    },
}


def _default_bundle_dir() -> Path:
    return Path(os.environ.get("HEALTHCLAW_MONAI_BUNDLE_DIR", "external_models/monai_bundles")).expanduser()


def _monai_available() -> bool:
    return importlib.util.find_spec("monai") is not None


def _bundle_root(bundle_key: str, bundle_dir: Optional[str] = None) -> Path:
    info = MONAI_BUNDLES[bundle_key]
    return Path(bundle_dir).expanduser() / info["bundle_name"] if bundle_dir else _default_bundle_dir() / info["bundle_name"]


def monai_bundle_status(bundle_key: str, bundle_dir: Optional[str] = None) -> Dict[str, Any]:
    """Return availability metadata for a MONAI model-zoo bundle."""
    if bundle_key not in MONAI_BUNDLES:
        return {
            "status": "error",
            "tool_name": "monai_bundle_status",
            "message": f"Unknown bundle_key: {bundle_key}",
            "available_bundle_keys": sorted(MONAI_BUNDLES),
            "input_visible_only": True,
        }
    info = MONAI_BUNDLES[bundle_key]
    root = _bundle_root(bundle_key, bundle_dir)
    config = root / "configs" / "inference.json"
    model_pt = root / "models" / "model.pt"
    return {
        "status": "available" if _monai_available() and config.exists() and model_pt.exists() else "not_ready",
        "tool_name": "monai_bundle_status",
        "bundle_key": bundle_key,
        "bundle_name": info["bundle_name"],
        "task_family": info["task_family"],
        "modality": info["modality"],
        "evidence_type": info["evidence_type"],
        "source": info["model_zoo_source"],
        "recommended_for": info["recommended_for"],
        "expected_outputs": info["expected_outputs"],
        "limitations": info.get("limitations", []),
        "monai_installed": _monai_available(),
        "bundle_root": str(root),
        "inference_config_exists": config.exists(),
        "model_weights_exist": model_pt.exists(),
        "input_visible_only": True,
        "gold_label_used": False,
        "future_cases_used": False,
        "setup_hint": (
            f"Install MONAI and download with: python -m monai.bundle download "
            f"\"{info['bundle_name']}\" --bundle_dir \"{str(_default_bundle_dir())}\""
        ),
    }


def monai_bundle_command(
    bundle_key: str,
    output_dir: str,
    bundle_dir: Optional[str] = None,
    dataset_dir: Optional[str] = None,
    extra_overrides: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Build an official MONAI bundle inference command without executing it.

    MONAI bundle configs differ by task. The caller may pass dataset_dir and
    explicit config overrides only when they come from visible/current inputs.
    """
    status = monai_bundle_status(bundle_key, bundle_dir=bundle_dir)
    if status.get("status") == "error":
        return status
    root = Path(status["bundle_root"])
    cmd = [
        "python",
        "-m",
        "monai.bundle",
        "run",
        "--bundle_root",
        str(root),
        "--config_file",
        str(root / "configs" / "inference.json"),
    ]
    if dataset_dir:
        cmd.extend(["--dataset_dir", dataset_dir])
    for item in extra_overrides or []:
        cmd.append(str(item))
    return {
        "status": "command_ready" if status.get("status") == "available" else "not_ready",
        "tool_name": "monai_bundle_command",
        "bundle_key": bundle_key,
        "bundle_status": status,
        "command": cmd,
        "output_dir": output_dir,
        "input_visible_only": True,
        "gold_label_used": False,
        "future_cases_used": False,
        "warning": "Command is generated but not executed; verify bundle config input keys for the target dataset.",
    }


def run_monai_bundle_command(command: List[str], timeout: int = 1800) -> Dict[str, Any]:
    """Execute a prebuilt MONAI command. Callers should log command provenance."""
    if not command:
        return {"status": "error", "tool_name": "run_monai_bundle_command", "message": "empty command"}
    if command[:4] != ["python", "-m", "monai.bundle", "run"]:
        return {
            "status": "error",
            "tool_name": "run_monai_bundle_command",
            "message": "refusing to run non-MONAI-bundle command",
            "command": command,
        }
    try:
        proc = subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)
    except Exception as exc:
        return {"status": "error", "tool_name": "run_monai_bundle_command", "message": str(exc), "command": command}
    return {
        "status": "success" if proc.returncode == 0 else "error",
        "tool_name": "run_monai_bundle_command",
        "returncode": proc.returncode,
        "stdout": proc.stdout[-4000:],
        "stderr": proc.stderr[-4000:],
        "command": command,
        "input_visible_only": True,
        "gold_label_used": False,
        "future_cases_used": False,
    }
