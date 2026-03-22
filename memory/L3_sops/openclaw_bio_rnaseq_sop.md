# gptomics RNA 定量与差异表达 SOP
> RNA 定量、差异表达分析、Ribo-seq、表达矩阵
> 包含 15 个 OpenClaw skill 的压缩迁移。

---

### bio-differential-expression-batch-correction
**用途**: Remove batch effects from RNA-seq data using ComBat, ComBat-Seq, limma removeBatchEffect, and SVA for unknown batch variables. Use when correcting batch effects in expression data.
```
# DON'T use batch-corrected values for:
# - Differential expression (use design formula instead)
# - Count-based methods expecting raw/normalized counts

# DO use batch-corrected values for:
# - Visualization (PCA, UMAP, heatmaps)
# - Clustering
# - Machine learning features
# - Cross-study comparisons
```

### bio-differential-expression-timeseries-de
**用途**: Analyze time-series RNA-seq data using limma voom with splines, maSigPro, and ImpulseDE2. Identify genes with dynamic expression patterns. Use when analyzing time-series or longitudinal expression ...
```
BiocManager::install('maSigPro')
```

### bio-expression-matrix-counts-ingest
**用途**: 
```
# Remove Ensembl version numbers (ENSG00000123456.12 -> ENSG00000123456)
counts.index = counts.index.str.split('.').str[0]

# Or keep as-is for compatibility
```

### bio-expression-matrix-gene-id-mapping
**用途**: 
```
import gseapy as gp

# Ensembl to Symbol using Enrichr
gene_list = ['ENSG00000141510', 'ENSG00000012048']
converted = gp.biomart.ensembl2name(gene_list, organism='hsapiens')
```

### bio-expression-matrix-metadata-joins
**用途**: 
```
import pandas as pd

# Load metadata
metadata = pd.read_csv('sample_info.csv', index_col=0)

# Metadata should have samples as rows, attributes as columns
# Index should match count matrix column names
```

### bio-expression-matrix-sparse-handling
**用途**: 
```
import pandas as pd
import scipy.sparse as sp

# To numpy array
dense_array = sparse_matrix.toarray()

# To pandas DataFrame
dense_df = pd.DataFrame(
    sparse_matrix.toarray(),
    index=gene_names,
    columns=sample_names
)
```

### bio-ribo-seq-orf-detection
**用途**: Detect and quantify translated ORFs from Ribo-seq data including uORFs and novel ORFs using RiboCode and ORFquant. Use when identifying translated regions beyond annotated coding sequences or quant...
```
# Install from Bioconductor
BiocManager::install('ORFik')
# ORFquant is part of the ORFik ecosystem
```

### bio-ribo-seq-riboseq-preprocessing
**用途**: Preprocess ribosome profiling data including adapter trimming, size selection, rRNA removal, and alignment. Use when preparing Ribo-seq reads for downstream analysis of translation.
```
# Trim 3' adapter
cutadapt \
    -a CTGTAGGCACCATCAAT \
    -m 20 \
    -M 40 \
    -o trimmed.fastq.gz \
    input.fastq.gz
```

### bio-ribo-seq-ribosome-periodicity
**用途**: Validate Ribo-seq data quality by checking 3-nucleotide periodicity and calculating P-site offsets. Use when assessing library quality or determining read offsets for downstream analysis.
```
# RiboCode includes periodicity analysis
RiboCode_onestep \
    -g annotation.gtf \
    -r riboseq.bam \
    -f genome.fa \
    -o output_dir

# Check output for periodicity plots
```

### bio-ribo-seq-ribosome-stalling
**用途**: Detect ribosome pausing and stalling sites from Ribo-seq data at codon resolution. Use when studying translational regulation, identifying pause sites, or analyzing codon-specific translation dynam...
```
def correlate_with_trna(codon_occupancy, trna_abundance):
    '''Test if pausing correlates with tRNA availability

    Rare codons (low tRNA) should have higher occupancy
    '''
    from scipy import stats

    codons = list(set(codon_occupancy.keys()) & set(trna_abundance.keys()))

    occ = [codon_occupancy[c] for c in codons]
    trna = [trna_abundance[c] for c in codons]

    corr, pval = stats.spearmanr(occ, trna)

    return corr, pval  # Expect negative correlation
```

### bio-ribo-seq-translation-efficiency
**用途**: Calculate translation efficiency (TE) as the ratio of ribosome occupancy to mRNA abundance. Use when comparing translational regulation between conditions or identifying genes with altered translat...
```
library(DESeq2)

# Combine Ribo-seq and RNA-seq counts
counts <- cbind(ribo_counts, rna_counts)

# Design matrix with interaction term
coldata <- data.frame(
    condition = factor(rep(c('ctrl', 'ctrl', 'treat', 'treat'), 2)),
    assay = factor(rep(c('ribo', 'rna'), each = 4)),
    row.names = colnames(counts)
)

dds <- DESeqDataSetFromMatrix(
    countData = counts,
    colData = coldata,
    design = ~ condition + assay + condition:assay
)

dds <- DESeq(dds)

# The interaction term tests for 
# ... (truncated)
```

### bio-rna-quantification-alignment-free-quant
**用途**: 
```
kallisto index -i kallisto_index transcripts.fa
```

### bio-rna-quantification-count-matrix-qc
**用途**: 
```
from sklearn.preprocessing import StandardScaler

cpm = counts * 1e6 / counts.sum()
log_cpm = np.log2(cpm + 1)
```

### bio-rna-quantification-featurecounts-counting
**用途**: 
```
# Remove first 6 columns (metadata) to get just counts
cut -f1,7- counts.txt | tail -n +2 > count_matrix.txt
```

### bio-rna-quantification-tximport-workflow
**用途**: 
```
txi <- tximport(files, type = 'rsem', tx2gene = tx2gene)
```
