# gptomics 生信工具套件 SOP
> 228 个细粒度生信模块：比对、QC、差异表达、通路、单细胞、表观、宏基因组、免疫、多组学、蛋白质组、结构、流行病学
> 包含 390 个 OpenClaw skill 的压缩迁移。

---

### bio-admet-prediction
**用途**: Predicts ADMET properties using ADMETlab 3.0 API or DeepChem models. Estimates bioavailability, CYP inhibition, hERG liability, and 119 toxicity endpoints with uncertainty quantification. Filters f...
```
import requests
import pandas as pd

def predict_admet_batch(smiles_list, api_url='https://admetlab3.scbdd.com/api/predict'):
    '''
    Predict ADMET properties using ADMETlab 3.0 API.

    Note: SwissADME has NO API - it is web-only.
    '''
    payload = {
        'smiles': smiles_list
    }

    response = requests.post(api_url, json=payload)
    response.raise_for_status()

    return pd.DataFrame(response.json())

# Example usage
# smiles = ['CCO', 'c1ccccc1O', 'CC(=O)Oc1ccccc1C(=O)O']
# 
# ... (truncated)
```

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

### bio-blast-searches
**用途**: 
```
from Bio.Blast import NCBIWWW, NCBIXML
from Bio import SeqIO
```

### bio-causal-genomics-colocalization-analysis
**用途**: Test whether two traits share a causal variant at a genomic locus using Bayesian colocalization with coloc. Computes posterior probabilities for shared vs distinct causal variants between GWAS and ...
```
# When only p-values are available, use MAF to approximate
gwas_pval <- list(
  pvalues = gwas_df$P,
  MAF = gwas_df$MAF,
  snp = gwas_df$SNP,
  position = gwas_df$POS,
  type = 'cc',
  s = 0.3,
  N = 50000
)

result <- coloc.abf(dataset1 = gwas_pval, dataset2 = eqtl_data)
```

### bio-causal-genomics-fine-mapping
**用途**: Identify likely causal variants within GWAS loci using SuSiE for sum of single effects regression and FINEMAP for shotgun stochastic search. Computes posterior inclusion probabilities and credible ...
```
# Read LD matrix into R
ld <- as.matrix(read.table('ld_matrix.ld'))

# Ensure positive semi-definite (numerical issues can violate this)
# Add small ridge to diagonal if needed
eigenvalues <- eigen(ld, only.values = TRUE)$values
if (any(eigenvalues < 0)) {
  ld <- ld + diag(abs(min(eigenvalues)) + 1e-6, nrow(ld))
}
```

### bio-causal-genomics-mediation-analysis
**用途**: Decompose genetic effects into direct and indirect paths through mediating variables using the mediation R package. Tests whether gene expression, methylation, or other molecular phenotypes mediate...
```
# For testing many potential mediators simultaneously (e.g., all CpG sites)
# install.packages('HIMA')
library(HIMA)

# X: treatment (genotype), M: high-dimensional mediators, Y: outcome
# HIMA uses penalized regression to select significant mediators

result <- hima(
  X = dat$genotype,
  Y = dat$disease,
  M = as.matrix(dat[, mediator_cols]),
  COV.XM = as.matrix(dat[, covariate_cols]),
  Y.family = 'binomial',
  M.family = 'gaussian',
  penalty = 'MCP'    # Minimax concave penalty (default)
)
# ... (truncated)
```

### bio-causal-genomics-mendelian-randomization
**用途**: Estimate causal effects between exposures and outcomes using genetic variants as instrumental variables with TwoSampleMR. Implements IVW, MR-Egger, weighted median, and MR-PRESSO methods for robust...
```
library(TwoSampleMR)

# Scatter plot: SNP-exposure vs SNP-outcome effects with method slopes
mr_scatter_plot(results, dat)

# Forest plot: Individual SNP and combined estimates
mr_forest_plot(single)

# Leave-one-out plot
mr_leaveoneout_plot(loo)

# Funnel plot: Precision vs causal estimate (asymmetry = pleiotropy)
mr_funnel_plot(single)
```

### bio-causal-genomics-pleiotropy-detection
**用途**: Detect and correct for horizontal pleiotropy in Mendelian randomization analyses using MR-PRESSO for outlier removal, MR-Egger regression for directional pleiotropy, and Steiger filtering for varia...
```
library(TwoSampleMR)

# Steiger test: Verify each instrument explains more variance in
# the exposure than the outcome. Instruments failing this test
# may act through a reverse causal pathway.

steiger <- steiger_filtering(dat)

# Keep only correctly oriented instruments
dat_steiger <- steiger[steiger$steiger_dir == TRUE, ]
cat('Instruments passing Steiger filter:', nrow(dat_steiger), 'of', nrow(steiger), '\n')

# Re-run MR with filtered instruments
results_steiger <- mr(dat_steiger)
print(resu
# ... (truncated)
```

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

### bio-clinical-databases-clinvar-lookup
**用途**: Query ClinVar for variant pathogenicity classifications, review status, and disease associations via REST API or local VCF. Use when determining clinical significance of variants for diagnostic or ...
```
# Annotate VCF with ClinVar
bcftools annotate \
    -a clinvar.vcf.gz \
    -c INFO/CLNSIG,INFO/CLNREVSTAT,INFO/CLNDN \
    input.vcf.gz \
    -o annotated.vcf.gz
```

### bio-clinical-databases-dbsnp-queries
**用途**: Query dbSNP for rsID lookups, variant annotations, and cross-references to other databases. Use when mapping between rsIDs and genomic coordinates or retrieving basic variant information.
```
import myvariant

mv = myvariant.MyVariantInfo()

def get_rsid_info(rsid):
    '''Get variant info by rsID'''
    result = mv.getvariant(rsid, fields=['dbsnp', 'clinvar', 'gnomad_exome'])
    return result

result = get_rsid_info('rs121913527')
```

### bio-clinical-databases-gnomad-frequencies
**用途**: Query gnomAD for population allele frequencies to assess variant rarity. Use when filtering variants by population frequency for rare disease analysis or determining if a variant is common in the g...
```
# Using Hail for gnomAD v4
import hail as hl

ht = hl.read_table('gs://gcp-public-data--gnomad/release/4.0/ht/exomes/gnomad.exomes.v4.0.sites.ht')

# Filter to rare variants
rare_ht = ht.filter(ht.freq[0].AF < 0.01)
```

### bio-clinical-databases-hla-typing
**用途**: Call HLA alleles from NGS data using OptiType, HLA-HD, or arcasHLA for immunogenomics applications. Use when determining HLA genotype for transplant matching, neoantigen prediction, or pharmacogeno...
```
# Merge multiple samples
arcasHLA merge output_dir/*.genotype.json -o merged_hla.tsv
```

### bio-clinical-databases-myvariant-queries
**用途**: Query myvariant.info API for aggregated variant annotations from multiple databases (ClinVar, gnomAD, dbSNP, COSMIC, etc.) in a single request. Use when annotating variants with clinical and popula...
```
import myvariant
```

### bio-clinical-databases-pharmacogenomics
**用途**: Query PharmGKB and CPIC for drug-gene interactions, pharmacogenomic annotations, and dosing guidelines. Use when predicting drug response from genetic variants or implementing clinical pharmacogeno...
```
def get_drug_annotations(drug_name):
    '''Get pharmacogenomic annotations for a drug'''
    url = 'https://api.pharmgkb.org/v1/data/clinicalAnnotation'
    params = {'view': 'base', 'chemicals.name': drug_name}
    response = requests.get(url, params=params)
    return response.json()['data']

warfarin_annotations = get_drug_annotations('warfarin')
```

### bio-clinical-databases-polygenic-risk
**用途**: Calculate polygenic risk scores using PRSice-2, LDpred2, or PRS-CS from GWAS summary statistics. Use when predicting disease risk from genome-wide genetic variants.
```
SNP          CHR  BP        A1  A2  BETA    SE      P
rs12345      1    10000     A   G   0.05    0.01    1e-8
rs67890      1    20000     T   C   -0.03   0.02    0.001
```

### bio-clinical-databases-somatic-signatures
**用途**: Extract and analyze mutational signatures from somatic variants using SigProfiler or MutationalPatterns to characterize mutagenic processes. Use when identifying DNA damage mechanisms or etiology i...
```
from SigProfilerAssignment import Analyzer as Analyze

# Fit to known COSMIC signatures
Analyze.cosmic_fit(
    samples='my_project/output/SBS/my_project.SBS96.all',
    output='assignment_output',
    input_type='matrix',
    genome_build='GRCh38',
    signature_database='SBS_GRCh38_GRCh38'
)
```

### bio-clinical-databases-tumor-mutational-burden
**用途**: Calculate tumor mutational burden from panel or WES data with proper normalization and clinical thresholds. Use when assessing immunotherapy eligibility or characterizing tumor immunogenicity.
```
# Common panel sizes (in megabases)
# Check your specific panel's capture region size
PANEL_SIZES_MB = {
    'FoundationOne CDx': 0.8,
    'MSK-IMPACT': 1.14,
    'TruSight Oncology 500': 1.94,
    'Oncomine Comprehensive': 1.5,
    'WES (exome)': 30.0,  # Approximate coding region
    'WGS': 3000.0,        # Approximate
}

def calculate_tmb_panel(vcf_path, panel_name):
    '''Calculate TMB for known panel'''
    if panel_name not in PANEL_SIZES_MB:
        raise ValueError(f'Unknown panel: {pan
# ... (truncated)
```

### bio-clinical-databases-variant-prioritization
**用途**: Filter and prioritize variants by pathogenicity, population frequency, and clinical evidence for rare disease analysis. Use when identifying candidate disease-causing variants from exome or genome ...
```
def assign_tiers(df):
    '''Assign clinical interpretation tiers

    Tier 1: Strong pathogenic evidence
    Tier 2: Potential pathogenic
    Tier 3: Uncertain significance
    Tier 4: Likely benign
    '''
    def get_tier(row):
        if row['clinvar_pathogenic'] and row['is_rare']:
            return 1
        elif row['is_rare'] and (row['cadd_deleterious'] or row['revel_pathogenic']):
            return 2
        elif row['is_rare']:
            return 3
        else:
            return 4
# ... (truncated)
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

### bio-codon-usage
**用途**: 
```
def find_rare_codons(seq, threshold=0.1):
    freq = codon_frequencies(seq)
    return {codon: f for codon, f in freq.items() if f < threshold}
