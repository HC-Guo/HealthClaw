# 手机控制 SOP (Phone Control via ADB)

> **must call update working ckp**：`手机操控用phone_control工具｜仅任务开始首次check_connection｜每步操作后截图确认（仅失败/疑似断开时再重查）`

## 文档定位与写入边界（强约束）
- 本文档是**通用手机控制 SOP**，仅包含 `phone_control` / `phone_screen_analyze` 的通用操作原语与容错策略。
- **禁止**在本文档写入任何具体 App 的业务流程、页面路径、分析模板与领域结论。
- 若出现任务特化经验（如外卖健康分析、社交App分析、运动数据解读），必须写入 `memory/L3_sops/<task>_sop.md`（示例：`meituan_food_analysis_sop.md`）。
- 本文档只允许保留“参考某任务 SOP”的导航，不承载任务细节。

### 写入判定规则
若新增内容满足任一条件，禁止写入本文件：
1. 含具体 App 名称 + 连续步骤链路（如“打开X→点击Y→进入Z”）
2. 含业务目标分析流程（如“订单健康评分/消费结构分析”）
3. 含仅对单一 App 成立的页面路径或固定坐标假设

## 前置条件
- Android 手机已通过 USB 连接电脑，或在同一 WiFi 下通过 `adb connect <ip>:5555` 连接
- 手机已开启 USB 调试（设置 → 开发者选项 → USB调试）
- 电脑已安装 adb：`brew install android-platform-tools`（macOS）

## 操作流程（感知-决策-执行循环）

### Step 1: 检查连接
```
phone_control(action="check_connection")  # 仅任务开始首次执行；后续失败才重查
```
确认手机已连接、型号、分辨率。

### Step 2: 感知当前界面
两种方式（按优先级）：
1. **UI Dump**（文本解析，快速精确）：
   ```
   phone_control(action="ui_dump", keyword="可选过滤词")
   ```
   返回所有 UI 元素的文本、坐标、是否可点击。
   
2. **截图分析**（视觉理解，适合复杂界面）：
   ```
   phone_control(action="screenshot_analyze", question="当前页面结构和可操作区域是什么？")
   ```
   截取屏幕并通过 LLM 视觉能力分析。

### Step 3: 决策下一步操作
根据感知结果，决定：
- 需要点击哪个元素？→ 使用元素的 (cx, cy) 坐标
- 需要滑动查看更多？→ scroll_down / scroll_up
- 需要输入文字？→ input_text
- 需要返回？→ press_key(back)

### Step 4: 执行操作
```
phone_control(action="tap", x=540, y=1200)        # 点击
phone_control(action="swipe", x1=540, y1=1600, x2=540, y2=400)  # 滑动
phone_control(action="input_text", text="示例输入")    # 输入
phone_control(action="press_key", key="back")       # 返回
phone_control(action="launch_app", app="目标应用名或包名")  # 启动App
```
**启动失败时**（以 Agent 自行匹配为准，工具只做兜底）：
1. **主流程**：工具仅返回本机已安装应用列表（完整或前 N 个）。**由 Agent 根据用户描述与该列表自行做关键词/语义匹配**，选出最可能的目标包名并用 `launch_app(app="包名")` 重试。不依赖代码内预置关键词表。
2. **兜底**：若 Agent 判断列表中**无与用户描述相关的包**，则停止任务并向用户说明，或建议用户说出具体应用名称。勿把预置名称（如「华为健康」）当成本机已安装。

### Step 5: 验证操作结果
**每次操作后必须**等待 1-2 秒，然后重新感知界面：
```
phone_control(action="ui_dump")
```
确认操作是否成功，再决定下一步。

## 避坑指南
- **等待加载**：App 页面切换后等 1-2 秒再 dump，否则会拿到过渡动画
- **弹窗处理**：先 ui_dump(clickable_only=True) 找关闭按钮
- **中文输入**：需要安装 ADBKeyboard，否则只能输入英文/数字
- **支付确认**：涉及支付操作时**必须先用 ask_user 确认**
- **坐标系统**：tap/swipe 使用手机的物理像素坐标（即截图上的坐标）
- **连接断开**：长时间操作可能断开；仅当 tap/screenshot/ui_dump 报错或判断疑似未连接时再调用 `check_connection`
