# gptomics 单细胞分析 SOP
> 单细胞 RNA-seq QC、聚类、注释、轨迹、细胞通讯
> 包含 15 个 OpenClaw skill 的压缩迁移。

---

### bio-single-cell-batch-integration
**用途**: Integrate multiple scRNA-seq samples/batches using Harmony, scVI, Seurat anchors, and fastMNN. Remove technical variation while preserving biological differences. Use when integrating multiple scRN...
```
# Correct for both sample and technology
merged <- RunHarmony(merged, group.by.vars = c('sample', 'technology'),
                     dims.use = 1:30, max.iter.harmony = 20)
```

### bio-single-cell-cell-annotation
**用途**: Automated cell type annotation using reference-based methods including CellTypist, scPred, SingleR, and Azimuth for consistent, reproducible cell labeling. Use when automatically annotating cell ty...
```
# CellTypist: filter low confidence
high_conf = adata[adata.obs['conf_score'] > 0.5].copy()

# Flag uncertain cells
adata.obs['annotation_uncertain'] = adata.obs['conf_score'] < 0.3
```

### bio-single-cell-cell-communication
**用途**: Infer cell-cell communication networks from scRNA-seq data using CellChat, NicheNet, and LIANA for ligand-receptor interaction analysis. Use when inferring ligand-receptor interactions between cell...
```
# Identify signaling roles
cellchat <- netAnalysis_computeCentrality(cellchat, slot.name = 'netP')

# Signaling role heatmap
netAnalysis_signalingRole_heatmap(cellchat, signaling = c('WNT', 'TGFb', 'BMP'))

# Dominant senders/receivers
netAnalysis_signalingRole_scatter(cellchat)

# Compare pathways
rankNet(cellchat, mode = 'comparison', stacked = TRUE, do.stat = TRUE)
```

### bio-single-cell-clustering
**用途**: Dimensionality reduction and clustering for single-cell RNA-seq using Seurat (R) and Scanpy (Python). Use for running PCA, computing neighbors, clustering with Leiden/Louvain algorithms, generating...
```
library(Seurat)
library(ggplot2)
```

### bio-single-cell-data-io
**用途**: Read, write, and create single-cell data objects using Seurat (R) and Scanpy (Python). Use for loading 10X Genomics data, importing/exporting h5ad and RDS files, creating Seurat objects and AnnData...
```
library(Seurat)
library(Matrix)
```

### bio-single-cell-doublet-detection
**用途**: Detect and remove doublets (multiple cells captured in one droplet) from single-cell RNA-seq data. Uses Scrublet (Python), DoubletFinder (R), and scDblFinder (R). Essential QC step before clusterin...
```
sce <- scDblFinder(sce, samples = 'sample_id')
```

### bio-single-cell-lineage-tracing
**用途**: Reconstruct cell lineage trees from CRISPR barcode tracing or mitochondrial mutations. Use when studying clonal dynamics, cell fate decisions, or developmental trajectories.
```
# Fate coupling between cell types
cs.tl.fate_coupling(adata, source='HSC')
cs.pl.fate_coupling(adata, source='HSC')

# Transition probabilities over time
cs.tl.transition_map(adata, time_key='day')
cs.pl.transition_map(adata)

# Clone size dynamics
cs.tl.clone_size(adata, time_key='day')
cs.pl.clone_size(adata)
```

### bio-single-cell-markers-annotation
**用途**: Find marker genes and annotate cell types in single-cell RNA-seq using Seurat (R) and Scanpy (Python). Use for differential expression between clusters, identifying cluster-specific markers, scorin...
```
library(Seurat)
library(dplyr)
```

### bio-single-cell-metabolite-communication
**用途**: Analyze metabolite-mediated cell-cell communication using MeboCost for metabolic signaling inference between cell types. Predict metabolite secretion and sensing patterns from scRNA-seq data. Use w...
```
import mebocost as mbc
import scanpy as sc

# Load scRNA-seq data
adata = sc.read_h5ad('adata.h5ad')

# Initialize MeboCost
mebo = mbc.create_obj(
    adata=adata,
    group_col='cell_type',  # Cell type annotation column
    species='human'  # 'human' or 'mouse'
)

# Infer metabolite communication
mebo.infer_commu(
    n_permutations=1000,  # Permutations for significance testing
    seed=42
)

# Get significant interactions
sig_interactions = mebo.commu_res[mebo.commu_res['pval'] < 0.05]
```

### bio-single-cell-multimodal-integration
**用途**: Analyze multi-modal single-cell data (CITE-seq, Multiome, spatial). Use when working with data that measures multiple modalities per cell like RNA + protein or RNA + ATAC. Use when analyzing CITE-s...
```
# Check how much each modality contributes per cell
weights <- obj@reductions$wnn@misc$weights

# Average weight by cluster
aggregate(weights, by = list(obj$seurat_clusters), mean)
```

### bio-single-cell-perturb-seq
**用途**: Analyze Perturb-seq and CROP-seq CRISPR screening data integrated with scRNA-seq. Use when identifying gene function through pooled genetic perturbations in single cells.
```
import decoupler as dc

# Get DE genes per perturbation
de_results = pb.results()

# Run pathway enrichment
dc.run_ora(
    mat=de_results,
    net=dc.get_resource('MSigDB'),
    source='geneset',
    target='gene'
)

# Visualize top pathways
dc.plot_barplot(de_results, 'TP53', top_n=20)
```

### bio-single-cell-preprocessing
**用途**: Quality control, filtering, and normalization for single-cell RNA-seq using Seurat (R) and Scanpy (Python). Use for calculating QC metrics, filtering cells and genes, normalizing counts, identifyin...
```
library(Seurat)
library(ggplot2)
```

### bio-single-cell-scatac-analysis
**用途**: Single-cell ATAC-seq analysis with Signac (R/Seurat) and ArchR. Process 10X Genomics scATAC data, perform QC, dimensionality reduction, clustering, peak calling, and motif activity scoring with chr...
```
BiocManager::install('chromVAR')
```

### bio-single-cell-splicing
**用途**: Analyzes alternative splicing at single-cell resolution using BRIE2 for probabilistic PSI estimation or leafcutter2 for cluster-based analysis with NMD detection. Identifies cell-type-specific spli...
```
import pandas as pd
import numpy as np

# For better statistical power, aggregate cells by type
def pseudobulk_junctions(junction_counts, cell_metadata, groupby='cell_type'):
    '''Aggregate junction counts by cell group.'''
    groups = cell_metadata.groupby(groupby).groups

    pseudobulk = {}
    for group, cells in groups.items():
        cell_mask = junction_counts.index.isin(cells)
        pseudobulk[group] = junction_counts.loc[cell_mask].sum()

    return pd.DataFrame(pseudobulk)

# Run
# ... (truncated)
```

### bio-single-cell-trajectory-inference
**用途**: Infer developmental trajectories and pseudotime from single-cell RNA-seq data using Monocle3, Slingshot, and scVelo for RNA velocity analysis. Use when inferring developmental trajectories or pseud...
```
# Generate loom file with spliced/unspliced counts
velocyto run10x -m repeat_mask.gtf /path/to/cellranger_output annotation.gtf

# For SmartSeq2
velocyto run_smartseq2 -o output -m repeat_mask.gtf -e sample bam_files/*.bam annotation.gtf
```
