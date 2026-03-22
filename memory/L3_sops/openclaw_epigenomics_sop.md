# 表观基因组学 SOP
> 甲基化分析、染色质可及性、组蛋白修饰
> 包含 1 个 OpenClaw skill 的压缩迁移。

---

### tooluniverse-epigenomics
**用途**: Production-ready genomics and epigenomics data processing for BixBench questions. Handles methylation array analysis (CpG filtering, differential methylation, age-related CpG detection, chromosome-...
```
Input: BED/narrowPeak file
Question: "What fraction of peaks are in promoter regions?"

Flow:
1. Load BED file with load_bed_file()
2. Load or fetch gene annotation (Ensembl)
3. Run annotate_peaks_to_genes()
4. Classify regions with classify_peak_regions()
5. Calculate fraction in promoters
```
**限制**: **No native pybedtools**: Uses pure Python interval operations (slower for very large BED files); **No native pyBigWig**: Cannot read BigWig files directly without package
