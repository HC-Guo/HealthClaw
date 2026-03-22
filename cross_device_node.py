#!/usr/bin/env python3
"""Run a generic cross-device OpenClaw node service."""
import argparse
import copy
import hmac
import json
import os
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


DEFAULT_BINDINGS_PATH = "memory/device_bindings.json"


DEMO_LOCATION_PRESETS = {
    "heart_rate_spike": {
        "location_text": "复旦大学邯郸校区 6 号楼 203 室",
        "campus": "复旦大学邯郸校区",
        "building": "6 号楼",
        "room": "203 室",
        "source": "demo_simulated_wearable_location",
    },
    "low_oxygen": {
        "location_text": "复旦大学邯郸校区 5 号楼 305 室",
        "campus": "复旦大学邯郸校区",
        "building": "5 号楼",
        "room": "305 室",
        "source": "demo_simulated_wearable_location",
    },
    "fall_detected": {
        "location_text": "复旦大学邯郸校区 2 号楼 102 室门口走廊",
        "campus": "复旦大学邯郸校区",
        "building": "2 号楼",
        "room": "102 室门口",
        "source": "demo_simulated_wearable_location",
    },
    "irregular_rhythm": {
        "location_text": "复旦大学邯郸校区 4 号楼 301 室",
        "campus": "复旦大学邯郸校区",
        "building": "4 号楼",
        "room": "301 室",
        "source": "demo_simulated_wearable_location",
    },
    "high_temperature": {
        "location_text": "复旦大学邯郸校区 7 号楼 318 室",
        "campus": "复旦大学邯郸校区",
        "building": "7 号楼",
        "room": "318 室",
        "source": "demo_simulated_wearable_location",
    },
    "prolonged_inactivity": {
        "location_text": "复旦大学邯郸校区 8 号楼 206 室",
        "campus": "复旦大学邯郸校区",
        "building": "8 号楼",
        "room": "206 室",
        "source": "demo_simulated_wearable_location",
    },
}


DEMO_SIGNAL_SCENARIOS = {
    "heart_rate_spike": {
        "label": "心率持续过快",
        "description": "",
        "alert_payload": {
            "signal_type": "heart_rate",
            "heart_rate": 145,
            "duration_sec": 120,
            "threshold": 130,
            "min_duration_sec": 60,
            "activity_state": "resting",
            "location": DEMO_LOCATION_PRESETS["heart_rate_spike"],
        },
        "safe_payload": {
            "signal_type": "heart_rate",
            "heart_rate": 88,
            "duration_sec": 20,
            "threshold": 130,
            "min_duration_sec": 60,
            "activity_state": "resting",
            "location": DEMO_LOCATION_PRESETS["heart_rate_spike"],
        },
    },
    "low_oxygen": {
        "label": "血氧持续偏低",
        "description": "模拟可穿戴设备检测到血氧持续低于安全阈值。",
        "alert_payload": {
            "signal_type": "blood_oxygen",
            "spo2": 88,
            "duration_sec": 180,
            "low_threshold": 90,
            "min_duration_sec": 120,
            "location": DEMO_LOCATION_PRESETS["low_oxygen"],
        },
        "safe_payload": {
            "signal_type": "blood_oxygen",
            "spo2": 97,
            "duration_sec": 60,
            "low_threshold": 90,
            "min_duration_sec": 120,
            "location": DEMO_LOCATION_PRESETS["low_oxygen"],
        },
    },
    "fall_detected": {
        "label": "疑似跌倒",
        "description": "模拟手表/胸牌检测到跌倒冲击并且老人短时间内没有恢复活动。",
        "alert_payload": {
            "signal_type": "fall_detected",
            "fall_detected": True,
            "impact_g": 3.4,
            "no_movement_sec": 45,
            "response_status": "no_response",
            "location": DEMO_LOCATION_PRESETS["fall_detected"],
        },
        "safe_payload": {
            "signal_type": "fall_detected",
            "fall_detected": False,
            "impact_g": 0.8,
            "no_movement_sec": 0,
            "response_status": "normal",
            "location": DEMO_LOCATION_PRESETS["fall_detected"],
        },
    },
    "irregular_rhythm": {
        "label": "疑似心律不齐",
        "description": "模拟可穿戴 ECG 或脉搏节律算法提示可能存在心律不齐。",
        "alert_payload": {
            "signal_type": "irregular_rhythm",
            "irregular_rhythm_detected": True,
            "duration_sec": 90,
            "min_duration_sec": 45,
            "episode_count": 3,
            "resting_heart_rate": 128,
            "location": DEMO_LOCATION_PRESETS["irregular_rhythm"],
        },
        "safe_payload": {
            "signal_type": "irregular_rhythm",
            "irregular_rhythm_detected": False,
            "duration_sec": 15,
            "min_duration_sec": 45,
            "episode_count": 0,
            "resting_heart_rate": 78,
            "location": DEMO_LOCATION_PRESETS["irregular_rhythm"],
        },
    },
    "high_temperature": {
        "label": "体温异常升高",
        "description": "模拟可穿戴体温传感器提示持续发热。",
        "alert_payload": {
            "signal_type": "body_temperature",
            "body_temperature": 39.1,
            "duration_sec": 1800,
            "high_threshold": 38.5,
            "low_threshold": 35.0,
            "min_duration_sec": 600,
            "location": DEMO_LOCATION_PRESETS["high_temperature"],
        },
        "safe_payload": {
            "signal_type": "body_temperature",
            "body_temperature": 36.7,
            "duration_sec": 600,
            "high_threshold": 38.5,
            "low_threshold": 35.0,
            "min_duration_sec": 600,
            "location": DEMO_LOCATION_PRESETS["high_temperature"],
        },
    },
    "prolonged_inactivity": {
        "label": "长时间无活动",
        "description": "模拟老人佩戴设备连续数小时无明显活动。",
        "alert_payload": {
            "signal_type": "inactivity",
            "inactivity_minutes": 180,
            "threshold_minutes": 120,
            "during_sleep": False,
            "last_motion_ago_minutes": 180,
            "location": DEMO_LOCATION_PRESETS["prolonged_inactivity"],
        },
        "safe_payload": {
            "signal_type": "inactivity",
            "inactivity_minutes": 45,
            "threshold_minutes": 120,
            "during_sleep": False,
            "last_motion_ago_minutes": 45,
            "location": DEMO_LOCATION_PRESETS["prolonged_inactivity"],
        },
    },
}


