# 肿瘤学与癌症智能体 SOP
> 癌症代谢、液体活检、MRD 检测、HRD 分析、CNV、克隆造血、肿瘤免疫微环境
> 包含 19 个 OpenClaw skill 的压缩迁移。

---

### bone-marrow-ai-agent
**用途**: 
```
python3 Skills/Hematology/Bone_Marrow_AI_Agent/bm_analyzer.py \
    --image aspirate_smear.tiff \
    --stain wright_giemsa \
    --target_cells 500 \
    --assess_dysplasia true \
    --model coatnet_bm_v2 \
    --output bm_report.json
```

### cancer-metabolism-agent
**用途**: 
```
python3 Skills/Oncology/Cancer_Metabolism_Agent/metabolism_analyzer.py \
    --metabolomics tumor_lcms.csv \
    --rnaseq tumor_expression.tsv \
    --tumor_type NSCLC \
    --normalize mtic \
    --pathway_analysis true \
    --drug_prediction true \
    --output metabolism_report/
```

### chip-clonal-hematopoiesis-agent
**用途**: 
```
python3 Skills/Hematology/CHIP_Clonal_Hematopoiesis_Agent/chip_analysis.py \
    --variants blood_variants.vcf \
    --cbc_data patient_cbc.csv \
    --clinical_data patient_demographics.json \
    --vaf_threshold 0.02 \
    --age 65 \
    --calculate_cvd_risk true \
    --output chip_analysis/
```

### chromosomal-instability-agent
**用途**: 
```
python3 Skills/Oncology/Chromosomal_Instability_Agent/cin_analyzer.py \
    --cnv_segments tumor_cnv.tsv \
    --expression rnaseq_tpm.tsv \
    --mutations somatic.maf \
    --tumor_type breast_cancer \
    --signatures cin70,cin25 \
    --output cin_report/
```

### cnv-caller-agent
**用途**: 
```
Total CN = Major allele + Minor allele

Examples:
- Normal: 1 + 1 = 2 (diploid)
- CN gain: 2 + 1 = 3 (trisomy)
- CN-LOH: 2 + 0 = 2 (normal total, LOH)
- Homozygous deletion: 0 + 0 = 0
- High amplification: 10 + 0 = 10 (focal amp)
```

### coagulation-thrombosis-agent
**用途**: 
```
python3 Skills/Hematology/Coagulation_Thrombosis_Agent/thrombosis_analyzer.py \
    --patient_data patient_demographics.json \
    --labs coagulation_panel.csv \
    --risk_model improved_padua \
    --anticoagulant lmwh \
    --renal_function egfr_45 \
    --output vte_assessment.json
```

### ctdna-dynamics-mrd-agent
**用途**: 
```
python3 Skills/Oncology/ctDNA_Dynamics_MRD_Agent/ctdna_mrd_analysis.py \
    --ctdna_data serial_ctdna.tsv \
    --tracked_mutations tumor_mutations.vcf \
    --sample_times 0,14,42,90,180 \
    --treatment_start 0 \
    --surgery_date 7 \
    --cancer_type colorectal \
    --output mrd_analysis/
```

### hemoglobinopathy-analysis-agent
**用途**: 
```
python3 Skills/Hematology/Hemoglobinopathy_Analysis_Agent/hb_analyzer.py \
    --hplc_data chromatogram.csv \
    --retention_times peak_times.json \
    --cbc cbc_results.json \
    --peripheral_smear smear_findings.txt \
    --molecular hbb_sequencing.vcf \
    --output hb_report.json
```

### hrd-analysis-agent
**用途**: 
```
python3 Skills/Oncology/HRD_Analysis_Agent/hrd_analyzer.py \
    --cnv_segments tumor_segments.tsv \
    --mutations somatic_variants.maf \
    --germline germline_variants.vcf \
    --tumor_type ovarian \
    --purity 0.65 \
    --ploidy 2.1 \
    --output hrd_report.json
```

### liquid-biopsy-analytics-agent
**用途**: 
```
python3 Skills/Oncology/Liquid_Biopsy_Analytics_Agent/lb_analyzer.py \
    --ctdna_variants longitudinal_ctdna.vcf \
    --timepoints week0,week4,week8,week12 \
    --tumor_markers cea_values.csv \
    --baseline_tissue baseline_tumor.maf \
    --analysis response_resistance \
    --chip_filter true \
    --output lb_report/
```

