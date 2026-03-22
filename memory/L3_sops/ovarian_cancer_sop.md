# Ovarian Cancer Risk Assessment SOP

## 1. Disease Overview
- **Lifetime risk (general population)**: ~1.5% (US)
- **Median diagnosis age**: 63 years
- **Histologic subtypes**: High-grade serous (HGSOC, 70%), endometrioid, clear cell, mucinous, low-grade serous
- **Hereditary proportion**: ~20-25% of epithelial OC have germline pathogenic variants

## 2. Genetic Risk Stratification

### 2.1 High-Penetrance Genes
| Gene | Lifetime OC Risk | Predominant Subtype | RRSO Timing |
|------|-----------------|---------------------|-------------|
| BRCA1 | 39-44% | HGSOC | Age 35-40 |
| BRCA2 | 11-17% | HGSOC | Age 40-45 |
| MLH1 | ~20% | Endometrioid/Clear cell | Case-by-case |
| MSH2 | ~20% | Endometrioid/Clear cell | Case-by-case |
| MSH6 | ~1-11% | Endometrioid/Clear cell | Case-by-case |

### 2.2 Moderate-Penetrance Genes
| Gene | Lifetime OC Risk | Notes |
|------|-----------------|-------|
| RAD51C | 5-15% | HR pathway; RRSO considered |
| RAD51D | 5-15% | HR pathway; RRSO considered |
| BRIP1 | 5-15% | Fanconi anemia pathway |
| PALB2 | Modest increase | Primarily breast cancer gene |

### 2.3 Rare Syndromes
| Gene | Associated Tumor | Syndrome |
|------|-----------------|----------|
| STK11 | Sex cord stromal (SCTAT) | Peutz-Jeghers |
| DICER1 | Sertoli-Leydig cell | DICER1 syndrome |
| PTEN | Endometrial (20-30%) | Cowden syndrome |

### 2.4 PRS
- Polygenic risk contributes modestly; less validated than breast cancer PRS
- Use `query_genetic_risk(by_prs, ["ovarian_cancer"])` if available

## 3. UKB Assessment Workflow

### Step 1: Load Patient
```
load_patient(eid, "ovarian_cancer")
```
**Key features to extract**: Age, BMI, family history of OC/breast/colorectal cancer, menopausal status, OCP use, parity, endometriosis history, ethnicity (Ashkenazi Jewish)

### Step 2: Risk Flag Evaluation
| Flag | Criteria | Action |
|------|----------|--------|
| Family history | 1st-degree relative with OC or breast cancer | → Genetic testing |
| Early onset | OC diagnosis <50 years | → Genetic testing |
| Ashkenazi Jewish | Self-reported or genetic ancestry | → BRCA1/2 founder mutations |
| Lynch features | Colorectal + endometrial + OC family pattern | → MMR genes |
| Bilateral/young breast + OC | Personal or family | → BRCA1/2 |

### Step 3: Genetic Risk Query
```
# High-risk panel (cost-effective order)
query_genetic_risk(by_gene, ["BRCA1", "BRCA2"])  # cost=0.2
# If negative and Lynch suspected:
query_genetic_risk(by_gene, ["MLH1", "MSH2", "MSH6", "PMS2"])
# If negative and moderate-risk indicated:
query_genetic_risk(by_gene, ["RAD51C", "RAD51D", "BRIP1"])
# Alternative: pathway query
query_genetic_risk(by_pathway, ["homologous_recombination"])
```

### Step 4: Protein Biomarkers
```
query_proteomics(["CA-125", "HE4", "WFDC2"])  # cost=0.05
```
**Interpretation**:
- **CA-125 (MUC16)**: Elevated >35 U/mL suggests OC; z-score >2 is concerning
- **HE4 (WFDC2)**: Complementary marker; better specificity in premenopausal
- **ROMA score**: Combines CA-125 + HE4 + menopausal status
  - Premenopausal cutoff: ≥7.4% = high risk
  - Postmenopausal cutoff: ≥25.3% = high risk

### Step 5: Imaging (if available)
```
query_imaging_detail("abdominal_mri")  # or ultrasound
```
Look for: adnexal mass, ascites, peritoneal thickening, omental caking

### Step 6: Integration
```
gene_protein_integration()  # cost=0.5, only if both genetic + proteomic data available
```

## 4. Risk Classification Output
| Category | Criteria | Estimated Lifetime Risk |
|----------|----------|------------------------|
| Very High | BRCA1 pathogenic variant | 39-44% |
| High | BRCA2 PV or Lynch (MLH1/MSH2) | 11-20% |
| Moderate | RAD51C/D, BRIP1 PV | 5-15% |
| Slightly Elevated | Strong family hx, no identified PV | 3-5% |
| Population | No risk factors | ~1.5% |

## 5. Cost-Efficiency Notes
- **BRCA carrier rate in OC patients**: 10-15% (general), 36-41% (Ashkenazi Jewish)
- **Priority**: Always query BRCA1/2 first; only expand panel if negative + strong family history
- **recall_similar_cases("ovarian_cancer", [...])** before expensive tools
- Skip gene_protein_integration unless both data streams are informative

## 6. Key Differentials
- Endometrial cancer (shared Lynch pathway, PTEN)
- Peritoneal carcinomatosis (primary peritoneal vs ovarian)
- Borderline ovarian tumors (different genetics, better prognosis)

## 7. References
- NCI BRCA-associated cancers PDQ (2024)
- NCCN Genetic/Familial High-Risk Assessment v2.2024
- MSK Hereditary Ovarian Cancer page
- Kuchenbaecker et al. JAMA 2017 (BRCA1/2 penetrance)