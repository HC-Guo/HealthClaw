# gptomics 表观基因组学 SOP
> ChIP-seq、ATAC-seq、Hi-C、CLIP-seq、表观转录组、小 RNA
> 包含 36 个 OpenClaw skill 的压缩迁移。

---

### bio-atac-seq-atac-peak-calling
**用途**: Call accessible chromatin regions from ATAC-seq data using MACS3 with ATAC-specific parameters. Use when identifying open chromatin regions from aligned ATAC-seq BAM files, different from ChIP-seq ...
```
chr1  100  500  peak1  500  .  10.5  50.2  45.1  200
```

### bio-atac-seq-atac-qc
**用途**: Quality control metrics for ATAC-seq data including fragment size distribution, TSS enrichment, FRiP, and library complexity. Use when assessing ATAC-seq library quality before or after peak callin...
```
# Mitochondrial reads
mt_reads=$(samtools view -c sample.bam chrM)
total_reads=$(samtools view -c sample.bam)

mt_frac=$(echo "scale=4; $mt_reads / $total_reads" | bc)
echo "Mitochondrial fraction: $mt_frac"

# Ideal: <20%, concerning: >50%
```

### bio-atac-seq-differential-accessibility
**用途**: Find differentially accessible chromatin regions between conditions using DiffBind or DESeq2. Use when comparing chromatin accessibility between treatment groups, cell types, or developmental stage...
```
# Complex design with batch correction
samples$Batch <- factor(c('A', 'B', 'A', 'B'))

dba <- dba(sampleSheet=samples)
dba <- dba.count(dba)
dba <- dba.normalize(dba)

# Design formula approach
dba <- dba.contrast(dba, design='~Batch + Condition')
dba <- dba.analyze(dba)
```

### bio-atac-seq-footprinting
**用途**: Detect transcription factor binding sites through footprinting analysis in ATAC-seq data using TOBIAS. Use when identifying TF occupancy patterns within accessible regions, as TF binding protects D...
```
# RGT suite HINT-ATAC
rgt-hint footprinting \
    --atac-seq \
    --organism hg38 \
    --output-prefix sample \
    sample.bam peaks.bed
```

### bio-atac-seq-motif-deviation
**用途**: Analyze transcription factor motif accessibility variability using chromVAR. Use when identifying which TF motifs show variable accessibility across samples or conditions in ATAC-seq data.
```
plotVariability(variability, use_plotly = FALSE)
```

### bio-atac-seq-nucleosome-positioning
**用途**: Extract nucleosome positions from ATAC-seq data using NucleoATAC, ATACseqQC, and fragment analysis. Use when analyzing chromatin organization, identifying nucleosome-free regions at promoters, or c...
```
pip install nucleoatac
```

### bio-chipseq-differential-binding
**用途**: Differential binding analysis using DiffBind. Compare ChIP-seq peaks between conditions with statistical rigor. Requires replicate samples. Outputs differentially bound regions with fold changes an...
```
# Average signal profile
profiles <- dba.plotProfile(dba_obj)
```

### bio-chipseq-motif-analysis
**用途**: De novo motif discovery and known motif enrichment analysis using HOMER and MEME-ChIP. Identify transcription factor binding motifs in ChIP-seq, ATAC-seq, or other genomic peak data. Use when findi...
```
conda install -c bioconda meme
```

### bio-chipseq-peak-annotation
**用途**: Annotate ChIP-seq peaks to genomic features and genes using ChIPseeker. Assign peaks to promoters, exons, introns, and intergenic regions. Find nearest genes and calculate distance to TSS. Generate...
```
# Plot peak coverage around TSS
covplot(peaks, weightCol = 'V5')  # V5 is score column in narrowPeak
```

### bio-chipseq-peak-calling
**用途**: ChIP-seq peak calling using MACS3 (or MACS2). Call narrow peaks for transcription factors or broad peaks for histone modifications. Supports input control, fragment size modeling, and various outpu...
```
chr1  100  200  peak_1  100  .  5.2  10.5  8.3  50
```

