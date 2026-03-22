# gptomics 序列操作 SOP
> 序列读写、过滤、切片、反向互补、翻译、相似性搜索、BLAST
> 包含 16 个 OpenClaw skill 的压缩迁移。

---

### bio-blast-searches
**用途**: 
```
from Bio.Blast import NCBIWWW, NCBIXML
from Bio import SeqIO
```

### bio-codon-usage
**用途**: 
```
def find_rare_codons(seq, threshold=0.1):
    freq = codon_frequencies(seq)
    return {codon: f for codon, f in freq.items() if f < threshold}
```

### bio-consensus-sequences
**用途**: Generate consensus FASTA sequences by applying VCF variants to a reference using bcftools consensus. Use when creating sample-specific reference sequences or reconstructing haplotypes.
```
# Number of differences
bcftools view -H input.vcf.gz | wc -l
```

### bio-filter-sequences
**用途**: Filter and select sequences by criteria (length, ID, GC content, patterns) using Biopython. Use when subsetting sequences, removing unwanted records, or selecting by specific criteria.
```
from Bio import SeqIO
from Bio.SeqUtils import gc_fraction
```

### bio-local-blast
**用途**: 
```
blastn -query query.fa -db my_db -outfmt "6 qseqid sseqid pident length evalue stitle"
```

### bio-motif-search
**用途**: 
```
from Bio.Seq import Seq
from Bio import motifs
import re
```

### bio-read-sequences
**用途**: Read biological sequence files (FASTA, FASTQ, GenBank, EMBL, ABI, SFF) using Biopython Bio.SeqIO. Use when parsing sequence files, iterating multi-sequence files, random access to large files, or h...
```
from Bio import SeqIO
```

### bio-reverse-complement
**用途**: 
```
from Bio.Seq import Seq
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

### bio-transcription-translation
**用途**: 
```
from Bio.Seq import Seq
```

### bio-write-sequences
**用途**: Write biological sequences to files (FASTA, FASTQ, GenBank, EMBL) using Biopython Bio.SeqIO. Use when saving sequences, creating new sequence files, or outputting modified records.
```
SeqIO.write(records, 'output.fasta', 'fasta')
```
