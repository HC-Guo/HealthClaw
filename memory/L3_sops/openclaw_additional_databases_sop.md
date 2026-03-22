# 补充科学数据库 SOP
> InterPro、JASPAR、GTEx、Monarch、DepMap、Imaging Data Commons
> 包含 8 个 OpenClaw skill 的压缩迁移。

---

### datacommons-client
**用途**: Work with Data Commons, a platform providing programmatic access to public statistical data from global sources. Use this skill when working with demographic data, economic indicators, health stati...
```
uv pip install datacommons-client
```

### depmap
**用途**: Query the Cancer Dependency Map (DepMap) for cancer cell line gene dependency scores (CRISPR Chronos), drug sensitivity data, and gene effect profiles. Use for identifying cancer-specific vulnerabi...
```
import requests
import pandas as pd

BASE_URL = "https://depmap.org/portal/api"

def depmap_get(endpoint, params=None):
    url = f"{BASE_URL}/{endpoint}"
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()
```
**注意**: **Use Chronos scores** (not DEMETER2) for current CRISPR analyses — better controlled for cutting efficiency; **Distinguish pan-essential from cancer-selective**: Target genes with low variance (essential in all lines) are poor drug targets; **Validate with expression data**: A gene not expressed in a cell line will score as non-essential regardless of actual function

### gtex-database
**用途**: Query GTEx (Genotype-Tissue Expression) portal for tissue-specific gene expression, eQTLs (expression quantitative trait loci), and sQTLs. Essential for linking GWAS variants to gene regulation, un...
```
# All significant eQTLs (v10)
wget https://storage.googleapis.com/adult-gtex/bulk-qtl/v10/single-tissue-cis-qtl/GTEx_Analysis_v10_eQTL.tar

# Normalized expression matrices
wget https://storage.googleapis.com/adult-gtex/bulk-gex/v10/rna-seq/GTEx_Analysis_v10_RNASeQCv2.4.2_gene_reads.gct.gz
```
**注意**: **Use GENCODE IDs** (e.g., `ENSG00000130203.10`) for gene queries; the `.version` suffix matters for some endpoints; **GTEx variant IDs** use the format `chr{chrom}_{pos}_{ref}_{alt}_b38` (GRCh38) — different from rs IDs; **Handle pagination**: Large queries (e.g., all eGenes) require iterating through pages

### imaging-data-commons
**用途**: Query and download public cancer imaging data from NCI Imaging Data Commons using idc-index. Use for accessing large-scale radiology (CT, MR, PET) and pathology datasets for AI training or research...
```
pip install --upgrade idc-index
```
**注意**: **Verify IDC version before generating responses** - Always call `client.get_idc_version()` at the start of a session to confirm you're using the expected data version (currently v23). If using an older version, recommend `pip install --upgrade idc-index`; **Check licenses before use** - Always query the `license_short_name` field and respect licensing terms (CC BY vs CC BY-NC); **Generate citations for attribution** - Use `citations_from_selection()` to get properly formatted citations from `source_DOI` values; include these in publications

### interpro-database
**用途**: Query InterPro for protein family, domain, and functional site annotations. Integrates Pfam, PANTHER, PRINTS, SMART, SUPERFAMILY, and 11 other member databases. Use for protein function prediction,...
```
import requests

BASE_URL = "https://www.ebi.ac.uk/interpro/api"

def interpro_get(endpoint, params=None):
    url = f"{BASE_URL}/{endpoint}"
    headers = {"Accept": "application/json"}
    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()
    return response.json()
```
**注意**: **Use UniProt accession numbers** (not gene names) for the most reliable lookups; **Distinguish types**: `family` gives broad classification; `domain` gives specific structural/functional units; **InterProScan is faster for novel sequences**: For sequences not in UniProt, submit to the web service

### jaspar-database
**用途**: Query JASPAR for transcription factor binding site (TFBS) profiles (PWMs/PFMs). Search by TF name, species, or class; scan DNA sequences for TF binding sites; compare matrices; essential for regula...
```
import requests

BASE_URL = "https://jaspar.elixir.no/api/v1"

def jaspar_get(endpoint, params=None):
    url = f"{BASE_URL}/{endpoint}"
    response = requests.get(url, params=params, headers={"Accept": "application/json"})
    response.raise_for_status()
    return response.json()
```
**注意**: **Use CORE collection** for most analyses — best validated and non-redundant; **Threshold selection**: 80% of max score is common for de novo prediction; 90% for high-confidence; **Always scan both strands** — TFs can bind in either orientation

### monarch-database
**用途**: Query the Monarch Initiative knowledge graph for disease-gene-phenotype associations across species. Integrates OMIM, ORPHANET, HPO, ClinVar, and model organism databases. Use for rare disease gene...
```
import requests

BASE_URL = "https://api-v3.monarchinitiative.org/v3"

def monarch_get(endpoint, params=None):
    """Make a GET request to the Monarch API."""
    url = f"{BASE_URL}/{endpoint}"
    response = requests.get(url, params=params, headers={"Accept": "application/json"})
    response.raise_for_status()
    return response.json()
```
**注意**: **Use MONDO IDs** for diseases — they unify OMIM/ORPHANET/MESH identifiers; **Use HPO IDs** for phenotypes — the standard for clinical phenotype description; **Handle pagination**: Large queries may require iterating with offset parameter

### tiledbvcf
**用途**: Efficient storage and retrieval of genomic variant data using TileDB. Scalable VCF/BCF ingestion, incremental sample addition, compressed storage, parallel queries, and export capabilities for popu...
```
# Sign up at https://cloud.tiledb.com
# Generate API token in your account settings
```
