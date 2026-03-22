# gptomics CRISPR 筛选 SOP
> CRISPR 文库分析、essentiality scoring、引物设计
> 包含 11 个 OpenClaw skill 的压缩迁移。

---

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
