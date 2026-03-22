# 蛋白质与结构数据库 SOP
> UniProt、PDB、AlphaFold DB、STRING、KEGG、Reactome、BRENDA 等
> 包含 17 个 OpenClaw skill 的压缩迁移。

---

### alphafold-database
**用途**: Access AlphaFold's 200M+ AI-predicted protein structures. Retrieve structures by UniProt ID, download PDB/mmCIF files, analyze confidence metrics (pLDDT, PAE), for drug discovery and structural bio...
```
# Download as PDB format instead of mmCIF
pdb_url = f"https://alphafold.ebi.ac.uk/files/{alphafold_id}-model_{version}.pdb"
response = requests.get(pdb_url)
with open(f"{alphafold_id}.pdb", "wb") as f:
    f.write(response.content)
```

### bio-pdb-geometric-analysis
**用途**: Perform geometric calculations on protein structures using Biopython Bio.PDB. Use when measuring distances, angles, and dihedrals, superimposing structures, calculating RMSD, or computing solvent a...
```
from Bio.PDB import PDBParser, NeighborSearch, Superimposer
from Bio.PDB import calc_angle, calc_dihedral
import numpy as np
```

### bio-pdb-structure-io
**用途**: Parse and write protein structure files using Biopython Bio.PDB. Use when reading PDB, mmCIF, and MMTF files, downloading structures from RCSB PDB, or writing structures to various formats.
```
from Bio.PDB import PDBParser, MMCIFParser, PDBIO, MMCIFIO, PDBList
from Bio.PDB.MMCIF2Dict import MMCIF2Dict
```

### bio-pdb-structure-modification
**用途**: Modify protein structures using Biopython Bio.PDB. Use when transforming coordinates, removing atoms or residues, adding new entities, modifying B-factors and occupancies, or building structures pr...
```
from Bio.PDB import PDBParser, PDBIO, StructureBuilder
from Bio.PDB.Structure import Structure
from Bio.PDB.Model import Model
from Bio.PDB.Chain import Chain
from Bio.PDB.Residue import Residue
from Bio.PDB.Atom import Atom
import numpy as np
```

### bio-pdb-structure-navigation
**用途**: Navigate protein structure hierarchy using Biopython Bio.PDB SMCRA model. Use when accessing models, chains, residues, and atoms, iterating over structure levels, or extracting sequences from PDB f...
```
from Bio.PDB import PDBParser, PPBuilder, Selection
from Bio.Data.PDBData import protein_letters_3to1
```

### bioservices
**用途**: Primary Python tool for 40+ bioinformatics services. Preferred for multi-database workflows: UniProt, KEGG, ChEMBL, PubChem, Reactome, QuickGO. Unified API for queries, ID mapping, pathway analysis...
```
uv pip install bioservices
```

### brenda-database
**用途**: Access BRENDA enzyme database via SOAP API. Retrieve kinetic parameters (Km, kcat), reaction equations, organism data, and substrate-specific enzyme information for biochemical research and metabol...
```
uv pip install zeep requests pandas matplotlib seaborn
```

### fda-database
**用途**: Query openFDA API for drugs, devices, adverse events, recalls, regulatory submissions (510k, PMA), substance identification (UNII), for FDA regulatory data analysis and safety research.
```
python scripts/fda_examples.py
```

### kegg-database
**用途**: Direct REST API access to KEGG (academic use only). Pathway analysis, gene-pathway mapping, metabolic pathways, drug interactions, ID conversion. For Python workflows with multiple databases, prefe...
```
from scripts.kegg_api import kegg_info

# Get pathway database info
info = kegg_info('pathway')

# Get organism-specific info
hsa_info = kegg_info('hsa')  # Human genome
```

### open-targets-search
**用途**: Search Open Targets drug-disease associations with natural language queries. Target validation powered by Valyu semantic search.
```
scripts/search setup <api-key>
```

### opentargets-database
**用途**: Query Open Targets Platform for target-disease associations, drug target discovery, tractability/safety data, genetics/omics evidence, known drugs, for therapeutic target identification.
```
# Search by drug name
results = search_entities("aspirin", entity_types=["drug"])
# Returns: [{"id": "CHEMBL25", "name": "ASPIRIN", ...}]
```

### pdb
**用途**: Fetch and analyze protein structures from RCSB PDB. Use this skill when: (1) Need to download a structure by PDB ID, (2) Search for similar structures, (3) Prepare target for binder design, (4) Ext...
```
from Bio.PDB import PDBList

pdbl = PDBList()
pdbl.retrieve_pdb_file("1ABC", pdir="structures/", file_format="pdb")
```

### pdb-database
**用途**: Access RCSB PDB for 3D protein/nucleic acid structures. Search by text/sequence/structure, download coordinates (PDB/mmCIF), retrieve metadata, for structural biology and drug discovery.
```
from rcsbapi.search import TextQuery
query = TextQuery("hemoglobin")
results = list(query())
print(f"Found {len(results)} structures")
```

### reactome-database
**用途**: Query Reactome REST API for pathway analysis, enrichment, gene-pathway mapping, disease pathways, molecular interactions, expression analysis, for systems biology studies.
```
uv pip install reactome2py
```

### string-database
**用途**: Query STRING API for protein-protein interactions (59M proteins, 20B interactions). Network analysis, GO/KEGG enrichment, interaction discovery, 5000+ species, for systems biology.
```
from scripts.string_api import string_version

version = string_version()
print(f"STRING version: {version}")
```

### uniprot-database
**用途**: Direct REST API access to UniProt. Protein searches, FASTA retrieval, ID mapping, Swiss-Prot/TrEMBL. For Python workflows with multiple databases, prefer bioservices (unified interface to 40+ servi...
```
gene:BRCA*
protein_name:kinase*
```

### zinc-database
**用途**: Access ZINC (230M+ purchasable compounds). Search by ZINC ID/SMILES, similarity searches, 3D-ready structures for docking, analog discovery, for virtual screening and drug discovery.
```
curl "https://cartblanche22.docking.org/smiles.txt:smiles=c1ccccc1"
```
