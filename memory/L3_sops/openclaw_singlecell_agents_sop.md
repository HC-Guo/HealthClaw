# 单细胞分析智能体 SOP
> CellAgent、scFoundation、RNA 速度、cfRNA、通用注释器
> 包含 11 个 OpenClaw skill 的压缩迁移。

---

### bioinformatics-singlecell
**用途**: 
```
# Save processed data
adata.write('processed_adata.h5ad')
model.save('totalvi_model/')
df.to_csv('DEG_results.csv', index=False)
```

### cellagent-annotation
**用途**: 
**触发条件**: Automated annotation of scRNA-seq datasets without manual curation.; Multi-step workflows (QC → clustering → annotation → DE analysis).; Integrating multiple batches requiring consistent labeling.
```
python3 Skills/Genomics/Single_Cell/CellAgent/repo/main.py --data "./data.h5ad" --goal "annotate"
```

### cellfree-rna-agent
**用途**: 
```
python3 Skills/Genomics/CellFree_RNA_Agent/cfrna_analyzer.py \
    --input plasma_cfrna.fastq.gz \
    --protocol total_rna \
    --reference gencode_v44 \
    --deconvolution true \
    --cancer_detection true \
    --output cfrna_results/
```

### deep-visual-proteomics-agent
**用途**: 
```
Input: Protein abundances
  ↓
Pathway Layer: Proteins → Pathways (sparse connections)
  ↓
Process Layer: Pathways → Biological processes
  ↓
Output: Phenotype classification + pathway importance scores
```

### exosome-ev-analysis-agent
**用途**: 
```
python3 Skills/Oncology/Exosome_EV_Analysis_Agent/ev_analyzer.py \
    --ev_mirna exosome_smallrna.tsv \
    --ev_protein exosome_proteome.tsv \
    --sample_groups pancreatic_cancer,healthy \
    --normalization spike_in \
    --biomarker_discovery true \
    --output ev_biomarker_report/
```

### nicheformer-spatial-agent
**用途**: 
```
python3 Skills/Genomics/Nicheformer_Spatial_Agent/nicheformer_analysis.py \
    --spatial_data xenium_tumor.h5ad \
    --model_weights nicheformer_pretrained.pt \
    --k_neighbors 15 \
    --niche_resolution 0.5 \
    --reference_atlas tabula_sapiens.h5ad \
    --output tumor_niches_analysis/
```

### rna-velocity-agent
**用途**: 
```
Transcription → Unspliced RNA → Splicing → Spliced (mature) mRNA → Degradation

Velocity = d[spliced]/dt = β[unspliced] - γ[spliced]

- Positive velocity: Gene upregulating
- Negative velocity: Gene downregulating
- Zero velocity: Steady state
```

### scfoundation-model-agent
**用途**: 
```
python3 foundation_predict.py \
    --input multi_batch.h5ad \
    --model scfoundation \
    --task integration \
    --batch_key batch \
    --output integrated.h5ad
```

### scrna-qc
**用途**: 

### scvelo
**用途**: RNA velocity analysis with scVelo. Estimate cell state transitions from unspliced/spliced mRNA dynamics, infer trajectory directions, compute latent time, and identify driver genes in single-cell R...
```
# Recover dynamics (computationally intensive; ~10-30 min for 10K cells)
scv.tl.recover_dynamics(adata, n_jobs=4)

# Compute velocity from dynamical model
scv.tl.velocity(adata, mode='dynamical')
scv.tl.velocity_graph(adata)
```
**注意**: **Start with stochastic mode** for exploration; switch to dynamical for final analysis; **Need good coverage of unspliced reads**: Short reads (< 100 bp) may miss intron coverage; **Minimum 2,000 cells**: RNA velocity is noisy with fewer cells

### universal-single-cell-annotator
**用途**: 
```
from universal_annotator import UniversalAnnotator
import scanpy as sc

adata = sc.read_h5ad('data.h5ad')
annotator = UniversalAnnotator(adata)

markers = {
    'T-cell': ['CD3D', 'CD3E', 'CD8A'],
    'B-cell': ['CD79A', 'MS4A1']
}

annotator.annotate_marker_based(markers)
# Results in adata.obs['predicted_cell_type']
```
