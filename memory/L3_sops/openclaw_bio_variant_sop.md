# gptomics 变异检测 SOP
> 变异检测、拷贝数变异、相位/填充、群体遗传学
> 包含 20 个 OpenClaw skill 的压缩迁移。

---

### bio-copy-number-cnv-annotation
**用途**: Annotate CNVs with genes, pathways, and clinical significance. Use when interpreting CNV calls or identifying affected genes from copy number analysis.
```
# Annotate during analysis
cnvkit.py batch tumor.bam --normal normal.bam \
    --targets targets.bed \
    --annotate refFlat.txt \
    --fasta reference.fa \
    -o results/

# Genes are included in output CNS file
```

### bio-copy-number-cnv-visualization
**用途**: Visualize copy number profiles, segments, and compare across samples. Create publication-quality plots of CNV data from CNVkit, GATK, or other callers. Use when creating genome-wide CNV plots, samp...
```
# Scatter plot with segments
cnvkit.py scatter sample.cnr -s sample.cns -o scatter.png

# Scatter for specific chromosome
cnvkit.py scatter sample.cnr -s sample.cns -c chr17 -o chr17_scatter.png

# Ideogram diagram
cnvkit.py diagram sample.cnr -s sample.cns -o diagram.pdf

# Heatmap across samples
cnvkit.py heatmap *.cns -o cohort_heatmap.pdf

# Heatmap for specific region
cnvkit.py heatmap *.cns -c chr17:7500000-7700000 -o tp53_region.pdf
```

### bio-copy-number-cnvkit-analysis
**用途**: Detect copy number variants from targeted/exome sequencing using CNVkit. Supports tumor-normal pairs, tumor-only, and germline CNV calling. Use when detecting CNVs from WES or targeted panel sequen...
```
# For whole genome sequencing (no targets file)
cnvkit.py batch tumor.bam \
    --normal normal.bam \
    --fasta reference.fa \
    --method wgs \
    --output-dir results/
```

### bio-copy-number-gatk-cnv
**用途**: Call copy number variants using GATK best practices workflow. Supports both somatic (tumor-normal) and germline CNV detection from WGS or WES data. Use when following GATK best practices or integra...
```
gatk CallCopyRatioSegments \
    -I results/tumor.cr.seg \
    -O results/tumor.called.seg
```

### bio-phasing-imputation-genotype-imputation
**用途**: 
```
# PLINK2 with dosages
plink2 --vcf imputed.vcf.gz dosage=DS \
    --glm \
    --pheno phenotypes.txt \
    --out gwas_results
```

### bio-phasing-imputation-haplotype-phasing
**用途**: 
```
# Use reference panel for better phasing
java -jar beagle.22Jul22.46e.jar \
    gt=input.vcf.gz \
    ref=reference.vcf.gz \
    map=genetic_map.txt \
    out=phased \
    nthreads=8
```

### bio-phasing-imputation-imputation-qc
**用途**: 
```
# Calculate HWE p-values (PLINK2)
plink2 --vcf imputed.vcf.gz \
    --hardy \
    --out hwe_check

# Filter extreme HWE deviations
plink2 --vcf imputed.vcf.gz \
    --hwe 1e-6 \
    --make-pgen \
    --out imputed_hwe_filtered
```

### bio-phasing-imputation-reference-panels
**用途**: 
```
# IMPUTE5 uses its own format
imp5Converter \
    --h reference.vcf.gz \
    --r chr22 \
    --o reference.chr22.imp5
```

### bio-population-genetics-association-testing
**用途**: 
```
# Linear regression for quantitative traits
plink2 --bfile data --pheno pheno.txt --glm --out results
```

### bio-population-genetics-linkage-disequilibrium
**用途**: 
```
# ld_results.ld contains:
CHR_A  BP_A  SNP_A  CHR_B  BP_B  SNP_B  R2
```

### bio-population-genetics-plink-basics
**用途**: 
```
# update.txt: old_id new_id
plink2 --bfile input --update-name update.txt --make-bed --out output
```

### bio-population-genetics-population-structure
**用途**: 
```
# From conda
conda install -c bioconda flashpca

# Or download binaries from GitHub
# https://github.com/gabraham/flashpca
```

### bio-population-genetics-scikit-allel-analysis
**用途**: 
```
pip install scikit-allel
# Optional: zarr for chunked storage
pip install zarr
```

### bio-population-genetics-selection-statistics
**用途**: 
```
nsl = allel.nsl(h_flt)
nsl_std = allel.standardize_by_allele_count(nsl, ac_flt[:, 1])
```

### bio-variant-calling
**用途**: Call SNPs and indels from aligned reads using bcftools mpileup and call. Use when detecting variants from BAM files or generating VCF from alignments.
```
bcftools mpileup -f reference.fa input.bam | bcftools call -mv -o variants.vcf
```

### bio-variant-calling-clinical-interpretation
**用途**: Clinical variant interpretation using ClinVar, ACMG guidelines, and pathogenicity predictors. Prioritize variants for diagnostic and research applications. Use when interpreting clinical significan...
```
git clone https://github.com/WGLab/InterVar.git
cd InterVar
# Download databases per documentation
```

### bio-variant-calling-deepvariant
**用途**: Deep learning-based variant calling with Google DeepVariant. Provides high accuracy for germline SNPs and indels from Illumina, PacBio, and ONT data. Use when calling variants with DeepVariant deep...
```
singularity pull docker://google/deepvariant:1.6.1
```

### bio-variant-calling-filtering-best-practices
**用途**: Comprehensive variant filtering including GATK VQSR, hard filters, bcftools expressions, and quality metric interpretation for SNPs and indels. Use when filtering variants using GATK best practices.
```
bcftools view -r chr1:1000000-2000000 input.vcf.gz -o region.vcf.gz

# Multiple regions
bcftools view -r chr1:1000-2000,chr2:3000-4000 input.vcf.gz
```

### bio-variant-calling-joint-calling
**用途**: Joint genotype calling across multiple samples using GATK CombineGVCFs and GenotypeGVCFs. Essential for cohort studies, population genetics, and leveraging VQSR. Use when performing joint genotypin...
```
gatk GenotypeGVCFs \
    -R reference.fa \
    -V cohort.g.vcf.gz \
    -O cohort.vcf.gz
```

### bio-variant-calling-structural-variant-calling
**用途**: Call structural variants (SVs) from short-read sequencing using Manta, Delly, and LUMPY. Detects deletions, insertions, inversions, duplications, and translocations that are too large for standard ...
```
# AnnotSV annotation
AnnotSV \
    -SVinputFile svs.vcf \
    -genomeBuild GRCh38 \
    -outputFile annotated_svs

# Output includes: genes, DGV, gnomAD-SV, ClinVar
```
