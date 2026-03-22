# Web 工具链初始化执行 SOP

若 web_scan 和 web_execute_js 已测试可用，无需执行此 SOP。
仅供初始安装时，code_run 可用但 web 工具尚未配置的场景。

## 目标
在仅具备系统级权限（code_run）时，建立 Web 交互能力（web_scan / web_execute_js）。底层为 TMWebDriver + Tampermonkey 注入真实浏览器（保留登录态/Cookie）。**本框架所有浏览器访问（含 browser_*、browse_and_learn）均通过此方式，与 pc-agent-loop 一致。**

## 前置：检测浏览器
```python
import shutil, subprocess
browser = "chrome" if shutil.which("chrome") else "msedge"  # Edge内置必存在，Chrome可选
```

## 阶段一：安装 Tampermonkey (手动)
**状态**: 尚未实现自动化，需用户手动操作。
1. 用 `start` 打开扩展商店页面（自动适配浏览器）：
   - Chrome: `start "" "https://chromewebstore.google.com/detail/篡改猴测试版/gcalenpjmijncebpfijmoaglllgpjagf"`
   - Edge: `start "" "https://microsoftedge.microsoft.com/addons/detail/tampermonkey/iikmkjmpaadaobahmlepeloendndfphd"`
2. 提示用户点击「安装」并确认。

## 阶段 1.5：开启「允许运行用户脚本」
**前置**：TM 已安装，但 Chrome 可能默认未开启此权限。
需打开 TM 的扩展详情页，手动开启相关开关。

### 自动打开详情页
1. 从文件系统读取 TM 扩展 ID：
   ```python
   import os, json, glob
   ext_dir = os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\User Data\Default\Extensions')
   for eid in os.listdir(ext_dir):
       for ver in glob.glob(os.path.join(ext_dir, eid, '*')):
           mf = os.path.join(ver, 'manifest.json')
           if os.path.isfile(mf):
               with open(mf, encoding='utf-8') as f:
                   m = json.load(f)
               if 'tampermonkey' in m.get('name','').lower() or 'tampermonkey' in m.get('description','').lower():
                   tm_id = eid; break
   ```
2. 导航到 `chrome://extensions/?id={tm_id}`：
   - ⚠️ `chrome://` 协议无法通过命令行参数或 JS(`window.open`) 打开
   - ✅ 用 ljqCtrl（需先打开一个 Chrome 窗口并置顶）或剪贴板+地址栏方案：
     ```python
     # 剪贴板方案：写入URL → Ctrl+L → Ctrl+V → Enter
     import win32clipboard
     win32clipboard.OpenClipboard(); win32clipboard.EmptyClipboard()
     win32clipboard.SetClipboardText(f'chrome://extensions/?id={tm_id}')
     win32clipboard.CloseClipboard()
     # 然后用 ljqCtrl 或 SendKeys 发送 Ctrl+L, Ctrl+V, Enter
     ```
3. 提示用户在详情页中开启「允许运行用户脚本」开关。

## 阶段二：安装 ljq_web_driver.user.js
**脚本路径**: `assets/ljq_web_driver.user.js`（相对代码根，即 seda_main.py 所在目录）

### 方案A（自动化，优先）
本地 HTTP 服务器 + TM 中间页，用 `start` 命令打开：
1. Python 启动 `http.server` 托管脚本（Content-Type: text/javascript）
   - ⚠️ 必须用 `Popen(..., stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)` 丢弃输出
   - ❌ 禁用 `stdout=PIPE` 或 `stderr=PIPE`，会导致缓冲区满后服务器阻塞返回空响应
   - Windows 可加 `creationflags=subprocess.CREATE_NO_WINDOW` 避免弹窗
2. `start "" "https://www.tampermonkey.net/script_installation.php#url=http://127.0.0.1:{port}/ljq_web_driver.user.js"`
   - ⚠️ 以上步骤均须用 `Popen` 非阻塞执行，禁止 `subprocess.run`（会等待进程结束）
   - 服务器需持续运行直到用户完成安装，用 `Popen` 启动后立即返回继续执行
3. TM 秒弹安装确认，用户点「安装」即可

### 方案B（手动 fallback）
若方案A失败，用剪贴板：
1. 读取脚本内容 → `pyperclip.copy()`
2. 通知用户在 TM 中【新建脚本 → 全选 → 粘贴 → 保存】

## 阶段 2.5：安装 CDP 桥扩展 ⭐新增
**扩展路径**：`assets/tmwd_cdp_bridge/`
CDP 桥让 agent 获得截图、isTrusted 事件派发、文件上传等原生浏览器能力。

### 安装步骤
1. **自动生成 config.js**（首次启动 SEDA 时自动执行）：
   ```python
   # ga.py 中的 ensure_cdp_config() 会自动检测并生成
   # 生成后 assets/tmwd_cdp_bridge/config.js 内容如：
   # const TID = '__ljq_ctrl_a1b2c3d4';
   ```
2. **Chrome 加载扩展**：
   - 打开 `chrome://extensions/`，开启「开发者模式」
   - 点击「加载已解压的扩展程序」，选择 `assets/tmwd_cdp_bridge/` 目录
   - 首次加载时 Chrome 会提示 debugger 权限警告，点击确认
3. **验证**：
   - 扩展列表中应出现「TMWD CDP Bridge」
   - 点击扩展图标，弹出 Cookies 面板即表示安装成功
   - 在 SEDA 中调用 `browser_screenshot` 工具验证截图功能

### macOS 注意事项
- macOS 的 Chrome 扩展路径为 `~/Library/Application Support/Google/Chrome/Default/Extensions/`
- 阶段 1.5 中读取 TM 扩展 ID 的路径需调整为上述目录
- `start` 命令替换为 `open`

## 阶段三：启动 TMWebDriver 并验证
1. 在代码根目录运行：`python TMWebDriver.py`（或由 SEDA 在需要时启动 WebSocket ws://localhost:18765 与 HTTP 18766）。
2. 打开已安装 Tampermonkey 脚本的浏览器，访问任意网页，页面右下角应出现「ljq_driver: 连接成功」。
3. 调用 `web_scan` 或注入 JS 心跳检测，确认脚本已生效。
4. **可选**：调用 `browser_screenshot` 验证 CDP 桥（需已完成阶段 2.5）。

## 避坑 (Chromium untrusted 拦截)
- ❌ 直接导航到 `localhost/.user.js` → Chromium 弹 untrusted 拦截 +「另存为」，延迟约1分钟
- ✅ 必须用 `start` 命令（系统级）打开 TM 中间页 URL → 秒弹安装，无拦截
- 此问题 Chrome 和 Edge 均存在（Chromium 内核通病）
