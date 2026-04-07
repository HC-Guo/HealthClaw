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
from i18n_stapp import (
    DEFAULT_LOCALE,
    autonomous_prompt_for_locale,
    build_autonomous_hints,
    format_suggested_direction_line,
    get_text,
    page_title_for_locale,
    pick_suggested_direction_id,
    subtask_display_name_desc,
)

if "ui_locale" not in st.session_state:
    st.session_state.ui_locale = DEFAULT_LOCALE

st.set_page_config(
    page_title=page_title_for_locale(st.session_state.ui_locale), layout="wide"
)


def _loc() -> str:
    return st.session_state.get("ui_locale", DEFAULT_LOCALE)


def t(key: str, **kwargs) -> str:
    return get_text(_loc(), key, **kwargs)


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
    loc = _loc()
    msgs = st.session_state.get("messages") or []
    if not msgs:
        return get_text(loc, "registry_ctx_empty")
    chunks = []
    for m in msgs[-max_msgs:]:
        role = m.get("role", "?")
        content = (m.get("content") or "").strip()
        if not content:
            continue
        if len(content) > 800:
            content = content[:800] + get_text(loc, "registry_ctx_truncated")
        chunks.append(f"[{role}]\n{content}")
    text = "\n\n---\n\n".join(chunks)
    if len(text) > max_chars:
        text = get_text(loc, "registry_ctx_omitted") + text[-max_chars:]
    return text


def _generate_autonomous_prompt_standalone(agent=None):
    """智能生成自主学习任务提示：基于知识空白+低置信度+轮换策略选择学习方向"""
    loc = getattr(agent, "ui_locale", None) or DEFAULT_LOCALE
    base = os.path.dirname(__file__)

    sop_dir = os.path.join(base, "memory", "L3_sops")
    existing_sops = set()
    if os.path.isdir(sop_dir):
        existing_sops = {f for f in os.listdir(sop_dir) if f.endswith(".md")}

    strategy_low_conf = []
    strategy_path = os.path.join(base, "memory", "L4_episodes", "disease_strategy.json")
    if os.path.exists(strategy_path):
        try:
            with open(strategy_path, "r", encoding="utf-8") as f:
                strategy = json.load(f)
            strategy_low_conf = [
                d for d, s in strategy.items() if s.get("avg_confidence", 1) < 0.6
            ]
        except Exception:
            pass

    recent_topics = []
    history_path = os.path.join(base, "temp", "autonomous_reports", "history.txt")
    if os.path.exists(history_path):
        try:
            with open(history_path, "r", encoding="utf-8") as f:
                recent_topics = [l.strip() for l in f.readlines()[-10:] if l.strip()]
        except Exception:
            pass

    hints = build_autonomous_hints(
        loc, base, existing_sops, strategy_low_conf, recent_topics
    )
    suggested_id = pick_suggested_direction_id(recent_topics, loc)
    hints.append(format_suggested_direction_line(loc, suggested_id))
    return autonomous_prompt_for_locale(loc, hints)


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
                prompt = _generate_autonomous_prompt_standalone(agent)
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
        st.error(get_text(st.session_state.get("ui_locale", DEFAULT_LOCALE), "err_no_llm"))
        st.stop()
    else:
        threading.Thread(target=agent.run, daemon=True).start()
        threading.Thread(
            target=_auto_explore_daemon, args=(agent,), daemon=True, name="auto-explore"
        ).start()
    return agent


agent = init()
agent.ui_locale = st.session_state.get("ui_locale", DEFAULT_LOCALE)

st.title(t("main_title"))
st.caption(t("main_caption"))
if not st.session_state.messages and not st.session_state.get(
    "_show_health_plan_form", False
):
    st.info(t("welcome_info"))


