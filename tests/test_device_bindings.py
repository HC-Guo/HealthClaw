#!/usr/bin/env python3
"""Tests for logical binding resolution and managed binding updates."""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cross_device_node import build_alert_requests, delete_node_binding, load_device_bindings, upsert_node_binding


def test_build_alert_requests():
    reqs = build_alert_requests(
        sender_id="elder_01",
        event_type="heart_rate_alert",
        message="alert message",
        severity="critical",
        details={"heart_rate": 142},
        binding_file="memory/device_bindings.json",
    )
    assert len(reqs) == 1
    assert reqs[0]["target_id"] == "child_01"
    assert reqs[0]["endpoint"].endswith("/external_alert")
    assert reqs[0]["payload"]["event_type"] == "heart_rate_alert"


def test_upsert_and_delete_binding():
    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, "bindings.json")
        with open(path, "w", encoding="utf-8") as f:
            f.write('{"relationships": {}, "nodes": {}}')

        upsert_node_binding(
            sender_id="elder_x",
            target_id="child_x",
            endpoint="http://127.0.0.1:9999/external_alert",
            token="abc",
            path=path,
        )
        data = load_device_bindings(path)
        assert data["relationships"]["elder_x"]["notify_targets"] == ["child_x"]
        assert data["nodes"]["child_x"]["endpoint"].endswith("/external_alert")

        delete_node_binding("elder_x", "child_x", path=path)
        data = load_device_bindings(path)
        assert "elder_x" not in data["relationships"]
        assert "child_x" not in data["nodes"]


if __name__ == "__main__":
    test_build_alert_requests()
    test_upsert_and_delete_binding()
    print("device binding test passed")
