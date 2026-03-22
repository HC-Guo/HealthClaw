# TMWebDriver SOP（浏览器注入方案 — 与 pc-agent-loop 一致）

SEDA 的浏览器访问**统一使用篡改猴 + TMWebDriver**（见 `web_setup_sop.md`）。browser_navigate、browser_click、browser_get_content、browser_search、browse_and_learn、browser_screenshot、cdp_command 等均为在此之上的封装，不再使用 Playwright。

- 禁止在业务代码中 import TMWebDriver 内部实现；通过高层工具（如 web_scan / web_execute_js）使用。
- 底层：TMWebDriver.py + Tampermonkey 脚本接管用户浏览器（保留 Cookie/登录态），非 Selenium/Playwright。

## 限制 (isTrusted)

- JS dispatch 的事件 `isTrusted=false`，文件上传、部分按钮可能被浏览器拦截。
- **⭐首选绕过：CDP 桥**——CDP 派发的 Input 事件为浏览器原生级别 (isTrusted=true)，且无需前台，见下方 CDP 章节。
- 文件上传：JS 无法填充 `<input type=file>`
  - ⭐首选 CDP batch：getDocument → querySelector → DOM.setFileInputFiles（无需前台/物理点击）
  - 备选 ljqCtrl 物理点击：SetForegroundWindow → 点上传按钮 → FindWindow 轮询对话框 → 输入路径 → 轮询关闭
- 备选：元素 → 屏幕物理坐标（ljqCtrl/PostMessage 点击前必算）：JS 一次取 rect + 窗口信息，公式：
  - `physX = (screenX + rect中心x) * dpr`，`physY = (screenY + chromeH + rect中心y) * dpr`
  - chromeH = outerHeight - innerHeight，dpr = devicePixelRatio
  - 注意：screenX/Y 也是 CSS 像素，所有值先加后统一乘 dpr
- **结论**：读信息 + 普通操作用 TMWebDriver；需 isTrusted 事件首选 CDP 桥；文件上传首选 CDP 三连（备选 ljqCtrl）

## 导航

- `web_scan` 仅读当前页不导航，切换网站用 `web_execute_js` + `location.href='url'`

## Google 图搜

- class 名混淆禁硬编码，点击结果用 `[role=button]` div
- web_scan 过滤边栏，弹出后用 JS：文本 `document.body.innerText`，大图遍历 img 按 `naturalWidth` 最大取 src
- "访问" 链接：遍历 a 找 `textContent.includes('访问')` 的 href
- 缩略图：`img[src^="data:image"]` 直接提取；大图 src 可能截断用 `return img.src`

## Chrome 下载 PDF

场景：PDF 链接在浏览器内预览而非下载
```js
fetch('PDF_URL').then(r=>r.blob()).then(b=>{
  const a=document.createElement('a');
  a.href=URL.createObjectURL(b);
  a.download='filename.pdf';
  a.click();
});
```
跨域时需先导航到目标域或 CORS 允许。

## Chrome 后台标签节流

- 后台标签中 `setTimeout` 被 Chrome intensive throttling 延迟到 ≥1min/次
- TM 脚本中 detect_newtab 的轮询已修复：移除 TM 脚本内轮询，改由 Python 侧 `get_session_dict()` 前后对比检测新标签
- 同理：TM 脚本中任何后台逻辑都应避免依赖 setTimeout 轮询

## CDP 桥 (tmwd_cdp_bridge 扩展) ⭐首选

扩展路径：`assets/tmwd_cdp_bridge/`（需安装，含 debugger 权限）

### TID 密钥
⚠ 首次运行自动生成到 `assets/tmwd_cdp_bridge/config.js`（已 gitignore），扩展通过 manifest 引用。
自动生成逻辑在 `ga.py` 的 `ensure_cdp_config()` 中，格式为：
```js
const TID = '__ljq_ctrl_xxxxxxxx';
```

### 调用方式
MutationObserver 监听 addedNodes (id=TID)，⚠ 每次必须 remove 旧 → createElement 新 → 设 textContent JSON → appendChild
```js
const TID = '从config.js读取的值';
const old = document.getElementById(TID);
if (old) old.remove();
const el = document.createElement('div');
el.id = TID; el.style.display = 'none';
el.textContent = JSON.stringify({cmd:'...', ...});
document.body.appendChild(el);  // 响应写回 el.textContent
```

### 可用命令
- 单命令：`{cmd:'tabs'}` | `{cmd:'cookies'}` | `{cmd:'cdp', tabId:N, method:'...', params:{...}}`
- ⭐batch 混合：`{cmd:'batch', commands:[{cmd:'cookies'},{cmd:'tabs'},{cmd:'cdp',...},...]}`
  - 返回 `{ok:true, results:[...]}`，一次请求多命令，CDP 懒 attach 复用 session
  - `$N.path` 引用第 N 个结果字段 (0-indexed)，如 `"nodeId":"$2.root.nodeId"`
  - 典型：文件上传三连 getDocument → querySelector(input[type=file]) → setFileInputFiles
  - ⚠ tabId：CDP 默认 sender.tab.id（当前注入页），跨 tab 需显式 tabId 或先 batch 内 tabs 查
- CDP 可用任意方法 (Input/Network/DOM/Page/Runtime/Emulation 等)，单条每次 attach → send → detach
- ⭐跨 tab 无需前台：指定 tabId 即可操作后台标签页
- ⭐绕过 isTrusted：CDP 派发的 Input 事件是浏览器原生级别

### 截图（SEDA 可直接用 `browser_screenshot` 工具）
```js
// 内部实现：通过 CDP Page.captureScreenshot 获取 base64 PNG
{cmd:'cdp', method:'Page.captureScreenshot', params:{format:'png'}}
// 返回 {ok:true, data:{data:'base64...'}}
```
- 无需前台，后台 tab 也可截图，全页高清
- 验证码 canvas/img 可用 JS `canvas.toDataURL()` 直接拿 base64 更干净
- SEDA 封装了 `browser_screenshot` 工具，自动执行上述流程并保存到文件

### autofill 获取
检测：web_scan 输出 input 带 `data-autofilled="true"`，value 显示为受保护提示
- ⭐首选 CDP 单次点击：JS 取任一 autofill 输入框坐标 → CDP `Input.dispatchMouseEvent` mousePressed 一次即可释放 → JS 读 `.value`
  - ⚠ 点击一个 autofill 字段会释放页面上**所有** autofill 字段的值
  - ⚠ 只需 mousePressed，不需要 mouseReleased 配对
  - 示例 (当前页)：`{cmd:'cdp',method:'Input.dispatchMouseEvent',params:{type:'mousePressed',x:X,y:Y,button:'left',clickCount:1}}`
  - ⚠ batch 的 `$N.path` 引用会将整数 tabId 转为字符串导致类型错误，跨 tab 时建议分两次命令

## 跨域 iframe 操控 (postMessage 中继)

- 跨域 iframe 的 contentDocument 不可访问，web_execute_js 只在顶层执行
- TM 脚本已改造：iframe 内不 return，改为监听 postMessage 并 eval 执行 + 回传结果
- 顶层发送：`iframe.contentWindow.postMessage({type:'ljq_exec', id, code}, '*')`
- iframe 回传：`{type:'ljq_result', id, result}` 通过 window.addEventListener('message') 接收
- ⚠ 只能 eval 表达式，不支持 return/函数体包装
- 流程：发 postMessage → 等 → 读 window._ljqResults[id] 获取结果
