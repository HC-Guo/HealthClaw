"""
HealthClaw - 自进化个人健康管家 主入口
基于 SEDA 框架，支持医学诊断 + 健康管理双模式
支持 API / 本地模型 两种 LLM 后端
"""

import os, sys, threading, queue, time, json, re, random

if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
elif hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(errors="replace")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")
elif hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(errors="replace")
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agent_loop import agent_runner_loop, StepOutcome, BaseHandler
from ga import smart_format, format_error, reset_session_tracker
from ukb_handler import UKBAgentHandler, get_global_memory
from config import LLM_MODE, LOCAL_MODEL_CONFIG, AGENT_CONFIG, MEMORY_CONFIG


def _build_llm_sessions():
    """构建 LLM 会话列表，支持 API 和本地模型"""
    from sidercall import LLMSession, ToolClient, ClaudeSession, XaiSession

    llm_sessions = []

    if LLM_MODE == "local":
        cfg = LOCAL_MODEL_CONFIG
        if cfg["api_base"]:
            llm_sessions.append(
                LLMSession(
                    api_key=cfg.get("api_key", "not-needed"),
                    api_base=cfg["api_base"],
                    model=cfg["model_name"],
                )
            )
    else:
        try:
            from sidercall import SiderLLMSession, mykeys

            for k, cfg in mykeys.items():
                if not any(x in k for x in ["api", "config", "cookie"]):
                    continue
                try:
                    if "claude" in k:
                        llm_sessions.append(
                            ClaudeSession(
                                api_key=cfg["apikey"],
                                api_base=cfg["apibase"],
                                model=cfg["model"],
                            )
                        )
                    if "oai" in k:
                        llm_sessions.append(
                            LLMSession(
                                api_key=cfg["apikey"],
                                api_base=cfg["apibase"],
                                model=cfg["model"],
                                proxy=cfg.get("proxy"),
                                temperature=cfg.get("temperature"),
                            )
                        )
                    if "xai" in k:
                        llm_sessions.append(XaiSession(cfg, mykeys.get("proxy", "")))
                    if "sider" in k:
                        for m in ["gemini-3.0-flash", "claude-haiku-4.5", "kimi-k2"]:
                            llm_sessions.append(SiderLLMSession(cfg, default_model=m))
                except Exception:
                    pass
        except ImportError:
            pass

    return llm_sessions


# 浏览器/网络深度工具在普通模式与自主模式下均可用，不再限制为仅自主探索模式
AUTONOMOUS_ONLY_TOOLS = set()


def _load_tools_schema():
    """加载全量工具 schema（含网络工具），运行时按模式过滤"""
    schemas = []
    base_path = os.path.join(os.path.dirname(__file__), "assets", "tools_schema.json")
    ukb_path = os.path.join(
        os.path.dirname(__file__), "assets", "ukb_tools_schema.json"
    )
    bioinfo_path = os.path.join(
        os.path.dirname(__file__), "assets", "bioinfo_tools_schema.json"
    )
    wearable_path = os.path.join(
        os.path.dirname(__file__), "assets", "wearable_tools_schema.json"
    )

    with open(base_path, "r", encoding="utf-8") as f:
        ts = f.read()
        base = json.loads(ts if os.name == "nt" else ts.replace("powershell", "bash"))

    base_keep = [
        "code_run",
        "file_read",
        "file_patch",
        "file_write",
        "update_working_checkpoint",
        "ask_user",
        "start_long_term_update",
        "web_scan",
        "web_execute_js",
    ]
    for t in base:
        if t["function"]["name"] in base_keep:
            schemas.append(t)

    if os.path.exists(ukb_path):
        with open(ukb_path, "r", encoding="utf-8") as f:
            ukb_tools = json.load(f)
        schemas.extend(ukb_tools)

    if os.path.exists(bioinfo_path):
        with open(bioinfo_path, "r", encoding="utf-8") as f:
            bioinfo_tools = json.load(f)
        schemas.extend(bioinfo_tools)

    if os.path.exists(wearable_path):
        with open(wearable_path, "r", encoding="utf-8") as f:
            wearable_tools = json.load(f)
        schemas.extend(wearable_tools)

    health_path = os.path.join(
        os.path.dirname(__file__), "assets", "health_tools_schema.json"
    )
    if os.path.exists(health_path):
        with open(health_path, "r", encoding="utf-8") as f:
            health_tools = json.load(f)
        schemas.extend(health_tools)

    return schemas


