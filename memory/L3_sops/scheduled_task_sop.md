# 定时任务 SOP

目录：`sche_tasks/{pending,running,done}/`（相对代码根，即 `./sche_tasks/`）
文件名：`YYYY-MM-DD_HHMM_描述.md`，内容含 prompt 与 schedule（如 once / daily / weekly）。

## 流程

1. **[AUTO] 唤醒**：`datetime.now()` 取当前时间，`ls ./sche_tasks/pending/`，文件名时间 ≤ 当前 → 到期，任选一个。
2. **立即 rename 到 running/**（先占再读，防多进程重复领）。
3. 读文件内容，按其中 prompt 执行任务。
4. **完成**：移到 `done/`，**在文件内追加执行报告**供用户查阅。
5. 若 schedule 非 once：计算下次执行时间，新建同名/新时间文件到 `pending/`。

注意：`sche_tasks` 在代码根目录下；若目录不存在，由 Agent 先创建 `pending` / `running` / `done` 三个子目录。

## 与诊断场景结合

- 可安排定期“自主学习”提醒、定期“记忆审查”、或按日/周生成某类疾病的风险汇总。
- 执行时仍遵守 L0 与自主行动 SOP 的权限边界（不修改核心代码、不删记忆）。
