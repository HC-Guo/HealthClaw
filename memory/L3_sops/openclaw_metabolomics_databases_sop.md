# 代谢组学数据库 SOP
> HMDB、PubChem、Metabolomics Workbench 及代谢组分析
> 包含 5 个 OpenClaw skill 的压缩迁移。

---

### hmdb-database
**用途**: Access Human Metabolome Database (220K+ metabolites). Search by name/ID/structure, retrieve chemical properties, biomarker data, NMR/MS spectra, pathways, for metabolomics and identification.
**注意**: - Verify metabolite identifications with multiple evidence types (spectra, structure, properties); Check experimental vs. predicted data quality indicators; Review citations and evidence for biomarker associations

### metabolomics-workbench-database
**用途**: Access NIH Metabolomics Workbench via REST API (4,200+ studies). Query metabolites, RefMet nomenclature, MS/NMR data, m/z searches, study metadata, for metabolomics and biomarker discovery.
```
response = requests.get('https://www.metabolomicsworkbench.org/rest/compound/regno/{regno}/png')
```

### pubchem-database
**用途**: Query PubChem via PUG-REST API/PubChemPy (110M+ compounds). Search by name/CID/SMILES, retrieve properties, similarity/substructure searches, bioactivity, for cheminformatics.
```
uv pip install pandas
```

### tooluniverse-metabolomics
**用途**: Comprehensive metabolomics research skill for identifying metabolites, analyzing studies, and searching metabolomics databases. Integrates HMDB (220k+ metabolites), MetaboLights, Metabolomics Workb...

### tooluniverse-metabolomics-analysis
**用途**: Analyze metabolomics data including metabolite identification, quantification, pathway analysis, and metabolic flux. Processes LC-MS, GC-MS, NMR data from targeted and untargeted experiments. Perfo...
```
Level 1: Confirmed with authentic standard (MS + RT match)
Level 2: Probable structure (accurate mass + MS/MS)
Level 3: Tentative match (accurate mass only)
Level 4: Unknown metabolite
```
**限制**: **Identification**: Many features remain unidentified (Level 4); **Coverage**: Cannot detect all metabolites (depends on method)