_BROWSER_TOOLS_BLACKLIST = {
    "browser_navigate",
    "browser_click",
    "browser_get_content",
    "browser_back",
    "browser_scroll",
    "browser_search",
}


def _filter_tools_for_mode(all_tools, autonomous=False):
    """普通模式使用全量工具；自主模式排除篡改猴浏览器工具（避免后台卡死）"""
    exclude = AUTONOMOUS_ONLY_TOOLS
    if autonomous:
        exclude = exclude | _BROWSER_TOOLS_BLACKLIST
    return [t for t in all_tools if t["function"]["name"] not in exclude]


# ============ 记忆自动提取 + SOP 自学习 ============
_MEMORY_TRIGGER_KEYWORDS = [
    "过敏",
    "慢病",
    "确诊",
    "用药",
    "停药",
    "家族",
    "手术",
    "住院",
    "怀孕",
    "哺乳",
    "体重",
    "身高",
    "血型",
    "糖尿病",
    "高血压",
    "心脏",
    "肝",
    "肾",
    "甲状腺",
]

SOP_LEARN_MIN_TURNS = 6
SOP_LEARN_MAX_FAILURES = 1


def _should_extract_memory(query, turn_count):
    min_turns = MEMORY_CONFIG.get("auto_extract_min_turns", 4)
    if turn_count >= min_turns:
        return True
    return any(kw in query for kw in _MEMORY_TRIGGER_KEYWORDS)


def _should_learn_sop(turn_count, tracker):
    """≥6 轮且失败 ≤1 次的成功对话，触发 SOP 自学习"""
    if turn_count < SOP_LEARN_MIN_TURNS:
        return False
    failure_count = len(tracker.failures) if tracker else 999
    return failure_count <= SOP_LEARN_MAX_FAILURES


def _build_workflow_summary(tracker):
    """从 SessionTracker 构建工作流摘要（零 LLM 成本）"""
    if not tracker or not tracker.turn_summaries:
        return ""
    lines = []
    for t in tracker.turn_summaries:
        status = "OK" if t.get("success") else "FAIL"
        lines.append(f"  Turn {t['turn']}: [{status}] {t['tool']} — {t['brief']}")
    return "\n".join(lines)


