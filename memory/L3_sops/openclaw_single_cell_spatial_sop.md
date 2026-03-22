# 单细胞与空间组学 SOP
> scRNA-seq 分析 (Scanpy/scVI)、空间转录组、轨迹分析、细胞注释、CellxGENE
> 包含 21 个 OpenClaw skill 的压缩迁移。

---

### anndata
**用途**: This skill should be used when working with annotated data matrices in Python, particularly for single-cell genomics analysis, managing experimental measurements with metadata, or handling large-sc...
```
uv pip install anndata

# With optional dependencies
uv pip install anndata[dev,test,doc]
```

### cellxgene-census
**用途**: Query CZ CELLxGENE Census (61M+ cells). Filter by cell type/tissue/disease, retrieve expression data, integrate with scanpy/PyTorch, for population-scale single-cell analysis.
```
uv pip install cellxgene-census
```

### scanpy
**用途**: Single-cell RNA-seq analysis. Load .h5ad/10X data, QC, normalization, PCA/UMAP/t-SNE, Leiden clustering, marker genes, cell type annotation, trajectory, for scRNA-seq analysis.
```
python scripts/qc_analysis.py input_file.h5ad --output filtered.h5ad
```

### scvi-tools
**用途**: This skill should be used when working with single-cell omics data analysis using scvi-tools, including scRNA-seq, scATAC-seq, CITE-seq, spatial transcriptomics, and other single-cell modalities. U...
```
uv pip install scvi-tools
# For GPU support
uv pip install scvi-tools[cuda]
```

### single-cell-annotation-skills-with-omicverse
**用途**: Guide Claude through SCSA, MetaTiME, CellVote, CellMatch, GPTAnno, and weighted KNN transfer workflows for annotating single-cell modalities.
```
# WRONG! 'cluster' is NOT a valid parameter for cell_auto_anno!
# scsa.cell_auto_anno(adata, cluster='leiden')  # ERROR!
```

### single-cell-rna-qc
**用途**: Performs quality control on single-cell RNA-seq data (.h5ad or .h5 files) using scverse best practices with MAD-based filtering and comprehensive visualizations. Use when users request QC analysis,...
```
python3 scripts/qc_analysis.py input.h5ad
# or for 10X Genomics .h5 files:
python3 scripts/qc_analysis.py raw_feature_bc_matrix.h5
```
**注意**: - Default thresholds intentionally retain most cells to avoid losing rare populations; - Always review before/after plots to ensure filtering makes biological sense; - Some tissues naturally have higher mitochondrial content (e.g., neurons, cardiomyocytes)

### single-cell-cellphonedb-communication-mapping
**用途**: Run omicverse's CellPhoneDB v5 wrapper on annotated single-cell data to infer ligand-receptor networks and produce CellChat-style visualisations.
```
cpdb_results, adata_cpdb = ov.single.run_cellphonedb_v5(
         adata,
         cpdb_file_path='./cellphonedb.zip',
         celltype_key='cell_labels',
         min_cell_fraction=0.005,
         min_genes=200,
         min_cells=3,
         iterations=1000,
         threshold=0.1,
         pvalue=0.05,
         threads=10,
         output_dir='./cpdb_results',
         cleanup_temp=True,
     )
```

### single-cell-clustering-and-batch-correction-with-omicverse
**用途**: Guide Claude through omicverse's single-cell clustering workflow, covering preprocessing, QC, multimethod clustering, topic modeling, cNMF, and cross-batch integration as demonstrated in t_cluster....
```
# Before clustering: check neighbors graph exists
     if 'neighbors' not in adata.uns:
         if 'X_pca' in adata.obsm:
             ov.pp.neighbors(adata, n_neighbors=15, use_rep='X_pca')
         else:
             raise ValueError("PCA must be computed before neighbors graph")

     # Before plotting by cluster: check clustering was performed
     if 'leiden' not in adata.obs:
         ov.single.leiden(adata, resolution=1.0)
```

### single-cell-downstream-analysis
**用途**: Checklist-style reference for OmicVerse downstream tutorials covering AUCell scoring, metacell DEG, and related exports.

### single-cell-multi-omics-integration
**用途**: Quick-reference sheet for OmicVerse tutorials spanning MOFA, GLUE pairing, SIMBA integration, TOSICA transfer, and StaVIA cartography.

