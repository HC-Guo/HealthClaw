"""
策略蒸馏器 - 从情景记忆中蒸馏出工具使用策略
Level 1 (原始经验) → Level 2 (策略统计) → Level 3 (规则提炼到L1)
"""
import os, json, time
from collections import defaultdict
from evolution.memory_policy import is_distillable_episode, normalize_episode


class StrategyDistiller:
    """从 L4 情景记忆蒸馏出工具使用策略"""

    def __init__(self):
        from config import MEMORY_CONFIG
        self.episodes_file = MEMORY_CONFIG.get("l4_episodes_file",
                                                "memory/L4_episodes/case_episodes.jsonl")
        self.strategy_file = MEMORY_CONFIG.get("l4_strategy_file",
                                                "memory/L4_episodes/disease_strategy.json")
        self.distill_log = MEMORY_CONFIG.get("distill_log_file",
                                              "memory/L4_episodes/distill_log.txt")

    def distill(self) -> dict:
        """执行蒸馏：从情景记忆统计各疾病的工具使用策略"""
        episodes = self._read_episodes()
        if not episodes:
            return {}

        stats = defaultdict(lambda: {
            "total_cases": 0,
            "tool_usage": defaultdict(lambda: {"called": 0, "useful": 0}),
            "confidence_lifts": [],
            "tool_sequences": defaultdict(int),
            "verified_correct": 0,
            "verified_incorrect": 0,
            "unverified": 0,
        })

        skipped = {
            "low_quality_or_unverified": 0,
            "artifact_or_unsafe": 0,
        }

        for raw_ep in episodes:
            ep = normalize_episode(raw_ep)
            if not is_distillable_episode(ep):
                if ep.get("artifact_risk") == "high" or ep.get("retrieval_policy") == "do_not_retrieve":
                    skipped["artifact_or_unsafe"] += 1
                else:
                    skipped["low_quality_or_unverified"] += 1
                continue

            disease = ep.get("disease", "unknown")
            s = stats[disease]
            s["total_cases"] += 1

            for tool, useful in ep.get("tools_useful", {}).items():
                s["tool_usage"][tool]["called"] += 1
                if useful and ep.get("outcome_correct") is True:
                    s["tool_usage"][tool]["useful"] += 1

            cc = ep.get("confidence_change", {})
            lift = cc.get("after_tools", 0) - cc.get("before_tools", 0)
            s["confidence_lifts"].append(lift)

            seq = "→".join(ep.get("tools_used", []))
            if seq:
                s["tool_sequences"][seq] += 1

            outcome = ep.get("outcome_correct")
            if outcome is True:
                s["verified_correct"] += 1
            elif outcome is False:
                s["verified_incorrect"] += 1
            else:
                s["unverified"] += 1

        strategy = {}
        for disease, s in stats.items():
            tool_utility = {}
            for tool, counts in s["tool_usage"].items():
                if counts["called"] > 0:
                    rate = counts["useful"] / counts["called"]
                    if rate > 0.7:
                        rec = "always"
                    elif rate > 0.3:
                        rec = "conditional"
                    else:
                        rec = "rarely"
                    tool_utility[tool] = {
                        "call_rate": round(counts["called"] / s["total_cases"], 2),
                        "usefulness_rate": round(rate, 2),
                        "recommendation": rec,
                        "called_count": counts["called"],
                        "useful_count": counts["useful"],
                    }

            lifts = s["confidence_lifts"]
            avg_lift = sum(lifts) / len(lifts) if lifts else 0

            best_seq = ""
            if s["tool_sequences"]:
                best_seq = max(s["tool_sequences"], key=s["tool_sequences"].get)

            strategy[disease] = {
                "total_cases": s["total_cases"],
                "tool_utility": tool_utility,
                "avg_confidence_lift": round(avg_lift, 3),
                "recommended_tool_sequence": best_seq,
                "accuracy": {
                    "verified_correct": s["verified_correct"],
                    "verified_incorrect": s["verified_incorrect"],
                    "unverified": s["unverified"],
                },
                "last_distill": time.strftime('%Y-%m-%d %H:%M'),
            }

        if skipped["low_quality_or_unverified"] or skipped["artifact_or_unsafe"]:
            strategy["_distill_filter_summary"] = {
                "skipped_low_quality_or_unverified": skipped["low_quality_or_unverified"],
                "skipped_artifact_or_unsafe": skipped["artifact_or_unsafe"],
                "policy": "Only verified, sufficiently high-quality, non-artifact L4 episodes are distilled.",
                "last_distill": time.strftime('%Y-%m-%d %H:%M'),
            }

        os.makedirs(os.path.dirname(self.strategy_file), exist_ok=True)
        with open(self.strategy_file, 'w', encoding='utf-8') as f:
            json.dump(strategy, f, indent=2, ensure_ascii=False)

        self._log_distill(len(episodes))

        return strategy

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

    def _log_distill(self, episode_count: int):
        os.makedirs(os.path.dirname(self.distill_log), exist_ok=True)
        with open(self.distill_log, 'a', encoding='utf-8') as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M')} | {episode_count} | distill completed\n")


class RuleExtractor:
    """从策略统计中提炼可写入 L1 RULES 的规则"""

    def __init__(self):
        from config import MEMORY_CONFIG
        self.strategy_file = MEMORY_CONFIG.get("l4_strategy_file",
                                                "memory/L4_episodes/disease_strategy.json")

    def extract_rules(self, min_cases=10) -> list:
        """提炼高置信度规则"""
        if not os.path.exists(self.strategy_file):
            return []

        with open(self.strategy_file, 'r', encoding='utf-8') as f:
            strategy = json.load(f)

        rules = []
        for disease, s in strategy.items():
            if s.get("total_cases", 0) < min_cases:
                continue

            for tool, util in s.get("tool_utility", {}).items():
                rate = util.get("usefulness_rate", 0)
                called = util.get("called_count", 0)

                if called >= min_cases and rate < 0.1:
                    rules.append(
                        f"{disease}: {tool} 有用率仅 {rate:.0%} ({called}次调用)，建议避免"
                    )
                elif called >= min_cases and rate > 0.85:
                    rules.append(
                        f"{disease}: {tool} 有用率 {rate:.0%}，建议始终调用"
                    )

        return rules
