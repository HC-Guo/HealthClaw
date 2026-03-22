# 其他医疗与科研技能 SOP
> 未归入主要类别的专业技能
> 包含 91 个 OpenClaw skill 的压缩迁移。

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

### bio-blast-searches
**用途**: 
```
from Bio.Blast import NCBIWWW, NCBIXML
from Bio import SeqIO
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

### bio-codon-usage
**用途**: 
```
def find_rare_codons(seq, threshold=0.1):
    freq = codon_frequencies(seq)
    return {codon: f for codon, f in freq.items() if f < threshold}
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

### bio-geo-data
**用途**: 
```
from Bio import Entrez

Entrez.email = 'your.email@example.com'  # Required by NCBI
Entrez.api_key = 'your_api_key'          # Optional
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

### bio-paired-end-fastq
**用途**: Handle paired-end FASTQ files (R1/R2) using Biopython. Use when working with Illumina paired reads, synchronizing pairs, interleaving/deinterleaving, or filtering paired data.
```
from Bio import SeqIO
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

### bio-pileup-generation
**用途**: 
```
samtools mpileup -f reference.fa -q 20 input.bam
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

### bio-write-sequences
**用途**: Write biological sequences to files (FASTA, FASTQ, GenBank, EMBL) using Biopython Bio.SeqIO. Use when saving sequences, creating new sequence files, or outputting modified records.
```
SeqIO.write(records, 'output.fasta', 'fasta')
```

### epigenomics-methylgpt-agent
**用途**: 
```
python3 Skills/Genomics/Epigenomics_MethylGPT_Agent/methylgpt_analyzer.py \
    --input tumor_normal_methylation.csv \
    --groups tumor,normal \
    --model methylgpt-base \
    --analysis dmr \
    --min_cpgs 5 \
    --delta_beta 0.2 \
    --output dmr_results.json
```

### gwas-prs
**用途**: Calculate polygenic risk scores from DTC genetic data using the PGS Catalog
```
PRS = SUM(dosage_i * beta_i)
```

### phylogenetics
**用途**: Build and analyze phylogenetic trees using MAFFT (multiple alignment), IQ-TREE 2 (maximum likelihood), and FastTree (fast NJ/ML). Visualize with ETE3 or FigTree. For evolutionary analysis, microbia...
```
# Conda (recommended for CLI tools)
conda install -c bioconda mafft iqtree fasttree
pip install ete3
```
**注意**: **Alignment quality first**: Poor alignment → unreliable trees; check alignment manually; **Use `linsi` for small (<200 seq), `fftns` or `auto` for large alignments**; **Model selection**: Always use `-m TEST` for IQ-TREE unless you have a specific reason

### uspto-database
**用途**: Access USPTO APIs for patent/trademark searches, examination history (PEDS), assignments, citations, office actions, TSDR, for IP analysis and prior art searches.
```
uv pip install uspto-opendata-python
```
**注意**: - Store API key in environment variables; Never commit keys to version control; Use same key across all USPTO APIs
