# Epilepsy — Genetic Diagnostic SOP

## 1. 疾病概述
- 癫痫遗传异质性极高，>800基因关联；遗传力h²~65%(广义遗传性癫痫)
- DEE(发育性和癫痫性脑病)单基因因素占比最高，诊断率30-50%
- 一般癫痫panel(70基因)总体诊断率~15.4%(n=8565, Epilepsia 2018)

## 2. 高优先级基因(Tier-1, 按阳性率排序)
| 基因 | 表型 | 遗传模式 | 备注 |
|------|------|----------|------|
| SCN1A | Dravet综合征/GEFS+ | AD(多de novo) | 阳性数最多 |
| KCNQ2 | 新生儿癫痫/DEE | AD(多de novo) | 阳性数并列最高 |
| SCN2A | DEE/良性家族性 | AD | 复发变异常见 |
| STXBP1 | Ohtahara/West | AD(100% de novo) | 突触功能 |
| CDKL5 | CDKL5缺乏症 | XL(100% de novo) | 女性为主 |
| SCN8A | DEE-13 | AD(100% de novo) | 钠通道 |
| MECP2 | Rett综合征 | XL | 复发变异多 |
| PRRT2 | PKD/良性婴儿癫痫 | AD(85.7%遗传) | 唯一高遗传率基因 |
| GABRA1 | DEE/JME | AD(100% de novo) | GABA受体 |
| FOXG1 | FOXG1综合征 | AD(100% de novo) | 严重智障 |

## 3. 次优先级基因(Tier-2)
- TSC1/TSC2(结节性硬化), SLC2A1(GLUT1缺乏), PCDH19, DEPDC5
- KCNA2, KCNB1, CHD2, SYNGAP1, GRIN2A, GABRG2

## 4. 检测策略(Evidence Grade: A — 大样本队列+系统综述)
### 适应症(高阳性率指标):
1. DEE/癫痫性脑病
2. 神经发育共病(智障/ASD)
3. 早发癫痫(＜2岁)
4. 不明原因药物难治性癫痫
5. 阳性家族史

### 推荐检测路径:
```
临床评估 → 是否DEE/早发/NDD共病?
  ├─ 是 → ES/GS(一线,ILAE推荐) 或 癫痫panel(≥70基因)
  ├─ 否,有家族史 → 靶向基因(如SCN1A for Dravet)
  └─ 否,散发成人 → 考虑PRS(多基因风险) + 药物基因组学
```

### CNV检测:
- ~9%阳性为大片段缺失/重复(aCGH检出)
- CMA应作为panel阴性后的补充

## 5. 药物基因组学
| 标记 | 药物 | 风险 | 人群 |
|------|------|------|------|
| HLA-B*15:02 | 卡马西平/奥卡西平 | SJS/TEN | 东亚/东南亚 |
| HLA-A*31:01 | 卡马西平 | DRESS/SJS | 泛种族 |
| CYP2C9*2/*3 | 苯妥英 | 毒性↑ | 泛种族 |
| CYP2C19 PM | 氯巴占→活性代谢物↓ | 疗效↓ | 泛种族 |

## 6. 关键参考文献
- Truty et al. Epilepsia 2019;60:1055-64 (PMID:29655203) — 8565pt/70gene, yield 15.4% [Grade A]
- Kaur S et al. Pediatr Neurol 2024 (PMID:38865949) — 综述,ES/GS推荐 [Grade B]
- ILAE Genetics Commission — ES/GS一线推荐 [Grade A]

## 7. UKB分析策略
- 遗传查询: by_gene → SCN1A,KCNQ2,SCN2A,STXBP1; by_prs → epilepsy
- 蛋白组学: 癫痫无直接Olink标记,可查IL-6/NSE(神经损伤)
- 影像: brain_mri(皮质发育异常、结节性硬化)
- 药物基因组: query HLA-B, CYP2C9, CYP2C19