# gptomics 测序读长 QC 与比对 SOP
> FASTQ QC、reads 比对、比对文件操作、索引、排序、MSA
> 包含 22 个 OpenClaw skill 的压缩迁移。

---

### bio-alignment-files-bam-statistics
**用途**: 
```
samtools flagstat input.bam
```

### bio-alignment-filtering
**用途**: 
```
samtools view -F 4 -o mapped.bam input.bam
```

### bio-alignment-indexing
**用途**: 
```
input.cram.crai
```

### bio-alignment-io
**用途**: Read, write, and convert multiple sequence alignment files using Biopython Bio.AlignIO. Supports Clustal, PHYLIP, Stockholm, FASTA, Nexus, and other alignment formats for phylogenetics and conserva...
```
AlignIO.write(alignment, 'output.fasta', 'fasta')
```

### bio-alignment-msa-parsing
**用途**: Parse and analyze multiple sequence alignments using Biopython. Extract sequences, identify conserved regions, analyze gaps, work with annotations, and manipulate alignment data for downstream anal...
```
seq_ids = [record.id for record in alignment]
```

### bio-alignment-msa-statistics
**用途**: Calculate alignment statistics including sequence identity, conservation scores, substitution matrices, and similarity metrics. Use when comparing alignment quality, measuring sequence divergence, ...
```
from Bio import AlignIO
from Bio.Align import substitution_matrices
from collections import Counter
import numpy as np
import math
```

### bio-alignment-pairwise
**用途**: Perform pairwise sequence alignment using Biopython Bio.Align.PairwiseAligner. Use when comparing two sequences, finding optimal alignments, scoring similarity, and identifying local or global matc...
```
from Bio.Align import PairwiseAligner
from Bio.Seq import Seq
from Bio import SeqIO
```

### bio-alignment-sorting
**用途**: 
```
samtools sort -o sorted.bam input.bam
```

### bio-alignment-validation
**用途**: 
```
samtools idxstats input.bam | awk '{print $1, $3/$2}' | head -25
```

### bio-long-read-sequencing-clair3-variants
**用途**: Deep learning-based variant calling from long reads using Clair3 for SNPs and small indels. Use when calling germline variants from ONT or PacBio alignments, particularly when high accuracy is need...
```
# List available models
ls ${CONDA_PREFIX}/bin/models/

# Specify exact model
run_clair3.sh \
    --bam_fn=sample.bam \
    --ref_fn=reference.fasta \
    --model_path=${CONDA_PREFIX}/bin/models/r1041_e82_400bps_sup_v430 \
    --output=clair3_out \
    --threads=32
```

### bio-long-read-sequencing-isoseq-analysis
**用途**: Analyze PacBio Iso-Seq data for full-length isoform discovery and quantification. Use when characterizing transcript diversity or identifying novel splice variants.
```
>primer_5p
AAGCAGTGGTATCAACGCAGAGTACATGGG
>primer_3p
AAGCAGTGGTATCAACGCAGAGTAC
```

### bio-long-read-sequencing-nanopore-methylation
**用途**: Calls DNA methylation from Oxford Nanopore sequencing data using signal-level analysis. Use when detecting 5mC or 6mA modifications directly from nanopore reads without bisulfite conversion.
```
# Assumes BAM has MM/ML tags from dorado basecalling
modkit pileup input.bam methylation.bed \
    --ref reference.fa \
    --cpg \
    --combine-strands
```

### bio-read-alignment-bowtie2-alignment
**用途**: 
```
# Bowtie2 prints alignment summary to stderr
bowtie2 -p 8 -x index -1 r1.fq -2 r2.fq -S aligned.sam 2> alignment_stats.txt
```

### bio-read-alignment-bwa-alignment
**用途**: 
```
# For SV detection, use -Y for soft clipping
bwa-mem2 mem -t 8 -Y reference.fa r1.fq r2.fq > aligned.sam
```

### bio-read-alignment-hisat2-alignment
**用途**: 
```
# HISAT2 prints summary to stderr
hisat2 -p 8 -x hisat2_index -1 r1.fq.gz -2 r2.fq.gz -S aligned.sam 2> summary.txt
```

### bio-read-alignment-star-alignment
**用途**: 
```
STAR --runThreadN 8 \
    --genomeDir star_index/ \
    --readFilesIn reads.fq.gz \
    --readFilesCommand zcat \
    --outFileNamePrefix sample_ \
    --outSAMtype BAM SortedByCoordinate
```

### bio-read-qc-adapter-trimming
**用途**: Remove sequencing adapters from FASTQ files using Cutadapt and Trimmomatic. Supports single-end and paired-end reads, Illumina TruSeq, Nextera, and custom adapter sequences. Use when FastQC shows a...
```
trimmomatic SE -phred33 \
    input.fastq.gz output.fastq.gz \
    ILLUMINACLIP:adapters.fa:2:30:10
```

### bio-read-qc-contamination-screening
**用途**: Detect sample contamination and cross-species reads using FastQ Screen. Screen reads against multiple reference genomes to identify bacterial, viral, adapter, or sample swap contamination. Use when...
```
# Index a FASTA file
bowtie2-build reference.fa reference

# Add to config
# DATABASE	MyGenome	/path/to/reference
```

### bio-read-qc-fastp-workflow
**用途**: All-in-one read preprocessing with fastp including adapter trimming, quality filtering, deduplication, base correction, and HTML report generation. Use when preprocessing Illumina data and wanting ...
```
fastp -i input.fastq.gz -o output.fastq.gz
```

### bio-read-qc-quality-filtering
**用途**: Filter reads by quality scores, length, and N content using Trimmomatic and fastp. Apply sliding window trimming, remove low-quality bases from read ends, and discard reads below thresholds. Use wh...
```
trimmomatic SE -phred33 \
    input.fastq.gz output.fastq.gz \
    LEADING:3 TRAILING:3 SLIDINGWINDOW:4:15 MINLEN:36
```

### bio-read-qc-quality-reports
**用途**: Generate and interpret quality reports from FASTQ files using FastQC and MultiQC. Assess per-base quality, adapter content, GC bias, duplication levels, and overrepresented sequences. Use when perf...
```
Custom_Adapter_Name    ACGTACGTACGT
```

### bio-read-qc-umi-processing
**用途**: Extract, process, and deduplicate reads using Unique Molecular Identifiers (UMIs) with umi_tools. Use when library prep includes UMIs and accurate molecule counting is needed, such as in single-cel...
```
gene    cell    count
ENSG00000139618    ACGT    15
ENSG00000139618    TGCA    8
ENSG00000141510    ACGT    42
```
