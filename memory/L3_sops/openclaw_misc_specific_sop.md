# 补充专项技能 SOP
> GWAS-PRS、甲基化 GPT、系统发育、USPTO 专利
> 包含 4 个 OpenClaw skill 的压缩迁移。

---

### epigenomics-methylgpt-agent
**用途**: 
```
python3 Skills/Genomics/Epigenomics_MethylGPT_Agent/methylgpt_analyzer.py \
    --input tumor_normal_methylation.csv \
    --groups tumor,normal \
    --model methylgpt-base \
    --analysis dmr \
    --min_cpgs 5 \
    --delta_beta 0.2 \
    --output dmr_results.json
```

### gwas-prs
**用途**: Calculate polygenic risk scores from DTC genetic data using the PGS Catalog
```
PRS = SUM(dosage_i * beta_i)
```

### phylogenetics
**用途**: Build and analyze phylogenetic trees using MAFFT (multiple alignment), IQ-TREE 2 (maximum likelihood), and FastTree (fast NJ/ML). Visualize with ETE3 or FigTree. For evolutionary analysis, microbia...
```
# Conda (recommended for CLI tools)
conda install -c bioconda mafft iqtree fasttree
pip install ete3
```
**注意**: **Alignment quality first**: Poor alignment → unreliable trees; check alignment manually; **Use `linsi` for small (<200 seq), `fftns` or `auto` for large alignments**; **Model selection**: Always use `-m TEST` for IQ-TREE unless you have a specific reason

### uspto-database
**用途**: Access USPTO APIs for patent/trademark searches, examination history (PEDS), assignments, citations, office actions, TSDR, for IP analysis and prior art searches.
```
uv pip install uspto-opendata-python
```
**注意**: - Store API key in environment variables; Never commit keys to version control; Use same key across all USPTO APIs
