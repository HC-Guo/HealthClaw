"""
情景记忆写入器 - 将病例反思写入 L4
"""
import os, json, time
from evolution.memory_policy import normalize_episode


class EpisodeWriter:
    """管理 L4 情景记忆的写入和统计"""

    def __init__(self):
        from config import MEMORY_CONFIG
        self.episodes_file = MEMORY_CONFIG.get("l4_episodes_file",
                                                "memory/L4_episodes/case_episodes.jsonl")
        self.distill_log = MEMORY_CONFIG.get("distill_log_file",
                                              "memory/L4_episodes/distill_log.txt")

    def write(self, episode: dict):
        """追加一条情景记忆"""
        episode = normalize_episode(episode)
        os.makedirs(os.path.dirname(self.episodes_file), exist_ok=True)
        with open(self.episodes_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(episode, ensure_ascii=False) + '\n')

    def count_total(self) -> int:
        """统计总情景数"""
        if not os.path.exists(self.episodes_file):
            return 0
        with open(self.episodes_file, 'r', encoding='utf-8') as f:
            return sum(1 for line in f if line.strip())

    def count_since_last_distill(self) -> int:
        """统计上次蒸馏以来的新情景数"""
        last_distill_count = 0
        if os.path.exists(self.distill_log):
            try:
                with open(self.distill_log, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                if lines:
                    last_line = lines[-1].strip()
                    parts = last_line.split('|')
                    if len(parts) >= 2:
                        last_distill_count = int(parts[1].strip())
            except (ValueError, IndexError):
                pass
        return self.count_total() - last_distill_count

    def read_all(self) -> list:
        """读取所有情景记忆"""
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

    def backfill_outcome(self, episode_id: str, outcome_correct: bool):
        """回填 ground truth 验证结果"""
        if not os.path.exists(self.episodes_file):
            return False

        episodes = self.read_all()
        updated = False
        with open(self.episodes_file, 'w', encoding='utf-8') as f:
            for ep in episodes:
                if ep.get("episode_id") == episode_id:
                    ep["outcome_correct"] = outcome_correct
                    ep = normalize_episode(ep)
                    updated = True
                f.write(json.dumps(ep, ensure_ascii=False) + '\n')
        return updated
