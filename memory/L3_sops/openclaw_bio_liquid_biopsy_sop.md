# gptomics 液体活检与 cfDNA SOP
> cfDNA 预处理、ctDNA 突变检测、液体活检管线、肿瘤分数估计
> 包含 6 个 OpenClaw skill 的压缩迁移。

---

### bio-cfdna-preprocessing
**用途**: Preprocesses cell-free DNA sequencing data including adapter trimming, alignment optimized for short fragments, and UMI-aware duplicate removal using fgbio. Applies cfDNA-specific quality threshold...
```
import pysam
import numpy as np
import matplotlib.pyplot as plt


def analyze_fragment_sizes(bam_path, max_size=500):
    '''Analyze cfDNA fragment size distribution.'''
    bam = pysam.AlignmentFile(bam_path, 'rb')
    sizes = []

    for read in bam.fetch():
        if read.is_proper_pair and not read.is_secondary and read.template_length > 0:
            if read.template_length <= max_size:
                sizes.append(read.template_length)

    bam.close()

    # cfDNA signature: peak at ~16
# ... (truncated)
```

### bio-ctdna-mutation-detection
**用途**: Detects somatic mutations in circulating tumor DNA using variant callers optimized for low allele fractions with UMI-based error suppression. Reliably detects mutations at VAF above 0.5 percent usi...
```
# VarDict is highly sensitive for low VAF
# Use on UMI-consensus BAM for best results

vardict-java \
    -G reference.fa \
    -f 0.005 \      # Min VAF 0.5%
    -N sample_id \
    -b sample.bam \
    -c 1 -S 2 -E 3 -g 4 \
    regions.bed | \
teststrandbias.R | \
var2vcf_valid.pl \
    -N sample_id \
    -E \
    -f 0.005 \
    > sample.vcf
```

### bio-fragment-analysis
**用途**: Analyzes cfDNA fragment size distributions and fragmentomics features using FinaleToolkit or Griffin. Extracts nucleosome positioning patterns, fragment ratios, and DELFI-style fragmentation profil...
```
import subprocess


def run_griffin(bam_path, sites_bed, output_dir):
    '''
    Run Griffin for nucleosome positioning analysis.
    Griffin 0.2.0+ required.
    '''
    # Griffin analyzes nucleosome accessibility around regulatory sites
    subprocess.run([
        'griffin',
        '--bam', bam_path,
        '--sites', sites_bed,  # TSS, CTCF, etc.
        '--output', output_dir,
        '--window', '2000',  # bp around site
        '--fragment_length', '120-180'
    ], check=True)
```

### bio-liquid-biopsy-pipeline
**用途**: 
```
# For deep targeted sequencing
# Use UMI-consensus BAM from Step 1

vardict-java \
    -G reference.fa \
    -f 0.005 \
    -N sample_id \
    -b consensus.bam \
    -c 1 -S 2 -E 3 -g 4 \
    panel.bed | \
teststrandbias.R | \
var2vcf_valid.pl \
    -N sample_id \
    -E \
    -f 0.005 \
    > sample.vcf
```

### bio-longitudinal-monitoring
**用途**: Tracks ctDNA dynamics over time for treatment response monitoring using serial liquid biopsy samples. Analyzes tumor fraction trends, mutation clearance kinetics, and defines molecular response cri...
```
def plot_ctdna_dynamics(patient_data, treatment_lines=None, output_file=None):
    '''
    Plot ctDNA dynamics over treatment.
    '''
    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot tumor fraction on log scale
    ax.semilogy(patient_data['timepoint'], patient_data['tumor_fraction'],
                'o-', linewidth=2, markersize=8)

    # Add treatment lines
    if treatment_lines:
        for time, label in treatment_lines:
            ax.axvline(x=time, color='gray', linestyle='--', a
# ... (truncated)
```

### bio-tumor-fraction-estimation
**用途**: Estimates circulating tumor DNA fraction from shallow whole-genome sequencing using ichorCNA. Detects copy number alterations via HMM segmentation and calculates ctDNA percentage. Requires 0.1-1x s...
```
library(ichorCNA)

# Step 1: Generate read counts in bins
# Run from command line or use HMMcopy
# readCounter --window 1000000 --quality 20 sample.bam > sample.wig

# Step 2: Run ichorCNA
runIchorCNA(
    WIG = 'sample.wig',
    gcWig = 'gc_hg38_1mb.wig',
    mapWig = 'mappability_hg38_1mb.wig',
    normalPanel = 'pon_median_1mb.rds',
    centromere = 'centromeres_hg38.txt',
    outDir = 'ichor_results/',
    id = 'sample_id',

    # Tumor fraction estimation parameters
    normal = c(0.5, 0.6,
# ... (truncated)
```
