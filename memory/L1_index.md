## 基因组分析工具集 (L3_scripts/)

| 模块 | 文件 | 功能 | 大小 |
|------|------|------|------|
| 变异解析器 | `variant_parser.py` | VCF/TSV解析、按基因/区域/LoF过滤、16个预定义基因区域 | 11KB |
| PRS计算器 | `prs_calculator.py` | 多基因风险评分、5种疾病权重、百分位计算、临床分层 | 13KB |
| 致病性分类器 | `pathogenicity_classifier.py` | ACMG 5级分类、12条证据规则、ClinVar整合 | 15KB |
| 基因面板分析器 | `gene_panel_analyzer.py` | 5种疾病面板(乳腺癌/FH/Lynch/心血管/AD)、批量分析 | 12KB |
| 报告生成器 | `genomic_report_generator.py` | 整合全部模块、综合风险评级、临床文本+JSON报告 | 14KB |

### 内置面板
- `hereditary_breast_ovarian` — 遗传性乳腺癌/卵巢癌 (13基因)
- `familial_hypercholesterolemia` — 家族性高胆固醇血症 (4基因)
- `lynch_syndrome` — Lynch综合征 (5基因)
- `cardiovascular_genetic` — 遗传性心血管病 (11基因)
- `alzheimer_risk` — 阿尔茨海默病遗传风险 (7基因)