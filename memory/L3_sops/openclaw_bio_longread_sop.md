# gptomics 长读长测序 SOP
> 长读长比对、QC、Medaka、结构变异
> 包含 4 个 OpenClaw skill 的压缩迁移。

---

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
