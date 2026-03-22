import json, re
from dataclasses import dataclass
from typing import Any, Optional
@dataclass
class StepOutcome:
    data: Any
    next_prompt: Optional[str] = None
    should_exit: bool = False

def try_call_generator(func, *args, **kwargs):
    ret = func(*args, **kwargs)
    if hasattr(ret, '__iter__') and not isinstance(ret, (str, bytes, dict, list)):
        ret = yield from ret
    return ret

class BaseHandler:
    def tool_before_callback(self, tool_name, args, response): pass
    def tool_after_callback(self, tool_name, args, response, ret): pass
    def next_prompt_patcher(self, next_prompt, outcome, turn): return next_prompt
    def dispatch(self, tool_name, args, response):
        method_name = f"do_{tool_name}"
        if hasattr(self, method_name):
            _ = yield from try_call_generator(self.tool_before_callback, tool_name, args, response)
            ret = yield from try_call_generator(getattr(self, method_name), args, response)
            _ = yield from try_call_generator(self.tool_after_callback, tool_name, args, response, ret)
            return ret
        elif tool_name == 'bad_json':
            return StepOutcome(None, next_prompt=args.get('msg', 'bad_json'), should_exit=False)
        else:
            yield f"未知工具: {tool_name}\n"
            return StepOutcome(None, next_prompt=f"未知工具 {tool_name}", should_exit=False)

def json_default(o):
    if isinstance(o, set): return list(o)
    return str(o) 

def exhaust(g):
    try: 
        while True: next(g)
    except StopIteration as e: return e.value

def get_pretty_json(data):
    if isinstance(data, dict) and "script" in data:
        data = data.copy()
        data["script"] = data["script"].replace("; ", ";\n  ")
    return json.dumps(data, indent=2, ensure_ascii=False).replace('\\n', '\n')

def _build_user_content(text, image_base64=None):
    """构建用户消息 content：纯文本或多模态（图片+文字）"""
    if not image_base64:
        return text
    content = []
    content.append({
        "type": "image_url",
        "image_url": {"url": f"data:image/png;base64,{image_base64}"}
    })
    content.append({"type": "text", "text": text})
    return content

def _is_llm_error_response(response):
    """检测 LLM 响应是否为错误（429/5xx 等穿透上来的 Error）"""
    if response.raw and response.raw.strip().startswith('Error:'):
        return True
    if response.content and response.content.strip().startswith('Error:'):
        return True
    return False

LLM_ERROR_MAX_RETRIES = 2
LLM_ERROR_RETRY_WAIT = 10

def agent_runner_loop(client, system_prompt, user_input, handler, tools_schema, max_turns=15, verbose=True, image_base64=None):
    first_content = _build_user_content(user_input, image_base64)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": first_content}
    ]
    import time as _time

    tracker = getattr(handler, 'tracker', None)
    if tracker:
        tracker.task_goal = str(user_input)[:300]

    for turn in range(max_turns):
        handler._current_turn = turn + 1
        yield f"**LLM Running (Turn {turn+1}) ...**\n\n"
        if (turn+1) % 10 == 0: client.last_tools = ''

        response = None
        for llm_retry in range(LLM_ERROR_MAX_RETRIES + 1):
            response_gen = client.chat(messages=messages, tools=tools_schema)
            response = yield from response_gen
            if not _is_llm_error_response(response):
                break
            if llm_retry < LLM_ERROR_MAX_RETRIES:
                err_msg = (response.raw or response.content or '')[:200]
                yield f"\n⚠️ **LLM 返回错误** (retry {llm_retry+1}/{LLM_ERROR_MAX_RETRIES}): `{err_msg}`\n"
                yield f"等待 {LLM_ERROR_RETRY_WAIT}s 后重试...\n\n"
                _time.sleep(LLM_ERROR_RETRY_WAIT)

        if _is_llm_error_response(response):
            err_msg = (response.raw or response.content or '')[:300]
            yield f"\n❌ **LLM 持续不可用**: `{err_msg}`\n"
            yield "框架将暂停当前轮次。你可以稍后重试，或切换 LLM 后端。\n"
            if tracker:
                tracker.total_turns = turn + 1
                tracker.record_failure("LLM", "", err_msg, turn + 1)
                tracker.save_report()
            return {'result': 'LLM_ERROR', 'data': {'error': err_msg}}

        if verbose: yield '\n\n'

        if not response.tool_calls:
            tool_name, args = 'no_tool', {}
        else:
            tool_call = response.tool_calls[0] 
            tool_name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)

        if tool_name == 'no_tool': pass
        else: 
            showarg = get_pretty_json(args)
            if not verbose and len(showarg) > 200: showarg = showarg[:200] + ' ...'
            yield f"🛠️ **正在调用工具:** `{tool_name}`  📥**参数:**\n````text\n{showarg}\n````\n" 
        gen = handler.dispatch(tool_name, args, response)
        if verbose:
            yield '`````\n'
            outcome = yield from gen
            yield '`````\n'
        else:
            outcome = exhaust(gen)

        if outcome.next_prompt is None:
            if tracker:
                tracker.total_turns = turn + 1
                tracker.save_report()
            return {'result': 'CURRENT_TASK_DONE', 'data': outcome.data}
        if outcome.should_exit:
            if tracker:
                tracker.total_turns = turn + 1
                tracker.save_report()
            return {'result': 'EXITED', 'data': outcome.data}
        if outcome.next_prompt.startswith('未知工具'): client.last_tools = ''

        next_prompt = ""
        if outcome.data is not None: 
            datastr = json.dumps(outcome.data, ensure_ascii=False, default=json_default) if type(outcome.data) in [dict, list] else str(outcome.data) 
            next_prompt += f"<tool_result>\n{datastr}\n</tool_result>\n\n"
        next_prompt += outcome.next_prompt
        next_prompt = handler.next_prompt_patcher(next_prompt, outcome, turn+1)
        messages = [{"role": "user", "content": next_prompt}]

    if tracker:
        tracker.total_turns = max_turns
        report_path = tracker.save_report()
        yield f"\n📋 **已达到最大轮次 ({max_turns})**，Session Report 已保存: `{report_path}`\n"
        yield "建议查看 report 审阅执行轨迹和自主决策记录。\n"
    return {'result': 'MAX_TURNS_EXCEEDED'}