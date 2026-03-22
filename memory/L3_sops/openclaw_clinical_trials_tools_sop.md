# 临床试验设计与匹配 SOP
> 试验可行性评估、患者匹配、指南检索
> 包含 3 个 OpenClaw skill 的压缩迁移。

---

### tooluniverse-clinical-guidelines
**用途**: Search and retrieve clinical practice guidelines across 12+ authoritative sources including NICE, WHO, ADA, AHA/ACC, NCCN, SIGN, CPIC, CMA, CTFPHC, GIN, MAGICapp, PubMed, EuropePMC, TRIP, and OpenA...
**触发条件**: "What are the guidelines for [condition]?"; "What does [ADA/AHA/NCCN/NICE/WHO] say about [topic]?"; "Standard of care for [disease]?"; "Drug-gene interactions for [drug/gene]?" (pharmacogenomics)
```
from tooluniverse import ToolUniverse
tu = ToolUniverse()
tu.load_tools()
assert hasattr(tu.tools, 'NICE_Clinical_Guidelines_Search')
```

### tooluniverse-clinical-trial-design
**用途**: Strategic clinical trial design feasibility assessment using ToolUniverse. Evaluates patient population sizing, biomarker prevalence, endpoint selection, comparator analysis, safety monitoring, and...
```
# BAD
EGFR L858R prevalence: 7% of NSCLC
```

### tooluniverse-clinical-trial-matching
**用途**: AI-driven patient-to-trial matching for precision medicine and oncology. Given a patient profile (disease, molecular alterations, stage, prior treatments), discovers and ranks clinical trials from ...
**触发条件**: "What clinical trials are available for my NSCLC with EGFR L858R?"; "Patient has BRAF V600E melanoma, failed ipilimumab - what trials?"; "Find basket trials for NTRK fusion"; "Breast cancer with HER2 amplification, post-CDK4/6 inhibitor trials"
```
clinical_trial_matching_[DISEASE]_[BIOMARKER]_[DATE].md
```
