# 健康分析器 SOP
> 家庭健康、职业健康、旅行健康、可穿戴设备、减重、康复
> 包含 8 个 OpenClaw skill 的压缩迁移。

---

### family-health-analyzer
**用途**: 分析家族病史、评估遗传风险、识别家庭健康模式、提供个性化预防建议
```
⚠️ 免责声明:
1. 本分析基于家族病史统计,仅供参考
2. 遗传风险评估不预测个体发病
3. 所有医疗决策请咨询专业医师
4. 遗传咨询建议咨询专业遗传咨询师
```

### occupational-health-analyzer
**用途**: 分析职业健康数据、识别工作相关健康风险、评估职业健康状况、提供个性化职业健康建议。支持与睡眠、运动、心理健康等其他健康数据的关联分析。
```
必查项目：
- 听力测试（每年1次）
```

### rehabilitation-analyzer
**用途**: 分析康复训练数据、识别康复模式、评估康复进展，并提供个性化康复建议
```
/rehab progress
```

### speech-pathology-ai
**用途**: Expert speech-language pathologist specializing in AI-powered speech therapy, phoneme analysis, articulation visualization, voice disorders, fluency intervention, and assistive communication techno...
```
pip install praat-parselmouth librosa torch transformers numpy scipy
```

### travel-health-analyzer
**用途**: 分析旅行健康数据、评估目的地健康风险、提供疫苗接种建议、生成多语言紧急医疗信息卡片。支持WHO/CDC数据集成的专业级旅行健康风险评估。
```
输入: "生成英中日泰四语紧急卡片"

输出:
1. 多语言卡片文本
2. 二维码(描述)
3. 保存建议
```

### wearable-analysis-agent
**用途**: 
```
python3 Skills/Consumer_Health/Wearable_Analysis/arrhythmia_detector.py --input apple_health_export.xml --window "last_month"
```

### weightloss-analyzer
**用途**: 分析减肥数据、计算代谢率、追踪能量缺口、管理减肥阶段
```
# 身体成分分析报告

## 基本信息
- 性别：男
- 年龄：52岁
- 身高：175cm
- 体重：75kg

## 身体指标

### BMI
- 当前BMI：24.5
- 分类：超重
- 理想体重：67kg（BMI=22）
- 需减重：8kg

### 体脂率
- 当前体脂率：25%
- 分类：偏高
- 目标体脂率：15-20%

### 围度分析
- 腰围：92cm（腹部肥胖风险）
- 臀围：98cm
- 腰臀比：0.94（腹部肥胖）

## 建议
1. 每周减重0.5-1kg
2. 目标减重时间：8-16周
3. 综合干预：饮食+运动
```

### wellally-tech
**用途**: Integrate digital health data sources (Apple Health, Fitbit, Oura Ring) and connect to WellAlly.tech knowledge base. Import external health device data, standardize to local format, and recommend r...
```
python scripts/import_fitbit.py --api --days 30
```
