"""
Self-Evolving HealthClaw — 飞书 Bot 前端
双模式：WebSocket 事件推送 + API 轮询回退。
启动: python fsapp.py
"""
import os, sys, threading, time, re, json, glob, urllib.request
import importlib.util
import queue as Q
from PIL import Image

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)
os.environ.setdefault("HEALTHCLAW_ENABLE_PHONE_MEITUAN", "1")

from cross_device_node import CrossDeviceServer
from meal_plan_service import MealPlanService, detect_meal_plan_action


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
    repo_parent = os.path.abspath(os.path.join(PROJECT_ROOT, ".."))

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
        try:
            spec = importlib.util.spec_from_file_location("healthclaw_shared_mykey", path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                return module
        except Exception as exc:
            print(f"[HealthClaw] 加载共享 mykey 失败: {path} -> {exc}")
    return None


mykey = _load_mykey_module()

_TAG_PATS = [r'<' + t + r'>.*?</' + t + r'>' for t in ('thinking', 'summary', 'tool_use', 'file_content')]

def _clean(text):
    for p in _TAG_PATS:
        text = re.sub(p, '', text, flags=re.DOTALL)
    return re.sub(r'\n{3,}', '\n\n', text).strip() or '...'

APP_ID = getattr(mykey, 'fs_app_id', None)
APP_SECRET = getattr(mykey, 'fs_app_secret', None)
ALLOWED_USERS = set(getattr(mykey, 'fs_allowed_users', []))
EXTERNAL_ALERT_HOST = getattr(mykey, 'fs_external_alert_host', '127.0.0.1')
EXTERNAL_ALERT_PORT = int(getattr(mykey, 'fs_external_alert_port', 8787))
EXTERNAL_ALERT_TOKEN = str(getattr(mykey, 'fs_external_alert_token', '') or '')
EXTERNAL_ALERT_TARGETS = dict(getattr(mykey, 'fs_external_alert_targets', {}) or {})
ENABLE_EXTERNAL_ALERT_SERVER = bool(getattr(mykey, 'fs_enable_external_alert_server', True))
ENABLE_ALERT_EXPLAINER = bool(getattr(mykey, 'fs_enable_alert_explainer', True))
NODE_ID = str(getattr(mykey, 'cross_device_node_id', 'child_01') or 'child_01')

agent = None
agent_init_error = ""
meal_plan_service = MealPlanService()

client = None
user_tasks = {}
_ws_event_received = False
external_alert_server = None
meal_plan_scheduler = None
_alert_llm_state = {
    "auth_invalid": False,
    "last_error": "",
    "probe_done": False,
}


def _startup_locale():
    return "en" if str(os.environ.get("HEALTHCLAW_DEMO_LOCALE", "") or "").strip().lower().startswith("en") else "zh"


def _startup_online_text(polling=False):
    if _startup_locale() == "en":
        if polling:
            return "🩺 HealthClaw is online (polling mode). You can start chatting now!"
        return "🩺 HealthClaw is online. You can start chatting now!"
    if polling:
        return "🩺 HealthClaw 已上线（轮询模式），可以开始对话！"
    return "🩺 HealthClaw 已上线，可以开始对话！"


def _feishu_application_lang():
    return "en_us" if _startup_locale() == "en" else "zh_cn"


def ensure_agent_ready():
    global agent, agent_init_error
    if agent is not None:
        return agent
    if agent_init_error:
        raise RuntimeError(agent_init_error)
    try:
        from seda_main import DiagnosisAgent
    except Exception as exc:
        agent_init_error = f"DiagnosisAgent unavailable: {exc}"
        raise RuntimeError(agent_init_error) from exc

    agent = DiagnosisAgent()
    threading.Thread(target=agent.run, daemon=True).start()
    return agent


def _coerce_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _coerce_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _strip_protocol_tags(text):
    if not text:
        return ""
    for tag in ("thinking", "summary", "tool_use", "tool_result", "file_content"):
        text = re.sub(rf"<{tag}>.*?</{tag}>", "", text, flags=re.DOTALL)
    text = re.sub(r"^```(?:markdown|md|text)?\s*", "", text.strip(), flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text.strip())
    return text.strip()


def _looks_like_auth_error(text):
    lowered = str(text or "").lower()
    return any(
        token in lowered
        for token in [
            "invalid api key",
            "invalid_api_key",
            "unauthorized",
            "401",
            "incorrect api key",
        ]
    )


def _record_alert_llm_error(error_text):
    if not error_text:
        return
    _alert_llm_state["last_error"] = str(error_text)
    if _looks_like_auth_error(error_text):
        _alert_llm_state["auth_invalid"] = True


def _probe_alert_llm_auth_once():
    if _alert_llm_state.get("probe_done"):
        return
    _alert_llm_state["probe_done"] = True

    cfg = getattr(mykey, "oai_config", {}) or {}
    api_base = str(cfg.get("apibase", "") or "").strip().rstrip("/")
    api_key = str(cfg.get("apikey", "") or "").strip()
    if not api_base or not api_key:
        return

    try:
        import requests

        response = requests.get(
            f"{api_base}/v1/models",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=15,
        )
        if response.status_code == 401:
            body = response.text or ""
            if _looks_like_auth_error(body) or "INVALID_API_KEY" in body:
                _record_alert_llm_error(body or "401 Unauthorized")
    except Exception:
        return


def _build_direct_fallback_result(alert, error_text="", source="fallback"):
    if error_text:
        _record_alert_llm_error(error_text)
    return {
        "status": "fallback",
        "source": source,
        "markdown": build_fallback_alert_explanation(alert),
        "error": error_text,
        "error_kind": "auth_invalid" if _looks_like_auth_error(error_text) else "llm_unavailable",
        "model": "",
    }


def _alert_locale(alert):
    if not isinstance(alert, dict):
        return "zh"
    locale = alert.get("locale")
    if not locale and isinstance(alert.get("details"), dict):
        locale = alert["details"].get("locale")
    return "en" if str(locale or "").strip().lower().startswith("en") else "zh"


def build_alert_explanation_prompt(alert):
    locale = _alert_locale(alert)
    alert_json = json.dumps(alert, ensure_ascii=False, indent=2)
    location_text = _extract_alert_location_text(alert)
    if locale == "en":
        location_hint = ""
        if location_text:
            location_hint = (
                f"9. If the alert already includes a location (currently: {location_text}), "
                "remind the family to contact the closest available person near that location first.\n\n"
            )
        return (
            "You are HealthClaw's caregiver alert explainer. "
            "Your job is not to decide whether the alert is valid again, but to explain an already-triggered alert to a family member without a medical background.\n\n"
            "Requirements:\n"
            "1. Explain only from the provided alert data. Do not invent vitals, location details, history, or test results.\n"
            "2. Use plain English and avoid heavy medical jargon.\n"
            "3. Do not give a definitive diagnosis. Use language such as 'may', 'could', 'worth watching', or 'should be confirmed'.\n"
            "4. Output Markdown and include exactly these 4 headings:\n"
            "**What This Means**\n"
            "**Possible Reasons**\n"
            "**What To Do Now**\n"
            "**When To Call Emergency Help**\n"
            "5. Under each heading, write 2-4 short bullet points.\n"
            "6. If the data is limited, explicitly say that the alert alone is not enough to determine the cause.\n"
            "7. For high heart rate alerts, remind the family to distinguish a brief post-activity spike from a sustained resting elevation.\n\n"
            "8. Alerts may come from wearable heart rate, oxygen, fall, rhythm, temperature, or activity signals, so the explanation should match the signal type.\n\n"
            f"{location_hint}"
            "Alert data:\n"
            f"```json\n{alert_json}\n```"
        )

    location_hint = ""
    if location_text:
        location_hint = (
            f"9. 如果告警里已经给出位置（当前为：{location_text}），"
            "要提醒家属可以优先联系离该位置最近的人前往查看。\n\n"
        )
    return (
        "你是 HealthClaw 的家庭照护告警解释器。"
        "你的任务不是重新判断是否报警，而是把已经触发的告警解释给非医学背景家属听。\n\n"
        "要求：\n"
        "1. 只依据提供的告警数据解释，不要编造未提供的生命体征、定位、病史或检查结果。\n"
        "2. 用简体中文，语言直白，不使用过多专业术语。\n"
        "3. 不要给出确定诊断，只能说“可能”“需要警惕”“建议确认”。\n"
        "4. 输出 Markdown，并且严格包含以下 4 个标题：\n"
        "**这代表什么**\n"
        "**可能原因**\n"
        "**建议马上做什么**\n"
        "**何时立刻急救**\n"
        "5. 每个标题下给 2-4 条简短要点。\n"
        "6. 如果数据不足，要明确写出“单靠这条告警不足以判断病因”。\n"
        "7. 如果是心率升高类告警，要提醒家属区分“活动后短暂升高”和“静息状态持续升高”。\n\n"
        "8. 告警可能来自可穿戴设备的心率、血氧、跌倒、心律不齐、体温、活动量等信号，要结合对应信号解释风险。\n\n"
        f"{location_hint}"
        "告警数据如下：\n"
        f"```json\n{alert_json}\n```"
    )


def _build_fallback_alert_explanation_en(alert):
    event_type = str(alert.get("event_type", "external_alert") or "external_alert")
    details = alert.get("details") if isinstance(alert.get("details"), dict) else {}
    heart_rate = _coerce_int(details.get("heart_rate", alert.get("heart_rate")), 0)
    duration_sec = _coerce_int(details.get("duration_sec", alert.get("duration_sec")), 0)
    threshold = _coerce_int((details.get("rule") or {}).get("threshold"), 0)
    spo2 = _coerce_int(details.get("spo2", alert.get("spo2")), 0)
    impact_g = _coerce_float(details.get("impact_g", alert.get("impact_g")), 0.0)
    no_movement_sec = _coerce_int(details.get("no_movement_sec", alert.get("no_movement_sec")), 0)
    episode_count = _coerce_int(details.get("episode_count", alert.get("episode_count")), 0)
    resting_heart_rate = _coerce_int(details.get("resting_heart_rate", alert.get("resting_heart_rate")), 0)
    body_temperature = _coerce_float(details.get("body_temperature", alert.get("body_temperature")), 0.0)
    inactivity_minutes = _coerce_int(details.get("inactivity_minutes", alert.get("inactivity_minutes")), 0)
    threshold_minutes = _coerce_int((details.get("rule") or {}).get("threshold_minutes"), 0)
    classification = str(details.get("classification", "") or "")

    if event_type == "heart_rate_alert":
        threshold_text = f"{threshold} bpm" if threshold > 0 else "the configured threshold"
        return "\n".join(
            [
                "**What This Means**",
                f"- The wearable detected a heart rate around {heart_rate} bpm for about {duration_sec} seconds, which is above the alert rule.",
                "- That means the older adult is worth checking on soon, but this alert alone is not enough to identify the exact cause.",
                "- A sustained elevation at rest is usually more concerning than a brief spike right after activity.",
                "",
                "**Possible Reasons**",
                "- This could reflect recent movement, stress, pain, fever, dehydration, or a loose wearable reading.",
                f"- It could also reflect an arrhythmia or other acute discomfort, but the alert alone cannot confirm that and only shows a sustained rate above {threshold_text}.",
                "",
                "**What To Do Now**",
                "- Contact the older adult and confirm they are awake, speaking normally, and not alone.",
                "- Ask about chest discomfort, shortness of breath, dizziness, palpitations, a fall, or clear weakness.",
                "- If possible, repeat the heart rate check after a short rest and see whether it comes down quickly.",
                "",
                "**When To Call Emergency Help**",
                "- Call emergency help right away if the alert comes with chest pain, severe shortness of breath, fainting, confusion, or one-sided weakness.",
                "- If the heart rate stays very high at rest and does not come down on repeat checks, urgent in-person care is also appropriate.",
                "- If the device keeps sending high-risk alerts and the family cannot reach the older adult, treat it as an emergency.",
            ]
        )

    if event_type == "blood_oxygen_alert":
        return "\n".join(
            [
                "**What This Means**",
                f"- The wearable detected oxygen saturation around {spo2}% for about {duration_sec} seconds, which can suggest breathing or circulation risk.",
                "- This alert alone is not enough to determine the cause, but sustained low oxygen deserves more attention than a brief fluctuation.",
                "",
                "**Possible Reasons**",
                "- This could reflect a respiratory infection, COPD or asthma worsening, another lung issue, or a temporary measurement error.",
                "- Loose device fit or movement during the reading can also cause a false alarm, so a repeat check matters.",
                "",
                "**What To Do Now**",
                "- Contact the older adult and ask about shortness of breath, chest tightness, fast breathing, blue lips, or unusual fatigue.",
                "- Ask them to sit upright, stay calm, and repeat the oxygen reading if possible.",
                "- If home oxygen or prior respiratory history exists, share that information with whoever can check on them in person.",
                "",
                "**When To Call Emergency Help**",
                "- Call emergency help if there is obvious breathing distress, blue lips, confusion, or the older adult cannot speak normally.",
                "- If repeat checks stay very low or the family cannot reach the older adult at all, treat it as urgent.",
            ]
        )

    if event_type == "fall_detected_alert":
        return "\n".join(
            [
                "**What This Means**",
                f"- The wearable detected a possible fall with about {impact_g:.1f}g of impact and about {no_movement_sec} seconds without clear movement afterward.",
                "- Fall alerts usually deserve faster on-site confirmation than a single abnormal vital sign because injuries can be hidden.",
                "",
                "**Possible Reasons**",
                "- This may be a true fall, a slip while standing up, or occasionally a strong device impact that caused a false alarm.",
                "- If there was prolonged stillness afterward, worry more about the older adult being unable to get up alone.",
                "",
                "**What To Do Now**",
                "- Contact the older adult or the nearest caregiver immediately and confirm whether they are awake, speaking, and in pain.",
                "- If someone is already there, do not force them up immediately before checking for head injury, deformity, or severe pain.",
                "- If they cannot stand, have strong pain, or may have hit their head, arrange in-person help quickly.",
                "",
                "**When To Call Emergency Help**",
                "- Call emergency help right away for loss of consciousness, head injury, suspected fracture, vomiting, or inability to stand.",
                "- If the device keeps showing a post-fall no-movement state and no one can reach the older adult, treat it as an emergency.",
            ]
        )

    if event_type == "arrhythmia_alert":
        return "\n".join(
            [
                "**What This Means**",
                f"- The wearable flagged a possible irregular rhythm for about {duration_sec} seconds with about {episode_count} abnormal rhythm segments.",
                f"- Resting heart rate is around {resting_heart_rate} bpm." if resting_heart_rate > 0 else "- The alert suggests rhythm instability worth checking, but it is not a confirmed diagnosis by itself.",
                "- The alert suggests rhythm instability worth checking, but it is not a confirmed diagnosis by itself." if resting_heart_rate > 0 else "",
                "",
                "**Possible Reasons**",
                "- This could reflect atrial fibrillation or another rhythm issue, but it can also come from wearable signal noise or a temporary rhythm disturbance.",
                "- The alert alone is not enough to determine the exact rhythm problem without symptoms and a formal ECG.",
                "",
                "**What To Do Now**",
                "- Contact the older adult and ask about palpitations, dizziness, chest discomfort, shortness of breath, or near-fainting.",
                "- Ask them to stop activity, sit down, rest, and repeat the reading if possible.",
                "- If there is prior ECG history or medication information, keep it ready for whoever follows up.",
                "",
                "**When To Call Emergency Help**",
                "- Call emergency help right away if the alert comes with fainting, severe shortness of breath, confusion, or ongoing chest pain.",
                "- If repeated irregular rhythm alerts continue and the older adult cannot be reached, arrange urgent on-site confirmation.",
            ]
        ).replace("\n- \n", "\n")

    if event_type == "temperature_alert":
        if classification == "low_temperature":
            return "\n".join(
                [
                    "**What This Means**",
                    f"- The wearable suggests a low body temperature around {body_temperature:.1f}C.",
                    "- Low temperature in an older adult can matter even when the cause is not yet clear.",
                    "",
                    "**Possible Reasons**",
                    "- This can happen with cold environment exposure, poor intake, infection, or a general decline in condition.",
                    "- Device error is also possible, so a repeat temperature check is important.",
                    "",
                    "**What To Do Now**",
                    "- Contact the older adult, confirm their mental status, and ask whether they feel cold, weak, or shaky.",
                    "- Repeat the temperature if possible and help them stay warm while arranging in-person follow-up if needed.",
                    "",
                    "**When To Call Emergency Help**",
                    "- Call emergency help if there is confusion, extreme weakness, slowed breathing, or no one can reach the older adult.",
                    "- If repeat checks still show low temperature, urgent in-person assessment is reasonable.",
                ]
            )
        return "\n".join(
            [
                "**What This Means**",
                f"- The wearable suggests a high body temperature around {body_temperature:.1f}C, which may reflect fever or an acute inflammatory process.",
                "- Fever does not automatically mean severe illness, but in older adults it can come with dehydration or mental status changes more easily.",
                "",
                "**Possible Reasons**",
                "- This could reflect a respiratory infection, urinary infection, another inflammatory issue, or sometimes environmental heat or a measurement error.",
                "- Symptoms such as cough, chills, painful urination, or low fluid intake make a true fever more likely.",
                "",
                "**What To Do Now**",
                "- Contact the older adult and ask about chills, cough, breathing changes, painful urination, weakness, or reduced drinking.",
                "- Repeat the temperature, encourage fluids if appropriate, and arrange an in-person check if the older adult seems worse.",
                "",
                "**When To Call Emergency Help**",
                "- Call emergency help if there is confusion, severe shortness of breath, persistent vomiting, or inability to get up.",
                "- If the family cannot reach the older adult or the temperature stays very high on repeat checks, escalate quickly.",
            ]
        )

    if event_type == "inactivity_alert":
        return "\n".join(
            [
                "**What This Means**",
                f"- The wearable detected about {inactivity_minutes} minutes without meaningful movement, which is beyond the alert threshold of about {threshold_minutes} minutes.",
                "- This does not automatically mean an emergency, but it is worth checking if the older adult would not normally stay still that long.",
                "",
                "**Possible Reasons**",
                "- This may simply reflect a nap, watching TV, taking the device off, or a tracking gap.",
                "- It could also reflect a fall, acute illness, reduced consciousness, or the older adult being unable to get up.",
                "",
                "**What To Do Now**",
                "- Contact the older adult and confirm whether they are awake, responding normally, and simply resting.",
                "- If they live alone, ask a nearby family member, neighbor, or caregiver to check in person soon.",
                "",
                "**When To Call Emergency Help**",
                "- Treat it as urgent if there is prolonged inactivity together with no response from the older adult.",
                "- If an in-person check finds abnormal breathing, altered consciousness, or inability to get up, call emergency help immediately.",
            ]
        )

    return "\n".join(
        [
            "**What This Means**",
            "- HealthClaw detected a health-related alert that deserves caregiver attention.",
            "- The alert alone is not enough to determine the exact cause without checking the older adult directly.",
            "",
            "**Possible Reasons**",
            "- The signal may reflect activity, device noise, or a real physical problem.",
            "- Symptoms, duration, and repeat measurements are all needed to judge risk more accurately.",
            "",
            "**What To Do Now**",
            "- Contact the older adult soon and confirm they are awake, responsive, and not alone.",
            "- Ask about chest discomfort, breathing changes, dizziness, pain, a fall, or any other obvious problem.",
            "- If practical, repeat the relevant measurement and see whether it improves.",
            "",
            "**When To Call Emergency Help**",
            "- Call emergency help if there is altered consciousness, major breathing trouble, chest pain, injury after a fall, or no response from the older adult.",
            "- If alerts keep repeating together with clear symptoms, urgent in-person care is appropriate.",
        ]
    )


def build_fallback_alert_explanation(alert):
    if _alert_locale(alert) == "en":
        return _build_fallback_alert_explanation_en(alert)
    event_type = str(alert.get("event_type", "external_alert") or "external_alert")
    details = alert.get("details") if isinstance(alert.get("details"), dict) else {}
    heart_rate = _coerce_int(details.get("heart_rate", alert.get("heart_rate")), 0)
    duration_sec = _coerce_int(details.get("duration_sec", alert.get("duration_sec")), 0)
    threshold = _coerce_int((details.get("rule") or {}).get("threshold"), 0)
    spo2 = _coerce_int(details.get("spo2", alert.get("spo2")), 0)
    impact_g = details.get("impact_g", alert.get("impact_g"))
    no_movement_sec = _coerce_int(details.get("no_movement_sec", alert.get("no_movement_sec")), 0)
    episode_count = _coerce_int(details.get("episode_count", alert.get("episode_count")), 0)
    resting_heart_rate = _coerce_int(details.get("resting_heart_rate", alert.get("resting_heart_rate")), 0)
    body_temperature = details.get("body_temperature", alert.get("body_temperature"))
    inactivity_minutes = _coerce_int(details.get("inactivity_minutes", alert.get("inactivity_minutes")), 0)
    threshold_minutes = _coerce_int((details.get("rule") or {}).get("threshold_minutes"), 0)
    classification = str(details.get("classification", "") or "")

    if event_type == "heart_rate_alert":
        hr_text = f"{heart_rate} bpm" if heart_rate > 0 else "偏快"
        duration_text = f"{duration_sec} 秒" if duration_sec > 0 else "一段时间"
        threshold_text = f"{threshold} bpm" if threshold > 0 else "设定阈值"
        return "\n".join(
            [
                "**这代表什么**",
                f"- 系统检测到老人心率达到 {hr_text}，并持续了 {duration_text}，已经超过预警条件。",
                "- 这说明当前值得尽快联系老人确认状态，但单靠这条告警还不足以直接判断具体病因。",
                "- 如果这是在静息状态下持续升高，通常比活动后短暂升高更需要重视。",
                "",
                "**可能原因**",
                "- 可能是刚活动、情绪紧张、疼痛、发热、脱水，或设备佩戴不稳导致读数异常。",
                "- 也可能提示心律失常、感染、急性不适等情况，需要结合老人当下症状判断。",
                f"- 当前只能确认“持续高于 {threshold_text} 的心率告警被触发”，不能直接等同于某一种疾病。",
                "",
                "**建议马上做什么**",
                "- 先尽快联系老人，确认是否清醒、能否正常说话、是否独处。",
                "- 问清是否有胸闷、胸痛、气短、头晕、心慌、跌倒或明显虚弱，并尽量让老人停止活动、坐下休息。",
                "- 如果条件允许，重新测一次心率或观察几分钟，看是否快速回落。",
                "- 如果无法联系上老人，建议尽快联系附近家人、邻居或照护人员到现场查看。",
                "",
                "**何时立刻急救**",
                "- 如果同时出现胸痛、呼吸困难、意识模糊、晕厥、单侧肢体无力、持续剧烈不适，应立即呼叫急救。",
                "- 如果老人处于静息状态却持续心率很高，且反复复测仍不下降，也应尽快线下就医。",
                "- 如果设备连续多次触发高危告警而家属始终联系不上老人，也应按紧急情况处理。",
            ]
        )

    if event_type == "blood_oxygen_alert":
        spo2_text = f"{spo2}%" if spo2 > 0 else "偏低"
        duration_text = f"{duration_sec} 秒" if duration_sec > 0 else "一段时间"
        return "\n".join(
            [
                "**这代表什么**",
                f"- 系统检测到老人血氧下降到 {spo2_text}，并持续了 {duration_text}，提示可能存在呼吸或循环方面的风险。",
                "- 单靠这条告警不足以判断具体病因，但持续低血氧通常比短暂波动更值得警惕。",
                "- 如果老人本身有肺部疾病、感染或正在静息状态下仍低血氧，需要更重视。",
                "",
                "**可能原因**",
                "- 可能是呼吸道感染、慢阻肺/哮喘加重、肺部问题、心功能异常，或短时佩戴不稳导致读数偏差。",
                "- 如果老人正在活动、刚说话或手表佩戴过松，也可能造成短时误报，需要复测确认。",
                "",
                "**建议马上做什么**",
                "- 先联系老人，确认是否气短、胸闷、呼吸急促、发绀、说话费力或明显乏力。",
                "- 让老人尽量坐起、保持安静，重新测一次血氧并观察是否回升。",
                "- 如果家里有制氧或既往病史资料，尽快同步给到现场照护人员或医生。",
                "",
                "**何时立刻急救**",
                "- 如果老人出现明显呼吸困难、嘴唇发紫、意识模糊、无法完整说话，应立即呼叫急救。",
                "- 如果反复复测血氧仍持续很低，或家属根本联系不上老人，也应按紧急情况处理。",
            ]
        )

    if event_type == "fall_detected_alert":
        impact_text = f"{float(impact_g):.1f}g" if impact_g not in (None, "") else "较明显冲击"
        no_motion_text = f"{no_movement_sec} 秒" if no_movement_sec > 0 else "短时间"
        return "\n".join(
            [
                "**这代表什么**",
                f"- 可穿戴设备检测到一次疑似跌倒事件，伴随 {impact_text} 的冲击，且之后约 {no_motion_text} 没有明显活动。",
                "- 跌倒告警通常比单一生命体征异常更需要优先确认现场安全，尤其要警惕头部外伤或骨折。",
                "- 单靠设备信号还不能判断受伤程度，但需要尽快确认老人是否还能自主活动和交流。",
                "",
                "**可能原因**",
                "- 可能是真实跌倒、滑倒、从床椅起身时失衡，也可能是设备受到剧烈撞击产生误报。",
                "- 如果同时伴随长时间无应答，就要警惕跌倒后无法自行起身的情况。",
                "",
                "**建议马上做什么**",
                "- 立即电话联系老人或附近照护人员，优先确认是否清醒、能否说话、是否头晕或疼痛。",
                "- 如果有人在现场，不要急着强行扶起，先确认是否头部受伤、肢体变形或明显疼痛。",
                "- 如果老人表示无法起身、剧痛或疑似撞到头部，应尽快安排线下救助。",
                "",
                "**何时立刻急救**",
                "- 如果老人失去意识、头部受伤出血、疑似骨折、无法站立或出现呕吐、嗜睡，应立即急救。",
                "- 如果设备持续显示跌倒后无活动、家属又联系不上老人，也应按紧急救援处理。",
            ]
        )

    if event_type == "arrhythmia_alert":
        rhythm_text = f"{episode_count} 次异常节律片段" if episode_count > 0 else "异常节律信号"
        hr_text = f"，静息心率约 {resting_heart_rate} bpm" if resting_heart_rate > 0 else ""
        duration_text = f"{duration_sec} 秒" if duration_sec > 0 else "一段时间"
        return "\n".join(
            [
                "**这代表什么**",
                f"- 设备检测到疑似心律不齐，持续约 {duration_text}，共提示 {rhythm_text}{hr_text}。",
                "- 这类告警并不等于已经明确诊断某种心律失常，但说明节律波动值得进一步确认。",
                "- 如果老人同时有心慌、头晕、胸闷或既往心脏病史，需要更重视。",
                "",
                "**可能原因**",
                "- 可能是房颤等心律异常、短暂早搏增多、疲劳或情绪波动，也可能与设备采集噪声有关。",
                "- 单靠可穿戴信号不足以确定具体类型，通常仍需要结合症状和正规心电图判断。",
                "",
                "**建议马上做什么**",
                "- 尽快联系老人，确认是否有心慌、胸闷、头晕、乏力、气短或快要晕倒的感觉。",
                "- 让老人先停止活动、坐下休息，并尽量再次测量心率或查看设备是否重复提示。",
                "- 如果家里有既往心电图、抗凝/抗心律失常药物信息，建议一起准备好。",
                "",
                "**何时立刻急救**",
                "- 如果伴随胸痛、晕厥、严重气短、意识模糊或持续明显心慌不缓解，应立即急救。",
                "- 如果设备反复提示异常节律且老人又联系不上，也应尽快安排现场查看。",
            ]
        )

    if event_type == "temperature_alert":
        if classification == "low_temperature":
            temp_text = f"{float(body_temperature):.1f}℃" if body_temperature not in (None, "") else "偏低"
            return "\n".join(
                [
                    "**这代表什么**",
                    f"- 设备检测到老人可能体温偏低，当前约为 {temp_text}，需要警惕受凉、感染或循环问题。",
                    "- 单靠这条告警无法判断具体原因，但低体温在老人中通常不能忽视。",
                    "",
                    "**可能原因**",
                    "- 可能与环境过冷、长时间卧床、感染、进食不足或全身状态变差有关。",
                    "- 也可能是设备测量误差，需要结合现场复测。",
                    "",
                    "**建议马上做什么**",
                    "- 先联系老人，确认意识、手脚温度、发抖情况和是否有明显虚弱。",
                    "- 尽快复测体温，并注意保暖，必要时联系现场照护人员查看。",
                    "",
                    "**何时立刻急救**",
                    "- 如果同时出现意识不清、极度虚弱、呼吸变慢或无法联系上老人，应立即急救。",
                    "- 如果复测仍持续低体温，也应尽快线下就医。",
                ]
            )

        temp_text = f"{float(body_temperature):.1f}℃" if body_temperature not in (None, "") else "偏高"
        return "\n".join(
            [
                "**这代表什么**",
                f"- 设备检测到老人体温异常升高，当前约 {temp_text}，提示可能存在发热或急性炎症反应。",
                "- 发热本身不等于严重疾病，但老人发热更容易合并脱水、精神状态改变或基础病波动。",
                "- 单靠这条告警还不足以判断感染部位或病因，需要结合症状确认。",
                "",
                "**可能原因**",
                "- 可能是呼吸道感染、泌尿系统感染、其他炎症，也可能是环境过热或短暂测量误差。",
                "- 如果同时伴随咳嗽、尿频尿痛、寒战、精神差，通常更支持真实发热。",
                "",
                "**建议马上做什么**",
                "- 尽快联系老人，确认是否发冷、咳嗽、气短、尿急尿痛、意识变差或进水减少。",
                "- 可以先复测体温，并提醒补水、休息，必要时联系家属或照护人员上门查看。",
                "- 如果已有医生指导用药史，可按既往方案参考，但要避免只凭设备自行判断。",
                "",
                "**何时立刻急救**",
                "- 如果高热伴意识模糊、呼吸困难、持续呕吐、明显虚弱不能起身，应立即急救。",
                "- 如果家属无法联系上老人，或复测后体温持续很高，也应尽快线下就医。",
            ]
        )

    if event_type == "inactivity_alert":
        minutes_text = f"{inactivity_minutes} 分钟" if inactivity_minutes > 0 else "较长时间"
        threshold_text = f"{threshold_minutes} 分钟" if threshold_minutes > 0 else "设定阈值"
        return "\n".join(
            [
                "**这代表什么**",
                f"- 设备检测到老人连续 {minutes_text} 没有明显活动，已经超过 {threshold_text} 的提醒阈值。",
                "- 这不一定代表突发疾病，但如果老人平时不会长时间静止，就需要尽快确认是否失联或行动受限。",
                "- 如果当前并不是睡眠时段，这类异常静止更值得警惕。",
                "",
                "**可能原因**",
                "- 可能只是午休、长时间看电视、忘记佩戴，或者设备没有正常记录到活动。",
                "- 也可能提示跌倒后无法起身、突发不适、意识差或手机/手表离身。",
                "",
                "**建议马上做什么**",
                "- 先联系老人，确认是否清醒、能否正常应答、是否只是休息或摘下了设备。",
                "- 如果老人平时独居，建议尽快联系附近家人、邻居或照护人员到现场确认。",
                "- 如果有家中门磁、摄像头或其他设备信息，也可以同步交叉确认。",
                "",
                "**何时立刻急救**",
                "- 如果长时间无活动同时伴随联系不上老人、其他设备也无响应，应按紧急失联处理。",
                "- 如果现场查看发现老人无法起身、意识改变或呼吸异常，应立即急救。",
            ]
        )

    return "\n".join(
        [
            "**这代表什么**",
            "- 系统检测到一条需要家属关注的健康异常提醒。",
            "- 单靠这条告警不足以判断具体病因，需要结合老人现场状态进一步确认。",
            "",
            "**可能原因**",
            "- 可能与当时活动状态、设备误差或真实身体不适有关。",
            "- 只有把症状、持续时间和复测结果结合起来，才能更准确判断风险。",
            "",
            "**建议马上做什么**",
            "- 尽快联系老人，确认当前是否清醒、能否交流、是否独处。",
            "- 询问是否伴随胸闷、气短、头晕、疼痛、跌倒或其他明显不适。",
            "- 如果方便，尽快复测相关指标并观察是否恢复。",
            "",
            "**何时立刻急救**",
            "- 如果出现意识改变、明显呼吸困难、胸痛、跌倒受伤或无法联系上老人，应立即求助。",
            "- 如果告警持续出现且伴随明显症状，建议尽快线下就医。",
        ]
    )


def _default_alert_llm_ask(prompt):
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


def explain_alert_for_caregiver(alert, llm_ask=None):
    prompt = build_alert_explanation_prompt(alert)
    fallback_markdown = build_fallback_alert_explanation(alert)
    ask = llm_ask or _default_alert_llm_ask

    try:
        result = ask(prompt)
        if isinstance(result, dict):
            text = _strip_protocol_tags(result.get("text", ""))
            model = result.get("model", "")
        else:
            text = _strip_protocol_tags(str(result))
            model = ""
        if text:
            return {
                "status": "ok",
                "source": "llm",
                "markdown": text,
                "model": model,
            }
    except Exception as exc:
        _record_alert_llm_error(str(exc))
        return {
            "status": "fallback",
            "source": "fallback",
            "markdown": fallback_markdown,
            "error": str(exc),
            "error_kind": "auth_invalid" if _looks_like_auth_error(exc) else "llm_unavailable",
            "model": "",
        }

    return {
        "status": "fallback",
        "source": "fallback",
        "markdown": fallback_markdown,
        "error": "empty_llm_response",
        "error_kind": "empty_response",
        "model": "",
    }


def create_client():
    import lark_oapi as lark

    return lark.Client.builder().app_id(APP_ID).app_secret(APP_SECRET) \
        .log_level(lark.LogLevel.INFO).build()


def _card(text):
    return json.dumps({
        "config": {"wide_screen_mode": True},
        "elements": [{"tag": "markdown", "content": text}]
    })


def send_message(open_id, content, msg_type="text", use_card=False):
    from lark_oapi.api.im.v1 import CreateMessageRequest, CreateMessageRequestBody

    if use_card:
        ct, mt = _card(content), "interactive"
    else:
        ct, mt = json.dumps({"text": content}), "text"

    body = CreateMessageRequest.builder().receive_id_type("open_id").request_body(
        CreateMessageRequestBody.builder()
        .receive_id(open_id).msg_type(mt).content(ct).build()
    ).build()
    r = client.im.v1.message.create(body)
    if r.success():
        return r.data.message_id
    print(f"[飞书] 发送失败: {r.code}, {r.msg}")
    return None


def upload_image(image_path):
    from lark_oapi.api.im.v1 import CreateImageRequest, CreateImageRequestBody

    src = os.path.abspath(image_path)
    stem, _ext = os.path.splitext(os.path.basename(src))
    prepared_path = os.path.join(PROJECT_ROOT, "temp", f"{stem}_feishu.jpg")
    with Image.open(src) as image:
        image.convert("RGB").save(prepared_path, format="JPEG", quality=92, optimize=True)

    with open(prepared_path, "rb") as image_file:
        body = CreateImageRequestBody.builder() \
            .image_type("message") \
            .image(image_file) \
            .build()
        req = CreateImageRequest.builder().request_body(body).build()
        r = client.im.v1.image.create(req)
    if r.success():
        return r.data.image_key
    print(f"[飞书] 图片上传失败: {r.code}, {r.msg} path={image_path}")
    return None


def send_image_message(open_id, image_path):
    from lark_oapi.api.im.v1 import CreateMessageRequest, CreateMessageRequestBody

    image_key = upload_image(image_path)
    if not image_key:
        return None
    body = CreateMessageRequest.builder().receive_id_type("open_id").request_body(
        CreateMessageRequestBody.builder()
        .receive_id(open_id)
        .msg_type("image")
        .content(json.dumps({"image_key": image_key}, ensure_ascii=False))
        .build()
    ).build()
    r = client.im.v1.message.create(body)
    if r.success():
        return r.data.message_id
    print(f"[飞书] 图片消息发送失败: {r.code}, {r.msg} path={image_path}")
    return None


def send_meal_artifact_bundle(open_id, artifacts):
    labels = [
        ("搜索结果页截图", artifacts.get("result_screenshot", "")),
        ("店铺页截图", artifacts.get("merchant_screenshot", "")),
        ("购物车页截图", artifacts.get("cart_screenshot", "")),
    ]
    sent = []
    for label, image_path in labels:
        if not image_path or not os.path.exists(image_path):
            continue
        text_msg_id = send_message(open_id, label)
        image_msg_id = send_image_message(open_id, image_path)
        sent.append({"label": label, "text_message_id": text_msg_id, "image_message_id": image_msg_id})
    return sent


def update_message(message_id, content):
    from lark_oapi.api.im.v1 import PatchMessageRequest, PatchMessageRequestBody

    body = PatchMessageRequest.builder().message_id(message_id).request_body(
        PatchMessageRequestBody.builder().content(_card(content)).build()
    ).build()
    r = client.im.v1.message.patch(body)
    if not r.success():
        print(f"[飞书] 更新消息失败: {r.code}, {r.msg}")
    return r.success()


def _resolve_external_alert_open_id(alert):
    open_id = (alert.get("recipient_open_id") or alert.get("open_id") or "").strip()
    if open_id:
        return open_id
    target_id = (alert.get("target_id") or "").strip()
    if target_id:
        return (EXTERNAL_ALERT_TARGETS.get(target_id) or "").strip()
    return ""


def _extract_alert_location_text(alert):
    location = alert.get("location")
    if not location and isinstance(alert.get("details"), dict):
        location = alert["details"].get("location")
    if isinstance(location, str):
        return location.strip()
    if isinstance(location, dict):
        return str(location.get("location_text", "") or "").strip()
    return ""


def _format_external_alert(alert, explanation=None, explanation_source="", explanation_pending=False):
    locale = _alert_locale(alert)
    event_type = alert.get("event_type", "external_alert")
    sender_id = alert.get("sender_id", "unknown")
    timestamp = alert.get("timestamp", time.strftime("%Y-%m-%d %H:%M:%S"))
    severity = alert.get("severity", "warning")
    message = alert.get("message", "")
    details = alert.get("details")
    location_text = _extract_alert_location_text(alert)

    if locale == "en":
        lines = [
            "**Cross-device Alert**",
            f"Event type: `{event_type}`",
            f"Source device: `{sender_id}`",
            f"Severity: `{severity}`",
            f"Time: `{timestamp}`",
        ]
    else:
        lines = [
            "**跨设备告警通知**",
            f"事件类型: `{event_type}`",
            f"来源设备: `{sender_id}`",
            f"告警等级: `{severity}`",
            f"时间: `{timestamp}`",
        ]
    if location_text:
        lines.append(f"Location: `{location_text}`" if locale == "en" else f"定位: `{location_text}`")
    lines.extend(["", message])
    if explanation_pending:
        lines.extend(
            ["", "_HealthClaw is preparing an explanation for this alert. Please wait a moment..._"]
            if locale == "en"
            else ["", "_HealthClaw 正在补充这条告警的含义解读，请稍候..._"]
        )
    elif explanation:
        title = "**HealthClaw Interpretation**" if locale == "en" else "**HealthClaw 解读**"
        if explanation_source == "fallback_auth_invalid":
            title = "**HealthClaw Baseline Interpretation (LLM temporarily unavailable)**" if locale == "en" else "**HealthClaw 基础解读（LLM 暂不可用）**"
        elif explanation_source == "fallback":
            title = "**HealthClaw Baseline Interpretation**" if locale == "en" else "**HealthClaw 基础解读**"
        lines.extend(["", title, explanation.strip()])
        if explanation_source == "fallback_auth_invalid":
            lines.append(
                "_HealthClaw has automatically switched to rule-enhanced fallback interpretation and will return to live LLM generation once credentials recover._"
                if locale == "en"
                else "_当前已自动切换为规则增强解读，待 LLM 凭证恢复后会自动恢复实时生成。_"
            )
    if details:
        details_text = json.dumps(details, ensure_ascii=False, indent=2)
        lines.extend(["", f"```json\n{details_text}\n```"])
    return "\n".join(lines)


def _update_alert_explanation_async(message_id, alert):
    try:
        result = explain_alert_for_caregiver(alert)
        explanation_source = result.get("source", "")
        if result.get("error_kind") == "auth_invalid":
            explanation_source = "fallback_auth_invalid"
        content = _format_external_alert(
            alert,
            explanation=result.get("markdown", ""),
            explanation_source=explanation_source,
            explanation_pending=False,
        )
        if not update_message(message_id, content):
            print(f"[飞书] 告警解释更新失败: message_id={message_id}")
            return
        print(
            "[飞书] 告警解释已更新: "
            f"message_id={message_id}, source={result.get('source')}, model={result.get('model', '')}"
        )
    except Exception as e:
        print(f"[飞书] 告警解释生成失败: {e}")


def handle_external_alert(alert):
    if client is None:
        raise RuntimeError("Feishu client not initialized")

    open_id = _resolve_external_alert_open_id(alert)
    if not open_id:
        raise ValueError("missing recipient_open_id/open_id or unmapped target_id")

    if ENABLE_ALERT_EXPLAINER:
        _probe_alert_llm_auth_once()

    direct_result = None
    if ENABLE_ALERT_EXPLAINER and _alert_llm_state.get("auth_invalid"):
        direct_result = _build_direct_fallback_result(
            alert,
            error_text=_alert_llm_state.get("last_error", ""),
            source="fallback_auth_invalid",
        )

    content = _format_external_alert(
        alert,
        explanation=(direct_result or {}).get("markdown", ""),
        explanation_source=(direct_result or {}).get("source", ""),
        explanation_pending=ENABLE_ALERT_EXPLAINER and direct_result is None,
    )
    msg_id = send_message(open_id, content, use_card=True)
    if not msg_id:
        raise RuntimeError("failed to send Feishu alert")

    if ENABLE_ALERT_EXPLAINER and direct_result is None:
        threading.Thread(
            target=_update_alert_explanation_async,
            args=(msg_id, dict(alert)),
            daemon=True,
        ).start()

    return {
        "status": "delivered",
        "open_id": open_id,
        "message_id": msg_id,
        "event_type": alert.get("event_type", "external_alert"),
        "explanation_enqueued": ENABLE_ALERT_EXPLAINER and direct_result is None,
        "explanation_source": (direct_result or {}).get("source", "queued" if ENABLE_ALERT_EXPLAINER else "disabled"),
    }


def _create_meal_plan_async(open_id, text):
    try:
        message_id = send_message(open_id, "🥗 正在根据你的健康数据生成未来 30 天的饮食计划...", use_card=True)
        result = meal_plan_service.create_plan(open_id, text)
        content = meal_plan_service.format_plan_created_message(result["plan"])
        if message_id:
            if not update_message(message_id, content):
                send_message(open_id, content, use_card=True)
        else:
            send_message(open_id, content, use_card=True)
    except Exception as e:
        send_message(open_id, f"❌ 饮食计划创建失败: {e}")


def maybe_handle_meal_plan_message(open_id, text):
    action = detect_meal_plan_action(text)
    if not action:
        return False

    if action == "create":
        threading.Thread(target=_create_meal_plan_async, args=(open_id, text), daemon=True).start()
        return True

    if action == "pause":
        result = meal_plan_service.pause_user_plans(open_id)
        if result.get("paused_count", 0) > 0:
            send_message(open_id, f"⏸️ 已暂停 {result['paused_count']} 个饮食计划。")
        else:
            send_message(open_id, "当前没有可暂停的激活饮食计划。")
        return True

    if action == "status":
        plan = meal_plan_service.get_latest_user_plan(open_id)
        send_message(open_id, meal_plan_service.format_plan_status_message(plan), use_card=True)
        return True

    return False


def process_user_message(open_id, text):
    """统一处理来自 WebSocket 或轮询的用户消息"""
    if maybe_handle_meal_plan_message(open_id, text):
        return

    if text.startswith("/"):
        handle_command(open_id, text)
        return

    try:
        ensure_agent_ready()
    except Exception as e:
        send_message(
            open_id,
            "⚠️ 当前通用健康分析能力暂不可用，但跨设备告警和饮食计划功能仍可正常使用。\n"
            f"详细原因: {str(e)[:300]}",
        )
        return

    if open_id in user_tasks:
        print(f"[飞书] 用户 {open_id} 已有任务运行中，忽略")
        return

    print(f"[飞书] 处理消息 [{open_id}]: {text}")

    def run_agent():
        user_tasks[open_id] = {'running': True}
        try:
            msg_id = send_message(open_id, "🧠 思考中...", use_card=True)
            dq = agent.put_task(text, source='feishu')
            last_text = ""

            while user_tasks.get(open_id, {}).get('running', False):
                time.sleep(3)
                item = None
                try:
                    while True:
                        item = dq.get_nowait()
                except Q.Empty:
                    pass

                if item is None:
                    continue

                raw = item.get("done") or item.get("next", "")
                done = "done" in item
                show = _clean(raw)

                if len(show) > 3500:
                    cut = show[-3000:]
                    if cut.count('```') % 2 == 1:
                        cut = '```\n' + cut
                    msg_id = send_message(open_id, "(继续...)", use_card=True)
                    last_text = ""
                    show = cut

                display = show if done else show + " ⏳"
                if display != last_text and msg_id:
                    update_message(msg_id, display)
                    last_text = display

                if done:
                    break

            if not user_tasks.get(open_id, {}).get('running', True):
                send_message(open_id, "⏹️ 已停止")

        except Exception as e:
            import traceback
            print(f"[飞书] run_agent 异常: {e}")
            traceback.print_exc()
            send_message(open_id, f"❌ 错误: {str(e)[:500]}")
        finally:
            user_tasks.pop(open_id, None)

    threading.Thread(target=run_agent, daemon=True).start()


def handle_message(data):
    """WebSocket 事件回调"""
    global _ws_event_received
    try:
        _ws_event_received = True
        print(f"[飞书-WS] 收到事件 type={type(data).__name__}")

        message = data.event.message
        sender = data.event.sender
        open_id = sender.sender_id.open_id
        msg_type = message.message_type
        chat_type = getattr(message, 'chat_type', 'unknown')

        if chat_type == "group":
            mentions = getattr(message, 'mentions', None)
            if not mentions:
                return

        if ALLOWED_USERS and open_id not in ALLOWED_USERS:
            print(f"[飞书-WS] 未授权用户: {open_id}")
            return

        if msg_type != "text":
            send_message(open_id, "⚠️ 目前只支持文本消息")
            return

        text = json.loads(message.content).get("text", "").strip()
        text = re.sub(r'@_user_\d+\s*', '', text).strip()
        if not text:
            return

        print(f"[飞书-WS] 消息 [{open_id}]: {text}")
        process_user_message(open_id, text)

    except Exception as e:
        import traceback
        print(f"[飞书-WS] 处理异常: {e}")
        traceback.print_exc()


def handle_command(open_id, cmd):
    if cmd == "/stop":
        if agent is None:
            send_message(open_id, "当前没有可停止的通用分析任务。")
            return
        if open_id in user_tasks:
            user_tasks[open_id]['running'] = False
        agent.abort()
        send_message(open_id, "⏹️ 正在停止...")

    elif cmd == "/help":
        send_message(open_id, (
            "📖 HealthClaw 飞书 Bot 命令:\n"
            "/stop — 停止当前任务\n"
            "/status — 查看运行状态\n"
            "/restore — 恢复上次对话历史\n"
            "/new — 清除对话历史，开启新会话\n"
            "/help — 显示本帮助\n\n"
            "饮食计划示例：\n"
            "我想减肥，给我未来一个月的用餐计划\n"
            "查看我的饮食计划\n"
            "暂停饮食计划"
        ))

    elif cmd == "/status":
        if agent is None:
            status = "⚠️ 通用分析未初始化"
            llm_name = "不可用"
            if not agent_init_error:
                try:
                    ensure_agent_ready()
                except Exception:
                    pass
            details = f"\n原因: {agent_init_error[:300]}" if agent_init_error else ""
            send_message(open_id, f"状态: {status}\nLLM: {llm_name}{details}")
            return
        status = "🔴 运行中" if agent.is_running else "🟢 空闲"
        llm_name = agent.get_llm_name() if agent.llmclient else "未配置"
        send_message(open_id, f"状态: {status}\nLLM: {llm_name}")

    elif cmd == "/new":
        if agent is None:
            send_message(open_id, "当前通用分析未初始化，暂无会话可重置。")
            return
        agent.history.clear()
        if agent.handler:
            agent.handler.key_info = ""
        send_message(open_id, "🔄 已清除对话历史，开始新会话")

    elif cmd == "/restore":
        if agent is None:
            send_message(open_id, "当前通用分析未初始化，无法恢复历史对话。")
            return
        try:
            files = glob.glob('./temp/model_responses_*.txt')
            if not files:
                send_message(open_id, "❌ 没有找到历史记录")
                return
            latest = max(files, key=os.path.getmtime)
            with open(latest, 'r', encoding='utf-8') as f:
                content = f.read()
            users = re.findall(r'=== USER ===\n(.+?)(?==== |$)', content, re.DOTALL)
            resps = re.findall(r'=== Response ===.*?\n(.+?)(?==== Prompt|$)', content, re.DOTALL)
            count = 0
            for u, r in zip(users, resps):
                u, r = u.strip(), r.strip()[:500]
                if u and r:
                    agent.history.extend([f"[USER]: {u}", f"[Agent] {r}"])
                    count += 1
            agent.abort()
            send_message(open_id, f"✅ 已恢复 {count} 轮对话\n来源: {os.path.basename(latest)}")
        except Exception as e:
            send_message(open_id, f"❌ 恢复失败: {e}")

    else:
        send_message(open_id, f"❓ 未知命令: {cmd}\n输入 /help 查看可用命令")


class MealPlanScheduler:
    """Poll active meal plans and send due meal pushes."""

    def __init__(self, poll_interval=30):
        self.poll_interval = poll_interval
        self._running = False

    def start(self):
        self._running = True
        while self._running:
            try:
                if client is not None:
                    pushes = meal_plan_service.collect_due_pushes()
                    for push in pushes:
                        content = meal_plan_service.format_push_message(push)
                        msg_id = send_message(push["open_id"], content, use_card=True)
                        if msg_id:
                            artifact_result = send_meal_artifact_bundle(
                                push["open_id"], push.get("artifacts", {})
                            )
                            meal_plan_service.mark_push_sent(
                                push["plan_id"], push["date"], push["meal_key"], msg_id
                            )
                            print(
                                f"[MealPlan] push sent plan={push['plan_id']} "
                                f"date={push['date']} meal={push['meal_key']} "
                                f"artifacts={len(artifact_result)}"
                            )
            except Exception as e:
                print(f"[MealPlan] scheduler error: {e}")
            time.sleep(self.poll_interval)

    def stop(self):
        self._running = False


# ─── API 轮询回退 ──────────────────────────────────────────

class MessagePoller:
    """通过 IM API 轮询新消息，作为 WebSocket 事件的回退方案"""

    def __init__(self, poll_interval=3):
        self.poll_interval = poll_interval
        self.known_chats = {}
        self.processed_ids = set()
        self._token = None
        self._token_expire = 0
        self._running = False

    def _get_token(self):
        now = time.time()
        if self._token and now < self._token_expire:
            return self._token
        data = json.dumps({'app_id': APP_ID, 'app_secret': APP_SECRET}).encode()
        req = urllib.request.Request(
            'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal',
            data=data, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=10) as r:
            result = json.loads(r.read())
        self._token = result['tenant_access_token']
        self._token_expire = now + result.get('expire', 7200) - 60
        return self._token

    def _api_get(self, url):
        token = self._get_token()
        req = urllib.request.Request(url, headers={'Authorization': f'Bearer {token}'})
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())

    def discover_chat(self, open_id):
        """通过给用户发空消息获取 chat_id（实际用 list messages 接口发现）"""
        if open_id in self.known_chats:
            return self.known_chats[open_id]
        msg_id = send_message(open_id, _startup_online_text())
        if msg_id:
            try:
                result = self._api_get(
                    f'https://open.feishu.cn/open-apis/im/v1/messages/{msg_id}')
                chat_id = result.get('data', {}).get('items', [{}])[0].get('chat_id', '')
                if not chat_id:
                    msg_body = result.get('data', {})
                    chat_id = msg_body.get('items', [{}])[0].get('chat_id', '') if 'items' in msg_body else ''
            except Exception:
                chat_id = ''

            if not chat_id:
                token = self._get_token()
                data_body = json.dumps({
                    'receive_id': open_id,
                    'msg_type': 'text',
                    'content': json.dumps({"text": "..."})
                }).encode()
                req = urllib.request.Request(
                    'https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id',
                    data=data_body,
                    headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'})
                try:
                    with urllib.request.urlopen(req, timeout=10) as r:
                        resp = json.loads(r.read())
                        chat_id = resp.get('data', {}).get('chat_id', '')
                except Exception:
                    pass

            if chat_id:
                self.known_chats[open_id] = chat_id
                print(f"[飞书-Poll] 发现会话 {open_id} -> {chat_id}")
                return chat_id
        return None

    def discover_from_owner(self):
        """使用应用信息中的 owner_id 发现 P2P 会话"""
        try:
            result = self._api_get(
                f'https://open.feishu.cn/open-apis/application/v6/applications/{APP_ID}?lang={_feishu_application_lang()}')
            owner_id = result.get('data', {}).get('app', {}).get('owner', {}).get('owner_id', '')
            if owner_id:
                print(f"[飞书-Poll] 应用 Owner: {owner_id}")
                token = self._get_token()
                data_body = json.dumps({
                    'receive_id': owner_id,
                    'msg_type': 'text',
                    'content': json.dumps({"text": _startup_online_text(polling=True)})
                }).encode()
                req = urllib.request.Request(
                    'https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id',
                    data=data_body,
                    headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'})
                with urllib.request.urlopen(req, timeout=10) as r:
                    resp = json.loads(r.read())
                    chat_id = resp.get('data', {}).get('chat_id', '')
                    if chat_id:
                        self.known_chats[owner_id] = chat_id
                        print(f"[飞书-Poll] Owner 会话: {owner_id} -> {chat_id}")
                        return True
        except Exception as e:
            print(f"[飞书-Poll] 发现 Owner 会话失败: {e}")
        return False

    def poll_chat(self, chat_id):
        """拉取一个会话中的最近消息"""
        try:
            result = self._api_get(
                f'https://open.feishu.cn/open-apis/im/v1/messages'
                f'?container_id_type=chat&container_id={chat_id}&page_size=5&sort_type=ByCreateTimeDesc')
            return result.get('data', {}).get('items', [])
        except Exception as e:
            print(f"[飞书-Poll] 拉取消息失败: {e}")
            return []

    def start(self):
        self._running = True
        self.discover_from_owner()

        print(f"[飞书-Poll] 轮询启动，已知会话: {len(self.known_chats)} 个，间隔 {self.poll_interval}s")

        while self._running:
            try:
                if _ws_event_received:
                    print("[飞书-Poll] WebSocket 事件已激活，轮询退出")
                    return

                for open_id, chat_id in list(self.known_chats.items()):
                    messages = self.poll_chat(chat_id)
                    for msg in reversed(messages):
                        msg_id = msg.get('message_id', '')
                        if msg_id in self.processed_ids:
                            continue
                        self.processed_ids.add(msg_id)

                        sender = msg.get('sender', {})
                        if sender.get('sender_type') != 'user':
                            continue

                        sender_open_id = sender.get('id', '')
                        if ALLOWED_USERS and sender_open_id not in ALLOWED_USERS:
                            continue

                        msg_type = msg.get('msg_type', '')
                        if msg_type != 'text':
                            continue

                        body = msg.get('body', {})
                        content = body.get('content', '{}')
                        try:
                            text = json.loads(content).get('text', '').strip()
                        except (json.JSONDecodeError, TypeError):
                            text = ''
                        text = re.sub(r'@_user_\d+\s*', '', text).strip()
                        if not text:
                            continue

                        print(f"[飞书-Poll] 新消息 [{sender_open_id}]: {text}")
                        process_user_message(sender_open_id, text)

                # 限制 processed_ids 大小
                if len(self.processed_ids) > 500:
                    self.processed_ids = set(list(self.processed_ids)[-200:])

            except Exception as e:
                print(f"[飞书-Poll] 轮询异常: {e}")

            time.sleep(self.poll_interval)

    def stop(self):
        self._running = False


def main():
    global client, external_alert_server, meal_plan_scheduler
    import lark_oapi as lark

    if not APP_ID or not APP_SECRET:
        print("=" * 50)
        print("错误: 请在 mykey.py 中配置飞书凭证:")
        print("  fs_app_id = 'cli_xxxxx'")
        print("  fs_app_secret = 'xxxxx'")
        print("=" * 50)
        sys.exit(1)

    client = create_client()

    handler = lark.EventDispatcherHandler.builder("", "") \
        .register_p2_im_message_receive_v1(handle_message).build()

    ws_client = lark.ws.Client(
        APP_ID, APP_SECRET,
        event_handler=handler,
        log_level=lark.LogLevel.INFO
    )

    print("=" * 50)
    print("  🩺 Self-Evolving HealthClaw — 飞书 Bot")
    print(f"  App ID: {APP_ID}")
    print(f"  授权用户: {ALLOWED_USERS or '全部'}")
    print("  模式: WebSocket + 轮询回退")
    if ENABLE_EXTERNAL_ALERT_SERVER:
        print(f"  外部告警监听: http://{EXTERNAL_ALERT_HOST}:{EXTERNAL_ALERT_PORT}/external_alert")
    print("  等待消息...")
    print("=" * 50)

    if ENABLE_EXTERNAL_ALERT_SERVER:
        external_alert_server = CrossDeviceServer(
            host=EXTERNAL_ALERT_HOST,
            port=EXTERNAL_ALERT_PORT,
            node_id=NODE_ID,
            binding_file="memory/device_bindings.json",
            auth_token=EXTERNAL_ALERT_TOKEN,
            on_alert=handle_external_alert,
            log_func=print,
        ).start()

    meal_plan_scheduler = MealPlanScheduler(poll_interval=30)
    meal_plan_thread = threading.Thread(target=meal_plan_scheduler.start, daemon=True)
    meal_plan_thread.start()
    print("[MealPlan] scheduler started")

    # WebSocket 在后台启动
    def run_ws():
        try:
            ws_client.start()
        except Exception as e:
            print(f"[飞书-WS] WebSocket 异常: {e}")

    ws_thread = threading.Thread(target=run_ws, daemon=True)
    ws_thread.start()

    # 等待 WebSocket 连接，然后检查是否能收到事件
    time.sleep(8)

    if not _ws_event_received:
        print("[飞书] WebSocket 已连接但尚未收到事件，启动轮询回退...")
        poller = MessagePoller(poll_interval=3)
        poll_thread = threading.Thread(target=poller.start, daemon=True)
        poll_thread.start()
    else:
        print("[飞书] WebSocket 事件正常工作！")

    # 主线程保持运行
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        print("\n[飞书] 正在退出...")
        if meal_plan_scheduler is not None:
            meal_plan_scheduler.stop()
        if external_alert_server is not None:
            external_alert_server.stop()
        sys.exit(0)


if __name__ == "__main__":
    main()
