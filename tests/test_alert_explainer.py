#!/usr/bin/env python3
"""Tests for caregiver-facing alert explanations."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fsapp import explain_alert_for_caregiver


def _sample_alert():
    return {
        "event_type": "heart_rate_alert",
        "sender_id": "elder_01",
        "severity": "critical",
        "message": "检测到老人心率异常升高（145 bpm，持续 120s），请尽快查看。",
        "details": {
            "heart_rate": 145,
            "duration_sec": 120,
            "location": {
                "location_text": "复旦大学邯郸校区 6 号楼 203 室",
                "source": "demo_simulated_wearable_location",
            },
            "rule": {
                "threshold": 130,
                "min_duration_sec": 60,
            },
        },
    }


def test_alert_explainer_uses_llm_output_when_available():
    def fake_llm(prompt):
        assert '"event_type": "heart_rate_alert"' in prompt
        assert "复旦大学邯郸校区 6 号楼 203 室" in prompt
        return "\n".join(
            [
                "**这代表什么**",
                "- 这是模拟的 LLM 解读。",
                "",
                "**可能原因**",
                "- 这是模拟内容。",
                "",
                "**建议马上做什么**",
                "- 先联系老人。",
                "",
                "**何时立刻急救**",
                "- 出现严重症状时立即急救。",
            ]
        )

    result = explain_alert_for_caregiver(_sample_alert(), llm_ask=fake_llm)
    assert result["source"] == "llm"
    assert "模拟的 LLM 解读" in result["markdown"]


def test_alert_explainer_falls_back_when_llm_fails():
    def bad_llm(_prompt):
        raise RuntimeError("network error")

    result = explain_alert_for_caregiver(_sample_alert(), llm_ask=bad_llm)
    assert result["source"] == "fallback"
    assert "145 bpm" in result["markdown"]
    assert "**建议马上做什么**" in result["markdown"]


def test_alert_explainer_falls_back_on_empty_response():
    result = explain_alert_for_caregiver(_sample_alert(), llm_ask=lambda _prompt: "")
    assert result["source"] == "fallback"
    assert "不足以直接判断具体病因" in result["markdown"]


def test_alert_explainer_fall_fallback():
    alert = {
        "event_type": "fall_detected_alert",
        "sender_id": "elder_01",
        "severity": "critical",
        "message": "检测到老人疑似跌倒，请立即确认。",
        "details": {
            "impact_g": 3.4,
            "no_movement_sec": 45,
            "response_status": "no_response",
        },
    }
    result = explain_alert_for_caregiver(alert, llm_ask=lambda _prompt: "")
    assert result["source"] == "fallback"
    assert "跌倒" in result["markdown"]
    assert "不要急着强行扶起" in result["markdown"]


if __name__ == "__main__":
    test_alert_explainer_uses_llm_output_when_available()
    test_alert_explainer_falls_back_when_llm_fails()
    test_alert_explainer_falls_back_on_empty_response()
    test_alert_explainer_fall_fallback()
    print("alert explainer test passed")
