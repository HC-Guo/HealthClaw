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
from PIL import Image
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
DEFAULT_REQUEST_EN = "I want to lose weight. Give me a meal plan for the next month. Lunch at 12:00, dinner at 18:30."
DEFAULT_MEAL = "lunch"
TARGET_OPEN_ID = str((getattr(mykey, "fs_external_alert_targets", {}) or {}).get("child_01", "") or "")

UI_TEXT = {
    "zh": {
        "title": "HealthClaw饮食计划与推荐演示",
        "caption": "这套 demo 会实际走：饮食计划生成 -> 真机美团搜索 -> 候选餐推荐 -> 尝试加入购物车 -> 飞书推送。",
        "section_env": "1. 环境检查",
        "check_phone": "检查手机链路",
        "start_fsapp": "启动飞书服务",
        "stop_fsapp": "停止飞书服务",
        "reset_demo": "重置 demo 数据",
        "phone_status": "**手机状态**",
        "target_open_id": "**飞书目标 open_id**",
        "push_target": "推送目标 open_id",
        "fsapp_status": "**fsapp 启动结果**",
        "section_plan": "2. 生成饮食计划",
        "request_label": "需求描述",
        "generate_plan": "生成月度饮食计划",
        "plan_summary": "**计划摘要**",
        "plan_preview": "**计划 JSON 预览**",
        "plan_empty": "先在这里生成一条月度饮食计划。",
        "section_live": "3. 执行真实推荐",
        "choose_meal": "选择本餐",
        "query_override": "手机美团搜索词覆盖",
        "query_override_help": "如果你想演示更稳定的真机结果，可以在这里手动指定搜索词。",
        "progress_title": "**实时执行过程**",
        "run_flow": "执行本餐推荐流程",
        "push_to_feishu": "将本餐推荐推送到飞书",
        "need_plan": "请先生成饮食计划。",
        "need_push": "请先执行本餐推荐流程。",
        "fallback_error": "当前 demo 发生了回退，这不符合“全真实链路”要求。请重新执行并排查手机链路。",
        "live_warning": "真实链路未完全打通：{status} / {message}",
        "push_preview": "**最终推送文案预览**",
        "live_json": "**执行结果 JSON**",
        "feishu_sent": "已发送飞书测试消息: {message_id}",
        "llm_process": "**LLM 执行过程**",
        "llm_error": "LLM 调用失败: {error}",
        "llm_empty": "LLM 返回为空。",
        "llm_model": "模型: {model}",
        "llm_input": "查看发给 LLM 的输入",
        "llm_output": "查看 LLM 输出",
        "empty_output": "(empty output)",
        "result_empty": "点“执行本餐推荐流程”后，这里会展示完整推荐结果。",
        "result_page": "搜索结果页",
        "merchant_page": "店铺页",
        "cart_page": "购物车/规格页",
        "no_image": "暂无截图",
        "demo_log": "Demo 日志",
        "fsapp_log": "fsapp 日志",
        "feishu_test_title": "**测试消息：饮食计划推荐流程演示**\n\n",
    },
    "en": {
        "title": "HealthClaw Meal-plan Recommendation Demo",
        "caption": "This demo walks through the real chain: meal-plan generation -> phone Meituan search -> candidate recommendations -> add-to-cart attempt -> Feishu push.",
        "section_env": "1. Environment Check",
        "check_phone": "Check phone chain",
        "start_fsapp": "Start Feishu service",
        "stop_fsapp": "Stop Feishu service",
        "reset_demo": "Reset demo data",
        "phone_status": "**Phone status**",
        "target_open_id": "**Feishu target open_id**",
        "push_target": "Push target open_id",
        "fsapp_status": "**fsapp start result**",
        "section_plan": "2. Generate Meal Plan",
        "request_label": "Request",
        "generate_plan": "Generate monthly meal plan",
        "plan_summary": "**Plan summary**",
        "plan_preview": "**Plan JSON preview**",
        "plan_empty": "Generate a monthly meal plan here first.",
        "section_live": "3. Run Live Recommendation",
        "choose_meal": "Choose meal",
        "query_override": "Phone Meituan query override",
        "query_override_help": "For a more stable live-phone demo, you can manually set the Meituan query here.",
        "progress_title": "**Live execution log**",
        "run_flow": "Run this meal flow",
        "push_to_feishu": "Push this meal result to Feishu",
        "need_plan": "Generate a meal plan first.",
        "need_push": "Run the meal flow first.",
        "fallback_error": "The demo fell back to local data, which breaks the fully live-chain requirement. Please retry and check the phone chain.",
        "live_warning": "The live chain is not fully connected yet: {status} / {message}",
        "push_preview": "**Final push preview**",
        "live_json": "**Execution result JSON**",
        "feishu_sent": "Feishu test message sent: {message_id}",
        "llm_process": "**LLM execution details**",
        "llm_error": "LLM call failed: {error}",
        "llm_empty": "LLM returned an empty response.",
        "llm_model": "Model: {model}",
        "llm_input": "View LLM input",
        "llm_output": "View LLM output",
        "empty_output": "(empty output)",
        "result_empty": "Run the meal flow and the full result will appear here.",
        "result_page": "Search results page",
        "merchant_page": "Merchant page",
        "cart_page": "Cart / spec page",
        "no_image": "No screenshot yet",
        "demo_log": "Demo log",
        "fsapp_log": "fsapp log",
        "feishu_test_title": "**Test message: meal-plan recommendation demo**\n\n",
    },
}


