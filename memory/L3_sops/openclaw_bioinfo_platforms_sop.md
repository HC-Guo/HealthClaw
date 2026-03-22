# 生信平台与通用智能体 SOP
> BioKernel、BioMaster、BioMNI、CompBioAgent、MCPMed、KRAGEN
> 包含 10 个 OpenClaw skill 的压缩迁移。

---

### biokernel
**用途**: 
```
python3 platform/biokernel/server.py --port 8000
```

### biomaster-workflows
**用途**: 

### biomcp-server
**用途**: 
**触发条件**: Unified literature search (PubMed/PMC) inside MCP clients.; Entity normalization via PubTator3 or genomic variant lookups.; ClinicalTrials.gov queries without bespoke API wrappers.

### biomedical-data-analysis
**用途**: 

### biomni
**用途**: Autonomous biomedical AI agent framework for executing complex research tasks across genomics, drug discovery, molecular biology, and clinical analysis. Use this skill when conducting multi-step bi...
```
uv pip install biomni --upgrade
```

### biomni-general-agent
**用途**: 

### biomni-research-agent
**用途**: 

### compbioagent-explorer
**用途**: 
**触发条件**: **Interactive Exploration**: When you need to visually explore a dataset without writing code.; **Hypothesis Generation**: Quickly checking expression of specific markers across clusters.; **Sharing**: Presenting data to non-computational collaborators.
```
compbioagent launch --port 8080 --data ./kidney_atlas.h5ad
```

### kragen-knowledge-graph
**用途**: 
**触发条件**: **Complex Reasoning**: Questions requiring multi-hop deduction (e.g., "How does gene A influence disease B via protein C?").; **Hypothesis Verification**: Checking if a proposed mechanism is supported by existing knowledge graphs.; **Literature Synthesis**: Combining facts from structured DBs and unstructured text.
```
python -m kragen.solve --question "BRCA1 mutations to ovarian cancer mechanism"
```

### mcpmed-bioinformatics-server
**用途**: Model Context Protocol (MCP) server for bioinformatics web services like GEO, STRING, and UCSC Cell Browser.
```
python3 -m mcpmed.cli query string --gene TP53
```
