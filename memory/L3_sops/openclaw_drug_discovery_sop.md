# 药物发现与安全 SOP
> 药物研究、再利用、DDI 预测、药物警戒、ADMET、不良事件检测
> 包含 16 个 OpenClaw skill 的压缩迁移。

---

### agentd-drug-discovery
**用途**: 

### chembl-database
**用途**: Query ChEMBL's bioactive molecules and drug discovery data. Search compounds by structure/properties, retrieve bioactivity data (IC50, Ki), find inhibitors, perform SAR studies, for medicinal chemi...
```
uv pip install chembl_webresource_client
```

### chembl-search
**用途**: Search ChEMBL bioactive molecules database with natural language queries. Find compounds and assay data with Valyu semantic search.
```
scripts/search setup <api-key>
```

### drug-discovery-search
**用途**: End-to-end drug discovery platform combining ChEMBL compounds, DrugBank, targets, and FDA labels. Natural language powered by Valyu.
```
scripts/search setup <api-key>
```

### drug-labels-search
**用途**: Search FDA drug labels with natural language queries. Official drug information, indications, and safety data via Valyu.
```
scripts/search setup <api-key>
```

### drugbank-database
**用途**: Access and analyze comprehensive drug information from the DrugBank database including drug properties, interactions, targets, pathways, chemical structures, and pharmacology data. This skill shoul...
```
from drugbank_downloader import download_drugbank
path = download_drugbank(version='5.1.10')  # Specify exact version
```

### drugbank-search
**用途**: Search DrugBank comprehensive drug database with natural language queries. Drug mechanisms, interactions, and safety data powered by Valyu.
```
$DRUGBANK_SCRIPT "ACE inhibitors" 15
```

### tooluniverse-adverse-event-detection
**用途**: Detect and analyze adverse drug event signals using FDA FAERS data, drug labels, disproportionality analysis (PRR, ROR, IC), and biomedical evidence. Generates quantitative safety signal scores (0-...
**触发条件**: "What are the safety signals for [drug]?"; "Detect adverse events for [drug]"; "Is [drug] associated with [adverse event]?"; "What are the FAERS signals for [drug]?"
```
Meta-analyses confirming safety signals: 10 points
Multiple RCTs with safety concerns: 7 points
Case reports/case series: 4 points
No published safety concerns: 0 points
```

### tooluniverse-binder-discovery
**用途**: Discover novel small molecule binders for protein targets using structure-based and ligand-based approaches. Creates actionable reports with candidate compounds, ADMET profiles, and synthesis feasi...
```
GtoPdb_get_target_interactions(target_id)
└─ Extract: Ligands with pKi/pIC50, selectivity data
```

### tooluniverse-chemical-compound-retrieval
**用途**: Retrieves chemical compound information from PubChem and ChEMBL with disambiguation, cross-referencing, and quality assessment. Creates comprehensive compound profiles with identifiers, properties,...
```
**Data Completeness**: ●●● Complete (properties, bioactivity, drug data)
```

### tooluniverse-chemical-safety
**用途**: Comprehensive chemical safety and toxicology assessment integrating ADMET-AI predictions, CTD toxicogenomics, FDA label safety data, DrugBank safety profiles, and STITCH chemical-protein interactio...
```
Input: Drug name (e.g., "Acetaminophen")
Workflow: All phases (0-7 + Synthesis)
Output: Complete safety dossier with regulatory + predictive + database evidence
```

### tooluniverse-drug-drug-interaction
**用途**: Comprehensive drug-drug interaction (DDI) prediction and risk assessment. Analyzes interaction mechanisms (CYP450, transporters, pharmacodynamic), severity classification, clinical evidence grading...

### tooluniverse-drug-repurposing
**用途**: Identify drug repurposing candidates using ToolUniverse for target-based, compound-based, and disease-driven strategies. Searches existing drugs for new therapeutic indications by analyzing targets...
```
# Use pathway analysis
pathways = tu.tools.drugbank_get_pathways_reactions_by_drug_or_id(
    drug_name_or_drugbank_id="[drug_name]"
)

# Find drugs affecting same pathways
pathway_drugs = tu.tools.drugbank_get_drug_name_and_description_by_pathway_name(
    pathway_name=pathways['data'][0]['pathway_name']
)
```

### tooluniverse-drug-research
**用途**: Generates comprehensive drug research reports with compound disambiguation, evidence grading, and mandatory completeness sections. Covers identity, chemistry, pharmacology, targets, clinical trials...
```
### Clinical Trials
Multiple trials completed. Approved for diabetes.
```

### tooluniverse-drug-target-validation
**用途**: Comprehensive computational validation of drug targets for early-stage drug discovery. Evaluates targets across 10 dimensions (disambiguation, disease association, druggability, chemical matter, cl...
```
safety = tu.tools.OpenTargets_get_target_safety_profile_by_ensemblID(ensemblId=ensembl_id)
# Returns: safety liabilities, adverse effects, experimental toxicity
```

### tooluniverse-pharmacovigilance
**用途**: Analyze drug safety signals from FDA adverse event reports, label warnings, and pharmacogenomic data. Calculates disproportionality measures (PRR, ROR), identifies serious adverse events, assesses ...
**触发条件**: "What are the safety concerns for [drug]?"; "What adverse events are associated with [drug]?"; "Is [drug] safe? What are the risks?"; "Should I be concerned about [specific adverse event] with [drug]?"
```
Signal Score = PRR × Severity_Weight × log10(Case_Count + 1)

Severity Weights:
- Fatal: 10
- Life-threatening: 8
- Hospitalization: 5
- Disability: 5
- Other serious: 3
- Non-serious: 1
```
