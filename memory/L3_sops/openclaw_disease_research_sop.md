# 疾病研究与精准医学 SOP
> 疾病研究报告、罕见病诊断、精准肿瘤学、免疫治疗响应预测
> 包含 6 个 OpenClaw skill 的压缩迁移。

---

### tooluniverse-disease-research
**用途**: Generate comprehensive disease research reports using 100+ ToolUniverse tools. Creates a detailed markdown report file and progressively updates it with findings from 10 research dimensions. All in...
**触发条件**: Asks about any disease, syndrome, or medical condition; Needs comprehensive disease intelligence; Wants a detailed research report with citations; Asks "what do we know about [disease]?"
```
tu.tools.OpenTargets_get_similar_entities_by_disease_efoId(efoId=efo_id, threshold=0.3, size=30)
```

### tooluniverse-immunotherapy-response-prediction
**用途**: Predict patient response to immune checkpoint inhibitors (ICIs) using multi-biomarker integration. Given a cancer type, somatic mutations, and optional biomarkers (TMB, PD-L1, MSI status), performs...
**触发条件**: "Will this patient respond to immunotherapy?"; "Should I give pembrolizumab to this melanoma patient?"; "Patient has NSCLC with TMB 25, PD-L1 80% - predict ICI response"; "MSI-high colorectal cancer - which checkpoint inhibitor?"
```
# PD-L1 (CD274) expression patterns
result = tu.tools.HPA_get_cancer_prognostics_by_gene(gene_name='CD274')
# Cancer-type specific prognostic data
```

### tooluniverse-infectious-disease
**用途**: Rapid pathogen characterization and drug repurposing analysis for infectious disease outbreaks. Identifies pathogen taxonomy, essential proteins, predicts structures, and screens existing drugs via...
**触发条件**: "New pathogen detected - what drugs might work?"; "Emerging virus [X] - therapeutic options?"; "Drug repurposing candidates for [pathogen]"; "What do we know about [novel coronavirus/bacteria]?"
```
### Target: RNA-dependent RNA polymerase (RdRp)
- **UniProt**: P0DTD1 (NSP12)
- **Essentiality**: Required for replication
- **Conservation**: >95% across variants
- **Drug precedent**: Remdesivir targets RdRp

*Source: UniProt via `UniProt_search`, literature review*
```

### tooluniverse-precision-medicine-stratification
**用途**: Comprehensive patient stratification for precision medicine by integrating genomic, clinical, and therapeutic data. Given a disease/condition, genomic data (germline variants, somatic mutations, ex...
**触发条件**: "Stratify this breast cancer patient: ER+/HER2-, BRCA1 mutation, stage II"; "What is the risk profile for this diabetes patient with HbA1c 8.5 and CYP2C19 poor metabolizer?"; "NSCLC patient with EGFR L858R, stage IV, TMB 25 - treatment strategy?"; "Predict prognosis and recommend treatment for this cardiovascular patient"
```
# Check variant frequency in gnomAD
result = tu.tools.gnomad_get_variant(variant_id='1-55505647-G-T')
# Returns allele frequency across populations
```

### tooluniverse-precision-oncology
**用途**: Provide actionable treatment recommendations for cancer patients based on molecular profile. Interprets tumor mutations, identifies FDA-approved therapies, finds resistance mechanisms, matches clin...
**触发条件**: "Patient has [cancer] with [mutation] - what treatments?"; "What are options for EGFR-mutant lung cancer?"; "Patient failed [drug], what's next?"; "Clinical trials for KRAS G12C?"
```
## Treatment Recommendations

### First-Line Options
**1. Osimertinib (Tagrisso)** ★★★
- FDA-approved for EGFR T790M+ NSCLC
- Evidence: AURA3 trial (ORR 71%, mPFS 10.1 mo)
- Source: FDA label, PMID:27959700

### Second-Line Options
**2. Combination: Osimertinib + [Agent]** ★★☆
- Evidence: Phase 2 data
- Source: NCT04487080
```

### tooluniverse-rare-disease-diagnosis
**用途**: Provide differential diagnosis for patients with suspected rare diseases based on phenotype and genetic data. Matches symptoms to HPO terms, identifies candidate diseases from Orphanet/OMIM, priori...
**触发条件**: "Patient has [symptoms], what rare disease could this be?"; "Unexplained developmental delay with [features]"; "WES found VUS in [gene], is this pathogenic?"; "What genes should we test for [phenotype]?"
```
### Candidate Disease: Marfan Syndrome
- **ORPHA**: ORPHA:558
- **OMIM**: 154700
- **Phenotype match**: 85% (17/20 HPO terms)
- **Inheritance**: AD
- **Gene**: FBN1

*Source: Orphanet via `Orphanet_558`, OMIM via `OMIM_get_entry`*
```