def get_demo_signal_scenarios():
    return copy.deepcopy(DEMO_SIGNAL_SCENARIOS)


def build_demo_signal_payload(scenario_key, sender_id="elder_01", safe=False):
    scenarios = get_demo_signal_scenarios()
    if scenario_key not in scenarios:
        raise KeyError(f"unknown demo scenario: {scenario_key}")
    payload_key = "safe_payload" if safe else "alert_payload"
    payload = scenarios[scenario_key][payload_key]
    payload["sender_id"] = sender_id
    return payload


def _coerce_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _coerce_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _coerce_bool(value, default=False):
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        text = value.strip().lower()
        if text in {"1", "true", "yes", "y", "on", "detected"}:
            return True
        if text in {"0", "false", "no", "n", "off", "", "none"}:
            return False
    return default


def _normalize_location(payload):
    raw = payload.get("location")
    location = None
    if isinstance(raw, str):
        text = raw.strip()
        if text:
            location = {"location_text": text}
    elif isinstance(raw, dict):
        location = {str(k): v for k, v in raw.items() if v not in (None, "")}

    if location is None:
        text = str(payload.get("location_text", "") or "").strip()
        if text:
            location = {"location_text": text}

    if location is None:
        return None

    if not location.get("location_text"):
        parts = [
            str(location.get("campus", "") or "").strip(),
            str(location.get("building", "") or "").strip(),
            str(location.get("room", "") or "").strip(),
        ]
        location_text = " ".join([item for item in parts if item])
        if not location_text:
            return None
        location["location_text"] = location_text

    if payload.get("location_source") and not location.get("source"):
        location["source"] = str(payload.get("location_source"))

    return location


def _attach_location(decision, payload):
    location = _normalize_location(payload)
    if not location:
        return decision
    decision["location"] = copy.deepcopy(location)
    decision["details"]["location"] = copy.deepcopy(location)
    return decision


