# -*- coding: utf-8 -*-
"""
一键健康分析：路径常量、主 SOP 写保护策略、任务模式与 prompt 拼装。
供 ga.py / seda_main.py / stapp.py 引用，避免逻辑与文案散落多处。

Agent 侧执行步骤、报告模板、注册表更新规程仍以 L3  Markdown 为准：
- memory/L3_sops/one_click_health_analysis_sop.md（注册表 JSON 含 name_en/description_en 供英文 UI）
- memory/L3_sops/one_click_registry_update_sop.md
本模块不替代上述 SOP，仅保证路径/mode/闸门与 UI 与之一致。
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Optional, Tuple

# --- 相对项目根的路径（与 ga.GenericAgentHandler._get_abs_path 解析 memory/ 一致）---
MAIN_SOP_RELPATH = "memory/L3_sops/one_click_health_analysis_sop.md"
REGISTRY_UPDATE_SOP_RELPATH = "memory/L3_sops/one_click_registry_update_sop.md"
L1_RELPATH = "memory/L1_disease_insight.txt"
L1_ONE_CLICK_SECTION = "## [ONE_CLICK_HEALTH]"

# --- 任务字典字段（put_task / run）---
TASK_KEY_REGISTRY_UPDATE = "one_click_registry_update"

# --- Prompt 模式（勿随意改名，与记忆后处理拦截一致）---
MODE_HEALTH_ANALYSIS = "one_click_health_analysis"
MODE_REGISTRY_UPDATE = "one_click_registry_update"
PROMPT_TAG_HEALTH_ANALYSIS = "[一键健康分析指令]"

# 与 MAIN_SOP_RELPATH 对齐，用于 endswith 判定（POSIX 风格）
_MAIN_SOP_SUFFIX_POSIX = MAIN_SOP_RELPATH.replace("\\", "/")

DEFAULT_SUBTASKS: list[dict[str, Any]] = [
    {
        "id": "meituan_food_analysis",
        "name": "美团外卖饮食分析",
        "description": "读取美团外卖近期订单，分析饮食结构、营养均衡度与健康风险",
        "name_en": "Meituan food delivery analysis",
        "description_en": "Read recent Meituan orders; analyze diet structure, nutritional balance, and health risks",
        "sop_file": "meituan_food_analysis_sop.md",
        "enabled_by_default": True,
    },
    {
        "id": "xiaomi_stress_analysis",
        "name": "小米运动健康压力分析",
        "description": "读取小米运动健康App压力周视图，分析压力水平、高压时段与风险提示",
        "name_en": "Xiaomi Health stress analysis",
        "description_en": "Read the Xiaomi Health app weekly stress view; analyze stress levels, high-pressure periods, and risk notes",
        "sop_file": "xiaomi_health_analysis_sop.md",
        "enabled_by_default": True,
    },
]

MSG_PATCH_DENIED = (
    "one_click_health_analysis_sop.md 为受保护的一键健康分析主 SOP（编排与报告模板不可改）。"
    "请使用 Streamlit 侧「主动更新子任务注册表」流程获得白名单后，仅通过 file_patch 更新 "
    "REGISTRY 注释下方的 JSON 围栏内 subtasks 区块。"
)
MSG_WRITE_DENIED = (
    "禁止对一键健康分析主 SOP 使用 file_write（含 append/prepend/overwrite）。"
    "请使用「主动更新子任务注册表」白名单任务，仅通过 file_patch 最小范围修改 subtasks JSON。"
)


def get_project_root() -> Path:
    """本文件位于 <root>/tools/one_click_health.py"""
    return Path(__file__).resolve().parent.parent


def normalize_posix_path(path: str) -> str:
    if not path:
        return ""
    return Path(path).resolve().as_posix()


def is_protected_one_click_main_sop(abs_path: str) -> bool:
    if not abs_path:
        return False
    return normalize_posix_path(abs_path).endswith(_MAIN_SOP_SUFFIX_POSIX)


def main_sop_abs_path(project_root: Optional[Path] = None) -> str:
    root = project_root or get_project_root()
    return str((root / MAIN_SOP_RELPATH).resolve())


def check_one_click_main_sop_file_patch_allowed(
    abs_path: str, allow_registry_edit: bool
) -> Tuple[bool, Optional[str]]:
    if not is_protected_one_click_main_sop(abs_path):
        return True, None
    if allow_registry_edit:
        return True, None
    return False, MSG_PATCH_DENIED


def check_one_click_main_sop_file_write_allowed(abs_path: str) -> Tuple[bool, Optional[str]]:
    if not is_protected_one_click_main_sop(abs_path):
        return True, None
    return False, MSG_WRITE_DENIED


def sop_slug_from_title(title: str) -> str:
    """与 seda_main._save_sop 中 slug 规则一致"""
    slug = re.sub(r"[^\w\u4e00-\u9fff]+", "_", (title or "")).strip("_").lower()
    return slug


def is_one_click_query_blocked_for_sop_learn(user_query: str) -> bool:
    if not user_query:
        return False
    ql = user_query.lower()
    if f"mode={MODE_HEALTH_ANALYSIS}" in ql:
        return True
    if f"mode={MODE_REGISTRY_UPDATE}" in ql:
        return True
    if PROMPT_TAG_HEALTH_ANALYSIS in user_query:
        return True
    return False


def should_skip_autosave_sop(title: str, user_query: str) -> Tuple[bool, str]:
    """自动 SOPLearn 落盘前调用；返回 (skip, reason_log)"""
    slug = sop_slug_from_title(title)
    learned_filename = f"{slug}_sop.md" if slug else ""
    if learned_filename == "one_click_health_analysis_sop.md":
        return True, f"protected filename {learned_filename}"
    if slug == "one_click_health_analysis_sop":
        return True, "protected slug"
    if is_one_click_query_blocked_for_sop_learn(user_query):
        return True, "one-click / registry task"
    return False, ""


def load_subtasks_from_main_sop(project_root: Optional[Path] = None) -> list[dict[str, Any]]:
    root = project_root or get_project_root()
    path = root / MAIN_SOP_RELPATH
    try:
        content = path.read_text(encoding="utf-8")
        m = re.search(r"```json\s*\n(\{.*?\})\s*\n```", content, re.DOTALL)
        if m:
            data = json.loads(m.group(1))
            tasks = data.get("subtasks", [])
            if tasks:
                return tasks
    except Exception:
        pass
    return list(DEFAULT_SUBTASKS)


def build_one_click_analysis_prompt(time_window_days: int, selected_task_ids: list) -> str:
    tasks_str = json.dumps(selected_task_ids, ensure_ascii=False)
    return (
        f"{PROMPT_TAG_HEALTH_ANALYSIS}\n"
        f"mode={MODE_HEALTH_ANALYSIS}\n"
        f"time_window_days={time_window_days}\n"
        f"tasks={tasks_str}\n"
        f"output_format=integrated_report_v1\n\n"
        f"请先读取 {MAIN_SOP_RELPATH} 获取执行规范，"
        f"然后按tasks列表顺序串行执行各子任务SOP，最后按SOP中定义的综合报告模板输出完整报告。\n"
        f"分析时间范围：最近{time_window_days}天。"
    )


def build_registry_update_prompt(recent_chat_context: str) -> str:
    ctx = (recent_chat_context or "").strip() or "（暂无历史对话）"
    return (
        f"mode={MODE_REGISTRY_UPDATE}\n\n"
        f"你必须先完整阅读并按规程执行：{REGISTRY_UPDATE_SOP_RELPATH}\n"
        f"主 SOP {MAIN_SOP_RELPATH} 的 PROTECTED 区域禁止修改；"
        f"仅允许对该文件中 REGISTRY 注释下方的 subtasks JSON 使用 file_patch 做最小增量更新。\n"
        f"同步维护 {L1_RELPATH} 中 {L1_ONE_CLICK_SECTION} 指针行。\n\n"
        f"### 近期对话摘要（判断刚完成的是否为新子任务类型）\n"
        f"{ctx}\n"
    )
