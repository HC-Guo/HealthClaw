import json
import os
import importlib.util
import signal
import subprocess
import sys
import time
from pathlib import Path
import urllib.request

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from cross_device_node import build_demo_signal_payload, get_demo_signal_scenarios


def http_get_json(url, timeout=10):
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8")
        return {
            "status": "success",
            "http_status": resp.status,
            "response": json.loads(raw) if raw else {},
        }


def http_post_json(url, payload, token="", timeout=10):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["X-OpenClaw-Token"] = token
    req = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers=headers,
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8")
        return {
            "status": "success",
            "http_status": resp.status,
            "response": json.loads(raw) if raw else {},
        }


TEMP_DIR = PROJECT_ROOT / "temp"
TEMP_DIR.mkdir(exist_ok=True)

DEMO_BINDING_FILE = TEMP_DIR / "demo_bindings.json"
YOUNG_LOG = TEMP_DIR / "demo_fsapp.log"
ELDER_LOG = TEMP_DIR / "demo_elder.log"
YOUNG_PID = TEMP_DIR / "demo_fsapp.pid"
ELDER_PID = TEMP_DIR / "demo_elder.pid"

YOUNG_BASE = "http://127.0.0.1:8787"
ELDER_BASE = "http://127.0.0.1:8790"
DEMO_SIGNAL_SCENARIOS = get_demo_signal_scenarios()

UI_TEXT = {
    "zh": {
        "title": "HealthClaw跨设备演示",
        "section_start": "1. 节点启动",
        "start_young": "启动年轻人节点",
        "start_elder": "启动老人节点",
        "start_both": "一键启动两个节点",
        "stop_both": "停止两个节点",
        "reset_demo": "重置演示环境",
        "young_health": "**年轻人节点健康状态**",
        "elder_health": "**老人节点健康状态**",
        "section_binding": "2. 绑定关系",
        "binding_desc": "默认将老人节点 `elder_01` 与年轻人节点 `child_01` 建立通知关系。",
        "bind_default": "建立默认绑定",
        "refresh_bindings": "刷新绑定状态",
        "current_bindings": "**当前绑定**",
        "binding_read_error": "当前无法读取绑定: {error}",
        "section_signal": "3. 模拟可穿戴异常信号",
        "choose_scenario": "选择异常场景",
        "sim_location": "模拟位置",
        "sim_location_help": "演示版先手动模拟位置，后续可以直接替换为真实可穿戴设备上报的位置。",
        "location_caption": "当前位置为演示定位字段，未来可直接替换为真实智能可穿戴设备上报的位置。",
        "send_alert": "发送当前异常场景",
        "send_safe": "发送当前正常样本",
        "alert_payload": "**异常样本 payload**",
        "safe_payload": "**正常样本 payload**",
        "last_result": "**最近一次信号处理结果**",
        "young_log": "年轻人节点日志",
        "elder_log": "老人节点日志",
        "young_start_result": "年轻人节点启动结果: {value}",
        "elder_start_result": "老人节点启动结果: {value}",
        "bind_result": "绑定结果: {value}",
        "stop_result": "停止结果: {value}",
        "reset_result": "重置结果: {value}",
        "not_triggered": "not_triggered",
    },
    "en": {
        "title": "HealthClaw Cross-device Demo",
        "section_start": "1. Start Nodes",
        "start_young": "Start young-side node",
        "start_elder": "Start elder-side node",
        "start_both": "Start both nodes",
        "stop_both": "Stop both nodes",
        "reset_demo": "Reset demo environment",
        "young_health": "**Young-side node health**",
        "elder_health": "**Elder-side node health**",
        "section_binding": "2. Device Binding",
        "binding_desc": "By default, this demo binds elder node `elder_01` to young-side node `child_01` for caregiver notifications.",
        "bind_default": "Create default binding",
        "refresh_bindings": "Refresh binding status",
        "current_bindings": "**Current bindings**",
        "binding_read_error": "Unable to read current bindings: {error}",
        "section_signal": "3. Simulate Wearable Alerts",
        "choose_scenario": "Choose alert scenario",
        "sim_location": "Simulated location",
        "sim_location_help": "This demo uses a manual location override for now and can later be replaced with a real wearable-reported location.",
        "location_caption": "The location shown here is a demo field and can later be replaced by a real wearable-reported location.",
        "send_alert": "Send alert sample",
        "send_safe": "Send safe sample",
        "alert_payload": "**Alert sample payload**",
        "safe_payload": "**Safe sample payload**",
        "last_result": "**Most recent signal result**",
        "young_log": "Young-side node log",
        "elder_log": "Elder-side node log",
        "young_start_result": "Young-side node start result: {value}",
        "elder_start_result": "Elder-side node start result: {value}",
        "bind_result": "Binding result: {value}",
        "stop_result": "Stop result: {value}",
        "reset_result": "Reset result: {value}",
        "not_triggered": "not_triggered",
    },
}


def _load_optional_mykey_module():
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
    return None


