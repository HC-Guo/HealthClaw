# 免疫学与细胞治疗 SOP
> 免疫检查点、NK 细胞、T 细胞耗竭、TCR/pMHC、细胞因子风暴、CAR-T、衰老
> 包含 9 个 OpenClaw skill 的压缩迁移。

---

### armored-cart-design-agent
**用途**: 
```
python3 Skills/Immunology_Vaccines/Armored_CART_Design_Agent/design_armored_cart.py \
    --car_target mesothelin \
    --tumor_type pancreatic \
    --armoring_payload IL-12 \
    --expression_system NFAT_inducible \
    --safety_switch iCasp9 \
    --backbone lentiviral \
    --optimize_codon human \
    --output armored_cart_design/
```

### cart-design-optimizer-agent
**用途**: 
```
dC/dt = r*C*(1 - C/K) - k*C*T  # CAR-T expansion
dT/dt = -α*C*T                   # Tumor killing
```

### cellular-senescence-agent
**用途**: 
```
python3 Skills/Longevity_Aging/Cellular_Senescence_Agent/senescence_analyzer.py \
    --rnaseq tissue_expression.tsv \
    --singlecell tissue_scrnaseq.h5ad \
    --signatures fridman_sasp,reactome_senescence \
    --senolytic_prediction true \
    --tissue liver \
    --output senescence_report/
```

### cytokine-storm-analysis-agent
**用途**: 
```
Fever + Elevated Cytokines
          |
    CAR-T context?
    /           \
  Yes            No
   |              |
Hypotension?   Infection workup
   |              |
  CRS          Sepsis vs viral
   |
Neuro symptoms?
   |
  ICANS vs CRS
   |
Ferritin >10,000?
   |
  HLH/MAS evaluation
```

### immune-checkpoint-combination-agent
**用途**: 
```
python3 Skills/Immunology_Vaccines/Immune_Checkpoint_Combination_Agent/ici_combination.py \
    --rnaseq tumor_expression.tsv \
    --ihc pd-l1_tps_60.json \
    --mutations tumor_mutations.maf \
    --tmb 12.5 \
    --msi stable \
    --tumor_type melanoma \
    --prior_treatment pembrolizumab \
    --output ici_recommendations.json
```

### nk-cell-therapy-agent
**用途**: 
```
[scFv] - [Hinge] - [Transmembrane] - [Costimulatory] - [Signaling]

NK-Optimized Domains:
- Transmembrane: NKG2D, CD8α, or CD28
- Costimulatory: 2B4, DAP10, or CD28
- Signaling: CD3ζ (with NK-specific adaptations)
- Additional: Cytokine secretion (IL-15), suicide switch
```

### tcell-exhaustion-analysis-agent
**用途**: 
```
python3 Skills/Immunology_Vaccines/TCell_Exhaustion_Analysis_Agent/exhaustion_analyzer.py \
    --input til_scrnaseq.h5ad \
    --tcells CD8A+CD3E+ \
    --signatures exhaustion_signatures.gmt \
    --epigenetic til_scatacseq.h5ad \
    --predict_response true \
    --output exhaustion_report/
```

### tcr-pmhc-prediction-agent
**用途**: 
```
python3 Skills/Immunology_Vaccines/TCR_pMHC_Prediction_Agent/tcr_pmhc_predict.py \
    --tcr_alpha_cdr3 CAVSDRGSTLGRLYF \
    --tcr_beta_cdr3 CASSLGQAYEQYF \
    --tcr_v_genes TRAV12-1,TRBV7-9 \
    --peptide KRAS_G12D_VVGADGVGK \
    --hla HLA-A*11:01 \
    --check_cross_reactivity true \
    --self_peptide_db human_proteome_9mers.fasta \
    --method alphafold3 \
    --output tcr_pmhc_results/
```

### tcr-repertoire-analysis-agent
**用途**: 
```
python3 Skills/Immunology_Vaccines/TCR_Repertoire_Analysis_Agent/tcr_repertoire_analysis.py \
    --tumor_tcr tumor_tils.tsv \
    --blood_tcr pbmc_tcrs.tsv \
    --cancer_type melanoma \
    --hla_type HLA-A*02:01,HLA-B*07:02 \
    --neoantigens patient_neoantigens.fasta \
    --task response_prediction,tcr_identification \
    --output tcr_analysis/
```
