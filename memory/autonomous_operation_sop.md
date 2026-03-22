# SEDA 自主行动 SOP (探测-学习-记忆)

⚠️ **报告目录**：autonomous_reports 在 temp/ 下，用 `./autonomous_reports/` 访问。

## 触发方式
- **自动触发**：用户离开 ≥10 分钟，idle_monitor 自动注入 [AUTO] 指令
- **手动触发**：用户在 UI 点击"🚀 立即开始自主学习"

## 🚫 Step 0（阻塞）：写入约束便签 — 未完成禁止进入后续步骤

**必须第一个动作就调用** `update_working_checkpoint`，写入以下内容：

```
自主学习｜≤20回合｜只有cwd和memory可写｜用户不在(问题存报告)｜报告目录:./autonomous_reports/｜收尾:更新history｜产出=学习报告+记忆更新
```

⛔ **跳过 Step 0 = 违规**。先占便签再选任务、再执行学习。

## 核心原则

价值公式：**「当前记忆中缺失」×「对未来诊断有持久收益」**

## 报告规则

⚠️ 历史记录位置：`./autonomous_reports/history.txt`

报告存于 `./autonomous_reports/`，文件名 `RXX_简短描述.md`。
完成后在 history.txt 首行 prepend：`#XX | 日期 | 类型 | 主题 | 结论`（严格单行）。

权限边界：
- 无需批准：web_search、browse_and_learn、读取任何记忆文件、cwd 内写报告
- 可以执行：file_patch 更新 L1/L2、file_write 创建 L3 SOP
- 需要谨慎：修改已有 L3 SOP（先读再改，只 patch 不覆盖）
- 绝对禁止：删除记忆文件、修改 L0、修改核心代码

## 任务选择

选择规则：
- 先读 history.txt 了解近期已探索方向，**不连续选择相同方向**
- 近10轮内同一方向 ≤3 次
- 选定后先声明一句话预期收益，写入报告开头

目标排序（按价值递减）：
1. **填补知识空白**：L1 索引中缺失的常见疾病 → 学习诊断标准、推荐基因 panel → 创建 L3 SOP
2. **强化薄弱领域**：L4 策略中置信度低的疾病 → 搜索最新指南/文献 → 更新 SOP
3. **扩充工具使用策略**：搜索基因/蛋白功能文献 → 更新 L1 RULES
4. **学习新兴诊断技术**：PRS 最新进展、蛋白标志物发现 → 写入 L2 事实库
5. **GeneReviews 深度学习**：逐条浏览 GeneReviews 条目 → 提炼为 L3 SOP
6. **记忆审查**：检查已有 SOP 是否过时或有错误（低频）

学习资源优先级：
GeneReviews > NICE/NCCN 指南 > PubMed 系统综述 > MedlinePlus > WHO/CDC

## 执行流程

### 阶段 1：评估知识状态
1. 读取 `memory/L1_disease_insight.txt` — 已有哪些疾病索引？
2. 扫描 `memory/L3_sops/` 目录 — 已有哪些疾病 SOP？
3. 读取 `memory/L4_episodes/disease_strategy.json` — 哪些疾病置信度低？
4. 读 history.txt — 近期已学过什么？

### 阶段 2：选择目标并学习
1. 选择一个价值最高的学习方向
2. 用 `web_search` 搜索相关文献/指南
3. 用 `browse_and_learn` 深度阅读关键页面
4. 提取关键知识：诊断标准、推荐基因 panel、风险因子、鉴别诊断

### 阶段 3：知识固化
按 L0 分类决策树存储：
- 通用规则 → `file_patch` L1 [RULES]
- 疾病 SOP → `file_write` L3_sops/疾病名_sop.md
- 环境事实 → `file_patch` L2
- 标注证据等级 (A/B/C)

### 阶段 4：生成报告
1. 写报告到 `./autonomous_reports/RXX_描述.md`
2. 更新 `./autonomous_reports/history.txt`
3. 报告内容：学了什么、更新了哪些记忆、发现了什么

## 避免「只读陷阱」
- 发现问题要动手验证，边探测边实验（如用 code_run 跑小脚本验证假设）。
- 完整验证再结论：禁止读部分文件即下判断，需追踪关联并实测后再写报告或更新记忆。

## 常见疾病学习清单（参考）

| 优先级 | 疾病 | 关键基因 | 关键蛋白 |
|--------|------|----------|----------|
| 高 | 乳腺癌 | BRCA1/2, TP53, PALB2 | CA15-3, HER2 |
| 高 | 冠心病 | LDLR, PCSK9, APOE | ApoB, Lp(a), CRP |
| 高 | 2型糖尿病 | TCF7L2, SLC30A8 | HbA1c, Adiponectin |
| 中 | 阿尔茨海默 | APOE, APP, PSEN1 | Amyloid-β, Tau |
| 中 | 结直肠癌 | APC, MLH1, MSH2 | CEA, CA19-9 |
| 中 | 帕金森病 | LRRK2, GBA, SNCA | α-Synuclein |
| 中 | 肺癌 | EGFR, ALK, KRAS | CYFRA21-1, NSE |
| 低 | 类风湿关节炎 | HLA-DRB1 | RF, Anti-CCP, CRP |
| 低 | 慢性肾病 | UMOD, APOL1 | Cystatin C, KIM-1 |