_OPTIONAL_MYKEY = _load_optional_mykey_module()
DEMO_TOKEN = str(
    os.environ.get("HEALTHCLAW_EXTERNAL_ALERT_TOKEN")
    or getattr(_OPTIONAL_MYKEY, "fs_external_alert_token", "")
    or "CHANGE_ME_BEFORE_DEMO"
)


def ensure_demo_binding_file():
    if DEMO_BINDING_FILE.exists():
        return
    DEMO_BINDING_FILE.write_text(
        json.dumps({"relationships": {}, "nodes": {}}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def reset_demo_binding_file():
    DEMO_BINDING_FILE.write_text(
        json.dumps({"relationships": {}, "nodes": {}}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def clear_demo_session_state():
    for key in [
        "young_start",
        "elder_start",
        "bind_result",
        "bindings",
        "signal_result",
        "stop_result",
        "reset_result",
    ]:
        st.session_state.pop(key, None)


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


def clear_pid(path):
    try:
        path.unlink()
    except FileNotFoundError:
        pass


def stop_process(path):
    pid = read_pid(path)
    if not pid:
        clear_pid(path)
        return False
    if not is_pid_alive(pid):
        clear_pid(path)
        return False
    os.kill(pid, signal.SIGTERM)
    for _ in range(20):
        if not is_pid_alive(pid):
            clear_pid(path)
            return True
        time.sleep(0.2)
    return False


def reset_demo_environment(stop_nodes=False):
    if stop_nodes:
        stop_process(YOUNG_PID)
        stop_process(ELDER_PID)
    reset_demo_binding_file()
    for log_path in [YOUNG_LOG, ELDER_LOG]:
        log_path.write_text("", encoding="utf-8")
    clear_demo_session_state()
    return {
        "status": "reset",
        "stop_nodes": stop_nodes,
        "binding_file": str(DEMO_BINDING_FILE),
    }


def launch_process(cmd, log_path, pid_path, env_overrides=None):
    with open(log_path, "ab") as log_file:
        env = dict(os.environ)
        if env_overrides:
            env.update({str(k): str(v) for k, v in env_overrides.items()})
        proc = subprocess.Popen(
            cmd,
            cwd=str(PROJECT_ROOT),
            stdout=log_file,
            stderr=subprocess.STDOUT,
            env=env,
        )
    pid_path.write_text(str(proc.pid), encoding="utf-8")
    return proc.pid


def safe_get_json(url):
    try:
        return http_get_json(url)["response"]
    except Exception as e:
        return {"status": "down", "msg": str(e)}


def start_young_node(locale="zh"):
    health = safe_get_json(YOUNG_BASE + "/healthz")
    if health.get("status") == "ok":
        return {"status": "already_running", "health": health}
    pid = launch_process(
        [sys.executable, "fsapp.py"],
        YOUNG_LOG,
        YOUNG_PID,
        env_overrides={"HEALTHCLAW_DEMO_LOCALE": locale},
    )
    time.sleep(3)
    return {"status": "started", "pid": pid, "health": safe_get_json(YOUNG_BASE + "/healthz")}


def start_elder_node():
    ensure_demo_binding_file()
    health = safe_get_json(ELDER_BASE + "/healthz")
    if health.get("status") == "ok":
        return {"status": "already_running", "health": health}
    pid = launch_process(
        [
            sys.executable,
            "cross_device_node.py",
            "--node-id",
            "elder_01",
            "--host",
            "127.0.0.1",
            "--port",
            "8790",
            "--binding-file",
            str(DEMO_BINDING_FILE),
        ],
        ELDER_LOG,
        ELDER_PID,
    )
    time.sleep(2)
    return {"status": "started", "pid": pid, "health": safe_get_json(ELDER_BASE + "/healthz")}


def bind_demo_nodes():
    ensure_demo_binding_file()
    return http_post_json(
        ELDER_BASE + "/bindings/upsert",
        {
            "sender_id": "elder_01",
            "target_id": "child_01",
            "endpoint": YOUNG_BASE + "/external_alert",
            "token": DEMO_TOKEN,
            "target_name": "Young OpenClaw",
        },
    )["response"]


def get_bindings():
    return http_get_json(ELDER_BASE + "/bindings")["response"]


def send_signal(payload):
    request_payload = dict(payload)
    request_payload.setdefault("sender_id", "elder_01")
    return http_post_json(
        ELDER_BASE + "/signal_input",
        request_payload,
    )["response"]


def read_log_tail(path, lines=30):
    if not path.exists():
        return "(no log yet)"
    text = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    if not text:
        return "(log empty)"
    return "\n".join(text[-lines:])


st.set_page_config(page_title="HealthClaw Cross-device Demo", layout="wide")

ensure_demo_binding_file()

if "cross_demo_locale" not in st.session_state:
    st.session_state["cross_demo_locale"] = "zh"

locale = st.selectbox(
    "Language / 语言",
    ["zh", "en"],
    index=0 if st.session_state.get("cross_demo_locale", "zh") == "zh" else 1,
    format_func=lambda value: "中文" if value == "zh" else "English",
)
st.session_state["cross_demo_locale"] = locale


def t(key, **kwargs):
    text = UI_TEXT[locale][key]
    return text.format(**kwargs) if kwargs else text


st.title(t("title"))

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader(t("section_start"))
    if st.button(t("start_young"), use_container_width=True):
        st.session_state["young_start"] = start_young_node(locale=locale)
    if st.button(t("start_elder"), use_container_width=True):
        st.session_state["elder_start"] = start_elder_node()
    if st.button(t("start_both"), type="primary", use_container_width=True):
        st.session_state["reset_result"] = reset_demo_environment(stop_nodes=True)
        st.session_state["young_start"] = start_young_node(locale=locale)
        st.session_state["elder_start"] = start_elder_node()
    if st.button(t("stop_both"), use_container_width=True):
        young_stopped = stop_process(YOUNG_PID)
        elder_stopped = stop_process(ELDER_PID)
        st.session_state["stop_result"] = {
            "young_stopped": young_stopped,
            "elder_stopped": elder_stopped,
        }
    if st.button(t("reset_demo"), use_container_width=True):
        st.session_state["reset_result"] = reset_demo_environment(stop_nodes=False)

    st.markdown(t("young_health"))
    st.json(safe_get_json(YOUNG_BASE + "/healthz"))
    st.markdown(t("elder_health"))
    st.json(safe_get_json(ELDER_BASE + "/healthz"))

with col2:
    st.subheader(t("section_binding"))
    st.write(t("binding_desc"))
    if st.button(t("bind_default"), use_container_width=True):
        try:
            st.session_state["bind_result"] = bind_demo_nodes()
        except Exception as e:
            st.session_state["bind_result"] = {"status": "error", "msg": str(e)}
    if st.button(t("refresh_bindings"), use_container_width=True):
        try:
            st.session_state["bindings"] = get_bindings()
        except Exception as e:
            st.session_state["bindings"] = {"status": "error", "msg": str(e)}

    st.markdown(t("current_bindings"))
    try:
        st.json(get_bindings())
    except Exception as e:
        st.warning(t("binding_read_error", error=e))

with col3:
    st.subheader(t("section_signal"))
    scenario_keys = list(DEMO_SIGNAL_SCENARIOS.keys())
    scenario_key = st.selectbox(
        t("choose_scenario"),
        scenario_keys,
        format_func=lambda key: DEMO_SIGNAL_SCENARIOS[key]["label_en"] if locale == "en" else DEMO_SIGNAL_SCENARIOS[key]["label"],
    )
    scenario = DEMO_SIGNAL_SCENARIOS[scenario_key]
    alert_payload = build_demo_signal_payload(scenario_key, sender_id="elder_01", safe=False, locale=locale)
    safe_payload = build_demo_signal_payload(scenario_key, sender_id="elder_01", safe=True, locale=locale)
    default_location_text = ((alert_payload.get("location") or {}).get("location_text") or "").strip()
    location_text = st.text_input(
        t("sim_location"),
        value=default_location_text,
        key=f"location_text_{locale}_{scenario_key}",
        help=t("sim_location_help"),
    ).strip()
    if location_text:
        for payload in [alert_payload, safe_payload]:
            location = dict(payload.get("location") or {})
            location["location_text"] = location_text
            location.setdefault("source", "demo_manual_override")
            payload["location"] = location

    scenario_description = scenario.get("description_en") if locale == "en" else scenario.get("description")
    if scenario_description:
        st.info(scenario_description)
    st.caption(t("location_caption"))
    if st.button(t("send_alert"), type="primary", use_container_width=True):
        try:
            st.session_state["signal_result"] = send_signal(alert_payload)
        except Exception as e:
            st.session_state["signal_result"] = {"status": "error", "msg": str(e)}
    if st.button(t("send_safe"), use_container_width=True):
        try:
            st.session_state["signal_result"] = send_signal(safe_payload)
        except Exception as e:
            st.session_state["signal_result"] = {"status": "error", "msg": str(e)}
    st.markdown(t("alert_payload"))
    st.json(alert_payload)
    st.markdown(t("safe_payload"))
    st.json(safe_payload)

    st.markdown(t("last_result"))
    st.json(st.session_state.get("signal_result", {"status": t("not_triggered")}))

st.divider()

left, right = st.columns(2)
with left:
    st.subheader(t("young_log"))
    st.code(read_log_tail(YOUNG_LOG), language="text")
with right:
    st.subheader(t("elder_log"))
    st.code(read_log_tail(ELDER_LOG), language="text")

if "young_start" in st.session_state:
    st.info(t("young_start_result", value=st.session_state["young_start"]))
if "elder_start" in st.session_state:
    st.info(t("elder_start_result", value=st.session_state["elder_start"]))
if "bind_result" in st.session_state:
    st.success(t("bind_result", value=st.session_state["bind_result"]))
if "stop_result" in st.session_state:
    st.warning(t("stop_result", value=st.session_state["stop_result"]))
if "reset_result" in st.session_state:
    st.info(t("reset_result", value=st.session_state["reset_result"]))
