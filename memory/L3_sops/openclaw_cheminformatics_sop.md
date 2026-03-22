# 化学信息学 SOP
> RDKit、分子对接 (DiffDock)、分子特征、QSAR、深度学习药物发现
> 包含 10 个 OpenClaw skill 的压缩迁移。

---

### cobrapy
**用途**: Constraint-based metabolic modeling (COBRA). FBA, FVA, gene knockouts, flux sampling, SBML models, for systems biology and metabolic engineering analysis.
```
from cobra.flux_analysis import pfba
solution = pfba(model)
```
**注意**: for temporary modifications to avoid state management issues; before analysis using `model.slim_optimize()` to ensure feasibility; after optimization - `optimal` indicates successful solve

### datamol
**用途**: Pythonic wrapper around RDKit with simplified interface and sensible defaults. Preferred for standard drug discovery: SMILES parsing, standardization, descriptors, fingerprints, clustering, 3D conf...
```
import datamol as dm
```
**注意**: from external sources:; after molecule parsing:; for large datasets:

### deepchem
**用途**: Molecular machine learning toolkit. Property prediction (ADMET, toxicity), GNNs (GCN, MPNN), MoleculeNet benchmarks, pretrained models, featurization, for drug discovery ML.
```
uv pip install deepchem
```

### diffdock
**用途**: Diffusion-based molecular docking. Predict protein-ligand binding poses from PDB/SMILES, confidence scores, virtual screening, for structure-based drug design. Not for affinity prediction.
```
python app/main.py
# Navigate to http://localhost:7860
```
**注意**: with `setup_check.py` before starting large jobs; with `prepare_batch_csv.py` to catch errors early; then tune parameters based on system-specific needs

### medchem
**用途**: Medicinal chemistry filters. Apply drug-likeness rules (Lipinski, Veber), PAINS filters, structural alerts, complexity metrics, for compound prioritization and library filtering.
```
uv pip install medchem
```

### molfeat
**用途**: Molecular featurization for ML (100+ featurizers). ECFP, MACCS, descriptors, pretrained models (ChemBERTa), convert SMILES to features, for QSAR and molecular ML.
```
uv pip install molfeat

# With all optional dependencies
uv pip install "molfeat[all]"
```

### pytdc
**用途**: Therapeutics Data Commons. AI-ready drug discovery datasets (ADME, toxicity, DTI), benchmarks, scaffold splits, molecular oracles, for therapeutic ML and pharmacological prediction.
```
uv pip install PyTDC
```

### rdkit
**用途**: Cheminformatics toolkit for fine-grained molecular control. SMILES/SDF parsing, descriptors (MW, LogP, TPSA), fingerprints, substructure search, 2D/3D generation, similarity, reactions. For standar...
```
mol = Chem.MolFromSmiles(smiles)
if mol is None:
    print(f"Failed to parse: {smiles}")
    continue
```

### torch-geometric
**用途**: Graph Neural Networks (PyG). Node/graph classification, link prediction, GCN, GAT, GraphSAGE, heterogeneous graphs, molecular property prediction, for geometric deep learning.
```
uv pip install torch_geometric
```

### torchdrug
**用途**: Graph-based drug discovery toolkit. Molecular property prediction (ADMET), protein modeling, knowledge graph reasoning, molecular generation, retrosynthesis, GNNs (GIN, GAT, SchNet), 40+ datasets, ...
```
uv pip install torchdrug
# Or with optional dependencies
uv pip install torchdrug[full]
```
