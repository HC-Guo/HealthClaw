# IBD (Inflammatory Bowel Disease) Diagnostic SOP

## 疾病概述
IBD包括克罗恩病(CD)、溃疡性结肠炎(UC)和未定型IBD(IBD-U)。遗传度: CD~50%, UC~30%。>240 GWAS位点已识别。

## 亚型与遗传特征

### 1. VEO-IBD (Very Early Onset, <6岁) — **最高基因检测价值**
- **IL10信号通路 (最可操作)**: IL10, IL10RA, IL10RB → AR遗传; 严重肛周病变+婴儿期起病
  - 阳性→考虑造血干细胞移植(HSCT); 传统免疫抑制常无效
- **免疫缺陷型IBD**: FOXP3(IPEX), XIAP(X连锁), WAS, LRBA, CTLA4, RAG1/2, IL2RA
- **吞噬细胞缺陷(CGD样)**: CYBB, CYBA, NCF2, NCF4, CYBC1 → 肉芽肿性结肠炎
- **上皮屏障缺陷**: COL7A1, FERMT1, GUCY2C, SLC9A3
- **建议**: VEO-IBD → **全panel检测(100+基因)**，诊断率可达30-50%

### 2. 克罗恩病 (CD) — 成人
- **高频变异**: NOD2 (R702W/rs2066844, G908R/rs2066845, L1007fs/rs2066847) — 欧洲裔CD最强遗传因素
  - 杂合OR≈2-4, 纯合/复合杂合OR≈17-40
  - 回肠型CD关联最强; NOD2阳性+回肠狭窄表型一致性高
- **自噬通路**: ATG16L1(T300A), IRGM
- **共有通路**: IL23R(R381Q=保护性), JAK1, STAT3, TNFSF15
- **基因建议**: 家族史阳性/早发(<30岁) → 查NOD2+自噬基因

### 3. 溃疡性结肠炎 (UC) — 成人
- **HLA关联**: HLA-DRB1*0103(重症UC)
- **IL23/Th17轴**: IL23R, IL12B, JAK2
- **其他**: HNF4A, CDH1(E-cadherin)
- **单基因少见**, 以多基因为主

### 4. 自身炎症型IBD
- **MEFV**(FMF), **MVK**(HIDS), **NLRC4**, **RIPK1**, **TNFAIP3**(A20)
- 表现: 反复发热+肠道炎症+系统性炎症

## 血清学/蛋白标志物
| 标志物 | CD | UC | 临床用途 |
|--------|----|----|---------|
| ASCA IgA/IgG | + | - | CD提示 |
| pANCA | - | + | UC提示 |
| 粪便钙卫蛋白 | ↑↑ | ↑↑ | 活动度监测(非特异) |
| CRP | ↑(CD常升) | 可正常 | 炎症活动度 |
| IL-6, TNF-α | ↑ | ↑ | 研究/治疗靶点 |

## 基因检测决策树
```
IBD疑诊
├─ VEO-IBD (<6岁) → 全panel NGS (≥100基因)
│   ├─ IL10/IL10RA/IL10RB阳性 → HSCT评估
│   ├─ XIAP/FOXP3阳性 → 免疫缺陷管理
│   └─ CGD基因阳性 → 抗感染+抗炎
├─ 早发CD (<30岁) + 家族史
│   ├─ 查NOD2三变异 + ATG16L1 + IL23R
│   └─ 阴性 → 考虑扩展panel或PRS
├─ 成人CD/UC (典型)
│   ├─ 血清学: ASCA+pANCA辅助分型
│   ├─ 基因检测增量价值有限(多基因架构)
│   └─ 药物基因组: TPMT/NUDT15(硫唑嘌呤毒性)
└─ 治疗决策
    ├─ 抗TNF无效 → 考虑IL23/JAK通路变异
    └─ TPMT/NUDT15检测 → 硫唑嘌呤剂量调整
```

## PRS状态
- CD PRS: 研究阶段, 中等区分力(AUC~0.65-0.70)
- UC PRS: 研究阶段, 效力略低于CD
- 非欧洲裔效力显著下降
- 临床不推荐常规使用

## 推荐Panel (来源: Fulgent IBD NGS Panel, 122基因)
核心基因分类:
- IL10信号: IL10, IL10RA, IL10RB
- NOD2/NLR: NOD2, NLRC4, NLRP12, CARD8
- IL23-JAK-STAT: IL23R, JAK1, STAT1, STAT3, STAT5B
- 吞噬: CYBA, CYBB, CYBC1, NCF2, NCF4
- Treg/免疫调节: FOXP3, CTLA4, LRBA, IL2RA, ICOS, ITCH
- 自身炎症: MEFV, MVK, RIPK1, TNFAIP3
- T/B细胞: RAG1, RAG2, BTK, WAS, XIAP, CD40, CD40LG
- TGF-β: TGFB1, TGFBR1, TGFBR2
- 上皮屏障: COL7A1, FERMT1, GUCY2C, DUOX2
- 端粒生物学: DKC1, RTEL1, TERC, TERT

## 证据等级
- NOD2-CD关联: **A级**(多项大型GWAS+Meta-分析, OR明确)
- IL10/IL10RA/IL10RB-VEO-IBD: **A级**(功能验证+HSCT治疗证据)
- ATG16L1/IRGM-CD: **B级**(GWAS复制, 功能研究)
- PRS临床应用: **C级**(研究阶段)
- 药物基因组TPMT/NUDT15: **A级**(CPIC指南)

## 来源
- Fulgent IBD NGS Panel (122基因): fulgentgenetics.com
- NOD2-CD review: IBD Journal 2025;31(2):552
- GWAS catalog: >240 IBD-associated loci