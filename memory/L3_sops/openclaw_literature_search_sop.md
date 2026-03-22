# 文献检索与搜索引擎 SOP
> PubMed/arXiv/bioRxiv/medRxiv/Semantic Scholar 等文献搜索和综述生成
> 包含 13 个 OpenClaw skill 的压缩迁移。

---

### arxiv-search
**用途**: Search arXiv physics, math, and computer science preprints using natural language queries. Powered by Valyu semantic search.
```
scripts/search setup <api-key>
```

### bgpt-paper-search
**用途**: Search scientific papers and retrieve structured experimental data extracted from full-text studies via the BGPT MCP server. Returns 25+ fields per paper including methods, results, sample sizes, q...
```
npx bgpt-mcp
```

### biomedical-search
**用途**: Complete biomedical information search combining PubMed, preprints, clinical trials, and FDA drug labels. Powered by Valyu semantic search.
```
scripts/search setup <api-key>
```

### biorxiv-database
**用途**: Efficient database search tool for bioRxiv preprint server. Use this skill when searching for life sciences preprints by keywords, authors, date ranges, or categories, retrieving paper metadata, do...
```
uv pip install requests
```

### literature-review
**用途**: Conduct comprehensive, systematic literature reviews using multiple academic databases (PubMed, arXiv, bioRxiv, Semantic Scholar, etc.). This skill should be used when conducting systematic literat...
```
- **Results**: 247 articles
```

### literature-search
**用途**: Comprehensive scientific literature search across PubMed, arXiv, bioRxiv, medRxiv. Natural language queries powered by Valyu semantic search.
```
scripts/search setup <api-key>
```

### medical-research-toolkit
**用途**: Query 14+ biomedical databases for drug repurposing, target discovery, clinical trials, and literature research. Access ChEMBL, PubMed, ClinicalTrials.gov, OpenTargets, OpenFDA, OMIM, Reactome, KEG...
```
https://mcp.cloud.curiloo.com/tools/unified/mcp
```

### medical-specialty-briefs
**用途**: Generate daily or on-demand medical research briefs for any medical specialty. Searches latest research from top-tier journals, delivers concise summaries with 1-sentence takeaways, images when ava...

### medrxiv-search
**用途**: Search medRxiv medical preprints with natural language queries. Powered by Valyu semantic search.
```
scripts/search setup <api-key>
```

### openalex-database
**用途**: Query and analyze scholarly literature using the OpenAlex database. This skill should be used when searching for academic papers, analyzing research trends, finding works by authors or institutions...
```
uv pip install requests
```

### patents-search
**用途**: Search global patents with natural language queries. Prior art, patent landscapes, and innovation tracking via Valyu.
```
scripts/search setup <api-key>
```

### pubmed-database
**用途**: Direct REST API access to PubMed. Advanced Boolean/MeSH queries, E-utilities API, batch processing, citation management. For Python workflows, prefer biopython (Bio.Entrez). Use this for direct HTT...
```
Format: journal|year|volume|page|author|key|
Example: Science|2008|320|5880|1185|key1|
```

### pubmed-search
**用途**: Search PubMed for scientific literature. Use when the user asks to find papers, search literature, look up research, find publications, or asks about recent studies. Triggers on "pubmed", "papers",...
**触发条件**: User asks to find papers on a topic; User wants recent publications in a field; User asks for references or citations; User wants to know the state of research on a topic
```
from Bio import Entrez
Entrez.email = "medclaw@freedomai.com"
```
