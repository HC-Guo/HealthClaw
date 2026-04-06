# -*- coding: utf-8 -*-
"""Streamlit stapp 界面文案（zh / en）。业务逻辑仍在 stapp.py。"""

from __future__ import annotations

from typing import Any, Mapping

LOCALES = ("zh", "en")
DEFAULT_LOCALE = "en"


def page_title_for_locale(locale: str) -> str:
    loc = locale if locale in LOCALES else DEFAULT_LOCALE
    return _PAGE_TITLE[loc]


def get_text(locale: str, key: str, **kwargs: Any) -> str:
    loc = locale if locale in LOCALES else DEFAULT_LOCALE
    table: Mapping[str, str] = _STRINGS[loc]
    s = table.get(key) or _STRINGS[DEFAULT_LOCALE].get(key) or key
    return s.format(**kwargs) if kwargs else s


def subtask_display_name_desc(task: Mapping[str, Any], locale: str) -> tuple[str, str]:
    """展示名来自主 SOP 注册表 JSON：`name`/`description`（中文 UI），`name_en`/`description_en`（英文 UI，缺省时回退到中文字段）。"""
    loc = locale if locale in LOCALES else DEFAULT_LOCALE
    if loc == "en":
        name = (task.get("name_en") or task.get("name") or "").strip()
        desc = (task.get("description_en") or task.get("description") or "").strip()
        return (str(name), str(desc))
    name = (task.get("name") or "").strip()
    desc = (task.get("description") or "").strip()
    return (str(name), str(desc))


# --- 自主探索：稳定 id + 关键词（与文件名匹配逻辑不变）---
_DOMAIN_ROWS: list[tuple[str, list[str]]] = [
    ("disease_dx", ["breast_cancer", "cardiovascular", "diabetes", "lung_cancer"]),
    ("med_safety", ["medication_review"]),
    ("icd", ["icd_coding"]),
    ("imaging", ["imaging_report", "imaging_centered"]),
    ("compliance", ["compliance_review", "clinical_pathway"]),
    ("evidence", ["evidence_grading"]),
]

_LEARNING_DIRECTION_IDS: list[str] = [
    "disease_dx",
    "guidelines",
    "med_safety",
    "icd",
    "imaging",
    "insurance_policy",
    "compliance",
    "bioinfo_tools",
    "health_literacy",
    "evidence",
]

_DOMAIN_LABEL: dict[str, dict[str, str]] = {
    "zh": {
        "disease_dx": "疾病诊断知识",
        "med_safety": "药物安全知识",
        "icd": "ICD编码规则",
        "imaging": "影像判读标准",
        "compliance": "合规审查知识",
        "evidence": "证据来源验证",
    },
    "en": {
        "disease_dx": "Disease diagnosis",
        "med_safety": "Medication safety",
        "icd": "ICD coding",
        "imaging": "Imaging interpretation",
        "compliance": "Compliance review",
        "evidence": "Evidence appraisal",
    },
}

_LEARNING_DIRECTION_LABEL: dict[str, dict[str, str]] = {
    "zh": {
        "disease_dx": "疾病诊断知识",
        "guidelines": "临床指南更新",
        "med_safety": "药物安全知识",
        "icd": "ICD编码规则",
        "imaging": "影像判读标准",
        "insurance_policy": "医保政策更新",
        "compliance": "合规审查知识",
        "bioinfo_tools": "生信工具更新",
        "health_literacy": "健康科普素材",
        "evidence": "证据来源验证",
    },
    "en": {
        "disease_dx": "Disease diagnosis",
        "guidelines": "Clinical guideline updates",
        "med_safety": "Medication safety",
        "icd": "ICD coding rules",
        "imaging": "Imaging interpretation standards",
        "insurance_policy": "Insurance policy updates",
        "compliance": "Compliance review",
        "bioinfo_tools": "Bioinformatics tools",
        "health_literacy": "Health literacy content",
        "evidence": "Evidence source verification",
    },
}


