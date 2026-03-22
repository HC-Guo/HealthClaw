# ClawBio 编排管道 SOP
> scRNA 编排、GWAS 管道、祖先分析、药物基因组学、结构生物学文献综合
> 包含 3 个 OpenClaw skill 的压缩迁移。

---

### bio-orchestrator
**用途**: Meta-agent that routes bioinformatics requests to specialised sub-skills. Handles file type detection, analysis planning, report generation, and reproducibility export.
```
# Analysis Report: [Title]

**Date**: [ISO date]
**Skill(s) used**: [list]
**Input files**: [list with checksums]

## Methods
[Tool versions, parameters, reference genomes used]

## Results
[Tables, figures, key findings]

## Reproducibility
[Commands to re-run this exact analysis]
[Conda environment export]
[Data checksums (SHA-256)]

## References
[Software citations in BibTeX]
```

### scrna-orchestrator
**用途**: Local Scanpy pipeline for single-cell RNA-seq QC, clustering, marker discovery, and optional two-group differential expression from raw-count .h5ad.
```
python clawbio.py run scrna --demo
```

### simulation-orchestrator
**用途**: Orchestrate multi-simulation campaigns including parameter sweeps, batch jobs, and result aggregation. Use for running parameter studies, managing simulation batches, tracking job status, combining...
```
python3 scripts/job_tracker.py \
    --campaign-dir ./campaign_001 \
    --update \
    --json
```
**限制**: **Not a job scheduler**: Does not submit jobs to SLURM/PBS; generates configs and tracks status; **No parallel execution**: User must run simulations externally (can use GNU parallel, SLURM, etc.)
