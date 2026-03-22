# 变异分析与解读 SOP
> VCF 处理、ACMG 分级、体细胞变异解读、结构变异、PRS
> 包含 5 个 OpenClaw skill 的压缩迁移。

---

### tooluniverse-cancer-variant-interpretation
**用途**: Provide comprehensive clinical interpretation of somatic mutations in cancer. Given a gene symbol + variant (e.g., EGFR L858R, BRAF V600E) and optional cancer type, performs multi-database analysis...
**触发条件**: "What treatments exist for EGFR L858R in lung cancer?"; "Patient has BRAF V600E melanoma - what are the options?"; "Is KRAS G12C targetable?"; "Patient progressed on osimertinib - what's next?"
```
| NCT ID | Phase | Agent(s) | Status | Cancer Type | Biomarker |
|--------|-------|----------|--------|-------------|-----------|
```

### tooluniverse-polygenic-risk-score
**用途**: Build and interpret polygenic risk scores (PRS) for complex diseases using GWAS summary statistics. Calculates genetic risk profiles, interprets PRS percentiles, and assesses disease predisposition...
```
PRS = Σ (dosage_i × effect_size_i)
```

### tooluniverse-structural-variant-analysis
**用途**: Comprehensive structural variant (SV) analysis skill for clinical genomics. Classifies SVs (deletions, duplications, inversions, translocations), assesses pathogenicity using ACMG-adapted criteria,...
```
SV: arr[GRCh38] 17q21.31(44039927-44352659)x1
- Type: Deletion (heterozygous)
- Size: 313 kb
- Genes: MAPT, KANSL1 (fully contained)
- Breakpoints: Well-defined (array resolution ±5kb)
```

### tooluniverse-variant-analysis
**用途**: Production-ready VCF processing, variant annotation, mutation analysis, and structural variant (SV/CNV) interpretation for bioinformatics questions. Parses VCF files (streaming, large files), class...
```
report = variant_analysis_pipeline("input.vcf", output_file="report.md")
```
**限制**: **VCF annotation required for mutation classification**: If VCF has no ANN/CSQ/FUNCOTATION in INFO, mutation types will be "unknown" until ToolUniverse annotation is applied; **Multi-allelic variants**: Parser takes first ALT allele for type classification

### tooluniverse-variant-interpretation
**用途**: Systematic clinical variant interpretation from raw variant calls to ACMG-classified recommendations with structural impact analysis. Aggregates evidence from ClinVar, gnomAD, CIViC, UniProt, and P...
```
{GENE}_{VARIANT}_interpretation_report.md

Examples:
BRCA1_c.5266dupC_interpretation_report.md
TP53_p.R273H_interpretation_report.md
```