```

### bio-comparative-genomics-ancestral-reconstruction
**用途**: 
```
def design_asr_construct(ancestral_seq, extant_reference, ambiguous_sites):
    '''Design constructs for ancestral protein resurrection

    Strategy:
    1. Use most probable state at each position
    2. Create alternative constructs at ambiguous sites
    3. Consider codon optimization for expression host

    Validation:
    - Test activity of resurrected proteins
    - Compare to extant proteins
    - Test alternative constructs at ambiguous positions
    '''
    constructs = [{'name': 'ASR
# ... (truncated)
```

### bio-comparative-genomics-hgt-detection
**用途**: 
```
def detect_phylogenetic_incongruence(gene_tree, species_tree):
    '''Detect HGT via phylogenetic incongruence

    Compare gene tree topology to species tree
    Genes with conflicting placement may be HGT

    Methods:
    - AU test: Approximately Unbiased test
    - SH test: Shimodaira-Hasegawa test
    - Bootstrap: Compare bootstrap support
    '''
    from Bio import Phylo
    from io import StringIO

    # Load trees
    g_tree = Phylo.read(StringIO(gene_tree), 'newick')
    s_tree = Phylo
# ... (truncated)
```

### bio-comparative-genomics-ortholog-inference
**用途**: 
```
def transfer_annotation(query_gene, orthologs, annotation_db):
    '''Transfer functional annotation via orthology

    Annotation transfer guidelines:
    - Single-copy orthologs: High confidence transfer
    - Co-orthologs: Transfer to all, note potential subfunctionalization
    - In-paralogs: Transfer with caution (may have diverged function)

    Evidence codes:
    - IEA: Inferred from Electronic Annotation
    - ISO: Inferred from Sequence Orthology
    '''
    annotations = []

    for s
# ... (truncated)
```

### bio-comparative-genomics-positive-selection
**用途**: 
```
'''
dN/dS (omega, ω) interpretation:
- ω < 1: Purifying (negative) selection - deleterious mutations removed
- ω = 1: Neutral evolution - no selective pressure
- ω > 1: Positive (diversifying) selection - advantageous mutations favored

Most genes: ω << 1 (strong purifying selection)
Immune genes, reproduction: Often show ω > 1 at specific sites
'''
```

### bio-comparative-genomics-synteny-analysis
**用途**: 
```
def create_synteny_plot(blocks_file, layout_file, output_file):
    '''Create synteny dot plot with JCVI

    JCVI (python-jcvi) provides publication-ready figures
    '''
    from jcvi.graphics.dotplot import dotplot
    from jcvi.graphics.karyotype import karyotype

    # Dotplot shows collinear blocks as diagonal lines
    # Good for detecting WGD (parallel diagonals)
    dotplot_cmd = f'python -m jcvi.graphics.dotplot {blocks_file}'
    subprocess.run(dotplot_cmd, shell=True)

    # Karyotyp
# ... (truncated)
```

### bio-compressed-files
**用途**: Read and write compressed sequence files (gzip, bzip2, BGZF) using Biopython. Use when working with .gz or .bz2 sequence files. Use BGZF for indexable compressed files.
```
import gzip
import bz2
from Bio import SeqIO
from Bio import bgzf
```

### bio-consensus-sequences
**用途**: Generate consensus FASTA sequences by applying VCF variants to a reference using bcftools consensus. Use when creating sample-specific reference sequences or reconstructing haplotypes.
```
# Number of differences
bcftools view -H input.vcf.gz | wc -l
```

### bio-copy-number-cnv-annotation
**用途**: Annotate CNVs with genes, pathways, and clinical significance. Use when interpreting CNV calls or identifying affected genes from copy number analysis.
```
# Annotate during analysis
cnvkit.py batch tumor.bam --normal normal.bam \
    --targets targets.bed \
    --annotate refFlat.txt \
    --fasta reference.fa \
    -o results/

# Genes are included in output CNS file
```

### bio-copy-number-cnv-visualization
**用途**: Visualize copy number profiles, segments, and compare across samples. Create publication-quality plots of CNV data from CNVkit, GATK, or other callers. Use when creating genome-wide CNV plots, samp...
```
# Scatter plot with segments
cnvkit.py scatter sample.cnr -s sample.cns -o scatter.png

# Scatter for specific chromosome
cnvkit.py scatter sample.cnr -s sample.cns -c chr17 -o chr17_scatter.png

# Ideogram diagram
cnvkit.py diagram sample.cnr -s sample.cns -o diagram.pdf

# Heatmap across samples
cnvkit.py heatmap *.cns -o cohort_heatmap.pdf

# Heatmap for specific region
cnvkit.py heatmap *.cns -c chr17:7500000-7700000 -o tp53_region.pdf
```

### bio-copy-number-cnvkit-analysis
**用途**: Detect copy number variants from targeted/exome sequencing using CNVkit. Supports tumor-normal pairs, tumor-only, and germline CNV calling. Use when detecting CNVs from WES or targeted panel sequen...
```
# For whole genome sequencing (no targets file)
cnvkit.py batch tumor.bam \
    --normal normal.bam \
    --fasta reference.fa \
    --method wgs \
    --output-dir results/
```

### bio-copy-number-gatk-cnv
**用途**: Call copy number variants using GATK best practices workflow. Supports both somatic (tumor-normal) and germline CNV detection from WGS or WES data. Use when following GATK best practices or integra...
```
gatk CallCopyRatioSegments \
    -I results/tumor.cr.seg \
    -O results/tumor.called.seg
```

### bio-crispr-screens-base-editing-analysis
**用途**: Analyzes base editing and prime editing outcomes including editing efficiency, bystander edits, and indel frequencies. Use when quantifying CRISPR base editor results, comparing ABE vs CBE efficien...
```
# C->T conversion (or G->A on opposite strand)
CRISPResso --fastq_r1 reads.fq.gz \
    --amplicon_seq $AMPLICON \
    --guide_seq $GUIDE \
    --base_editor_output \
    --conversion_nuc_from C \
    --conversion_nuc_to T
```

### bio-crispr-screens-batch-correction
**用途**: Batch effect correction for CRISPR screens. Covers normalization across batches, technical replicate handling, and batch-aware analysis. Use when combining screens from multiple batches or correcti...
```
def quantile_normalize(counts_df, guide_cols=None):
    '''Quantile normalization across samples.'''
    if guide_cols is None:
        guide_cols = [c for c in counts_df.columns if c.startswith('sample_')]

    data = counts_df[guide_cols].values.copy()

    sorted_data = np.sort(data, axis=0)
    mean_values = sorted_data.mean(axis=1)

    ranks = np.argsort(np.argsort(data, axis=0), axis=0)
    normalized = mean_values[ranks]

    result = counts_df.copy()
    result[guide_cols] = normalized

# ... (truncated)
```

### bio-crispr-screens-crispresso-editing
**用途**: CRISPResso2 for analyzing CRISPR gene editing outcomes. Quantifies indels, HDR efficiency, and generates comprehensive editing reports. Use when analyzing amplicon sequencing data from CRISPR editi...
```
# Analyze off-target editing from WGS
CRISPRessoWGS \
    --bam aligned.bam \
    --reference genome.fa \
    --regions_file targets.bed \
    --output_folder wgs_output
```

### bio-crispr-screens-hit-calling
**用途**: Statistical methods for calling hits in CRISPR screens. Covers MAGeCK, BAGEL2, drugZ, and custom approaches for identifying essential and resistance genes. Use when identifying significant genes fr...
```
# DrugZ for drug screens (synergy/resistance)
drugz.py \
    -i counts.txt \
    -o drugz_output.txt \
    -c Control1,Control2 \
    -x Treatment1,Treatment2 \
    --remove-genes Control_genes.txt

# Output columns:
# Gene, sumZ (combined z-score), normZ, pval_synth (synthetic lethal), pval_supp (suppressor)
```

### bio-crispr-screens-jacks-analysis
**用途**: JACKS (Joint Analysis of CRISPR/Cas9 Knockout Screens) for modeling sgRNA efficacy and gene essentiality. Use when analyzing multiple CRISPR screens simultaneously or when accounting for variable s...
```
# guidemap.txt
sgRNA1	GENE_A
sgRNA2	GENE_A
sgRNA3	GENE_B
sgRNA4	GENE_B
...
```

### bio-crispr-screens-library-design
**用途**: CRISPR library design for genetic screens. Covers sgRNA selection, library composition, control design, and oligo ordering. Use when designing custom sgRNA libraries for knockout, activation, or in...
```
# Cas12a example (TTTV PAM, 23nt guide)
def design_cas12a_guides(gene_sequence, n_guides=4):
    pam_pattern = 'TTT[ACG]'  # TTTV
    guide_length = 23

    for match in re.finditer(f'({pam_pattern})([ACGT]{{{guide_length}}})', gene_sequence):
        pam = match.group(1)
        guide = match.group(2)
        # Cas12a cuts downstream of guide
        # ...
```

### bio-crispr-screens-mageck-analysis
**用途**: MAGeCK (Model-based Analysis of Genome-wide CRISPR-Cas9 Knockout) for pooled CRISPR screen analysis. Covers count normalization, gene ranking, and pathway analysis. Use when identifying essential g...
```
# library.csv (tab-separated)
sgRNA_ID	Gene	Sequence
BRCA1_1	BRCA1	ATGGATTTATCTGCTCTTCG
BRCA1_2	BRCA1	CAGCAGATACTTGATGCATC
TP53_1	TP53	CCATTGTTCAATATCGTCCG
...
```

### bio-crispr-screens-screen-qc
**用途**: Quality control for pooled CRISPR screens. Covers library representation, read distribution, replicate correlation, and essential gene recovery. Use when assessing screen quality before hit calling...
```
# sgRNAs per gene
sgrnas_per_gene = genes.value_counts()
print(f'\nsgRNAs per gene: mean={sgrnas_per_gene.mean():.1f}, min={sgrnas_per_gene.min()}, max={sgrnas_per_gene.max()}')

# Check for genes with few sgRNAs
few_sgrnas = sgrnas_per_gene[sgrnas_per_gene < 3]
if len(few_sgrnas) > 0:
    print(f'WARNING: {len(few_sgrnas)} genes have <3 sgRNAs')
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

### bio-data-visualization-circos-plots
**用途**: 
```
pip install pyCircos
```

### bio-data-visualization-color-palettes
**用途**: 
```
import seaborn as sns

sns.heatmap(data, cmap='RdBu_r', center=0, vmin=-2, vmax=2)
```

### bio-data-visualization-genome-browser-tracks
**用途**: 
```
[hic_matrix]
file = matrix.cool
title = Hi-C
height = 10
depth = 1000000
min_value = 0
max_value = 100
transform = log1p
colormap = RdYlBu_r
show_masked_bins = false
```

### bio-data-visualization-genome-tracks
**用途**: 
```
# pyGenomeTracks with BED regions
pyGenomeTracks --tracks tracks.ini --BED regions.bed \
    --outFileName multi_region.pdf --dpi 150
```

### bio-data-visualization-ggplot2-fundamentals
**用途**: 
```
library(ggplot2)

# Grammar of graphics: data + aesthetics + geometry
ggplot(data, aes(x = var1, y = var2)) +
    geom_point()
```

### bio-data-visualization-heatmaps-clustering
**用途**: 
```
# pheatmap to file
pheatmap(mat, filename = 'heatmap.pdf', width = 8, height = 10)

# ComplexHeatmap to file
pdf('heatmap.pdf', width = 8, height = 10)
draw(ht)
dev.off()
```

### bio-data-visualization-interactive-visualization
**用途**: 
```
# plotly - works automatically in Jupyter
fig.show()

# bokeh
from bokeh.io import output_notebook, show
output_notebook()
show(p)
```

### bio-data-visualization-multipanel-figures
**用途**: 
```
# Python
fig.savefig('figure1.pdf', bbox_inches='tight')
fig.savefig('figure1.png', dpi=300, bbox_inches='tight')
```

### bio-data-visualization-specialized-omics-plots
**用途**: 
```
library(survival)
library(survminer)

fit <- survfit(Surv(time, status) ~ group, data = df)
ggsurvplot(fit, data = df, risk.table = TRUE, pval = TRUE,
           palette = c('#4DBBD5', '#E64B35'),
           legend.labs = c('Low', 'High'))
```

### bio-data-visualization-upset-plots
**用途**: 
```
# Python
fig = plt.figure(figsize=(10, 6))
upset.plot(fig=fig)
plt.savefig('upset.pdf', bbox_inches='tight')
plt.savefig('upset.png', dpi=300, bbox_inches='tight')
```

### bio-data-visualization-volcano-customization
**用途**: 
```
# Python
plt.savefig('volcano.pdf', bbox_inches='tight')
plt.savefig('volcano.png', dpi=300, bbox_inches='tight')
```

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

### bio-de-visualization
**用途**: Visualize differential expression results using DESeq2/edgeR built-in functions. Covers plotMA, plotDispEsts, plotCounts, plotBCV, sample distance heatmaps, and p-value histograms. Use when visuali...
```
plotDispEsts(dds, main = 'Dispersion Estimates')
```

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

### bio-differential-splicing
**用途**: Detects differential alternative splicing between conditions using rMATS-turbo (BAM-based) or SUPPA2 diffSplice (TPM-based). Reports events with FDR-corrected significance and delta PSI effect size...
```
# Prioritize by effect size and significance
significant['score'] = -np.log10(significant['FDR']) * significant['IncLevelDifference'].abs()
top_events = significant.nlargest(50, 'score')

# Annotate with gene function
# Consider protein domain disruption, NMD sensitivity
```

### bio-duplicate-handling
**用途**: 
```
samtools markdup input.bam marked.bam
```

### bio-entrez-fetch
**用途**: 
```
from Bio import Entrez

Entrez.email = 'your.email@example.com'  # Required by NCBI
Entrez.api_key = 'your_api_key'          # Optional, raises rate limit 3->10 req/sec
```

### bio-entrez-link
**用途**: 
```
from Bio import Entrez

Entrez.email = 'your.email@example.com'  # Required by NCBI
Entrez.api_key = 'your_api_key'          # Optional, raises rate limit
```

### bio-entrez-search
**用途**: 
```
term = 'immun*'                         # Wildcard
term = '"breast cancer"[title]'         # Exact phrase
```

### bio-epidemiological-genomics-amr-surveillance
**用途**: Detect and track antimicrobial resistance genes using AMRFinderPlus and ResFinder with epidemiological context. Monitor resistance trends and identify emerging resistance patterns. Use when screeni...
```
# ResFinder for acquired resistance genes
# Web: https://cge.cbs.dtu.dk/services/ResFinder/

# Command line via KMA
kma -i reads_1.fq reads_2.fq -o output -t_db resfinder_db -1t1

# Or use CGE Docker
docker run --rm -v $(pwd):/data cgetools/resfinder \
    -i /data/genome.fasta -o /data/results -db_res /db/resfinder_db
```

### bio-epidemiological-genomics-pathogen-typing
**用途**: Perform multi-locus sequence typing (MLST), core genome MLST, and SNP-based strain typing for bacterial isolate characterization using mlst and chewBBACA. Use when identifying strain types, trackin...
```
# chewBBACA for cgMLST
pip install chewbbaca

# Download or create schema
chewBBACA.py DownloadSchema -sp "Salmonella enterica" -o schema_dir

# Run cgMLST
chewBBACA.py AlleleCall -i genomes/ -g schema_dir -o results/

# Analyze results
chewBBACA.py ExtractCgMLST -i results/results_alleles.tsv \
    -o cgmlst_results.tsv --threshold 0.95
```

### bio-epidemiological-genomics-phylodynamics
**用途**: Construct time-scaled phylogenies and infer evolutionary dynamics using TreeTime and BEAST2 for outbreak analysis. Estimate divergence times, molecular clock rates, and ancestral states. Use when d...
```
def extract_skyline(treetime_results_dir):
    '''Extract coalescent skyline from TreeTime output

    Skyline shows effective population size over time.
    Useful for:
    - Detecting population expansions (outbreak growth)
    - Identifying bottlenecks
    - Estimating R0 from growth rate
    '''
    import json

    with open(f'{treetime_results_dir}/skyline.json') as f:
        skyline = json.load(f)

    times = skyline['times']
    Ne = skyline['Ne']  # Effective population size

    retu
# ... (truncated)
```

### bio-epidemiological-genomics-transmission-inference
**用途**: Infer pathogen transmission networks and identify likely transmission pairs using TransPhylo and outbreak reconstruction algorithms. Estimate who-infected-whom from genomic and epidemiological data...
```
# Analyze TransPhylo output

# Get median transmission tree
med_tree <- medTTree(res)

# Plot transmission tree
plot(med_tree)

# Get R0 estimate
r0_samples <- res$record[, 'off.r']
cat('R0 estimate:', median(r0_samples), '\n')
cat('95% CI:', quantile(r0_samples, c(0.025, 0.975)), '\n')

# Identify superspreaders
# Count number infected by each case
infections_per_case <- table(med_tree$ttree[, 'infector'])
superspreaders <- names(infections_per_case[infections_per_case > 3])
```

### bio-epidemiological-genomics-variant-surveillance
**用途**: Assign pathogen lineages and track variants using Nextclade and pangolin for viral surveillance. Monitor variant prevalence and identify emerging variants of concern. Use when classifying viral seq...
```
# Install pangolin
pip install pangolin

# Update lineage definitions
pangolin --update

# Run lineage assignment
pangolin sequences.fasta -o pangolin_results.csv

# With specific version
pangolin sequences.fasta --analysis-mode accurate -o results.csv
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

### bio-experimental-design-batch-design
**用途**: 
```
# BAD: Confounded design
# Batch 1: All treated samples
# Batch 2: All control samples
# -> Cannot separate batch from treatment

# GOOD: Balanced design
# Batch 1: 3 treated, 3 control
# Batch 2: 3 treated, 3 control
# -> Batch effect can be estimated and removed
```

### bio-experimental-design-multiple-testing
**用途**: 
```
# Controls false discovery rate
p_adj <- p.adjust(pvalues, method = 'BH')
# Most common for genomics
# FDR 0.05 = expect 5% of significant results to be false
```

### bio-experimental-design-power-analysis
**用途**: 
```
library(ssizeRNA)

# For differential accessibility
size.zhao(m = 10000, m1 = 500, fc = 2, fdr = 0.05, power = 0.8,
          mu = 10, disp = 0.1)
```

### bio-experimental-design-sample-size
**用途**: 
```
library(powsimR)

# Estimate for scRNA-seq
# Accounts for dropout and cell-to-cell variability
params <- estimateParam(pilot_sce)
power <- simulateDE(params, n1 = 100, n2 = 100,
                    p.DE = 0.1, pLFC = 1)
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

### bio-fastq-quality
**用途**: Work with FASTQ quality scores using Biopython. Use when analyzing read quality, filtering by quality, trimming low-quality bases, or generating quality reports.
```
from Bio import SeqIO
from Bio.Seq import Seq
```

### bio-filter-sequences
**用途**: Filter and select sequences by criteria (length, ID, GC content, patterns) using Biopython. Use when subsetting sequences, removing unwanted records, or selecting by specific criteria.
```
from Bio import SeqIO
from Bio.SeqUtils import gc_fraction
```

### bio-flow-cytometry-bead-normalization
**用途**: Bead-based normalization for CyTOF and high-parameter flow cytometry. Covers EQ bead normalization, signal drift correction, and batch normalization. Use when correcting instrument drift in CyTOF o...
```
# Save normalized FCS files
write.FCS(ff_clean, 'normalized_sample.fcs')

# For CATALYST object
# saveRDS(sce, 'normalized_sce.rds')
```

### bio-flow-cytometry-clustering-phenotyping
**用途**: Unsupervised clustering and cell type identification for flow/mass cytometry. Covers FlowSOM, Phenograph, and CATALYST workflows. Use when discovering cell populations in high-dimensional cytometry...
```
# UMAP
sce <- runDR(sce, dr = 'UMAP', features = 'type')

# tSNE
sce <- runDR(sce, dr = 'TSNE', features = 'type')

# Plot
plotDR(sce, 'UMAP', color_by = 'meta20')
```

### bio-flow-cytometry-compensation-transformation
**用途**: Spillover compensation and data transformation for flow cytometry. Covers compensation matrix calculation, application, and biexponential/arcsinh transforms. Use when correcting spectral overlap be...
```
# Create compensation object
comp <- compensation(comp_matrix)

# Apply to flowFrame
fcs_comp <- compensate(fcs, comp)

# Apply to flowSet
fs_comp <- compensate(fs, comp)
```

### bio-flow-cytometry-cytometry-qc
**用途**: Comprehensive quality control for flow cytometry and CyTOF data. Covers flow rate stability, signal drift, margin events, dead cell exclusion, and batch QC. Use when assessing acquisition quality o...
```
library(flowAI)
library(flowCore)

# Load FCS file
ff <- read.FCS('sample.fcs')

# Run automated QC
# Checks: flow rate, signal stability, dynamic range
qc_result <- flow_auto_qc(
    ff,
    folder_results = 'qc_output/',
    fcs_QC = TRUE,       # Export QC'd FCS
    html_report = TRUE,  # Generate HTML report
    mini_report = TRUE   # Also make summary
)

# Get cleaned data
ff_clean <- qc_result$fcs

# QC metrics
cat('Original events:', nrow(ff), '\n')
cat('After QC:', nrow(ff_clean), '\n')

# ... (truncated)
```

### bio-flow-cytometry-differential-analysis
**用途**: Differential abundance and state analysis for cytometry data. Compare cell populations between conditions using statistical methods. Use when testing for significant changes in cell frequencies or ...
```
# DA results heatmap
plotDiffHeatmap(sce, res_DA, all = TRUE, fdr = 0.05)

# DS results heatmap
plotDiffHeatmap(sce, res_DS, all = TRUE, fdr = 0.05)

# Abundance by condition
plotAbundances(sce, k = 'meta20', by = 'cluster_id', group_by = 'condition')
```

### bio-flow-cytometry-doublet-detection
**用途**: Detect and remove doublets from flow and mass cytometry data. Covers FSC/SSC gating and computational doublet detection methods. Use when filtering out cell aggregates before clustering or quantita...
```
# For cell types where FSC doesn't discriminate well,
# use SSC-A vs SSC-H additionally

ssc_singlet_gate <- rectangleGate(
    filterId = 'ssc_singlets',
    'SSC-A' = c(10000, 200000),
    'SSC-H' = c(10000, 200000)
)

# Combine FSC and SSC gates
combined_gate <- singlet_gate & ssc_singlet_gate
singlets <- Subset(fs, combined_gate)
```

### bio-flow-cytometry-fcs-handling
**用途**: Read and manipulate Flow Cytometry Standard (FCS) files. Covers loading data, accessing parameters, and basic data exploration. Use when loading and inspecting flow or mass cytometry data before pr...
```
# Write single file
write.FCS(fcs, 'output.fcs')

# Write flowSet
write.flowSet(fs, outdir = 'output_dir')
```

### bio-flow-cytometry-gating-analysis
**用途**: Manual and automated gating for defining cell populations in flow cytometry. Covers rectangular, polygon, and data-driven gates. Use when identifying cell populations through hierarchical gating st...
```
# Save GatingSet
save_gs(gs, 'gating_set')

# Export to FlowJo workspace
library(CytoML)
gatingset_to_flowjo(gs, 'analysis.wsp')
```

### bio-format-conversion
**用途**: Convert between sequence file formats (FASTA, FASTQ, GenBank, EMBL) using Biopython Bio.SeqIO. Use when changing file formats or preparing data for different tools.
```
from Bio import SeqIO
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

### bio-gatk-variant-calling
**用途**: Variant calling with GATK HaplotypeCaller following best practices. Covers germline SNP/indel calling, GVCF workflow for cohorts, joint genotyping, and variant quality score recalibration (VQSR). U...
```
gatk HaplotypeCaller \
    -R reference.fa \
    -I sample.bam \
    -O sample.vcf.gz
```

### bio-genome-assembly-assembly-polishing
**用途**: 
```
conda install -c bioconda pilon
```

### bio-genome-assembly-assembly-qc
**用途**: 
```
busco --list-datasets
```

### bio-genome-assembly-contamination-detection
**用途**: 
```
# When genomes may include novel taxa
gtdbtk de_novo_wf --genome_dir genomes/ --out_dir gtdbtk_denovo \
    --bacteria --extension fa --cpus 16
```

### bio-genome-assembly-hifi-assembly
**用途**: 
```
# Combine HiFi accuracy with ONT length
hifiasm -o hybrid_asm -t 32 \
    --ul ont_ultralong.fastq.gz \
    hifi_reads.fastq.gz

# UL reads help span complex repeats
```

### bio-genome-assembly-long-read-assembly
**用途**: 
```
conda install -c bioconda flye
```

### bio-genome-assembly-metagenome-assembly
**用途**: 
```
# Flye marks circular contigs in assembly_info.txt
grep "Y" flye_meta/assembly_info.txt | cut -f1 > circular_contigs.txt

# Extract circular contigs
seqkit grep -f circular_contigs.txt assembly.fasta > circular_genomes.fasta
```

### bio-genome-assembly-scaffolding
**用途**: 
```
# Load .hic file in Juicebox Assembly Tools (JBAT)
# Perform manual corrections:
# - Break misjoins
# - Order/orient scaffolds
# - Merge scaffolds

# Export corrected assembly
# File -> Export Assembly -> FASTA
```

### bio-genome-assembly-short-read-assembly
**用途**: 
```
>NODE_1_length_500000_cov_50.5
```

### bio-genome-engineering-base-editing-design
**用途**: Design guides for cytosine and adenine base editing using editing window optimization and BE-Hive outcome prediction. Select optimal positions for C-to-T or A-to-G conversions without double-strand...
```
Cytosine Base Editors (CBE):
- Convert C to T (or G to A on opposite strand)
- Examples: BE3, BE4, BE4max, AncBE4max
- Editing window: Positions 4-8 (PAM-distal numbering)

Adenine Base Editors (ABE):
- Convert A to G (or T to C on opposite strand)
- Examples: ABE7.10, ABE8e, ABE8.20
- Editing window: Positions 4-7 (narrower than CBE)

Position numbering:
Position 1 = PAM-proximal (next to NGG)
Position 20 = PAM-distal (5' end of spacer)
Editing window is typically positions 4-8 from PAM-distal 
# ... (truncated)
```

### bio-genome-engineering-grna-design
**用途**: Design guide RNAs for CRISPR-Cas9/Cas12a experiments using CRISPRscan and local scoring algorithms. Score guides for on-target activity using Rule Set 2 and Azimuth models. Use when designing sgRNA...
```
# CRISPRscan uses a different model optimized for zebrafish
# but works well across species for Cas9

def crisprscan_score(guide_35mer):
    '''Score using CRISPRscan model

    Input: 35-mer (6bp upstream + 20bp guide + 3bp PAM + 6bp downstream)
    Output: Activity score 0-100

    Requires the crisprscan package:
    pip install crisprscan
    '''
    try:
        import crisprscan
        return crisprscan.score(guide_35mer)
    except ImportError:
        # Fallback to simplified scoring
  
# ... (truncated)
```

### bio-genome-engineering-hdr-template-design
**用途**: Design homology-directed repair donor templates for CRISPR knock-ins using primer3-py. Create ssODN, dsDNA, or plasmid templates with optimized homology arms. Use when designing donor templates for...
```
ssODN (single-stranded oligodeoxynucleotide):
- Length: 100-200nt total
- Homology arms: 30-60nt each side
- Best for: Small insertions (<50bp), point mutations
- Delivery: Electroporation with RNP

dsDNA (double-stranded DNA):
- Length: 500bp - 5kb total
- Homology arms: 200-800bp each side
- Best for: Larger insertions (tags, reporters)
- Delivery: Plasmid or PCR product

Plasmid donor:
- Homology arms: 500-2000bp
- Best for: Large insertions (>1kb), conditional alleles
- Delivery: Transfectio
# ... (truncated)
```

### bio-genome-engineering-off-target-prediction
**用途**: Predict CRISPR off-target sites using Cas-OFFinder and CFD scoring algorithms. Identify potential unintended cleavage sites genome-wide and assess guide specificity. Use when evaluating guide RNA s...
```
# Input file format (input.txt):
# Line 1: Path to genome directory (2bit or fasta index)
# Line 2: PAM pattern (N = any, R = A/G, Y = C/T)
# Line 3+: Guide sequences with mismatch tolerance

# Example input.txt:
# /path/to/genome
# NNNNNNNNNNNNNNNNNNNNNGG
# ATCGATCGATCGATCGATCGNNN 4

# Run Cas-OFFinder
cas-offinder input.txt C output.txt  # C = use CPU
cas-offinder input.txt G output.txt  # G = use GPU (faster)
```

### bio-genome-engineering-prime-editing-design
**用途**: Design pegRNAs for prime editing using PrimeDesign algorithms. Generate spacer, PBS, and RT template sequences for precise genomic modifications without double-strand breaks. Use when designing pri...
```
pegRNA components:
1. Spacer (20nt) - guides Cas9 to target site
2. Scaffold - Cas9 binding sequence
3. RT template - encodes the desired edit
4. PBS (primer binding site) - anneals to nicked strand

        Spacer (20nt)      Scaffold     RT template    PBS
    5'─[NNNNNNNNNNNNNNNNNNNN]─[scaffold]─[edit]─────[PBS]─3'
```

### bio-genome-intervals-bed-file-basics
**用途**: 
```
import pybedtools

bed = pybedtools.BedTool('input.bed')
sorted_bed = bed.sort()
sorted_bed.saveas('sorted.bed')
```

### bio-genome-intervals-bigwig-tracks
**用途**: 
```
pip install pyBigWig
```

### bio-genome-intervals-coverage-analysis
**用途**: 
```
# bedGraph: chr, start, end, value (0-based coordinates)
chr1    0       100     0
chr1    100     200     5.5
chr1    200     300     10.2
chr1    300     400     3.1
```

### bio-genome-intervals-gtf-gff-handling
**用途**: 
```
pip install gtfparse
```

### bio-genome-intervals-interval-arithmetic
**用途**: 
```
# Statistical test for overlap significance
bedtools fisher -a peaks.bed -b genes.bed -g genome.txt
```

### bio-genome-intervals-proximity-operations
**用途**: 
```
import pybedtools

bed = pybedtools.BedTool('peaks.bed')

# Shift downstream
result = bed.shift(g='genome.txt', s=100)

# Shift upstream
result = bed.shift(g='genome.txt', s=-100)

result.saveas('shifted.bed')
```

### bio-geo-data
**用途**: 
```
from Bio import Entrez

Entrez.email = 'your.email@example.com'  # Required by NCBI
Entrez.api_key = 'your_api_key'          # Optional
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

### bio-imaging-mass-cytometry-cell-segmentation
**用途**: Cell segmentation from multiplexed tissue images. Covers deep learning (Cellpose, Mesmer) and classical approaches for nuclear and whole-cell segmentation. Use when extracting single-cell data from...
```
from skimage.segmentation import expand_labels

# If only nuclear segmentation available, expand to approximate cells
nuclear_masks = masks  # From nuclear segmentation
expanded_masks = expand_labels(nuclear_masks, distance=10)

print(f'Expanded masks from nuclei')
```

### bio-imaging-mass-cytometry-data-preprocessing
**用途**: Load and preprocess imaging mass cytometry (IMC) and MIBI data. Covers MCD/TIFF handling, hot pixel removal, and image normalization. Use when starting IMC analysis from raw MCD files or preparing ...
```
# panel.csv
channel,name,keep,ilastik
1,DNA1,1,1
2,CD45,1,1
3,CD3,1,0
4,CD8,1,0
5,CD4,1,0
```

### bio-imaging-mass-cytometry-interactive-annotation
**用途**: Interactive cell type annotation for IMC data. Covers napari-based annotation, marker-guided labeling, training data generation, and annotation validation. Use when manually annotating cell types f...
```
import napari
import numpy as np
from skimage import io
import pandas as pd

# Load IMC image stack
image_stack = io.imread('imc_image.tiff')  # (C, H, W)
segmentation_mask = io.imread('cell_segmentation.tiff')

# Create napari viewer
viewer = napari.Viewer()

# Add channels as separate layers for visualization
channel_names = ['CD45', 'CD3', 'CD68', 'panCK', 'DNA']
for i, name in enumerate(channel_names):
    viewer.add_image(image_stack[i], name=name, visible=False, colormap='gray', blending='
# ... (truncated)
```

### bio-imaging-mass-cytometry-phenotyping
**用途**: Cell type assignment from marker expression in IMC data. Covers manual gating, clustering, and automated classification approaches. Use when assigning cell types to segmented IMC cells based on pro...
```
# Add annotations to adata
adata.write('imc_phenotyped.h5ad')

# Export cell types
adata.obs[['cell_id', 'cell_type', 'centroid_x', 'centroid_y']].to_csv('cell_phenotypes.csv', index=False)
```

### bio-imaging-mass-cytometry-quality-metrics
**用途**: Quality metrics for IMC data including signal-to-noise, channel correlation, tissue integrity, and acquisition QC. Use when assessing data quality before analysis or troubleshooting problematic acq...
```
def assess_dynamic_range(channel, percentiles=(1, 99)):
    '''Assess if channel uses full dynamic range.'''
    low, high = np.percentile(channel, percentiles)
    channel_range = high - low
    max_possible = channel.max()

    utilized = channel_range / max_possible if max_possible > 0 else 0

    return {
        'range_low': low,
        'range_high': high,
        'range_utilized': utilized,
        'adequate': utilized > 0.1
    }

for i, name in enumerate(channel_names):
    dr = assess_
# ... (truncated)
```

### bio-imaging-mass-cytometry-spatial-analysis
**用途**: Spatial analysis of cell neighborhoods and interactions in IMC data. Covers neighbor graphs, spatial statistics, and interaction testing. Use when analyzing spatial relationships between cell types...
```
# Permutation test for interactions
sq.gr.interaction_matrix(adata, cluster_key='cell_type', normalized=True)

# Get interaction matrix
interaction = adata.uns['cell_type_interactions']
```

### bio-immunoinformatics-epitope-prediction
**用途**: Predict B-cell and T-cell epitopes using BepiPred, IEDB tools, and structure-based methods for vaccine and antibody design. Identify immunogenic regions in antigens. Use when designing vaccines, ma...
```
def map_epitopes_from_peptide_array(array_results, overlap=11):
    '''Map epitopes from peptide array experiments

    Peptide arrays test binding of overlapping peptides
    covering the entire antigen sequence.

    Args:
        array_results: Dict mapping peptide -> signal intensity
        overlap: Overlap between consecutive peptides

    Returns:
        Epitope map with per-residue scores
    '''
    # Implementation would process experimental binding data
    pass
```

### bio-immunoinformatics-immunogenicity-scoring
**用途**: Score and prioritize neoantigens and epitopes for immunogenicity using multi-factor models combining MHC binding, processing, expression, and sequence features. Rank candidates for vaccine design. ...
```
def check_anchor_hydrophobicity(peptide):
    '''Check hydrophobicity at MHC anchor positions

    For HLA-A*02:01 and similar alleles:
    - Position 2: Prefers hydrophobic (L, I, V, M)
    - Position 9 (C-terminus): Prefers hydrophobic (L, V, I)

    Strong anchors improve binding stability.
    '''
    hydrophobic = set('LIVMFYW')

    pos2 = peptide[1] if len(peptide) > 1 else ''
    pos_last = peptide[-1]

    return {
        'pos2_hydrophobic': pos2 in hydrophobic,
        'pos_last_hydro
# ... (truncated)
```

### bio-immunoinformatics-mhc-binding-prediction
**用途**: Predict peptide-MHC class I and II binding affinity using MHCflurry and NetMHCpan neural network models. Identify potential T-cell epitopes from protein sequences. Use when predicting MHC binding f...
```
# Install MHCflurry
pip install mhcflurry

# Download prediction models
mhcflurry-downloads fetch

# Download models for specific alleles
mhcflurry-downloads fetch models_class1_pan
```

### bio-immunoinformatics-neoantigen-prediction
**用途**: Identify tumor neoantigens from somatic mutations using pVACtools for personalized cancer immunotherapy. Predict mutant peptides that bind patient HLA and may elicit T-cell responses. Use when iden...
```
# Install pVACtools
pip install pvactools

# Or use conda for dependencies
conda create -n pvactools python=3.8
conda activate pvactools
pip install pvactools

# Download IEDB tools
pvactools download_iedb_tools
```

### bio-immunoinformatics-tcr-epitope-binding
**用途**: Predict TCR-epitope specificity using ERGO-II and deep learning models for T-cell receptor antigen recognition. Match TCRs to their cognate epitopes or predict TCR targets. Use when analyzing TCR r...
```
# ERGO-II uses deep learning to predict TCR-epitope binding
# GitHub: https://github.com/IdoSpringer/ERGO-II

def setup_ergo():
    '''Setup ERGO-II for TCR-epitope prediction

    Requirements:
    - PyTorch
    - Pre-trained models from ERGO-II repository

    ERGO-II features:
    - Uses both CDR3 alpha and beta chains
    - Incorporates MHC context
    - Trained on VDJdb and IEDB data
    '''
    print('ERGO-II setup:')
    print('1. Clone: git clone https://github.com/IdoSpringer/ERGO-II')

# ... (truncated)
```

### bio-isoform-switching
**用途**: Analyzes isoform switching events and functional consequences using IsoformSwitchAnalyzeR. Predicts protein domain changes, NMD sensitivity, ORF alterations, and coding potential shifts between con...
```
# Plot individual gene switches
switchPlot(
    switchAnalyzeRlist,
    gene = 'GENE_OF_INTEREST',
    condition1 = 'control',
    condition2 = 'treatment'
)

# Summary of consequence types
extractConsequenceSummary(
    switchAnalyzeRlist,
    consequencesToAnalyze = 'all',
    plotGenes = FALSE
)

# Enrichment of consequences
extractConsequenceEnrichment(
    switchAnalyzeRlist,
    consequencesToAnalyze = 'all'
)
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

### bio-local-blast
**用途**: 
```
blastn -query query.fa -db my_db -outfmt "6 qseqid sseqid pident length evalue stitle"
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

### bio-longread-alignment
**用途**: Align long reads using minimap2 for Oxford Nanopore and PacBio data. Supports various presets for different read types and applications. Use when aligning ONT or PacBio reads to a reference genome ...
```
# PAF format (faster, for quick analysis)
minimap2 -x map-ont reference.fa reads.fastq.gz > alignments.paf
```

### bio-longread-medaka
**用途**: Polish assemblies and call variants from Oxford Nanopore data using medaka. Uses neural networks trained on specific basecaller versions. Use when improving ONT-only assemblies or calling variants ...
```
# Polish specific region
medaka inference aligned.bam consensus.hdf \
    --model r1041_e82_400bps_sup_v5.0.0 \
    --region chr1:1000000-2000000
```

### bio-longread-qc
**用途**: Quality control for long-read sequencing data using NanoPlot, NanoStat, and chopper. Generate QC reports, filter reads by length and quality, and visualize read characteristics. Use when assessing ...
```
# Filter by length and quality
gunzip -c reads.fastq.gz | chopper -q 10 -l 1000 | gzip > filtered.fastq.gz

# Quality >= 10, length >= 1000bp
```

### bio-longread-structural-variants
**用途**: Detect structural variants from long-read alignments using Sniffles, cuteSV, and SVIM. Use when detecting deletions, insertions, inversions, translocations, or complex rearrangements from ONT or Pa...
```
# Call SVs from aligned BAM
sniffles --input aligned.bam \
    --vcf structural_variants.vcf \
    --reference reference.fa \
    --threads 4
```

### bio-machine-learning-atlas-mapping
**用途**: 
```
import scanpy as sc

# Combine reference and query for visualization
adata_combined = adata_ref.concatenate(adata_query, batch_key='dataset', batch_categories=['reference', 'query'])

# Use latent space for neighbors/UMAP
sc.pp.neighbors(adata_combined, use_rep='X_scVI')
sc.tl.umap(adata_combined)
sc.pl.umap(adata_combined, color=['dataset', 'cell_type'], save='_transfer.png')
```

### bio-machine-learning-biomarker-discovery
**用途**: 
```
from mrmr import mrmr_classif

# K: Number of features to select; start with 50-100 for omics
selected_features = mrmr_classif(X=X, y=pd.Series(y), K=50)
X_selected = X[selected_features]
```

### bio-machine-learning-model-validation
**用途**: 
```
from sklearn.model_selection import LeaveOneOut, cross_val_predict

# Use for very small datasets (n < 30)
loo = LeaveOneOut()
y_pred = cross_val_predict(pipe, X, y, cv=loo, method='predict_proba')[:, 1]
auc = roc_auc_score(y, y_pred)
print(f'LOO AUC: {auc:.3f}')
```

### bio-machine-learning-omics-classifiers
**用途**: 
```
import pandas as pd

importances = pipe.named_steps['clf'].feature_importances_
feature_imp = pd.DataFrame({'feature': X.columns, 'importance': importances})
feature_imp = feature_imp.sort_values('importance', ascending=False).head(20)
```

### bio-machine-learning-prediction-explanation
**用途**: 
```
# Shows how SHAP value varies with feature value
# Automatically colors by interacting feature
shap.plots.scatter(shap_values[:, 'GENE1'], color=shap_values, show=False)
plt.savefig('shap_dependence.png', dpi=150, bbox_inches='tight')
```

### bio-machine-learning-survival-analysis
**用途**: 
```
# Test PH assumption
cph.check_assumptions(df, p_value_threshold=0.05, show_plots=True)
```

### bio-metabolomics-lipidomics
**用途**: Specialized lipidomics analysis for lipid identification, quantification, and pathway interpretation. Covers LC-MS lipidomics with LipidSearch, MS-DIAL, and LipidMaps annotation. Use when analyzing...
```
# Parse lipid names to extract class, chain info
lipid_data <- annotate_lipids(lipid_data)

# View lipid classes
table(rowData(lipid_data)$Class)

# Chain length and saturation
plot_chain_distribution(lipid_data)
```

### bio-metabolomics-metabolite-annotation
**用途**: Metabolite identification from m/z and retention time. Covers database matching, MS/MS spectral matching, and confidence level assignment. Use when assigning compound identities to detected feature...
```
# Molecular formula and structure prediction
sirius \
    --input sample.ms \
    --output sirius_results \
    --database hmdb \
    formula \
    fingerid

# Output structure:
# sirius_results/
#   compound_1/
#     formula_candidates.tsv
#     fingerid_candidates.tsv
```

### bio-metabolomics-msdial-preprocessing
**用途**: MS-DIAL-based metabolomics preprocessing as alternative to XCMS. Covers peak detection, alignment, annotation, and export for downstream analysis. Use when processing MS-DIAL output files for R/Pyt...
```
# MS-DIAL console application for batch processing
# Available on Windows

# Create parameter file (msdial_param.txt)
# See MS-DIAL documentation for all parameters

# Run MS-DIAL console
MsdialConsoleApp.exe lcmsdda -i input_folder -o output_folder -m msdial_param.txt
```

### bio-metabolomics-normalization-qc
**用途**: Quality control and normalization for metabolomics data. Covers QC-based correction, batch effect removal, and data transformation methods. Use when correcting technical variation in metabolomics d...
```
# Simple sum normalization
tic_normalize <- function(data) {
    row_sums <- rowSums(data, na.rm = TRUE)
    normalized <- data / row_sums * median(row_sums)
    return(normalized)
}

data_tic <- tic_normalize(data)
```

### bio-metabolomics-pathway-mapping
**用途**: Map metabolites to biological pathways using KEGG, Reactome, and MetaboAnalyst. Perform pathway enrichment and topology analysis. Use when interpreting metabolomics results in the context of bioche...
```
library(ReactomePA)
library(clusterProfiler)

# Convert to Reactome IDs (if available)
reactome_ids <- c('R-HSA-70171', 'R-HSA-1428517')  # Example

# Enrichment
enriched <- enrichPathway(gene = reactome_ids, organism = 'human', pvalueCutoff = 0.05)
print(enriched)
```

### bio-metabolomics-statistical-analysis
**用途**: Statistical analysis for metabolomics data. Covers univariate testing, multivariate methods (PCA, PLS-DA), and biomarker discovery. Use when identifying differentially abundant metabolites or build...
```
library(ropls)

# OPLS-DA
oplsda <- opls(data, groups, predI = 1, orthoI = NA)

# Summary
print(oplsda)

# Scores plot
plot(oplsda, typeVc = 'x-score')

# S-plot (loadings vs correlation)
plot(oplsda, typeVc = 'x-loading')

# VIP
vip_scores <- getVipVn(oplsda)
top_vip <- sort(vip_scores, decreasing = TRUE)[1:20]
```

### bio-metabolomics-targeted-analysis
**用途**: Targeted metabolomics analysis using MRM/SRM with standard curves. Covers absolute quantification, method validation, and quality assessment. Use when quantifying specific metabolites using calibra...
```
# Final results table
results_final <- data.frame(
    sample = samples$sample,
    concentration_nM = round(samples$concentration, 2),
    concentration_uM = round(samples$concentration / 1000, 4),
    cv_percent = round(samples$cv, 1),
    qc_flag = ifelse(samples$cv > 20, 'FAIL', 'PASS')
)

write.csv(results_final, 'targeted_results.csv', row.names = FALSE)
```

### bio-metabolomics-xcms-preprocessing
**用途**: XCMS3 workflow for LC-MS/MS metabolomics preprocessing. Covers peak detection, retention time alignment, correspondence (grouping), and gap filling. Use when processing raw LC-MS data into a featur...
```
# MatchedFilter for profile/continuum data
mfp <- MatchedFilterParam(
    binSize = 0.1,
    fwhm = 30,
    snthresh = 10,
    step = 0.1,
    mzdiff = 0.8
)

xdata_profile <- findChromPeaks(raw_data, param = mfp)
```

### bio-metagenomics-abundance
**用途**: Species abundance estimation using Bracken with Kraken2 output. Redistributes reads from higher taxonomic levels to species for more accurate estimates. Use when accurate species-level abundances a...
```
# Use threshold for minimum reads
bracken -d db \
    -i report.txt \
    -o bracken.txt \
    -r 150 \
    -l S \
    -t 10                          # Minimum reads threshold
```

### bio-metagenomics-amr-detection
**用途**: Detect antimicrobial resistance genes using AMRFinderPlus, ResFinder, and CARD. Screen isolates and metagenomes for resistance determinants. Use when characterizing resistance profiles in clinical ...
```
conda install -c bioconda abricate
abricate --setupdb  # Update databases
```

### bio-metagenomics-functional-profiling
**用途**: Profile functional potential of metagenomes using HUMAnN3 and similar tools. Use when obtaining pathway abundances, gene family counts, or functional annotations from metagenomic data.
```
# Format for LEfSe
humann_join_tables -i . -o merged.tsv --file_name pathabundance
humann_renorm_table -i merged.tsv -o merged_relab.tsv -u relab
```

### bio-metagenomics-kraken
**用途**: Taxonomic classification of metagenomic reads using Kraken2. Fast k-mer based classification against RefSeq database. Use when performing initial taxonomic classification of shotgun metagenomic rea...
```
# View database contents
kraken2-inspect --db /path/to/kraken2_db | head -50
```

### bio-metagenomics-metaphlan
**用途**: Marker gene-based taxonomic profiling using MetaPhlAn 4. Provides accurate species-level relative abundances using clade-specific markers. Use when accurate taxonomic profiling is needed and comput...
```
# Profile single sample
metaphlan sample.fastq.gz \
    --input_type fastq \
    --output_file profile.txt
```

### bio-metagenomics-strain-tracking
**用途**: Track bacterial strains using MASH, sourmash, fastANI, and inStrain. Compare genomes, detect contamination, and monitor strain-level variation. Use when needing sub-species resolution for outbreak ...
```
conda install -c bioconda mash
```

### bio-metagenomics-visualization
**用途**: Visualize metagenomic profiles using R (phyloseq, microbiome) and Python (matplotlib, seaborn). Create stacked bar plots, heatmaps, PCA plots, and diversity analyses. Use when creating publication-...
```
# From Kraken2 report
ktImportTaxonomy -q 1 -t 5 kraken_report.txt -o krona_chart.html

# From MetaPhlAn
metaphlan2krona.py -p profile.txt -k krona_profile.txt
ktImportText krona_profile.txt -o krona_metaphlan.html
```

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

### bio-microbiome-amplicon-processing
**用途**: Amplicon sequence variant (ASV) inference from 16S rRNA or ITS amplicon sequencing using DADA2. Covers quality filtering, error learning, denoising, and chimera removal. Use when processing demulti...
```
mergers <- mergePairs(dadaFs, filtFs, dadaRs, filtRs, verbose = TRUE)

# Check merge success
head(mergers[[1]])
```

### bio-microbiome-differential-abundance
**用途**: Differential abundance testing for microbiome data using compositionally-aware methods like ALDEx2, ANCOM-BC2, and MaAsLin2. Use when identifying taxa that differ between experimental groups while ...
```
library(DESeq2)
library(phyloseq)

# Convert to DESeq2 (use geometric mean of poscounts)
ps_deseq <- ps
ps_deseq <- prune_samples(sample_sums(ps_deseq) > 1000, ps_deseq)

dds <- phyloseq_to_deseq2(ps_deseq, ~ Group)
dds <- DESeq(dds, test = 'Wald', fitType = 'parametric', sfType = 'poscounts')

res <- results(dds, alpha = 0.05)
sig_deseq <- res[which(res$padj < 0.05 & abs(res$log2FoldChange) > 1), ]
```

### bio-microbiome-diversity-analysis
**用途**: Alpha and beta diversity analysis for microbiome data. Calculate within-sample richness, evenness, and between-sample dissimilarity with phyloseq and vegan. Use when comparing community composition...
```
# Test homogeneity of dispersions (assumption of PERMANOVA)
beta_disp <- betadisper(bray, metadata$Group)
permutest(beta_disp)
plot(beta_disp)
```

### bio-microbiome-functional-prediction
**用途**: Predict metagenome functional content from 16S rRNA marker gene data using PICRUSt2. Infer KEGG, MetaCyc, and EC abundances from ASV tables. Use when functional profiling is needed from 16S data wi...
```
# Map pathway IDs to names
add_descriptions.py \
    -i pathway_abundance.tsv \
    -m METACYC \
    -o pathway_abundance_described.tsv
```
**限制**: Predictions based on phylogenetic placement; Novel taxa (high NSTI) have unreliable predictions

### bio-microbiome-qiime2-workflow
**用途**: QIIME2 command-line workflow for 16S/ITS amplicon analysis. Alternative to DADA2/phyloseq R workflow with built-in provenance tracking. Use when preferring CLI over R, needing reproducible provenan...
```
# metadata.tsv (tab-separated)
sample-id	Group	Timepoint
sample1	Treatment	Day0
sample2	Control	Day0
sample3	Treatment	Day7
```

### bio-microbiome-taxonomy-assignment
**用途**: Taxonomic classification of ASVs using reference databases like SILVA, GTDB, or UNITE. Covers naive Bayes classifiers (DADA2, IDTAXA) and exact matching approaches. Use when assigning taxonomy to A...
```
# UNITE database for fungal ITS
taxa_its <- assignTaxonomy(seqtab_nochim, 'sh_general_release_dynamic_25.07.2023.fasta',
                           multithread = TRUE)
```

### bio-molecular-descriptors
**用途**: Calculates molecular descriptors and fingerprints using RDKit. Computes Morgan fingerprints (ECFP), MACCS keys, Lipinski properties, QED drug-likeness, TPSA, and 3D conformer descriptors. Use when ...
```
from rdkit.Chem import MACCSkeys

maccs = MACCSkeys.GenMACCSKeys(mol)  # 167 bits

# As numpy array
maccs_array = np.array(maccs)
```

### bio-molecular-io
**用途**: Reads, writes, and converts molecular file formats (SMILES, SDF, MOL2, PDB) using RDKit and Open Babel. Handles structure parsing, canonicalization, and full standardization pipeline including sani...
```
from rdkit import Chem

# To SMILES
smiles = Chem.MolToSmiles(mol)  # Canonical SMILES
smiles_iso = Chem.MolToSmiles(mol, isomericSmiles=True)  # With stereochemistry

# To SDF file
writer = Chem.SDWriter('output.sdf')
for mol in molecules:
    writer.write(mol)
writer.close()

# To MOL block (string)
mol_block = Chem.MolToMolBlock(mol)
```

### bio-motif-search
**用途**: 
```
from Bio.Seq import Seq
from Bio import motifs
import re
```

### bio-multi-omics-data-harmonization
**用途**: Preprocessing and harmonization of multi-omics data before integration. Covers normalization, batch correction, feature alignment, and missing value handling across data types. Use when preparing m...
```
# Find complete samples across all assays
complete_samples <- intersectColumns(mae)
cat('Samples in all assays:', ncol(complete_samples), '\n')

# Subset to common samples
mae_matched <- mae[, complete_samples, ]

# Alternative: keep samples with N-1 assays
subsetByColData(mae, mae$has_at_least_2_assays)
```

### bio-multi-omics-mixomics-analysis
**用途**: Supervised and unsupervised multi-omics integration with mixOmics. Includes sPLS for pairwise integration and DIABLO for multi-block discriminant analysis. Use when performing supervised multi-omic...
```
# Cross-validation performance
perf_result <- perf(diablo, validation = 'Mfold', folds = 5, nrepeat = 50, cpus = 4)

# Error rates
plot(perf_result)
perf_result$error.rate

# AUC
auc_diablo <- auroc(diablo, roc.block = 'RNA', roc.comp = 1)
```

### bio-multi-omics-mofa-integration
**用途**: Multi-Omics Factor Analysis (MOFA2) for unsupervised integration of multiple data modalities. Identifies shared and view-specific sources of variation. Use when integrating RNA-seq, proteomics, met...
```
# Load sample annotations
metadata <- read.csv('sample_metadata.csv', row.names = 1)

# Add to MOFA object
samples_metadata(mofa) <- metadata[samples_names(mofa)[[1]], ]

# Color by metadata
plot_factor(mofa, factor = 1, color_by = 'Condition')
plot_factors(mofa, factors = 1:3, color_by = 'Condition')
```

### bio-multi-omics-similarity-network
**用途**: Similarity Network Fusion (SNF) for patient stratification using multi-omics data. Integrates multiple data types into a unified patient similarity network. Use when performing patient stratificati...
```
# Determine optimal number of clusters
estimateNumberOfClustersGivenGraph(fused, NUMC = 2:10)

# Spectral clustering
num_clusters <- 3
clusters <- spectralClustering(fused, num_clusters)

# Add to sample metadata
sample_info <- data.frame(
    Sample = rownames(data1),
    Cluster = factor(clusters)
)
```

### bio-orchestrator
**用途**: Meta-agent that routes bioinformatics requests to specialised sub-skills. Handles file type detection, analysis planning, report generation, and reproducibility export.
```
# Analysis Report: [Title]

**Date**: [ISO date]
**Skill(s) used**: [list]
**Input files**: [list with checksums]

## Methods
[Tool versions, parameters, reference genomes used]

## Results
[Tables, figures, key findings]

## Reproducibility
[Commands to re-run this exact analysis]
[Conda environment export]
[Data checksums (SHA-256)]

## References
[Software citations in BibTeX]
```

### bio-paired-end-fastq
**用途**: Handle paired-end FASTQ files (R1/R2) using Biopython. Use when working with Illumina paired reads, synchronizing pairs, interleaving/deinterleaving, or filtering paired data.
```
from Bio import SeqIO
```

### bio-pathway-enrichment-visualization
**用途**: Visualize enrichment results using enrichplot package functions. Use when creating publication-quality figures from clusterProfiler results. Covers dotplot, barplot, cnetplot, emapplot, gseaplot2, ...
```
upsetplot(ego)

# Limit to specific number of terms
upsetplot(ego, n = 10)
```

### bio-pathway-go-enrichment
**用途**: Gene Ontology over-representation analysis using clusterProfiler enrichGO. Use when identifying biological functions enriched in a gene list from differential expression or other analyses. Supports...
```
# Remove redundant GO terms (keeps representative terms)
ego_simplified <- simplify(ego, cutoff = 0.7, by = 'p.adjust', select_fun = min)
```

### bio-pathway-gsea
**用途**: Gene Set Enrichment Analysis using clusterProfiler gseGO and gseKEGG. Use when analyzing ranked gene lists to find coordinated expression changes in gene sets without arbitrary significance cutoffs...
```
results_df <- as.data.frame(gse_go)
write.csv(results_df, 'gsea_go_results.csv', row.names = FALSE)

# Get leading edge genes for a term
leading_edge <- strsplit(results_df$core_enrichment[1], '/')[[1]]
```

### bio-pathway-kegg-pathways
**用途**: KEGG pathway and module enrichment analysis using clusterProfiler enrichKEGG and enrichMKEGG. Use when identifying metabolic and signaling pathways over-represented in a gene list. Supports 4000+ o...
```
# Find organism codes
search_kegg_organism('mouse')
search_kegg_organism('zebrafish')
```

### bio-pathway-reactome
**用途**: Reactome pathway enrichment using ReactomePA package. Use when analyzing gene lists against Reactome's curated peer-reviewed pathway database. Performs over-representation analysis and GSEA with vi...
```
results_df <- as.data.frame(pathway_result)
write.csv(results_df, 'reactome_enrichment.csv', row.names = FALSE)

# Key columns: ID, Description, GeneRatio, BgRatio, pvalue, p.adjust, geneID, Count
```

### bio-pathway-wikipathways
**用途**: WikiPathways enrichment using clusterProfiler and rWikiPathways. Use when analyzing gene lists against community-curated open-source pathways. Performs over-representation analysis and GSEA for 30+...
```
results_df <- as.data.frame(wp_result)
write.csv(results_df, 'wikipathways_enrichment.csv', row.names = FALSE)
```

### bio-phasing-imputation-genotype-imputation
**用途**: 
```
# PLINK2 with dosages
plink2 --vcf imputed.vcf.gz dosage=DS \
    --glm \
    --pheno phenotypes.txt \
    --out gwas_results
```

### bio-phasing-imputation-haplotype-phasing
**用途**: 
```
# Use reference panel for better phasing
java -jar beagle.22Jul22.46e.jar \
    gt=input.vcf.gz \
    ref=reference.vcf.gz \
    map=genetic_map.txt \
    out=phased \
    nthreads=8
```

### bio-phasing-imputation-imputation-qc
**用途**: 
```
# Calculate HWE p-values (PLINK2)
plink2 --vcf imputed.vcf.gz \
    --hardy \
    --out hwe_check

# Filter extreme HWE deviations
plink2 --vcf imputed.vcf.gz \
    --hwe 1e-6 \
    --make-pgen \
    --out imputed_hwe_filtered
```

### bio-phasing-imputation-reference-panels
**用途**: 
```
# IMPUTE5 uses its own format
imp5Converter \
    --h reference.vcf.gz \
    --r chr22 \
    --o reference.chr22.imp5
```

### bio-phylo-distance-calculations
**用途**: 
```
constructor = DistanceTreeConstructor()
upgma_tree = constructor.upgma(dm)
Phylo.draw_ascii(upgma_tree)
```

### bio-phylo-modern-tree-inference
**用途**: 
```
# IQ-TREE2: Resume from checkpoint
iqtree2 -s alignment.fasta -m GTR+G -B 1000 --redo-tree

# RAxML-ng: Resume
raxml-ng --msa alignment.fasta --model GTR+G --redo
```

### bio-phylo-tree-io
**用途**: 
```
from Bio import Phylo
from io import StringIO
```

### bio-phylo-tree-manipulation
**用途**: 
```
from Bio import Phylo
from io import StringIO
```

### bio-phylo-tree-visualization
**用途**: 
```
from Bio import Phylo
import matplotlib.pyplot as plt
```

### bio-pileup-generation
**用途**: 
```
samtools mpileup -f reference.fa -q 20 input.bam
```

### bio-population-genetics-association-testing
**用途**: 
```
# Linear regression for quantitative traits
plink2 --bfile data --pheno pheno.txt --glm --out results
```

### bio-population-genetics-linkage-disequilibrium
**用途**: 
```
# ld_results.ld contains:
CHR_A  BP_A  SNP_A  CHR_B  BP_B  SNP_B  R2
```

### bio-population-genetics-plink-basics
**用途**: 
```
# update.txt: old_id new_id
plink2 --bfile input --update-name update.txt --make-bed --out output
```

### bio-population-genetics-population-structure
**用途**: 
```
# From conda
conda install -c bioconda flashpca

# Or download binaries from GitHub
# https://github.com/gabraham/flashpca
```

### bio-population-genetics-scikit-allel-analysis
**用途**: 
```
pip install scikit-allel
# Optional: zarr for chunked storage
pip install zarr
```

### bio-population-genetics-selection-statistics
**用途**: 
```
nsl = allel.nsl(h_flt)
nsl_std = allel.standardize_by_allele_count(nsl, ac_flt[:, 1])
```

### bio-primer-design-primer-basics
**用途**: 
```
import primer3
from primer3 import p3helpers
from Bio import SeqIO
from Bio.Seq import Seq
```

### bio-primer-design-primer-validation
**用途**: 
```
import primer3
```

### bio-primer-design-qpcr-primers
**用途**: 
```
import primer3
from Bio import SeqIO
```

### bio-proteomics-data-import
**用途**: Load and parse mass spectrometry data formats including mzML, mzXML, and quantification tool outputs like MaxQuant proteinGroups.txt. Use when starting a proteomics analysis with raw or processed M...
```
library(MSnbase)

raw_data <- readMSData('sample.mzML', mode = 'onDisk')
spectra <- spectra(raw_data)
header_info <- fData(raw_data)
```

### bio-proteomics-dia-analysis
**用途**: Data-independent acquisition (DIA) proteomics analysis with DIA-NN and other tools. Use when analyzing DIA mass spectrometry data with library-free or library-based workflows for deep proteome prof...
```
# DIA-NN MBR is automatic with --reanalyse flag
# First pass: identifies peptides per run
# Second pass: transfers IDs between runs

diann \
    --f *.mzML \
    --lib library.tsv \
    --reanalyse \
    --out report_mbr.tsv
```

### bio-proteomics-differential-abundance
**用途**: Statistical testing for differentially abundant proteins between conditions. Covers limma and MSstats workflows with multiple testing correction. Use when identifying proteins with significant abun...
```
# Volcano plot
library(ggplot2)

ggplot(results, aes(x = log2FC, y = -log10(adj.P.Val))) +
    geom_point(aes(color = significant), alpha = 0.6) +
    geom_hline(yintercept = -log10(0.05), linetype = 'dashed') +
    geom_vline(xintercept = c(-1, 1), linetype = 'dashed') +
    scale_color_manual(values = c('grey', 'red')) +
    theme_minimal()
```

### bio-proteomics-peptide-identification
**用途**: Peptide-spectrum matching and protein identification from MS/MS data. Use when identifying peptides from tandem mass spectra. Covers database searching, spectral library matching, and FDR estimatio...
```
library(MSnbase)

# Read mzIdentML results
psms <- readMzIdData('results.mzid')

# Filter to 1% FDR
psms_filtered <- psms[psms$qvalue <= 0.01, ]

# Unique peptides per protein
peptide_counts <- table(psms_filtered$accession)
```

### bio-proteomics-protein-inference
**用途**: Protein grouping and inference from peptide identifications. Use when resolving protein ambiguity from shared peptides. Handles protein groups and protein-level FDR control using parsimony and prob...
```
library(ProteinInference)

# From peptide-protein mapping
protein_groups <- infer_proteins(
    peptides = psm_data$peptide,
    proteins = psm_data$protein,
    method = 'parsimony'
)

# Count unique peptides per group
protein_groups$n_unique <- sapply(protein_groups$peptides, function(p) {
    sum(sapply(p, function(pep) length(peptide_to_protein[[pep]]) == 1))
})
```

### bio-proteomics-proteomics-qc
**用途**: Quality control and assessment for proteomics data. Use when evaluating proteomics data quality before downstream analysis. Covers sample metrics, missing value patterns, replicate correlation, bat...
```
library(limma)
library(ggplot2)

# Intensity distribution
plotDensities(protein_matrix, legend = FALSE, main = 'Intensity Distributions')

# MA plots between samples
for (i in 2:ncol(protein_matrix)) {
    plotMA(protein_matrix[, c(1, i)], main = paste('MA:', colnames(protein_matrix)[i]))
}

# MDS plot (similar to PCA)
plotMDS(protein_matrix, col = as.numeric(sample_info$condition))
```

### bio-proteomics-ptm-analysis
**用途**: Post-translational modification analysis including phosphorylation, acetylation, and ubiquitination. Covers site localization, motif analysis, and quantitative PTM analysis. Use when analyzing phos...
```
PTM_MASSES = {
    'Phosphorylation': 79.966331,      # STY
    'Oxidation': 15.994915,             # M
    'Acetylation': 42.010565,           # K, N-term
    'Methylation': 14.015650,           # KR
    'Dimethylation': 28.031300,         # KR
    'Trimethylation': 42.046950,        # K
    'Ubiquitination': 114.042927,       # K (GlyGly remnant)
    'Deamidation': 0.984016,            # NQ
    'Carbamidomethyl': 57.021464,       # C (fixed mod from IAA)
}
```

### bio-proteomics-quantification
**用途**: Protein quantification from mass spectrometry data including label-free (LFQ, intensity-based), isobaric labeling (TMT, iTRAQ), and metabolic labeling (SILAC) approaches. Use when extracting protei...
```
def spectral_count_normalize(counts, total_spectra):
    '''Normalized spectral abundance factor (NSAF)'''
    # Divide by protein length, then by total
    nsaf = counts / total_spectra
    return nsaf / nsaf.sum()
```

### bio-proteomics-spectral-libraries
**用途**: Build, manage, and search spectral libraries for proteomics. Use when creating or working with spectral libraries for DIA analysis. Covers DDA-based library generation, predicted libraries (Prosit,...
```
# Required columns
PrecursorMz    ProductMz    Annotation    ProteinId    GeneName
PeptideSequence    ModifiedSequence    PrecursorCharge
FragmentCharge    FragmentType    FragmentSeriesNumber
NormalizedRetentionTime    LibraryIntensity
```

### bio-reaction-enumeration
**用途**: Enumerates chemical libraries through reaction SMARTS transformations using RDKit. Generates virtual compound libraries from building blocks using defined chemical reactions with product validation...
```
REACTIONS = {
    'amide_coupling': '[C:1](=[O:2])O.[N:3]>>[C:1](=[O:2])[N:3]',
    'reductive_amination': '[C:1]=O.[N:2]>>[C:1][N:2]',
    'suzuki': '[c:1][Br].[c:2][B](O)O>>[c:1][c:2]',
    'buchwald': '[c:1][Br].[N:2]>>[c:1][N:2]',
    'ester_formation': '[C:1](=[O:2])O.[O:3]>>[C:1](=[O:2])[O:3]',
    'michael_addition': '[C:1]=[C:2]C(=O).[C:3]>>[C:1][C:2]([C:3])C(=O)',
}
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

### bio-read-sequences
**用途**: Read biological sequence files (FASTA, FASTQ, GenBank, EMBL, ABI, SFF) using Biopython Bio.SeqIO. Use when parsing sequence files, iterating multi-sequence files, random access to large files, or h...
```
from Bio import SeqIO
```

### bio-reference-operations
**用途**: 
```
samtools faidx reference.fa chr1
```

### bio-reporting-automated-qc-reports
**用途**: 
```
from multiqc import run as multiqc_run

# Run programmatically
multiqc_run(analysis_dir='results/', outdir='qc_report/')
```

### bio-reporting-figure-export
**用途**: 
```
library(ggplot2)

p <- ggplot(data, aes(x, y)) + geom_point() +
  theme_classic(base_size = 8) +
  theme(text = element_text(family = 'Arial'))

# PDF for vector graphics
ggsave('figure1.pdf', p, width = 3.5, height = 3, units = 'in')

# High-res PNG
ggsave('figure1.png', p, width = 3.5, height = 3, units = 'in', dpi = 300)

# TIFF (some journals require)
ggsave('figure1.tiff', p, width = 3.5, height = 3, units = 'in',
       dpi = 300, compression = 'lzw')
```

### bio-reporting-jupyter-reports
**用途**: 
```
# Parameters (tag this cell as "parameters")
input_file = 'default.csv'
output_dir = 'results/'
fdr_threshold = 0.05
```
**注意**: Keep analysis code in cells, explanatory text in markdown; Use parameters for all configurable values; Include version information and timestamps

### bio-reporting-quarto-reports
**用途**: 
```

```

### bio-reporting-rmarkdown-reports
**用途**: 
```

```

### bio-research-tools-biomarker-signature-studio
**用途**: 
```
python Skills/Research_Tools/Biomarker_Signature_Studio/scripts/biomarker_signature_studio.py \
  --expression data/expression.csv \
  --metadata data/metadata.csv \
  --label-column phenotype \
  --selectors boruta,lasso,mrmr \
  --models rf,logit \
  --output-dir outputs/biomarkers_run1
```

### bio-restriction-enzyme-selection
**用途**: 
```
# Common Type IIS enzymes for Golden Gate/modular cloning
from Bio.Restriction import BsaI, BsmBI, BbsI, SapI, BtgZI

golden_gate_enzymes = [BsaI, BsmBI, BbsI, SapI, BtgZI]

for enzyme in golden_gate_enzymes:
    print(f'{enzyme}: site={enzyme.site}, overhang={enzyme.ovhg}bp')
```

### bio-restriction-fragment-analysis
**用途**: 
```
from Bio.Restriction import EcoRI

fragments = EcoRI.catalyze(seq)[0]

for i, frag in enumerate(fragments, 1):
    print(f'Fragment {i}: {len(frag)} bp')
    print(f'  5\' end: {frag[:20]}...')
    print(f'  3\' end: ...{frag[-20:]}')
```

### bio-restriction-mapping
**用途**: 
```
# Map format (visual)
analysis.print_as('map')

# Linear format (list)
analysis.print_as('linear')

# Tabular format
analysis.print_as('tabulate')

# Get as string instead of printing
map_str = analysis.format_as('map')
linear_str = analysis.format_as('linear')
```

### bio-restriction-sites
**用途**: 
```
from Bio.Restriction import AllEnzymes

# Get enzyme by string name
ecori = AllEnzymes.get('EcoRI')
sites = ecori.search(seq)

# Check if enzyme exists
if 'EcoRI' in AllEnzymes:
    print('EcoRI is in database')
```

### bio-reverse-complement
**用途**: 
```
from Bio.Seq import Seq
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

### bio-rnaseq-qc
**用途**: RNA-seq specific quality control including rRNA contamination detection, strandedness verification, gene body coverage, and transcript integrity metrics. Use when validating RNA-seq libraries befor...
```
infer_experiment.py -i aligned.bam -r genes.bed
```

### bio-sam-bam-basics
**用途**: 
```
samtools view -H input.bam
```

### bio-sashimi-plots
**用途**: Creates sashimi plots showing RNA-seq read coverage and splice junction counts using ggsashimi or rmats2sashimiplot. Visualizes differential splicing events with grouped samples and junction read s...
```
# For rMATS output specifically
rmats2sashimiplot \
    --b1 sample1.bam,sample2.bam \
    --b2 sample3.bam,sample4.bam \
    -t SE \
    -e rmats_output/SE.MATS.JC.txt \
    --l1 Control \
    --l2 Treatment \
    -o sashimi_rmats \
    --exon_s 1 \
    --intron_s 5
```

### bio-seq-objects
**用途**: 
```
seq = Seq('ATGCGATCGATCG')
```

### bio-sequence-properties
**用途**: 
```
helix, turn, sheet = protein.secondary_structure_fraction()
```

### bio-sequence-similarity
**用途**: 
```
hmmbuild profile.hmm alignment.sto
```

### bio-sequence-slicing
**用途**: 
```
from Bio.Seq import Seq
```

### bio-sequence-statistics
**用途**: Calculate sequence statistics (N50, length distribution, GC content, summary reports) using Biopython. Use when analyzing sequence datasets, generating QC reports, or comparing assemblies.
```
from Bio import SeqIO
from Bio.SeqUtils import gc_fraction
import statistics
```

### bio-similarity-searching
**用途**: Performs molecular similarity searches using Tanimoto coefficient on fingerprints via RDKit. Finds structurally similar compounds using ECFP or MACCS keys and clusters molecules by structural simil...
```
from rdkit import Chem, DataStructs
from rdkit.Chem import AllChem

# Generate fingerprints
mol1 = Chem.MolFromSmiles('CCO')
mol2 = Chem.MolFromSmiles('CCCO')

fp1 = AllChem.GetMorganFingerprintAsBitVect(mol1, radius=2, nBits=2048)
fp2 = AllChem.GetMorganFingerprintAsBitVect(mol2, radius=2, nBits=2048)

# Tanimoto similarity (0-1)
similarity = DataStructs.TanimotoSimilarity(fp1, fp2)
print(f'Tanimoto similarity: {similarity:.3f}')
```

### bio-single-cell-batch-integration
**用途**: Integrate multiple scRNA-seq samples/batches using Harmony, scVI, Seurat anchors, and fastMNN. Remove technical variation while preserving biological differences. Use when integrating multiple scRN...
```
# Correct for both sample and technology
merged <- RunHarmony(merged, group.by.vars = c('sample', 'technology'),
                     dims.use = 1:30, max.iter.harmony = 20)
```

### bio-single-cell-cell-annotation
**用途**: Automated cell type annotation using reference-based methods including CellTypist, scPred, SingleR, and Azimuth for consistent, reproducible cell labeling. Use when automatically annotating cell ty...
```
# CellTypist: filter low confidence
high_conf = adata[adata.obs['conf_score'] > 0.5].copy()

# Flag uncertain cells
adata.obs['annotation_uncertain'] = adata.obs['conf_score'] < 0.3
```

### bio-single-cell-cell-communication
**用途**: Infer cell-cell communication networks from scRNA-seq data using CellChat, NicheNet, and LIANA for ligand-receptor interaction analysis. Use when inferring ligand-receptor interactions between cell...
```
# Identify signaling roles
cellchat <- netAnalysis_computeCentrality(cellchat, slot.name = 'netP')

# Signaling role heatmap
netAnalysis_signalingRole_heatmap(cellchat, signaling = c('WNT', 'TGFb', 'BMP'))

# Dominant senders/receivers
netAnalysis_signalingRole_scatter(cellchat)

# Compare pathways
rankNet(cellchat, mode = 'comparison', stacked = TRUE, do.stat = TRUE)
```

### bio-single-cell-clustering
**用途**: Dimensionality reduction and clustering for single-cell RNA-seq using Seurat (R) and Scanpy (Python). Use for running PCA, computing neighbors, clustering with Leiden/Louvain algorithms, generating...
```
library(Seurat)
library(ggplot2)
```

### bio-single-cell-data-io
**用途**: Read, write, and create single-cell data objects using Seurat (R) and Scanpy (Python). Use for loading 10X Genomics data, importing/exporting h5ad and RDS files, creating Seurat objects and AnnData...
```
library(Seurat)
library(Matrix)
```

### bio-single-cell-doublet-detection
**用途**: Detect and remove doublets (multiple cells captured in one droplet) from single-cell RNA-seq data. Uses Scrublet (Python), DoubletFinder (R), and scDblFinder (R). Essential QC step before clusterin...
```
sce <- scDblFinder(sce, samples = 'sample_id')
```

### bio-single-cell-lineage-tracing
**用途**: Reconstruct cell lineage trees from CRISPR barcode tracing or mitochondrial mutations. Use when studying clonal dynamics, cell fate decisions, or developmental trajectories.
```
# Fate coupling between cell types
cs.tl.fate_coupling(adata, source='HSC')
cs.pl.fate_coupling(adata, source='HSC')

# Transition probabilities over time
cs.tl.transition_map(adata, time_key='day')
cs.pl.transition_map(adata)

# Clone size dynamics
cs.tl.clone_size(adata, time_key='day')
cs.pl.clone_size(adata)
```

### bio-single-cell-markers-annotation
**用途**: Find marker genes and annotate cell types in single-cell RNA-seq using Seurat (R) and Scanpy (Python). Use for differential expression between clusters, identifying cluster-specific markers, scorin...
```
library(Seurat)
library(dplyr)
```

### bio-single-cell-metabolite-communication
**用途**: Analyze metabolite-mediated cell-cell communication using MeboCost for metabolic signaling inference between cell types. Predict metabolite secretion and sensing patterns from scRNA-seq data. Use w...
```
import mebocost as mbc
import scanpy as sc

# Load scRNA-seq data
adata = sc.read_h5ad('adata.h5ad')

# Initialize MeboCost
mebo = mbc.create_obj(
    adata=adata,
    group_col='cell_type',  # Cell type annotation column
    species='human'  # 'human' or 'mouse'
)

# Infer metabolite communication
mebo.infer_commu(
    n_permutations=1000,  # Permutations for significance testing
    seed=42
)

# Get significant interactions
sig_interactions = mebo.commu_res[mebo.commu_res['pval'] < 0.05]
```

### bio-single-cell-multimodal-integration
**用途**: Analyze multi-modal single-cell data (CITE-seq, Multiome, spatial). Use when working with data that measures multiple modalities per cell like RNA + protein or RNA + ATAC. Use when analyzing CITE-s...
```
# Check how much each modality contributes per cell
weights <- obj@reductions$wnn@misc$weights

# Average weight by cluster
aggregate(weights, by = list(obj$seurat_clusters), mean)
```

### bio-single-cell-perturb-seq
**用途**: Analyze Perturb-seq and CROP-seq CRISPR screening data integrated with scRNA-seq. Use when identifying gene function through pooled genetic perturbations in single cells.
```
import decoupler as dc

# Get DE genes per perturbation
de_results = pb.results()

# Run pathway enrichment
dc.run_ora(
    mat=de_results,
    net=dc.get_resource('MSigDB'),
    source='geneset',
    target='gene'
)

# Visualize top pathways
dc.plot_barplot(de_results, 'TP53', top_n=20)
```

### bio-single-cell-preprocessing
**用途**: Quality control, filtering, and normalization for single-cell RNA-seq using Seurat (R) and Scanpy (Python). Use for calculating QC metrics, filtering cells and genes, normalizing counts, identifyin...
```
library(Seurat)
library(ggplot2)
```

### bio-single-cell-scatac-analysis
**用途**: Single-cell ATAC-seq analysis with Signac (R/Seurat) and ArchR. Process 10X Genomics scATAC data, perform QC, dimensionality reduction, clustering, peak calling, and motif activity scoring with chr...
```
BiocManager::install('chromVAR')
```

### bio-single-cell-splicing
**用途**: Analyzes alternative splicing at single-cell resolution using BRIE2 for probabilistic PSI estimation or leafcutter2 for cluster-based analysis with NMD detection. Identifies cell-type-specific spli...
```
import pandas as pd
import numpy as np

# For better statistical power, aggregate cells by type
def pseudobulk_junctions(junction_counts, cell_metadata, groupby='cell_type'):
    '''Aggregate junction counts by cell group.'''
    groups = cell_metadata.groupby(groupby).groups

    pseudobulk = {}
    for group, cells in groups.items():
        cell_mask = junction_counts.index.isin(cells)
        pseudobulk[group] = junction_counts.loc[cell_mask].sum()

    return pd.DataFrame(pseudobulk)

# Run
# ... (truncated)
```

### bio-single-cell-trajectory-inference
**用途**: Infer developmental trajectories and pseudotime from single-cell RNA-seq data using Monocle3, Slingshot, and scVelo for RNA velocity analysis. Use when inferring developmental trajectories or pseud...
```
# Generate loom file with spliced/unspliced counts
velocyto run10x -m repeat_mask.gtf /path/to/cellranger_output annotation.gtf

# For SmartSeq2
velocyto run_smartseq2 -o output -m repeat_mask.gtf -e sample bam_files/*.bam annotation.gtf
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

### bio-spatial-transcriptomics-image-analysis
**用途**: Process and analyze tissue images from spatial transcriptomics data using Squidpy. Extract image features, segment cells/nuclei, and compute morphological features from H&E or IF images. Use when p...
```
import squidpy as sq
import scanpy as sc
import numpy as np
import matplotlib.pyplot as plt
from skimage import io, filters, segmentation
```

### bio-spatial-transcriptomics-spatial-communication
**用途**: Analyze cell-cell communication in spatial transcriptomics data using ligand-receptor analysis with Squidpy. Infer intercellular signaling, identify communication pathways, and visualize interactio...
```
import squidpy as sq
import scanpy as sc
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
```

### bio-spatial-transcriptomics-spatial-data-io
**用途**: Load spatial transcriptomics data from Visium, Xenium, MERFISH, Slide-seq, and other platforms using Squidpy and SpatialData. Read Space Ranger outputs, convert formats, and access spatial coordina...
```
# Stereo-seq (BGI)
sdata = sdio.stereoseq('path/to/stereoseq/output/')
```

### bio-spatial-transcriptomics-spatial-deconvolution
**用途**: Estimate cell type composition in spatial transcriptomics spots using reference-based deconvolution. Use cell2location, RCTD, SPOTlight, or Tangram to infer cell type proportions from scRNA-seq ref...
```
import scanpy as sc
import anndata as ad
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
```

### bio-spatial-transcriptomics-spatial-domains
**用途**: Identify spatial domains and tissue regions in spatial transcriptomics data using Squidpy and Scanpy. Cluster spots considering both expression and spatial context to define anatomical regions. Use...
```
import squidpy as sq
import scanpy as sc
import numpy as np
import matplotlib.pyplot as plt
```

### bio-spatial-transcriptomics-spatial-multiomics
**用途**: Analyze high-resolution spatial platforms like Slide-seq, Stereo-seq, and Visium HD. Use when working with subcellular resolution or high-density spatial data.
```
# Visium HD produces bin files at multiple resolutions
# Load 8µm binned data (recommended starting point)
adata = sc.read_h5ad('visium_hd_8um.h5ad')

# Downsample to 16µm if needed for initial analysis
# Original 2µm data available for detailed analysis
```

### bio-spatial-transcriptomics-spatial-neighbors
**用途**: Build spatial neighbor graphs for spatial transcriptomics data using Squidpy. Compute k-nearest neighbors, Delaunay triangulation, and radius-based connectivity for downstream spatial analyses. Use...
```
import squidpy as sq
import scanpy as sc
import numpy as np
```

### bio-spatial-transcriptomics-spatial-preprocessing
**用途**: Quality control, filtering, normalization, and feature selection for spatial transcriptomics data. Calculate QC metrics, filter spots/cells, normalize counts, and identify highly variable genes. Us...
```
# Scale for PCA (use log-normalized data)
sc.pp.scale(adata, max_value=10)
```

### bio-spatial-transcriptomics-spatial-proteomics
**用途**: Analyzes spatial proteomics data from CODEX, IMC, and MIBI platforms including cell segmentation and protein colocalization. Use when working with multiplexed imaging data, analyzing protein spatia...
```
# Log transform intensities
sm.pp.log1p(adata)

# Rescale markers (0-1 per marker)
sm.pp.rescale(adata)

# Combat batch correction if multiple FOVs
sm.pp.combat(adata, batch_key='fov')
```

### bio-spatial-transcriptomics-spatial-statistics
**用途**: Compute spatial statistics for spatial transcriptomics data using Squidpy. Calculate Moran's I, Geary's C, spatial autocorrelation, co-occurrence analysis, and neighborhood enrichment. Use when com...
```
import squidpy as sq
import scanpy as sc
import pandas as pd
import numpy as np
```

### bio-spatial-transcriptomics-spatial-visualization
**用途**: Visualize spatial transcriptomics data using Squidpy and Scanpy. Create tissue plots with gene expression, clusters, and annotations overlaid on histology images. Use when visualizing spatial expre...
```
import squidpy as sq
import scanpy as sc
import matplotlib.pyplot as plt
```

### bio-splicing-pipeline
**用途**: 
```
FASTQ → Read QC → STAR 2-pass → Junction QC → rMATS-turbo → Results → Visualization
                                    ↓
                            (Optional) IsoformSwitchAnalyzeR
```

### bio-splicing-qc
**用途**: Assesses RNA-seq data quality for splicing analysis including junction saturation curves, splice site strength scoring, and junction coverage metrics using RSeQC. Use when evaluating data suitabili...
```
# Classify junctions as known, partial novel, or complete novel
junction_annotation.py \
    -i sample.bam \
    -r annotation.bed \
    -o sample_junc_annot
```

### bio-splicing-quantification
**用途**: Quantifies alternative splicing events (PSI/percent spliced in) from RNA-seq using SUPPA2 from transcript TPM or rMATS-turbo from BAM files. Calculates inclusion levels for skipped exons, alternati...
```
# rMATS-turbo for BAM-based quantification
rmats.py \
    --b1 condition1_bams.txt \
    --b2 condition2_bams.txt \
    --gtf annotation.gtf \
    -t paired \
    --readLength 150 \
    --nthread 8 \
    --od output_dir \
    --tmp tmp_dir \
    --statoff  # Use for quantification only, no differential testing
```

### bio-sra-data
**用途**: 
```
# Basic stats
sra-stat --quick SRR12345678

# Detailed XML output
sra-stat --xml SRR12345678
```

### bio-structural-biology-modern-structure-prediction
**用途**: Predict protein structures using modern ML models including AlphaFold3, ESMFold, Chai-1, and Boltz-1. Use when predicting structures for novel proteins, protein complexes, or when comparing predict...
```
pip install boltz
```

### bio-substructure-search
**用途**: Searches molecular libraries for substructure matches using SMARTS patterns with RDKit. Filters compounds by pharmacophore features, functional groups, or scaffold matches with atom mapping. Use wh...
```
from rdkit import Chem

mol = Chem.MolFromSmiles('c1ccc(O)cc1CCO')

# Check if pattern exists
pattern = Chem.MolFromSmarts('[OH]')  # Hydroxyl group
has_hydroxyl = mol.HasSubstructMatch(pattern)
print(f'Contains hydroxyl: {has_hydroxyl}')

# Get all matches (atom indices)
matches = mol.GetSubstructMatches(pattern)
print(f'Hydroxyl positions: {matches}')
```

### bio-systems-biology-context-specific-models
**用途**: 
```
def create_tissue_model(generic_model, gtex_expression, tissue='liver'):
    '''Create tissue-specific model from GTEx expression data

    GTEx provides median TPM for 54 human tissues.
    Download from: https://gtexportal.org/home/datasets
    '''
    import pandas as pd

    # Load GTEx median expression
    gtex = pd.read_csv(gtex_expression, sep='\t')

    # Extract tissue column
    tissue_col = [c for c in gtex.columns if tissue.lower() in c.lower()][0]
    expression = dict(zip(gtex['ge
# ... (truncated)
```

### bio-systems-biology-flux-balance-analysis
**用途**: 
```
from cobra.flux_analysis import loopless_solution

# Remove thermodynamically infeasible loops
# Important for realistic flux predictions

solution = loopless_solution(model)
```

### bio-systems-biology-gene-essentiality
**用途**: 
```
import cobra
from cobra.flux_analysis import single_gene_deletion

model = cobra.io.load_model('textbook')

# Perform all single gene deletions
# Returns growth rate with each gene knocked out
deletion_results = single_gene_deletion(model)

# deletion_results is a DataFrame with:
# - ids: gene IDs (frozenset)
# - growth: growth rate after deletion
# - status: solver status

# Find essential genes (no growth when deleted)
# Essential: growth < 0.01 (allowing for numerical tolerance)
essential = d
# ... (truncated)
```

### bio-systems-biology-metabolic-reconstruction
**用途**: 
```
# Install CarveMe
pip install carveme

# Basic reconstruction from protein FASTA
carve genome.faa -o model.xml

# Specify output format
carve genome.faa -o model.xml --format sbml
carve genome.faa -o model.json --format json

# Gap-fill for specific media
carve genome.faa -o model.xml --gapfill M9

# Available media: M9, LB, M9[glc], M9[glyc], etc.
```

### bio-systems-biology-model-curation
**用途**: 
```
# Install memote
pip install memote

# Run full quality report
memote report snapshot model.xml --filename report.html

# Quick score
memote run model.xml

# Continuous integration testing
memote run --pytest-args "--tb=short" model.xml
```

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

### bio-transcription-translation
**用途**: 
```
from Bio.Seq import Seq
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

### bio-uniprot-access
**用途**: 
```
# Human kinases with structures
query = 'organism_id:9606 AND keyword:kinase AND database:pdb AND reviewed:true'
results = search_uniprot(query, size=100)
```

### bio-variant-annotation
**用途**: Comprehensive variant annotation using bcftools annotate/csq, VEP, SnpEff, and ANNOVAR. Add database annotations, predict functional consequences, and assess clinical significance. Use when annotat...
```
snpEff ann GRCh38.105 input.vcf > output.vcf
```

### bio-variant-calling
**用途**: Call SNPs and indels from aligned reads using bcftools mpileup and call. Use when detecting variants from BAM files or generating VCF from alignments.
```
bcftools mpileup -f reference.fa input.bam | bcftools call -mv -o variants.vcf
```

### bio-variant-calling-clinical-interpretation
**用途**: Clinical variant interpretation using ClinVar, ACMG guidelines, and pathogenicity predictors. Prioritize variants for diagnostic and research applications. Use when interpreting clinical significan...
```
git clone https://github.com/WGLab/InterVar.git
cd InterVar
# Download databases per documentation
```

### bio-variant-calling-deepvariant
**用途**: Deep learning-based variant calling with Google DeepVariant. Provides high accuracy for germline SNPs and indels from Illumina, PacBio, and ONT data. Use when calling variants with DeepVariant deep...
```
singularity pull docker://google/deepvariant:1.6.1
```

### bio-variant-calling-filtering-best-practices
**用途**: Comprehensive variant filtering including GATK VQSR, hard filters, bcftools expressions, and quality metric interpretation for SNPs and indels. Use when filtering variants using GATK best practices.
```
bcftools view -r chr1:1000000-2000000 input.vcf.gz -o region.vcf.gz

# Multiple regions
bcftools view -r chr1:1000-2000,chr2:3000-4000 input.vcf.gz
```

### bio-variant-calling-joint-calling
**用途**: Joint genotype calling across multiple samples using GATK CombineGVCFs and GenotypeGVCFs. Essential for cohort studies, population genetics, and leveraging VQSR. Use when performing joint genotypin...
```
gatk GenotypeGVCFs \
    -R reference.fa \
    -V cohort.g.vcf.gz \
    -O cohort.vcf.gz
```

### bio-variant-calling-structural-variant-calling
**用途**: Call structural variants (SVs) from short-read sequencing using Manta, Delly, and LUMPY. Detects deletions, insertions, inversions, duplications, and translocations that are too large for standard ...
```
# AnnotSV annotation
AnnotSV \
    -SVinputFile svs.vcf \
    -genomeBuild GRCh38 \
    -outputFile annotated_svs

# Output includes: genes, DGV, gnomAD-SV, ClinVar
```

### bio-variant-normalization
**用途**: Normalize indel representation and split multiallelic variants using bcftools norm. Use when comparing variants from different callers or preparing VCF for downstream analysis.
```
chr1  100  .  ATG  GCA  30  PASS
```

### bio-vcf-basics
**用途**: View, query, and understand VCF/BCF variant files using bcftools and cyvcf2. Use when inspecting variants, extracting specific fields, or understanding VCF format structure.
```
bcftools view -h input.vcf.gz
```

### bio-vcf-manipulation
**用途**: Merge, concatenate, sort, intersect, and subset VCF files using bcftools. Use when combining variant files, comparing call sets, or restructuring VCF data.
```
bcftools sort input.vcf -Oz -o sorted.vcf.gz
```

### bio-vcf-statistics
**用途**: Generate variant statistics, sample concordance, and quality metrics using bcftools stats and gtcheck. Use when evaluating variant quality, comparing samples, or summarizing VCF contents.
```
bcftools query -l input.vcf.gz
```

### bio-virtual-screening
**用途**: Performs structure-based virtual screening using AutoDock Vina 1.2 for molecular docking. Prepares receptor PDBQT files, generates ligand conformers, defines binding site boxes, and ranks compounds...
```
from rdkit import Chem
from rdkit.Chem import AllChem

def prepare_ligand(smiles, output_pdbqt):
    '''
    Prepare ligand for docking.
    Steps: Generate 3D -> Minimize -> Assign charges -> PDBQT
    '''
    mol = Chem.MolFromSmiles(smiles)
    mol = Chem.AddHs(mol)

    # Generate 3D conformer (ETKDGv3 is default in modern RDKit)
    AllChem.EmbedMolecule(mol, AllChem.ETKDGv3())

    # Minimize with MMFF
    AllChem.MMFFOptimizeMolecule(mol)

    # Write to MOL file
    mol_file = output_pdb
# ... (truncated)
```

### bio-workflow-management-cwl-workflows
**用途**: 
```
# Run with Docker
cwltool --docker workflow.cwl job.yaml

# Run with Singularity
cwltool --singularity workflow.cwl job.yaml
```

### bio-workflow-management-nextflow-pipelines
**用途**: 
```
process ALIGN {
    label 'process_high'
    // ...
}
```

### bio-workflow-management-snakemake-workflows
**用途**: 
```
# Run with Singularity
snakemake --use-singularity --singularity-args "-B /data"
```

### bio-workflow-management-wdl-workflows
**用途**: 
```
{
    "rnaseq.fastq_1": "data/sample1_R1.fq.gz",
    "rnaseq.fastq_2": "data/sample1_R2.fq.gz",
    "rnaseq.salmon_index": "ref/salmon_index",
    "rnaseq.threads": 8
}
```

### bio-workflows-atacseq-pipeline
**用途**: 
```
# Convert to BED and shift
bedtools bamtobed -i aligned/${sample}.dedup.bam | \
    awk 'BEGIN{OFS="\t"} {if($6=="+"){$2=$2+4} else if($6=="-"){$3=$3-5} print}' | \
    sort -k1,1 -k2,2n > aligned/${sample}.shifted.bed
```

### bio-workflows-biomarker-pipeline
**用途**: 
```
import pandas as pd
import joblib

# Save biomarker panel
feature_names = X_train.columns[selected_idx].tolist()
pd.DataFrame({'feature': feature_names}).to_csv('biomarker_panel.csv', index=False)

# Save model and scaler for deployment
joblib.dump(clf, 'biomarker_classifier.joblib')
joblib.dump(scaler, 'feature_scaler.joblib')
```

### bio-workflows-chipseq-pipeline
**用途**: 
```
FASTQ files (IP + Input)
    |
    v
[1. QC & Trimming] -----> fastp
    |
    v
[2. Alignment] ---------> Bowtie2
    |
    v
[3. BAM Processing] ----> sort, markdup, filter
    |
    v
[4. Peak Calling] ------> MACS3
    |
    v
[5. QC] ----------------> FRiP, fingerprint plots
    |
    v
[6. Annotation] --------> ChIPseeker
    |
    v
Annotated peaks + QC report
```

### bio-workflows-clip-pipeline
**用途**: 
```
FASTQ → QC → UMI extract → Trim adapters → Align → Filter → Dedup → Peak call → Annotate → Motifs
```

### bio-workflows-cnv-pipeline
**用途**: 
```
# For each sample
for bam in *.bam; do
    sample=$(basename $bam .bam)

    # Target coverage
    cnvkit.py coverage $bam targets.bed \
        -o coverage/${sample}.targetcoverage.cnn

    # Antitarget coverage
    cnvkit.py coverage $bam antitargets.bed \
        -o coverage/${sample}.antitargetcoverage.cnn
done
```

### bio-workflows-crispr-editing-pipeline
**用途**: 
```
pip install crisprscan biopython pandas numpy matplotlib

conda install -c bioconda primer3-py cas-offinder

# Python packages for scoring
pip install crisprtools  # if available
```

### bio-workflows-crispr-screen-pipeline
**用途**: 
```
# For enrichment screens (e.g., drug resistance)
mageck test \
    -k counts.txt \
    -t Resistant_Rep1,Resistant_Rep2 \
    -c Sensitive \
    -n positive_screen \
    --gene-lfc-method alphamedian
```

### bio-workflows-cytometry-pipeline
**用途**: 
```
# CyTOF-specific settings
sce <- prepData(fs, panel, md,
                transform = TRUE,
                cofactor = 5,  # CyTOF uses cofactor 5
                FACS = FALSE)  # Not flow cytometry

# Bead normalization should be done upstream (Fluidigm software)
```

### bio-workflows-expression-to-pathways
**用途**: 
```
library(ReactomePA)

reactome <- enrichPathway(gene = sig_entrez$ENTREZID,
                          organism = 'human',
                          pvalueCutoff = 0.05,
                          readable = TRUE)
```

### bio-workflows-fastq-to-variants
**用途**: 
```
samtools flagstat aligned/${sample}.bam
```

### bio-workflows-genome-assembly-pipeline
**用途**: 
```
# NanoPlot for long-read QC
NanoPlot --fastq reads.fastq.gz \
    --outdir nanoplot_output \
    --threads 8
```

### bio-workflows-gwas-pipeline
**用途**: 
```
# Calculate principal components
plink2 --bfile study_pruned \
    --pca 10 \
    --out study_pca

# The eigenvec file contains PCs for use as covariates
```

### bio-workflows-hic-pipeline
**用途**: 
```
import cooler
import cooltools

# Load matrix
clr = cooler.Cooler('sample.mcool::resolutions/10000')

# Balance (ICE normalization)
cooltools.balance_cooler(clr, store=True, mad_max=5)

# Or via command line
# cooler balance sample.mcool::resolutions/10000
```

### bio-workflows-imc-pipeline
**用途**: 
```
# Spatial interactions with tumor
tumor_cells = adata[adata.obs['cell_type'] == 'Tumor'].obs_names
sq.gr.ligrec(adata, cluster_key='cell_type', source_groups=['Tumor'],
             target_groups=['T cells', 'Macrophages'])
```

### bio-workflows-longread-sv-pipeline
**用途**: 
```
samtools flagstat aligned.bam
samtools depth -a aligned.bam | awk '{sum+=$3} END {print "Average coverage:",sum/NR}'
```

### bio-workflows-merip-pipeline
**用途**: 
```
FASTQ → QC → Align IP+Input → Peak calling → Annotation → Differential → Visualization
```

### bio-workflows-metabolic-modeling-pipeline
**用途**: 
```
pip install cobra carveme memote escher pandas numpy matplotlib seaborn

conda install -c bioconda diamond
```

### bio-workflows-metabolomics-pipeline
**用途**: 
```
# Adjust peak width for lipids
cwp_lipid <- CentWaveParam(
    peakwidth = c(10, 60),  # Broader peaks
    ppm = 15,
    snthresh = 5
)

# Use LipidMaps for annotation
```

### bio-workflows-metagenomics-pipeline
**用途**: 
```
# Classify reads
for sample in sample1 sample2 sample3; do
    kraken2 --db kraken2_db \
        --threads 8 \
        --paired \
        --report kraken/${sample}.report \
        --output kraken/${sample}.output \
        host_removed/${sample}_R1.fq.gz \
        host_removed/${sample}_R2.fq.gz
done
```

### bio-workflows-methylation-pipeline
**用途**: 
```
deduplicate_bismark \
    --bam \
    -p \
    -o deduplicated/ \
    aligned/sample_R1_val_1_bismark_bt2_pe.bam
```

### bio-workflows-microbiome-pipeline
**用途**: 
```
# V3-V4 (~460bp): truncLen = c(280, 200)
# V4 (~253bp): truncLen = c(240, 160)
# V1-V3 (~500bp): truncLen = c(260, 220)
```

### bio-workflows-multi-omics-pipeline
**用途**: 
```
# MOFA+ for single-cell
library(MOFA2)
mofa <- create_mofa_from_Seurat(seurat_obj, groups = 'cell_type',
                                 assays = c('RNA', 'ATAC'))
```

### bio-workflows-multiome-pipeline
**用途**: 
```
# QC metrics
seurat_obj[['percent.mt']] <- PercentageFeatureSet(seurat_obj, pattern = '^MT-')

# Filter
seurat_obj <- subset(seurat_obj,
    nCount_RNA > 1000 &
    nCount_RNA < 25000 &
    percent.mt < 20
)

# Normalize RNA
seurat_obj <- SCTransform(seurat_obj, assay = 'RNA', verbose = FALSE)

# PCA
seurat_obj <- RunPCA(seurat_obj, assay = 'SCT', verbose = FALSE)
```

### bio-workflows-neoantigen-pipeline
**用途**: 
```
pip install pvactools mhcflurry vatools

mhcflurry-downloads fetch

conda install -c bioconda vep arcashla optitype
```

### bio-workflows-outbreak-pipeline
**用途**: 
```
conda install -c bioconda mlst abricate snippy iqtree fasttree

pip install treetime transphylo biopython pandas matplotlib

# R packages for TransPhylo
Rscript -e "install.packages('TransPhylo')"
```

### bio-workflows-proteomics-pipeline
**用途**: 
```
# Load DIA-NN report
diann <- read.delim('report.tsv')

# Pivot to matrix
library(tidyr)
protein_matrix <- diann %>%
    select(Protein.Group, Run, PG.MaxLFQ) %>%
    pivot_wider(names_from = Run, values_from = PG.MaxLFQ)

# Then proceed with normalization and limma
```

### bio-workflows-riboseq-pipeline
**用途**: 
```
FASTQ → Preprocessing → rRNA removal → Alignment → P-site → TE → ORF calling
```

### bio-workflows-rnaseq-to-de
**用途**: 
```
# Count reads per gene
featureCounts -T 8 -p --countReadPairs \
    -a genes.gtf \
    -o counts.txt \
    aligned/*_Aligned.sortedByCoord.out.bam
```

### bio-workflows-scrnaseq-pipeline
**用途**: 
```
# SCTransform (recommended for most analyses)
seurat_obj <- SCTransform(seurat_obj, vars.to.regress = 'percent.mt', verbose = FALSE)
```

### bio-workflows-smrna-pipeline
**用途**: 
```
FASTQ → cutadapt trim → miRDeep2 → Quantification → DESeq2 → Target prediction
```

### bio-workflows-somatic-variant-pipeline
**用途**: 
```
gatk LearnReadOrientationModel \
    -I f1r2.tar.gz \
    -O read-orientation-model.tar.gz
```

### bio-workflows-spatial-pipeline
**用途**: 
```
# Gene expression in space
genes = ['EPCAM', 'VIM', 'PTPRC', 'COL1A1']
sc.pl.spatial(adata, color=genes, ncols=2, spot_size=1.5, cmap='viridis')
plt.savefig('marker_genes_spatial.pdf')

# Cluster markers in space
sc.tl.rank_genes_groups(adata, 'leiden', method='wilcoxon')
sc.pl.rank_genes_groups_dotplot(adata, n_genes=5)
plt.savefig('cluster_markers.pdf')

# Save
adata.write('spatial_analyzed.h5ad')
```

### bio-workflows-tcr-pipeline
**用途**: 
```
FASTQ → MiXCR align → Assemble → Export → VDJtools diversity → Visualization
```

### bio-write-sequences
**用途**: Write biological sequences to files (FASTA, FASTQ, GenBank, EMBL) using Biopython Bio.SeqIO. Use when saving sequences, creating new sequence files, or outputting modified records.
```
SeqIO.write(records, 'output.fasta', 'fasta')
```
