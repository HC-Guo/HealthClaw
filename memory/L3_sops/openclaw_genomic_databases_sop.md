# 基因组与变异数据库 SOP
> ClinVar、Ensembl、NCBI Gene、GEO、ENA、GWAS Catalog、COSMIC 等
> 包含 11 个 OpenClaw skill 的压缩迁移。

---

### bindingdb-database
**用途**: Query BindingDB for measured drug-target binding affinities (Ki, Kd, IC50, EC50). Search by target (UniProt ID), compound (SMILES/name), or pathogen. Essential for drug discovery, lead optimization...
```
import requests

BASE_URL = "https://www.bindingdb.org/axis2/services/BDBService"

def bindingdb_query(method, params):
    """Query the BindingDB REST API."""
    url = f"{BASE_URL}/{method}"
    response = requests.get(url, params=params, headers={"Accept": "application/json"})
    response.raise_for_status()
    return response.json()
```
**注意**: **Use Ki for direct binding**: Ki reflects true binding affinity independent of enzymatic mechanism; **IC50 context-dependency**: IC50 values depend on substrate concentration (Cheng-Prusoff equation); **Normalize units**: BindingDB reports in nM; verify units when comparing across studies

### clinpgx-database
**用途**: Access ClinPGx pharmacogenomics data (successor to PharmGKB). Query gene-drug interactions, CPIC guidelines, allele functions, for precision medicine and genotype-guided dosing decisions.
```
uv pip install requests
```

### clinvar-database
**用途**: Query NCBI ClinVar for variant clinical significance. Search by gene/position, interpret pathogenicity classifications, access via E-utilities API or FTP, annotate VCFs, for genomic medicine.
```
TP53[gene] AND pathogenic[CLNSIG] NOT conflicting[RVSTAT]
```

### cosmic-database
**用途**: Access COSMIC cancer mutation database. Query somatic mutations, Cancer Gene Census, mutational signatures, gene fusions, for cancer research and precision oncology. Requires authentication.
```
uv pip install requests pandas
```

### ena-database
**用途**: Access European Nucleotide Archive via API/FTP. Retrieve DNA/RNA sequences, raw reads (FASTQ), genome assemblies by accession, for genomics and bioinformatics pipelines. Supports multiple formats.
```
# Query taxonomy API
taxon_id = "562"  # E. coli
url = f"https://www.ebi.ac.uk/ena/taxonomy/rest/tax-id/{taxon_id}"
```

### ensembl-database
**用途**: Query Ensembl genome database REST API for 250+ species. Gene lookups, sequence retrieval, variant analysis, comparative genomics, orthologs, VEP predictions, for genomic research.
```
uv pip install requests
```

### gene-database
**用途**: Query NCBI Gene via E-utilities/Datasets API. Search by symbol/ID, retrieve gene info (RefSeqs, GO, locations, phenotypes), batch lookups, for gene annotation and functional analysis.
```
python scripts/batch_gene_lookup.py --file gene_list.txt --organism human
python scripts/batch_gene_lookup.py --ids 672,7157,5594 --output results.json
```
**注意**: when searching by gene symbol to avoid ambiguity; for precise lookups when available; when working with multiple genes to minimize API calls

### geo-database
**用途**: Access NCBI GEO for gene expression/genomics data. Search/download microarray and RNA-seq datasets (GSE, GSM, GPL), retrieve SOFT/Matrix files, for transcriptomics and expression analysis.
```
uv pip install GEOparse
```

### gget
**用途**: CLI/Python toolkit for rapid bioinformatics queries. Preferred for quick BLAST searches. Access to 20+ databases: gene info (Ensembl/UniProt), AlphaFold, ARCHS4, Enrichr, OpenTargets, COSMIC, genom...
```
gget setup elm
```

### gwas-database
**用途**: Query NHGRI-EBI GWAS Catalog for SNP-trait associations. Search variants by rs ID, disease/trait, gene, retrieve p-values and summary statistics, for genetic epidemiology and polygenic risk scores.
```
rs7903146
```
**限制**: Not all GWAS publications are included (curation criteria apply); Full summary statistics available for subset of studies

### pysam
**用途**: Genomic file toolkit. Read/write SAM/BAM/CRAM alignments, VCF/BCF variants, FASTA/FASTQ sequences, extract regions, calculate coverage, for NGS data processing pipelines.
```
uv pip install pysam
```
