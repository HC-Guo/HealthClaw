# gptomics 差异表达核心 SOP
> DESeq2/edgeR 基础、DE 结果处理、RNA-seq QC
> 包含 4 个 OpenClaw skill 的压缩迁移。

---

### bio-de-deseq2-basics
**用途**: Perform differential expression analysis using DESeq2 in R/Bioconductor. Use for analyzing RNA-seq count data, creating DESeqDataSet objects, running the DESeq workflow, and extracting results with...
```
library(DESeq2)
library(apeglm)  # For lfcShrink with type='apeglm'
```

### bio-de-edger-basics
**用途**: Perform differential expression analysis using edgeR in R/Bioconductor. Use for analyzing RNA-seq count data with the quasi-likelihood F-test framework, creating DGEList objects, normalization, dis...
```
library(edgeR)
library(limma)  # For design matrices and voom
```

### bio-de-results
**用途**: Extract, filter, annotate, and export differential expression results from DESeq2 or edgeR. Use for identifying significant genes, applying multiple testing corrections, adding gene annotations, an...
```
library(DESeq2)  # or library(edgeR)
library(dplyr)   # For data manipulation
```

### bio-rnaseq-qc
**用途**: RNA-seq specific quality control including rRNA contamination detection, strandedness verification, gene body coverage, and transcript integrity metrics. Use when validating RNA-seq libraries befor...
```
infer_experiment.py -i aligned.bam -r genes.bed
```
