#!/usr/bin/env python3
"""Tests for wearable signal evaluation rules."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cross_device_node import build_demo_signal_payload, evaluate_signal_payload


def test_heart_rate_alert():
    decision = evaluate_signal_payload(build_demo_signal_payload("heart_rate_spike"))
    assert decision["triggered"] is True
    assert decision["event_type"] == "heart_rate_alert"
    assert decision["details"]["location"]["location_text"] == "复旦大学邯郸校区 6 号楼 203 室"


def test_blood_oxygen_alert():
    decision = evaluate_signal_payload(build_demo_signal_payload("low_oxygen"))
    assert decision["triggered"] is True
    assert decision["event_type"] == "blood_oxygen_alert"
    assert decision["details"]["spo2"] == 88


def test_fall_detected_alert():
    decision = evaluate_signal_payload(build_demo_signal_payload("fall_detected"))
    assert decision["triggered"] is True
    assert decision["event_type"] == "fall_detected_alert"


def test_irregular_rhythm_alert():
    decision = evaluate_signal_payload(build_demo_signal_payload("irregular_rhythm"))
    assert decision["triggered"] is True
    assert decision["event_type"] == "arrhythmia_alert"


def test_temperature_alert():
    decision = evaluate_signal_payload(build_demo_signal_payload("high_temperature"))
    assert decision["triggered"] is True
    assert decision["event_type"] == "temperature_alert"


def test_inactivity_alert():
    decision = evaluate_signal_payload(build_demo_signal_payload("prolonged_inactivity"))
    assert decision["triggered"] is True
    assert decision["event_type"] == "inactivity_alert"


def test_safe_sample_does_not_trigger():
    decision = evaluate_signal_payload(build_demo_signal_payload("low_oxygen", safe=True))
    assert decision["triggered"] is False
    assert decision["reason"] == "threshold_not_met"


def test_manual_location_passthrough():
    decision = evaluate_signal_payload(
        {
            "signal_type": "heart_rate",
            "sender_id": "elder_01",
            "heart_rate": 150,
            "duration_sec": 120,
            "location": {
                "location_text": "复旦大学邯郸校区 9 号楼 909 室",
                "source": "wearable_device",
            },
        }
    )
    assert decision["location"]["location_text"] == "复旦大学邯郸校区 9 号楼 909 室"
    assert decision["details"]["location"]["source"] == "wearable_device"


if __name__ == "__main__":
    test_heart_rate_alert()
    test_blood_oxygen_alert()
    test_fall_detected_alert()
    test_irregular_rhythm_alert()
    test_temperature_alert()
    test_inactivity_alert()
    test_safe_sample_does_not_trigger()
    test_manual_location_passthrough()
    print("signal rules test passed")
