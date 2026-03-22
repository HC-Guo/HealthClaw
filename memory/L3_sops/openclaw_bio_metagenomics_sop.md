# gptomics 宏基因组与微生物组 SOP
> 宏基因组分析、16S/ITS、微生物组、多样性
> 包含 13 个 OpenClaw skill 的压缩迁移。

---

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