### single-cell-preprocessing-with-omicverse
**用途**: Walk through omicverse's single-cell preprocessing tutorials to QC PBMC3k data, normalise counts, detect HVGs, and run PCA/embedding pipelines on CPU, CPU–GPU mixed, or GPU stacks.
```
ValueError: Extrapolation not allowed with blending
```

### single2spatial-spatial-mapping
**用途**: Map scRNA-seq atlases onto spatial transcriptomics slides using omicverse's Single2Spatial workflow for deep-forest training, spot-level assessment, and marker visualisation.

### single-trajectory-analysis
**用途**: Guide to reproducing OmicVerse trajectory workflows spanning PAGA, Palantir, VIA, velocity coupling, and fate scoring notebooks.

### spatial-agent
**用途**: 

### spatial-epigenomics-agent
**用途**: 
```
python3 Skills/Genomics/Spatial_Epigenomics_Agent/spatial_epigenomics.py \
    --input spatial_atac_fragments.tsv.gz \
    --coordinates spot_coordinates.csv \
    --peaks macs2_peaks.bed \
    --spatial_variable true \
    --motif_db jaspar_2024 \
    --integrate_with spatial_rna.h5ad \
    --output spatial_epi_results/
```

### spatial-transcriptomics-agent
**用途**: 
**触发条件**: Analysis of Visium/Xenium or similar ST datasets.; Visual reasoning over spatial plots, H&E images, or cluster maps.; Automatically generating Scanpy/Squidpy code for new ST workflows.; Hypothesis generation about spatial gene expression patterns.
```
User: "Analyze this breast cancer ST dataset, find immune infiltrates."
Agent: loads data, runs `sqidpy.gr.spatial_neighbors`, computes Leiden clusters, plots marker genes (CD3D, CD19), and summarizes which clusters map to tumor core vs. stromal/immune zones.
```

### spatial-transcriptomics-analysis
**用途**: 
```
from Skills.Genomics.Spatial_Transcriptomics.spatial_analyzer import SpatialAnalyzer

# Initialize
sa = SpatialAnalyzer(data_path="./data/visium_sample1")

# Run Pipeline
sa.load_data()
sa.preprocess()
sa.find_spatial_features()
sa.plot_spatial("INS", save_path="./output/insulin_spatial.png")
```

### spatial-transcriptomics-tutorials-with-omicverse
**用途**: Guide users through omicverse's spatial transcriptomics tutorials covering preprocessing, deconvolution, and downstream modelling workflows across Visium, Visium HD, Stereo-seq, and Slide-seq datas...

### tooluniverse-single-cell
**用途**: Production-ready single-cell and expression matrix analysis using scanpy, anndata, and scipy. Performs scRNA-seq QC, normalization, PCA, UMAP, Leiden/Louvain clustering, differential expression (Wi...
```
# One-way ANOVA across multiple groups
f_stat, p_val = stats.f_oneway(group1, group2, group3, ...)
```

### tooluniverse-spatial-omics-analysis
**用途**: Computational analysis framework for spatial multi-omics data integration. Given spatially variable genes (SVGs), spatial domain annotations, tissue type, and disease context from spatial transcrip...
```
# Spatial Multi-Omics Analysis Report: {Tissue Type}

**Report Generated**: {date}
**Technology**: {platform}
**Tissue**: {tissue_type}
**Disease Context**: {disease or "Normal tissue"}
**Total SVGs Analyzed**: {count}
**Spatial Domains**: {count}
**Spatial Omics Integration Score**: (to be calculated)

---

## Executive Summary

(2-3 sentence synthesis of key spatial findings - fill after all phases complete)

---

## 1. Tissue & Disease Context

### Tissue Information
| Property | Value | Sour
# ... (truncated)
```

### tooluniverse-spatial-transcriptomics
**用途**: Analyze spatial transcriptomics data to map gene expression in tissue architecture. Supports 10x Visium, MERFISH, seqFISH, Slide-seq, and imaging-based platforms. Performs spatial clustering, domai...
```
def select_hvg_spatial(adata):
    """
    Select highly variable genes for spatial analysis.
    """
    import scanpy as sc

    # Standard HVG selection
    sc.pp.highly_variable_genes(adata, n_top_genes=2000)

    # Optionally: weight by spatial autocorrelation
    # Genes with spatial patterns are more informative

    return adata
```
**限制**: **Resolution**: Visium spots contain multiple cells (not single-cell); **Gene coverage**: Imaging methods have limited gene panels