def _base_context(payload):
    signal_type = str(payload.get("signal_type", "heart_rate") or "heart_rate")
    sender_id = str(payload.get("sender_id", "") or "")
    severity = str(payload.get("severity", "") or "")
    timestamp = str(payload.get("timestamp", "") or time.strftime("%Y-%m-%d %H:%M:%S"))
    return signal_type, sender_id, severity, timestamp


def _evaluate_heart_rate(payload):
    signal_type, sender_id, severity, timestamp = _base_context(payload)
    heart_rate = _coerce_int(payload.get("heart_rate", payload.get("value", 0)), 0)
    duration_sec = _coerce_int(payload.get("duration_sec", 0), 0)
    threshold = _coerce_int(payload.get("threshold", 130), 130)
    min_duration_sec = _coerce_int(payload.get("min_duration_sec", 60), 60)
    activity_state = str(payload.get("activity_state", "unknown") or "unknown")
    triggered = heart_rate >= threshold and duration_sec >= min_duration_sec
    if triggered:
        default_message = f"检测到老人心率异常升高（{heart_rate} bpm，持续 {duration_sec}s），请尽快查看。"
    else:
        default_message = (
            f"当前心率为 {heart_rate} bpm，持续 {duration_sec}s，尚未达到 "
            f"{threshold} bpm 且持续 {min_duration_sec}s 的预警条件。"
        )
    decision = {
        "triggered": triggered,
        "supported": True,
        "signal_type": signal_type,
        "sender_id": sender_id,
        "timestamp": timestamp,
        "heart_rate": heart_rate,
        "duration_sec": duration_sec,
        "threshold": threshold,
        "min_duration_sec": min_duration_sec,
        "severity": severity or "critical",
        "message": payload.get("message") or default_message,
        "event_type": "heart_rate_alert",
        "details": {
            "heart_rate": heart_rate,
            "duration_sec": duration_sec,
            "activity_state": activity_state,
            "rule": {
                "threshold": threshold,
                "min_duration_sec": min_duration_sec,
            },
        },
    }
    if not triggered:
        decision["reason"] = "threshold_not_met"
    return _attach_location(decision, payload)


def _evaluate_blood_oxygen(payload):
    signal_type, sender_id, severity, timestamp = _base_context(payload)
    spo2 = _coerce_int(payload.get("spo2", payload.get("value", 0)), 0)
    duration_sec = _coerce_int(payload.get("duration_sec", 0), 0)
    low_threshold = _coerce_int(payload.get("low_threshold", 90), 90)
    min_duration_sec = _coerce_int(payload.get("min_duration_sec", 120), 120)
    triggered = 0 < spo2 <= low_threshold and duration_sec >= min_duration_sec
    if triggered:
        default_message = f"检测到老人血氧偏低（SpO2 {spo2}% ，持续 {duration_sec}s），请尽快确认呼吸状态。"
    else:
        default_message = (
            f"当前血氧为 {spo2}% ，持续 {duration_sec}s，尚未达到持续低于 "
            f"{low_threshold}% 且持续 {min_duration_sec}s 的预警条件。"
        )
    decision = {
        "triggered": triggered,
        "supported": True,
        "signal_type": signal_type,
        "sender_id": sender_id,
        "timestamp": timestamp,
        "spo2": spo2,
        "duration_sec": duration_sec,
        "low_threshold": low_threshold,
        "min_duration_sec": min_duration_sec,
        "severity": severity or "critical",
        "message": payload.get("message") or default_message,
        "event_type": "blood_oxygen_alert",
        "details": {
            "spo2": spo2,
            "duration_sec": duration_sec,
            "rule": {
                "low_threshold": low_threshold,
                "min_duration_sec": min_duration_sec,
            },
        },
    }
    if not triggered:
        decision["reason"] = "threshold_not_met"
    return _attach_location(decision, payload)


