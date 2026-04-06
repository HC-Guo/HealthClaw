import sys, os, re, json, time, threading
from datetime import datetime
from pathlib import Path
import tempfile, traceback, subprocess, itertools, collections

if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agent_loop import BaseHandler, StepOutcome, try_call_generator

from tools.one_click_health import (
    check_one_click_main_sop_file_patch_allowed,
    check_one_click_main_sop_file_write_allowed,
)


class SessionTracker:
    """追踪单次 agent 会话的失败记录、自主决策、轮次摘要、证据引用链，用于生成 session report 和审计回放"""

    def __init__(self):
        self.failures = []
        self.autonomous_decisions = []
        self.turn_summaries = []
        self.citations = []
        self.task_goal = ""
        self.start_time = datetime.now()
        self.total_turns = 0

    def record_failure(self, tool_name, args_summary, error_msg, turn):
        self.failures.append(
            {
                "turn": turn,
                "tool": tool_name,
                "args": str(args_summary)[:200],
                "error": str(error_msg)[:300],
                "time": datetime.now().strftime("%H:%M:%S"),
            }
        )

    def record_decision(self, question, chosen, alternatives, reason, turn):
        self.autonomous_decisions.append(
            {
                "turn": turn,
                "question": str(question)[:200],
                "chosen": str(chosen)[:100],
                "alternatives": str(alternatives)[:200],
                "reason": reason,
                "time": datetime.now().strftime("%H:%M:%S"),
            }
        )

    def record_turn(self, turn, tool_name, success, brief):
        self.turn_summaries.append(
            {
                "turn": turn,
                "tool": tool_name,
                "success": success,
                "brief": str(brief)[:150],
            }
        )

    def record_citation(
        self,
        turn,
        conclusion,
        evidence_tier,
        source,
        citation_snippet="",
        tool_chain=None,
        sop_used="",
        evidence_level_override="",
    ):
        """记录一条证据引用到审计链，用于审计回放和可复现性追溯。

        Args:
            turn: 当前轮次
            conclusion: 得出的结论（≤200字）
            evidence_tier: 证据等级 T1-T6
            source: 来源描述（指南名/PMID/说明书等）
            citation_snippet: 原文引用片段（≤200字）
            tool_chain: 使用的工具调用链
            sop_used: 引用的 SOP 名称
            evidence_level_override: 覆盖默认引用档位 (strict/standard/relaxed)
        """
        self.citations.append(
            {
                "turn": turn,
                "conclusion": str(conclusion)[:200],
                "evidence_tier": str(evidence_tier),
                "source": str(source)[:300],
                "citation_snippet": str(citation_snippet)[:200],
                "tool_chain": tool_chain or [],
                "sop_used": sop_used,
                "level_override": evidence_level_override,
                "time": datetime.now().strftime("%H:%M:%S"),
            }
        )

    def get_citation_summary(self):
        """返回证据引用链摘要，用于审计回放"""
        if not self.citations:
            return ""
        lines = ["**证据引用链：**"]
        for c in self.citations:
            tier = c["evidence_tier"]
            lines.append(
                f"  - Turn {c['turn']}: [{tier}] {c['source'][:80]} → \"{c['conclusion'][:60]}\""
            )
            if c.get("citation_snippet"):
                lines.append(f"    引用: \"{c['citation_snippet'][:80]}...\"")
        return "\n".join(lines)

    def get_failure_summary(self):
        if not self.failures:
            return ""
        lines = ["**近期失败记录：**"]
        for f in self.failures[-3:]:
            lines.append(f"  - Turn {f['turn']}: `{f['tool']}` → {f['error'][:100]}")
        return "\n".join(lines)

    def export_audit_json(self):
        """导出完整审计数据为 JSON，支持外部系统消费"""
        return {
            "task_goal": self.task_goal,
            "start_time": self.start_time.isoformat(),
            "total_turns": self.total_turns,
            "citations": self.citations,
            "tool_trace": self.turn_summaries,
            "failures": self.failures,
            "decisions": self.autonomous_decisions,
        }

    def generate_report(self):
        elapsed = (datetime.now() - self.start_time).total_seconds()
        lines = [
            f"# Session Report",
            f"- **时间**: {self.start_time.strftime('%Y-%m-%d %H:%M')} ~ {datetime.now().strftime('%H:%M')} ({elapsed:.0f}s)",
            f"- **总轮次**: {self.total_turns}",
            f"- **任务目标**: {self.task_goal or '(未记录)'}",
            "",
        ]
        if self.turn_summaries:
            lines.append("## 执行轨迹")
            for t in self.turn_summaries:
                status = "✅" if t["success"] else "❌"
                lines.append(
                    f"- Turn {t['turn']}: {status} `{t['tool']}` — {t['brief']}"
                )
            lines.append("")

        if self.citations:
            tier_counts = collections.Counter(
                c["evidence_tier"] for c in self.citations
            )
            tier_summary = ", ".join(f"{k}:{v}" for k, v in sorted(tier_counts.items()))
            lines.append(f"## 证据引用链 ({len(self.citations)} 条, {tier_summary})")
            for c in self.citations:
                tier = c["evidence_tier"]
                tools = " → ".join(c["tool_chain"]) if c["tool_chain"] else "(直接推理)"
                lines.append(
                    f"- **Turn {c['turn']}** [{c['time']}]: [{tier}] {c['source']}"
                )
                lines.append(f"  - 结论: {c['conclusion']}")
                if c.get("citation_snippet"):
                    lines.append(f"  - 引用: \"{c['citation_snippet']}\"")
                lines.append(f"  - 工具链: {tools}")
                if c.get("sop_used"):
                    lines.append(f"  - SOP: {c['sop_used']}")
            lines.append("")

        if self.failures:
            lines.append(f"## 失败记录 ({len(self.failures)} 次)")
            for f in self.failures:
                lines.append(f"- **Turn {f['turn']}** [{f['time']}] `{f['tool']}`")
                lines.append(f"  - 参数: {f['args']}")
                lines.append(f"  - 错误: {f['error']}")
            lines.append("")

        if self.autonomous_decisions:
            lines.append(f"## 自主决策 ({len(self.autonomous_decisions)} 次)")
            for d in self.autonomous_decisions:
                lines.append(f"- **Turn {d['turn']}** [{d['time']}]: {d['question']}")
                lines.append(f"  - 选择: {d['chosen']}")
                lines.append(f"  - 备选: {d['alternatives']}")
                lines.append(f"  - 理由: {d['reason']}")
            lines.append("")

        if not self.failures and not self.autonomous_decisions and not self.citations:
            lines.append("## 本次会话无失败、自主决策或证据引用记录\n")

        return "\n".join(lines)

    def save_report(self, base_dir="."):
        report_dir = os.path.join(base_dir, "temp", "session_reports")
        os.makedirs(report_dir, exist_ok=True)
        filename = f"report_{self.start_time.strftime('%Y%m%d_%H%M%S')}.md"
        path = os.path.join(report_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.generate_report())
        print(f"[SessionTracker] Report saved: {path}")
        return path