### bio-chipseq-qc
**用途**: ChIP-seq quality control metrics including FRiP (Fraction of Reads in Peaks), cross-correlation analysis (NSC/RSC), library complexity, and IDR (Irreproducibility Discovery Rate) for replicate conc...
```
# Parse results
awk -F'\t' '{
    print "Fragment length:", $3
    print "NSC:", $9
    print "RSC:", $10
    print "Quality:", $11
}' chip_cc.txt
```

### bio-chipseq-super-enhancers
**用途**: Identifies super-enhancers from H3K27ac ChIP-seq data using ROSE and related tools. Use when studying cell identity genes, cancer-associated regulatory elements, or master transcription factor bind...
```
git clone https://github.com/stjude/ROSE.git
cd ROSE
# Requires samtools, R, bedtools
```

### bio-chipseq-visualization
**用途**: Visualize ChIP-seq data using deepTools, Gviz, and ChIPseeker. Create heatmaps, profile plots, and genome browser tracks. Visualize signal around peaks, TSS, or custom regions. Use when visualizing...
```
# Signal across gene bodies
computeMatrix scale-regions \
    -R genes.bed \
    -S sample1.bw sample2.bw \
    -b 3000 -a 3000 \              # Flanking regions
    -m 5000 \                       # Scaled body length
    -o matrix_scaled.gz
```

### bio-clip-seq-binding-site-annotation
**用途**: 
```
# Annotate to UTRs
bedtools intersect -a peaks.bed -b 3utr.bed -wa -wb > peaks_3utr.bed
```

### bio-clip-seq-clip-alignment
**用途**: 
```
# Index
samtools index aligned.bam

# Deduplicate with UMIs
umi_tools dedup \
    --stdin=aligned.bam \
    --stdout=deduped.bam
```

### bio-clip-seq-clip-motif-analysis
**用途**: 
```
meme-chip -oc output_dir \
    -dna \
    peaks.fa
```

### bio-clip-seq-clip-peak-calling
**用途**: 
```
# PAR-CLIP specific caller
peakachu adaptive \
    -c control.bam \
    -t treatment.bam \
    -r reference.fa \
    -o peakachu_peaks.gff
```

### bio-clip-seq-clip-preprocessing
**用途**: 
```
# Trim adapters after UMI extraction
cutadapt \
    -a AGATCGGAAGAGCACACGTCT \
    -A AGATCGGAAGAGCGTCGTGTAGGGAAAGAGTGT \
    -m 18 \
    -o trimmed_R1.fastq.gz \
    -p trimmed_R2.fastq.gz \
    R1_umi.fastq.gz R2_umi.fastq.gz
```

### bio-epitranscriptomics-m6a-differential
**用途**: 
```
library(ggplot2)

# Volcano plot
ggplot(diff_sites, aes(x = log2FoldChange, y = -log10(padj))) +
    geom_point(aes(color = padj < 0.05 & abs(log2FoldChange) > 1)) +
    geom_hline(yintercept = -log10(0.05), linetype = 'dashed') +
    geom_vline(xintercept = c(-1, 1), linetype = 'dashed')
```

### bio-epitranscriptomics-m6a-peak-calling
**用途**: 
```
# Filter by fold enrichment and q-value
# FC > 2, q < 0.05 typical thresholds
awk '$7 > 2 && $9 < 0.05' peaks.xls > filtered_peaks.bed
```

### bio-epitranscriptomics-m6anet-analysis
**用途**: 
```
import pandas as pd

results = pd.read_csv('m6anet_results/data.site_proba.csv')

# Filter high-confidence m6A sites
# probability > 0.9: High confidence threshold
m6a_sites = results[results['probability_modified'] > 0.9]
```

### bio-epitranscriptomics-merip-preprocessing
**用途**: 
```
# Index BAMs
for bam in *Aligned.sortedByCoord.out.bam; do
    samtools index $bam
done

# Check IP enrichment
# Good MeRIP: IP should have peaks, input should be uniform
samtools flagstat IP_rep1_Aligned.sortedByCoord.out.bam
```

### bio-epitranscriptomics-modification-visualization
**用途**: 
```
library(ComplexHeatmap)

# m6A signal around peaks
Heatmap(
    signal_matrix,
    name = 'm6A signal',
    cluster_rows = TRUE,
    show_row_names = FALSE
)
```

