# 用药审查 SOP

## 触发条件
- 用户通过 manage_medication(action=add) 新增用药时自动触发
- 用户问「这些药能一起吃吗」「新开了XX药安全吗」
- 用户上传处方单或用药清单

## 流程

### Step 1: 用药信息收集
```
load_user_profile()          → 获取过敏史、慢病、年龄、性别、孕哺状态
manage_medication(action=list) → 获取当前活跃用药
```
补充收集（如 latest_indicators.json 中有）：eGFR、ALT/AST、肌酐、INR

### Step 2: 药物相互作用检索
```
medication_review(drugs=[...], new_drug="拟新增药物")
```
检查维度：

**2a. 药物-药物交互 (DDI)**
- 药代动力学：CYP450 酶抑制/诱导（如克拉霉素抑制CYP3A4→辛伐他汀浓度升高）
- 药效学：协同增毒/拮抗（如ACEi+保钾利尿剂→高钾风险）
- 重复用药：同类药物叠加（如两种NSAID同用）

**2b. 药物-疾病禁忌**
- β受体阻滞剂 + 哮喘 = 禁忌
- eGFR<30 时二甲双胍禁用
- 肝功能异常时他汀类需调量

**2c. 药物-过敏交叉反应**
- 青霉素过敏 → 检查头孢交叉过敏风险（约1-2%）
- 磺胺类交叉过敏

**2d. 特殊人群**
- 妊娠分级（FDA A/B/C/D/X）
- 哺乳安全性
- 老年人 Beers 标准（≥65岁适用）

### Step 3: 指南核验（≥中风险时触发）
```
web_search("drug interaction [药A] [药B] clinical guideline")
browse_and_learn(url="药品说明书/UpToDate/PharmGKB")
```
- 搜索时使用药物通用名，禁止包含用户个人信息
- 标注证据来源和等级

### Step 4: 风险分级输出

🔴 **禁忌级 (Contraindicated)** — 绝对不应合用
  → 必须强烈建议就医，不能仅说「仅供参考」

🟠 **严重级 (Major)** — 可能致严重后果
  → 明确警示，列出风险、机制、替代方案

🟡 **中等级 (Moderate)** — 需监测或调整剂量
  → 建议监测指标和频率

🟢 **轻微级 (Minor)** — 临床意义小
  → 告知即可

每个问题包含：风险等级、涉及药物、交互机制、临床后果、建议措施

### Step 5: 用户确认与记录
```
ask_user → 展示审查报告，确认是否继续用药
update_user_profile → 记录审查结论
manage_medication → 确认后更新用药列表
```

## 与现有流程联动
- parse_checkup_report 发现 eGFR/ALT 异常时 → 交叉检查当前用药是否需调量
- health_risk_screening 时 → 将用药情况纳入风险评估
- 审查经验积累到 L4 episodes → 高频 DDI 可沉淀为规则

## 安全原则
- 审查结果仅供参考，用药调整请咨询医生或药师
- 禁忌级问题措辞必须强烈：「请立即咨询医生」
- 搜索时禁止包含用户个人信息
