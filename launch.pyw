import webview, threading, subprocess, sys, time, os, ctypes, atexit, socket, random

WINDOW_WIDTH, WINDOW_HEIGHT, RIGHT_PADDING, TOP_PADDING = 600, 900, 0, 300

def find_free_port(lo=8501, hi=8599):
    ports = list(range(lo, hi+1)); random.shuffle(ports)
    for p in ports:
        try: s = socket.socket(); s.bind(('127.0.0.1', p)); s.close(); return p
        except OSError: continue
    raise RuntimeError(f'No free port in {lo}-{hi}')

def get_screen_width():
    try: return ctypes.windll.user32.GetSystemMetrics(0)
    except: return 1920

def start_streamlit(port):
    global proc
    cmd = [sys.executable, "-m", "streamlit", "run", "stapp.py", "--server.port", str(port), "--server.headless", "true", "--theme.base", "dark"]  # 暗黑模式
    proc = subprocess.Popen(cmd)
    atexit.register(proc.kill)

def inject(text):
    window.evaluate_js(f"""
        const textarea = document.querySelector('textarea[data-testid="stChatInputTextArea"]');
        if (textarea) {{
            // 1. 用原生 setter 设置值（绕过 React）
            const nativeTextAreaValueSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
            nativeTextAreaValueSetter.call(textarea, {repr(text)});
            // 2. 触发 React 的 input 事件
            textarea.dispatchEvent(new Event('input', {{ bubbles: true }}));
            // 3. 触发 change 事件（有些组件需要）
            textarea.dispatchEvent(new Event('change', {{ bubbles: true }}));
            // 4. 延迟提交
            setTimeout(() => {{
                const btn = document.querySelector('[data-testid="stChatInputSubmitButton"]');
                if (btn) {{btn.click();console.log('Submitted:', {repr(text)});}}
            }}, 200);
        }}""")

def get_last_reply_time():
    last = window.evaluate_js("""
        const el = document.getElementById('last-reply-time');
        el ? parseInt(el.textContent) : 0;
    """) or 0
    return last or int(time.time())

def generate_autonomous_prompt():
    """根据当前记忆状态动态生成自主学习任务"""
    import json as _json

    # 读取自主探索历史，避免重复
    history_path = os.path.join(os.path.dirname(__file__), 'temp', 'autonomous_reports', 'history.txt')
    recent_topics = []
    if os.path.exists(history_path):
        try:
            with open(history_path, 'r', encoding='utf-8') as f:
                for line in f.readlines()[:10]:
                    recent_topics.append(line.strip())
        except Exception:
            pass
    recent_hint = ""
    if recent_topics:
        recent_hint = f"\n近期已探索: {'; '.join(recent_topics[:5])}\n请选择不同方向。"

    # 读取L1索引，找知识空白
    l1_path = os.path.join(os.path.dirname(__file__), 'memory', 'L1_disease_insight.txt')
    l1_hint = ""
    if os.path.exists(l1_path):
        try:
            with open(l1_path, 'r', encoding='utf-8') as f:
                l1_content = f.read()
            if len(l1_content) < 200:
                l1_hint = "\nL1索引内容较少，建议优先学习常见疾病的诊断标准并充实索引。"
        except Exception:
            pass

    # 读取L3 SOP目录，看覆盖了哪些疾病
    sop_dir = os.path.join(os.path.dirname(__file__), 'memory', 'L3_sops')
    existing_sops = []
    if os.path.isdir(sop_dir):
        existing_sops = [f.replace('_sop.md', '').replace('.md', '') for f in os.listdir(sop_dir)
                         if f.endswith('.md') and f != 'autonomous_learning_sop.md']
    sop_hint = ""
    if len(existing_sops) < 5:
        sop_hint = f"\n当前仅有 {len(existing_sops)} 个疾病SOP ({', '.join(existing_sops)})，建议扩展更多常见疾病。"

    # 读取策略统计
    strategy_path = os.path.join(os.path.dirname(__file__), 'memory', 'L4_episodes', 'disease_strategy.json')
    strategy_hint = ""
    if os.path.exists(strategy_path):
        try:
            with open(strategy_path, 'r', encoding='utf-8') as f:
                strategy = _json.load(f)
            low_conf = [d for d, s in strategy.items() if s.get('avg_confidence', 1) < 0.6]
            if low_conf:
                strategy_hint = f"\n以下疾病历史置信度偏低: {', '.join(low_conf[:3])}，建议针对性学习。"
        except Exception:
            pass

    prompt = (
        "[AUTO]🤖 自主探索模式已激活。你现在是 Self-Evolving MedicalClaw，进入自主学习阶段。\n\n"
        "请按以下流程执行：\n"
        "1. 读取 memory/L3_sops/autonomous_learning_sop.md 了解学习SOP\n"
        "2. 检查 memory/L1_disease_insight.txt 评估当前知识覆盖\n"
        "3. 选择一个有价值的学习方向（优先填补知识空白）\n"
        "4. 用 browse_and_learn 或 web_search 学习新知识\n"
        "5. 将学到的知识写入 L1/L2/L3 记忆\n"
        "6. 用 file_write 写一份简短报告到 ./autonomous_reports/\n\n"
        "约束：≤20回合 | 只写cwd和memory | 遵守L0记忆规则 | 报告要简洁\n"
        f"{l1_hint}{sop_hint}{strategy_hint}{recent_hint}"
    )
    return prompt


def idle_monitor():
    """空闲监控器：用户离开后自动触发自主学习"""
    last_trigger_time = 0
    COOLDOWN = 120           # 两次自动探索间隔至少2分钟
    IDLE_THRESHOLD = 300     # 空闲5分钟后自动探索
    while True:
        time.sleep(5)
        try:
            now = time.time()
            if now - last_trigger_time < COOLDOWN:
                continue
            last_reply = get_last_reply_time()
            if now - last_reply > IDLE_THRESHOLD:
                prompt = generate_autonomous_prompt()
                print(f'[Idle Monitor] Idle {int(now - last_reply)}s, launching autonomous learning...')
                inject(prompt)
                last_trigger_time = now
        except Exception as e:
            print(f'[Idle Monitor] Error: {e}')

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('port', nargs='?', default='0'); 
    parser.add_argument('--tg', action='store_true', help='启动 Telegram Bot'); 
    parser.add_argument('--llm_no', type=int, default=0, help='LLM编号')
    args = parser.parse_args()
    port = str(find_free_port()) if args.port == '0' else args.port
    print(f'[Launch] Using port {port}')
    threading.Thread(target=start_streamlit, args=(port,), daemon=True).start()

    if args.tg:
        tgproc = subprocess.Popen([sys.executable, "tgapp.py"], creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        atexit.register(tgproc.kill)
        print('[Launch] Telegram Bot started')
    else: print('[Launch] Telegram Bot not enabled (use --tg to start)')
    
    print('[Launch] Task Scheduler not available in SEDA (use --no-sched or ignore)')

    monitor_thread = threading.Thread(target=idle_monitor, daemon=True)
    monitor_thread.start()
    if os.name == 'nt':
        screen_width = get_screen_width()
        x_pos = screen_width - WINDOW_WIDTH - RIGHT_PADDING
    else: x_pos = 100
    time.sleep(2) 
    window = webview.create_window(
        title='SEDA - Diagnosis Agent', url=f'http://localhost:{port}',
        width=WINDOW_WIDTH, height=WINDOW_HEIGHT, x=x_pos, y=TOP_PADDING,
        resizable=True, text_select=True)
    webview.start()