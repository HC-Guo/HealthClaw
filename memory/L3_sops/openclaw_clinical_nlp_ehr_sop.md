# 临床 NLP 与电子病历 SOP
> 临床文本提取、病历摘要、诊断推理、EHR/FHIR 集成、护理协调
> 包含 14 个 OpenClaw skill 的压缩迁移。

---

### care-coordination
**用途**: 
```
python3 Skills/Anthropic_Health_Stack/Care_Coordination/coworker.py
```

### chatehr-clinician-assistant
**用途**: 
**触发条件**: **Rapid Review**: "Summarize the patient's cardiology history."; **Data Extraction**: "What was the last creatinine level?"; **Documentation**: Generating draft notes or discharge summaries.
```
python -m chatehr.query --patient_id 12345 --prompt "Summarize last 3 oncology visits"
```

### claims-appeals
**用途**: 
```
python3 Skills/Anthropic_Health_Stack/Claims_Appeals/coworker.py
```

### clinical-diagnostic-reasoning
**用途**: Identify and counteract cognitive biases in medical decision-making through systematic error analysis and contextual algorithm application. For diagnostic reasoning, treatment decisions, and clinic...
**触发条件**: Diagnostic decision-making in clinical practice; Treatment planning and therapeutic choices; Case review and error analysis; Medical education on clinical reasoning
```
Need to present medical information
    ↓
What decision does patient need to make?
    ↓
Identify equivalent framings:
    - Positive frame (% success/survival)
    - Negative frame (% failure/mortality)
    - Absolute numbers
    - Relative risk
    ↓
Which framing facilitates genuine understanding?
    ↓
Is my framing choice unintentionally biasing decision?
    ├─ YES → Present multiple equivalent framings
    │         Allow patient to process from different angles
    │
    └─ UNCERTAIN → P
# ... (truncated)
```

### clinical-nlp-extractor
**用途**: 
```
python3 Skills/Clinical/Clinical_NLP/entity_extractor.py \
    --text "Patient has diabetes type 2. Prescribed Metformin 500mg. No chest pain." \
    --output entities.json
```

### clinical-note-summarization
**用途**: 

### digital-twin-clinical-agent
**用途**: 
```
python3 Skills/Clinical/Digital_Twin_Clinical_Agent/create_twin.py \
    --patient_data patient_ehr.json \
    --genomics patient_wgs.vcf \
    --imaging mri_series/ \
    --cognitive_scores mmse_history.csv \
    --biomarkers abeta_tau_nfl.csv \
    --disease alzheimers \
    --simulate_treatment drug_a \
    --compare_to placebo \
    --prediction_horizon 24_months \
    --output digital_twin_results/
```

### ehr-fhir-integration
**用途**: 
```
python3 Skills/Clinical/EHR_FHIR_Integration/fhir_client.py \
    --server https://hapi.fhir.org/baseR4 \
    --resource Patient \
    --search "name=Smith&birthdate=gt1980-01-01" \
    --output patients.json
```

### emergency-card
**用途**: 生成紧急情况下快速访问的医疗信息摘要卡片。当用户需要旅行、就诊准备、紧急情况或询问"紧急信息"、"医疗卡片"、"急救信息"时使用此技能。提取关键信息（过敏、用药、急症、植入物），支持多格式输出（JSON、文本、二维码），用于急救或快速就医。
```
const qrCode = generateQRCode(JSON.stringify(emergencyCard));
emergencyCard.qr_code = qrCode;
```

### fhir-development
**用途**: 
```
python3 Skills/Anthropic_Health_Stack/FHIR_Development/coworker.py
```

### prior-auth-coworker
**用途**: 
```
python3 Skills/Clinical/Prior_Authorization/anthropic_coworker.py --code "MRI-L-SPINE" --note "Patient has back pain > 2 months. Failed PT."
```

### treatment-plans
**用途**: Generate concise (3-4 page), focused medical treatment plans in LaTeX/PDF format for all clinical specialties. Supports general medical treatment, rehabilitation therapy, mental health care, chroni...
```
python check_completeness.py my_treatment_plan.tex
```

### trial-eligibility-agent
**用途**: 

### trialgpt-matching
**用途**: 