_session_tracker = SessionTracker()


def get_session_tracker():
    return _session_tracker


def reset_session_tracker():
    global _session_tracker
    _session_tracker = SessionTracker()
    return _session_tracker


def code_run(
    code, code_type="python", timeout=60, cwd=None, code_cwd=None, stop_signal=[]
):
    """代码执行器
    python: 运行复杂的 .py 脚本（文件模式）
    powershell/bash: 运行单行指令（命令模式）
    优先使用python，仅在必要系统操作时使用powershell。
    """
    preview = (code[:60].replace("\n", " ") + "...") if len(code) > 60 else code.strip()
    yield f"[Action] Running {code_type} in {os.path.basename(cwd)}: {preview}\n"
    cwd = cwd or os.path.join(os.getcwd(), "temp")
    tmp_path = None
    if code_type == "python":
        tmp_file = tempfile.NamedTemporaryFile(
            suffix=".ai.py", delete=False, mode="w", encoding="utf-8", dir=code_cwd
        )
        tmp_file.write(code)
        tmp_path = tmp_file.name
        tmp_file.close()
        cmd = [sys.executable, "-X", "utf8", "-u", tmp_path]
    elif code_type in ["powershell", "bash"]:
        if os.name == "nt":
            cmd = ["powershell", "-NoProfile", "-NonInteractive", "-Command", code]
        else:
            cmd = ["bash", "-c", code]
    else:
        return {"status": "error", "msg": f"不支持的类型: {code_type}"}
    print("code run output:")
    startupinfo = None
    if os.name == "nt":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0  # SW_HIDE
    full_stdout = []

    def stream_reader(proc, logs):
        for line_bytes in iter(proc.stdout.readline, b""):
            try:
                line = line_bytes.decode("utf-8")
            except UnicodeDecodeError:
                line = line_bytes.decode("gbk", errors="ignore")
            logs.append(line)
            try:
                print(line, end="")
            except:
                pass

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,
            cwd=cwd,
            startupinfo=startupinfo,
        )
        start_t = time.time()
        t = threading.Thread(
            target=stream_reader, args=(process, full_stdout), daemon=True
        )
        t.start()

        while t.is_alive():
            istimeout = time.time() - start_t > timeout
            if istimeout or len(stop_signal) > 0:
                process.kill()
                print("[Debug] Process killed due to timeout or stop signal.")
                if istimeout:
                    full_stdout.append("\n[Timeout Error] 超时强制终止")
                else:
                    full_stdout.append("\n[Stopped] 用户强制终止")
                break
            time.sleep(1)

        t.join(timeout=1)
        exit_code = process.poll()

        stdout_str = "".join(full_stdout)
        status = "success" if exit_code == 0 else "error"
        status_icon = "✅" if exit_code == 0 else "❌"
        if exit_code is None:
            status_icon = "⏳"
        output_snippet = smart_format(
            stdout_str, max_str_len=600, omit_str="\n[omitted long output]\n"
        )
        yield f"[Status] {status_icon} Exit Code: {exit_code}\n[Stdout]\n{output_snippet}\n"
        if process.stdout:
            threading.Thread(target=process.stdout.close, daemon=True).start()
        return {
            "status": status,
            "stdout": smart_format(
                stdout_str, max_str_len=8000, omit_str="\n[omitted long output]\n"
            ),
            "exit_code": exit_code,
        }
    except Exception as e:
        if "process" in locals():
            process.kill()
        return {"status": "error", "msg": str(e)}
    finally:
        if code_type == "python" and tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


def ask_user(question: str, candidates: list = None):
    """question: 向用户提出的问题。candidates: 可选的候选项列表。需要保证should_exit为True"""
    return {
        "status": "INTERRUPT",
        "intent": "HUMAN_INTERVENTION",
        "data": {"question": question, "candidates": candidates or []},
    }


from simphtml import execute_js_rich, get_html
import threading as _threading

driver = None
_driver_lock = _threading.Lock()
_driver_ready = _threading.Event()


_cdp_tid = None


def ensure_cdp_config():
    """确保 CDP 桥的 config.js 存在，首次调用时自动生成 TID 密钥"""
    global _cdp_tid
    config_path = os.path.join(
        os.path.dirname(__file__), "assets", "tmwd_cdp_bridge", "config.js"
    )
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            content = f.read()
        m = re.search(r"const TID\s*=\s*'([^']+)'", content)
        if m:
            _cdp_tid = m.group(1)
            return _cdp_tid
    import secrets

    tid = "__ljq_ctrl_" + secrets.token_hex(4)
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with open(config_path, "w") as f:
        f.write(f"const TID = '{tid}';\n")
    print(f"[CDP Bridge] Generated config.js with TID={tid}")
    _cdp_tid = tid
    return tid


_cdp_available = None
_cdp_last_check = 0


def _cdp_send_cmd(tid, cmd_json):
    """向页面注入 CDP 命令 DOM 元素（同步，不依赖 Promise）"""
    js_payload = json.dumps(cmd_json, ensure_ascii=False)
    inject_js = f"""
(function() {{
  var TID = '{tid}';
  var old = document.getElementById(TID);
  if (old) old.remove();
  var el = document.createElement('div');
  el.id = TID; el.style.display = 'none';
  el.textContent = JSON.stringify({js_payload});
  document.body.appendChild(el);
  return 'injected';
}})()
"""
    return web_execute_js(inject_js)


