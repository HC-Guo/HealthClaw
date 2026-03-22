# BioOS 扩展智能体 SOP
> 肿瘤学、血液学、免疫治疗、单细胞、药物设计、临床 AI、研究基础设施
> 包含 5 个 OpenClaw skill 的压缩迁移。

---

### autonomous-oncology-agent
**用途**: 

### microbiome-cancer-agent
**用途**: 
```
python3 Skills/Microbiome/Microbiome_Cancer_Agent/microbiome_cancer.py \
    --metagenomics fecal_shotgun.fastq.gz \
    --tumor_data melanoma_rnaseq.tsv \
    --clinical treatment_outcomes.csv \
    --analysis ici_response \
    --reference metaphlan_db \
    --output microbiome_report/
```

### tumor-clonal-evolution-agent
**用途**: 
```
dNi/dt = ri * Ni * (1 - sum(aij * Nj) / Ki)
```

### tumor-heterogeneity-agent
**用途**: 
```
python3 Skills/Oncology/Tumor_Heterogeneity_Agent/ith_analysis.py \
    --multi_region_vcfs region1.vcf,region2.vcf,region3.vcf \
    --cnv_segments cnv_calls.seg \
    --purity 0.7,0.65,0.72 \
    --sample_names Primary,Met1,Met2 \
    --method pyclone-vi \
    --phylogeny_method citup \
    --output ith_analysis/
```

### tumor-mutational-burden-agent
**用途**: 
```
TMB_WES = a * TMB_panel + b

Conversion factors (example):
- FoundationOne CDx: TMB_WES ≈ 1.0 × TMB_F1
- MSK-IMPACT: TMB_WES ≈ 1.1 × TMB_IMPACT
- TSO500: TMB_WES ≈ 0.9 × TMB_TSO
```
