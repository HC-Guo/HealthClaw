# Creating memory_trigger_sop.md
memory_sop = """# Memory Write Trigger SOP (v1.0)

## 1. 问题诊断: 为何记忆"写不入"

### 1.1 现状分析

| 层级 | 设计容量 | 实际状态 | 问题根因 |
|------|---------|---------|---------|
| L4 (情景记忆) | 每案例1条 | 仅1条 | ① 诊断中断未反思 ② 成功时跳过 ③ 失败后放弃 |
| L2 (全局事实) | 持续累积 | 19行 | 无主动触发，依赖"事后想起" |
| L1 (疾病索引) | 动态更新 | 已清空 | 未与L4/L2建立自动同步 |

### 1.2 执行层断裂点

```
理想流程: 诊断 → 反思 → 写入L4 → 定期蒸馏 → 更新L1/L2
           ↓      ↓       ↓          ↓
实际流程: 诊断 → [经常缺失] → [从不发生]
           ↑
      用户打断 / 成功自满 / 失败沮丧
```

## 2. 强制触发器体系

### 2.1 L4写入强制触发

**触发条件 (满足任一即强制写入):**

| 场景 | 触发器 | 写入内容 |
|------|--------|---------|
| 诊断完成 | `submit_diagnosis` 前检查 | 完整案例反思 |
| 工具组合创新 | 使用≥3种工具或新组合 | 工具效能评估 |
| 置信度低 | 最终<0.6 或 波动>0.3 | 失败分析 |
| 3次失败 | 同一步骤重试3次 | 避坑经验 |
| 用户干预 | 调用 `ask_user` | 决策分歧记录 |

**执行机制:**
```
submit_diagnosis 调用前检查:
  IF NOT write_case_reflection_called:
    自动插入 write_case_reflection
    标记: 强制写入
```

### 2.2 L2写入简化流程

**旧流程 (高门槛)**:
```
发现 → 读L0 → 确认格式 → patch修改 → 同步Insight
         ↑_______ 认知负担高，经常放弃
```

**新流程 (低门槛)**:
```
发现 → 直接追加 → 系统定期整理
         ↓
    file_write(L2_global_facts.txt, mode="append")
```

**L2追加格式**:
```markdown
[2026-03-09] [CATEGORY] 发现内容 [置信度] [来源]
[2026-03-09] [Tool_Pattern] web_search失败时改用browser_navigate [0.9] [case#127]
[2026-03-09] [Disease_Insight] BRCA2在胰腺癌中检出率5-10% [0.95] [文献PMID123]
[2026-03-09] [User_Pref] 用户偏好先给结论再展开 [0.8] [对话观察]
```

### 2.3 L1自动同步机制

**触发条件**:
- L4某疾病案例数 ≥5
- L2某类别条目数 ≥10
- 手动触发 `distill_experience`

**同步流程**:
```python
def sync_l1_from_l4():
    clusters = group_l4_by_disease()
    for disease, cases in clusters.items():
        if len(cases) >= 5:
            patterns = extract_common_patterns(cases)
            update_l1_insight(disease, patterns)
```

## 3. 记忆写入检查清单

### 每个L3/L4任务必须:

**执行中 (触发时立即写)**:
- [ ] 3次失败 → 写L2 (避坑)
- [ ] 工具创新 → 写L4 (工具评估)

**结束前 (submit前强制)**:
- [ ] write_case_reflection 已调用? (若否，自动插入)
- [ ] key_lesson 非空?
- [ ] tools_useful 完整?

**周期间 (系统触发)**:
- [ ] L4案例>5的疾病 → 蒸馏到L1
- [ ] L2条目>10的类别 → 整理到结构化格式

## 4. 写入模板速查

### L4: write_case_reflection 模板

```python
write_case_reflection(
    patient_profile="F/52/BMI24/family_hx+",
    tools_useful={
        "query_genetic_risk": True,   # 实际改变了判断
        "query_proteomics": False,    # 无增量价值
        "recall_similar_cases": True  # 避免了重复踩坑
    },
    key_lesson="BRCA2检测改变了风险分层，但蛋白CA15-3无增量价值",
    confidence_before_tools=0.4,
    confidence_after_tools=0.85,
    tags=["breast_cancer", "BRCA2+", "family_history", "protein_unhelpful"]
)
```

### L2: 快速追加格式

```markdown
# 新增条目 (自动时间戳)
[2026-03-09] [类别] 具体内容 [置信度0-1] [来源标识]

# 类别列表
Tool_Pattern: 工具使用模式
Disease_Insight: 疾病诊断洞察  
User_Pref: 用户偏好
Failure_Mode: 失败模式与恢复
Environment: 环境配置事实
```

## 5. 与现有SOP的整合

### 在 `task_triage_sop` 中:
- L3/L4任务必须包含记忆写入检查
- 结束前验证 `write_case_reflection` 调用

### 在 `evidence_driven_planning_sop` 中:
- 3次工具失败后触发L2写入
- 最终诊断前强制L4反思

### 在 `L0_memory_management_sop` 中:
- 简化L2写入流程 (append优先于patch)
- 明确自动蒸馏触发条件

## 6. 修复效果度量

| 指标 | 当前 | 目标 | 测量方式 |
|------|------|------|---------|
| L4案例数 | 1 | ≥20/月 | 计数 |
| L2条目数 | 19 | ≥100 | 行数 |
| 写入延迟 | ∞ (常不写) | <5分钟 | 诊断到反思时间 |
| 蒸馏频率 | 0 | 1次/周 | 定时任务执行 |

## 7. 立即执行检查

本次会话结束后:
- [ ] 确认4个新SOP已写入L3
- [ ] 本次对话经验写入L2 (SOP重构经验)
- [ ] 更新 `update_working_checkpoint` 记录进度
"""

print(f"Memory Trigger SOP: {len(memory_sop)} chars")
```