def _cdp_read_response(tid):
    """读取 CDP 桥写回到 DOM 元素的响应（同步）"""
    read_js = f"""
(function() {{
  var el = document.getElementById('{tid}');
  if (!el) return 'GONE';
  return el.textContent;
}})()
"""
    result = web_execute_js(read_js)
    if result.get("status") != "success":
        return None
    return result.get("js_return") or result.get("data")


def _cdp_poll(tid, timeout=6, interval=0.3):
    """Python 端轮询 DOM 元素，等待 CDP 桥写回响应"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(interval)
        raw = _cdp_read_response(tid)
        if raw is None or raw == "GONE":
            return {"ok": False, "error": "CDP element removed from DOM"}
        try:
            parsed = json.loads(raw)
            if parsed.get("ok") is not None or parsed.get("error"):
                return parsed
        except (json.JSONDecodeError, TypeError, ValueError):
            pass
    return {"ok": False, "error": f"CDP timeout ({timeout}s)"}


def is_cdp_available(force=False):
    """快速探测 CDP 桥扩展是否可用（2 秒超时，结果缓存 60 秒）。
    使用 Python 端轮询（TMWebDriver 不支持 Promise 返回值）。"""
    global _cdp_available, _cdp_last_check
    now = time.time()
    if not force and _cdp_available is not None and now - _cdp_last_check < 60:
        return _cdp_available
    ok, err = _ensure_driver_ready(timeout=3)
    if not ok:
        _cdp_available = False
        _cdp_last_check = now
        return False
    tid = _cdp_tid or ensure_cdp_config()
    inject_result = _cdp_send_cmd(tid, {"cmd": "tabs"})
    if (
        inject_result.get("status") != "success"
        or inject_result.get("js_return") != "injected"
    ):
        _cdp_available = False
        _cdp_last_check = now
        print("[CDP Bridge] 探测失败: 无法注入命令到页面")
        return False
    resp = _cdp_poll(tid, timeout=2, interval=0.2)
    _cdp_available = resp.get("ok", False) is not False and "error" not in resp
    _cdp_last_check = now
    if not _cdp_available:
        print(
            f"[CDP Bridge] 探测失败: {resp.get('error', '扩展未安装或 Service Worker 无效')}"
        )
    else:
        print("[CDP Bridge] 探测成功: 扩展可用")
    return _cdp_available


def cdp_execute(cmd_json, timeout=6):
    """通过 TMWebDriver 向 CDP 桥发送命令并等待响应。
    使用 Python 端轮询替代 JS Promise（TMWebDriver 不支持 Promise 返回值）。
    cmd_json: dict, e.g. {cmd:'cdp', method:'Page.captureScreenshot', params:{format:'png'}}
    """
    if not is_cdp_available():
        return {
            "ok": False,
            "error": "CDP 桥不可用。请检查: chrome://extensions/ 中 TMWD CDP Bridge 是否正常（无红色错误标记）。如 Service Worker 无效，移除后重新加载扩展。",
        }

    ok, err = _ensure_driver_ready(timeout=5)
    if not ok:
        return {"ok": False, "error": err}

    tid = _cdp_tid or ensure_cdp_config()
    inject_result = _cdp_send_cmd(tid, cmd_json)
    if (
        inject_result.get("status") != "success"
        or inject_result.get("js_return") != "injected"
    ):
        return {"ok": False, "error": "无法注入 CDP 命令到页面"}

    resp = _cdp_poll(tid, timeout=timeout, interval=0.3)
    if not resp.get("ok") and "timeout" in str(resp.get("error", "")):
        global _cdp_available
        _cdp_available = None
    return resp


def first_init_driver():
    """初始化 TMWebDriver（线程安全，只执行一次）"""
    global driver
    if not _driver_lock.acquire(blocking=False):
        _driver_ready.wait(timeout=30)
        return
    try:
        if driver is not None:
            return
        ensure_cdp_config()
        from TMWebDriver import TMWebDriver

        d = TMWebDriver()
        print("[TMWebDriver] Server started, waiting for browser connections...")
        for i in range(20):
            time.sleep(1)
            sess = d.get_all_sessions()
            if len(sess) > 0:
                print(f"[TMWebDriver] {len(sess)} browser tab(s) connected")
                break
        else:
            print(
                "[TMWebDriver] Warning: no browser connected after 20s (Tampermonkey script needed)"
            )
        driver = d
    except Exception as e:
        print(f"[TMWebDriver] Init failed: {e}")
    finally:
        _driver_ready.set()
        _driver_lock.release()


def _ensure_driver_ready(timeout=15):
    """确保 driver 已初始化且有活跃 Session，返回 (ok, error_msg)"""
    global driver

    if driver is None:
        if not _driver_ready.is_set():
            print("[TMWebDriver] Waiting for background init to complete...")
            _driver_ready.wait(timeout=30)

    if driver is None:
        first_init_driver()

    if driver is None:
        return False, (
            "TMWebDriver 初始化失败。请确认：\n"
            "1. pip install simple-websocket-server bottle\n"
            "2. 端口 18765/18766 未被占用\n"
            "3. 重启 SEDA 后重试"
        )

    sessions = driver.get_all_sessions()
    if sessions:
        if driver.default_session_id is None:
            driver.default_session_id = sessions[0]["id"]
        return True, None

    print(f"[TMWebDriver] No active sessions, waiting up to {timeout}s...")
    for _ in range(timeout):
        time.sleep(1)
        sessions = driver.get_all_sessions()
        if sessions:
            if driver.default_session_id is None:
                driver.default_session_id = sessions[0]["id"]
            print(f"[TMWebDriver] Session ready: {sessions[0].get('url', '?')}")
            return True, None

    return False, (
        "没有可用的浏览器标签页。请确认：\n"
        "1. Chrome 已安装 Tampermonkey 扩展\n"
        "2. ljq_web_driver 脚本已启用并在所有网站上运行\n"
        "3. Chrome 中至少有一个打开的网页标签\n"
        "4. 刷新 Chrome 页面后重试"
    )


def web_scan(tabs_only=False, switch_tab_id=None):
    """
    获取当前页面的简化HTML内容和标签页列表。注意：简化过程会过滤边栏、浮动元素等非主体内容。
    tabs_only: 仅返回标签页列表，不获取HTML内容（节省token）。
    switch_tab_id: 可选参数，如果提供，则在扫描前切换到该标签页。
    应当多用execute_js，少全量观察html。
    """
    try:
        ok, err = _ensure_driver_ready(timeout=8)
        if not ok:
            return {"status": "error", "msg": err}
        tabs = []
        for sess in driver.get_all_sessions():
            sess.pop("connected_at", None)
            sess.pop("type", None)
            sess["url"] = sess.get("url", "")[:50] + (
                "..." if len(sess.get("url", "")) > 50 else ""
            )
            tabs.append(sess)
        if switch_tab_id:
            driver.default_session_id = switch_tab_id
        result = {
            "status": "success",
            "metadata": {
                "tabs_count": len(tabs),
                "tabs": tabs,
                "active_tab": driver.default_session_id,
            },
        }
        if not tabs_only:
            result["content"] = get_html(driver, cutlist=True, maxchars=23000)
        return result
    except Exception as e:
        return {"status": "error", "msg": format_error(e)}


def format_error(e):
    exc_type, exc_value, exc_traceback = sys.exc_info()
    tb = traceback.extract_tb(exc_traceback)
    if tb:
        f = tb[-1]
        fname = os.path.basename(f.filename)
        return f"{exc_type.__name__}: {str(e)} @ {fname}:{f.lineno}, {f.name} -> `{f.line}`"
    return f"{exc_type.__name__}: {str(e)}"


def log_memory_access(path):
    if "memory" not in path:
        return
    stats_file = "memory/file_access_stats.json"
    try:
        with open(stats_file, "r", encoding="utf-8") as f:
            stats = json.load(f)
    except:
        stats = {}
    fname = os.path.basename(path)
    stats[fname] = {
        "count": stats.get(fname, {}).get("count", 0) + 1,
        "last": datetime.now().strftime("%Y-%m-%d"),
    }
    with open(stats_file, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)


def web_execute_js(script, switch_tab_id=None):
    """
    执行 JS 脚本来控制浏览器，并捕获结果和页面变化。
    script: 要执行的 JavaScript 代码字符串。
    return {
        "status": "failed" if error_msg else "success",
        "js_return": result,
        "error": error_msg,
        "transients": transients,
        "environment": {
            "newTabs": [],
            "reloaded": reloaded
        },
        "diff": diff_summary,
    }
    """
    try:
        ok, err = _ensure_driver_ready(timeout=10)
        if not ok:
            return {"status": "error", "msg": err}
        if switch_tab_id:
            driver.default_session_id = switch_tab_id
        result = execute_js_rich(script, driver)
        return result
    except Exception as e:
        return {"status": "error", "msg": format_error(e)}


def file_patch(path: str, old_content: str, new_content: str):
    """在文件中寻找唯一的 old_content 块并替换为 new_content。"""
    path = str(Path(path).resolve())
    try:
        if not os.path.exists(path):
            return {"status": "error", "msg": "文件不存在"}
        with open(path, "r", encoding="utf-8") as f:
            full_text = f.read()
        if not old_content:
            return {"status": "error", "msg": "old_content 为空，请确认 arguments"}
        count = full_text.count(old_content)
        if count == 0:
            return {
                "status": "error",
                "msg": "未找到匹配的旧文本块，建议：先用 file_read 确认当前内容，再分小段进行 patch。若多次失败则询问用户，严禁自行使用 overwrite 或代码替换。",
            }
        if count > 1:
            return {
                "status": "error",
                "msg": f"找到 {count} 处匹配，无法确定唯一位置。请提供更长、更具体的旧文本块以确保唯一性。建议：包含上下文行来增强特征，或分小段逐个修改。",
            }
        updated_text = full_text.replace(old_content, new_content)
        with open(path, "w", encoding="utf-8") as f:
            f.write(updated_text)
        return {"status": "success", "msg": "文件局部修改成功"}
    except Exception as e:
        return {"status": "error", "msg": str(e)}


def file_read(path, start=1, keyword=None, count=200, show_linenos=True):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            stream = ((i, l.rstrip("\r\n")) for i, l in enumerate(f, 1))
            stream = itertools.dropwhile(lambda x: x[0] < start, stream)
            if keyword:
                before = collections.deque(maxlen=count // 3)
                for i, l in stream:
                    if keyword.lower() in l.lower():
                        res = (
                            list(before)
                            + [(i, l)]
                            + list(itertools.islice(stream, count - len(before) - 1))
                        )
                        break
                    before.append((i, l))
                else:
                    return (
                        f"Keyword '{keyword}' not found after line {start}. Falling back to content from line {start}:\n\n"
                        + file_read(path, start, None, count, show_linenos)
                    )
            else:
                res = list(itertools.islice(stream, count))
            realcnt = len(res)
            L_MAX = max(100, 512000 // realcnt)
            TAG = " ... [TRUNCATED]"
            remaining = sum(1 for _ in itertools.islice(stream, 5000))
            total_lines = (start - 1) + realcnt + remaining
            total_tag = (
                "[FILE] Total "
                + (f"{total_lines}+" if remaining >= 5000 else str(total_lines))
                + " lines\n"
            )
            res = [(i, l if len(l) <= L_MAX else l[:L_MAX] + TAG) for i, l in res]
            result = "\n".join(f"{i}|{l}" if show_linenos else l for i, l in res)
            if show_linenos:
                result = total_tag + result
            return result
    except Exception as e:
        return f"Error: {str(e)}"


def smart_format(data, max_depth=2, max_str_len=100, omit_str=" ... "):
    def truncate(obj, depth):
        if isinstance(obj, str):
            if len(obj) < max_str_len + len(omit_str) * 2:
                return obj
            return f"{obj[:max_str_len//2]}{omit_str}{obj[-max_str_len//2:]}"
        if depth >= max_depth:
            return truncate(str(obj), depth + 1)
        if isinstance(obj, dict):
            return {k: truncate(v, depth + 1) for k, v in obj.items()}
        if isinstance(obj, list):
            return [truncate(i, depth + 1) for i in obj]
        return obj

    if isinstance(data, (str, bytes)):
        return truncate(data, 0)
    return json.dumps(truncate(data, 0), indent=2, ensure_ascii=False, default=str)


class GenericAgentHandler(BaseHandler):
    """Generic Agent 工具库，包含多种工具的实现。工具函数自动加上了 do_ 前缀。实际工具名没有前缀。"""

    def __init__(self, parent, last_history=None, cwd="./"):
        self.parent = parent
        self.key_info = ""
        self.related_sop = ""
        self.cwd = cwd
        self.history_info = last_history if last_history else []
        self.code_stop_signal = []
        self.tracker = get_session_tracker()
        self._current_turn = 0
        # 长期记忆结算流程的状态标记，避免同一会话内重复触发造成自循环
        self._long_term_update_started = False
        self._long_term_update_start_turn = None
        # 一键主 SOP 写保护：仅 one_click_registry_update 任务允许 file_patch
        self._allow_one_click_registry_edit = False

    def _get_abs_path(self, path):
        if not path:
            return ""
        if os.path.isabs(path):
            return os.path.abspath(path)

        normalized = path.replace("\\", "/").lstrip("./")
        project_root = os.path.dirname(os.path.abspath(__file__))

        # 固定目录优先按项目根解析，避免 cwd 在 temp 时误读 temp/memory 或 temp/assets
        if normalized.startswith("memory/") or normalized.startswith("assets/"):
            return os.path.abspath(os.path.join(project_root, normalized))

        return os.path.abspath(os.path.join(self.cwd, path))

    def tool_after_callback(self, tool_name, args, response, ret):
        rsumm = re.search(r"<summary>(.*?)</summary>", response.content, re.DOTALL)
        if rsumm:
            summary = rsumm.group(1).strip()[:200]
        else:
            summary = f"调用工具{tool_name}, args: {args}"
            if tool_name == "no_tool":
                summary = "直接回答了用户问题"
            if type(ret.next_prompt) is str:
                ret.next_prompt += "\nPROTOCOL_VIOLATION: 上一轮遗漏了<summary>。 我已根据物理动作自动补全。请务必在下次回复中记得<summary>协议。"
        self.history_info.append("[Agent] " + smart_format(summary, max_str_len=100))

        is_error = False
        if isinstance(ret.data, dict) and ret.data.get("status") in (
            "error",
            "fail",
            "FAIL",
        ):
            is_error = True
        elif (
            isinstance(ret.data, dict)
            and "error" in str(ret.data.get("msg", "")).lower()
        ):
            is_error = True

        self.tracker.record_turn(
            self._current_turn, tool_name, not is_error, summary[:150]
        )
        if is_error:
            err_msg = (
                ret.data.get("msg", "") or ret.data.get("error", "")
                if isinstance(ret.data, dict)
                else str(ret.data)[:200]
            )
            self.tracker.record_failure(
                tool_name, str(args)[:200], err_msg, self._current_turn
            )

    def do_code_run(self, args, response):
        """执行代码片段，有长度限制，不允许代码中放大量数据，如有需要应当通过文件读取进行。"""
        code_type = args.get("type", "python")
        # 从 response.content 中提取代码块, 匹配 ```python ... ``` 或 ```powershell ... ```
        pattern = rf"```{code_type}\n(.*?)\n```"
        matches = re.findall(pattern, response.content, re.DOTALL)
        warning = ""
        if not matches:
            code = args.get("code")
            if not code:
                return StepOutcome(
                    None,
                    next_prompt=f"【系统错误】：你调用了 code_run，但未在先在回复正文中提供 ```{code_type} 代码块。请重新输出代码并附带工具调用。",
                )
            warning = "\n下次要记得先在回复正文中提供代码块，而不是放在参数中"
        else:
            code = matches[
                -1
            ].strip()  # 提取最后一个代码块（通常是模型修正后的最终逻辑）
        timeout = args.get("timeout", 60)
        raw_path = os.path.join(self.cwd, args.get("cwd", "./"))
        cwd = os.path.normpath(os.path.abspath(raw_path))
        code_cwd = os.path.normpath(self.cwd)
        result = yield from code_run(
            code,
            code_type,
            timeout,
            cwd,
            code_cwd=code_cwd,
            stop_signal=self.code_stop_signal,
        )
        next_prompt = self._get_anchor_prompt() + warning
        return StepOutcome(result, next_prompt=next_prompt)

    _DANGEROUS_KEYWORDS = [
        "删除",
        "移除",
        "覆盖",
        "格式化",
        "清空",
        "重置",
        "不可逆",
        "永久",
        "delete",
        "remove",
        "overwrite",
        "format",
        "drop",
        "truncate",
        "destroy",
        "rm ",
        "rm -",
        "rmdir",
        "sudo",
        "force",
    ]

    def _is_dangerous_question(self, question, candidates):
        """检测 ask_user 是否涉及危险/不可逆操作"""
        text = (question + " " + " ".join(str(c) for c in candidates)).lower()
        return any(kw in text for kw in self._DANGEROUS_KEYWORDS)

    def do_ask_user(self, args, response):
        question = args.get("question", "请提供输入：")
        candidates = args.get("candidates", [])
        yield f"[ask_user] 问题: {question}\n"
        if candidates:
            yield f"[ask_user] 候选项: {candidates}\n"

        if self._is_dangerous_question(question, candidates):
            yield "[ask_user] ⚠️ 检测到危险操作关键词，必须等待用户确认。\n"
            result = ask_user(question, candidates)
            return StepOutcome(result, next_prompt="", should_exit=True)

        chosen = candidates[0] if candidates else "继续执行当前方案"
        reason = "用户未在场，框架自动选择第一个/最安全选项（非危险操作）"

        self.tracker.record_decision(
            question=question,
            chosen=chosen,
            alternatives=candidates[1:] if len(candidates) > 1 else ["(无其他选项)"],
            reason=reason,
            turn=self._current_turn,
        )

        yield f"[ask_user] ⚡ 自主决策: 选择 '{chosen}' ({reason})\n"
        next_prompt = self._get_anchor_prompt() + (
            f"\n[System — 自主决策通知] Agent 调用了 ask_user，但当前用户不在场。\n"
            f"框架已自动选择: 「{chosen}」\n"
            f"原问题: {question}\n"
            f"备选项: {candidates}\n"
            f"此决策已记录到 session report，用户回来后可审阅。\n"
            f"请基于选择「{chosen}」继续推进任务。如果此选择导致后续失败，可尝试其他选项。\n"
        )
        return StepOutcome(
            {
                "status": "AUTO_DECIDED",
                "question": question,
                "chosen": chosen,
                "candidates": candidates,
            },
            next_prompt=next_prompt,
            should_exit=False,
        )

    def do_web_scan(self, args, response):
        """获取当前页面内容和标签页列表。也可用于切换标签页。
        注意：HTML经过简化，边栏/浮动元素等可能被过滤。如需查看被过滤的内容请用execute_js。
        tabs_only=true时仅返回标签页列表，不获取HTML（省token）。
        """
        tabs_only = args.get("tabs_only", False)
        switch_tab_id = args.get("switch_tab_id", None)
        result = web_scan(tabs_only=tabs_only, switch_tab_id=switch_tab_id)
        content = result.pop("content", None)
        yield f"[Info] {str(result)}\n"
        if content:
            next_prompt = f"<tool_result>\n```html\n{content}\n```\n</tool_result>"
        else:
            next_prompt = (
                "标签页列表如上\n"  # 手动tool_result为了触发历史上下文自动压缩
            )
        return StepOutcome(result, next_prompt=next_prompt)

    def do_web_execute_js(self, args, response):
        """web情况下的优先使用工具，执行任何js达成对浏览器的*完全*控制。
        支持将结果保存到文件供后续读取分析，但保存功能仅限即时读取，与await等异步操作不兼容。
        """
        script = args.get("script", "")
        if not script:
            return StepOutcome(
                None,
                next_prompt="[Error] Empty script param. Check your tool call arguments.",
            )
        save_to_file = args.get("save_to_file", "")
        switch_tab_id = args.get("switch_tab_id") or args.get("tab_id")
        result = web_execute_js(script, switch_tab_id=switch_tab_id)
        if save_to_file and "js_return" in result:
            content = str(result["js_return"] or "")
            abs_path = self._get_abs_path(save_to_file)
            result["js_return"] = smart_format(content, max_str_len=170)
            try:
                with open(abs_path, "w", encoding="utf-8") as f:
                    f.write(str(content))
                result["js_return"] += f"\n\n[已保存完整内容到 {abs_path}]"
            except:
                result["js_return"] += f"\n\n[保存失败，无法写入文件 {abs_path}]"
        try:
            print("Web Execute JS Result:", smart_format(result))
        except:
            pass
        yield f"JS 执行结果:\n{smart_format(result)}\n"
        next_prompt = self._get_anchor_prompt()
        return StepOutcome(
            smart_format(result, max_str_len=5000), next_prompt=next_prompt
        )

    def do_file_patch(self, args, response):
        path = self._get_abs_path(args.get("path", ""))
        yield f"[Action] Patching file: {path}\n"
        allow_reg = getattr(self, "_allow_one_click_registry_edit", False)
        ok, err = check_one_click_main_sop_file_patch_allowed(path, allow_reg)
        if not ok:
            yield f"[Status] ❌ {err}\n"
            return StepOutcome(
                {"status": "error", "msg": err},
                next_prompt=self._get_anchor_prompt(),
            )
        old_content = args.get("old_content", "")
        new_content = args.get("new_content", "")
        result = file_patch(path, old_content, new_content)
        yield f"\n{smart_format(result)}\n"
        next_prompt = self._get_anchor_prompt()
        return StepOutcome(result, next_prompt=next_prompt)

    def do_file_write(self, args, response):
        """用于对整个文件的大量处理，精细修改要用file_patch。
        需要将要写入的内容放在<file_content>标签内，或者放在代码块中。
        """
        path = self._get_abs_path(args.get("path", ""))
        ok_w, err_w = check_one_click_main_sop_file_write_allowed(path)
        if not ok_w:
            yield f"[Status] ❌ {err_w}\n"
            return StepOutcome({"status": "error", "msg": err_w}, next_prompt="\n")
        mode = args.get("mode", "overwrite")  # overwrite/append/prepend
        action_str = {"prepend": "Prepending to", "append": "Appending to"}.get(
            mode, "Overwriting"
        )
        yield f"[Action] {action_str} file: {os.path.basename(path)}\n"

        def extract_robust_content(text):
            tag = re.search(r"<file_content>(.*)</file_content>", text, re.DOTALL)
            if tag:
                return tag.group(1).strip()
            s, e = text.find("```"), text.rfind("```")
            if -1 < s < e:
                return text[text.find("\n", s) + 1 : e].strip()
            return None

        blocks = extract_robust_content(response.content)
        if not blocks:
            yield f"[Status] ❌ 失败: 未在回复中找到代码块内容\n"
            return StepOutcome(
                {
                    "status": "error",
                    "msg": "No content found, if you want a blank, you should use code_run",
                },
                next_prompt="\n",
            )
        new_content = blocks
        try:
            if mode == "prepend":
                old = (
                    open(path, "r", encoding="utf-8").read()
                    if os.path.exists(path)
                    else ""
                )
                open(path, "w", encoding="utf-8").write(new_content + old)
            else:
                with open(
                    path, "a" if mode == "append" else "w", encoding="utf-8"
                ) as f:
                    f.write(new_content)
            yield f"[Status] ✅ {mode.capitalize()} 成功 ({len(new_content)} bytes)\n"
            next_prompt = self._get_anchor_prompt()
            return StepOutcome(
                {"status": "success", "writed_bytes": len(new_content)},
                next_prompt=next_prompt,
            )
        except Exception as e:
            yield f"[Status] ❌ 写入异常: {str(e)}\n"
            return StepOutcome({"status": "error", "msg": str(e)}, next_prompt="\n")

    def do_file_read(self, args, response):
        """读取文件内容。从第start行开始读取。如有keyword则返回第一个keyword(忽略大小写)周边内容"""
        path = self._get_abs_path(args.get("path", ""))
        yield f"\n[Action] Reading file: {path}\n"
        start = args.get("start", 1)
        count = args.get("count", 200)
        keyword = args.get("keyword")
        show_linenos = args.get("show_linenos", True)
        result = file_read(
            path, start=start, keyword=keyword, count=count, show_linenos=show_linenos
        )
        if show_linenos:
            tips = "由于设置了show_linenos，以下返回信息为：(行号|)内容 。\n"
            result = tips + result
        if " ... [TRUNCATED]" in result:
            result += "\n\n（某些行被截断，如需完整内容可改用 code_run 读取）"
        next_prompt = self._get_anchor_prompt()
        log_memory_access(path)
        if "memory" in path or "sop" in path:
            next_prompt += "\n[SYSTEM TIPS] 正在读取记忆或SOP文件，若决定按sop执行请提取sop中的关键点（特别是靠后的）update working memory."
        return StepOutcome(result, next_prompt=next_prompt)

    def do_update_working_checkpoint(self, args, response):
        """为整个任务设定后续需要临时记忆的重点。"""
        key_info = args.get("key_info", "")
        related_sop = args.get("related_sop", "")
        if key_info:
            self.key_info = key_info
        if related_sop:
            self.related_sop = related_sop
        yield f"[Info] Updated key_info and related_sop.\n"
        yield f"key_info:\n{self.key_info}\n\n"
        yield f"related_sop:\n{self.related_sop}\n\n"
        next_prompt = self._get_anchor_prompt()
        # next_prompt += '\n[SYSTEM TIPS] 此函数一般在任务开始或中间时调用，如果任务已成功完成应该是start_long_term_update用于结算长期记忆。\n'
        return StepOutcome({"status": "success"}, next_prompt=next_prompt)

    _no_tool_consecutive = 0

    def do_no_tool(self, args, response):
        """当模型在一轮中未显式调用任何工具时，由引擎自动触发。
        核心改进：只有连续 2 次不调工具才允许退出，第 1 次推动 LLM 继续行动。
        early turn 放行：turn <= 3 且无失败记录时，LLM 第 1 次不调工具即可退出（简单对话不浪费轮次）。
        """
        content = getattr(response, "content", "") or ""
        long_term_enabled = getattr(self, "enable_long_term_memory", True)

        if not response or not content.strip():
            yield "[Warn] LLM returned an empty response. Retrying...\n"
            self._no_tool_consecutive = 0
            return StepOutcome(
                {},
                next_prompt="[System] 回复为空，请重新生成内容或调用工具。",
                should_exit=False,
            )

        code_block_pattern = r"```[a-zA-Z0-9_]*\n[\s\S]{100,}?```"
        m = re.search(code_block_pattern, content)
        if m:
            residual = content.replace(m.group(0), "")
            residual = re.sub(
                r"<thinking>[\s\S]*?</thinking>", "", residual, flags=re.IGNORECASE
            )
            residual = re.sub(
                r"<summary>[\s\S]*?</summary>", "", residual, flags=re.IGNORECASE
            )
            if len(re.sub(r"\s+", "", residual)) <= 50:
                yield "[Info] Detected code block without tool call. Pushing to act.\n"
                self._no_tool_consecutive = 0
                return StepOutcome(
                    {},
                    next_prompt=(
                        "[System] 检测到较大代码块但未调用工具。"
                        "请调用相应工具执行（code_run/file_write/file_patch），或补充说明是否还需额外操作。"
                    ),
                    should_exit=False,
                )

        self._no_tool_consecutive += 1

        early_turn = self._current_turn <= 3 and not self.tracker.failures
        if early_turn:
            yield "[Info] Early turn 且无失败记录，允许直接结束。\n"
            self._no_tool_consecutive = 0
            return StepOutcome(response, next_prompt=None, should_exit=True)

        # 长期记忆关闭时，不再推动“是否调用 start_long_term_update”的额外轮次；
        # 与 early turn 一样在无失败场景下直接结束，减少无效调用。
        if not long_term_enabled and not self.tracker.failures:
            yield "[Info] Long-term memory disabled 且无失败记录，允许直接结束。\n"
            self._no_tool_consecutive = 0
            return StepOutcome(response, next_prompt=None, should_exit=True)

        if self._no_tool_consecutive < 2:
            yield "[Info] LLM 未调用工具（第 1 次），推动继续...\n"
            failure_hint = self.tracker.get_failure_summary()
            if long_term_enabled:
                completion_guidance = "1. 任务目标是否已**完全达成**？若是，请调用 `start_long_term_update` 沉淀经验后结束。\n"
            else:
                completion_guidance = "1. 任务目标是否已**完全达成**？若是，请直接给出最终结论并结束，不要再为记忆结算追加工具调用。\n"
            push_prompt = (
                "[System — 任务驱动检查] 你刚才没有调用任何工具。请自检：\n"
                f"{completion_guidance}"
                "2. 若任务未完成，请继续调用工具推进，不要用纯文本总结替代行动。\n"
                "3. 若遇到困难：查记忆(file_read L1/L3) → 替代方案 → browse_and_learn → ask_user。\n"
            )
            if failure_hint:
                push_prompt += f"\n{failure_hint}\n请分析失败原因并尝试替代方案。\n"
            return StepOutcome({}, next_prompt=push_prompt, should_exit=False)

        yield "[Info] LLM 连续 2 次未调用工具，确认结束。\n"
        self._no_tool_consecutive = 0
        return StepOutcome(response, next_prompt=None, should_exit=True)

    def do_start_long_term_update(self, args, response):
        """Agent觉得当前任务完成后有重要信息需要记忆时调用此工具。"""
        # 前端或上层若显式关闭了长期记忆（如 Streamlit 开关），则直接跳过结算过程
        if hasattr(self, "enable_long_term_memory") and not getattr(
            self, "enable_long_term_memory", True
        ):
            yield "[Info] Long-term memory update is disabled for this task. Skip.\n"
            next_prompt = self._get_anchor_prompt()
            return StepOutcome({"status": "disabled"}, next_prompt=next_prompt)

        # 若当前会话已进入长期记忆结算流程，则忽略后续重复触发，避免在总结/记忆阶段形成自循环
        if getattr(self, "_long_term_update_started", False):
            yield "[Info] Long-term memory update already started in this session. Skip duplicate trigger.\n"
            next_prompt = self._get_anchor_prompt()
            return StepOutcome({"status": "already_started"}, next_prompt=next_prompt)

        self._long_term_update_started = True
        self._long_term_update_start_turn = self._current_turn

        prompt = (
            """### [总结提炼经验] 既然你觉得当前任务有重要信息需要记忆，请提取最近一次任务中【事实验证成功且长期有效】的环境事实、用户偏好、重要步骤，更新记忆。