def autonomous_prompt_for_locale(locale: str, hints: list[str]) -> str:
    loc = locale if locale in LOCALES else DEFAULT_LOCALE
    hint_lines = "\n".join(f"- {h}" for h in hints)
    if loc == "en":
        return (
            "[AUTO]🤖 Autonomous exploration mode is active.\n\n"
            "Follow this workflow:\n"
            "1. Read memory/L3_sops/autonomous_learning_sop.md for the learning SOP and direction pool\n"
            "2. Review memory/L1_disease_insight.txt to assess current coverage\n"
            "3. Choose a learning direction from the clues below (prioritize filling gaps)\n"
            "4. Learn with web_search + browse_and_learn (do NOT use browser_navigate or similar tampermonkey tools)\n"
            "5. Write knowledge into L1/L2/L3 memory\n"
            "6. Write a short report under ./autonomous_reports/\n\n"
            f"Current analysis:\n{hint_lines}\n\n"
            "Constraints: ≤15 turns | write only cwd and memory | follow L0 memory rules | keep the report concise | "
            "do not use browser_navigate/browser_click/browser_search or similar tampermonkey tools\n"
        )
    return (
        "[AUTO]🤖 自主探索模式已激活。\n\n"
        "请按以下流程执行：\n"
        "1. 读取 memory/L3_sops/autonomous_learning_sop.md 了解学习SOP和方向池\n"
        "2. 检查 memory/L1_disease_insight.txt 评估当前知识覆盖\n"
        "3. 根据以下线索选择学习方向（优先填补知识空白）\n"
        "4. 用 web_search + browse_and_learn 学习（禁止直接使用 browser_navigate 等篡改猴工具）\n"
        "5. 将知识写入 L1/L2/L3 记忆\n"
        "6. 写一份简短报告到 ./autonomous_reports/\n\n"
        f"当前分析:\n{hint_lines}\n\n"
        "约束：≤15回合 | 只写cwd和memory | 遵守L0记忆规则 | 报告要简洁 | 禁用 browser_navigate/browser_click/browser_search 等篡改猴工具\n"
    )


def build_autonomous_hints(
    locale: str,
    base_dir: str,
    existing_sops: set[str],
    strategy_low_conf: list[str],
    recent_topics: list[str],
) -> list[str]:
    import os

    loc = locale if locale in LOCALES else DEFAULT_LOCALE
    hints: list[str] = []

    l1_path = os.path.join(base_dir, "memory", "L1_disease_insight.txt")
    l1_content = ""
    if os.path.exists(l1_path):
        try:
            with open(l1_path, "r", encoding="utf-8") as f:
                l1_content = f.read()
            if len(l1_content) < 200:
                if loc == "en":
                    hints.append(
                        "L1 index is very sparse; prioritize enriching common disease mappings and the health index."
                    )
                else:
                    hints.append("L1索引内容极少，建议优先充实常见疾病映射和健康管理索引。")
        except Exception:
            pass

    weak_ids: list[str] = []
    for domain_id, keywords in _DOMAIN_ROWS:
        if not any(any(kw in sop for kw in keywords) for sop in existing_sops):
            weak_ids.append(domain_id)
    if weak_ids:
        labels = [_DOMAIN_LABEL[loc][i] for i in weak_ids if i in _DOMAIN_LABEL[loc]]
        if loc == "en":
            hints.append(f"Capability areas missing SOPs: {', '.join(labels)}")
        else:
            hints.append(f"以下能力域缺少SOP: {', '.join(labels)}")

    if strategy_low_conf:
        if loc == "en":
            hints.append(
                f"Low-confidence diseases: {', '.join(strategy_low_conf[:3])}; consider targeted learning."
            )
        else:
            hints.append(
                f"低置信度疾病: {', '.join(strategy_low_conf[:3])}，建议针对性学习。"
            )

    if recent_topics:
        tail = "; ".join(recent_topics[-5:])
        if loc == "en":
            hints.append(
                f"Recently explored: {tail}. Please pick a different direction when possible."
            )
        else:
            hints.append(f"近期已探索: {tail}，请选择不同方向。")

    return hints


