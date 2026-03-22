# 生信流程与工具 SOP
> Biopython、nf-core、FASTQ 分析、DeepTools、GRN 推断、LaminDB
> 包含 12 个 OpenClaw skill 的压缩迁移。

---

### arboreto
**用途**: Infer gene regulatory networks (GRNs) from gene expression data using scalable algorithms (GRNBoost2, GENIE3). Use when analyzing transcriptomics data (bulk RNA-seq, single-cell RNA-seq) to identif...
```
uv pip install arboreto
```

### biopython
**用途**: Primary Python toolkit for molecular biology. Preferred for Python-based PubMed/NCBI queries (Bio.Entrez), sequence manipulation, file parsing (FASTA, GenBank, FASTQ, PDB), advanced BLAST workflows...
```
uv pip install biopython
```
**注意**: before writing code; for specific functions or examples; before parsing

### deeptools
**用途**: NGS analysis toolkit. BAM to bigWig conversion, QC (correlation, PCA, fingerprints), heatmaps/profiles (TSS, peaks), for ChIP-seq, RNA-seq, ATAC-seq visualization.
```
uv pip install deeptools
```

### dnanexus-integration
**用途**: DNAnexus cloud genomics platform. Build apps/applets, manage data (upload/download), dxpy Python SDK, run workflows, FASTQ/BAM/VCF, for genomics pipeline development and execution.
```
dx login
```

### etetoolkit
**用途**: Phylogenetic tree toolkit (ETE). Tree manipulation (Newick/NHX), evolutionary event detection, orthology/paralogy, NCBI taxonomy, visualization (PDF/SVG), for phylogenomics.
```
ncbi.update_taxonomy_database()  # Download latest NCBI data
```

### fastq-analysis-pipeline
**用途**: Guide through omicverse's alignment module for SRA downloading, FASTQ quality control, STAR alignment, gene quantification, and single-cell kallisto/bustools pipelines covering both bulk and single...
```
bam_items = [
       (r['sample'], r['bam'])
       for r in (bams if isinstance(bams, list) else [bams])
       if 'bam' in r
   ]
```

### geniml
**用途**: This skill should be used when working with genomic interval data (BED files) for machine learning tasks. Use for training region embeddings (Region2Vec, BEDspace), single-cell ATAC-seq analysis (s...
```
uv uv pip install geniml
```

### gtars
**用途**: High-performance toolkit for genomic interval analysis in Rust with Python bindings. Use when working with genomic regions, BED files, coverage tracks, overlap detection, tokenization for ML models...
```
uv uv pip install gtars
```

### lamindb
**用途**: This skill should be used when working with LaminDB, an open-source data framework for biology that makes data queryable, traceable, reproducible, and FAIR. Use when managing biological datasets (s...
```
# In Nextflow process script
import lamindb as ln

ln.track()

# Load input artifact
input_artifact = ln.Artifact.get(key="raw/batch_${batch_id}.fastq.gz")
input_path = input_artifact.cache()

# Process (alignment, quantification, etc.)
# ... Nextflow process logic ...

# Save output
output_artifact = ln.Artifact(
    "counts.csv",
    key="processed/batch_${batch_id}_counts.csv"
).save()

ln.finish()
```

### latchbio-integration
**用途**: Latch platform for bioinformatics workflows. Build pipelines with Latch SDK, @workflow/@task decorators, deploy serverless workflows, LatchFile/LatchDir, Nextflow/Snakemake integration.
```
# Install Latch SDK
python3 -m uv pip install latch

# Login to Latch
latch login

# Initialize a new workflow
latch init my-workflow

# Register workflow to platform
latch register my-workflow
```

### nextflow-development
**用途**: Run nf-core bioinformatics pipelines (rnaseq, sarek, atacseq) on sequencing data. Use when analyzing RNA-seq, WGS/WES, or ATAC-seq data—either local FASTQs or public datasets from GEO/SRA. Triggers...
```
python scripts/check_environment.py
```

### scikit-bio
**用途**: Biological data toolkit. Sequence analysis, alignments, phylogenetic trees, diversity metrics (alpha/beta, UniFrac), ordination (PCoA), PERMANOVA, FASTA/Newick I/O, for microbiome analysis.
```
uv pip install scikit-bio
```