本工具是标记开启结算过程，若已在更新记忆过程或没有值得记忆的点，忽略本次调用。
**提取行动验证成功的信息**：
- **环境事实**（路径/凭证/配置）→ `file_patch` 更新 L2，同步 L1
- **复杂任务经验**（关键坑点/前置条件/重要步骤）→ L3 精简 SOP（只记你被坑得多次重试的核心要点）
**禁止**：临时变量、具体推理过程、未验证信息、通用常识、你可以轻松复现的细节。
**操作**：严格遵循提供的L0的记忆更新SOP。先 `file_read` 看现有 → 判断类型 → 最小化更新 → 无新内容跳过，保证对记忆库最小局部修改。\n
"""
            + get_global_memory()
        )
        yield "[Info] Start distilling good memory for long-term storage.\n"

        # 优先读取 L0 记忆管理宪法，其次退回旧版 memory_management_sop；
        # 统一使用基于项目根目录的绝对路径，避免 cwd 落在 temp 时相对路径失效
        base_dir = os.path.dirname(os.path.abspath(__file__))
        candidate_paths = [
            os.path.join(base_dir, "memory", "L0_memory_management_sop.md"),
            os.path.join(base_dir, "memory", "memory_management_sop.md"),
        ]
        result = None
        for path in candidate_paths:
            if os.path.exists(path):
                result = file_read(path, show_linenos=False)
                break
        if result is None:
            result = "Memory Management SOP not found. Do not update memory."

        return StepOutcome(result, next_prompt=prompt)

    def _get_anchor_prompt(self):
        h_str = "\n".join(self.history_info[-20:])
        prompt = f"\n### [WORKING MEMORY]\n<history>\n{h_str}\n</history>"
        if self.key_info:
            prompt += f"\n<key_info>{self.key_info}</key_info>"
        if self.related_sop:
            prompt += f"\n有不清晰的地方请再次读取{self.related_sop}"
        try:
            print(prompt)
        except:
            pass
        return prompt

    def next_prompt_patcher(self, next_prompt, outcome, turn):
        self._current_turn = turn
        # 每轮都追加输出语言提示；优先尊重用户显式要求（如 answer in Chinese）。
        q = ""
        for line in reversed(self.history_info or []):
            if line.startswith("[USER]:"):
                q = line[len("[USER]:") :].strip()
                break
        if q:
            ql = q.lower()
            lang = None
            zh_override_markers = (
                "answer in chinese",
                "reply in chinese",
                "respond in chinese",
                "in chinese",
                "请用中文",
                "用中文回答",
                "中文回答",
                "中文输出",
            )
            en_override_markers = (
                "answer in english",
                "reply in english",
                "respond in english",
                "in english",
                "请用英文",
                "用英文回答",
                "英文回答",
                "英文输出",
            )
            if any(m in ql for m in zh_override_markers):
                lang = "zh"
            elif any(m in ql for m in en_override_markers):
                lang = "en"
            else:
                cjk_count = len(re.findall(r"[\u4e00-\u9fff]", q))
                en_word_count = len(re.findall(r"\b[a-zA-Z]{2,}\b", q))
                if en_word_count >= 3 and en_word_count > cjk_count:
                    lang = "en"
                elif cjk_count >= 2 and cjk_count >= en_word_count:
                    lang = "zh"

            if lang == "en":
                next_prompt += (
                    "\n\n[System — Output Language]\n"
                    "Respond in English for this turn.\n"
                    "If your draft is not in English, rewrite it in English before final output."
                )
            elif lang == "zh":
                next_prompt += (
                    "\n\n[System — 输出语言]\n"
                    "本轮请使用中文回答。\n"
                    "若草稿不是中文，请在输出前改写为中文。"
                )

        failure_hint = self.tracker.get_failure_summary()
        if failure_hint and turn % 3 == 0:
            next_prompt += f"\n\n[System — 失败分析提醒]\n{failure_hint}\n请分析原因，尝试替代方案，避免重复相同失败。"

        if turn % 30 == 0:
            next_prompt += f"\n\n[DANGER] 已连续执行第 {turn} 轮。请 update_working_checkpoint 保存上下文，调用 start_long_term_update 沉淀经验。"
        elif turn % 10 == 0:
            next_prompt += get_global_memory()
            next_prompt += f"\n\n[System — 进度检查 Turn {turn}] 请回顾：任务目标是否在推进？若卡住，必须切换策略（查记忆/搜索/替代工具），不要原地重试相同方案。"
        elif turn % 5 == 0:
            next_prompt += f"\n\n[System — 任务驱动 Turn {turn}] 还有轮次可用。请高效利用：继续推进任务或学习新知识写入记忆。"

        return next_prompt


def get_global_memory():
    prompt = "\n"
    try:
        with open("memory/global_mem_insight.txt", "r", encoding="utf-8") as f:
            insight = f.read()
        with open("assets/insight_fixed_structure.txt", "r", encoding="utf-8") as f:
            structure = f.read()
        prompt += f"\n[Memory]\n"
        temp_cwd = os.path.abspath("./temp")
        memory_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "memory"))
        prompt += f"cwd(code_run/file_read 默认工作目录) = {temp_cwd}\n"
        prompt += f"记忆根目录 = {memory_root}\n"
        prompt += '访问记忆/L3_SOP 时，请优先使用基于项目根的绝对路径，或以 "../memory/..." 为前缀的相对路径，避免误指向 temp 子目录。\n'
        prompt += structure + "\n../memory/global_mem_insight.txt:\n"
        prompt += insight + "\n"
    except FileNotFoundError:
        pass
    return prompt
