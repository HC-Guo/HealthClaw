# 证据分级与审计框架 SOP（基础层）

> 横切关注点：所有临床 SOP 在输出结论时必须遵循本框架。
> 本 SOP 不独立触发，由其他 SOP（medication_review / medical_record_qc / icd_coding / clinical_pathway_compliance / compliance_review）引用。

---

## 一、证据分级体系（Evidence Tier, T1-T6）

| Tier | 来源类型 | 说明 | 可信度 |
|------|---------|------|--------|
| **T1** | 临床指南 / Meta分析 / 大型RCT | WHO/NICE/ESC/AHA/CSCO等权威机构发布的指南 | 最高 |
| **T2** | 专家共识 / 系统评价 | Delphi共识、Cochrane系统评价 | 高 |
| **T3** | 药品说明书 / 医保目录 / ICD标准 / 行业制度 | 法规性文件、药监局批准说明书、医保限定条件 | 高（法规性） |
| **T4** | 单篇文献 / 病例报告 / 回顾性研究 | PubMed发表的研究、个案报告 | 中 |
| **T5** | 数据分析结论 | 用户历史指标趋势、本地数据统计 | 中（需注明来源数据） |
| **T6** | LLM推理（无外部证据） | Agent基于训练知识的推理，未经外部验证 | 最低 |

### 分级规则
- 同一结论有多个来源时，取最高 Tier
- T1/T2 来源需标注具体指南名称+年份+章节（如「2023 ESC心衰指南 §5.2」）
- T3 来源需标注文件名+条款号（如「氯吡格雷说明书·禁忌症」）
- T4 来源需标注 PMID 或 DOI
- T6 必须明确声明「基于 AI 推理，未经外部验证」

---

## 二、引用要求（3 档可配置）

通过 config.py 的 `MEMORY_CONFIG.evidence_citation_level` 配置：

### strict（严格模式）
适用：合规审阅、医保预审、法规相关场景
- T1-T3 来源：**每条结论必须引用**，含来源名称、版本/年份、条款/页码
- T4-T5 来源：**标注** ⚠️ + 来源信息
- T6 来源：**标注** ⚠️⚠️ + 「证据不足，建议人工复核」
- 无任何外部证据时：**中断输出**，返回「证据缺失，无法给出可靠结论」

### standard（标准模式，默认）
适用：用药审查、病历质控、ICD编码等常规临床场景
- T1-T4 来源：标注来源类型 + 关键信息（指南名/PMID）
- T5-T6 来源：标注置信度等级（高/中/低）
- 全部为 T6 的结论：插入 ⚠️ 低置信度提示

### relaxed（宽松模式）
适用：健康科普、生活方式建议等非临床决策场景
- 仅标注来源类型（如「来源：临床指南」「来源：AI推理」）
- 不强制引用具体文献

---

## 三、证据缺失与低置信度告警

### 证据缺失提示（Missing Evidence Alert）
触发条件：结论所需的关键证据在当前上下文中不存在
```
⚠️ 证据缺失：[缺失内容描述]
   需要: [期望的证据类型]
   建议: [获取方式，如"补充XX检查"/"查阅XX指南"]
```

### 低置信度告警（Low Confidence Warning）
触发条件：
- 结论仅有 T5-T6 支撑
- 多个证据相互矛盾
- 证据时效性过期（指南 > 5年）

```
⚠️ 低置信度：[原因]
   当前证据等级: T[n]
   建议: [如"建议人工复核"/"建议查阅最新指南"]
```

### 证据矛盾处理
当不同来源得出矛盾结论时：
1. 标注矛盾所在
2. 按 Tier 优先级排序（T1 > T2 > ... > T6）
3. 如同级矛盾，标注「证据矛盾，建议人工裁定」
4. 引用双方证据，不单方面隐藏

---

## 四、审计回放（Audit Trail）

### 记录内容
每个关键结论通过 SessionTracker.record_citation() 记录：

```json
{
  "turn": 3,
  "conclusion": "氯吡格雷与奥美拉唑存在 CYP2C19 竞争性抑制",
  "evidence_tier": "T1",
  "source": "2023 ESC抗血栓指南 §4.3.2",
  "citation_snippet": "Omeprazole should be avoided in patients on clopidogrel...",
  "tool_chain": ["medication_review", "web_search"],
  "sop_used": "medication_review_sop",
  "timestamp": "2026-03-12T14:30:00"
}
```

### 回放能力
审计报告（扩展 SessionTracker.generate_report）新增：

```
## 证据引用链
- Turn 2: [T1] 2023 ESC指南 §4.3.2 → "氯吡格雷+奥美拉唑 DDI"
  工具链: medication_review → web_search
  引用片段: "Omeprazole should be avoided..."
- Turn 3: [T3] 氯吡格雷说明书·药物相互作用 → 确认禁忌
  工具链: medication_review
```

### 可复现性保障
- **知识版本**：记录使用的 L3 SOP 文件名（即 sop_used 字段）
- **Prompt 模板**：记录触发的能力域编号和 SOP 名称
- **工具调用链**：通过已有的 turn_summaries 记录
- **引用片段**：citation_snippet 保留原文（≤200 字）

---

## 五、与其他 SOP 的联动协议

### 调用方式
其他 SOP 在输出结论时，按以下模式附加证据信息：

```
[结论内容]
📎 证据: [T{n}] {来源名称} {条款/PMID}
   "{引用片段（≤100字）}"
```

### 各 SOP 的默认引用档位
| SOP | 默认档位 | 说明 |
|-----|---------|------|
| medication_review_sop | standard | 用药安全需明确来源 |
| medical_record_qc_sop | standard | 质控规则需引用规范 |
| icd_coding_sop | standard | 编码需引用 ICD 标准 |
| clinical_pathway_compliance_sop | strict | 合规审查必须精确引用条款 |
| compliance_review_sop | strict | 法规审阅必须精确引用 |
| 疾病诊断 SOP (L3_sops/*) | standard | 诊断结论需证据支撑 |
| 健康管家场景 (能力域2-5) | relaxed | 科普建议无需严格引用 |

可通过 `record_citation(evidence_level_override="strict")` 在单次调用中覆盖默认档位。
