# 复制本文件为 mykey.py 并填入你的 API 信息，切勿将 mykey.py 提交到 Git。
# Copy this file to mykey.py and fill in your API keys. Never commit mykey.py.

# OpenAI 兼容接口（或自建/代理）
oai_config = {
    'apikey': 'YOUR_OPENAI_OR_PROXY_API_KEY',
    'apibase': 'https://api.openai.com/v1',  # 或你的代理地址
    'model': 'gpt-4o'
}

# Qwen / DashScope OpenAI-compatible 示例：
# 复制到本地 mykey.py 后，把 apikey 改成真实密钥。mykey.py 已被 .gitignore 忽略。
# oai_config = {
#     'apikey': 'YOUR_DASHSCOPE_API_KEY',
#     'apibase': 'https://dashscope.aliyuncs.com/compatible-mode/v1',
#     'model': 'qwen3.7-plus'
# }

# 可选：Sider 等
# sider_cookie = 'YOUR_SIDER_COOKIE_IF_NEEDED'

# 可选：更多 LLM 后端
# oai_config2 = { 'apikey': '...', 'apibase': '...', 'model': '...' }
# claude_config = { 'apikey': '...', 'apibase': '...', 'model': '...' }

# 可选：Telegram Bot
# tg_bot_token = 'YOUR_BOT_TOKEN'
# tg_allowed_users = [123456789]

# 可选：飞书 Bot（在 https://open.feishu.cn/ 创建企业自建应用，开启机器人+WebSocket模式）
# fs_app_id = 'cli_xxxxx'           # 飞书应用 App ID
# fs_app_secret = 'xxxxx'           # 飞书应用 App Secret
# fs_allowed_users = ['ou_xxxxx']   # 允许使用的用户 open_id 列表（空=不限制）

# 可选：跨设备外部告警监听（另一个 OpenClaw 节点可通过 HTTP POST 发事件过来）
# fs_enable_external_alert_server = True
# fs_external_alert_host = '127.0.0.1'   # 跨设备联通时改为 0.0.0.0
# fs_external_alert_port = 8787
# fs_external_alert_token = 'CHANGE_ME'
# cross_device_node_id = 'child_01'
# fs_external_alert_targets = {
#     'child_01': 'ou_xxxxx',            # 逻辑 target_id -> 飞书 open_id
# }

# 可选：代理
# proxy = "http://127.0.0.1:2082"
