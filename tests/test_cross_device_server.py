#!/usr/bin/env python3
"""End-to-end tests for the unified cross-device server."""
import os
import sys
import tempfile
import json
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cross_device_node import CrossDeviceServer


def http_get_json(url, timeout=10):
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8")
        return {
            "status": "success",
            "http_status": resp.status,
            "response": json.loads(raw) if raw else {},
        }


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


def test_bind_then_signal_alert():
    received = []

    def on_alert(payload):
        received.append(payload)
        return {"status": "delivered"}

    receiver = CrossDeviceServer(
        host="127.0.0.1",
        port=0,
        node_id="child_01",
        auth_token="token-x",
        on_alert=on_alert,
        log_func=lambda *_: None,
    ).start()

    with tempfile.TemporaryDirectory() as td:
        binding_file = os.path.join(td, "bindings.json")
        with open(binding_file, "w", encoding="utf-8") as f:
            f.write('{"relationships": {}, "nodes": {}}')

        elder = CrossDeviceServer(
            host="127.0.0.1",
            port=0,
            node_id="elder_01",
            binding_file=binding_file,
            log_func=lambda *_: None,
        ).start()

        try:
            base = f"http://127.0.0.1:{elder.port}"

            health = http_get_json(base + "/healthz")
            assert health["response"]["status"] == "ok"
            assert health["response"]["node_id"] == "elder_01"

            upsert = http_post_json(
                base + "/bindings/upsert",
                {
                    "sender_id": "elder_01",
                    "target_id": "child_01",
                    "endpoint": f"http://127.0.0.1:{receiver.port}/external_alert",
                    "token": "token-x",
                },
            )
            assert upsert["response"]["status"] == "ok"

            signal = http_post_json(
                base + "/signal_input",
                {
                    "signal_type": "heart_rate",
                    "sender_id": "elder_01",
                    "heart_rate": 145,
                    "duration_sec": 120,
                },
            )
            assert signal["response"]["status"] == "alert_sent"
            assert received and received[0]["event_type"] == "heart_rate_alert"
        finally:
            elder.stop()
            receiver.stop()


def test_bind_then_low_oxygen_alert():
    received = []

    def on_alert(payload):
        received.append(payload)
        return {"status": "delivered"}

    receiver = CrossDeviceServer(
        host="127.0.0.1",
        port=0,
        node_id="child_01",
        auth_token="token-y",
        on_alert=on_alert,
        log_func=lambda *_: None,
    ).start()

    with tempfile.TemporaryDirectory() as td:
        binding_file = os.path.join(td, "bindings.json")
        with open(binding_file, "w", encoding="utf-8") as f:
            f.write('{"relationships": {}, "nodes": {}}')

        elder = CrossDeviceServer(
            host="127.0.0.1",
            port=0,
            node_id="elder_01",
            binding_file=binding_file,
            log_func=lambda *_: None,
        ).start()

        try:
            base = f"http://127.0.0.1:{elder.port}"
            upsert = http_post_json(
                base + "/bindings/upsert",
                {
                    "sender_id": "elder_01",
                    "target_id": "child_01",
                    "endpoint": f"http://127.0.0.1:{receiver.port}/external_alert",
                    "token": "token-y",
                },
            )
            assert upsert["response"]["status"] == "ok"

            signal = http_post_json(
                base + "/signal_input",
                {
                    "signal_type": "blood_oxygen",
                    "sender_id": "elder_01",
                    "spo2": 88,
                    "duration_sec": 180,
                },
            )
            assert signal["response"]["status"] == "alert_sent"
            assert received and received[0]["event_type"] == "blood_oxygen_alert"
        finally:
            elder.stop()
            receiver.stop()


if __name__ == "__main__":
    test_bind_then_signal_alert()
    test_bind_then_low_oxygen_alert()
    print("cross device server test passed")
