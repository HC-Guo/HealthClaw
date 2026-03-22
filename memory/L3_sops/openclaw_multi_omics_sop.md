# 多组学整合与系统生物学 SOP
> 多组学整合、通路分析、基因富集、网络药理学、系统生物学建模
> 包含 7 个 OpenClaw skill 的压缩迁移。

---

### gsea-enrichment-analysis
**用途**: Gene set enrichment analysis with correct geneset format handling. Critical guidance for loading pathway databases and running enrichment in OmicVerse.
```
# WRONG! Don't pass file path directly to geneset_enrichment!
# enr = ov.bulk.geneset_enrichment(
#     gene_list=deg_genes,
#     pathways_dict='genesets/GO_Biological_Process_2021.gmt'  # ERROR! String path doesn't work!
# )

# WRONG! geneset_enrichment expects dict, not file path
# enr = ov.bulk.geneset_enrichment(
#     gene_list=deg_genes,
#     pathways_dict='GO_Biological_Process_2021'  # ERROR!
# )
```

### tcga-bulk-data-preprocessing-with-omicverse
**用途**: Guide Claude through ingesting TCGA sample sheets, expression archives, and clinical carts into omicverse, initialising survival metadata, and exporting annotated AnnData files.

### tooluniverse-gene-enrichment
**用途**: Perform comprehensive gene enrichment and pathway analysis using gseapy (ORA and GSEA), PANTHER, STRING, Reactome, and 40+ ToolUniverse tools. Supports GO enrichment (BP, MF, CC), KEGG, Reactome, W...
```
report_path = f"{analysis_name}_enrichment_report.md"
# Write header with placeholder sections
# Update progressively as analysis proceeds
```

### tooluniverse-multi-omics-integration
**用途**: Integrate and analyze multiple omics datasets (transcriptomics, proteomics, epigenomics, genomics, metabolomics) for systems biology and precision medicine. Performs cross-omics correlation, multi-...
```
# Map all features to genes
feature_mapping = {
    'rnaseq': 'gene_symbol',  # Already gene-level
    'proteomics': 'gene_symbol',  # Map protein to gene
    'methylation': 'gene_symbol',  # Map CpG to gene (promoter)
    'cnv': 'gene_symbol',  # CNV regions to overlapping genes
    'metabolomics': 'enzyme_gene'  # Metabolite to enzyme gene
}
```
**限制**: **Sample size**: Multi-omics integration requires sufficient samples (n≥20 recommended); **Missing data**: Some patients may not have all omics types

### tooluniverse-multiomic-disease-characterization
**用途**: Comprehensive multi-omics disease characterization integrating genomics, transcriptomics, proteomics, pathway, and therapeutic layers for systems-level understanding. Produces a detailed multi-omic...
```
{
  "status": "success",
  "data": "{\"connected_paths\": {\"Path: ...\": \"Total Weight: ...\"}}"
}
```

### tooluniverse-network-pharmacology
**用途**: Construct and analyze compound-target-disease networks for drug repurposing, polypharmacology discovery, and systems pharmacology. Builds multi-layer networks from ChEMBL, OpenTargets, STRING, Drug...
```
# Create report file FIRST
report_path = "[entity]_network_pharmacology_report.md"
# Write header and placeholder sections
```

### tooluniverse-systems-biology
**用途**: Comprehensive systems biology and pathway analysis using multiple pathway databases (Reactome, KEGG, WikiPathways, Pathway Commons, BioModels). Performs pathway enrichment, protein-pathway mapping,...
```
Input → Phase 1: Enrichment → Phase 2: Protein Mapping → Phase 3: Keyword Search → Phase 4: Top Pathways → Report
```
