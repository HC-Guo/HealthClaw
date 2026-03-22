# gptomics 文件格式与 I/O SOP
> FASTQ/BAM/VCF/BED 文件操作、格式转换、压缩、批量下载
> 包含 13 个 OpenClaw skill 的压缩迁移。

---

### bio-basecalling
**用途**: Convert raw Nanopore signal data (FAST5/POD5) to nucleotide sequences using Dorado basecaller. Covers model selection, GPU acceleration, modified base detection, and quality filtering. Use when pro...
```
dorado download --list
```

### bio-batch-downloads
**用途**: 
```
from Bio import Entrez
import time

Entrez.email = 'your.email@example.com'  # Required by NCBI
Entrez.api_key = 'your_api_key'          # Recommended for large downloads
```

### bio-batch-processing
**用途**: Process multiple sequence files in batch using Biopython. Use when working with many files, merging/splitting sequences, or automating file operations across directories.
```
from pathlib import Path
from Bio import SeqIO
```

### bio-bedgraph-handling
**用途**: 
```
bedtools genomecov -ibam sample.bam -bg -5 > sample.5prime.bedgraph
```

### bio-compressed-files
**用途**: Read and write compressed sequence files (gzip, bzip2, BGZF) using Biopython. Use when working with .gz or .bz2 sequence files. Use BGZF for indexable compressed files.
```
import gzip
import bz2
from Bio import SeqIO
from Bio import bgzf
```

### bio-duplicate-handling
**用途**: 
```
samtools markdup input.bam marked.bam
```

### bio-fastq-quality
**用途**: Work with FASTQ quality scores using Biopython. Use when analyzing read quality, filtering by quality, trimming low-quality bases, or generating quality reports.
```
from Bio import SeqIO
from Bio.Seq import Seq
```

### bio-format-conversion
**用途**: Convert between sequence file formats (FASTA, FASTQ, GenBank, EMBL) using Biopython Bio.SeqIO. Use when changing file formats or preparing data for different tools.
```
from Bio import SeqIO
```

### bio-paired-end-fastq
**用途**: Handle paired-end FASTQ files (R1/R2) using Biopython. Use when working with Illumina paired reads, synchronizing pairs, interleaving/deinterleaving, or filtering paired data.
```
from Bio import SeqIO
```

### bio-pileup-generation
**用途**: 
```
samtools mpileup -f reference.fa -q 20 input.bam
```

### bio-reference-operations
**用途**: 
```
samtools faidx reference.fa chr1
```

### bio-sam-bam-basics
**用途**: 
```
samtools view -H input.bam
```

### bio-sra-data
**用途**: 
```
# Basic stats
sra-stat --quick SRR12345678

# Detailed XML output
sra-stat --xml SRR12345678
```
