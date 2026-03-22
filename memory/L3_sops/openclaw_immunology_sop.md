# 免疫学与免疫库分析 SOP
> TCR/BCR 分析、CRISPR 筛选、免疫库测序
> 包含 2 个 OpenClaw skill 的压缩迁移。

---

### tooluniverse-crispr-screen-analysis
**用途**: Comprehensive CRISPR screen analysis for functional genomics. Analyze pooled or arrayed CRISPR screens (knockout, activation, interference) to identify essential genes, synthetic lethal interaction...
```
def filter_low_count_sgrnas(count_matrix, sgrna_to_gene, min_reads=30, min_samples=2):
    """
    Remove sgRNAs with insufficient read counts.
    """
    # Keep sgRNAs with >= min_reads in >= min_samples
    keep_mask = (count_matrix >= min_reads).sum(axis=1) >= min_samples

    filtered_counts = count_matrix[keep_mask].copy()
    filtered_mapping = {k: v for k, v in sgrna_to_gene.items() if k in filtered_counts.index}

    print(f"Filtered: {(~keep_mask).sum()} sgRNAs removed, {keep_mask.sum(
# ... (truncated)
```

### tooluniverse-immune-repertoire-analysis
**用途**: Comprehensive immune repertoire analysis for T-cell and B-cell receptor sequencing data. Analyze TCR/BCR repertoires to assess clonality, diversity, V(D)J gene usage, CDR3 characteristics, converge...
```
# Minimal workflow
from tooluniverse import ToolUniverse

# 1. Load data
tcr_data = load_airr_data("clonotypes.txt", format='mixcr')

# 2. Define clonotypes
clonotypes = define_clonotypes(tcr_data, method='vj_cdr3')

# 3. Calculate diversity
diversity = calculate_diversity(clonotypes['count'])
print(f"Shannon entropy: {diversity['shannon_entropy']:.2f}")

# 4. Detect expanded clones
expansion = detect_expanded_clones(clonotypes)
print(f"Expanded clonotypes: {expansion['n_expanded']}")

# 5. Anal
# ... (truncated)
```
