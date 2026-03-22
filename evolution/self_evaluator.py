"""
自我评估器 - 用 ground truth 验证系统诊断准确性，检测策略漂移
"""
import os, json
from collections import defaultdict


class SelfEvaluator:
    """系统自我评估，检测准确性趋势和策略偏差"""

    def __init__(self):
        from config import MEMORY_CONFIG
        self.episodes_file = MEMORY_CONFIG.get("l4_episodes_file",
                                                "memory/L4_episodes/case_episodes.jsonl")
        self.strategy_file = MEMORY_CONFIG.get("l4_strategy_file",
                                                "memory/L4_episodes/disease_strategy.json")

    def generate_report(self) -> dict:
        """生成自我评估报告"""
        episodes = self._read_episodes()
        if not episodes:
            return {"status": "no_data"}

        verified = [e for e in episodes if e.get("outcome_correct") is not None]

        report = {
            "total_episodes": len(episodes),
            "verified_episodes": len(verified),
            "overall_accuracy": None,
            "by_disease": {},
            "tool_efficiency": {},
            "strategy_drift_warnings": [],
        }

        if verified:
            correct = sum(1 for e in verified if e["outcome_correct"])
            report["overall_accuracy"] = round(correct / len(verified), 3)

        disease_stats = defaultdict(lambda: {"correct": 0, "incorrect": 0, "total": 0})
        tool_stats = defaultdict(lambda: {"total_calls": 0, "useful_calls": 0})

        for ep in verified:
            d = ep.get("disease", "unknown")
            disease_stats[d]["total"] += 1
            if ep["outcome_correct"]:
                disease_stats[d]["correct"] += 1
            else:
                disease_stats[d]["incorrect"] += 1

            for tool, useful in ep.get("tools_useful", {}).items():
                tool_stats[tool]["total_calls"] += 1
                if useful:
                    tool_stats[tool]["useful_calls"] += 1

        for d, s in disease_stats.items():
            acc = s["correct"] / s["total"] if s["total"] > 0 else 0
            report["by_disease"][d] = {
                "accuracy": round(acc, 3),
                "total": s["total"],
                "correct": s["correct"],
            }
            if s["total"] >= 10 and acc < 0.6:
                report["strategy_drift_warnings"].append(
                    f"[WARNING] {d}: 准确率仅 {acc:.0%} ({s['total']}例)，需要检查策略"
                )

        for tool, s in tool_stats.items():
            rate = s["useful_calls"] / s["total_calls"] if s["total_calls"] > 0 else 0
            report["tool_efficiency"][tool] = {
                "usefulness_rate": round(rate, 3),
                "total_calls": s["total_calls"],
            }

        return report

    def _read_episodes(self) -> list:
        if not os.path.exists(self.episodes_file):
            return []
        episodes = []
        with open(self.episodes_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        episodes.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return episodes
