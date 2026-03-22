# 健康管理与生活方式 SOP
> 营养、睡眠、健身、心理健康、中医体质
> 包含 7 个 OpenClaw skill 的压缩迁移。

---

### adhd-daily-planner
**用途**: Time-blind friendly planning, executive function support, and daily structure for ADHD brains. Specializes in realistic time estimation, dopamine-aware task design, and building systems that actual...
```
Take your first estimate. Now:

"5 minutes" → Actually 15-20 minutes
"30 minutes" → Actually 1-1.5 hours
"A couple hours" → Actually half a day
"This weekend" → Actually won't happen without body doubling
```

### fitness-analyzer
**用途**: 分析运动数据、识别运动模式、评估健身进展，并提供个性化训练建议。支持与慢性病数据的关联分析。
```
/fitness trend 3months
```

### health-trend-analyzer
**用途**: 分析一段时间内健康数据的趋势和模式。关联药物、症状、生命体征、化验结果和其他健康指标的变化。识别令人担忧的趋势、改善情况，并提供数据驱动的洞察。当用户询问健康趋势、模式、随时间的变化或"我的健康状况有什么变化？"时使用。支持多维度分析（体重/BMI、症状、药物依从性、化验结果、情绪睡眠），相关性分析，变化检测，以及交互式HTML可视化报告（ECharts图表）。
```
// 皮尔逊相关系数
function pearsonCorrelation(x, y) {
  // 计算相关系数
  // 返回值范围：-1（负相关）到 1（正相关）
}

// 应用场景
- 药物开始日期 vs 症状频率
- 睡眠时长 vs 情绪评分
- 体重变化 vs 饮食记录
- 运动量 vs 情绪状态
```

### mental-health-analyzer
**用途**: 分析心理健康数据、识别心理模式、评估心理健康状况、提供个性化心理健康建议。支持与睡眠、运动、营养等其他健康数据的关联分析。
```
### 数据不足
```

### nutrition-analyzer
**用途**: 分析营养数据、识别营养模式、评估营养状况，并提供个性化营养建议。支持与运动、睡眠、慢性病数据的关联分析。
```
rda_achievement = (actual_intake / rda_value) * 100

status_classification:
- < 50%: 严重缺乏
- 50-75%: 不足
- 75-100%: 接近目标
- 100-150%: 充足（理想范围）
- > 150%: 过量（注意安全上限UL）
```

### sleep-analyzer
**用途**: 分析睡眠数据、识别睡眠模式、评估睡眠质量，并提供个性化睡眠改善建议。支持与其他健康数据的关联分析。
```
# 睡眠质量分析报告

## 分析周期
2025-03-20 至 2025-06-20（3个月）

---

## 睡眠时长趋势

- **趋势**：⬆️ 改善
- **开始**：平均6.2小时/晚
- **当前**：平均7.1小时/晚
- **变化**：+0.9小时 (+14.5%)
- **解读**：睡眠时长显著增加，接近理想目标（7.5小时）

**趋势线**：
```

### tcm-constitution-analyzer
**用途**: 分析中医体质数据、识别体质类型、评估体质特征,并提供个性化养生建议。支持与营养、运动、睡眠等健康数据的关联分析。
```
def calculate_constitution_scores(answers):
    """
    基于《中医体质分类与判定》标准

    计算公式:
    转化分数 = [(原始分数 - 题目数) / (题目数 × 4)] × 100

    其中:
    - 原始分数 = 各题目得分之和
    - 题目数 = 该体质的问题数量
    """
    scores = {}
    for constitution, questions in CONSTITUTION_QUESTIONS.items():
        original_score = sum(answers[q] for q in questions)
        question_count = len(questions)
        converted_score = ((original_score - question_count) / (question_count * 4)) * 100
        scores[constitution] = round(con
# ... (truncated)
```
