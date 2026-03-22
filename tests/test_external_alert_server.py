#!/usr/bin/env python3
"""Basic tests for the /external_alert listener exposed by CrossDeviceServer."""
import json
import os
import sys
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cross_device_node import CrossDeviceServer, send_external_alert


def _post_json(url, payload, token=""):
    data = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["X-OpenClaw-Token"] = token
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=5) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))


def test_external_alert_server():
    events = []

    def on_alert(payload):
        events.append(payload)
        return {"status": "delivered", "target_id": payload.get("target_id")}

    server = CrossDeviceServer(
        host="127.0.0.1",
        port=0,
        node_id="child_01",
        auth_token="secret-token",
        on_alert=on_alert,
        log_func=lambda *_: None,
    ).start()

    try:
        health_url = f"http://127.0.0.1:{server.port}/healthz"
        with urllib.request.urlopen(health_url, timeout=5) as resp:
            health = json.loads(resp.read().decode("utf-8"))
        assert resp.status == 200
        assert health["status"] == "ok"

        alert_url = f"http://127.0.0.1:{server.port}/external_alert"
        status, body = _post_json(
            alert_url,
            {
                "event_type": "heart_rate_alert",
                "sender_id": "elder_01",
                "target_id": "child_01",
                "message": "heart rate spiked",
            },
            token="secret-token",
        )
        assert status == 200
        assert body["status"] == "ok"
        assert body["result"]["status"] == "delivered"
        assert events and events[0]["event_type"] == "heart_rate_alert"

        try:
            _post_json(
                alert_url,
                {
                    "event_type": "heart_rate_alert",
                    "message": "forbidden test",
                },
                token="wrong-token",
            )
        except urllib.error.HTTPError as e:
            assert e.code == 403
        else:
            raise AssertionError("expected forbidden response")
    finally:
        server.stop()


def test_external_alert_end_to_end():
    events = []

    def on_alert(payload):
        events.append(payload)
        return {"status": "delivered"}

    server = CrossDeviceServer(
        host="127.0.0.1",
        port=0,
        node_id="child_01",
        auth_token="secret-token",
        on_alert=on_alert,
        log_func=lambda *_: None,
    ).start()

    try:
        result = send_external_alert(
            f"http://127.0.0.1:{server.port}/external_alert",
            {
                "event_type": "fall_alert",
                "sender_id": "elder_01",
                "target_id": "child_01",
                "message": "fall detected",
            },
            token="secret-token",
            timeout=5,
        )
        assert result["status"] == "success"
        assert result["response"]["status"] == "ok"
        assert events and events[0]["event_type"] == "fall_alert"
    finally:
        server.stop()


if __name__ == "__main__":
    test_external_alert_server()
    test_external_alert_end_to_end()
    print("external alert server test passed")
