# 药物基因组学 SOP
> 基因-药物交互、CPIC 指南、基因型导向用药
> 包含 3 个 OpenClaw skill 的压缩迁移。

---

### clinpgx
**用途**: Query the ClinPGx API for pharmacogenomic gene-drug data, clinical annotations, CPIC guidelines, and FDA drug labels
```
output_directory/
├── report.md                    # Full markdown report
└── tables/
    ├── gene_drug_pairs.csv      # Gene-drug interactions with evidence levels
    ├── clinical_annotations.csv # Curated variant-drug-phenotype annotations
    ├── guidelines.csv           # CPIC/DPWG clinical guidelines
    └── alleles.csv              # Known allele definitions
```

### pharmacogenomics-agent
**用途**: 
```
python3 Skills/Precision_Medicine/Pharmacogenomics_Agent/pgx_analyzer.py \
    --genotype patient_pgx_panel.vcf \
    --medications current_meds.json \
    --guidelines cpic_dpwg \
    --risk_scores oncology_response \
    --output pgx_recommendations.json
```

### pharmgx-reporter
**用途**: Pharmacogenomic report from DTC genetic data (23andMe/AncestryDNA) — 12 genes, 31 SNPs, 51 drugs
```
python clawbio.py run pharmgx --demo
```
