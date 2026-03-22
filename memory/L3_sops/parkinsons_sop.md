# Parkinson's Disease Diagnostic SOP

## 1. MDS Clinical Diagnostic Criteria
- **Essential**: Bradykinesia PLUS at least one of:
  - Rest tremor (4-6 Hz, pill-rolling)
  - Rigidity (lead-pipe or cogwheel)
- **Supportive criteria** (≥2 needed for "clinically established"):
  - Clear beneficial response to levodopa
  - Levodopa-induced dyskinesias
  - Rest tremor of a limb (documented on exam)
  - Olfactory loss or cardiac sympathetic denervation (MIBG scan)

## 2. Exclusion Criteria (Red Flags for Atypical Parkinsonism)
| Red Flag | Suggests |
|----------|----------|
| Early severe autonomic failure | MSA |
| Vertical supranuclear gaze palsy | PSP |
| Early cognitive fluctuations + visual hallucinations | DLB |
| Rapid progression (wheelchair <5yr) | MSA/PSP |
| Early frequent falls | PSP |
| Cerebellar signs | MSA-C |
| Cortical features (apraxia, alien limb) | CBS |
| No levodopa response at adequate dose | Atypical |

## 3. Genetic Testing Indications
- **Early-onset PD** (< 50 years) → screen PARK2 (Parkin), PINK1, DJ-1 (AR)
- **Family history of PD** → screen LRRK2 (AD, most common familial)
- **Ashkenazi Jewish or North African Berber ancestry** → LRRK2 G2019S
- **Any PD patient** → consider GBA screening (strongest common risk factor, OR~5)
- **Familial with dementia overlap** → SNCA (duplication/triplication)

| Gene | Inheritance | Phenotype | When to Query |
|------|------------|-----------|---------------|
| LRRK2 | AD | Late-onset, typical PD | Family hx, Ashkenazi/Berber |
| GBA | Risk factor | PD + faster cognitive decline | All PD (strongest risk gene) |
| SNCA | AD | Early-onset, aggressive, dementia | Family hx + early + dementia |
| PARK2 (Parkin) | AR | Very early onset, slow progression | Onset <40 |
| PINK1 | AR | Early onset, slow | Onset <40 |
| DJ-1 (PARK7) | AR | Early onset, rare | Onset <40, negative Parkin/PINK1 |

## 4. Protein Biomarkers
| Protein | Clinical Utility | Interpretation |
|---------|-----------------|----------------|
| α-Synuclein (SAA) | Synucleinopathy confirmation | Positive = PD/DLB (not MSA) |
| NFL (Neurofilament Light) | Neurodegeneration severity | High = faster progression, also ↑ in atypical |
| DJ-1 | Oxidative stress marker | Altered in CSF of PD |
| Dopamine metabolites (HVA) | DA system integrity | Decreased in PD |

## 5. UKB Analysis Decision Flow
```
Patient data loaded
├── Motor symptoms: bradykinesia + tremor/rigidity → PD suspected
├── Step 1: Age at onset
│   ├── <50 → early-onset pathway: query_genetic_risk(by_gene, [PARK2, PINK1, DJ1])
│   └── ≥50 → typical onset pathway
├── Step 2: Ancestry/Family history
│   ├── Ashkenazi/Berber OR family hx → query_genetic_risk(by_gene, [LRRK2])
│   └── Any PD → consider query_genetic_risk(by_gene, [GBA])
├── Step 3: Protein biomarkers
│   └── query_proteomics([NFL, alpha-synuclein]) if available
├── Step 4: Imaging
│   └── query_imaging_detail(brain_mri) — look for atrophy patterns
├── Step 5: PRS
│   └── query_genetic_risk(by_prs, [parkinsons]) for overall risk
├── Step 6: Differentiate from atypical
│   ├── NFL very high → consider MSA/PSP
│   ├── Cognitive features early → DLB vs PDD
│   └── Cerebellar/autonomic dominant → MSA
└── Step 7: gene_protein_integration() + submit_diagnosis
```

## 6. Key Pathophysiology Notes
- Selective loss of dopaminergic neurons in substantia nigra pars compacta
- α-Synuclein misfolding → Lewy body formation (hallmark)
- Dopamine biosynthesis: Tyrosine → L-DOPA (by TH) → Dopamine (by AADC)
- GBA: encodes glucocerebrosidase; loss → lysosomal dysfunction → α-syn accumulation
- LRRK2: kinase; G2019S gain-of-function → neuronal toxicity

## Source
- MDS Clinical Diagnostic Criteria (Postuma et al., 2015)
- StatPearls: Parkinson's Disease (NBK536726), Codon Publications 2018
- L1 existing knowledge (LRRK2/GBA/SNCA/PARK2/PINK1/DJ-1)