def format_suggested_direction_line(locale: str, direction_id: str) -> str:
    loc = locale if locale in LOCALES else DEFAULT_LOCALE
    label = _LEARNING_DIRECTION_LABEL[loc].get(direction_id, direction_id)
    if loc == "en":
        return f"Suggested direction (you may adjust): {label}"
    return f"建议方向（可自主调整）: {label}"


def pick_suggested_direction_id(recent_topics: list[str], locale: str) -> str:
    import random

    loc = locale if locale in LOCALES else DEFAULT_LOCALE
    labels_zh = _LEARNING_DIRECTION_LABEL["zh"]
    # history.txt 通常为中文主题名；与中文标签比对以去重
    available = [
        d
        for d in _LEARNING_DIRECTION_IDS
        if labels_zh.get(d) not in recent_topics and _LEARNING_DIRECTION_LABEL[loc].get(d)
    ]
    if not available:
        available = _LEARNING_DIRECTION_IDS[:]
    return random.choice(available)


_PAGE_TITLE = {
    "zh": "HealthClaw - 个人健康管家",
    "en": "HealthClaw - Personal Health Assistant",
}

_STRINGS: dict[str, dict[str, str]] = {
    "zh": {
        "sidebar_language": "界面语言",
        "err_no_llm": (
            "⚠️ 未配置任何可用的 LLM 接口，请在 mykey.py 中添加 sider_cookie 或 oai_apikey+oai_apibase 等信息后重启。"
        ),
        "main_title": "🩺 HealthClaw — 个人健康管家",
        "main_caption": "在此对话咨询健康问题、上传影像或报告图片；侧栏可管理 Agent、长期记忆、自主学习与一键健康分析。",
        "welcome_info": (
            "**可以这样开始：**\n\n"
            "- 描述症状或用药情况，需要注意事项与就医建议\n\n"
            "- 上传检查报告或皮肤照片，请助手解读要点\n\n"
            "- 请助手分析手机 App 数据并给出健康建议\n\n"
            "- 侧栏「一键健康分析」汇总手机健康 App 数据（需按流程授权）"
        ),
        "sidebar_agent": "⚙️ Agent 状态",
        "llm_caption_help": "当前使用的 LLM 链路，点击下方按钮可切换备用链路",
        "status_running": "🔄 运行中",
        "status_idle": "💤 空闲 {secs}s",
        "status_label": "状态: {status}",
        "btn_switch_llm": "切换备用链路",
        "expander_advanced": "高级与调试",
        "btn_abort": "强行停止任务",
        "toast_abort": "已发送停止信号",
        "btn_reinject": "重新注入 System Prompt",
        "toast_reinject": "下次将重新注入 System Prompt",
        "toggle_debug": "显示 Agent 调试输出",
        "toggle_debug_help": (
            "开启（默认）：展示完整原始流，含 <thinking>、<summary>、<tool_use>、<tool_result> 等协议标签。\n"
            "关闭：隐藏上述协议标签，仍保留 **LLM Running (Turn n)**、正在调用工具说明与五反引号工具执行输出。"
        ),
        "sidebar_memory": "🧠 长期记忆",
        "sidebar_memory_help": "控制当前浏览器会话是否写入/更新长期记忆（L2/L3/L4）",
        "toggle_ltm": "使用长期记忆优化回答",
        "toggle_ltm_help": (
            "开启：允许将本轮对话中的关键信息写入 L2/L3/L4，用于优化后续回答。\n"
            "关闭：跳过 start_long_term_update 和对话结束后的自动记忆提取，适合一次性调试/高度隐私内容。"
        ),
        "caption_ltm_on": "✅ 当前会话允许写入长期记忆，将用于优化后续回答。",
        "caption_ltm_off": "⛔ 本轮对话不会写入长期记忆，仅做即时回答。",
        "sidebar_auto": "🌐 自主探索模式",
        "sidebar_auto_help": "Agent 空闲时是否后台自行学习医学/健康相关知识",
        "toggle_auto": "允许空闲时在后台自动学习",
        "toggle_auto_help": "开启后：Agent 在空闲 ≥ 阈值 秒时会自动发起一次学习任务（不依赖浏览器前端）。",
        "caption_auto_on": "🟢 后台自动探索已开启 — 空闲 {threshold}s 后自动学习",
        "caption_auto_idle": "当前空闲 {idle}s / 阈值 {threshold}s",
        "caption_auto_count": "📊 已完成 {count} 次自主学习",
        "btn_auto_now": "🚀 立即开始一次自主学习",
        "caption_auto_off": "⚪ 自主探索已关闭 — 仅在你主动提问时工作。",
        "expander_auto_log": "📋 自主学习记录（最近 {n} 条）",
        "sidebar_one_click": "🏥 一键健康分析",
        "sidebar_one_click_cap": "自动分析手机中各健康App数据，生成综合健康报告",
        "btn_one_click_start": "🚀 开始一键健康分析",
        "caption_registry_hint": "若你刚和助手完成**新的**健康类操作，可点击下方把该流程登记进「一键分析」勾选列表。",
        "btn_add_registry": "➕ 将本轮对话加入一键健康分析",
        "btn_add_registry_help": (
            "助手会结合**上面聊天记录**判断：这是否是尚未收录的一键子任务。"
            "若是，会更新「一键分析」里可勾选的 App/场景（并写好对应操作说明）；"
            "不会把你刚才对话里的隐私原文写进长期记忆。"
        ),
        "health_plan_title": "### 📋 健康分析计划确认",
        "health_plan_caption": (
            "请确认分析范围后点击执行。列表来自系统配置；"
            "若要把**新 App/新流程**加进本列表，请用侧栏「➕ 将本轮对话加入一键健康分析」。"
        ),
        "health_plan_days": "分析时间范围（天）",
        "health_plan_pick": "**选择分析子任务：**",
        "btn_confirm": "✅ 确认执行",
        "btn_cancel": "❌ 取消",
        "warn_pick_one": "请至少勾选一个子任务",
        "one_click_fallback_display": "🏥 一键健康分析",
        "one_click_user_header": "🏥 **一键健康分析** — 最近{days}天\n",
        "registry_user_msg": "➕ **将本轮对话登记为一键健康分析子任务**（助手将判断是否为新场景并更新可选列表）",
        "file_upload_label": "📎 上传图片（医学影像、检查报告、皮肤照片等）",
        "upload_caption": "已上传: {name}",
        "chat_input_placeholder": "请输入指令（可同时上传图片）",
        "manual_auto_display": "🤖 [手动触发] 自主学习已启动",
        "registry_ctx_empty": "（暂无历史对话）",
        "registry_ctx_truncated": "…[截断]",
        "registry_ctx_omitted": "…[更早消息已省略]\n\n",
    },
    "en": {
        "sidebar_language": "Interface language",
        "err_no_llm": (
            "⚠️ No usable LLM endpoint is configured. Add sider_cookie or oai_apikey+oai_apibase in mykey.py, then restart."
        ),
        "main_title": "🩺 HealthClaw — Personal Health Assistant",
        "main_caption": (
            "Chat about health, upload imaging or report photos; use the sidebar for Agent controls, long-term memory, "
            "autonomous learning, and one-click health analysis."
        ),
        "welcome_info": (
            "**You can start by:**\n\n"
            "- Describing symptoms or medications and asking for precautions and care guidance\n\n"
            "- Uploading lab reports or skin photos for key takeaways\n\n"
            "- Asking the assistant to analyze mobile app data and suggest healthy habits\n\n"
            "- Using sidebar **One-click health analysis** to aggregate health-app data (authorization required)"
        ),
        "sidebar_agent": "⚙️ Agent status",
        "llm_caption_help": "Current LLM stack; use the button below to switch to a fallback stack",
        "status_running": "🔄 Running",
        "status_idle": "💤 Idle {secs}s",
        "status_label": "Status: {status}",
        "btn_switch_llm": "Switch fallback stack",
        "expander_advanced": "Advanced & debug",
        "btn_abort": "Abort task",
        "toast_abort": "Stop signal sent",
        "btn_reinject": "Re-inject system prompt",
        "toast_reinject": "System prompt will refresh on next turn",
        "toggle_debug": "Show agent debug stream",
        "toggle_debug_help": (
            "On (default): full raw stream including <thinking>, <summary>, <tool_use>, <tool_result>, etc.\n"
            "Off: hide those protocol tags; still show **LLM Running (Turn n)**, tool-call notices, and fenced tool output."
        ),
        "sidebar_memory": "🧠 Long-term memory",
        "sidebar_memory_help": "Whether this browser session may write/update long-term memory (L2/L3/L4)",
        "toggle_ltm": "Use long-term memory to improve answers",
        "toggle_ltm_help": (
            "On: allow writing key session facts to L2/L3/L4 for better follow-up answers.\n"
            "Off: skip start_long_term_update and post-turn memory extraction—useful for one-off tests or high privacy."
        ),
        "caption_ltm_on": "✅ This session may write long-term memory for better follow-up answers.",
        "caption_ltm_off": "⛔ This session will not write long-term memory; answers are ephemeral.",
        "sidebar_auto": "🌐 Autonomous exploration",
        "sidebar_auto_help": "Whether the agent may learn in the background while idle",
        "toggle_auto": "Allow background learning when idle",
        "toggle_auto_help": (
            "When on: after idle ≥ threshold seconds, the agent starts a learning task automatically (no browser UI needed)."
        ),
        "caption_auto_on": "🟢 Background exploration on — starts after {threshold}s idle",
        "caption_auto_idle": "Idle {idle}s / threshold {threshold}s",
        "caption_auto_count": "📊 {count} autonomous run(s) completed",
        "btn_auto_now": "🚀 Run autonomous learning now",
        "caption_auto_off": "⚪ Autonomous exploration off — only runs when you ask.",
        "expander_auto_log": "📋 Autonomous runs (last {n})",
        "sidebar_one_click": "🏥 One-click health analysis",
        "sidebar_one_click_cap": "Analyze health apps on your phone and produce a consolidated report",
        "btn_one_click_start": "🚀 Start one-click health analysis",
        "caption_registry_hint": (
            "If you just finished a **new** health workflow with the assistant, register it below to add it to the checklist."
        ),
        "btn_add_registry": "➕ Add this chat to one-click analysis",
        "btn_add_registry_help": (
            "The assistant reads the **chat above** to decide whether this is a new one-click subtask. "
            "If so, it updates the selectable apps/scenarios (with instructions) without storing private chat text in memory."
        ),
        "health_plan_title": "### 📋 Confirm analysis plan",
        "health_plan_caption": (
            "Confirm scope, then run. The list comes from system config. "
            "To add a **new app/workflow**, use sidebar **➕ Add this chat to one-click analysis**."
        ),
        "health_plan_days": "Analysis window (days)",
        "health_plan_pick": "**Select subtasks:**",
        "btn_confirm": "✅ Run",
        "btn_cancel": "❌ Cancel",
        "warn_pick_one": "Select at least one subtask",
        "one_click_fallback_display": "🏥 One-click health analysis",
        "one_click_user_header": "🏥 **One-click health analysis** — last {days} day(s)\n",
        "registry_user_msg": (
            "➕ **Register this chat as a one-click subtask** (assistant decides if it is new and updates the checklist)"
        ),
        "file_upload_label": "📎 Upload image (imaging, lab report, skin photo, etc.)",
        "upload_caption": "Uploaded: {name}",
        "chat_input_placeholder": "Type a message (you can also attach an image above)",
        "manual_auto_display": "🤖 [Manual] Autonomous learning started",
        "registry_ctx_empty": "(No prior chat history)",
        "registry_ctx_truncated": "…[truncated]",
        "registry_ctx_omitted": "…[earlier messages omitted]\n\n",
    },
}