### bio-hi-c-analysis-compartment-analysis
**用途**: Detect A/B compartments from Hi-C data using cooltools and eigenvector decomposition. Identify active (A) and inactive (B) chromatin compartments from contact matrices. Use when identifying A/B com...
```
import cooler
import cooltools
import cooltools.lib.plotting
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import bioframe
```

### bio-hi-c-analysis-contact-pairs
**用途**: Process Hi-C read pairs using pairtools. Parse alignments, filter duplicates, classify pairs, and generate contact statistics from Hi-C sequencing data. Use when processing raw Hi-C read pairs.
```
# Sort pairs by position
pairtools sort \
    --nproc 8 \
    --output sorted.pairs.gz \
    parsed.pairs.gz
```

### bio-hi-c-analysis-hic-data-io
**用途**: Load, convert, and manipulate Hi-C contact matrices using cooler format. Read .cool/.mcool files, convert from .hic format, access matrix data, and export to different formats. Use when loading or ...
```
import cooler
import numpy as np
import pandas as pd
```

### bio-hi-c-analysis-hic-differential
**用途**: Compare Hi-C contact matrices between conditions to identify differential chromatin interactions. Compute log2 fold changes, statistical significance, and visualize differential contact maps. Use w...
```
import cooler
import cooltools
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
from scipy import stats
import bioframe
```

### bio-hi-c-analysis-hic-visualization
**用途**: Visualize Hi-C contact matrices, TADs, loops, and genomic features using matplotlib, cooltools, and HiCExplorer. Create triangle plots, virtual 4C, and multi-track figures. Use when visualizing con...
```
import cooler
import cooltools
import cooltools.lib.plotting
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import bioframe
```

### bio-hi-c-analysis-loop-calling
**用途**: Detect chromatin loops and point interactions from Hi-C data using cooltools, chromosight, and HiCCUPS-like methods. Identify CTCF-mediated loops and enhancer-promoter contacts. Use when detecting ...
```
import cooler
import cooltools
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import bioframe
```

### bio-hi-c-analysis-matrix-operations
**用途**: Balance, normalize, and transform Hi-C contact matrices using cooler and cooltools. Apply iterative correction (ICE), compute expected values, and generate observed/expected matrices. Use when norm...
```
import cooler
import cooltools
import numpy as np
import pandas as pd
```

### bio-hi-c-analysis-tad-detection
**用途**: Call topologically associating domains (TADs) from Hi-C data using insulation score, HiCExplorer, and other methods. Identify domain boundaries and hierarchical domain structure. Use when calling T...
```
import cooler
import cooltools
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import bioframe
```

### bio-small-rna-seq-differential-mirna
**用途**: 
```
# apeglm shrinkage for more accurate log2 fold changes
# Particularly important for low-count miRNAs
library(apeglm)

res_shrunk <- lfcShrink(
    dds,
    coef = 'condition_treated_vs_control',
    type = 'apeglm'
)
```

### bio-small-rna-seq-mirdeep2-analysis
**用途**: 
```
# Build bowtie index for miRDeep2 mapper
bowtie-build genome.fa genome_index
```

### bio-small-rna-seq-mirge3-analysis
**用途**: 
```
# Detect A-to-I editing
miRge3.0 annotate \
    -s sample.fastq.gz \
    -lib miRge3_libs \
    -on human \
    -db mirbase \
    --AtoI \
    -o output_dir

# Outputs editing sites and frequencies
```

### bio-small-rna-seq-smrna-preprocessing
**用途**: 
```
# Using seqkit
seqkit rmdup -s trimmed.fastq.gz -o collapsed.fasta

# Using fastx_toolkit (legacy)
fastx_collapser -i trimmed.fastq -o collapsed.fasta
```

### bio-small-rna-seq-target-prediction
**用途**: 
```
# Run miRanda for target prediction
miranda miRNA.fa UTRs.fa \
    -sc 140 \
    -en -20 \
    -out predictions.txt

# Options:
# -sc 140: Minimum alignment score (default 140)
# -en -20: Maximum free energy threshold (kcal/mol)
# Higher score and lower energy = stronger prediction
```
