# CRISPR 工具 SOP
> sgRNA 设计、脱靶预测
> 包含 2 个 OpenClaw skill 的压缩迁移。

---

### crispr-guide-design
**用途**: 
**触发条件**: Designing CRISPR knockout/knock-in experiments that need validated guides.; Locating all PAM-compatible target sites in a gene or locus.; Filtering guides by efficiency/off-target metrics before cloning.
```
python3 Skills/Genomics/CRISPR_Design_Agent/crispr_designer.py \
    --sequence "ATGGAGGAGCCGCAGTCAGATCCTAGCGTCGAGCCCCCTCTGAGTCAGGAAACATTTTCAGACCTATGGAAACTGTGAGTGGATCCATTGGAAGGGC" \
    --output guides.json
```

### crispr-offtarget-predictor
**用途**: 
```
python3 Skills/Genomics/CRISPR_Prediction/impl.py --sequence GAGTCCGAGCAGAAGAAGAA --pam NGG
```
