# Prostate Cancer - Genetic Risk Assessment SOP

## 1. Disease Overview
- Most common non-skin cancer in men; ~1 in 8 lifetime risk
- Hereditary prostate cancer accounts for ~5-10% of all cases; ~40% of early-onset (<55y)
- Key distinction: sporadic vs hereditary vs familial clustering

## 2. Core Gene Panel (NCCN-recommended for hereditary assessment)

| Gene | Syndrome | Risk (OR/RR) | Penetrance | Evidence Level |
|------|----------|-------------|------------|----------------|
| **BRCA2** | HBOC | OR 2.5-4.6 | High | NCCN Cat 1 |
| **BRCA1** | HBOC | OR 1.8-3.8 | Moderate-High | NCCN Cat 1 |
| **HOXB13** (G84E) | Hereditary PCa | OR 3-5 | Moderate | NCCN Cat 2A |
| **ATM** | Ataxia-Telangiectasia | OR 2.0-3.0 | Moderate | NCCN Cat 2A |
| **PALB2** | FA complementation | OR ~2.0 | Moderate | Emerging |
| **CHEK2** | Li-Fraumeni-like | OR 1.5-2.2 | Low-Moderate | NCCN Cat 2A |
| **MLH1/MSH2/MSH6/PMS2** | Lynch Syndrome | OR 2.0-5.0 (MSH2 highest) | Moderate | NCCN Cat 2A |
| **NBN** | Nijmegen Breakage | OR ~1.5 | Low | Emerging |

## 3. Genetic Testing Indications (NCCN Criteria)
Test if **any** of:
- Metastatic prostate cancer (any histology)
- High-risk/very high-risk localized prostate cancer
- Regional (node-positive) prostate cancer
- Intraductal/cribriform histology
- Grade Group ≥3 (Gleason ≥4+3)
- Family history: ≥1 first-degree relative with PCa <60y, ≥2 relatives with PCa/breast/ovarian/pancreatic cancer
- Known pathogenic variant in family
- Ashkenazi Jewish ancestry
- Male breast cancer personal/family history

## 4. PSA Screening by Genetic Risk

| Carrier Status | Start Age | Frequency | Notes |
|----------------|-----------|-----------|-------|
| BRCA2 carrier | 40 | Annual | Most aggressive screening; consider MRI |
| BRCA1 carrier | 40 | Annual | |
| HOXB13 G84E | 40 | Annual | Higher risk in younger men |
| ATM/PALB2/CHEK2 | 40 | Annual | Shared decision-making |
| Lynch (esp MSH2) | 40 | Annual | Also screen for Lynch-associated cancers |
| General population | 50 (or 45 if Black/FHx+) | Every 2y if PSA <1 | Per AUA/NCCN |

## 5. Treatment-Relevant Biomarkers

### 5.1 HRR (Homologous Recombination Repair) Deficiency
- **Genes**: BRCA1, BRCA2, ATM, PALB2, CHEK2, CDK12, FANCA, RAD51B/C/D
- **Implication**: PARP inhibitor eligibility (olaparib, rucaparib, niraparib, talazoparib)
- **FDA-approved**: Olaparib for HRR-mutated mCRPC (PROfound trial); Rucaparib for BRCA1/2 mCRPC
- Testing: Recommend somatic + germline; tumor tissue preferred for somatic

### 5.2 MSI-H / dMMR
- **Genes**: MLH1, MSH2, MSH6, PMS2 (Lynch syndrome genes)
- **Implication**: Pembrolizumab (anti-PD-1) eligible regardless of tissue type
- Prevalence: ~2-3% of advanced prostate cancer

### 5.3 TMB-High
- TMB ≥10 mut/Mb → pembrolizumab eligible
- Rare in prostate cancer (~3-5%)

## 6. UKB Analysis Decision Tree

```
Patient: Male with prostate cancer context
│
├─ Step 1: load_patient → Extract age_at_dx, PSA, Gleason, family_hx, ancestry
│
├─ Step 2: recall_similar_cases(prostate_cancer, [features])
│
├─ Step 3: Assess if genetic testing indicated (Section 3 criteria)
│   ├─ YES → query_genetic_risk(by_gene, [BRCA2,BRCA1,HOXB13,ATM,CHEK2,PALB2])
│   │         query_genetic_risk(by_pathway, [DNA_damage_repair])
│   │         query_genetic_risk(by_gene, [MLH1,MSH2,MSH6,PMS2]) if Lynch suspected
│   └─ NO → Consider PRS only
│            query_genetic_risk(by_prs, [prostate_cancer])
│
├─ Step 4: Protein markers (if available)
│   └─ query_proteomics([KLK3, FOLH1, AR, TMPRSS2])
│       - KLK3 = PSA protein; elevated = tumor burden
│       - FOLH1 = PSMA; elevated = PSMA-targeted therapy candidate
│       - AR = androgen receptor; relevant to castration resistance
│
├─ Step 5: gene_protein_integration() if both genetic + proteomic data available
│
└─ Step 6: Risk stratification & reporting
    - Integrate Gleason + PSA + genetic risk + proteomic markers
    - Flag PARP inhibitor eligibility if HRR defect found
    - Flag immunotherapy eligibility if MSI-H/dMMR
```

## 7. Key Clinical Notes
- **BRCA2 is the most clinically actionable gene** in prostate cancer: higher risk, more aggressive disease, PARP inhibitor eligible
- Germline BRCA2 carriers have worse prognosis (earlier metastasis, shorter survival)
- HOXB13 G84E is a founder mutation; prevalence ~1-3% in European men with early-onset PCa
- Always check for **somatic** HRR mutations even if germline is negative (somatic BRCA2 loss in ~6% mCRPC)
- CDK12 biallelic loss → unique neoantigen-enriched phenotype → potential immunotherapy response

## 8. Sources & Evidence Grades
- NCCN Prostate Cancer v1.2025 (Cat 1-2A recommendations)
- NCCN Genetic/Familial High-Risk Assessment v3.2024
- PROfound Trial (de Bono et al., NEJM 2020) - PARP inhibitor in HRR-mutated mCRPC
- Pritchard et al., NEJM 2016 - prevalence of DNA repair gene mutations in mCRPC
- Nyberg et al., Eur Urol 2020 - BRCA2 prostate cancer risk estimates
- **Note**: Written primarily from training knowledge; online sources were inaccessible during autonomous learning session

---
*Created: Autonomous Learning Session | Evidence: Training knowledge + NCCN guidelines synthesis*
*Confidence: Moderate-High (core content well-established; specific OR values may need verification)*