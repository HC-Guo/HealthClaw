# 心血管疾病风险评估 SOP

## 标准流程
1. load_patient → 检查: 传统危险因素(年龄、性别、吸烟、血压、血脂、糖尿病、BMI)
2. 传统因素已明确高危(3+因素) → 可能不需要额外基因/蛋白数据
3. 中间风险或传统因素不一致 → PRS(by_prs, [CAD]) 可提供增量价值
4. 早发冠心病家族史 → query_genetic_risk(by_gene, [LDLR, PCSK9, APOB]) 排查FH
5. 蛋白标志物: Lp(a), ApoB, IL-6 对风险再分层有帮助
6. LPA 基因变异 + Lp(a) 蛋白升高 → 强证据，考虑 gene_protein_integration

## 关键坑点
- Lp(a) 水平>90%百分位是独立风险因素，且目前无有效药物干预
- FH 诊断需要 LDL-C + 家族史 + 基因共同判断，单一证据不够
- PRS 对中间风险人群的再分层最有价值
