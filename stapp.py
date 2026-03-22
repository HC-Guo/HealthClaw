import os, sys

if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")
try:
    sys.stdout.reconfigure(errors="replace")
except:
    pass
try:
    sys.stderr.reconfigure(errors="replace")
except:
    pass
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import time, json, re, threading
from seda_main import DiagnosisAgent
from tools import one_click_health as och

st.set_page_config(page_title="HealthClaw - 个人健康管家", layout="wide")


def _inject_streamlit_custom_css():
    css_path = os.path.join(os.path.dirname(__file__), "assets", "streamlit_custom.css")
    if os.path.isfile(css_path):
        with open(css_path, encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


_inject_streamlit_custom_css()

if "messages" not in st.session_state:
    st.session_state.messages = []

IDLE_THRESHOLD = 60  # 空闲1分钟后自动探索
IDLE_COOLDOWN = 30  # 两次自动探索间隔至少30秒


def _sanitize_agent_display(text: str, show_debug: bool) -> str:
    """Streamlit 展示用：关闭调试时仅去掉模型协议标签；保留 LLM Running 与工具调用/执行块。"""
    if show_debug or not (text or "").strip():
        return text
    t = text
    for pat in (
        r"<thinking>[\s\S]*?</thinking>",
        r"<summary>[\s\S]*?</summary>",
        r"<tool_use>[\s\S]*?</tool_use>",
        r"<tool_result>[\s\S]*?</tool_result>",
    ):
        t = re.sub(pat, "", t, flags=re.IGNORECASE)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


# ============================================================
# 一键健康分析：子任务与 prompt（逻辑见 tools/one_click_health.py）
# ============================================================
def _load_subtasks_from_sop():
    """从主 SOP 解析 subtasks JSON，失败回退默认列表"""
    return och.load_subtasks_from_main_sop()


def _recent_messages_context_for_registry(
    max_msgs: int = 10, max_chars: int = 3500
) -> str:
    msgs = st.session_state.get("messages") or []
    if not msgs:
        return "（暂无历史对话）"
    chunks = []
    for m in msgs[-max_msgs:]:
        role = m.get("role", "?")
        content = (m.get("content") or "").strip()
        if not content:
            continue
        if len(content) > 800:
            content = content[:800] + "…[截断]"
        chunks.append(f"[{role}]\n{content}")
    text = "\n\n---\n\n".join(chunks)
    if len(text) > max_chars:
        text = "…[更早消息已省略]\n\n" + text[-max_chars:]
    return text


_LEARNING_DIRECTIONS = [
    "疾病诊断知识",
    "临床指南更新",
    "药物安全知识",
    "ICD编码规则",
    "影像判读标准",
    "医保政策更新",
    "合规审查知识",
    "生信工具更新",
    "健康科普素材",
    "证据来源验证",
]

_DOMAIN_SOP_KEYWORDS = {
    "疾病诊断知识": ["breast_cancer", "cardiovascular", "diabetes", "lung_cancer"],
    "药物安全知识": ["medication_review"],
    "ICD编码规则": ["icd_coding"],
    "影像判读标准": ["imaging_report", "imaging_centered"],
    "合规审查知识": ["compliance_review", "clinical_pathway"],
    "证据来源验证": ["evidence_grading"],
}


def _generate_autonomous_prompt_standalone():
    """智能生成自主学习任务提示：基于知识空白+低置信度+轮换策略选择学习方向"""
    hints = []
    base = os.path.dirname(__file__)

    l1_path = os.path.join(base, "memory", "L1_disease_insight.txt")
    l1_content = ""
    if os.path.exists(l1_path):
        try:
            with open(l1_path, "r", encoding="utf-8") as f:
                l1_content = f.read()
            if len(l1_content) < 200:
                hints.append("L1索引内容极少，建议优先充实常见疾病映射和健康管理索引。")
        except Exception:
            pass

    sop_dir = os.path.join(base, "memory", "L3_sops")
    existing_sops = set()
    if os.path.isdir(sop_dir):
        existing_sops = {f for f in os.listdir(sop_dir) if f.endswith(".md")}

    weak_domains = []
    for domain, keywords in _DOMAIN_SOP_KEYWORDS.items():
        if not any(any(kw in sop for kw in keywords) for sop in existing_sops):
            weak_domains.append(domain)
    if weak_domains:
        hints.append(f"以下能力域缺少SOP: {', '.join(weak_domains)}")

    strategy_path = os.path.join(base, "memory", "L4_episodes", "disease_strategy.json")
    if os.path.exists(strategy_path):
        try:
            with open(strategy_path, "r", encoding="utf-8") as f:
                strategy = json.load(f)
            low_conf = [
                d for d, s in strategy.items() if s.get("avg_confidence", 1) < 0.6
            ]
            if low_conf:
                hints.append(
                    f"低置信度疾病: {', '.join(low_conf[:3])}，建议针对性学习。"
                )
        except Exception:
            pass

    recent_topics = []
    history_path = os.path.join(base, "temp", "autonomous_reports", "history.txt")
    if os.path.exists(history_path):
        try:
            with open(history_path, "r", encoding="utf-8") as f:
                recent_topics = [l.strip() for l in f.readlines()[-10:] if l.strip()]
            if recent_topics:
                hints.append(
                    f"近期已探索: {'; '.join(recent_topics[-5:])}，请选择不同方向。"
                )
        except Exception:
            pass

    import random

    available = [d for d in _LEARNING_DIRECTIONS if d not in recent_topics]
    if not available:
        available = _LEARNING_DIRECTIONS[:]
    suggested = random.choice(available)
    hints.append(f"建议方向（可自主调整）: {suggested}")

    hints_block = "\n".join(f"- {h}" for h in hints)

    return (
        "[AUTO]🤖 自主探索模式已激活。\n\n"
        "请按以下流程执行：\n"
        "1. 读取 memory/L3_sops/autonomous_learning_sop.md 了解学习SOP和方向池\n"
        "2. 检查 memory/L1_disease_insight.txt 评估当前知识覆盖\n"
        "3. 根据以下线索选择学习方向（优先填补知识空白）\n"
        "4. 用 web_search + browse_and_learn 学习（禁止直接使用 browser_navigate 等篡改猴工具）\n"
        "5. 将知识写入 L1/L2/L3 记忆\n"
        "6. 写一份简短报告到 ./autonomous_reports/\n\n"
        f"当前分析:\n{hints_block}\n\n"
        "约束：≤15回合 | 只写cwd和memory | 遵守L0记忆规则 | 报告要简洁 | 禁用 browser_navigate/browser_click/browser_search 等篡改猴工具\n"
    )


def _auto_explore_daemon(agent):
    """服务端后台自动探索线程（不依赖浏览器）。
    使用 agent.lock 防止与用户任务竞态。"""
    print(
        f"[AutoExplore] Daemon started (threshold={IDLE_THRESHOLD}s, cooldown={IDLE_COOLDOWN}s)",
        flush=True,
    )
    last_trigger = 0
    check_count = 0
    while True:
        time.sleep(30)
        check_count += 1
        try:
            idle = time.time() - agent.last_task_time
            cooldown_ok = time.time() - last_trigger > IDLE_COOLDOWN

            if check_count % 10 == 1:
                print(
                    f"[AutoExplore] Check #{check_count}: enabled={agent.auto_explore_enabled}, "
                    f"running={agent.is_running}, idle={int(idle)}s, cooldown_ok={cooldown_ok}",
                    flush=True,
                )

            if not agent.auto_explore_enabled:
                continue
            if agent.is_running:
                if check_count % 5 == 0:
                    print(f"[AutoExplore] Skipped: agent is running", flush=True)
                continue
            if idle < IDLE_THRESHOLD or not cooldown_ok:
                continue

            acquired = agent.lock.acquire(blocking=False)
            if not acquired:
                print(
                    "[AutoExplore] Lock busy (user task likely starting), skipping",
                    flush=True,
                )
                continue
            try:
                if agent.is_running or not agent.task_queue.empty():
                    print(
                        "[AutoExplore] Agent became busy after lock, skipping",
                        flush=True,
                    )
                    continue
                print(
                    f"[AutoExplore] Idle {int(idle)}s >= {IDLE_THRESHOLD}s, triggering autonomous learning...",
                    flush=True,
                )
                last_trigger = time.time()
                prompt = _generate_autonomous_prompt_standalone()
                dq = agent.put_task(prompt, source="auto")
            finally:
                agent.lock.release()

            task_start = time.time()
            MAX_TASK_TIME = 300
            completed = False
            while True:
                try:
                    item = dq.get(timeout=30)
                    if "done" in item:
                        resp = item["done"]
                        summary = resp[:200] + "..." if len(resp) > 200 else resp
                        print(
                            f"[AutoExplore] Task completed ({len(resp)} chars): {summary}",
                            flush=True,
                        )
                        agent._auto_results.append(
                            {"time": time.strftime("%Y-%m-%d %H:%M"), "response": resp}
                        )
                        if len(agent._auto_results) > 50:
                            agent._auto_results = agent._auto_results[-30:]
                        completed = True
                        break
                except Exception:
                    elapsed = time.time() - task_start
                    if elapsed > MAX_TASK_TIME:
                        print(
                            f"[AutoExplore] Task exceeded {MAX_TASK_TIME}s, force aborting...",
                            flush=True,
                        )
                        agent.abort()
                        time.sleep(3)
                        if agent.is_running:
                            print(
                                "[AutoExplore] Force resetting agent.is_running",
                                flush=True,
                            )
                            agent.is_running = False
                            agent.stop_sig = False
                        break

            if not completed:
                print(
                    f"[AutoExplore] Task ended (completed={completed}), will retry after cooldown",
                    flush=True,
                )
        except Exception as e:
            print(f"[AutoExplore] Error: {e}")
            time.sleep(60)


@st.cache_resource
def init():
    agent = DiagnosisAgent()
    agent._auto_results = []
    if agent.llmclient is None:
        st.error(
            "⚠️ 未配置任何可用的 LLM 接口，请在 mykey.py 中添加 sider_cookie 或 oai_apikey+oai_apibase 等信息后重启。"
        )
        st.stop()
    else:
        threading.Thread(target=agent.run, daemon=True).start()
        threading.Thread(
            target=_auto_explore_daemon, args=(agent,), daemon=True, name="auto-explore"
        ).start()
    return agent


agent = init()

st.title("🩺 HealthClaw — 个人健康管家")
st.caption(
    "在此对话咨询健康问题、上传影像或报告图片；侧栏可管理 Agent、长期记忆、自主学习与一键健康分析。"
)
if not st.session_state.messages and not st.session_state.get(
    "_show_health_plan_form", False
):
    st.info(
        "**可以这样开始：**\n\n"
        "- 描述症状或用药情况，需要注意事项与就医建议\n\n"
        "- 上传检查报告或皮肤照片，请助手解读要点\n\n"
        "- 请助手分析手机 App 数据并给出健康建议\n\n"
        "- 侧栏「一键健康分析」汇总手机健康 App 数据（需按流程授权）"
    )


@st.fragment
def render_sidebar():
    # === 1. Agent 状态与基础控制 ===
    st.subheader("⚙️ Agent 状态")
    current_idx = agent.llm_no
    st.caption(
        f"LLM Core: {current_idx}: {agent.get_llm_name()}",
        help="当前使用的 LLM 链路，点击下方按钮可切换备用链路",
    )
    idle_secs = int(time.time() - agent.last_task_time)
    status = "🔄 运行中" if agent.is_running else f"💤 空闲 {idle_secs}s"
    st.caption(f"状态: {status}")

    if st.button("切换备用链路"):
        agent.next_llm()
        st.rerun(scope="fragment")

    if "show_agent_debug_output" not in st.session_state:
        st.session_state["show_agent_debug_output"] = True
    with st.expander("高级与调试", expanded=False):
        if st.button("强行停止任务"):
            agent.abort()
            st.toast("已发送停止信号")
            st.rerun()
        if st.button("重新注入 System Prompt"):
            agent.llmclient.last_tools = ""
            st.toast("下次将重新注入 System Prompt")
        st.toggle(
            "显示 Agent 调试输出",
            key="show_agent_debug_output",
            help=(
                "开启（默认）：展示完整原始流，含 <thinking>、<summary>、<tool_use>、<tool_result> 等协议标签。\n"
                "关闭：隐藏上述协议标签，仍保留 **LLM Running (Turn n)**、正在调用工具说明与五反引号工具执行输出。"
            ),
        )

    st.divider()

    # === 2. 记忆策略设置 ===
    st.subheader(
        "🧠 长期记忆", help="控制当前浏览器会话是否写入/更新长期记忆（L2/L3/L4）"
    )
    # 使用 session_state 作为单一真值来源，避免 widget 与 agent 属性在 rerun 时互相覆盖导致的闪烁。
    # 仅在第一次访问该会话时，从 agent 读取默认值。
    if "long_term_memory_enabled" not in st.session_state:
        st.session_state["long_term_memory_enabled"] = getattr(
            agent, "enable_long_term_memory", True
        )
    st.toggle(
        "使用长期记忆优化回答",
        key="long_term_memory_enabled",
        help=(
            "开启：允许将本轮对话中的关键信息写入 L2/L3/L4，用于优化后续回答。\n"
            "关闭：跳过 start_long_term_update 和对话结束后的自动记忆提取，适合一次性调试/高度隐私内容。"
        ),
    )
    agent.enable_long_term_memory = st.session_state["long_term_memory_enabled"]
    if st.session_state["long_term_memory_enabled"]:
        st.caption("✅ 当前会话允许写入长期记忆，将用于优化后续回答。")
    else:
        st.caption("⛔ 本轮对话不会写入长期记忆，仅做即时回答。")

    st.divider()

    # === 3. 自主探索模式 ===
    st.subheader(
        "🌐 自主探索模式", help="Agent 空闲时是否后台自行学习医学/健康相关知识"
    )
    if "auto_explore_enabled" not in st.session_state:
        st.session_state["auto_explore_enabled"] = agent.auto_explore_enabled
    st.toggle(
        "允许空闲时在后台自动学习",
        key="auto_explore_enabled",
        help="开启后：Agent 在空闲 ≥ 阈值 秒时会自动发起一次学习任务（不依赖浏览器前端）。",
    )
    agent.auto_explore_enabled = st.session_state["auto_explore_enabled"]
    if not st.session_state["auto_explore_enabled"]:
        agent.autonomous_mode = False

    if st.session_state["auto_explore_enabled"]:
        st.caption(f"🟢 后台自动探索已开启 — 空闲 {IDLE_THRESHOLD}s 后自动学习")
        st.caption(f"当前空闲 {idle_secs}s / 阈值 {IDLE_THRESHOLD}s")

        auto_count = len(getattr(agent, "_auto_results", []))
        if auto_count:
            st.caption(f"📊 已完成 {auto_count} 次自主学习")

        if st.button("🚀 立即开始一次自主学习", type="primary"):
            agent.autonomous_mode = True
            st.session_state["_manual_auto_learn"] = True
            st.rerun()
    else:
        st.caption("⚪ 自主探索已关闭 — 仅在你主动提问时工作。")

    # 自主学习记录统一放在底部
    if getattr(agent, "_auto_results", []):
        with st.expander(f"📋 自主学习记录（最近 {len(agent._auto_results)} 条）"):
            for r in reversed(agent._auto_results[-5:]):
                st.markdown(f"**{r['time']}**")
                st.text(
                    r["response"][:300] + ("..." if len(r["response"]) > 300 else "")
                )
                st.divider()

    st.divider()

    # === 4. 一键健康分析 ===
    st.subheader("🏥 一键健康分析")
    st.caption("自动分析手机中各健康App数据，生成综合健康报告")
    if st.button("🚀 开始一键健康分析", type="primary", use_container_width=True):
        st.session_state["_show_health_plan_form"] = True
        st.rerun()
    st.caption(
        "若你刚和助手完成**新的**健康类操作，可点击下方把该流程登记进「一键分析」勾选列表。"
    )
    if st.button(
        "➕ 将本轮对话加入一键健康分析",
        use_container_width=True,
        help=(
            "助手会结合**上面聊天记录**判断：这是否是尚未收录的一键子任务。"
            "若是，会更新「一键分析」里可勾选的 App/场景（并写好对应操作说明）；"
            "不会把你刚才对话里的隐私原文写进长期记忆。"
        ),
    ):
        st.session_state["_pending_registry_prompt"] = och.build_registry_update_prompt(
            _recent_messages_context_for_registry()
        )
        st.rerun()


with st.sidebar:
    render_sidebar()


def agent_backend_stream(
    prompt, image_base64=None, autonomous=False, **put_task_kwargs
):
    agent.autonomous_mode = autonomous
    if agent.is_running:
        agent.abort()
        for _ in range(30):
            if not agent.is_running:
                break
            time.sleep(0.3)
        if agent.is_running:
            agent.is_running = False
            agent.stop_sig = False
    display_queue = agent.put_task(
        prompt, source="user", image_base64=image_base64, **put_task_kwargs
    )
    try:
        while True:
            item = display_queue.get()
            if "next" in item:
                yield item["next"]
            if "done" in item:
                yield item["done"]
                break
    finally:
        agent.abort()


_dbg = st.session_state.get("show_agent_debug_output", True)
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        _content = (
            msg["content"]
            if msg["role"] != "assistant"
            else _sanitize_agent_display(msg["content"], _dbg)
        )
        st.markdown(_content)
        if msg.get("image"):
            import base64 as _b64

            st.image(_b64.b64decode(msg["image"]), width=300)

# ============================================================
# 一键健康分析：计划确认表单
# ============================================================
if st.session_state.get("_show_health_plan_form", False):
    subtasks = _load_subtasks_from_sop()
    with st.container(border=True):
        st.markdown("### 📋 健康分析计划确认")
        st.caption(
            "请确认分析范围后点击执行。列表来自系统配置；"
            "若要把**新 App/新流程**加进本列表，请用侧栏「➕ 将本轮对话加入一键健康分析」。"
        )

        time_window = st.number_input(
            "分析时间范围（天）",
            min_value=1,
            max_value=30,
            value=st.session_state.get("_health_plan_days", 3),
            step=1,
            key="_health_plan_days_input",
        )
        st.markdown("---")
        st.markdown("**选择分析子任务：**")
        selected_ids = []
        for task in subtasks:
            checked = st.checkbox(
                f"**{task['name']}**  \n{task.get('description', '')}",
                value=task.get("enabled_by_default", True),
                key=f"_health_task_{task['id']}",
            )
            if checked:
                selected_ids.append(task["id"])

        col_run, col_cancel = st.columns([1, 1])
        with col_run:
            run_clicked = st.button(
                "✅ 确认执行",
                type="primary",
                disabled=(len(selected_ids) == 0),
                use_container_width=True,
            )
        with col_cancel:
            if st.button("❌ 取消", use_container_width=True):
                st.session_state["_show_health_plan_form"] = False
                st.rerun()

        if len(selected_ids) == 0:
            st.warning("请至少勾选一个子任务")

        if run_clicked and selected_ids:
            st.session_state["_show_health_plan_form"] = False
            _prompt = och.build_one_click_analysis_prompt(
                int(time_window), selected_ids
            )
            _task_names = [t["name"] for t in subtasks if t["id"] in selected_ids]
            _display = f"🏥 **一键健康分析** — 最近{int(time_window)}天\n" + "\n".join(
                f"  - {n}" for n in _task_names
            )
            st.session_state.messages.append({"role": "user", "content": _display})
            st.session_state["_pending_health_prompt"] = _prompt
            st.session_state["_pending_health_display"] = _display
            st.rerun()

# 处理待执行的一键健康分析任务
if st.session_state.get("_pending_health_prompt"):
    _prompt = st.session_state.pop("_pending_health_prompt")
    _display = st.session_state.pop("_pending_health_display", "🏥 一键健康分析")
    with st.chat_message("user"):
        st.markdown(_display)
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        response = ""
        for response in agent_backend_stream(
            _prompt, image_base64=None, autonomous=False
        ):
            message_placeholder.markdown(
                _sanitize_agent_display(
                    response, st.session_state.get("show_agent_debug_output", True)
                )
                + "▌"
            )
        message_placeholder.markdown(
            _sanitize_agent_display(
                response, st.session_state.get("show_agent_debug_output", True)
            )
        )
    st.session_state.messages.append({"role": "assistant", "content": response})
    agent.last_task_time = time.time()

if st.session_state.get("_pending_registry_prompt"):
    _rp = st.session_state.pop("_pending_registry_prompt")
    _rdisp = "➕ **将本轮对话登记为一键健康分析子任务**（助手将判断是否为新场景并更新可选列表）"
    st.session_state.messages.append({"role": "user", "content": _rdisp})
    with st.chat_message("user"):
        st.markdown(_rdisp)
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        response = ""
        for response in agent_backend_stream(
            _rp,
            image_base64=None,
            autonomous=False,
            one_click_registry_update=True,
            task_enable_long_term_memory=False,
        ):
            message_placeholder.markdown(
                _sanitize_agent_display(
                    response, st.session_state.get("show_agent_debug_output", True)
                )
                + "▌"
            )
        message_placeholder.markdown(
            _sanitize_agent_display(
                response, st.session_state.get("show_agent_debug_output", True)
            )
        )
    st.session_state.messages.append({"role": "assistant", "content": response})
    agent.last_task_time = time.time()

uploaded_file = st.file_uploader(
    "📎 上传图片（医学影像、检查报告、皮肤照片等）",
    type=["png", "jpg", "jpeg", "webp", "gif"],
    key="img_upload",
)
user_image_b64 = None
if uploaded_file is not None:
    import base64 as _b64

    raw_bytes = uploaded_file.read()
    user_image_b64 = _b64.b64encode(raw_bytes).decode("utf-8")
    st.image(raw_bytes, caption=f"已上传: {uploaded_file.name}", width=300)

manual_auto = st.session_state.pop("_manual_auto_learn", False)
prompt = st.chat_input("请输入指令（可同时上传图片）")

if manual_auto:
    prompt = _generate_autonomous_prompt_standalone()
    display_label = "🤖 [手动触发] 自主学习已启动"
    _is_autonomous = True
    user_image_b64 = None
elif prompt:
    display_label = prompt
    _is_autonomous = False
else:
    display_label = None
    _is_autonomous = False

if display_label and prompt:
    user_msg = {"role": "user", "content": display_label}
    if user_image_b64:
        user_msg["image"] = user_image_b64
    st.session_state.messages.append(user_msg)
    with st.chat_message("user"):
        st.markdown(display_label)
        if user_image_b64:
            import base64 as _b64

            st.image(_b64.b64decode(user_image_b64), width=300)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        response = ""
        for response in agent_backend_stream(
            prompt, image_base64=user_image_b64, autonomous=_is_autonomous
        ):
            message_placeholder.markdown(
                _sanitize_agent_display(
                    response, st.session_state.get("show_agent_debug_output", True)
                )
                + "▌"
            )
        message_placeholder.markdown(
            _sanitize_agent_display(
                response, st.session_state.get("show_agent_debug_output", True)
            )
        )
    st.session_state.messages.append({"role": "assistant", "content": response})
    agent.last_task_time = time.time()
