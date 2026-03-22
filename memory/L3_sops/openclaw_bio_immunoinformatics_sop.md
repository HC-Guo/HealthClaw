# gptomics 免疫信息学 SOP
> 表位预测、MHC 结合、新抗原预测、TCR-表位结合、免疫原性评分
> 包含 5 个 OpenClaw skill 的压缩迁移。

---

### bio-immunoinformatics-epitope-prediction
**用途**: Predict B-cell and T-cell epitopes using BepiPred, IEDB tools, and structure-based methods for vaccine and antibody design. Identify immunogenic regions in antigens. Use when designing vaccines, ma...
```
def map_epitopes_from_peptide_array(array_results, overlap=11):
    '''Map epitopes from peptide array experiments

    Peptide arrays test binding of overlapping peptides
    covering the entire antigen sequence.

    Args:
        array_results: Dict mapping peptide -> signal intensity
        overlap: Overlap between consecutive peptides

    Returns:
        Epitope map with per-residue scores
    '''
    # Implementation would process experimental binding data
    pass
```

### bio-immunoinformatics-immunogenicity-scoring
**用途**: Score and prioritize neoantigens and epitopes for immunogenicity using multi-factor models combining MHC binding, processing, expression, and sequence features. Rank candidates for vaccine design. ...
```
def check_anchor_hydrophobicity(peptide):
    '''Check hydrophobicity at MHC anchor positions

    For HLA-A*02:01 and similar alleles:
    - Position 2: Prefers hydrophobic (L, I, V, M)
    - Position 9 (C-terminus): Prefers hydrophobic (L, V, I)

    Strong anchors improve binding stability.
    '''
    hydrophobic = set('LIVMFYW')

    pos2 = peptide[1] if len(peptide) > 1 else ''
    pos_last = peptide[-1]

    return {
        'pos2_hydrophobic': pos2 in hydrophobic,
        'pos_last_hydro
# ... (truncated)
```

### bio-immunoinformatics-mhc-binding-prediction
**用途**: Predict peptide-MHC class I and II binding affinity using MHCflurry and NetMHCpan neural network models. Identify potential T-cell epitopes from protein sequences. Use when predicting MHC binding f...
```
# Install MHCflurry
pip install mhcflurry

# Download prediction models
mhcflurry-downloads fetch

# Download models for specific alleles
mhcflurry-downloads fetch models_class1_pan
```

### bio-immunoinformatics-neoantigen-prediction
**用途**: Identify tumor neoantigens from somatic mutations using pVACtools for personalized cancer immunotherapy. Predict mutant peptides that bind patient HLA and may elicit T-cell responses. Use when iden...
```
# Install pVACtools
pip install pvactools

# Or use conda for dependencies
conda create -n pvactools python=3.8
conda activate pvactools
pip install pvactools

# Download IEDB tools
pvactools download_iedb_tools
```

### bio-immunoinformatics-tcr-epitope-binding
**用途**: Predict TCR-epitope specificity using ERGO-II and deep learning models for T-cell receptor antigen recognition. Match TCRs to their cognate epitopes or predict TCR targets. Use when analyzing TCR r...
```
# ERGO-II uses deep learning to predict TCR-epitope binding
# GitHub: https://github.com/IdoSpringer/ERGO-II

def setup_ergo():
    '''Setup ERGO-II for TCR-epitope prediction

    Requirements:
    - PyTorch
    - Pre-trained models from ERGO-II repository

    ERGO-II features:
    - Uses both CDR3 alpha and beta chains
    - Incorporates MHC context
    - Trained on VDJdb and IEDB data
    '''
    print('ERGO-II setup:')
    print('1. Clone: git clone https://github.com/IdoSpringer/ERGO-II')

# ... (truncated)
```
