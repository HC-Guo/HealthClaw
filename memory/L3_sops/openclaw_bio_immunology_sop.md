# gptomics 免疫信息学 SOP
> TCR/BCR 库分析、免疫组库、克隆性
> 包含 5 个 OpenClaw skill 的压缩迁移。

---

### bio-tcr-bcr-analysis-immcantation-analysis
**用途**: Analyze BCR repertoires for somatic hypermutation, clonal lineages, and B cell phylogenetics using the Immcantation framework. Use when studying B cell affinity maturation, germinal center dynamics...
```
library(alakazam)
library(shazam)
library(dplyr)

# Load AIRR-formatted data (from MiXCR, IMGT/HighV-QUEST, etc.)
db <- readChangeoDb('clones_airr.tsv')

# Required columns:
# sequence_id, sequence, v_call, d_call, j_call, junction, junction_aa
```

### bio-tcr-bcr-analysis-mixcr-analysis
**用途**: Perform V(D)J alignment and clonotype assembly from TCR-seq or BCR-seq data using MiXCR. Use when processing raw immune repertoire sequencing data to identify clonotypes and their frequencies.
```
mixcr refineTagsAndSort alignments.vdjca alignments_refined.vdjca

mixcr assemble alignments_refined.vdjca clones.clns
```

### bio-tcr-bcr-analysis-repertoire-visualization
**用途**: Create publication-quality visualizations of immune repertoire data including circos plots, clone tracking, diversity plots, and network graphs. Use when generating figures for repertoire compariso...
```
# Generate V-J usage circos plot
vdjtools PlotFancyVJUsage \
    -m metadata.txt \
    output_dir/

# Generates PDF circos plots showing V-J pairing frequencies
```

### bio-tcr-bcr-analysis-scirpy-analysis
**用途**: Analyze single-cell TCR and BCR data integrated with gene expression using scirpy. Use when working with 10x Genomics VDJ data alongside scRNA-seq or when integrating immune receptor information wi...
```
# Identify expanded clonotypes
ir.tl.clonal_expansion(adata)

# Categories: 1 (singleton), 2, 3-10, >10

# Plot expansion by cell type
ir.pl.clonal_expansion(adata, groupby='cell_type')
```

### bio-tcr-bcr-analysis-vdjtools-analysis
**用途**: Calculate immune repertoire diversity metrics, compare samples, and track clonal dynamics using VDJtools. Use when analyzing repertoire diversity, finding shared clonotypes, or comparing immune pro...
```
# Convert MiXCR output to VDJtools format
vdjtools Convert \
    -S mixcr \
    mixcr_clones.txt \
    output.txt
```
