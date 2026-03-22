# 临床医疗工具 SOP
> 临床报告、决策支持、FHIR、预授权、USMLE、患者文档、医学实体提取
> 包含 11 个 OpenClaw skill 的压缩迁移。

---

### clinical-decision-support
**用途**: Generate professional clinical decision support (CDS) documents for pharmaceutical and clinical research settings, including patient cohort analyses (biomarker-stratified with outcomes) and treatme...
**触发条件**: **Analyze patient cohorts** stratified by biomarkers, molecular subtypes, or clinical characteristics; **Generate treatment recommendation reports** with evidence grading for clinical guidelines or pharmaceutical strategies; **Compare outcomes** between patient subgroups with statistical analysis (survival, response rates, hazard ratios); **Produce pharmaceutical research documents** for drug development, clinical trials, or regulatory submissions
```
python scripts/generate_schematic.py "your diagram description" -o figures/output.png
```

### clinical-reports
**用途**: Write comprehensive clinical reports including case reports (CARE guidelines), diagnostic reports (radiology/pathology/lab), clinical trial reports (ICH-E3, SAE, CSR), and patient documentation (SO...
```
python scripts/generate_schematic.py "your diagram description" -o figures/output.png
```

### clinical-trial-protocol-skill
**用途**: Generate clinical trial protocols for medical devices or drugs. This skill should be used when users say "Create a clinical trial protocol", "Generate protocol for [device/drug]", "Help me design a...
```
pip install -r requirements.txt
```

### clinical-trials-search
**用途**: Search ClinicalTrials.gov with natural language queries. Find clinical trials, enrollment, and outcomes using Valyu semantic search.
```
scripts/search setup <api-key>
```

### clinicaltrials-database
**用途**: Query ClinicalTrials.gov via API v2. Search trials by condition, drug, location, status, or phase. Retrieve trial details by NCT ID, export data, for clinical research and patient matching.
```
python3 scripts/query_clinicaltrials.py
```

### fhir-developer-skill
**用途**: FHIR API development guide for building healthcare endpoints. Use when: (1) Creating FHIR REST endpoints (Patient, Observation, Encounter, Condition, MedicationRequest), (2) Validating FHIR resourc...
```
python scripts/setup_fhir_project.py my_fhir_api
```

### medical-entity-extractor
**用途**: Extract medical entities (symptoms, medications, lab values, diagnoses) from patient messages.
```
openclaw skill run medical-entity-extractor --input '[{"id":"msg-1","priority_score":78,...}]' --json
```

### medical-imaging-review
**用途**: Write comprehensive literature reviews for medical imaging AI research. Use when writing survey papers, systematic reviews, or literature analyses on topics like segmentation, detection, classifica...
```
Topic sentence (main claim)
  → Supporting evidence (citations + data)
  → Analysis (critical evaluation)
  → Transition to next paragraph
```

### patiently-ai
**用途**: Patiently AI simplifies medical documents for patients. Takes doctor's letters, test results, prescriptions, discharge summaries, and clinical notes and explains them in clear, personalised languag...

### prior-auth-review-skill
**用途**: Automate payer review of prior authorization (PA) requests. This skill should be used when users say "Review this PA request", "Process prior authorization for [procedure]", "Assess medical necessi...
```
Use the prior-auth-review-skill
```

### usmle
**用途**: Prepare for US medical licensing exams with progress tracking, weak area analysis, question bank management, and residency match planning.
```
~/usmle/
├── profile.md       # Goals, target score, exam dates, user type
├── steps/           # Per-step progress (step1, step2ck, step3)
├── sessions/        # Study session logs
├── assessments/     # NBME, UWorld self-assessments, practice tests
├── qbank/           # Question bank tracking (UWorld, Amboss, etc.)
└── feedback.md      # What works, what doesn't
```
