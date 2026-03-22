# gptomics VCF 与变异注释 SOP
> VCF 解析、操作、统计、变异注释、标准化、GATK
> 包含 6 个 OpenClaw skill 的压缩迁移。

---

### bio-gatk-variant-calling
**用途**: Variant calling with GATK HaplotypeCaller following best practices. Covers germline SNP/indel calling, GVCF workflow for cohorts, joint genotyping, and variant quality score recalibration (VQSR). U...
```
gatk HaplotypeCaller \
    -R reference.fa \
    -I sample.bam \
    -O sample.vcf.gz
```

### bio-variant-annotation
**用途**: Comprehensive variant annotation using bcftools annotate/csq, VEP, SnpEff, and ANNOVAR. Add database annotations, predict functional consequences, and assess clinical significance. Use when annotat...
```
snpEff ann GRCh38.105 input.vcf > output.vcf
```

### bio-variant-normalization
**用途**: Normalize indel representation and split multiallelic variants using bcftools norm. Use when comparing variants from different callers or preparing VCF for downstream analysis.
```
chr1  100  .  ATG  GCA  30  PASS
```

### bio-vcf-basics
**用途**: View, query, and understand VCF/BCF variant files using bcftools and cyvcf2. Use when inspecting variants, extracting specific fields, or understanding VCF format structure.
```
bcftools view -h input.vcf.gz
```

### bio-vcf-manipulation
**用途**: Merge, concatenate, sort, intersect, and subset VCF files using bcftools. Use when combining variant files, comparing call sets, or restructuring VCF data.
```
bcftools sort input.vcf -Oz -o sorted.vcf.gz
```

### bio-vcf-statistics
**用途**: Generate variant statistics, sample concordance, and quality metrics using bcftools stats and gtcheck. Use when evaluating variant quality, comparing samples, or summarizing VCF contents.
```
bcftools query -l input.vcf.gz
```