def _evaluate_fall_detected(payload):
    signal_type, sender_id, severity, timestamp = _base_context(payload)
    fall_detected = _coerce_bool(payload.get("fall_detected", payload.get("value", False)), False)
    impact_g = _coerce_float(payload.get("impact_g", 0.0), 0.0)
    no_movement_sec = _coerce_int(payload.get("no_movement_sec", 0), 0)
    response_status = str(payload.get("response_status", "unknown") or "unknown")
    triggered = fall_detected
    if triggered:
        default_message = (
            f"检测到老人疑似跌倒（冲击 {impact_g:.1f}g，静止 {no_movement_sec}s），请立即确认是否受伤。"
        )
    else:
        default_message = "当前未检测到需要上报的跌倒事件。"
    decision = {
        "triggered": triggered,
        "supported": True,
        "signal_type": signal_type,
        "sender_id": sender_id,
        "timestamp": timestamp,
        "fall_detected": fall_detected,
        "impact_g": impact_g,
        "no_movement_sec": no_movement_sec,
        "response_status": response_status,
        "severity": severity or "critical",
        "message": payload.get("message") or default_message,
        "event_type": "fall_detected_alert",
        "details": {
            "fall_detected": fall_detected,
            "impact_g": impact_g,
            "no_movement_sec": no_movement_sec,
            "response_status": response_status,
        },
    }
    if not triggered:
        decision["reason"] = "threshold_not_met"
    return _attach_location(decision, payload)


def _evaluate_irregular_rhythm(payload):
    signal_type, sender_id, severity, timestamp = _base_context(payload)
    detected = _coerce_bool(payload.get("irregular_rhythm_detected", payload.get("value", False)), False)
    duration_sec = _coerce_int(payload.get("duration_sec", 0), 0)
    min_duration_sec = _coerce_int(payload.get("min_duration_sec", 45), 45)
    episode_count = _coerce_int(payload.get("episode_count", 1), 1)
    resting_heart_rate = _coerce_int(payload.get("resting_heart_rate", 0), 0)
    triggered = detected and duration_sec >= min_duration_sec
    if triggered:
        default_message = (
            f"检测到老人疑似心律不齐（持续 {duration_sec}s，检测到 {episode_count} 次异常节律片段），请尽快确认。"
        )
    else:
        default_message = f"当前未持续检测到异常节律，尚未达到持续 {min_duration_sec}s 的预警条件。"
    decision = {
        "triggered": triggered,
        "supported": True,
        "signal_type": signal_type,
        "sender_id": sender_id,
        "timestamp": timestamp,
        "irregular_rhythm_detected": detected,
        "duration_sec": duration_sec,
        "min_duration_sec": min_duration_sec,
        "episode_count": episode_count,
        "resting_heart_rate": resting_heart_rate,
        "severity": severity or "high",
        "message": payload.get("message") or default_message,
        "event_type": "arrhythmia_alert",
        "details": {
            "irregular_rhythm_detected": detected,
            "duration_sec": duration_sec,
            "episode_count": episode_count,
            "resting_heart_rate": resting_heart_rate,
            "rule": {
                "min_duration_sec": min_duration_sec,
            },
        },
    }
    if not triggered:
        decision["reason"] = "threshold_not_met"
    return _attach_location(decision, payload)


def _evaluate_body_temperature(payload):
    signal_type, sender_id, severity, timestamp = _base_context(payload)
    body_temperature = _coerce_float(
        payload.get("body_temperature", payload.get("temperature", payload.get("value", 0.0))),
        0.0,
    )
    duration_sec = _coerce_int(payload.get("duration_sec", 0), 0)
    high_threshold = _coerce_float(payload.get("high_threshold", 38.5), 38.5)
    low_threshold = _coerce_float(payload.get("low_threshold", 35.0), 35.0)
    min_duration_sec = _coerce_int(payload.get("min_duration_sec", 600), 600)

    classification = ""
    if body_temperature >= high_threshold:
        classification = "high_temperature"
    elif 0 < body_temperature <= low_threshold:
        classification = "low_temperature"

    triggered = bool(classification) and duration_sec >= min_duration_sec
    if classification == "low_temperature":
        if triggered:
            default_message = (
                f"检测到老人可能体温偏低（{body_temperature:.1f}℃，持续 {duration_sec}s），请尽快确认保暖与意识状态。"
            )
        else:
            default_message = (
                f"当前体温约 {body_temperature:.1f}℃，持续 {duration_sec}s，尚未达到低体温告警条件。"
            )
    else:
        if triggered:
            default_message = (
                f"检测到老人体温异常升高（{body_temperature:.1f}℃，持续 {duration_sec}s），请尽快确认。"
            )
        else:
            default_message = (
                f"当前体温约 {body_temperature:.1f}℃，持续 {duration_sec}s，尚未达到体温异常告警条件。"
            )

    decision = {
        "triggered": triggered,
        "supported": True,
        "signal_type": signal_type,
        "sender_id": sender_id,
        "timestamp": timestamp,
        "body_temperature": body_temperature,
        "duration_sec": duration_sec,
        "high_threshold": high_threshold,
        "low_threshold": low_threshold,
        "min_duration_sec": min_duration_sec,
        "severity": severity or ("critical" if classification == "low_temperature" else "high"),
        "message": payload.get("message") or default_message,
        "event_type": "temperature_alert",
        "details": {
            "body_temperature": body_temperature,
            "duration_sec": duration_sec,
            "classification": classification or "normal",
            "rule": {
                "high_threshold": high_threshold,
                "low_threshold": low_threshold,
                "min_duration_sec": min_duration_sec,
            },
        },
    }
    if not triggered:
        decision["reason"] = "threshold_not_met"
    return _attach_location(decision, payload)