def _strip_protocol_tags(text):
    if not text:
        return ""
    for tag in ("thinking", "summary", "tool_use", "tool_result", "file_content"):
        text = re.sub(rf"<{tag}>.*?</{tag}>", "", text, flags=re.DOTALL)
    text = re.sub(r"^```(?:markdown|md|text|json)?\s*", "", text.strip(), flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text.strip())
    return text.strip()


def _normalize_locale(locale):
    return "en" if str(locale or "").strip().lower().startswith("en") else "zh"


def _meal_label_display(meal_key, locale):
    labels = {
        "zh": {"breakfast": "早餐", "lunch": "午餐", "dinner": "晚餐"},
        "en": {"breakfast": "Breakfast", "lunch": "Lunch", "dinner": "Dinner"},
    }
    loc = _normalize_locale(locale)
    return labels[loc].get(meal_key, meal_key)


def _localized_plan_preview(plan, locale):
    loc = _normalize_locale(locale)
    preview_schedule = {}
    for meal_key in ["breakfast", "lunch", "dinner"]:
        schedule = copy.deepcopy(plan["meal_schedule"][meal_key])
        schedule["label"] = schedule.get("label_en") if loc == "en" else schedule.get("label")
        preview_schedule[meal_key] = schedule

    day_preview = copy.deepcopy(plan["days"][0])
    if loc == "en":
        day_preview["theme"] = day_preview.get("theme_en") or day_preview.get("theme")
        for meal in day_preview.get("meals", {}).values():
            meal["meal_label"] = meal.get("meal_label_en") or meal.get("meal_label")
            meal["goal_note"] = meal.get("goal_note_en") or meal.get("goal_note")
            meal["query"] = meal.get("query_en_display") or meal.get("query")

    return {
        "goal": plan.get("goal_label_en") if loc == "en" else plan.get("goal_label"),
        "start_date": plan["start_date"],
        "meal_schedule": preview_schedule,
        "day_1": day_preview,
    }


def build_meal_demo_prompt(plan, push, live, locale="zh"):
    loc = _normalize_locale(locale)
    plan_summary = {
        "goal_label": plan.get("goal_label_en", "") if loc == "en" else plan.get("goal_label", ""),
        "summary": plan.get("summary_en", "") if loc == "en" else plan.get("summary", ""),
        "meal_time": push.get("meal_time", ""),
        "meal_label": push.get("meal_label_en", "") if loc == "en" else push.get("meal_label", ""),
        "day_theme": (push.get("day_plan") or {}).get("theme_en", "") if loc == "en" else (push.get("day_plan") or {}).get("theme", ""),
        "meal_spec": {
            **(push.get("meal_spec") or {}),
            "meal_label": (push.get("meal_spec") or {}).get("meal_label_en") if loc == "en" else (push.get("meal_spec") or {}).get("meal_label"),
            "goal_note": (push.get("meal_spec") or {}).get("goal_note_en") if loc == "en" else (push.get("meal_spec") or {}).get("goal_note"),
            "query": (push.get("meal_spec") or {}).get("query_en_display") if loc == "en" else (push.get("meal_spec") or {}).get("query"),
        },
        "display_candidates": [
            {
                **item,
                "reason": item.get("reason_en") if loc == "en" else item.get("reason"),
            }
            for item in (push.get("display_candidates") or [])
        ],
        "cart_action": push.get("cart_action", {}),
        "live_status": live.get("live_status", ""),
        "live_message": live.get("live_message", ""),
        "fallback_used": live.get("fallback_used", False),
    }
    if loc == "en":
        return (
            "You are the HealthClaw meal recommendation explainer. "
            "Based on the real execution result below, explain why this breakfast, lunch, or dinner recommendation was chosen. "
            "Do not invent Meituan results that were not actually observed, and do not claim payment has already happened.\n\n"
            "Output requirements:\n"
            "1. Use English.\n"
            "2. Output Markdown.\n"
            "3. You must include these headings:\n"
            "**LLM Summary**\n"
            "**Why These Candidates Were Recommended**\n"
            "**Where The Real Chain Stopped**\n"
            "**What To Do Next**\n"
            "4. If add-to-cart failed, clearly say which step failed.\n"
            "5. If an item was added to cart, clearly state that payment has not happened yet and still requires manual payment.\n\n"
            "Input data:\n"
            f"```json\n{json.dumps(plan_summary, ensure_ascii=False, indent=2)}\n```"
        )
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