def _save_sop(title, content):
    """写入 L3 SOP 文件并追加 L1 索引引用"""
    slug = re.sub(r"[^\w\u4e00-\u9fff]+", "_", title).strip("_").lower()
    if not slug:
        slug = f"auto_sop_{int(time.time())}"
    filename = f"{slug}_sop.md"
    sop_path = os.path.join("memory", "L3_sops", filename)

    os.makedirs(os.path.dirname(sop_path), exist_ok=True)
    with open(sop_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[SOPLearn] SOP saved: {sop_path}")

    l1_path = "memory/L1_disease_insight.txt"
    if os.path.exists(l1_path):
        try:
            with open(l1_path, "r", encoding="utf-8") as f:
                l1 = f.read()
            ref_line = f"{title}→sop:{filename.replace('.md','')}"
            if ref_line not in l1 and filename not in l1:
                marker = "## [HEALTH_MANAGEMENT]"
                if marker in l1:
                    idx = l1.index(marker)
                    section_end = l1.find("\n## [", idx + len(marker))
                    if section_end == -1:
                        section_end = len(l1)
                    insert_pos = l1.rfind("\n", idx, section_end) + 1
                    if insert_pos <= idx:
                        insert_pos = section_end
                    l1 = l1[:insert_pos] + ref_line + "\n" + l1[insert_pos:]
                    with open(l1_path, "w", encoding="utf-8") as f:
                        f.write(l1)
                    print(f"[SOPLearn] L1 index updated: {ref_line}")
        except Exception as e:
            print(f"[SOPLearn] L1 update failed (non-critical): {e}")

    return sop_path


def _post_task_memory_extract(
    llmclient, user_query, agent_response, turn_count, tracker=None
):
    """后处理记忆提取 + SOP 自学习。对话结束后用一次 LLM 调用同时完成：
    1. 提取用户画像信息（profile_updates）
    2. 如果满足 SOP 学习条件（≥6轮+少失败），同时提取可复用工作流 SOP
    """
    try:
        if not _should_extract_memory(user_query, turn_count):
            return
        if not llmclient or not agent_response:
            return

        from tools.health_data_store import HealthDataStore

        store = HealthDataStore()
        store.append_conversation_log(user_query, agent_response[:500], turn_count)

        learn_sop = _should_learn_sop(turn_count, tracker)
        workflow = _build_workflow_summary(tracker) if learn_sop else ""

        extract_prompt = (
            "从以下对话中提取值得记忆的信息。只输出 JSON，无其他内容。\n"
            "格式:\n"
            "{\n"
            '  "profile_updates": [{"field": "...", "action": "append", "data": ...}],\n'
            '  "key_facts": ["..."]\n'
        )
        if learn_sop:
            extract_prompt += (
                '  ,"sop": {"title": "简短中文标题", "content": "markdown格式的SOP内容"}\n'
                "  // sop 字段：如果本次对话包含一个可复用的多步工作流，将其总结为 SOP。\n"
                "  // 如果不值得固化（纯问答/流程太简单），sop 设为 null。\n"
                "  // SOP 应包含：适用场景、步骤、每步用什么工具、注意事项。\n"
            )
        extract_prompt += (
            "}\n"
            "可提取的 profile 字段: allergies, chronic_diseases, medications, family_history, basic_info, health_goals\n"
            "如果无有价值信息，profile_updates 和 key_facts 设为空数组。\n\n"
            f"用户: {user_query[:500]}\n"
            f"助手: {agent_response[:1500]}\n"
        )
        if learn_sop and workflow:
            extract_prompt += f"\n执行轨迹 ({turn_count} 轮):\n{workflow}\n"

        try:
            max_tokens = 1200 if learn_sop else 500
            result_text = llmclient.ask_block(extract_prompt, max_tokens=max_tokens)
            if not result_text:
                return
            json_match = re.search(r"\{.*\}", result_text, re.DOTALL)
            if not json_match:
                return
            extracted = json.loads(json_match.group())

            for update in extracted.get("profile_updates", []):
                field = update.get("field", "")
                action = update.get("action", "append")
                data = update.get("data")
                if field and data:
                    store.update_profile_field(field, action, data)
                    print(f"[MemoryExtract] Profile updated: {field} ({action})")

            facts = extracted.get("key_facts", [])
            if facts:
                print(f"[MemoryExtract] Key facts: {facts}")

            sop_data = extracted.get("sop")
            if sop_data and isinstance(sop_data, dict) and sop_data.get("content"):
                title = sop_data.get("title", "自动学习SOP")
                content = sop_data["content"]
                if not content.startswith("#"):
                    content = f"# {title}\n\n{content}"
                content += f"\n\n---\n*自动学习于 {time.strftime('%Y-%m-%d')}，基于 {turn_count} 轮对话*\n"
                _save_sop(title, content)

        except Exception as e:
            print(f"[MemoryExtract] LLM call failed (non-critical): {e}")
    except Exception as e:
        print(f"[MemoryExtract] Error (non-critical): {e}")


def get_system_prompt(autonomous=False, user_query=""):
    """构建系统提示词 = 基础角色 + 日期 + 全局记忆 (+ 自主模式指令)"""
    if not os.path.exists("memory"):
        os.makedirs("memory")
    for sub in ["L3_sops", "L3_scripts", "L4_episodes"]:
        p = os.path.join("memory", sub)
        if not os.path.exists(p):
            os.makedirs(p)

    if not os.path.exists("memory/L2_global_facts.txt"):
        with open("memory/L2_global_facts.txt", "w", encoding="utf-8") as f:
            f.write(
                "## [UKB_DATA_PATHS]\n\n## [POPULATION_STATS]\n\n## [ANALYSIS_CONFIGS]\n"
            )

    insight_path = "memory/L1_disease_insight.txt"
    if not os.path.exists(insight_path):
        tpl = "assets/L1_disease_insight_template.txt"
        if os.path.exists(tpl):
            content = open(tpl, encoding="utf-8").read()
        else:
            content = "# Disease-Tool Index\n## [HIGH-FREQ MAPPING]\n\n## [LOW-FREQ KEYWORDS]\n\n## [RULES]\n"
        with open(insight_path, "w", encoding="utf-8") as f:
            f.write(content)

    with open("assets/sys_prompt.txt", "r", encoding="utf-8") as f:
        prompt = f.read()

    if not autonomous:
        prompt = _strip_autonomous_section(prompt)
        prompt += "\n[模式] 健康管家模式\n"
        prompt += "可用网络工具：web_search、browser_navigate/click/get_content/search、browse_and_learn、code_run。浏览器能力依赖篡改猴+TMWebDriver（web_scan/web_execute_js），需按 web_setup_sop 配置。\n"
    else:
        prompt += "\n[模式] 🌐 自主探索模式 — 网络搜索和自主学习工具已启用。"
        prompt += "\n你可以主动搜索文献、学习新知识并写入记忆。"
        prompt += "\n推荐流程："
        prompt += "\n  1. web_search 定位高质量资源 → 获取 URL"
        prompt += "\n  2. browse_and_learn(url/topic) 深度阅读 + 提炼（不依赖篡改猴）"
        prompt += "\n  3. 有价值的知识 → file_patch/file_write 写入 L1/L2/L3 记忆"
        prompt += "\n⚠️ 禁止在自主探索模式中使用 browser_navigate/browser_click/browser_search/browser_get_content 等篡改猴工具，"
        prompt += "它们依赖浏览器连接，在后台运行时会导致卡死。\n"

    prompt += f"\nToday: {time.strftime('%Y-%m-%d %a')}\n"
    prompt += get_global_memory(user_query=user_query)
    return prompt


def _strip_autonomous_section(text):
    """从系统提示中移除'自主学习模式'段落"""
    lines = text.split("\n")
    result = []
    skip = False
    for line in lines:
        if line.strip().startswith("## 自主学习模式"):
            skip = True
            continue
        if skip and line.strip().startswith("## "):
            skip = False
        if not skip:
            result.append(line)
    return "\n".join(result)


class HealthClawAgent:
    """HealthClaw 个人健康管家 主类（兼容 DiagnosisAgent）"""

    def __init__(self):
        if not os.path.exists("temp"):
            os.makedirs("temp")

        llm_sessions = _build_llm_sessions()
        if llm_sessions:
            from sidercall import ToolClient

            self.llmclient = ToolClient(llm_sessions, auto_save_tokens=True)
        else:
            self.llmclient = None
            print("[WARN] No LLM backend configured. Set SEDA_LLM_MODE and keys.")

        self.tools_schema_all = _load_tools_schema()
        self.lock = threading.Lock()
        self.history = []
        self.task_queue = queue.Queue()
        self.is_running = False
        self.stop_sig = False
        self.llm_no = 0
        self.inc_out = False
        self.handler = None
        self.verbose = True
        self.autonomous_mode = False
        self.auto_explore_enabled = False
        self.last_task_time = time.time()
        # 是否允许当前会话在任务结束后执行长期记忆更新（start_long_term_update + 后处理抽取）
        # 由前端（如 Streamlit）或上层应用控制，默认开启以保持既有行为
        self.enable_long_term_memory = True

        print(
            "[HealthClaw] Playwright browser will initialize on first use (lazy, thread-safe)"
        )

    def next_llm(self, n=-1):
        self.llm_no = ((self.llm_no + 1) if n < 0 else n) % len(self.llmclient.backends)
        self.llmclient.last_tools = ""

    def list_llms(self):
        return [
            (i, f"{type(b).__name__}/{b.default_model}", i == self.llm_no)
            for i, b in enumerate(self.llmclient.backends)
        ]

    def get_llm_name(self):
        b = self.llmclient.backends[self.llm_no]
        return f"{type(b).__name__}/{b.default_model}"

    def abort(self):
        print("Abort current task...")
        if not self.is_running:
            return
        self.stop_sig = True
        if self.handler is not None:
            self.handler.code_stop_signal.append(1)

    def put_task(self, query, source="user", image_base64=None):
        display_queue = queue.Queue()
        self.task_queue.put(
            {
                "query": query,
                "source": source,
                "output": display_queue,
                "image": image_base64,
                "autonomous": self.autonomous_mode,
                "enable_long_term_memory": self.enable_long_term_memory,
            }
        )
        return display_queue

    def run(self):
        while True:
            task = self.task_queue.get()
            self.is_running = True
            raw_query = task["query"]
            source = task["source"]
            display_queue = task["output"]
            task_image = task.get("image")
            task_autonomous = task.get("autonomous", False)
            task_enable_long_term = task.get("enable_long_term_memory", True)
            rquery = smart_format(raw_query.replace("\n", " "), max_str_len=200)
            self.history.append(
                f"[USER]: {rquery}" + (" [+图片]" if task_image else "")
            )

            sys_prompt = get_system_prompt(
                autonomous=task_autonomous, user_query=raw_query
            )
            tools = _filter_tools_for_mode(
                self.tools_schema_all, autonomous=task_autonomous
            )
            reset_session_tracker()
            handler = UKBAgentHandler(
                None, self.history, "./temp", autonomous=task_autonomous
            )
            # 将前端传入的长期记忆开关下沉到具体会话 handler，控制 start_long_term_update 等工具的行为
            setattr(handler, "enable_long_term_memory", task_enable_long_term)
            if self.handler and self.handler.key_info:
                handler.key_info = self.handler.key_info
                if "清除工作记忆" not in handler.key_info:
                    handler.key_info += (
                        "\n[SYSTEM] 如果是新任务，请先更新或清除工作记忆\n"
                    )
            self.handler = handler
            self.llmclient.backend = self.llmclient.backends[self.llm_no]

            max_turns = AGENT_CONFIG.get("max_turns", 40)
            if task_autonomous:
                max_turns = min(max(max_turns, 20), 25)

            user_input = raw_query
            if source == "feishu" and len(self.history) > 1:
                user_input = (
                    handler._get_anchor_prompt() + f"\n\n### 用户当前消息\n{raw_query}"
                )

            gen = agent_runner_loop(
                self.llmclient,
                sys_prompt,
                user_input,
                handler,
                tools,
                max_turns=max_turns,
                verbose=self.verbose,
                image_base64=task_image,
            )

            full_resp = ""
            try:
                last_pos = 0
                for chunk in gen:
                    if self.stop_sig:
                        break
                    full_resp += chunk
                    if len(full_resp) - last_pos > 50:
                        display_queue.put(
                            {
                                "next": (
                                    full_resp[last_pos:] if self.inc_out else full_resp
                                ),
                                "source": source,
                            }
                        )
                        last_pos = len(full_resp)
                if self.inc_out and last_pos < len(full_resp):
                    display_queue.put({"next": full_resp[last_pos:], "source": source})
                if "</summary>" in full_resp:
                    full_resp = full_resp.replace("</summary>", "</summary>\n\n")
                display_queue.put({"done": full_resp, "source": source})
                self.history = handler.history_info
            except Exception as e:
                print(f"Backend Error: {format_error(e)}")
                display_queue.put(
                    {
                        "done": full_resp + f"\n```\n{format_error(e)}\n```",
                        "source": source,
                    }
                )
            finally:
                self.is_running = self.stop_sig = False
                self.last_task_time = time.time()
                self.task_queue.task_done()
                if self.handler is not None:
                    self.handler.code_stop_signal.append(1)
                    # 若当前任务关闭了长期记忆功能，则跳过后处理记忆抽取，避免在短对话/调试时污染长期记忆
                    if getattr(self.handler, "enable_long_term_memory", True):
                        _post_task_memory_extract(
                            self.llmclient,
                            raw_query,
                            full_resp,
                            self.handler._current_turn,
                            tracker=self.handler.tracker,
                        )


DiagnosisAgent = HealthClawAgent  # backward compat


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="HealthClaw - 个人健康管家")
    parser.add_argument("--llm_no", type=int, default=0, help="LLM 后端编号")
    parser.add_argument(
        "--batch", metavar="FILE", help="批量模式: 从 JSONL 文件读取患者任务"
    )
    parser.add_argument("--verbose", action="store_true", default=False)
    args = parser.parse_args()

    agent = HealthClawAgent()
    agent.llm_no = args.llm_no
    agent.verbose = args.verbose
    threading.Thread(target=agent.run, daemon=True).start()

    if args.batch:
        import jsonlines

        results = []
        with jsonlines.open(args.batch) as reader:
            for task in reader:
                dq = agent.put_task(task["query"], source="batch")
                while "done" not in (item := dq.get(timeout=300)):
                    pass
                results.append({"query": task["query"], "response": item["done"]})
        out_path = args.batch.replace(".jsonl", "_results.jsonl")
        with jsonlines.open(out_path, mode="w") as writer:
            for r in results:
                writer.write(r)
        print(f"Results saved to {out_path}")
    else:
        agent.inc_out = True
        print("=" * 60)
        print("  HealthClaw - 个人健康管家")
        print("  示例:")
        print("  > 帮我看看这个体检报告")
        print("  > 我血糖 6.8 正常吗")
        print("  > 我爸有糖尿病，我需要注意什么")
        print("=" * 60)
        while True:
            q = input("SEDA> ").strip()
            if not q:
                continue
            if q.lower() in ("quit", "exit"):
                break
            try:
                dq = agent.put_task(q, source="user")
                while True:
                    item = dq.get()
                    if "next" in item:
                        print(item["next"], end="", flush=True)
                    if "done" in item:
                        print()
                        break
            except KeyboardInterrupt:
                agent.abort()
                print("\n[Interrupted]")
