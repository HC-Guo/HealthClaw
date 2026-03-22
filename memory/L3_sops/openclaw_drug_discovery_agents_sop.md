# 药物发现智能体 SOP
> AI 驱动药物发现、分子进化、分子胶、PROTAC、冷冻电镜药物设计
> 包含 11 个 OpenClaw skill 的压缩迁移。

---

### chematagent-drug-discovery
**用途**: 
**触发条件**: **Molecule Design**: Generating novel structures with specific properties.; **Property Prediction**: Estimating solubility, toxicity, and bioactivity.; **Synthesis Planning**: Designing retro-synthetic routes.
```
python -m chematagent.design --scaffold "Aspirin" --objective "maximize solubility"
```

### chemcrow-drug-discovery
**用途**: 

### cryoem-ai-drug-design-agent
**用途**: 
```
python3 Skills/Structural_Biology/CryoEM_AI_Drug_Design_Agent/design_from_cryoem.py \
    --density_map gpcr_3.2A.mrc \
    --protein_sequence gpcr.fasta \
    --alphafold_model gpcr_af2.pdb \
    --resolution 3.2 \
    --ligand_screening fragment_library.sdf \
    --binding_site_residues "3.32,5.46,6.48,7.39" \
    --md_refinement true \
    --generative_optimization true \
    --output gpcr_drug_design/
```

### drug-interaction-checker
**用途**: 
```
python3 Skills/Pharma/Drug_Interaction/impl.py --drugs "Warfarin, Aspirin"
```

### drug-photo
**用途**: Medication photo to personalised PGx dosage card via Claude vision — snap a pill, get genotype-informed guidance
```
python clawbio.py run drugphoto --demo --drug Plavix
```

### medea-therapeutic-discovery
**用途**: An AI agent for therapeutic discovery that executes transparent, multi-step omics analyses including research planning, code execution, and literature reasoning.
```
python3 -m medea.agent --dataset breast_cancer_omics.h5ad --mode full_discovery
```

### modern-drug-rehab-computer
**用途**: Comprehensive knowledge system for addiction recovery environments, supporting both residential and outpatient (IOP/PHP) patients. Expert in evidence-based treatment modalities (CBT, DBT, MI, EMDR,...
```
Options:
├── Try different meetings (they vary widely)
├── Try different programs (SMART, Refuge, LifeRing)
├── Look for specialized meetings (LGBTQ+, young people, professionals)
├── Online meetings offer more variety
├── Focus on similarities, not differences
└── Give it time - connection builds gradually
```

### molecular-glue-discovery-agent
**用途**: 
```
python3 Skills/Drug_Discovery/Molecular_Glue_Discovery_Agent/discover_glue.py \
    --target_substrate IKZF1 \
    --e3_ligase CRBN \
    --selectivity_against IKZF3 \
    --scaffold_library imid_derivatives.sdf \
    --interface_model crbn_ikzf1_complex.pdb \
    --n_candidates 100 \
    --output glue_discovery/
```

### molecule-evolution-agent
**用途**: 
```
python3 Skills/Drug_Discovery/Molecule_Design/evolution_agent.py
# (Note: The script currently defaults to GPRC5D, but can be extended for arguments)
```

### protac-design-agent
**用途**: 
```
python3 Skills/Drug_Discovery/PROTAC_Design_Agent/design_protac.py \
    --target BRD4 \
    --target_structure pdb:3MXF \
    --warhead_smiles "JQ1_core_smiles" \
    --e3_ligase CRBN \
    --linker_library peg,alkyl,piperdine \
    --linker_length_range 4,12 \
    --optimize_oral true \
    --output protac_designs/
```

### tpd-ternary-complex-agent
**用途**: 
```
python3 Skills/Drug_Discovery/TPD_Ternary_Complex_Agent/predict_ternary.py \
    --poi_structure brd4_bd1.pdb \
    --warhead_pose brd4_warhead_docked.sdf \
    --e3_ligase VHL \
    --e3_ligand vhl_ligand.sdf \
    --protac_smiles "PROTAC_SMILES_STRING" \
    --linker_conformations 100 \
    --md_refinement true \
    --output ternary_complex_results/
```
