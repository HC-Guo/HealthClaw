#!/usr/bin/env python3
"""Tests for Meituan phone-search suggestion parsing."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from meal_plan_service import _extract_suggestions


def test_extract_suggestions_filters_noise():
    nodes = [
        {"text": "问小团", "cy": 240},
        {"text": "轻食鸡胸肉", "cy": 420, "cx": 500},
        {"text": "沙野轻食鸡胸肉烤时蔬碗点击 发起搜索", "cy": 520, "cx": 500},
        {"text": "全部", "cy": 240},
        {"text": "减脂鸡胸肉", "cy": 620, "cx": 500},
        {"text": "地图搜索 按钮", "cy": 150},
    ]
    results = _extract_suggestions(nodes, "轻食鸡胸肉", limit=3)
    assert len(results) == 3
    assert results[0]["item_name"] == "轻食鸡胸肉"
    assert "沙野轻食鸡胸肉烤时蔬碗" in results[1]["item_name"]
    assert results[2]["item_name"] == "减脂鸡胸肉"


if __name__ == "__main__":
    test_extract_suggestions_filters_noise()
    print("meituan phone provider test passed")
