# gptomics 剪接与亚型分析 SOP
> 差异剪接、剪接定量、亚型转换、sashimi 图
> 包含 6 个 OpenClaw skill 的压缩迁移。

---

### bio-differential-splicing
**用途**: Detects differential alternative splicing between conditions using rMATS-turbo (BAM-based) or SUPPA2 diffSplice (TPM-based). Reports events with FDR-corrected significance and delta PSI effect size...
```
# Prioritize by effect size and significance
significant['score'] = -np.log10(significant['FDR']) * significant['IncLevelDifference'].abs()
top_events = significant.nlargest(50, 'score')

# Annotate with gene function
# Consider protein domain disruption, NMD sensitivity
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
