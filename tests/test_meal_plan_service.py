#!/usr/bin/env python3
"""Tests for meal planning and scheduled push service."""
import os
import sys
import tempfile
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from meal_plan_service import MealPlanService
from tools.health_data_store import HealthDataStore


def _build_service():
    temp_dir = tempfile.TemporaryDirectory()
    store = HealthDataStore(base_dir=temp_dir.name)
    return temp_dir, MealPlanService(store=store), store


def test_create_plan_from_weight_loss_request():
    temp_dir, service, _store = _build_service()
    try:
        result = service.create_plan("ou_test", "我想减肥，给我未来一个月的用餐计划，中午12点吃饭。")
        plan = result["plan"]
        assert plan["goal"] == "weight_loss"
        assert plan["duration_days"] == 30
        assert len(plan["days"]) == 30
        assert plan["meal_schedule"]["lunch"]["meal_time"] == "12:00"
        assert plan["meal_schedule"]["lunch"]["push_time"] == "11:00"
    finally:
        temp_dir.cleanup()


def test_create_plan_uses_indicator_constraints():
    temp_dir, service, store = _build_service()
    try:
        store.append_checkup(
            "2026-03-17",
            {
                "fasting_blood_glucose": {"value": 6.4, "unit": "mmol/L"},
                "systolic_bp": {"value": 145, "unit": "mmHg"},
            },
        )
        plan = service.create_plan("ou_test", "给我一个月饮食计划")["plan"]
        notes = "\n".join(plan["constraints"]["notes"])
        assert "低糖" in notes
        assert "低盐" in notes
    finally:
        temp_dir.cleanup()


def test_collect_due_pushes():
    temp_dir, service, store = _build_service()
    try:
        plan = service.create_plan("ou_test", "我想减肥，给我未来一个月的饮食计划")["plan"]
        today = datetime.now().strftime("%Y-%m-%d")
        plan["start_date"] = today
        plan["days"][0]["date"] = today
        for meal_key in ["breakfast", "lunch", "dinner"]:
            plan["meal_schedule"][meal_key]["push_time"] = datetime.now().strftime("%H:%M")
        store.upsert_meal_plan(plan)

        pushes = service.collect_due_pushes(now=datetime.now())
        assert pushes
        assert pushes[0]["open_id"] == "ou_test"
        assert pushes[0]["candidates"]

        sent = service.mark_push_sent(plan["id"], today, pushes[0]["meal_key"], "msg_x")
        assert sent["status"] == "success"
    finally:
        temp_dir.cleanup()


if __name__ == "__main__":
    test_create_plan_from_weight_loss_request()
    test_create_plan_uses_indicator_constraints()
    test_collect_due_pushes()
    print("meal plan service test passed")