def _evaluate_inactivity(payload):
    signal_type, sender_id, severity, timestamp = _base_context(payload)
    inactivity_minutes = _coerce_int(payload.get("inactivity_minutes", payload.get("minutes", 0)), 0)
    threshold_minutes = _coerce_int(payload.get("threshold_minutes", 120), 120)
    during_sleep = _coerce_bool(payload.get("during_sleep", False), False)
    last_motion_ago_minutes = _coerce_int(payload.get("last_motion_ago_minutes", inactivity_minutes), inactivity_minutes)
    triggered = inactivity_minutes >= threshold_minutes and not during_sleep
    if triggered:
        default_message = (
            f"检测到老人连续 {inactivity_minutes} 分钟无明显活动，且当前未标记为睡眠时段，请尽快确认。"
        )
    elif during_sleep:
        default_message = "当前处于睡眠或休息时段，未触发无活动告警。"
    else:
        default_message = f"当前连续无活动 {inactivity_minutes} 分钟，尚未达到 {threshold_minutes} 分钟的预警条件。"
    decision = {
        "triggered": triggered,
        "supported": True,
        "signal_type": signal_type,
        "sender_id": sender_id,
        "timestamp": timestamp,
        "inactivity_minutes": inactivity_minutes,
        "threshold_minutes": threshold_minutes,
        "during_sleep": during_sleep,
        "last_motion_ago_minutes": last_motion_ago_minutes,
        "severity": severity or ("critical" if inactivity_minutes >= threshold_minutes * 2 else "warning"),
        "message": payload.get("message") or default_message,
        "event_type": "inactivity_alert",
        "details": {
            "inactivity_minutes": inactivity_minutes,
            "during_sleep": during_sleep,
            "last_motion_ago_minutes": last_motion_ago_minutes,
            "rule": {
                "threshold_minutes": threshold_minutes,
            },
        },
    }
    if not triggered:
        decision["reason"] = "sleep_window" if during_sleep else "threshold_not_met"
    return _attach_location(decision, payload)


SIGNAL_EVALUATORS = {
    "heart_rate": _evaluate_heart_rate,
    "blood_oxygen": _evaluate_blood_oxygen,
    "fall_detected": _evaluate_fall_detected,
    "irregular_rhythm": _evaluate_irregular_rhythm,
    "body_temperature": _evaluate_body_temperature,
    "inactivity": _evaluate_inactivity,
}


def evaluate_signal_payload(payload):
    if not isinstance(payload, dict):
        raise ValueError("signal payload must be a dict")

    signal_type = str(payload.get("signal_type", "heart_rate") or "heart_rate")
    sender_id = str(payload.get("sender_id", "") or "")
    evaluator = SIGNAL_EVALUATORS.get(signal_type)
    if evaluator is None:
        return {
            "triggered": False,
            "supported": False,
            "signal_type": signal_type,
            "reason": "unsupported_signal_type",
            "sender_id": sender_id,
        }
    return evaluator(payload)


def send_external_alert(url, payload, token="", timeout=10):
    """Send one JSON alert to a remote OpenClaw listener."""
    if not isinstance(payload, dict):
        raise TypeError("payload must be a dict")
    if not url:
        raise ValueError("url is required")

    headers = {"Content-Type": "application/json"}
    if token:
        headers["X-OpenClaw-Token"] = token

    req = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers=headers,
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8")
        return {
            "status": "success",
            "http_status": resp.status,
            "response": json.loads(raw) if raw else {},
        }


