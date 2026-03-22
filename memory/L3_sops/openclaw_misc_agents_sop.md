# 其他专业智能体 SOP
> MAGE 抗体、UKB 导航、SIMO 多组学、HypoGenic 等
> 包含 6 个 OpenClaw skill 的压缩迁移。

---

### aeon
**用途**: This skill should be used for time series machine learning tasks including classification, regression, clustering, forecasting, anomaly detection, segmentation, and similarity search. Use when work...
```
uv pip install aeon
```

### hypogenic
**用途**: Automated hypothesis generation and testing using large language models. Use this skill when generating scientific hypotheses from datasets, combining literature insights with empirical data, testi...
```
uv pip install hypogenic
```

### mage-antibody-generator
**用途**: 

### pyzotero
**用途**: Interact with Zotero reference management libraries using the pyzotero Python client. Retrieve, create, update, and delete items, collections, tags, and attachments via the Zotero Web API v3. Use t...
```
uv add pyzotero
# or with CLI support:
uv add "pyzotero[cli]"
```

### simo-multiomics-integration-agent
**用途**: 
```
python3 Skills/Genomics/SIMO_Multiomics_Integration_Agent/simo_integration.py \
    --spatial_data visium_data.h5ad \
    --scrna_ref scrna_atlas.h5ad \
    --scatac_ref scatac_atlas.h5ad \
    --modalities rna,atac \
    --n_spots_per_cell 5 \
    --uncertainty_quantification true \
    --output integrated_spatial_multiome.h5ad
```

### ukb-navigator
**用途**: Semantic search across UK Biobank's 12,000+ data fields and publications — find the right variables for your research question.
```
python ukb_navigator.py --demo --output /tmp/ukb_demo
```
