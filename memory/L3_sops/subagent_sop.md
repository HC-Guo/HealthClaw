# Subagent 调用 SOP (SEDA 版)

> **当前状态**：SEDA 主流程为单任务串行（Streamlit → seda_main → agent_loop），**尚未实现**通过子进程启动独立 Agent 实例。本 SOP 移植自 pc-agent-loop，用于**未来扩展**（如多患者并行、批量疾病筛查）或**人工按文件协议**做多任务手递手。

---

## Task Mode 文件 IO 协议（约定）

- **目录**：`temp/{task_name}/`（相对代码根），主 agent 的 cwd 在 `temp/` 时即 `./{task_name}/`。
- **启动**（当实现时）：`python seda_main.py --task {task_name} [--llm_no N]` 或通过队列/子进程调用等价入口，cwd=代码根。
- **流程**：
  1. 主 agent 写 `input.txt`（目标 + 约束，可指定 SOP 名；禁写凭印象猜的实现步骤）。
  2. 启动 subagent。
  3. 轮询 `output.txt`（或 output1.txt, output2.txt … 多轮）。
  4. 读回复后若需继续，写 `reply.txt`；不写则 subagent 在超时后自动退出（如 5min）。

---

## 后台调用要点（实现时遵守）

- 必须 **Popen** 启动 subagent，禁止 `subprocess.run`（会阻塞主 agent）。
- stdout/stderr 重定向到 `temp/{task_name}/stdout.log`、`stderr.log` 便于排查卡死、LLM 超时等。
- 文件统一 UTF-8；subagent 无新 `reply.txt` 时 5min 自动退出，无需主 agent 清理进程。
- **禁止**把「启动 Popen」和「轮询 output.txt」放在同一个 `code_run` 里——会阻塞；启动后立即返回，下一轮再 poll。

---

## 场景 1：测试模式（行为验证）

- **用途**：观察 agent 真实行为，修正 RULES / L2 / L3 / SOP。
- **流程**：创建 `temp/test_xxx/`，写 `input.txt` → 启动 subagent → 轮询 `output.txt`（如 2 秒间隔）→ 验证 → 清理或归档。
- **原则**：只给目标，不提示路径、不诱导做法。

---

## 场景 2：Map 模式（并行处理）

- **用途**：将 N 个独立同构子任务（如 N 个患者、N 个疾病）分发给多个 subagent。
- **约束**：
  - 文件系统共享：不同 agent 读不同输入文件、写不同输出文件。
  - 共享资源：同一时刻只有一个任务在用浏览器/LLM 流；若 subagent 仅做文件/API 计算则可并行。
- **标准流程**：主 agent 准备多份输入 → 对每份启动一个 subagent → 全部完成后主 agent 读各输出并汇总（reduce）。

---

## 与 SEDA 的对应

| 项目     | pc-agent-loop     | SEDA                         |
|----------|-------------------|------------------------------|
| 主入口   | agentmain.py      | seda_main.py（Streamlit 驱动）|
| 任务目录 | temp/{task_name}/ | 同上                          |
| 子进程   | `agentmain.py --task` | 待实现                     |

当 SEDA 支持 `--task` 或等效“批处理/子 agent”入口时，按本 SOP 的 IO 协议与 Popen/轮询规则实现即可。
