# Creating task_triage_sop.md
task_sop = """# Task Triage & Layered Planning SOP (v1.0)

## 1. 任务分层模型

### 1.1 四层任务分类

| 层级 | 名称 | 特征 | 示例 | Planning模式 |
|------|------|------|------|-------------|
| L1 | 原子任务 | 1-2步，确定性高，无分支 | 查天气、单次搜索、截图 | DIRECT (直接执行) |
| L2 | 简单序列 | 3-5步，路径明确，少分支 | 点外卖、查快递、单次导航 | LINEAR_PLAN (线性规划) |
| L3 | 复杂任务 | 多步+分支+需验证 | 医学诊断、故障排查、数据分析 | FULL_PLAN (完整规划) |
| L4 | 探索任务 | 目标模糊，需迭代 | 学习新疾病、自主研究 | ITERATIVE_PLAN (迭代规划) |

### 1.2 快速判定法

```
判定流程 (每次任务开始前，<thinking>中执行):

Step 1: 估计步数
├── ≤2步 → L1/DIRECT
└── >2步 → 继续

Step 2: 评估分支复杂度
├── 无分支或单一路径 → L2/LINEAR
├── 多分支但目标明确 → L3/FULL
└── 目标需探索澄清 → L4/ITERATIVE

Step 3: 验证确定性
├── 每步结果可预测 → 保持当前层级
└── 存在不确定性 → 升级一级
```

## 2. 各层级执行规范

### 2.1 L1: DIRECT - 直接执行

**触发条件**:
- 明确单一动作: "截图"、"搜索XX"、"打开XX"
- 无前置依赖
- 失败可立即反馈

**执行要求**:
```
无需正式Planning
<thinking>中仅需确认: 理解正确性
直接执行工具调用
失败后最多重试1次，然后升级至L2
```

**典型场景**:
- `web_search`: 单次查询
- `phone_control screenshot`: 截图查看
- `code_run`: 简单代码执行
- `file_read`: 读取单个文件

### 2.2 L2: LINEAR_PLAN - 线性规划

**触发条件**:
- 多步骤但路径固定
- 步骤间有明确依赖 (A→B→C)
- 失败处理简单 (重试或跳过)

**执行要求**:
```
<thinking>中列出步骤序列:
  Step 1: [动作] → 预期结果
  Step 2: [动作] → 预期结果
  ...
  失败预案: [如果X失败，则Y]

无需调用 update_working_checkpoint (除非>5步)
按序列执行，每步验证
```

**典型场景**:
- 手机点外卖: 启动App → 搜索店铺 → 选择商品 → 确认支付
- 浏览器查询: 导航 → 搜索 → 点击结果 → 提取内容
- 文件处理: 读取 → 处理 → 写入

### 2.3 L3: FULL_PLAN - 完整规划

**触发条件**:
- 医学诊断任务
- 多源数据整合
- 需要分支决策 (if-then-else)
- 涉及不确定性管理

**执行要求**:
```
必须执行完整Planning流程:
1. 读取相关SOP (evidence_driven_planning_sop等)
2. 分析证据缺口
3. 制定工具调用策略 (含分支)
4. 调用 update_working_checkpoint 记录计划
5. 执行并动态调整
6. 最终验证与反思
```

**关键组件**:
- **预检清单**: 调用工具前的6个问题 (见evidence_driven_planning_sop)
- **分支预案**: 每种可能结果对应的下一步
- **置信度追踪**: 每次调用后重新评估
- **强制反思**: 结束前 write_case_reflection

### 2.4 L4: ITERATIVE_PLAN - 迭代规划

**触发条件**:
- 目标模糊: "学习XX"、"探索XX"、"优化XX"
- 需要多轮尝试才能明确方向
- 每步结果影响下一步目标

**执行要求**:
```
迭代循环:
  While 目标未达成:
    1. 评估当前认知状态
    2. 设定本轮子目标 (SMART)
    3. 执行探索 (搜索/浏览/实验)
    4. 分析结果，更新认知
    5. 调整或确认目标
    
    每3轮必须调用 update_working_checkpoint
```

**典型场景**:
- `browse_and_learn`: 学习新疾病
- 自主研究: "X病的最新诊断标准"
- 策略优化: "改进Y流程的效率"

## 3. 层级升降规则

### 3.1 自动升级条件

| 当前层级 | 升级触发 | 升至 |
|---------|---------|------|
| L1 | 执行时发现隐藏依赖 | L2 |
| L1/L2 | 失败3次或出现分支 | L3 |
| L3 | 目标持续模糊/需探索 | L4 |

### 3.2 降级可能

- L4→L3: 目标已澄清，路径明确
- L3→L2: 诊断已明确，仅需执行
- 降级时更新 working_checkpoint

## 4. 工具选择速查表

| 任务类型 | 推荐工具 | Planning层级 |
|---------|---------|-------------|
| 快速信息查询 | web_search | L1 |
| 深度网页浏览 | browser_navigate + scan | L2 |
| 手机简单操作 | phone_control | L1/L2 |
| 手机复杂交互 | phone_control + screen_analyze | L2/L3 |
| 医学诊断 | load_patient + query_* | L3 |
| 代码执行 | code_run | L1/L2 |
| 知识学习 | browse_and_learn | L4 |

## 5. 执行检查清单

### 每个任务开始前:
- [ ] 判定任务层级 (L1/L2/L3/L4)
- [ ] 选择对应Planning模式
- [ ] 预估是否需要 working_checkpoint

### L3/L4任务额外检查:
- [ ] 相关SOP已读取
- [ ] 分支预案已考虑
- [ ] 成功/失败标准已明确

### 任务结束时:
- [ ] 结果与预期对比
- [ ] 需要写入记忆? (L3/L4强制)
- [ ] 经验教训总结 (L3/L4)

## 6. 与诊断SOP的衔接

医学诊断任务统一按 **L3/FULL_PLAN** 处理，但遵循:

1. 先读取 `evidence_driven_planning_sop` 和 `imaging_centered_decision_sop`
2. 按"影像→基因→蛋白"优先级评估
3. 置信度达标 (≥0.7) 后可提前结束
4. 必须调用 `write_case_reflection` (L4记忆)
"""

print(f"Task Triage SOP: {len(task_sop)} chars")
```