import os, json, re, time, requests, sys, threading, urllib3, random, importlib.util
from datetime import datetime
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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
    repo_root = os.path.dirname(os.path.abspath(__file__))
    repo_parent = os.path.abspath(os.path.join(repo_root, ".."))

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
    raise Exception('[ERROR] mykey.py not found, please copy mykey_template.py to mykey.py and fill your LLM backend.')

mykey = _load_mykey_module()

mykeys = vars(mykey)
proxy = mykeys.get("proxy", 'http://127.0.0.1:2082')
proxies = {"http": proxy, "https": proxy} if proxy else None

def compress_history_tags(messages, keep_recent=4, max_len=200):
    """Compress <thinking>/<tool_use>/<tool_result> tags in older messages to save tokens."""
    for i, msg in enumerate(messages):
        if i < len(messages) - keep_recent and 'orig' not in msg:
            msg['orig'] = msg['prompt']
            for tag in ('thinking', 'tool_use', 'tool_result'):
                msg['prompt'] = re.sub(
                    rf'(<{tag}>)([\s\S]*?)(</{tag}>)',
                    lambda m, _ml=max_len: m.group(1) + (m.group(2)[:_ml] + '...') + m.group(3) if len(m.group(2)) > _ml else m.group(0),
                    msg['prompt']
                )
    return messages

class SiderLLMSession:
    def __init__(self, sider_cookie, default_model="gemini-3.0-flash"):
        from sider_ai_api import Session   # 不使用sider的话没必要安装这个包
        self._core = Session(cookie=sider_cookie, proxies=proxies)   
        self.default_model = default_model
    def ask(self, prompt, model=None, stream=False):
        if model is None: model = self.default_model
        if len(prompt) > 28000: 
            print(f"[Warn] Prompt too long ({len(prompt)} chars), truncating.")
            prompt = prompt[-28000:]
        full_text = self._core.chat(prompt, model, stream=False)
        if stream: return iter([full_text])   # gen有奇怪的空回复或死循环行为，sider足够快
        return full_text   