@st.fragment
def render_sidebar():
    cur_loc = st.session_state.get("ui_locale", DEFAULT_LOCALE)
    lang = st.selectbox(
        t("sidebar_language"),
        ["zh", "en"],
        index=0 if cur_loc == "zh" else 1,
        format_func=lambda x: "中文" if x == "zh" else "English",
        key="_stapp_locale_select",
    )
    if lang != st.session_state.get("ui_locale", DEFAULT_LOCALE):
        st.session_state.ui_locale = lang
        agent.ui_locale = lang
        st.rerun()

    st.divider()

    # === 1. Agent 状态与基础控制 ===
    st.subheader(t("sidebar_agent"))
    current_idx = agent.llm_no
    st.caption(
        f"LLM Core: {current_idx}: {agent.get_llm_name()}",
        help=t("llm_caption_help"),
    )
    idle_secs = int(time.time() - agent.last_task_time)
    status = (
        t("status_running")
        if agent.is_running
        else t("status_idle", secs=idle_secs)
    )
    st.caption(t("status_label", status=status))

    if st.button(t("btn_switch_llm")):
        agent.next_llm()
        st.rerun(scope="fragment")

    if "show_agent_debug_output" not in st.session_state:
        st.session_state["show_agent_debug_output"] = True
    with st.expander(t("expander_advanced"), expanded=False):
        if st.button(t("btn_abort")):
            agent.abort()
            st.toast(t("toast_abort"))
            st.rerun()
        if st.button(t("btn_reinject")):
            agent.llmclient.last_tools = ""
            st.toast(t("toast_reinject"))
        st.toggle(
            t("toggle_debug"),
            key="show_agent_debug_output",
            help=t("toggle_debug_help"),
        )

    st.divider()

    # === 2. 记忆策略设置 ===
    st.subheader(t("sidebar_memory"), help=t("sidebar_memory_help"))
    # 使用 session_state 作为单一真值来源，避免 widget 与 agent 属性在 rerun 时互相覆盖导致的闪烁。
    # 仅在第一次访问该会话时，从 agent 读取默认值。
    if "long_term_memory_enabled" not in st.session_state:
        st.session_state["long_term_memory_enabled"] = getattr(
            agent, "enable_long_term_memory", True
        )
    st.toggle(
        t("toggle_ltm"),
        key="long_term_memory_enabled",
        help=t("toggle_ltm_help"),
    )
    agent.enable_long_term_memory = st.session_state["long_term_memory_enabled"]
    if st.session_state["long_term_memory_enabled"]:
        st.caption(t("caption_ltm_on"))
    else:
        st.caption(t("caption_ltm_off"))

    st.divider()

    # === 3. 自主探索模式 ===
    st.subheader(t("sidebar_auto"), help=t("sidebar_auto_help"))
    if "auto_explore_enabled" not in st.session_state:
        st.session_state["auto_explore_enabled"] = agent.auto_explore_enabled
    st.toggle(
        t("toggle_auto"),
        key="auto_explore_enabled",
        help=t("toggle_auto_help"),
    )
    agent.auto_explore_enabled = st.session_state["auto_explore_enabled"]
    if not st.session_state["auto_explore_enabled"]:
        agent.autonomous_mode = False

    if st.session_state["auto_explore_enabled"]:
        st.caption(t("caption_auto_on", threshold=IDLE_THRESHOLD))
        st.caption(t("caption_auto_idle", idle=idle_secs, threshold=IDLE_THRESHOLD))

        auto_count = len(getattr(agent, "_auto_results", []))
        if auto_count:
            st.caption(t("caption_auto_count", count=auto_count))

        if st.button(t("btn_auto_now"), type="primary"):
            agent.autonomous_mode = True
            st.session_state["_manual_auto_learn"] = True
            st.rerun()
    else:
        st.caption(t("caption_auto_off"))

    # 自主学习记录统一放在底部
    if getattr(agent, "_auto_results", []):
        with st.expander(t("expander_auto_log", n=len(agent._auto_results))):
            for r in reversed(agent._auto_results[-5:]):
                st.markdown(f"**{r['time']}**")
                st.text(
                    r["response"][:300] + ("..." if len(r["response"]) > 300 else "")
                )
                st.divider()

    st.divider()

    # === 4. 一键健康分析 ===
    st.subheader(t("sidebar_one_click"))
    st.caption(t("sidebar_one_click_cap"))
    if st.button(t("btn_one_click_start"), type="primary", use_container_width=True):
        st.session_state["_show_health_plan_form"] = True
        st.rerun()
    st.caption(t("caption_registry_hint"))
    if st.button(
        t("btn_add_registry"),
        use_container_width=True,
        help=t("btn_add_registry_help"),
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
    _hl = _loc()
    with st.container(border=True):
        st.markdown(t("health_plan_title"))
        st.caption(t("health_plan_caption"))

        time_window = st.number_input(
            t("health_plan_days"),
            min_value=1,
            max_value=30,
            value=st.session_state.get("_health_plan_days", 3),
            step=1,
            key="_health_plan_days_input",
        )
        st.markdown("---")
        st.markdown(t("health_plan_pick"))
        selected_ids = []
        for task in subtasks:
            _tn, _td = subtask_display_name_desc(task, _hl)
            checked = st.checkbox(
                f"**{_tn}**  \n{_td}",
                value=task.get("enabled_by_default", True),
                key=f"_health_task_{task['id']}",
            )
            if checked:
                selected_ids.append(task["id"])

        col_run, col_cancel = st.columns([1, 1])
        with col_run:
            run_clicked = st.button(
                t("btn_confirm"),
                type="primary",
                disabled=(len(selected_ids) == 0),
                use_container_width=True,
            )
        with col_cancel:
            if st.button(t("btn_cancel"), use_container_width=True):
                st.session_state["_show_health_plan_form"] = False
                st.rerun()

        if len(selected_ids) == 0:
            st.warning(t("warn_pick_one"))

        if run_clicked and selected_ids:
            st.session_state["_show_health_plan_form"] = False
            _prompt = och.build_one_click_analysis_prompt(
                int(time_window), selected_ids
            )
            _task_names = [
                subtask_display_name_desc(row, _hl)[0]
                for row in subtasks
                if row["id"] in selected_ids
            ]
            _display = t("one_click_user_header", days=int(time_window)) + "\n".join(
                f"  - {n}" for n in _task_names
            )
            st.session_state.messages.append({"role": "user", "content": _display})
            st.session_state["_pending_health_prompt"] = _prompt
            st.session_state["_pending_health_display"] = _display
            st.rerun()

# 处理待执行的一键健康分析任务
if st.session_state.get("_pending_health_prompt"):
    _prompt = st.session_state.pop("_pending_health_prompt")
    _display = st.session_state.pop(
        "_pending_health_display", t("one_click_fallback_display")
    )
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
    _rdisp = t("registry_user_msg")
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
    t("file_upload_label"),
    type=["png", "jpg", "jpeg", "webp", "gif"],
    key="img_upload",
)
user_image_b64 = None
if uploaded_file is not None:
    import base64 as _b64

    raw_bytes = uploaded_file.read()
    user_image_b64 = _b64.b64encode(raw_bytes).decode("utf-8")
    st.image(raw_bytes, caption=t("upload_caption", name=uploaded_file.name), width=300)

manual_auto = st.session_state.pop("_manual_auto_learn", False)
prompt = st.chat_input(t("chat_input_placeholder"))

if manual_auto:
    prompt = _generate_autonomous_prompt_standalone(agent)
    display_label = t("manual_auto_display")
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
