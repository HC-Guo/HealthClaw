# gptomics 甲基化分析 SOP
> Bismark 比对、甲基化检测、DMR、MethylKit
> 包含 5 个 OpenClaw skill 的压缩迁移。

---

### bio-methylation-based-detection
**用途**: Analyzes cfDNA methylation patterns for cancer detection using cfMeDIP-seq or bisulfite sequencing with MethylDackel. Identifies cancer-specific methylation signatures and performs tissue-of-origin...
```
# Extract methylation from bisulfite BAM
MethylDackel extract \
    reference.fa \
    sample_bismark.bam \
    --CHG \
    --CHH \
    -o sample_methylation

# Output: sample_methylation_CpG.bedGraph, etc.

# Merge C and G strand calls
MethylDackel mergeContext \
    reference.fa \
    sample_methylation
```

### bio-methylation-bismark-alignment
**用途**: Bisulfite sequencing read alignment using Bismark with bowtie2/hisat2. Handles genome preparation and produces BAM files with methylation information. Use when aligning WGBS, RRBS, or other bisulfi...
```
bismark --genome /path/to/genome_folder/ reads.fastq.gz -o output_dir/
```

### bio-methylation-calling
**用途**: Extract methylation calls from Bismark BAM files using bismark_methylation_extractor. Generates per-cytosine reports for CpG, CHG, and CHH contexts. Use when extracting methylation levels from alig...
```
bismark_methylation_extractor --paired-end --gzip --bedGraph \
    sample_bismark_bt2_pe.bam
```

### bio-methylation-dmr-detection
**用途**: Differentially methylated region (DMR) detection using methylKit tiles, bsseq BSmooth, and DMRcate. Use when identifying contiguous genomic regions with methylation differences between experimental...
```
library(GenomicRanges)

dmr_gr <- as(dmrs, 'GRanges')

# Merge DMRs within 500bp
dmr_merged <- reduce(dmr_gr, min.gapwidth = 500)
```

### bio-methylation-methylkit
**用途**: DNA methylation analysis with methylKit in R. Import Bismark coverage files, filter by coverage, normalize samples, and perform statistical comparisons. Use when analyzing single-base methylation p...
```
# Combine biological replicates
meth_pooled <- pool(meth_united, sample.ids = c('control', 'treatment'))
```
