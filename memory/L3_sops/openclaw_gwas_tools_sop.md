# GWAS 分析工具 SOP
> GWAS 关联分析、精细定位、SNP 解读、药物靶点发现
> 包含 5 个 OpenClaw skill 的压缩迁移。

---

### tooluniverse-gwas-drug-discovery
**用途**: Transform GWAS signals into actionable drug targets and repurposing opportunities. Performs locus-to-gene mapping, target druggability assessment, existing drug identification, safety profile evalu...
```
Target Score = (GWAS Score × 0.4) + (Druggability × 0.3) + (Clinical Evidence × 0.2) + (Novelty × 0.1)
```

### tooluniverse-gwas-finemapping
**用途**: Identify and prioritize causal variants at GWAS loci using statistical fine-mapping and locus-to-gene predictions. Computes posterior probabilities for causal variants, links variants to genes via ...
```
result = prioritize_causal_variants("APOE", "alzheimer")

# Get experimental validation suggestions
suggestions = result.get_validation_suggestions()
for suggestion in suggestions:
    print(suggestion)

# Output includes:
# - CRISPR knock-in experiments
# - Reporter assays
# - eQTL analysis
# - Colocalization studies
```
**注意**: when exploring a new disease; for replication of signals; (eQTLs, chromatin, CRISPR screens)

### tooluniverse-gwas-snp-interpretation
**用途**: Interpret genetic variants (SNPs) from GWAS studies by aggregating evidence from multiple databases (GWAS Catalog, Open Targets Genetics, ClinVar). Retrieves variant annotations, GWAS trait associa...
```
Genome-wide significant associations with 100 traits/diseases:
  - Type 2 diabetes
  - Diabetic retinopathy
  - HbA1c levels
  ...

Identified in 20 fine-mapped loci.
Predicted causal genes: TCF7L2
```

### tooluniverse-gwas-study-explorer
**用途**: Compare GWAS studies, perform meta-analyses, and assess replication across cohorts. Integrates NHGRI-EBI GWAS Catalog and Open Targets Genetics to compare study designs, effect sizes, ancestry dive...
```
I² = [(Q - df) / Q] × 100%

where Q = Cochran's Q statistic
      df = degrees of freedom (n_studies - 1)
```

### tooluniverse-gwas-trait-to-gene
**用途**: Discover genes associated with diseases and traits using GWAS data from the GWAS Catalog (500,000+ associations) and Open Targets Genetics (L2G predictions). Identifies genetic risk factors, priori...
```
# Instead of:
discover_gwas_genes("diabetes")  # Ambiguous

# Use:
discover_gwas_genes(
    "type 2 diabetes",
    disease_ontology_id="MONDO_0005148"  # Specific
)
```
**注意**: ```
**限制**: - Positional mapping assigns SNPs to nearest gene (may be incorrect); Fine-mapping available for only a subset of studies