def explain_meal_demo(plan, push, live, locale="zh", llm_ask=None):
    prompt = build_meal_demo_prompt(plan, push, live, locale=locale)
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


def _prepare_feishu_upload_image(image_path):
    src = Path(image_path)
    prepared = TEMP_DIR / f"{src.stem}_feishu.jpg"
    with Image.open(src) as image:
        normalized = image.convert("RGB")
        normalized.save(prepared, format="JPEG", quality=92, optimize=True)
    return str(prepared)


def upload_feishu_image(image_path):
    client = create_feishu_client()
    prepared_path = _prepare_feishu_upload_image(image_path)
    with open(prepared_path, "rb") as image_file:
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


def send_feishu_demo_bundle(open_id, content, artifacts, locale="zh"):
    labels = (
        [("搜索结果页截图", artifacts.get("result_screenshot", "")), ("店铺页截图", artifacts.get("merchant_screenshot", "")), ("购物车页截图", artifacts.get("cart_screenshot", ""))]
        if _normalize_locale(locale) != "en"
        else [("Search results screenshot", artifacts.get("result_screenshot", "")), ("Merchant page screenshot", artifacts.get("merchant_screenshot", "")), ("Cart page screenshot", artifacts.get("cart_screenshot", ""))]
    )
    message_ids = {"main": send_feishu_card(open_id, content), "images": []}
    for label, path in labels:
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
        "meal_label_en": aligned_plan["meal_schedule"][meal_key].get("label_en", ""),
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


