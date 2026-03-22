import copy
import json
import os
import importlib.util
import re
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import lark_oapi as lark
import streamlit as st
from lark_oapi.api.im.v1 import CreateMessageRequest, CreateMessageRequestBody
from lark_oapi.api.im.v1 import CreateImageRequest, CreateImageRequestBody

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from meal_plan_service import MealPlanService
from meal_plan_service import _run_adb
from tools.health_data_store import HealthDataStore
from tools.phone_control import check_connection


def _load_mykey_module():
    try:
        import mykey as local_mykey

        return local_mykey
    except ImportError:
        pass

    candidates = []
    explicit_path = str(os.environ.get("HEALTHCLAW_MYKEY_PATH", "") or "").strip()
    explicit_dir = str(os.environ.get("HEALTHCLAW_MYKEY_DIR", "") or "").strip()
    shared_home = str(os.environ.get("HEALTHCLAW_SHARED_HOME", "") or "").strip()
    repo_parent = str(PROJECT_ROOT.parent)

    if explicit_path:
        candidates.append(explicit_path)
    if explicit_dir:
        candidates.append(os.path.join(explicit_dir, "mykey.py"))
    if shared_home:
        candidates.append(os.path.join(shared_home, "mykey.py"))
    candidates.extend(
        [
            os.path.join(repo_parent, "openclaw", "mykey.py"),
            os.path.join(repo_parent, "healthclaw_shared", "mykey.py"),
        ]
    )

    for path in candidates:
        if not path or not os.path.exists(path):
            continue
        spec = importlib.util.spec_from_file_location("healthclaw_shared_mykey", path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
    raise RuntimeError("未找到 mykey.py，无法运行饮食计划 demo")


mykey = _load_mykey_module()


TEMP_DIR = PROJECT_ROOT / "temp"
TEMP_DIR.mkdir(exist_ok=True)

DEMO_USER_DATA_DIR = TEMP_DIR / "meal_demo_user_data"
DEMO_LOG = TEMP_DIR / "meal_demo.log"
DEMO_FSAPP_LOG = TEMP_DIR / "demo_fsapp.log"
DEMO_FSAPP_PID = TEMP_DIR / "demo_fsapp.pid"

DEFAULT_ADB_SOCKET = os.environ.get("ADB_SERVER_SOCKET", "tcp:127.0.0.1:15038")
DEFAULT_REQUEST = "我想减肥，给我未来一个月的用餐计划，中午12点吃饭，晚饭18点半。"
DEFAULT_MEAL = "lunch"
TARGET_OPEN_ID = str((getattr(mykey, "fs_external_alert_targets", {}) or {}).get("child_01", "") or "")


def _strip_protocol_tags(text):
    if not text:
        return ""
    for tag in ("thinking", "summary", "tool_use", "tool_result", "file_content"):
        text = re.sub(rf"<{tag}>.*?</{tag}>", "", text, flags=re.DOTALL)
    text = re.sub(r"^```(?:markdown|md|text|json)?\s*", "", text.strip(), flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text.strip())
    return text.strip()


def build_meal_demo_prompt(plan, push, live):
    plan_summary = {
        "goal_label": plan.get("goal_label", ""),
        "summary": plan.get("summary", ""),
        "meal_time": push.get("meal_time", ""),
        "meal_label": push.get("meal_label", ""),
        "day_theme": (push.get("day_plan") or {}).get("theme", ""),
        "meal_spec": push.get("meal_spec", {}),
        "display_candidates": push.get("display_candidates", []),
        "cart_action": push.get("cart_action", {}),
        "live_status": live.get("live_status", ""),
        "live_message": live.get("live_message", ""),
        "fallback_used": live.get("fallback_used", False),
    }
    return (
        "你是 HealthClaw 饮食推荐解释器。"
        "请根据以下真实执行结果，解释这次早餐/午餐/晚餐推荐为什么这样选。"
        "不要编造不存在的美团结果，不要声称已经支付。\n\n"
        "输出要求：\n"
        "1. 用简体中文。\n"
        "2. 输出 Markdown。\n"
        "3. 必须包含以下标题：\n"
        "**LLM判断摘要**\n"
        "**为什么推荐这些候选**\n"
        "**当前真实执行到哪一步**\n"
        "**下一步怎么做**\n"
        "4. 如果自动加购失败，要明确说明失败在哪一步。\n"
        "5. 如果已成功加入购物车，要明确说“还未支付，需要用户手动支付”。\n\n"
        "输入数据如下：\n"
        f"```json\n{json.dumps(plan_summary, ensure_ascii=False, indent=2)}\n```"
    )


def _default_llm_ask(prompt):
    from seda_main import _build_llm_sessions

    sessions = _build_llm_sessions()
    if not sessions:
        raise RuntimeError("no_llm_backend_configured")

    errors = []
    for session in sessions:
        model_name = f"{type(session).__name__}/{getattr(session, 'default_model', '?')}"
        try:
            text = session.ask(prompt, stream=False)
        except Exception as exc:
            errors.append(f"{model_name}: {exc}")
            continue
        text = _strip_protocol_tags(text)
        if text and not text.startswith("Error:"):
            return {"text": text, "model": model_name}
        errors.append(f"{model_name}: {text[:120] if text else 'empty_response'}")
    raise RuntimeError("; ".join(errors) or "all_llm_backends_failed")


def explain_meal_demo(plan, push, live, llm_ask=None):
    prompt = build_meal_demo_prompt(plan, push, live)
    ask = llm_ask or _default_llm_ask
    try:
        result = ask(prompt)
        if isinstance(result, dict):
            text = _strip_protocol_tags(result.get("text", ""))
            model = result.get("model", "")
        else:
            text = _strip_protocol_tags(str(result))
            model = ""
        return {
            "status": "ok" if text else "empty",
            "prompt": prompt,
            "output": text,
            "model": model,
        }
    except Exception as exc:
        return {
            "status": "error",
            "prompt": prompt,
            "output": "",
            "model": "",
            "error": str(exc),
        }


def log_demo(message):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(DEMO_LOG, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")


def read_log_tail(path, lines=40):
    if not path.exists():
        return "(no log yet)"
    text = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    if not text:
        return "(log empty)"
    return "\n".join(text[-lines:])


def ensure_runtime_env(adb_socket):
    os.environ["ADB_SERVER_SOCKET"] = adb_socket.strip() or DEFAULT_ADB_SOCKET
    os.environ["HEALTHCLAW_ENABLE_PHONE_MEITUAN"] = "1"


def get_demo_service(base_dir=None):
    base = str(base_dir or DEMO_USER_DATA_DIR)
    store = HealthDataStore(base_dir=base)
    return MealPlanService(store=store)


def reset_demo_user_data():
    if DEMO_USER_DATA_DIR.exists():
        for child in sorted(DEMO_USER_DATA_DIR.rglob("*"), reverse=True):
            if child.is_file():
                child.unlink()
            elif child.is_dir():
                try:
                    child.rmdir()
                except OSError:
                    pass
    DEMO_USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
    log_demo("已重置饮食计划 demo 用户数据目录")


def create_feishu_client():
    app_id = getattr(mykey, "fs_app_id", None)
    app_secret = getattr(mykey, "fs_app_secret", None)
    if not app_id or not app_secret:
        raise RuntimeError("mykey.py 中缺少飞书凭证")
    return lark.Client.builder().app_id(app_id).app_secret(app_secret).log_level(lark.LogLevel.INFO).build()


def send_feishu_card(open_id, content):
    client = create_feishu_client()
    body = CreateMessageRequest.builder().receive_id_type("open_id").request_body(
        CreateMessageRequestBody.builder()
        .receive_id(open_id)
        .msg_type("interactive")
        .content(
            json.dumps(
                {
                    "config": {"wide_screen_mode": True},
                    "elements": [{"tag": "markdown", "content": content}],
                },
                ensure_ascii=False,
            )
        )
        .build()
    ).build()
    result = client.im.v1.message.create(body)
    if not result.success():
        raise RuntimeError(f"飞书发送失败: {result.code}, {result.msg}")
    return result.data.message_id


def upload_feishu_image(image_path):
    client = create_feishu_client()
    with open(image_path, "rb") as image_file:
        body = CreateImageRequestBody.builder().image_type("message").image(image_file).build()
        req = CreateImageRequest.builder().request_body(body).build()
        result = client.im.v1.image.create(req)
    if not result.success():
        raise RuntimeError(f"飞书图片上传失败: {result.code}, {result.msg}")
    return result.data.image_key


def send_feishu_image(open_id, image_path):
    client = create_feishu_client()
    image_key = upload_feishu_image(image_path)
    body = CreateMessageRequest.builder().receive_id_type("open_id").request_body(
        CreateMessageRequestBody.builder()
        .receive_id(open_id)
        .msg_type("image")
        .content(json.dumps({"image_key": image_key}, ensure_ascii=False))
        .build()
    ).build()
    result = client.im.v1.message.create(body)
    if not result.success():
        raise RuntimeError(f"飞书图片发送失败: {result.code}, {result.msg}")
    return result.data.message_id


def send_feishu_demo_bundle(open_id, content, artifacts):
    message_ids = {"main": send_feishu_card(open_id, content), "images": []}
    for label, path in [
        ("搜索结果页截图", artifacts.get("result_screenshot", "")),
        ("店铺页截图", artifacts.get("merchant_screenshot", "")),
        ("购物车页截图", artifacts.get("cart_screenshot", "")),
    ]:
        if not path or not Path(path).exists():
            continue
        text_id = send_feishu_card(open_id, f"**{label}**")
        image_id = send_feishu_image(open_id, path)
        message_ids["images"].append({"label": label, "text": text_id, "image": image_id})
    return message_ids


def is_pid_alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def read_pid(path):
    try:
        return int(path.read_text(encoding="utf-8").strip())
    except Exception:
        return None


def stop_process(path):
    pid = read_pid(path)
    if not pid:
        return False
    if not is_pid_alive(pid):
        try:
            path.unlink()
        except FileNotFoundError:
            pass
        return False
    os.kill(pid, signal.SIGTERM)
    for _ in range(20):
        if not is_pid_alive(pid):
            try:
                path.unlink()
            except FileNotFoundError:
                pass
            return True
        time.sleep(0.2)
    return False


def start_fsapp(adb_socket):
    ensure_runtime_env(adb_socket)
    if DEMO_FSAPP_LOG.exists():
        DEMO_FSAPP_LOG.write_text("", encoding="utf-8")
    if DEMO_FSAPP_PID.exists():
        pid = read_pid(DEMO_FSAPP_PID)
        if pid and is_pid_alive(pid):
            return {"status": "already_running", "pid": pid}
    proc = subprocess.Popen(
        [sys.executable, "fsapp.py"],
        cwd=str(PROJECT_ROOT),
        stdout=open(DEMO_FSAPP_LOG, "ab"),
        stderr=subprocess.STDOUT,
        env=dict(os.environ),
    )
    DEMO_FSAPP_PID.write_text(str(proc.pid), encoding="utf-8")
    log_demo(f"已启动 fsapp.py，pid={proc.pid}，ADB_SERVER_SOCKET={os.environ.get('ADB_SERVER_SOCKET')}")
    time.sleep(3)
    return {"status": "started", "pid": proc.pid}


def align_plan_for_demo(plan, meal_key, query_override=""):
    aligned = copy.deepcopy(plan)
    today = time.strftime("%Y-%m-%d")
    aligned["start_date"] = today
    if aligned.get("days"):
        aligned["days"][0]["date"] = today
    if query_override.strip():
        aligned["days"][0]["meals"][meal_key]["phone_query"] = query_override.strip()
    return aligned


def build_demo_push(service, plan, meal_key, query_override=""):
    aligned_plan = align_plan_for_demo(plan, meal_key, query_override=query_override)
    live = service.prepare_live_meituan_push(
        aligned_plan,
        meal_key,
        target_date=datetime.now(),
        limit=3,
        allow_fallback=False,
    )
    push = {
        "plan_id": aligned_plan["id"],
        "open_id": aligned_plan["open_id"],
        "date": time.strftime("%Y-%m-%d"),
        "meal_key": meal_key,
        "meal_label": aligned_plan["meal_schedule"][meal_key]["label"],
        "meal_time": aligned_plan["meal_schedule"][meal_key]["meal_time"],
        "day_plan": aligned_plan["days"][0],
        "meal_spec": aligned_plan["days"][0]["meals"][meal_key],
        "display_candidates": live.get("display_candidates", []),
        "cart_action": live.get("cart_action", {}),
        "artifacts": live.get("artifacts", {}),
    }
    return aligned_plan, live, push


def phone_status(adb_socket):
    ensure_runtime_env(adb_socket)
    ok, info = check_connection()
    return {"connected": ok, "info": info, "adb_socket": os.environ.get("ADB_SERVER_SOCKET")}


def append_progress(logs, message, placeholder=None):
    timestamp = datetime.now().strftime("%H:%M:%S")
    logs.append(f"[{timestamp}] {message}")
    st.session_state["demo_progress_log"] = logs
    if placeholder is not None:
        placeholder.markdown(
            "**实时执行过程**\n\n" + "\n".join(f"- {item}" for item in logs)
        )


st.set_page_config(page_title="HealthClaw饮食计划演示", layout="wide")
st.title("HealthClaw饮食计划与推荐演示")
st.caption("这套 demo 会实际走：饮食计划生成 -> 真机美团搜索 -> 候选餐推荐 -> 尝试加入购物车 -> 飞书推送。")

if "demo_plan" not in st.session_state:
    st.session_state["demo_plan"] = None
if "demo_push" not in st.session_state:
    st.session_state["demo_push"] = None
if "demo_live" not in st.session_state:
    st.session_state["demo_live"] = None
if "demo_message_id" not in st.session_state:
    st.session_state["demo_message_id"] = ""
if "demo_message_bundle" not in st.session_state:
    st.session_state["demo_message_bundle"] = None
if "demo_llm_debug" not in st.session_state:
    st.session_state["demo_llm_debug"] = None
if "demo_progress_log" not in st.session_state:
    st.session_state["demo_progress_log"] = []

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("1. 环境检查")
    adb_socket = st.text_input("ADB_SERVER_SOCKET", value=DEFAULT_ADB_SOCKET)
    ensure_runtime_env(adb_socket)
    if st.button("检查手机链路", use_container_width=True):
        st.session_state["phone_status"] = phone_status(adb_socket)
    if st.button("启动飞书服务", use_container_width=True):
        st.session_state["fsapp_status"] = start_fsapp(adb_socket)
    if st.button("停止飞书服务", use_container_width=True):
        st.session_state["fsapp_stop"] = {"stopped": stop_process(DEMO_FSAPP_PID)}
    if st.button("重置 demo 数据", use_container_width=True):
        reset_demo_user_data()
        st.session_state["demo_plan"] = None
        st.session_state["demo_push"] = None
        st.session_state["demo_live"] = None
        st.session_state["demo_message_id"] = ""
        st.session_state["demo_progress_log"] = []

    st.markdown("**手机状态**")
    st.json(st.session_state.get("phone_status", phone_status(adb_socket)))
    st.markdown("**飞书目标 open_id**")
    open_id = st.text_input("推送目标 open_id", value=TARGET_OPEN_ID)
    st.markdown("**fsapp 启动结果**")
    st.json(st.session_state.get("fsapp_status", {"status": "idle"}))

with col2:
    st.subheader("2. 生成饮食计划")
    request_text = st.text_area("需求描述", value=DEFAULT_REQUEST, height=120)
    if st.button("生成月度饮食计划", type="primary", use_container_width=True):
        service = get_demo_service()
        plan = service.create_plan(open_id or "meal_demo_user", request_text)["plan"]
        st.session_state["demo_plan"] = plan
        st.session_state["demo_plan_message"] = service.format_plan_created_message(plan)
        log_demo(f"已生成 demo 饮食计划，goal={plan['goal']}, open_id={plan['open_id']}")

    if st.session_state.get("demo_plan"):
        plan = st.session_state["demo_plan"]
        st.markdown("**计划摘要**")
        st.markdown(st.session_state.get("demo_plan_message", ""))
        preview = {
            "goal": plan["goal_label"],
            "start_date": plan["start_date"],
            "meal_schedule": plan["meal_schedule"],
            "day_1": plan["days"][0],
        }
        st.markdown("**计划 JSON 预览**")
        st.json(preview)
    else:
        st.info("先在这里生成一条月度饮食计划。")

with col3:
    st.subheader("3. 执行真实推荐")
    meal_key = st.selectbox(
        "选择本餐",
        ["breakfast", "lunch", "dinner"],
        index=["breakfast", "lunch", "dinner"].index(DEFAULT_MEAL),
        format_func=lambda key: {"breakfast": "早餐", "lunch": "午餐", "dinner": "晚餐"}[key],
    )
    query_override = st.text_input(
        "手机美团搜索词覆盖",
        value="鸡胸肉蔬菜沙拉" if meal_key == "lunch" else "",
        help="如果你想演示更稳定的真机结果，可以在这里手动指定搜索词。",
    )
    progress_placeholder = st.empty()
    if st.session_state.get("demo_progress_log"):
        progress_placeholder.markdown(
            "**实时执行过程**\n\n" + "\n".join(f"- {item}" for item in st.session_state["demo_progress_log"])
        )
    if st.button("执行本餐推荐流程", type="primary", use_container_width=True):
        if not st.session_state.get("demo_plan"):
            st.warning("请先生成饮食计划。")
        else:
            logs = []
            append_progress(logs, f"开始执行{ {'breakfast':'早餐','lunch':'午餐','dinner':'晚餐'}[meal_key] }推荐流程", progress_placeholder)
            service = get_demo_service()
            append_progress(logs, "正在对齐今日计划与演示时间", progress_placeholder)
            aligned_plan = align_plan_for_demo(st.session_state["demo_plan"], meal_key, query_override=query_override)
            append_progress(logs, "正在重置美团 App 状态", progress_placeholder)
            _run_adb("shell", "am", "force-stop", "com.sankuai.meituan", timeout=20)
            time.sleep(1)
            append_progress(logs, "正在执行真实手机美团链路（搜索 -> 结果页 -> 店铺页）", progress_placeholder)
            live = service.prepare_live_meituan_push(
                aligned_plan,
                meal_key,
                target_date=datetime.now(),
                limit=3,
                allow_fallback=False,
            )
            append_progress(
                logs,
                f"真实链路返回：status={live.get('live_status', '') or live.get('status', '')} / fallback={live.get('fallback_used')}",
                progress_placeholder,
            )
            append_progress(logs, "正在整理候选餐与推送文案", progress_placeholder)
            push = {
                "plan_id": aligned_plan["id"],
                "open_id": aligned_plan["open_id"],
                "date": time.strftime("%Y-%m-%d"),
                "meal_key": meal_key,
                "meal_label": aligned_plan["meal_schedule"][meal_key]["label"],
                "meal_time": aligned_plan["meal_schedule"][meal_key]["meal_time"],
                "day_plan": aligned_plan["days"][0],
                "meal_spec": aligned_plan["days"][0]["meals"][meal_key],
                "display_candidates": live.get("display_candidates", []),
                "cart_action": live.get("cart_action", {}),
                "artifacts": live.get("artifacts", {}),
            }
            st.session_state["demo_plan"] = aligned_plan
            st.session_state["demo_live"] = live
            st.session_state["demo_push"] = push
            st.session_state["demo_push_message"] = service.format_push_message(push)
            append_progress(logs, "正在调用 LLM 解释推荐结果", progress_placeholder)
            st.session_state["demo_llm_debug"] = explain_meal_demo(aligned_plan, push, live)
            llm_debug = st.session_state["demo_llm_debug"]
            append_progress(
                logs,
                f"LLM 执行完成：status={llm_debug.get('status', '')} / model={llm_debug.get('model', '') or 'unknown'}",
                progress_placeholder,
            )
            append_progress(logs, "本餐推荐流程执行完成，下面展示最终结果", progress_placeholder)
            log_demo(
                f"已执行 {meal_key} 推荐流程，cart_action={live.get('cart_action', {}).get('status', '')}, "
                f"source={live.get('source', '')}, fallback_used={live.get('fallback_used')}, "
                f"live_status={live.get('live_status', '')}"
            )
    if st.button("将本餐推荐推送到飞书", use_container_width=True):
        if not st.session_state.get("demo_push"):
            st.warning("请先执行本餐推荐流程。")
        else:
            content = "**测试消息：饮食计划推荐流程演示**\n\n" + st.session_state.get("demo_push_message", "")
            message_bundle = send_feishu_demo_bundle(
                open_id,
                content,
                (st.session_state.get("demo_push") or {}).get("artifacts", {}),
            )
            st.session_state["demo_message_id"] = message_bundle["main"]
            st.session_state["demo_message_bundle"] = message_bundle
            log_demo(f"已发送 demo 飞书消息，message_id={message_bundle['main']}")

    if st.session_state.get("demo_push"):
        live = st.session_state.get("demo_live", {})
        if live.get("fallback_used"):
            st.error("当前 demo 发生了回退，这不符合“全真实链路”要求。请重新执行并排查手机链路。")
        elif live.get("live_status") not in {"success", "partial"}:
            st.warning(f"真实链路未完全打通：{live.get('live_status')} / {live.get('live_message', '')}")
        st.markdown("**最终推送文案预览**")
        st.markdown(st.session_state.get("demo_push_message", ""))
        st.markdown("**执行结果 JSON**")
        st.json(live)
        if st.session_state.get("demo_message_id"):
            st.success(f"已发送飞书测试消息: {st.session_state['demo_message_id']}")
        if st.session_state.get("demo_message_bundle"):
            st.json(st.session_state["demo_message_bundle"])
        llm_debug = st.session_state.get("demo_llm_debug")
        if llm_debug:
            st.markdown("**LLM 执行过程**")
            if llm_debug.get("status") == "error":
                st.warning(f"LLM 调用失败: {llm_debug.get('error', '')}")
            elif llm_debug.get("status") == "empty":
                st.warning("LLM 返回为空。")
            else:
                st.caption(f"模型: {llm_debug.get('model', 'unknown')}")
            with st.expander("查看发给 LLM 的输入", expanded=False):
                st.code(llm_debug.get("prompt", ""), language="text")
            with st.expander("查看 LLM 输出", expanded=True):
                output = llm_debug.get("output", "")
                if output:
                    st.markdown(output)
                else:
                    st.code("(empty output)", language="text")
    else:
        st.info("点“执行本餐推荐流程”后，这里会展示完整推荐结果。")

st.divider()
img_col1, img_col2, img_col3 = st.columns(3)
artifacts = (st.session_state.get("demo_push") or {}).get("artifacts", {})
with img_col1:
    st.subheader("搜索结果页")
    result_path = artifacts.get("result_screenshot", "")
    if result_path and Path(result_path).exists():
        st.image(result_path, caption=Path(result_path).name)
    else:
        st.caption("暂无截图")
with img_col2:
    st.subheader("店铺页")
    merchant_path = artifacts.get("merchant_screenshot", "")
    if merchant_path and Path(merchant_path).exists():
        st.image(merchant_path, caption=Path(merchant_path).name)
    else:
        st.caption("暂无截图")
with img_col3:
    st.subheader("购物车页")
    cart_path = artifacts.get("cart_screenshot", "")
    if cart_path and Path(cart_path).exists():
        st.image(cart_path, caption=Path(cart_path).name)
    else:
        st.caption("暂无截图")

st.divider()
left, right = st.columns(2)
with left:
    st.subheader("Demo 日志")
    st.code(read_log_tail(DEMO_LOG), language="text")
with right:
    st.subheader("fsapp 日志")
    st.code(read_log_tail(DEMO_FSAPP_LOG), language="text")
