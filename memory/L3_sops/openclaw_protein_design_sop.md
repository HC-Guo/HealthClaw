# 蛋白质设计与工程 SOP
> AlphaFold/RFdiffusion/ProteinMPNN/BindCraft 结构预测与从头设计
> 包含 23 个 OpenClaw skill 的压缩迁移。

---

### aav-vector-design-agent
**用途**: 
```
5' ITR - [Promoter] - [5' UTR] - [Transgene] - [WPRE] - [PolyA] - 3' ITR

Packaging limit: ~4.7 kb between ITRs
```

### adaptyv
**用途**: Cloud laboratory platform for automated protein testing and validation. Use when designing proteins and needing experimental validation including binding assays, expression testing, thermostability...
```
ADAPTYV_API_KEY=your_api_key_here
```

### alphafold
**用途**: Validate protein designs using AlphaFold2 structure prediction. Use this skill when: (1) Validating designed sequences fold correctly, (2) Predicting binder-target complex structures, (3) Calculati...
```
modal run modal_esmfold.py \
  --sequence "MKTAYIAKQRQISFVK..."
```

### antibody-design-agent
**用途**: 

### bindcraft
**用途**: End-to-end binder design using BindCraft hallucination. Use this skill when: (1) Designing protein binders with built-in AF2 validation, (2) Running production-quality binder campaigns, (3) Using d...
```
find output -name "binder.pdb" | wc -l  # Should match num_designs
```

### binder-design
**用途**: Guidance for choosing the right protein binder design tool. Use this skill when: (1) Deciding between BoltzGen, BindCraft, or RFdiffusion, (2) Planning a binder design campaign, (3) Understanding t...
```
# Fetch structure from PDB
# Use pdb skill for guidance
```

### binding-characterization
**用途**: Guidance for SPR and BLI binding characterization experiments. Use when: (1) Planning binding kinetics experiments, (2) Troubleshooting poor/no binding signal, (3) Interpreting kinetic data artifac...

### bio-structural-biology-alphafold-predictions
**用途**: Access and analyze AlphaFold protein structure predictions. Use when predicted structures are needed for proteins without experimental structures, or for confidence scores (pLDDT).
```
def check_alphafold_exists(uniprot_id):
    '''Check if AlphaFold prediction exists'''
    url = f'https://alphafold.ebi.ac.uk/api/prediction/{uniprot_id}'
    response = requests.get(url)
    return response.status_code == 200

if check_alphafold_exists('P04637'):
    print('AlphaFold structure available')
```

### boltz
**用途**: Structure prediction using Boltz-1/Boltz-2, an open biomolecular structure predictor. Use this skill when: (1) Predicting protein complex structures, (2) Validating designed binders, (3) Need open-...
```
>protein_A
MKTAYIAKQRQISFVK...
>protein_B
MVLSPADKTNVKAAWG...
```

### boltzgen
**用途**: All-atom protein design using BoltzGen diffusion model. Use this skill when: (1) Need side-chain aware design from the start, (2) Designing around small molecules or ligands, (3) Want all-atom diff...
```
find output -name "*.cif" | wc -l  # Should match num_samples
```

### cell-free-expression
**用途**: Guidance for cell-free protein synthesis (CFPS) optimization. Use when: (1) Planning CFPS experiments, (2) Troubleshooting low yield or aggregation, (3) Optimizing DNA template design for CFPS, (4)...
```
1. Deplete DTT from extract (dialysis or treatment with IAM 5 mM)
2. Add oxidized/reduced glutathione: 4 mM GSSG, 1 mM GSH (4:1 ratio)
3. Add 10 μM PDI (protein disulfide isomerase)
4. Optional: Add 5 μM DsbC (disulfide isomerase)
5. Express at 25°C (not 37°C) for better folding
6. Incubation time: 4-6 hours
```
**限制**: No chaperones (add separately); No post-translational modifications

### chai
**用途**: Structure prediction using Chai-1, a foundation model for molecular structure. Use this skill when: (1) Predicting protein-protein complex structures, (2) Validating designed binders, (3) Predictin...
```
>protein
MKTAYIAKQRQISFVKSHFSRQLE...
>dna
ATCGATCGATCG
```

