# 宏基因组学与微生物组 SOP
> 宏基因组分析、微生物组、16S/ITS
> 包含 2 个 OpenClaw skill 的压缩迁移。

---

### claw-metagenomics
**用途**: Shotgun metagenomics profiling — taxonomy, resistome, and functional pathways
```
python metagenomics_profiler.py --demo --output demo_report
```

### lobster-bioinformatics
**用途**: Run bioinformatics analyses using Lobster AI - single-cell RNA-seq, bulk RNA-seq, literature mining, dataset discovery, quality control, and visualization. Use when analyzing genomics data, searchi...
```
lobster config-test --json
```
**限制**: Lobster requires active LLM provider (Ollama/Anthropic/Bedrock); Large datasets (>100K cells) may be slow depending on system resources
