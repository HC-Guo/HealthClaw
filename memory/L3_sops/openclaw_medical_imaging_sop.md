# 医学影像与病理 SOP
> DICOM、数字病理、放射组学、多模态影像融合、放射报告
> 包含 8 个 OpenClaw skill 的压缩迁移。

---

### computational-pathology-agent
**用途**: 
```
from Skills.Pathology_AI.Computational_Pathology_Agent.wsi_analyzer import WSIAnalyzer

# Initialize
path_agent = WSIAnalyzer(slide_path="./data/biopsy_001.svs")

# Extract tissue patches
path_agent.extract_patches(patch_size=256, level=1)

# Analyze Nuclei (requires model weights)
# path_agent.segment_nuclei()
```

### histolab
**用途**: Digital pathology image processing toolkit for whole slide images (WSI). Use this skill when working with histopathology slides, processing H&E or IHC stained tissue images, extracting tiles from g...
```
uv pip install histolab
```

### multimodal-medical-imaging
**用途**: 
```
python3 Skills/Clinical/Medical_Imaging/Multimodal_Analysis/multimodal_agent.py \
    --image "/path/to/cxr.jpg" \
    --prompt "Check for signs of pneumonia and consolidation."
```

### multimodal-radpath-fusion-agent
**用途**: 
```
python3 Skills/Clinical/Multimodal_Radpath_Fusion_Agent/multimodal_fusion.py \
    --ct_dicom ct_chest/ \
    --pet_dicom pet_scan/ \
    --wsi_path biopsy.svs \
    --genomic_vcf tumor_wes.vcf \
    --rna_expression expression.tsv \
    --clinical_ehr patient_data.json \
    --task treatment_recommendation \
    --cancer_type nsclc \
    --output integrated_assessment/
```

### pathml
**用途**: Computational pathology toolkit for analyzing whole-slide images (WSI) and multiparametric imaging data. Use this skill when working with histopathology slides, H&E stained images, multiplex immuno...
```
# Install PathML
uv pip install pathml

# With optional dependencies for all features
uv pip install pathml[all]
```

### pydicom
**用途**: Python library for working with DICOM (Digital Imaging and Communications in Medicine) files. Use this skill when reading, writing, or modifying medical imaging data in DICOM format, extracting pix...
```
python scripts/anonymize_dicom.py input.dcm output.dcm
```
**注意**: before accessing them using `hasattr()` or `get()`; when modifying files by using `save_as()` with `write_like_original=True`; to understand compression format before processing pixel data

### radgpt-radiology-reporter
**用途**: 
**触发条件**: **Patient Communication**: Converting technical findings into plain language.; **Clinician Review**: Highlighting critical findings (e.g., "Pneumothorax detected").; **Follow-up**: Suggesting appropriate next steps based on findings.
```
python -m radgpt.explain --report ./report.txt --target_audience patient
```

### radiomics-pathomics-fusion-agent
**用途**: 
```
python3 Skills/Oncology/Radiomics_Pathomics_Fusion_Agent/fusion_predict.py \
    --ct_dicom ct_scan/ \
    --wsi_path biopsy.svs \
    --clinical_data patient_clinical.json \
    --genomic_data tumor_wes.vcf \
    --task immunotherapy_response \
    --cancer_type nsclc \
    --fusion_method attention \
    --output fusion_prediction/
```
