# 搜索与知识工具 SOP
> Perplexity 搜索、语义相似度、ClawBio 工具
> 包含 3 个 OpenClaw skill 的压缩迁移。

---

### claw-ancestry-pca
**用途**: Ancestry decomposition PCA against the Simons Genome Diversity Project
```
python ancestry_pca.py --demo --output demo_report
```

### claw-semantic-sim
**用途**: Semantic Similarity Index for disease research literature using PubMedBERT embeddings
```
python semantic_sim.py --demo --output demo_report
```

### perplexity-search
**用途**: Perform AI-powered web searches with real-time information using Perplexity models via LiteLLM and OpenRouter. This skill should be used when conducting web searches for current information, findin...
```
uv pip install litellm
```
