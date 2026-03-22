# 分子动力学与结构预测 SOP
> 分子动力学模拟、蛋白结构预测、冷冻电镜
> 包含 4 个 OpenClaw skill 的压缩迁移。

---

### molecular-dynamics
**用途**: Run and analyze molecular dynamics simulations with OpenMM and MDAnalysis. Set up protein/small molecule systems, define force fields, run energy minimization and production MD, analyze trajectorie...
```
conda install -c conda-forge openmm mdanalysis nglview
# or
pip install openmm mdanalysis
```
**注意**: **Always minimize before MD**: Raw PDB structures have steric clashes; **Equilibrate before production**: NVT (50–100 ps) → NPT (100–500 ps) → Production; **Use GPU**: Simulations are 10–100× faster on GPU (CUDA/OpenCL)

### protein-structure-prediction
**用途**: 
```
python3 Skills/Drug_Discovery/Protein_Structure/esmfold_client.py \
    --sequence "MKTIIALSYIFCLVFDYDY" \
    --output structure.pdb
```

### struct-predictor
**用途**: Local protein structure prediction with AlphaFold, Boltz, or Chai. Compare predicted structures, compute RMSD, visualise 3D models.

### time-resolved-cryoem-agent
**用途**: 
```
python3 Skills/Structural_Biology/Time_Resolved_CryoEM_Agent/analyze_dynamics.py \
    --timepoints "0ms,10ms,50ms,100ms,500ms,1s" \
    --particle_stacks timepoint_particles/ \
    --protein_sequence kinase.fasta \
    --ligand drug_compound.sdf \
    --kinetics_model two_state \
    --extract_intermediates true \
    --output kinase_dynamics/
```
