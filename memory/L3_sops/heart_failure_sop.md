# Heart Failure / Cardiomyopathy (HF/CM) — Genetic Diagnostic SOP
**Version:** 1.0 | **Date:** 2025-01 | **Sources:** PMID:39405019 (2024 review), ClinGen Inherited Cardiomyopathy Expert Panel, ACMG/AMP guidelines

## 1. Phenotype Classification
| Subtype | Key Features | Core Genes (by diagnostic yield) |
|---------|-------------|----------------------------------|
| **HCM** | LVH ≥15mm unexplained, diastolic dysfunction | MYBPC3 (~40%), MYH7 (~30%), TNNT2, TNNI3, TPM1, MYL2, MYL3, ACTC1 |
| **DCM** | LV dilation + systolic dysfunction (LVEF<45%) | TTN truncating (~20-25%), LMNA (~6%), MYH7, RBM20, BAG3, SCN5A, PLN, FLNC, DSP |
| **ARVC** | RV dysfunction, fibrofatty replacement, arrhythmia | PKP2 (~40%), DSP, DSG2, DSC2, JUP, TMEM43, PLN |
| **RCM** | Restrictive filling, normal/near-normal wall thickness | TNNI3, MYH7, FLNC, DES (overlap with HCM genes) |

## 2. When to Order Genetic Testing
- **Strong indication:** Unexplained cardiomyopathy (any subtype), especially if:
  - Age of onset <50 years (early-onset)
  - Family history of cardiomyopathy, sudden cardiac death, or heart transplant
  - Conduction disease + DCM (suspect LMNA)
  - Skeletal myopathy features (DES, FLNC, LMNA)
- **Moderate indication:** HFrEF without clear ischemic cause after workup
- **Low yield:** HFpEF in elderly with multiple comorbidities (usually acquired)

## 3. Diagnostic Yield by Subtype
- HCM: 30-60% (highest in familial cases; MYBPC3+MYH7 = ~70% of positives)
- DCM: 20-40% (TTN truncating variants most common)
- ARVC: 50-60% (PKP2 dominant)
- RCM: 20-30% (often overlaps HCM genes)

## 4. UKB Diagnostic Strategy
### Step 1: Clinical phenotyping
- Load patient → check LVEF, LV dimensions, wall thickness, NT-proBNP, troponin
- Cardiac MRI if available: LGE pattern, wall motion, ECV (fibrosis marker)

### Step 2: Risk stratification for genetic testing
- Early onset (<50) OR family history → proceed to genetic testing
- Conduction abnormalities + DCM → prioritize LMNA, SCN5A

### Step 3: Genetic testing (by subtype)
- **HCM phenotype:** query_genetic_risk by_gene [MYBPC3, MYH7, TNNT2, TNNI3, TPM1]
- **DCM phenotype:** query_genetic_risk by_gene [TTN, LMNA, MYH7, RBM20, BAG3, FLNC]
- **ARVC phenotype:** query_genetic_risk by_gene [PKP2, DSP, DSG2, DSC2, TMEM43]
- **Unclassified/overlap:** by_pathway [cardiomyopathy] or broader panel
- **PRS:** by_prs [heart_failure] — emerging, useful for polygenic background

### Step 4: Protein biomarkers (if Olink available)
- query_proteomics [NT-proBNP, BNP, Troponin-I, sST2, Galectin-3, GDF-15, IL-6, CRP]
- NT-proBNP z>2: strong HF signal; sST2/Gal-3 elevated: fibrosis/remodeling

### Step 5: Integration
- Monogenic variant found → high confidence genetic cardiomyopathy
- PRS top decile + protein markers elevated → polygenic HF risk
- gene_protein_integration if both genetic and proteomic data available

## 5. Key Clinical-Genetic Correlations
| Gene | Phenotype | Clinical Implication |
|------|-----------|---------------------|
| LMNA | DCM + conduction disease | High SCD risk → early ICD consideration |
| TTN truncating | DCM | Generally better prognosis; may recover with therapy |
| MYBPC3 | HCM | Variable penetrance; common in founder populations |
| PKP2 | ARVC | Exercise restriction critical |
| PLN | DCM/ARVC overlap | Low-voltage ECG, end-stage HF risk |
| FLNC truncating | DCM + LV fibrosis | High arrhythmic risk |

## 6. Heritability & PRS
- HF heritability: ~26% (twin/family studies)
- PRS for HF: GWAS loci include BAG3, HSPB7, CLCNKA, ZBTB17, TTN region
- Polygenic background modifies penetrance of monogenic variants (Fahed et al., Nat Comm)
- PRS not yet standard clinical use but valuable for research risk stratification