def load_device_bindings(path=DEFAULT_BINDINGS_PATH):
    if not os.path.exists(path):
        raise FileNotFoundError(f"binding file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("binding file must contain a JSON object")
    data.setdefault("relationships", {})
    data.setdefault("nodes", {})
    return data


def save_device_bindings(data, path=DEFAULT_BINDINGS_PATH):
    if not isinstance(data, dict):
        raise ValueError("binding data must be a dict")
    data.setdefault("relationships", {})
    data.setdefault("nodes", {})
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path


def list_device_bindings(path=DEFAULT_BINDINGS_PATH):
    return load_device_bindings(path)


def upsert_node_binding(
    sender_id,
    target_id,
    endpoint,
    token="",
    sender_role="elder",
    target_role="caregiver",
    sender_name="",
    target_name="",
    recipient_open_id="",
    path=DEFAULT_BINDINGS_PATH,
):
    if not sender_id:
        raise ValueError("sender_id is required")
    if not target_id:
        raise ValueError("target_id is required")
    if not endpoint:
        raise ValueError("endpoint is required")

    data = load_device_bindings(path)

    sender_node = data["nodes"].setdefault(sender_id, {})
    sender_node["role"] = sender_role or sender_node.get("role", "elder")
    sender_node["display_name"] = sender_name or sender_node.get("display_name") or sender_id

    target_node = data["nodes"].setdefault(target_id, {})
    target_node["role"] = target_role or target_node.get("role", "caregiver")
    target_node["display_name"] = target_name or target_node.get("display_name") or target_id
    target_node["endpoint"] = endpoint
    target_node["token"] = token
    if recipient_open_id:
        target_node["recipient_open_id"] = recipient_open_id

    rel = data["relationships"].setdefault(sender_id, {})
    targets = rel.setdefault("notify_targets", [])
    if target_id not in targets:
        targets.append(target_id)

    save_device_bindings(data, path)
    return data


def delete_node_binding(sender_id, target_id, path=DEFAULT_BINDINGS_PATH):
    data = load_device_bindings(path)
    rel = data["relationships"].get(sender_id, {})
    targets = list(rel.get("notify_targets", []))
    if target_id in targets:
        targets.remove(target_id)
    if targets:
        rel["notify_targets"] = targets
        data["relationships"][sender_id] = rel
    elif sender_id in data["relationships"]:
        del data["relationships"][sender_id]

    still_referenced = any(
        target_id in (item.get("notify_targets", []) or [])
        for item in data["relationships"].values()
        if isinstance(item, dict)
    )
    if not still_referenced and target_id in data["nodes"]:
        del data["nodes"][target_id]

    save_device_bindings(data, path)
    return data


def resolve_notify_targets(sender_id, path=DEFAULT_BINDINGS_PATH):
    data = load_device_bindings(path)
    relationship = data["relationships"].get(sender_id, {})
    targets = relationship.get("notify_targets", [])
    if not isinstance(targets, list):
        raise ValueError("notify_targets must be a list")
    return data, targets


def build_alert_requests(
    sender_id,
    event_type,
    message,
    severity="warning",
    details=None,
    timestamp="",
    target_ids=None,
    binding_file=DEFAULT_BINDINGS_PATH,
):
    data, default_targets = resolve_notify_targets(sender_id, binding_file)
    targets = target_ids if target_ids is not None else default_targets
    if not targets:
        raise ValueError(f"no notify targets configured for sender_id={sender_id}")

    requests = []
    for target_id in targets:
        node = data["nodes"].get(target_id)
        if not isinstance(node, dict):
            raise ValueError(f"node config missing for target_id={target_id}")
        endpoint = (node.get("endpoint") or "").strip()
        if not endpoint:
            raise ValueError(f"endpoint missing for target_id={target_id}")
        payload = {
            "event_type": event_type,
            "sender_id": sender_id,
            "target_id": target_id,
            "message": message,
            "severity": severity or "warning",
            "timestamp": timestamp or time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        if details:
            payload["details"] = details
        if node.get("recipient_open_id"):
            payload["recipient_open_id"] = node["recipient_open_id"]
        requests.append(
            {
                "target_id": target_id,
                "endpoint": endpoint,
                "token": node.get("token", ""),
                "payload": payload,
            }
        )
    return requests


def send_bound_alert(
    sender_id,
    event_type,
    message,
    severity="warning",
    details=None,
    timestamp="",
    target_ids=None,
    binding_file=DEFAULT_BINDINGS_PATH,
    timeout=10,
):
    requests = build_alert_requests(
        sender_id=sender_id,
        event_type=event_type,
        message=message,
        severity=severity,
        details=details or {},
        timestamp=timestamp,
        target_ids=target_ids,
        binding_file=binding_file,
    )

    results = []
    for item in requests:
        result = send_external_alert(
            item["endpoint"],
            item["payload"],
            token=item.get("token", ""),
            timeout=timeout,
        )
        results.append(
            {
                "target_id": item["target_id"],
                "endpoint": item["endpoint"],
                "result": result,
            }
        )
    return results


class CrossDeviceServer:
    """Expose binding, signal, and alert endpoints for one OpenClaw node."""

    def __init__(
        self,
        host="127.0.0.1",
        port=8787,
        node_id="",
        binding_file="memory/device_bindings.json",
        auth_token="",
        on_alert=None,
        log_func=None,
        max_body_bytes=64 * 1024,
    ):
        self.host = host
        self.port = int(port)
        self.node_id = node_id or ""
        self.binding_file = binding_file
        self.auth_token = auth_token or ""
        self.on_alert = on_alert
        self.log = log_func or print
        self.max_body_bytes = int(max_body_bytes)
        self.httpd = None
        self.thread = None
        self.received_count = 0
        self.last_alert = None
        self.last_signal = None

    def start(self):
        if self.httpd is not None:
            return self
        self.httpd = ThreadingHTTPServer((self.host, self.port), self._build_handler())
        self.port = int(self.httpd.server_address[1])
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        self.log(
            f"[CrossDevice] Listening on http://{self.host}:{self.port}"
            f" node_id={self.node_id or '(unset)'}"
        )
        return self

    def stop(self):
        if self.httpd is None:
            return
        self.httpd.shutdown()
        self.httpd.server_close()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2)
        self.httpd = None
        self.thread = None

    def _build_handler(self):
        outer = self

        class Handler(BaseHTTPRequestHandler):
            server_version = "OpenClawCrossDevice/0.1"

            def log_message(self, fmt, *args):
                outer.log("[CrossDevice] " + fmt % args)

            def _send_json(self, status, payload):
                body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def _require_token(self):
                if not outer.auth_token:
                    return True
                token = self.headers.get("X-OpenClaw-Token", "")
                if hmac.compare_digest(token, outer.auth_token):
                    return True
                self._send_json(403, {"status": "error", "msg": "forbidden"})
                return False

            def _read_json_body(self):
                try:
                    content_length = int(self.headers.get("Content-Length", "0"))
                except ValueError:
                    self._send_json(400, {"status": "error", "msg": "invalid_content_length"})
                    return None
                if content_length <= 0:
                    self._send_json(400, {"status": "error", "msg": "empty_body"})
                    return None
                if content_length > outer.max_body_bytes:
                    self._send_json(413, {"status": "error", "msg": "payload_too_large"})
                    return None
                raw = self.rfile.read(content_length)
                try:
                    payload = json.loads(raw.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    self._send_json(400, {"status": "error", "msg": "invalid_json"})
                    return None
                if not isinstance(payload, dict):
                    self._send_json(400, {"status": "error", "msg": "json_object_required"})
                    return None
                return payload

            def do_GET(self):
                if self.path == "/healthz":
                    self._send_json(
                        200,
                        {
                            "status": "ok",
                            "node_id": outer.node_id,
                            "binding_file": outer.binding_file,
                            "received_count": outer.received_count,
                        },
                    )
                    return
                if self.path == "/bindings":
                    self._send_json(
                        200,
                        {
                            "status": "ok",
                            "node_id": outer.node_id,
                            "bindings": list_device_bindings(outer.binding_file),
                        },
                    )
                    return
                self._send_json(404, {"status": "error", "msg": "not_found"})

            def do_POST(self):
                if self.path == "/external_alert":
                    if not self._require_token():
                        return
                    payload = self._read_json_body()
                    if payload is None:
                        return
                    if not payload.get("event_type"):
                        self._send_json(400, {"status": "error", "msg": "event_type_required"})
                        return
                    if not payload.get("message"):
                        self._send_json(400, {"status": "error", "msg": "message_required"})
                        return
                    outer.received_count += 1
                    outer.last_alert = payload
                    try:
                        result = outer.on_alert(payload) if outer.on_alert else {"status": "accepted"}
                    except Exception as e:
                        outer.log(f"[CrossDevice] alert callback failed: {e}")
                        self._send_json(500, {"status": "error", "msg": str(e)})
                        return
                    self._send_json(
                        200,
                        {
                            "status": "ok",
                            "received_count": outer.received_count,
                            "result": result,
                        },
                    )
                    return

                if self.path == "/bindings/upsert":
                    payload = self._read_json_body()
                    if payload is None:
                        return
                    try:
                        data = upsert_node_binding(
                            sender_id=payload.get("sender_id", ""),
                            target_id=payload.get("target_id", ""),
                            endpoint=payload.get("endpoint", ""),
                            token=payload.get("token", ""),
                            sender_role=payload.get("sender_role", "elder"),
                            target_role=payload.get("target_role", "caregiver"),
                            sender_name=payload.get("sender_name", ""),
                            target_name=payload.get("target_name", ""),
                            recipient_open_id=payload.get("recipient_open_id", ""),
                            path=payload.get("binding_file", outer.binding_file),
                        )
                    except Exception as e:
                        self._send_json(400, {"status": "error", "msg": str(e)})
                        return
                    self._send_json(200, {"status": "ok", "bindings": data})
                    return

                if self.path == "/bindings/delete":
                    payload = self._read_json_body()
                    if payload is None:
                        return
                    try:
                        data = delete_node_binding(
                            sender_id=payload.get("sender_id", ""),
                            target_id=payload.get("target_id", ""),
                            path=payload.get("binding_file", outer.binding_file),
                        )
                    except Exception as e:
                        self._send_json(400, {"status": "error", "msg": str(e)})
                        return
                    self._send_json(200, {"status": "ok", "bindings": data})
                    return

                if self.path == "/signal_input":
                    payload = self._read_json_body()
                    if payload is None:
                        return
                    payload.setdefault("sender_id", outer.node_id)
                    decision = evaluate_signal_payload(payload)
                    outer.last_signal = {"payload": payload, "decision": decision}
                    if not decision.get("supported", True):
                        self._send_json(400, {"status": "error", "decision": decision})
                        return
                    if not decision.get("triggered"):
                        self._send_json(200, {"status": "no_alert", "decision": decision})
                        return
                    try:
                        result = send_bound_alert(
                            sender_id=decision.get("sender_id") or outer.node_id,
                            event_type=decision["event_type"],
                            message=decision["message"],
                            severity=decision["severity"],
                            details=decision.get("details", {}),
                            timestamp=decision.get("timestamp", ""),
                            binding_file=outer.binding_file,
                            timeout=10,
                        )
                    except Exception as e:
                        self._send_json(
                            500,
                            {"status": "error", "msg": str(e), "decision": decision},
                        )
                        return
                    self._send_json(
                        200,
                        {
                            "status": "alert_sent",
                            "decision": decision,
                            "results": result,
                        },
                    )
                    return

                self._send_json(404, {"status": "error", "msg": "not_found"})

        return Handler


def main():
    parser = argparse.ArgumentParser(description="Run a cross-device OpenClaw node service.")
    parser.add_argument("--node-id", required=True, help="Logical node id, e.g. elder_01")
    parser.add_argument("--host", default="0.0.0.0", help="Listen host")
    parser.add_argument("--port", type=int, default=8790, help="Listen port")
    parser.add_argument("--binding-file", default="memory/device_bindings.json", help="Binding config path")
    parser.add_argument("--token", default="", help="Optional token for /external_alert")
    args = parser.parse_args()

    server = CrossDeviceServer(
        host=args.host,
        port=args.port,
        node_id=args.node_id,
        binding_file=args.binding_file,
        auth_token=args.token,
        log_func=print,
    ).start()

    print(f"[CrossDeviceNode] node_id={args.node_id} binding_file={args.binding_file}")
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        print("[CrossDeviceNode] shutting down...")
        server.stop()


if __name__ == "__main__":
    main()
