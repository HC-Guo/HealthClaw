# gptomics 化学信息学 SOP
> 分子描述符、分子 I/O、子结构搜索、虚拟筛选、反应枚举、限制酶
> 包含 9 个 OpenClaw skill 的压缩迁移。

---

### bio-molecular-descriptors
**用途**: Calculates molecular descriptors and fingerprints using RDKit. Computes Morgan fingerprints (ECFP), MACCS keys, Lipinski properties, QED drug-likeness, TPSA, and 3D conformer descriptors. Use when ...
```
from rdkit.Chem import MACCSkeys

maccs = MACCSkeys.GenMACCSKeys(mol)  # 167 bits

# As numpy array
maccs_array = np.array(maccs)
```

### bio-molecular-io
**用途**: Reads, writes, and converts molecular file formats (SMILES, SDF, MOL2, PDB) using RDKit and Open Babel. Handles structure parsing, canonicalization, and full standardization pipeline including sani...
```
from rdkit import Chem

# To SMILES
smiles = Chem.MolToSmiles(mol)  # Canonical SMILES
smiles_iso = Chem.MolToSmiles(mol, isomericSmiles=True)  # With stereochemistry

# To SDF file
writer = Chem.SDWriter('output.sdf')
for mol in molecules:
    writer.write(mol)
writer.close()

# To MOL block (string)
mol_block = Chem.MolToMolBlock(mol)
```

### bio-reaction-enumeration
**用途**: Enumerates chemical libraries through reaction SMARTS transformations using RDKit. Generates virtual compound libraries from building blocks using defined chemical reactions with product validation...
```
REACTIONS = {
    'amide_coupling': '[C:1](=[O:2])O.[N:3]>>[C:1](=[O:2])[N:3]',
    'reductive_amination': '[C:1]=O.[N:2]>>[C:1][N:2]',
    'suzuki': '[c:1][Br].[c:2][B](O)O>>[c:1][c:2]',
    'buchwald': '[c:1][Br].[N:2]>>[c:1][N:2]',
    'ester_formation': '[C:1](=[O:2])O.[O:3]>>[C:1](=[O:2])[O:3]',
    'michael_addition': '[C:1]=[C:2]C(=O).[C:3]>>[C:1][C:2]([C:3])C(=O)',
}
```

### bio-restriction-enzyme-selection
**用途**: 
```
# Common Type IIS enzymes for Golden Gate/modular cloning
from Bio.Restriction import BsaI, BsmBI, BbsI, SapI, BtgZI

golden_gate_enzymes = [BsaI, BsmBI, BbsI, SapI, BtgZI]

for enzyme in golden_gate_enzymes:
    print(f'{enzyme}: site={enzyme.site}, overhang={enzyme.ovhg}bp')
```

### bio-restriction-fragment-analysis
**用途**: 
```
from Bio.Restriction import EcoRI

fragments = EcoRI.catalyze(seq)[0]

for i, frag in enumerate(fragments, 1):
    print(f'Fragment {i}: {len(frag)} bp')
    print(f'  5\' end: {frag[:20]}...')
    print(f'  3\' end: ...{frag[-20:]}')
```

### bio-restriction-mapping
**用途**: 
```
# Map format (visual)
analysis.print_as('map')

# Linear format (list)
analysis.print_as('linear')

# Tabular format
analysis.print_as('tabulate')

# Get as string instead of printing
map_str = analysis.format_as('map')
linear_str = analysis.format_as('linear')
```

### bio-restriction-sites
**用途**: 
```
from Bio.Restriction import AllEnzymes

# Get enzyme by string name
ecori = AllEnzymes.get('EcoRI')
sites = ecori.search(seq)

# Check if enzyme exists
if 'EcoRI' in AllEnzymes:
    print('EcoRI is in database')
```

### bio-substructure-search
**用途**: Searches molecular libraries for substructure matches using SMARTS patterns with RDKit. Filters compounds by pharmacophore features, functional groups, or scaffold matches with atom mapping. Use wh...
```
from rdkit import Chem

mol = Chem.MolFromSmiles('c1ccc(O)cc1CCO')

# Check if pattern exists
pattern = Chem.MolFromSmarts('[OH]')  # Hydroxyl group
has_hydroxyl = mol.HasSubstructMatch(pattern)
print(f'Contains hydroxyl: {has_hydroxyl}')

# Get all matches (atom indices)
matches = mol.GetSubstructMatches(pattern)
print(f'Hydroxyl positions: {matches}')
```

### bio-virtual-screening
**用途**: Performs structure-based virtual screening using AutoDock Vina 1.2 for molecular docking. Prepares receptor PDBQT files, generates ligand conformers, defines binding site boxes, and ranks compounds...
```
from rdkit import Chem
from rdkit.Chem import AllChem

def prepare_ligand(smiles, output_pdbqt):
    '''
    Prepare ligand for docking.
    Steps: Generate 3D -> Minimize -> Assign charges -> PDBQT
    '''
    mol = Chem.MolFromSmiles(smiles)
    mol = Chem.AddHs(mol)

    # Generate 3D conformer (ETKDGv3 is default in modern RDKit)
    AllChem.EmbedMolecule(mol, AllChem.ETKDGv3())

    # Minimize with MMFF
    AllChem.MMFFOptimizeMolecule(mol)

    # Write to MOL file
    mol_file = output_pdb
# ... (truncated)
```
