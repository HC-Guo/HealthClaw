# gptomics 临床数据库 SOP
> ClinVar、PharmGKB、OMIM、HPO、OrphaNet 查询
> 包含 10 个 OpenClaw skill 的压缩迁移。

---

### bio-clinical-databases-clinvar-lookup
**用途**: Query ClinVar for variant pathogenicity classifications, review status, and disease associations via REST API or local VCF. Use when determining clinical significance of variants for diagnostic or ...
```
# Annotate VCF with ClinVar
bcftools annotate \
    -a clinvar.vcf.gz \
    -c INFO/CLNSIG,INFO/CLNREVSTAT,INFO/CLNDN \
    input.vcf.gz \
    -o annotated.vcf.gz
```

### bio-clinical-databases-dbsnp-queries
**用途**: Query dbSNP for rsID lookups, variant annotations, and cross-references to other databases. Use when mapping between rsIDs and genomic coordinates or retrieving basic variant information.
```
import myvariant

mv = myvariant.MyVariantInfo()

def get_rsid_info(rsid):
    '''Get variant info by rsID'''
    result = mv.getvariant(rsid, fields=['dbsnp', 'clinvar', 'gnomad_exome'])
    return result

result = get_rsid_info('rs121913527')
```

### bio-clinical-databases-gnomad-frequencies
**用途**: Query gnomAD for population allele frequencies to assess variant rarity. Use when filtering variants by population frequency for rare disease analysis or determining if a variant is common in the g...
```
# Using Hail for gnomAD v4
import hail as hl

ht = hl.read_table('gs://gcp-public-data--gnomad/release/4.0/ht/exomes/gnomad.exomes.v4.0.sites.ht')

# Filter to rare variants
rare_ht = ht.filter(ht.freq[0].AF < 0.01)
```

### bio-clinical-databases-hla-typing
**用途**: Call HLA alleles from NGS data using OptiType, HLA-HD, or arcasHLA for immunogenomics applications. Use when determining HLA genotype for transplant matching, neoantigen prediction, or pharmacogeno...
```
# Merge multiple samples
arcasHLA merge output_dir/*.genotype.json -o merged_hla.tsv
```

### bio-clinical-databases-myvariant-queries
**用途**: Query myvariant.info API for aggregated variant annotations from multiple databases (ClinVar, gnomAD, dbSNP, COSMIC, etc.) in a single request. Use when annotating variants with clinical and popula...
```
import myvariant
```

### bio-clinical-databases-pharmacogenomics
**用途**: Query PharmGKB and CPIC for drug-gene interactions, pharmacogenomic annotations, and dosing guidelines. Use when predicting drug response from genetic variants or implementing clinical pharmacogeno...
```
def get_drug_annotations(drug_name):
    '''Get pharmacogenomic annotations for a drug'''
    url = 'https://api.pharmgkb.org/v1/data/clinicalAnnotation'
    params = {'view': 'base', 'chemicals.name': drug_name}
    response = requests.get(url, params=params)
    return response.json()['data']

warfarin_annotations = get_drug_annotations('warfarin')
```

### bio-clinical-databases-polygenic-risk
**用途**: Calculate polygenic risk scores using PRSice-2, LDpred2, or PRS-CS from GWAS summary statistics. Use when predicting disease risk from genome-wide genetic variants.
```
SNP          CHR  BP        A1  A2  BETA    SE      P
rs12345      1    10000     A   G   0.05    0.01    1e-8
rs67890      1    20000     T   C   -0.03   0.02    0.001
```

### bio-clinical-databases-somatic-signatures
**用途**: Extract and analyze mutational signatures from somatic variants using SigProfiler or MutationalPatterns to characterize mutagenic processes. Use when identifying DNA damage mechanisms or etiology i...
```
from SigProfilerAssignment import Analyzer as Analyze

# Fit to known COSMIC signatures
Analyze.cosmic_fit(
    samples='my_project/output/SBS/my_project.SBS96.all',
    output='assignment_output',
    input_type='matrix',
    genome_build='GRCh38',
    signature_database='SBS_GRCh38_GRCh38'
)
```

### bio-clinical-databases-tumor-mutational-burden
**用途**: Calculate tumor mutational burden from panel or WES data with proper normalization and clinical thresholds. Use when assessing immunotherapy eligibility or characterizing tumor immunogenicity.
```
# Common panel sizes (in megabases)
# Check your specific panel's capture region size
PANEL_SIZES_MB = {
    'FoundationOne CDx': 0.8,
    'MSK-IMPACT': 1.14,
    'TruSight Oncology 500': 1.94,
    'Oncomine Comprehensive': 1.5,
    'WES (exome)': 30.0,  # Approximate coding region
    'WGS': 3000.0,        # Approximate
}

def calculate_tmb_panel(vcf_path, panel_name):
    '''Calculate TMB for known panel'''
    if panel_name not in PANEL_SIZES_MB:
        raise ValueError(f'Unknown panel: {pan
# ... (truncated)
```

### bio-clinical-databases-variant-prioritization
**用途**: Filter and prioritize variants by pathogenicity, population frequency, and clinical evidence for rare disease analysis. Use when identifying candidate disease-causing variants from exome or genome ...
```
def assign_tiers(df):
    '''Assign clinical interpretation tiers

    Tier 1: Strong pathogenic evidence
    Tier 2: Potential pathogenic
    Tier 3: Uncertain significance
    Tier 4: Likely benign
    '''
    def get_tier(row):
        if row['clinvar_pathogenic'] and row['is_rare']:
            return 1
        elif row['is_rare'] and (row['cadd_deleterious'] or row['revel_pathogenic']):
            return 2
        elif row['is_rare']:
            return 3
        else:
            return 4
# ... (truncated)
```
