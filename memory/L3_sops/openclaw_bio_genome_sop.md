# gptomics 基因组组装与工程 SOP
> 基因组组装、基因组工程、比较基因组学、基因组区间
> 包含 24 个 OpenClaw skill 的压缩迁移。

---

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
