# gptomics NCBI Entrez SOP
> Entrez 搜索/获取/链接、GEO 数据、UniProt 访问
> 包含 5 个 OpenClaw skill 的压缩迁移。

---

### bio-entrez-fetch
**用途**: 
```
from Bio import Entrez

Entrez.email = 'your.email@example.com'  # Required by NCBI
Entrez.api_key = 'your_api_key'          # Optional, raises rate limit 3->10 req/sec
```

### bio-entrez-link
**用途**: 
```
from Bio import Entrez

Entrez.email = 'your.email@example.com'  # Required by NCBI
Entrez.api_key = 'your_api_key'          # Optional, raises rate limit
```

### bio-entrez-search
**用途**: 
```
term = 'immun*'                         # Wildcard
term = '"breast cancer"[title]'         # Exact phrase
```

### bio-geo-data
**用途**: 
```
from Bio import Entrez

Entrez.email = 'your.email@example.com'  # Required by NCBI
Entrez.api_key = 'your_api_key'          # Optional
```

### bio-uniprot-access
**用途**: 
```
# Human kinases with structures
query = 'organism_id:9606 AND keyword:kinase AND database:pdb AND reviewed:true'
results = search_uniprot(query, size=100)
```
