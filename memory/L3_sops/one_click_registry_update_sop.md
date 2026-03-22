# 一键健康分析：子任务注册表主动更新 SOP

> **适用场景**：用户在 Streamlit 点击「主动更新子任务注册表」，且当前任务已带白名单 `one_click_registry_update`（允许对主 SOP 的 **subtasks JSON** 执行 `file_patch`）。白名单键名与 `mode=` 常量定义见 **`tools/one_click_health.py`**（`TASK_KEY_REGISTRY_UPDATE`、`MODE_REGISTRY_UPDATE` 等），勿在 prompt 中自创别名。

> **勿删本文件**：本规程与 `tools/one_click_health.py` 互补——代码管「谁能改、怎么进站」，本文管「改什么、怎么改、如何校验」。

## 硬性规则

1. **先读规程再动手**：完整阅读本文件与 `memory/L3_sops/one_click_health_analysis_sop.md`。
2. **主 SOP 分层**：
   - `<!-- REGISTRY` … 至首个 **JSON 代码块**（以 markdown 代码围栏 `json` 语言标记包裹的 `subtasks` 对象）：**唯一**允许在白名单任务中 `file_patch` 修改的区域（最小增量：追加数组项或替换整段 JSON，须保持合法 JSON）。
   - `<!-- PROTECTED:BEGIN` 至 `<!-- PROTECTED:END`：**禁止** `file_patch` / `file_write` 修改（代码层对 `file_write` 整文件亦永久拒绝该路径）。
3. **新 App 流程**：详细步骤**只**写在新建文件 `memory/L3_sops/<slug>_sop.md`，**不要**把子流程抄进主 SOP 的 PROTECTED 区。
4. **L1 同步**：在 `memory/L1_disease_insight.txt` 的 `## [ONE_CLICK_HEALTH]` 小节中，用 `file_patch` **最小增量**增加或修正指针行，格式与 JSON 一致：
   - `{子任务id}→sop:{sop_file 去掉 .md 后缀}|tool:phone_control,phone_screen_analyze`（按需追加 `analyze_lifestyle` 等，须与子 SOP 实际工具一致）。
5. **校验（推荐）**：用 `code_run` 读取主 SOP 中第一个 `json` 语言围栏内的对象（与 `tools/one_click_health.load_subtasks_from_main_sop` 的解析规则一致），`json.loads` 成功且每个 `subtasks[].id` 唯一；失败则修正 patch 后重试。

## 执行步骤

### Step 1：理解上下文

- 阅读用户提供的「近期对话摘要」，判断**上一轮/最近一次**是否完成了**新的、可复用多步流程**（与现有 `subtasks[].id` 对比）。
- 若仅为已有子任务的重复执行、或流程未验证稳定：**不要**改注册表；向用户说明原因即可。

### Step 2：若确认为新子任务类型

1. 若尚无独立 SOP：用 `file_write` **新建** `memory/L3_sops/<slug>_sop.md`（仅 App 操作步骤、验证点、失败处理；不含一键综合报告模板）。
2. 对主 SOP **仅** `file_patch`：在 `subtasks` 数组中**追加**一项，字段建议：
   - `id`：全局唯一 snake_case
   - `name` / `description`：简短中文
   - `sop_file`：与新建文件名一致，如 `huawei_export_health_analysis_sop.md`
   - `enabled_by_default`：新任务建议 `false`，由用户在 UI 勾选启用
3. `file_patch` 更新 L1 的 `## [ONE_CLICK_HEALTH]`（保持小节存在；只改指针行，勿动其他疾病映射区块）。

### Step 3：收尾

- 简要列出变更：新增 SOP 路径、JSON 新增项、`[ONE_CLICK_HEALTH]` 新增行。
- （可选）`ask_user` 展示拟追加的 JSON 片段 diff，用户确认后再提交 patch。

## 禁止事项

- 不要用长期记忆自动学习替代本流程去改主 SOP 或 L1 注册指针。
- 不要删除或重命名已有 `subtasks[].id`（除非用户明确要求迁移且已评估影响）。
