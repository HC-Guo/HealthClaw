# gptomics 研究工具 SOP
> 生物标志物签名工作室
> 包含 1 个 OpenClaw skill 的压缩迁移。

---

### bio-research-tools-biomarker-signature-studio
**用途**: 
```
python Skills/Research_Tools/Biomarker_Signature_Studio/scripts/biomarker_signature_studio.py \
  --expression data/expression.csv \
  --metadata data/metadata.csv \
  --label-column phenotype \
  --selectors boruta,lasso,mrmr \
  --models rf,logit \
  --output-dir outputs/biomarkers_run1
```
