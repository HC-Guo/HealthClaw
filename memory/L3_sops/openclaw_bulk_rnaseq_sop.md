# Bulk RNA-seq 分析 SOP
> DESeq2 差异表达、批次校正、WGCNA、PPI、反卷积
> 包含 10 个 OpenClaw skill 的压缩迁移。

---

### bulk-rna-seq-batch-correction-with-combat
**用途**: Use omicverse's pyComBat wrapper to remove batch effects from merged bulk RNA-seq or microarray cohorts, export corrected matrices, and benchmark pre/post correction visualisations.

### bulk-rna-seq-differential-expression-with-omicverse
**用途**: Guide Claude through omicverse's bulk RNA-seq DEG pipeline, from gene ID mapping and DESeq2 normalization to statistical testing, visualization, and pathway enrichment. Use when a user has bulk cou...

### bulk-rna-seq-deseq2-analysis-with-omicverse
**用途**: Walk Claude through PyDESeq2-based differential expression, including ID mapping, DE testing, fold-change thresholding, and enrichment visualisation.

### string-protein-interaction-analysis-with-omicverse
**用途**: Help Claude query STRING for protein interactions, build PPI graphs with pyPPI, and render styled network figures for bulk gene lists.

### bulk-rna-seq-deconvolution-with-bulk2single
**用途**: Turn bulk RNA-seq cohorts into synthetic single-cell datasets using omicverse's Bulk2Single workflow for cell fraction estimation, beta-VAE generation, and quality control comparisons against refer...

### bulktrajblend-trajectory-interpolation
**用途**: Extend scRNA-seq developmental trajectories with BulkTrajBlend by generating intermediate cells from bulk RNA-seq, training beta-VAE and GNN models, and interpolating missing states.

### bulk-wgcna-analysis-with-omicverse
**用途**: Assist Claude in running PyWGCNA through omicverse—preprocessing expression matrices, constructing co-expression modules, visualising eigengenes, and extracting hub genes.

### pydeseq2
**用途**: Differential gene expression analysis (Python DESeq2). Identify DE genes from bulk RNA-seq counts, Wald tests, FDR correction, volcano/MA plots, for RNA-seq analysis.
```
uv pip install pydeseq2
```

### tooluniverse-expression-data-retrieval
**用途**: Retrieves gene expression and omics datasets from ArrayExpress and BioStudies with gene disambiguation, experiment quality assessment, and structured reports. Creates comprehensive dataset profiles...
```
result = tu.tools.arrayexpress_search_experiments(
    keywords="breast cancer RNA-seq",
    species="Homo sapiens",
    limit=20
)
```

### tooluniverse-rnaseq-deseq2
**用途**: Production-ready RNA-seq differential expression analysis using PyDESeq2. Performs DESeq2 normalization, dispersion estimation, Wald testing, LFC shrinkage, and result filtering. Handles multi-fact...
```
pip install pydeseq2 gseapy pandas numpy scipy anndata
```