### mpn-progression-monitor-agent
**用途**: 
```
python3 Skills/Hematology/MPN_Progression_Monitor_Agent/mpn_monitor.py \
    --patient_id MF_001 \
    --molecular_data serial_mutations.csv \
    --cbc_data serial_cbc.csv \
    --clinical_data symptoms.json \
    --mpn_type pmf \
    --baseline_date 2024-01-15 \
    --calculate_scores dipss,mipss70 \
    --output mpn_monitoring/
```

### mpn-research-assistant
**用途**: 
```
fibrosis_genes = [
    'TGFB1', 'IL12A', 'IL1B', 'RAB37', 'TIMP1', 'APIP', 'PF4V1', 'VEGFA',
    'FBLN2', 'SFRP1', 'COL6A2', 'COL4A2', 'COL5A1', 'PDGFRB', 'LOXL2', 'RUNX2'
]

# ECM remodeling
ecm_markers = ['COL1A1', 'COL3A1', 'FN1', 'LAMA1', 'LAMB1']

# Profibrotic cytokines
cytokines = ['TGFB1', 'PDGF', 'VEGFA', 'IL1B', 'IL6', 'TNF']
```

### mrd-edge-detection-agent
**用途**: 
```
python3 Skills/Oncology/MRD_EDGE_Detection_Agent/mrd_edge_detect.py \
    --cfdna_bam plasma_cfDNA.bam \
    --tumor_vcf primary_tumor_mutations.vcf \
    --normal_bam matched_normal.bam \
    --coverage_depth 50000 \
    --cancer_type colorectal \
    --model_weights mrd_edge_v2.pt \
    --output mrd_edge_results/
```

### myeloma-mrd-agent
**用途**: 
```
python3 Skills/Hematology/Myeloma_MRD_Agent/myeloma_mrd.py \
    --flow_fcs bone_marrow_ngf.fcs \
    --ngs_clonotype clonoseq_results.json \
    --ms_mprotein maldi_spectrum.csv \
    --baseline_clone diagnosis_clone.json \
    --treatment_phase post_consolidation \
    --output mrd_report.json
```

### organoid-drug-response-agent
**用途**: 
```
python3 Skills/Oncology/Organoid_Drug_Response_Agent/organoid_analyzer.py \
    --screening_data drug_screen_384well.csv \
    --organoid_rnaseq organoid_expression.tsv \
    --organoid_mutations organoid_variants.maf \
    --patient_tumor patient_expression.tsv \
    --tumor_type colorectal \
    --combination_matrix combo_screen.csv \
    --output organoid_report/
```

### pan-cancer-multiomics-agent
**用途**: 
```
Input Layers:
  - Genomic encoder (mutations, CNV)
  - Transcriptomic encoder (mRNA, miRNA)
  - Epigenomic encoder (methylation)
  - Proteomic encoder (RPPA)

Fusion Layer:
  - Cross-attention mechanism
  - Multi-modal variational autoencoder

Output Heads:
  - Subtype classifier
  - Survival predictor
  - Drug response predictor
```

### pdx-model-analysis-agent
**用途**: 
```
python3 Skills/Oncology/PDX_Model_Analysis_Agent/pdx_analyzer.py \
    --pdx_rnaseq pdx_expression.tsv \
    --pdx_mutations pdx_variants.maf \
    --patient_tumor patient_expression.tsv \
    --drug_responses pdx_drug_panel.csv \
    --tumor_type breast_cancer \
    --concordance_check true \
    --output pdx_recommendations/
```

### precision-oncology-agent
**用途**: 

### tme-immune-profiling-agent
**用途**: 
```
python3 Skills/Immunology_Vaccines/TME_Immune_Profiling_Agent/tme_profiling.py \
    --bulk_rna expression_matrix.tsv \
    --scRNA_data scRNA_lung.h5ad \
    --spatial_data visium_tumor.h5ad \
    --cancer_type nsclc \
    --deconvolution_methods cibersortx,epic,mcpcounter \
    --response_labels clinical_response.csv \
    --output tme_profiles/
```
