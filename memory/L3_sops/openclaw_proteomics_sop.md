# 蛋白质组学与质谱 SOP
> 质谱分析 (matchms/pyOpenMS)、蛋白互作、蛋白结构检索
> 包含 6 个 OpenClaw skill 的压缩迁移。

---

### flowio
**用途**: Parse FCS (Flow Cytometry Standard) files v2.0-3.1. Extract events as NumPy arrays, read metadata/channels, convert to CSV/DataFrame, for flow cytometry data preprocessing.
```
uv pip install flowio
```
**注意**: Use `only_text=True` when event data is not needed; Wrap file operations in try-except blocks for robust code; Check for MultipleDataSetsError and use appropriate function

### matchms
**用途**: Mass spectrometry analysis. Process mzML/MGF/MSP, spectral similarity (cosine, modified cosine), metadata harmonization, compound ID, for metabolomics and MS data processing.
```
uv pip install matchms
```

### pyopenms
**用途**: Python interface to OpenMS for mass spectrometry data analysis. Use for LC-MS/MS proteomics and metabolomics workflows including file handling (mzML, mzXML, mzTab, FASTA, pepXML, protXML, mzIdentML...
```
uv uv pip install pyopenms
```

### protein-interaction-network-analysis
**用途**: Analyze protein-protein interaction networks using STRING, BioGRID, and SASBDB databases. Maps protein identifiers, retrieves interaction networks with confidence scores, performs functional enrich...
```
BIOGRID_API_KEY=your_key_here
```

### tooluniverse-protein-structure-retrieval
**用途**: Retrieves protein structure data from RCSB PDB, PDBe, and AlphaFold with protein disambiguation, quality assessment, and comprehensive structural profiles. Creates detailed structure reports with e...
```
Phase 0: Clarify (if needed)
    ↓
Phase 1: Disambiguate Protein Identity
    ↓
Phase 2: Retrieve Structures (Internal)
    ↓
Phase 3: Report Structure Profile
```

### tooluniverse-proteomics-analysis
**用途**: Analyze mass spectrometry proteomics data including protein quantification, differential expression, post-translational modifications (PTMs), and protein-protein interactions. Processes MaxQuant, S...
```
def protein_complex_enrichment(protein_list):
    """
    Test for enrichment of known protein complexes (CORUM database).
    """
    # Query CORUM or use ToolUniverse
    # Identify if proteins are part of known complexes
    pass
```
**限制**: **Platform-specific**: Optimized for MS-based proteomics (not Western blot quantification); **Missing values**: High missing rate (>50% per protein) limits statistical power
