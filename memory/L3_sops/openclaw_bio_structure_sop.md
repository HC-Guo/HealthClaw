# gptomics 结构生物学 SOP
> PDB 结构分析、系统发育树、结构生物学
> 包含 6 个 OpenClaw skill 的压缩迁移。

---

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

### bio-structural-biology-modern-structure-prediction
**用途**: Predict protein structures using modern ML models including AlphaFold3, ESMFold, Chai-1, and Boltz-1. Use when predicting structures for novel proteins, protein complexes, or when comparing predict...
```
pip install boltz
```
