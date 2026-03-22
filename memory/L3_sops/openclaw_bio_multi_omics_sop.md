# gptomics 多组学整合 SOP
> 多组学整合、实验设计
> 包含 8 个 OpenClaw skill 的压缩迁移。

---

### bio-experimental-design-batch-design
**用途**: 
```
# BAD: Confounded design
# Batch 1: All treated samples
# Batch 2: All control samples
# -> Cannot separate batch from treatment

# GOOD: Balanced design
# Batch 1: 3 treated, 3 control
# Batch 2: 3 treated, 3 control
# -> Batch effect can be estimated and removed
```

### bio-experimental-design-multiple-testing
**用途**: 
```
# Controls false discovery rate
p_adj <- p.adjust(pvalues, method = 'BH')
# Most common for genomics
# FDR 0.05 = expect 5% of significant results to be false
```

### bio-experimental-design-power-analysis
**用途**: 
```
library(ssizeRNA)

# For differential accessibility
size.zhao(m = 10000, m1 = 500, fc = 2, fdr = 0.05, power = 0.8,
          mu = 10, disp = 0.1)
```

### bio-experimental-design-sample-size
**用途**: 
```
library(powsimR)

# Estimate for scRNA-seq
# Accounts for dropout and cell-to-cell variability
params <- estimateParam(pilot_sce)
power <- simulateDE(params, n1 = 100, n2 = 100,
                    p.DE = 0.1, pLFC = 1)
```

### bio-multi-omics-data-harmonization
**用途**: Preprocessing and harmonization of multi-omics data before integration. Covers normalization, batch correction, feature alignment, and missing value handling across data types. Use when preparing m...
```
# Find complete samples across all assays
complete_samples <- intersectColumns(mae)
cat('Samples in all assays:', ncol(complete_samples), '\n')

# Subset to common samples
mae_matched <- mae[, complete_samples, ]

# Alternative: keep samples with N-1 assays
subsetByColData(mae, mae$has_at_least_2_assays)
```

### bio-multi-omics-mixomics-analysis
**用途**: Supervised and unsupervised multi-omics integration with mixOmics. Includes sPLS for pairwise integration and DIABLO for multi-block discriminant analysis. Use when performing supervised multi-omic...
```
# Cross-validation performance
perf_result <- perf(diablo, validation = 'Mfold', folds = 5, nrepeat = 50, cpus = 4)

# Error rates
plot(perf_result)
perf_result$error.rate

# AUC
auc_diablo <- auroc(diablo, roc.block = 'RNA', roc.comp = 1)
```

### bio-multi-omics-mofa-integration
**用途**: Multi-Omics Factor Analysis (MOFA2) for unsupervised integration of multiple data modalities. Identifies shared and view-specific sources of variation. Use when integrating RNA-seq, proteomics, met...
```
# Load sample annotations
metadata <- read.csv('sample_metadata.csv', row.names = 1)

# Add to MOFA object
samples_metadata(mofa) <- metadata[samples_names(mofa)[[1]], ]

# Color by metadata
plot_factor(mofa, factor = 1, color_by = 'Condition')
plot_factors(mofa, factors = 1:3, color_by = 'Condition')
```

### bio-multi-omics-similarity-network
**用途**: Similarity Network Fusion (SNF) for patient stratification using multi-omics data. Integrates multiple data types into a unified patient similarity network. Use when performing patient stratificati...
```
# Determine optimal number of clusters
estimateNumberOfClustersGivenGraph(fused, NUMC = 2:10)

# Spectral clustering
num_clusters <- 3
clusters <- spectralClustering(fused, num_clusters)

# Add to sample metadata
sample_info <- data.frame(
    Sample = rownames(data1),
    Cluster = factor(clusters)
)
```
