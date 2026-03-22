# CKD (慢性肾病) 诊断与遗传风险评估 SOP

## 1. 诊断标准 (KDIGO 2024)
- **定义**: 肾脏结构或功能异常 ≥3个月
- **eGFR分期**:
  - G1: ≥90 (正常或高) — 需有其他肾损伤证据
  - G2: 60-89 (轻度下降)
  - G3a: 45-59 (轻-中度下降)
  - G3b: 30-44 (中-重度下降)
  - G4: 15-29 (重度下降)
  - G5: <15 (肾衰竭/ESKD)
- **蛋白尿分级 (ACR mg/g)**:
  - A1: <30 (正常-轻度升高)
  - A2: 30-300 (中度升高/微量白蛋白尿)
  - A3: >300 (重度升高/大量白蛋白尿)
- **风险矩阵**: G×A交叉 → 绿(低危)/黄(中危)/橙(高危)/红(极高危)
- **推荐eGFR公式**: CKD-EPI 2021 (无种族系数)

## 2. 遗传风险基因 Panel (8基因)
| 基因 | 疾病 | 遗传方式 | 人群频率 | 备注 |
|------|------|----------|----------|------|
| PKD1 | ADPKD | AD | 1:400-1000 | ~85% ADPKD,更严重,中位ESKD~54岁 |
| PKD2 | ADPKD | AD | 同上 | ~15% ADPKD,较温和,中位ESKD~74岁 |
| APOL1 | FSGS/HIVAN/高血压肾病 | AR(双hit) | 非裔G1/G2 ~35%携带 | 纯合/复合杂合OR=7-10 |
| UMOD | 肾小管间质肾病/CKD风险 | AD/PRS | 常见变异 | GWAS显著位点,影响尿调蛋白 |
| COL4A3 | Alport综合征 | AR/AD | 罕见 | 血尿+肾衰+听力丧失 |
| COL4A4 | Alport综合征 | AR/AD | 罕见 | 同上 |
| COL4A5 | Alport综合征 | X-linked | 罕见 | 男性更严重 |
| HNF1B | 肾囊肿与糖尿病综合征 | AD | 罕见 | 肾发育异常+MODY5 |

## 3. 蛋白质标志物
| 蛋白 | 临床意义 | 阶段 |
|------|----------|------|
| Cystatin C | eGFR估算(补充肌酐) | 诊断/监测 |
| KIM-1 | 肾小管损伤早期标志物 | 早期检测 |
| NGAL | 急性肾损伤→CKD进展预测 | 预后 |
| TNFR1/TNFR2 | CKD进展风险(尤其糖尿病肾病) | 预后 |

## 4. 工具调用决策树
```
CKD患者 →
├─ 1. load_patient (基线eGFR,ACR,年龄,种族,家族史,合并症)
├─ 2. recall_similar_cases(disease="CKD", features=[...])
├─ 3. 评估是否查基因:
│   ├─ 多囊肾影像/家族史 → query_genetic_risk(by_gene, [PKD1,PKD2])
│   ├─ 非裔+不明原因CKD → query_genetic_risk(by_gene, [APOL1])
│   ├─ 血尿+听力下降+家族史 → query_genetic_risk(by_gene, [COL4A3,COL4A4,COL4A5])
│   ├─ 早发(<40岁)/不明原因 → query_genetic_risk(by_gene, [PKD1,PKD2,APOL1,UMOD,COL4A3-5,HNF1B])
│   └─ 复杂CKD(糖尿病/高血压背景) → query_genetic_risk(by_prs, [CKD])
├─ 4. query_proteomics([CystatinC, KIM-1, NGAL, TNFR1, TNFR2])
├─ 5. 如有肾脏影像 → query_imaging_detail(abdominal_mri)
└─ 6. gene_protein_integration → submit_diagnosis
```

## 5. 关键临床要点
- ADPKD: 50%在60岁前进展至ESKD; PKD1比PKD2严重~20年
- APOL1: 仅在非裔人群高频; 需双hit(G1/G1, G2/G2, G1/G2)才致病
- Alport: 三联征 = 血尿 + 进行性肾衰 + 感音神经性耳聋
- Tolvaptan(托伐普坦): ADPKD快速进展者的治疗选择
- eGFR用CKD-EPI 2021公式(去种族化)

## 6. 来源
- KDIGO 2024 CKD Guideline (Kidney International Supplement, March 2024)
- GeneReviews: ADPKD (Harris & Torres, updated 2022)
- 临床遗传学知识库