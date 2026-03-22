# gptomics 流式细胞术 SOP
> 流式数据分析、设门、补偿、高维聚类
> 包含 8 个 OpenClaw skill 的压缩迁移。

---

### bio-flow-cytometry-bead-normalization
**用途**: Bead-based normalization for CyTOF and high-parameter flow cytometry. Covers EQ bead normalization, signal drift correction, and batch normalization. Use when correcting instrument drift in CyTOF o...
```
# Save normalized FCS files
write.FCS(ff_clean, 'normalized_sample.fcs')

# For CATALYST object
# saveRDS(sce, 'normalized_sce.rds')
```

### bio-flow-cytometry-clustering-phenotyping
**用途**: Unsupervised clustering and cell type identification for flow/mass cytometry. Covers FlowSOM, Phenograph, and CATALYST workflows. Use when discovering cell populations in high-dimensional cytometry...
```
# UMAP
sce <- runDR(sce, dr = 'UMAP', features = 'type')

# tSNE
sce <- runDR(sce, dr = 'TSNE', features = 'type')

# Plot
plotDR(sce, 'UMAP', color_by = 'meta20')
```

### bio-flow-cytometry-compensation-transformation
**用途**: Spillover compensation and data transformation for flow cytometry. Covers compensation matrix calculation, application, and biexponential/arcsinh transforms. Use when correcting spectral overlap be...
```
# Create compensation object
comp <- compensation(comp_matrix)

# Apply to flowFrame
fcs_comp <- compensate(fcs, comp)

# Apply to flowSet
fs_comp <- compensate(fs, comp)
```

### bio-flow-cytometry-cytometry-qc
**用途**: Comprehensive quality control for flow cytometry and CyTOF data. Covers flow rate stability, signal drift, margin events, dead cell exclusion, and batch QC. Use when assessing acquisition quality o...
```
library(flowAI)
library(flowCore)

# Load FCS file
ff <- read.FCS('sample.fcs')

# Run automated QC
# Checks: flow rate, signal stability, dynamic range
qc_result <- flow_auto_qc(
    ff,
    folder_results = 'qc_output/',
    fcs_QC = TRUE,       # Export QC'd FCS
    html_report = TRUE,  # Generate HTML report
    mini_report = TRUE   # Also make summary
)

# Get cleaned data
ff_clean <- qc_result$fcs

# QC metrics
cat('Original events:', nrow(ff), '\n')
cat('After QC:', nrow(ff_clean), '\n')

# ... (truncated)
```

### bio-flow-cytometry-differential-analysis
**用途**: Differential abundance and state analysis for cytometry data. Compare cell populations between conditions using statistical methods. Use when testing for significant changes in cell frequencies or ...
```
# DA results heatmap
plotDiffHeatmap(sce, res_DA, all = TRUE, fdr = 0.05)

# DS results heatmap
plotDiffHeatmap(sce, res_DS, all = TRUE, fdr = 0.05)

# Abundance by condition
plotAbundances(sce, k = 'meta20', by = 'cluster_id', group_by = 'condition')
```

### bio-flow-cytometry-doublet-detection
**用途**: Detect and remove doublets from flow and mass cytometry data. Covers FSC/SSC gating and computational doublet detection methods. Use when filtering out cell aggregates before clustering or quantita...
```
# For cell types where FSC doesn't discriminate well,
# use SSC-A vs SSC-H additionally

ssc_singlet_gate <- rectangleGate(
    filterId = 'ssc_singlets',
    'SSC-A' = c(10000, 200000),
    'SSC-H' = c(10000, 200000)
)

# Combine FSC and SSC gates
combined_gate <- singlet_gate & ssc_singlet_gate
singlets <- Subset(fs, combined_gate)
```

### bio-flow-cytometry-fcs-handling
**用途**: Read and manipulate Flow Cytometry Standard (FCS) files. Covers loading data, accessing parameters, and basic data exploration. Use when loading and inspecting flow or mass cytometry data before pr...
```
# Write single file
write.FCS(fcs, 'output.fcs')

# Write flowSet
write.flowSet(fs, outdir = 'output_dir')
```

### bio-flow-cytometry-gating-analysis
**用途**: Manual and automated gating for defining cell populations in flow cytometry. Covers rectangular, polygon, and data-driven gates. Use when identifying cell populations through hierarchical gating st...
```
# Save GatingSet
save_gs(gs, 'gating_set')

# Export to FlowJo workspace
library(CytoML)
gatingset_to_flowjo(gs, 'analysis.wsp')
```
