# 乳腺癌风险评估 SOP

## 标准流程
1. load_patient → 检查: 年龄、性别、家族史、既往乳腺疾病
2. 家族史阳性 或 早发(≤50岁) → query_genetic_risk(by_gene, [BRCA1, BRCA2, PALB2, ATM, CHEK2])
3. 发现高外显率变异 → 不需要 PRS（增量价值小）→ 直接评估
4. 未发现高外显率变异 → 考虑 PRS(by_prs, [breast_cancer])
5. 蛋白标志物(CA15-3, HE4)增量价值有限，一般不需要查

## 关键坑点
- BRCA1/2 变异的致病性判断以 ClinVar 为准，VUS 不能作为诊断依据
- 男性也可能携带 BRCA 变异，有乳腺癌家族史的男性也需评估
- 非欧洲裔人群的 BRCA VUS 比例更高，需特别注意