class ClaudeSession:
    def __init__(self, api_key, api_base, model="claude-opus", context_win=9000):
        self.api_key, self.api_base, self.default_model, self.context_win = api_key, api_base.rstrip('/'), model, context_win
        self.raw_msgs, self.lock = [], threading.Lock()
    def _trim_messages(self, messages):
        compress_history_tags(messages)
        total = sum(len(m['prompt']) for m in messages)
        if total <= self.context_win * 4: return messages
        target, current, result = self.context_win * 4 * 0.9, 0, []
        for msg in reversed(messages):
            if (msg_len := len(msg['prompt'])) + current <= target:
                result.append(msg); current += msg_len
            else: break
        if current > self.context_win * 3.6: print(f'[DEBUG] {len(result)} contexts, whole length {current//4} tokens.')
        return result[::-1] or messages[-2:]
    def raw_ask(self, messages, model=None, temperature=0.5, max_tokens=4096):
        model = model or self.default_model
        headers = {"x-api-key": self.api_key, "Content-Type": "application/json", "anthropic-version": "2023-06-01"}
        payload = {"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens, "stream": True}
        retryable = {429, 500, 502, 503, 504, 520, 529}
        last_err = None
        for attempt in range(4):
            try:
                with requests.post(f"{self.api_base}/v1/messages", headers=headers, json=payload, stream=True, timeout=(5,30)) as r:
                    if r.status_code in retryable:
                        wait = 3 * (2 ** attempt) + random.uniform(0, 1)
                        print(f"[Claude] HTTP {r.status_code}, retry {attempt+1}/4 in {wait:.1f}s...")
                        time.sleep(wait); last_err = f"HTTP {r.status_code}"; continue
                    r.raise_for_status()
                    for line in r.iter_lines():
                        if not line: continue
                        line = line.decode("utf-8") if isinstance(line, bytes) else line
                        if not line.startswith("data:"): continue
                        data = line[5:].lstrip()
                        if data == "[DONE]": break
                        try:
                            obj = json.loads(data)
                            if obj.get("type") == "content_block_delta" and obj.get("delta", {}).get("type") == "text_delta":
                                text = obj["delta"].get("text", "")
                                if text: yield text
                        except: pass
                    return
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                wait = 3 * (2 ** attempt) + random.uniform(0, 1)
                print(f"[Claude] {type(e).__name__}, retry {attempt+1}/4 in {wait:.1f}s...")
                time.sleep(wait); last_err = str(e); continue
            except Exception as e:
                last_err = str(e); break
        yield f"Error: {last_err or 'unknown'} (after retries)"
    def make_messages(self, raw_list):
        trimmed = self._trim_messages(raw_list)
        return [{"role": m['role'], "content": m['prompt']} for m in trimmed]
    def ask(self, prompt, model=None, stream=False):
        def _ask_gen():
            content = ''
            with self.lock:
                self.raw_msgs.append({"role": "user", "prompt": prompt})
                messages = self.make_messages(self.raw_msgs)
            for chunk in self.raw_ask(messages, model):
                content += chunk; yield chunk
            if not content.startswith("Error:"): self.raw_msgs.append({"role": "assistant", "prompt": content})
        return _ask_gen() if stream else ''.join(list(_ask_gen()))

class LLMSession:
    MAX_RETRIES = 4
    RETRY_BASE_DELAY = 3
    RETRYABLE_STATUS = {429, 500, 502, 503, 504, 520, 524}

    def __init__(self, api_key, api_base, model, context_win=12000, proxy=None, temperature=None):
        self.api_key = api_key; self.api_base = api_base; self.default_model = model
        self.context_win = context_win; self.raw_msgs = []; self.messages = []
        self.proxies = {"http": proxy, "https": proxy} if proxy else None
        self.lock = threading.Lock()
        self.default_temperature = temperature
        self._consecutive_failures = 0

    def raw_ask(self, messages, model=None, temperature=None):
        if temperature is None:
            temperature = self.default_temperature if self.default_temperature is not None else 0.5
        if model is None: model = self.default_model
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json", "Accept": "text/event-stream"}
        payload = {"model": model, "messages": messages, "temperature": temperature, "stream": True}
        last_err = None
        for attempt in range(self.MAX_RETRIES):
            try:
                with requests.post(f"{self.api_base}/v1/chat/completions", headers=headers,
                                   json=payload, stream=True, timeout=(5, 120), proxies=self.proxies) as r:
                    if r.status_code in self.RETRYABLE_STATUS:
                        wait = self.RETRY_BASE_DELAY * (2 ** attempt) + random.uniform(0, 1)
                        print(f"[LLM] HTTP {r.status_code}, retry {attempt+1}/{self.MAX_RETRIES} in {wait:.1f}s...")
                        time.sleep(wait)
                        last_err = f"HTTP {r.status_code}: {r.text[:200]}"
                        continue
                    r.raise_for_status()
                    buffer = ''
                    call_start = time.time()
                    TOTAL_TIMEOUT = 300
                    for line in r.iter_lines():
                        if time.time() - call_start > TOTAL_TIMEOUT:
                            print(f"[LLM] Total timeout {TOTAL_TIMEOUT}s exceeded, aborting response")
                            break
                        line = line.decode("utf-8")
                        if not line or not line.startswith("data:"): continue
                        data = line[5:].lstrip()
                        if data == "[DONE]": break
                        obj = json.loads(data); ch = (obj.get("choices") or [{}])[0]
                        finish_reason = ch.get("finish_reason")
                        delta = (ch.get("delta") or {}).get("content")
                        if delta:
                            yield delta; buffer += delta
                            if '</tool_use>' in buffer[-30:]: break
                        if finish_reason: break
                    self._consecutive_failures = 0
                    return
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                wait = self.RETRY_BASE_DELAY * (2 ** attempt) + random.uniform(0, 1)
                print(f"[LLM] {type(e).__name__}, retry {attempt+1}/{self.MAX_RETRIES} in {wait:.1f}s...")
                time.sleep(wait)
                last_err = str(e)
                continue
            except Exception as e:
                last_err = str(e)
                break
        self._consecutive_failures += 1
        yield f"Error: {last_err or 'unknown'} (after {self.MAX_RETRIES} retries)"

    def make_messages(self, raw_list, omit_images=True):
        compress_history_tags(raw_list)
        messages = []
        for i, msg in enumerate(raw_list):
            prompt = msg['prompt']
            if omit_images and msg['image']: messages.append({"role": msg['role'], "content": "[Image omitted, if you needed it, ask me]\n" + prompt})
            elif not omit_images and msg['image']:
                messages.append({"role": msg['role'], "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{msg['image']}"}},
                    {"type": "text", "text": prompt} ]})
            else:
                messages.append({"role": msg['role'], "content": prompt})
        return messages
       
    def summary_history(self, model=None):
        if model is None: model = self.default_model
        with self.lock:
            keep = 0; tok = 0
            for m in reversed(self.raw_msgs):
                l = len(str(m))//4
                if tok + l > self.context_win*0.2: break
                tok += l; keep += 1
            keep = max(2, keep)
            old, self.raw_msgs = self.raw_msgs[:-keep], self.raw_msgs[-keep:]
            if len(old) == 0: old = self.raw_msgs; self.raw_msgs = []
            p = "Summarize prev summary and prev conversations into compact memory (facts/decisions/constraints/open questions). Do NOT restate long schemas. The new summary should less than 1000 tokens. Permit dropping non-important things.\n"
            messages = self.make_messages(old, omit_images=True)
            messages += [{"role":"user", "content":p}]
            msg_lens = [1000 if isinstance(m["content"], list) else len(str(m["content"]))//4 for m in messages]
            summary = ''.join(list(self.raw_ask(messages, model, temperature=0.1)))
            print('[Debug] Summary length:', len(summary)//4, '; Orig context lengths:', str(msg_lens))
            if not summary.startswith("Error:"): 
                self.raw_msgs.insert(0, {"role":"assistant", "prompt":"Prev summary:\n"+summary, "image":None})
            else: self.raw_msgs = old + self.raw_msgs   # 不做了，下次再做

    def ask(self, prompt, model=None, image_base64=None, stream=False):
        if model is None: model = self.default_model
        def _ask_gen():
            content = ''
            with self.lock:
                self.raw_msgs.append({"role": "user", "prompt": prompt, "image": image_base64})
                messages = self.make_messages(self.raw_msgs[:-1], omit_images=True)
                messages += self.make_messages([self.raw_msgs[-1]], omit_images=False)
                msg_lens = [1000 if isinstance(m["content"], list) else len(str(m["content"]))//4 for m in messages]
                total_len = sum(msg_lens)   # estimate token count
            gen = self.raw_ask(messages, model)
            for chunk in gen:
                content += chunk; yield chunk
            if not content.startswith("Error:"):
                self.raw_msgs.append({"role": "assistant", "prompt": content, "image": None})
            if total_len > 5000: print(f"[Debug] Whole context length {total_len} {str(msg_lens)}.")
            if total_len > self.context_win: 
                yield '[NextWillSummary]'
                threading.Thread(target=self.summary_history, daemon=True).start()
        if stream: return _ask_gen()
        return ''.join(list(_ask_gen())) 
        
  
class GeminiSession:
    def __init__(self, api_key=None, default_model="gemini-2.0-flash-001", proxy=proxy):
        self.api_key = api_key or google_api_key
        if not self.api_key: raise ValueError("google_api_key 未配置或为空，请在 mykey.py 中设置")
        self.default_model = default_model
        self.proxies = {"http":proxy, "https":proxy} if proxy else None
    def ask(self, prompt, model=None, stream=False):
        if model is None: model = self.default_model
        url = f"https://generativelanguage.googleapis.com/v1/models/{model}:generateContent?key={self.api_key}"
        headers = {"Content-Type":"application/json"}
        data = {"contents":[{"role":"user","parts":[{"text":prompt}]}]}
        retryable = {429, 500, 502, 503, 504}
        last_err = None
        for attempt in range(4):
            try:
                kw = {"headers":headers, "json":data, "timeout":60, 'proxies': self.proxies}
                r = requests.post(url, **kw)
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                wait = 3 * (2 ** attempt) + random.uniform(0, 1)
                print(f"[Gemini] {type(e).__name__}, retry {attempt+1}/4 in {wait:.1f}s...")
                time.sleep(wait); last_err = str(e); continue
            except Exception as e:
                return f"[GeminiError] request failed: {e}"
            if r.status_code in retryable:
                wait = 3 * (2 ** attempt) + random.uniform(0, 1)
                print(f"[Gemini] HTTP {r.status_code}, retry {attempt+1}/4 in {wait:.1f}s...")
                time.sleep(wait); last_err = f"HTTP {r.status_code}"; continue
            if r.status_code != 200:
                body = r.text[:500].replace("\n"," ")
                return f"[GeminiError] HTTP {r.status_code}: {body}"
            try:
                obj = r.json(); cands = obj.get("candidates") or []
                if not cands: return "[GeminiError] empty candidates"
                parts = (cands[0].get("content") or {}).get("parts") or []
                full_text = "".join(p.get("text","") for p in parts)
            except Exception as e:
                return f"[GeminiError] invalid response format: {e}"
            return iter([full_text]) if stream else full_text
        err_msg = f"[GeminiError] {last_err} (after retries)"
        return iter([err_msg]) if stream else err_msg

class XaiSession:
    def __init__(self, api_key, proxy="http://127.0.0.1:2082", default_model="grok-4-1-fast-non-reasoning"):
        import xai_sdk
        from xai_sdk.chat import user, system
        self._user, self._system = user, system
        self.default_model = default_model
        self._last_response_id = None  # 多轮对话链
        os.environ["XAI_API_KEY"] = api_key
        if not proxy.startswith("http"): proxy = f"http://{proxy}"
        os.environ.setdefault("grpc_proxy", proxy)
        self._client = xai_sdk.Client()
    def ask(self, prompt, model=None, system_prompt=None, stream=False):
        """发送消息，自动串联多轮对话；stream=True返回生成器"""
        mdl = model or self.default_model
        try:
            kw = dict(model=mdl, store_messages=True)
            if self._last_response_id: kw["previous_response_id"] = self._last_response_id
            chat = self._client.chat.create(**kw)
            if system_prompt: chat.append(self._system(system_prompt))
            chat.append(self._user(prompt))
            if stream: return self._stream(chat)
            resp = chat.sample()
            self._last_response_id = resp.id
            return resp.content
        except Exception as e:
            err = f"[XaiError] {e}"
            return iter([err]) if stream else err
    def _stream(self, chat):
        try:
            last_resp = None
            for resp, chunk in chat.stream():
                last_resp = resp
                if chunk and chunk.content: yield chunk.content
            if last_resp and hasattr(last_resp, 'id'): self._last_response_id = last_resp.id
        except Exception as e:
            yield f"[XaiError] {e}"
    def reset(self): self._last_response_id = None

class MockFunction:
    def __init__(self, name, arguments): self.name, self.arguments = name, arguments  
         
class MockToolCall:
    def __init__(self, name, args):
        arg_str = json.dumps(args, ensure_ascii=False) if isinstance(args, dict) else args
        self.function = MockFunction(name, arg_str)

class MockResponse:
    def __init__(self, thinking, content, tool_calls, raw):
        self.thinking = thinking        # 存放 <thinking> 内部的思维过程
        self.content = content          # 存放去除标签后的纯文本回复
        self.tool_calls = tool_calls    # 存放 MockToolCall 列表 或 None
        self.raw = raw
    def __repr__(self):    
        return f"<MockResponse thinking={bool(self.thinking)}, content='{self.content}', tools={bool(self.tool_calls)}>"

class ToolClient:
    def __init__(self, backends, auto_save_tokens=False):
        if isinstance(backends, list): self.backends = backends
        else: self.backends = [backends]
        self.backend = self.backends[0]
        self.auto_save_tokens = auto_save_tokens
        self.last_tools = ''
        self.total_cd_tokens = 0

    def chat(self, messages, tools=None):
        full_prompt = self._build_protocol_prompt(messages, tools)      
        print("Full prompt length:", len(full_prompt), 'chars')
        with open(f'./temp/model_responses_{os.getpid()}.txt', 'a', encoding='utf-8', errors="replace") as f:
            f.write(f"=== Prompt === {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n{full_prompt}\n")

        raw_text = ''
        tried_backends = set()
        original_idx = self.backends.index(self.backend) if self.backend in self.backends else 0

        for fallback_attempt in range(len(self.backends)):
            backend = self.backends[(original_idx + fallback_attempt) % len(self.backends)]
            backend_name = f"{type(backend).__name__}/{getattr(backend, 'default_model', '?')}"
            if id(backend) in tried_backends:
                continue
            tried_backends.add(id(backend))

            if fallback_attempt > 0:
                print(f"[ToolClient] Fallback to backend #{(original_idx + fallback_attempt) % len(self.backends)}: {backend_name}")

            gen = backend.ask(full_prompt, stream=True)
            raw_text = ''
            summarytag = '[NextWillSummary]'
            has_real_content = False
            for chunk in gen:
                raw_text += chunk
                if chunk != summarytag:
                    yield chunk
                if not chunk.startswith('Error:') and len(chunk.strip()) > 0:
                    has_real_content = True

            if raw_text.startswith('Error:') or (not has_real_content and len(raw_text.strip()) < 10):
                print(f"[ToolClient] Backend {backend_name} failed: {raw_text[:200]}")
                if fallback_attempt < len(self.backends) - 1:
                    wait = 2 * (fallback_attempt + 1)
                    print(f"[ToolClient] Waiting {wait}s before trying next backend...")
                    time.sleep(wait)
                    continue
            break

        print('Complete response received.')
        if raw_text.endswith(summarytag):
            self.last_tools = ''; raw_text = raw_text[:-len(summarytag)]
        with open(f'./temp/model_responses_{os.getpid()}.txt', 'a', encoding='utf-8', errors="replace") as f:
            f.write(f"=== Response === {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n{raw_text}\n\n")
        return self._parse_mixed_response(raw_text)

    def ask_block(self, prompt, max_tokens=None):
        """单轮纯文本补全（无工具协议），供 `_post_task_memory_extract` 等侧车调用。

        与 `chat()` 不同：不走 <thinking>/<tool_use> 模板。优先使用 backend.raw_ask
        单条 user 消息，避免向 LLMSession / ClaudeSession 的 raw_msgs 追加一轮对话。
        `max_tokens` 若当前后端未支持则忽略。
        """
        if not prompt:
            return None
        order = []
        if self.backend is not None:
            order.append(self.backend)
        for b in self.backends:
            if b not in order:
                order.append(b)
        if not order:
            return None
        one_shot = [{"role": "user", "content": prompt}]
        last_err = None
        for backend in order:
            try:
                if hasattr(backend, "raw_ask"):
                    gen = backend.raw_ask(one_shot)
                    text = "".join(list(gen))
                    if text and not str(text).startswith("Error:"):
                        return text
                    last_err = (text or "")[:300]
                    continue
                # Sider / Gemini / Xai 等：无 raw_ask 时用 ask(stream=False)
                try:
                    out = backend.ask(prompt, stream=False)
                except TypeError:
                    out = backend.ask(prompt)
                if isinstance(out, str):
                    if out and not out.startswith("Error:"):
                        return out
                    last_err = out[:300]
                    continue
                if hasattr(out, "__iter__") and not isinstance(out, (str, bytes)):
                    text = "".join(out)
                    if text and not text.startswith("Error:"):
                        return text
                    last_err = (text or "")[:300]
            except Exception as e:
                last_err = str(e)
                continue
        if last_err:
            print(f"[ToolClient.ask_block] failed: {last_err}")
        return None

    def _build_protocol_prompt(self, messages, tools):
        system_content = next((m['content'] for m in messages if m['role'].lower() == 'system'), "")
        history_msgs = [m for m in messages if m['role'].lower() != 'system']
        # 构造工具描述
        tool_instruction = ""
        if tools:
            tools_json = json.dumps(tools, ensure_ascii=False, separators=(',', ':'))
            tool_instruction = f"""
### 交互协议 (必须严格遵守，持续有效)
请按照以下步骤思考并行动，标签之间需要回车换行：
1. **思考**: 在 `<thinking>` 标签中先进行思考，分析现状和策略。
2. **总结**: 在 `<summary>` 中输出*极为简短*的高度概括的单行（<30字）物理快照，包括上次工具调用结果获取的新信息+本次工具调用意图和预期。此内容将进入长期工作记忆，记录关键信息，严禁输出无实际信息增量的描述。
3. **行动**: 如需调用工具，请在回复正文之后输出一个 **<tool_use>块**，然后结束，我会稍后给你返回<tool_result>块。
   格式: ```<tool_use>\n{{"name": "工具名", "arguments": {{参数}}}}\n</tool_use>\n```

### 可用工具库（已挂载，持续有效）
{tools_json}
"""
            if self.auto_save_tokens and self.last_tools == tools_json:
                tool_instruction = "\n### 工具库状态：持续有效（code_run/file_read等），**可正常调用**。调用协议沿用。\n"
            else:
                self.total_cd_tokens = 0
            self.last_tools = tools_json
            
        prompt = ""
        if system_content: prompt += f"=== SYSTEM ===\n{system_content}\n"
        prompt += f"{tool_instruction}\n\n"
        for m in history_msgs:
            role = "USER" if m['role'] == 'user' else "ASSISTANT"
            prompt += f"=== {role} ===\n{m['content']}\n\n"
            self.total_cd_tokens += len(m['content'])
            
        if self.total_cd_tokens > 6000: self.last_tools = ''

        prompt += "=== ASSISTANT ===\n" 
        return prompt

    def _parse_mixed_response(self, text):
        remaining_text = text; thinking = ''
        think_pattern = r"<thinking>(.*?)</thinking>"
        think_match = re.search(think_pattern, text, re.DOTALL)
        
        if think_match:
            thinking = think_match.group(1).strip()
            remaining_text = re.sub(think_pattern, "", remaining_text, flags=re.DOTALL)
        
        tool_calls = []; json_strs = []; errors = []
        tool_pattern = r"<tool_use>(.{15,}?)</tool_use>"
        tool_all = re.findall(tool_pattern, remaining_text, re.DOTALL)
        
        if tool_all:
            tool_all = [s.strip() for s in tool_all]
            json_strs.extend([s for s in tool_all if s.startswith('{') and s.endswith('}')])
            remaining_text = re.sub(tool_pattern, "", remaining_text, flags=re.DOTALL)
        elif '<tool_use>' in remaining_text:
            weaktoolstr = remaining_text.split('<tool_use>')[-1].strip()
            json_str = weaktoolstr if weaktoolstr.endswith('}') else ''
            if json_str == '' and '```' in weaktoolstr and weaktoolstr.split('```')[0].strip().endswith('}'):
                json_str = weaktoolstr.split('```')[0].strip()
            if json_str:
                json_strs.append(json_str)
            remaining_text = remaining_text.replace('<tool_use>'+weaktoolstr, "")
        elif '"name":' in remaining_text and '"arguments":' in remaining_text:
            json_match = re.search(r"(\{.*\"name\":.*?\})", remaining_text, re.DOTALL | re.MULTILINE)
            if json_match:
                json_str = json_match.group(1).strip()
                json_strs.append(json_str)
                remaining_text = remaining_text.replace(json_str, "").strip()

        for json_str in json_strs:
            try:
                data = tryparse(json_str)
                func_name = data.get('name') or data.get('function') or data.get('tool')
                args = data.get('arguments') or data.get('args') or data.get('params') or data.get('parameters')
                if args is None: args = data
                if func_name: tool_calls.append(MockToolCall(func_name, args))
            except json.JSONDecodeError as e:
                errors.append({'err': f"[Warn] Failed to parse tool_use JSON: {json_str}", 'bad_json': f'Failed to parse tool_use JSON: {json_str[:200]}'})
                self.last_tools = ''   # llm肯定忘了tool schema了，再提供下
            except Exception as e:
                errors.append({'err': f'[Warn] Exception during tool_use parsing: {str(e)} {str(data)}'})
        if len(tool_calls) == 0:
            for e in errors:
                print(e['err'])
                if 'bad_json' in e: tool_calls.append(MockToolCall('bad_json', {'msg': e['bad_json']}))
        content = remaining_text.strip()
        return MockResponse(thinking, content, tool_calls[-1:], text)

def tryparse(json_str):
    try: return json.loads(json_str)
    except: pass
    json_str = json_str.strip().strip('`').replace('json\n', '', 1).strip()
    try: return json.loads(json_str)
    except: pass
    try: return json.loads(json_str[:-1])
    except: pass
    if '}' in json_str: json_str = json_str[:json_str.rfind('}') + 1]
    return json.loads(json_str)

if __name__ == "__main__":
    import sys, os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        import mykey
    except ImportError:
        class MockMyKey: pass
        mykey = MockMyKey()
    
    mykeys = vars(mykey)
    sider_cookie = mykeys.get("sider_cookie")
    oai_configs = {
        k: v for k, v in vars(mykey).items() if k.startswith("oai_config") and v
    }
    google_api_key = mykeys.get("google_api_key")
    cfg = oai_configs.get("oai_config")

    llmclient = ToolClient(GeminiSession(api_key=google_api_key, proxy='127.0.0.1:2082').ask)
    #llmclient = ToolClient(LLMSession(api_key=cfg['apikey'], api_base=cfg['apibase'], model=cfg['model']).ask)
    #llmclient = ToolClient(SiderLLMSession().ask)
    def get_final(gen):
        try:
            while True: print('mid:', next(gen))
        except StopIteration as e:
            return e.value
        
    response = get_final(llmclient.chat(
        messages=[{"role": "user", "content": "我的IP是多少"}], 
        tools=[{"name": "get_ip", "parameters": {}}]
    ))
    print(f"思考: {response.thinking}") 
    if response.tool_calls:
        cmd = response.tool_calls[0]
        print(f"调用: {cmd.function.name} 参数: {cmd.function.arguments}")

    response = get_final(llmclient.chat(
        messages=[{"role": "user", "content": "<tool_result>10.176.45.12</tool_result>"}] 
    ))
    print(response.content)
