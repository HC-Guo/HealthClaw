#!/usr/bin/env python3
"""
Simulate elder-side wearable signals and trigger a bound external alert.
"""
import argparse
import json
import sys
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from cross_device_node import (
    build_demo_signal_payload,
    evaluate_signal_payload,
    get_demo_signal_scenarios,
    send_bound_alert,
)


def http_post_json(url, payload, token="", timeout=10):
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


def _build_manual_payload(args):
    payload = {
        "signal_type": "heart_rate",
        "sender_id": args.sender_id,
        "heart_rate": args.heart_rate,
        "duration_sec": args.duration_sec,
        "threshold": args.threshold,
        "min_duration_sec": args.min_duration_sec,
    }
    if args.location_text:
        payload["location"] = {
            "location_text": args.location_text,
            "source": "demo_cli_override",
        }
    if args.message:
        payload["message"] = args.message
    return payload


def _build_payload(args):
    if args.scenario:
        payload = build_demo_signal_payload(args.scenario, sender_id=args.sender_id, safe=args.safe_sample)
        if args.location_text:
            location = dict(payload.get("location") or {})
            location["location_text"] = args.location_text
            location["source"] = "demo_cli_override"
            payload["location"] = location
        if args.message:
            payload["message"] = args.message
        return payload
    return _build_manual_payload(args)


def main():
    parser = argparse.ArgumentParser(description="Simulate elder-side wearable alerts.")
    parser.add_argument("--sender-id", default="elder_01", help="Logical elder node id")
    parser.add_argument("--binding-file", default="memory/device_bindings.json", help="Binding config path")
    parser.add_argument("--server-url", default="", help="Optional running elder node base URL, e.g. http://10.0.0.9:8790")
    parser.add_argument("--scenario", default="", help="Demo scenario key, e.g. low_oxygen")
    parser.add_argument("--safe-sample", action="store_true", help="Use the selected scenario's normal sample instead of the alert sample")
    parser.add_argument("--list-scenarios", action="store_true", help="List built-in demo scenarios and exit")
    parser.add_argument("--heart-rate", type=int, default=145, help="Manual heart-rate simulation value")
    parser.add_argument("--duration-sec", type=int, default=90, help="Duration of the manual signal")
    parser.add_argument("--threshold", type=int, default=130, help="Manual heart-rate alert threshold")
    parser.add_argument("--min-duration-sec", type=int, default=60, help="Manual minimum duration to trigger")
    parser.add_argument("--location-text", default="", help="Optional wearable-reported location text")
    parser.add_argument("--message", default="", help="Optional custom alert message")
    args = parser.parse_args()

    if args.list_scenarios:
        print(json.dumps(get_demo_signal_scenarios(), ensure_ascii=False, indent=2))
        return

    payload = _build_payload(args)

    if args.server_url:
        result = http_post_json(args.server_url.rstrip("/") + "/signal_input", payload)
        print(json.dumps(result["response"], ensure_ascii=False, indent=2))
        return

    decision = evaluate_signal_payload(payload)

    if not decision["triggered"]:
        print(
            json.dumps(
                {
                    "status": "no_alert",
                    "reason": decision.get("reason", "threshold_not_met"),
                    "decision": decision,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    results = send_bound_alert(
        sender_id=decision["sender_id"],
        event_type=decision["event_type"],
        message=decision["message"],
        severity=decision["severity"],
        details=decision["details"],
        binding_file=args.binding_file,
        timeout=10,
    )
    print(
        json.dumps(
            {
                "status": "alert_sent",
                "payload": payload,
                "decision": decision,
                "results": results,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
