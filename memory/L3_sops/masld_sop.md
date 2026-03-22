# MASLD (Metabolic Dysfunction-Associated Steatotic Liver Disease) SOP
> Source: Wikipedia NAFLD (2024), 2023 Delphi Consensus, AASLD/EASL guidelines
> Evidence: A-level (large cohort + international consensus)

## 1. Nomenclature (2023 Delphi Consensus)
- **SLD** = Steatotic Liver Disease (umbrella term)
- **MASLD** replaces NAFLD = hepatic steatosis + ≥1 cardiometabolic risk factor
- **MASH** replaces NASH = MASLD + hepatocyte inflammation/ballooning
- **MetALD** = MASLD + moderate alcohol intake (140-350g/wk W, 210-420g/wk M)

## 2. Diagnostic Criteria
**Required:** Hepatic steatosis (>5% hepatocytes by histology OR imaging evidence)
**Plus ≥1 of:**
- BMI ≥25 (or ≥23 Asian) OR waist circumference >94cm M / >80cm F
- Fasting glucose ≥100 mg/dL or HbA1c ≥5.7% or T2D
- Blood pressure ≥130/85 mmHg or antihypertensive treatment
- Triglycerides ≥150 mg/dL or lipid-lowering treatment
- HDL-C <40 mg/dL M / <50 mg/dL F or lipid-lowering treatment

**Exclusions:** Significant alcohol (>20g/d W, >30g/d M), viral hepatitis, DILI, monogenic causes

**Staging:** Steatosis → MASH → Fibrosis (F0-F4) → Cirrhosis → HCC
- Biopsy = gold standard; NAS score (0-8): steatosis 0-3, lobular inflam 0-3, ballooning 0-2
- Non-invasive: FibroScan (VCTE), FIB-4 index, NAFLD Fibrosis Score

## 3. Epidemiology
- Global prevalence: 25-38% adults
- >90% of obese, ~60% of T2D patients, ~20% of normal-weight individuals
- MASLD→MASH progression: 7-35%/year
- MASH all-cause mortality: +2.6%/year above background

## 4. Genetic Risk Factors (Key for UKB Analysis)

| Gene | Variant | rsID | Effect | OR/Beta | Evidence |
|------|---------|------|--------|---------|----------|
| **PNPLA3** | I148M | rs738409 | ↑lipid retention, ↑inflammation | OR≈3.26 (homozygous) | A-level |
| **TM6SF2** | E167K | rs58542926 | ↓VLDL secretion, ↑hepatic fat | OR≈2.1 | A-level |
| **HSD17B13** | splice variant | rs72613567 | Protective, ↓inflammation | OR≈0.73 (protective) | A-level |
| **MBOAT7** | intergenic | rs641738 | ↑steatosis risk | Modest effect | A-level |
| **GCKR** | P446L | rs1260326 | ↑de novo lipogenesis | Modest effect | A-level |

**PRS:** Effective for risk stratification; combines PNPLA3+TM6SF2+HSD17B13+GCKR+MBOAT7

### UKB Tool Strategy
- **query_genetic_risk(by_gene):** PNPLA3, TM6SF2, HSD17B13 — always check for suspected MASLD
- **query_genetic_risk(by_prs):** masld/nafld — effective for polygenic risk
- **query_proteomics:** CK-18 (apoptosis marker), FGF21 (metabolic stress), adiponectin
- **query_imaging_detail(abdominal_mri):** liver PDFF for steatosis quantification
- **Gene check trigger:** family history of cirrhosis/MASLD, unexplained steatosis in lean patients, early-onset (<40y)

## 5. Treatment Landscape
- **First-line:** Weight loss (≥7-10% for MASH resolution, ≥10% for fibrosis improvement)
- **Pharmacological:**
  - Resmetirom (THR-β agonist) — FDA approved March 2024 for MASH with F2-F3 fibrosis
  - GLP-1 receptor agonists (semaglutide) — evidence for MASH resolution
  - Pioglitazone — evidence for MASH in diabetic patients
  - SGLT-2 inhibitors — emerging evidence
  - Vitamin E — non-diabetic MASH (800 IU/day)
- **Monitoring:** FIB-4 every 1-2 years; hepatology referral if FIB-4 >2.67

## 6. Clinical Decision Pitfalls
- ⚠️ Lean MASLD (~20% of cases) — don't exclude based on BMI alone
- ⚠️ PNPLA3 I148M homozygous = 3x risk even without obesity
- ⚠️ HSD17B13 is protective — finding variant is reassuring, not alarming
- ⚠️ MetALD overlap: always assess alcohol intake before diagnosing pure MASLD
- ⚠️ MASLD increases cardiovascular mortality more than liver mortality in early stages