def append_progress(logs, message, placeholder=None, locale="zh"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    logs.append(f"[{timestamp}] {message}")
    st.session_state["demo_progress_log"] = logs
    if placeholder is not None:
        placeholder.markdown(
            (UI_TEXT[_normalize_locale(locale)]["progress_title"] + "\n\n" + "\n".join(f"- {item}" for item in logs))
        )


st.set_page_config(page_title="HealthClaw Meal Demo", layout="wide")

if "meal_demo_locale" not in st.session_state:
    st.session_state["meal_demo_locale"] = "zh"
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

locale = st.selectbox(
    "Language / 语言",
    ["zh", "en"],
    index=0 if st.session_state.get("meal_demo_locale", "zh") == "zh" else 1,
    format_func=lambda value: "中文" if value == "zh" else "English",
)
st.session_state["meal_demo_locale"] = locale


def t(key, **kwargs):
    text = UI_TEXT[locale][key]
    return text.format(**kwargs) if kwargs else text


st.title(t("title"))
st.caption(t("caption"))

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader(t("section_env"))
    adb_socket = st.text_input("ADB_SERVER_SOCKET", value=DEFAULT_ADB_SOCKET)
    ensure_runtime_env(adb_socket)
    if st.button(t("check_phone"), use_container_width=True):
        st.session_state["phone_status"] = phone_status(adb_socket)
    if st.button(t("start_fsapp"), use_container_width=True):
        st.session_state["fsapp_status"] = start_fsapp(adb_socket)
    if st.button(t("stop_fsapp"), use_container_width=True):
        st.session_state["fsapp_stop"] = {"stopped": stop_process(DEMO_FSAPP_PID)}
    if st.button(t("reset_demo"), use_container_width=True):
        reset_demo_user_data()
        st.session_state["demo_plan"] = None
        st.session_state["demo_push"] = None
        st.session_state["demo_live"] = None
        st.session_state["demo_message_id"] = ""
        st.session_state["demo_message_bundle"] = None
        st.session_state["demo_llm_debug"] = None
        st.session_state["demo_progress_log"] = []

    st.markdown(t("phone_status"))
    st.json(st.session_state.get("phone_status", phone_status(adb_socket)))
    st.markdown(t("target_open_id"))
    open_id = st.text_input(t("push_target"), value=TARGET_OPEN_ID)
    st.markdown(t("fsapp_status"))
    st.json(st.session_state.get("fsapp_status", {"status": "idle"}))

with col2:
    st.subheader(t("section_plan"))
    request_text = st.text_area(
        t("request_label"),
        value=DEFAULT_REQUEST if locale == "zh" else DEFAULT_REQUEST_EN,
        height=120,
        key=f"meal_request_{locale}",
    )
    if st.button(t("generate_plan"), type="primary", use_container_width=True):
        service = get_demo_service()
        plan = service.create_plan(open_id or "meal_demo_user", request_text)["plan"]
        st.session_state["demo_plan"] = plan
        log_demo(f"已生成 demo 饮食计划，goal={plan['goal']}, open_id={plan['open_id']}")

    if st.session_state.get("demo_plan"):
        service = get_demo_service()
        plan = st.session_state["demo_plan"]
        st.markdown(t("plan_summary"))
        st.markdown(service.format_plan_created_message(plan, locale=locale))
        st.markdown(t("plan_preview"))
        st.json(_localized_plan_preview(plan, locale))
    else:
        st.info(t("plan_empty"))

with col3:
    st.subheader(t("section_live"))
    meal_key = st.selectbox(
        t("choose_meal"),
        ["breakfast", "lunch", "dinner"],
        index=["breakfast", "lunch", "dinner"].index(DEFAULT_MEAL),
        format_func=lambda key: _meal_label_display(key, locale),
    )
    query_override = st.text_input(
        t("query_override"),
        value="鸡胸肉蔬菜沙拉" if meal_key == "lunch" else "",
        help=t("query_override_help"),
        key=f"meal_query_override_{locale}_{meal_key}",
    )
    progress_placeholder = st.empty()
    if st.session_state.get("demo_progress_log"):
        progress_placeholder.markdown(
            t("progress_title") + "\n\n" + "\n".join(f"- {item}" for item in st.session_state["demo_progress_log"])
        )
    if st.button(t("run_flow"), type="primary", use_container_width=True):
        if not st.session_state.get("demo_plan"):
            st.warning(t("need_plan"))
        else:
            logs = []
            service = get_demo_service()
            append_progress(logs, f"开始执行{_meal_label_display(meal_key, locale)}推荐流程" if locale == "zh" else f"Starting the {_meal_label_display(meal_key, locale)} recommendation flow", progress_placeholder, locale=locale)
            append_progress(logs, "正在对齐今日计划与演示时间" if locale == "zh" else "Aligning the plan with today's demo time", progress_placeholder, locale=locale)
            aligned_plan = align_plan_for_demo(st.session_state["demo_plan"], meal_key, query_override=query_override)
            append_progress(logs, "正在重置美团 App 状态" if locale == "zh" else "Resetting the Meituan app state", progress_placeholder, locale=locale)
            _run_adb("shell", "am", "force-stop", "com.sankuai.meituan", timeout=20)
            time.sleep(1)
            append_progress(logs, "正在执行真实手机美团链路（搜索 -> 结果页 -> 店铺页）" if locale == "zh" else "Running the real phone Meituan chain (search -> results -> merchant page)", progress_placeholder, locale=locale)
            live = service.prepare_live_meituan_push(
                aligned_plan,
                meal_key,
                target_date=datetime.now(),
                limit=3,
                allow_fallback=False,
            )
            append_progress(
                logs,
                (
                    f"真实链路返回：status={live.get('live_status', '') or live.get('status', '')} / fallback={live.get('fallback_used')}"
                    if locale == "zh"
                    else f"Live chain returned: status={live.get('live_status', '') or live.get('status', '')} / fallback={live.get('fallback_used')}"
                ),
                progress_placeholder,
                locale=locale,
            )
            append_progress(logs, "正在整理候选餐与推送文案" if locale == "zh" else "Formatting candidates and push copy", progress_placeholder, locale=locale)
            push = {
                "plan_id": aligned_plan["id"],
                "open_id": aligned_plan["open_id"],
                "date": time.strftime("%Y-%m-%d"),
                "meal_key": meal_key,
                "meal_label": aligned_plan["meal_schedule"][meal_key]["label"],
                "meal_label_en": aligned_plan["meal_schedule"][meal_key].get("label_en", ""),
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
            append_progress(logs, "正在调用 LLM 解释推荐结果" if locale == "zh" else "Calling the LLM to explain the recommendation", progress_placeholder, locale=locale)
            st.session_state["demo_llm_debug"] = explain_meal_demo(aligned_plan, push, live, locale=locale)
            llm_debug = st.session_state["demo_llm_debug"]
            append_progress(
                logs,
                (
                    f"LLM 执行完成：status={llm_debug.get('status', '')} / model={llm_debug.get('model', '') or 'unknown'}"
                    if locale == "zh"
                    else f"LLM finished: status={llm_debug.get('status', '')} / model={llm_debug.get('model', '') or 'unknown'}"
                ),
                progress_placeholder,
                locale=locale,
            )
            append_progress(logs, "本餐推荐流程执行完成，下面展示最终结果" if locale == "zh" else "The meal flow is complete. Final results are shown below.", progress_placeholder, locale=locale)
            log_demo(
                f"已执行 {meal_key} 推荐流程，cart_action={live.get('cart_action', {}).get('status', '')}, "
                f"source={live.get('source', '')}, fallback_used={live.get('fallback_used')}, "
                f"live_status={live.get('live_status', '')}"
            )
    if st.button(t("push_to_feishu"), use_container_width=True):
        if not st.session_state.get("demo_push"):
            st.warning(t("need_push"))
        else:
            service = get_demo_service()
            push_message = service.format_push_message(st.session_state["demo_push"], locale=locale)
            content = t("feishu_test_title") + push_message
            message_bundle = send_feishu_demo_bundle(
                open_id,
                content,
                (st.session_state.get("demo_push") or {}).get("artifacts", {}),
                locale=locale,
            )
            st.session_state["demo_message_id"] = message_bundle["main"]
            st.session_state["demo_message_bundle"] = message_bundle
            log_demo(f"已发送 demo 飞书消息，message_id={message_bundle['main']}")

    if st.session_state.get("demo_push"):
        service = get_demo_service()
        live = st.session_state.get("demo_live", {})
        push_message = service.format_push_message(st.session_state["demo_push"], locale=locale)
        if live.get("fallback_used"):
            st.error(t("fallback_error"))
        elif live.get("live_status") not in {"success", "partial"}:
            st.warning(t("live_warning", status=live.get("live_status"), message=live.get("live_message", "")))
        st.markdown(t("push_preview"))
        st.markdown(push_message)
        st.markdown(t("live_json"))
        st.json(live)
        if st.session_state.get("demo_message_id"):
            st.success(t("feishu_sent", message_id=st.session_state["demo_message_id"]))
        if st.session_state.get("demo_message_bundle"):
            st.json(st.session_state["demo_message_bundle"])
        llm_debug = st.session_state.get("demo_llm_debug")
        if llm_debug:
            st.markdown(t("llm_process"))
            if llm_debug.get("status") == "error":
                st.warning(t("llm_error", error=llm_debug.get("error", "")))
            elif llm_debug.get("status") == "empty":
                st.warning(t("llm_empty"))
            else:
                st.caption(t("llm_model", model=llm_debug.get("model", "unknown")))
            with st.expander(t("llm_input"), expanded=False):
                st.code(llm_debug.get("prompt", ""), language="text")
            with st.expander(t("llm_output"), expanded=True):
                output = llm_debug.get("output", "")
                if output:
                    st.markdown(output)
                else:
                    st.code(t("empty_output"), language="text")
    else:
        st.info(t("result_empty"))

st.divider()
img_col1, img_col2, img_col3 = st.columns(3)
artifacts = (st.session_state.get("demo_push") or {}).get("artifacts", {})
with img_col1:
    st.subheader(t("result_page"))
    result_path = artifacts.get("result_screenshot", "")
    if result_path and Path(result_path).exists():
        st.image(result_path, caption=Path(result_path).name)
    else:
        st.caption(t("no_image"))
with img_col2:
    st.subheader(t("merchant_page"))
    merchant_path = artifacts.get("merchant_screenshot", "")
    if merchant_path and Path(merchant_path).exists():
        st.image(merchant_path, caption=Path(merchant_path).name)
    else:
        st.caption(t("no_image"))
with img_col3:
    st.subheader(t("cart_page"))
    cart_path = artifacts.get("cart_screenshot", "")
    if cart_path and Path(cart_path).exists():
        st.image(cart_path, caption=Path(cart_path).name)
    else:
        st.caption(t("no_image"))

st.divider()
left, right = st.columns(2)
with left:
    st.subheader(t("demo_log"))
    st.code(read_log_tail(DEMO_LOG), language="text")
with right:
    st.subheader(t("fsapp_log"))
    st.code(read_log_tail(DEMO_FSAPP_LOG), language="text")