### esm
**用途**: Comprehensive toolkit for protein language models including ESM3 (generative multimodal protein design across sequence, structure, and function) and ESM C (efficient protein embeddings and represen...
```
uv pip install esm
```
**注意**: - Start with smaller models for prototyping (`esm3-sm-open-v1`); Use temperature parameter to control diversity (0.0 = deterministic, 1.0 = diverse); Implement iterative refinement with chain-of-thought for complex designs

### foldseek
**用途**: Structure similarity search with Foldseek. Use this skill when: (1) Finding similar structures in PDB/AFDB databases, (2) Structural homology search, (3) Database queries by 3D structure, (4) Findi...
```
wc -l results.m8  # Number of hits
```

### ipsae
**用途**: Binder design ranking using ipSAE (interprotein Score from Aligned Errors). Use this skill when: (1) Ranking binder designs for experimental testing, (2) Filtering BindCraft or RFdiffusion outputs,...
```
python ipsae.py pae_model_0.npz model_0.cif 10 10
```

### ligandmpnn
**用途**: Ligand-aware protein sequence design using LigandMPNN. Use this skill when: (1) Designing sequences around small molecules, (2) Enzyme active site design, (3) Ligand binding pocket optimization, (4...
```
grep -c "^>" output/seqs/*.fa  # Should match backbone_count × num_seq_per_target
```

### protein-design-workflow
**用途**: End-to-end guidance for protein design pipelines. Use this skill when: (1) Starting a new protein design project, (2) Need step-by-step workflow guidance, (3) Understanding the full design pipeline...
```
# Download from PDB
curl -o target.pdb "https://files.rcsb.org/download/XXXX.pdb"
```

### protein-qc
**用途**: Quality control metrics and filtering thresholds for protein design. Use this skill when: (1) Evaluating design quality for binding, expression, or structure, (2) Setting filtering thresholds for p...
```
boltzgen run ... \
  --budget 60 \
  --alpha 0.01 \
  --filter_biased true \
  --refolding_rmsd_threshold 2.0 \
  --additional_filters 'ALA_fraction<0.3'
```

### proteinmpnn
**用途**: Design protein sequences using ProteinMPNN inverse folding. Use this skill when: (1) Designing sequences for RFdiffusion backbones, (2) Redesigning existing protein sequences, (3) Fixing specific r...
```
--pdb_path_chains A,B    # No spaces
```

### rfdiffusion
**用途**: Generate protein backbones using RFdiffusion, a diffusion-based generative model for de novo protein structure generation. Use this skill when: (1) Designing binder scaffolds for a target protein, ...
```
ls output/*.pdb | wc -l  # Should match num_designs
```

### solublempnn
**用途**: Solubility-optimized protein sequence design using SolubleMPNN. Use this skill when: (1) Designing for E. coli expression, (2) Optimizing solubility of designed proteins, (3) Reducing aggregation p...
```
output/
├── seqs/backbone.fa
└── backbone_pdb/backbone_0001.pdb
```

### tooluniverse-antibody-engineering
**用途**: Comprehensive antibody engineering and optimization for therapeutic development. Covers humanization, affinity maturation, developability assessment, and immunogenicity prediction. Use when asked t...
**触发条件**: "Humanize this mouse antibody sequence"; "Optimize antibody affinity for [target]"; "Assess developability of this antibody"; "Predict immunogenicity risk for [sequence]"
```
**Version 2: With key backmutations** (positions 27, 48)
```

### tooluniverse-protein-therapeutic-design
**用途**: Design novel protein therapeutics (binders, enzymes, scaffolds) using AI-guided de novo design. Uses RFdiffusion for backbone generation, ProteinMPNN for sequence design, ESMFold/AlphaFold2 for val...
**触发条件**: "Design a protein binder for [target]"; "Create a therapeutic protein against [protein/epitope]"; "Design a protein scaffold with [property]"; "Optimize this protein sequence for [function]"
```
*Source: NVIDIA NIM via `NvidiaNIM_proteinmpnn`*
```
