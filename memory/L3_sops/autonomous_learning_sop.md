# 自主学习 SOP (Autonomous Learning v2)

## 触发条件
1. 空闲超过阈值（由 daemon 自动触发）
2. L1 索引无当前查询的匹配条目
3. 工具调用后置信度仍 < 0.6
4. 用户明确要求"学习"或"充电"
5. 新能力域上线但缺少实践经验

## 学习方向选择（12 能力域覆盖）

### 优先级规则
1. **知识空白优先**: L1/L3 中缺失但用户可能会问的方向
2. **低置信度优先**: disease_strategy.json 中 avg_confidence < 0.6 的疾病
3. **轮换原则**: 检查 autonomous_reports/history.txt，避免重复学习

### 可选方向池

| 方向 | 学习目标 | 产出 |
|------|---------|------|
| 疾病诊断知识 | 新疾病的诊断标准/基因panel/蛋白标志物 | L3 疾病SOP + L1映射 |
| 临床指南更新 | 最新版指南的关键变更（ESC/AHA/NCCN等） | L3 SOP更新 + L1 RULES |
| 药物安全知识 | 高频DDI/新药禁忌/特殊人群用药 | L3 medication_review_sop补充 |
| ICD编码规则 | 编码争议案例/新增编码/常见错误 | L4 经验 |
| 影像判读标准 | 分级标准更新(Lung-RADS/TI-RADS等) | L3 imaging SOP补充 |
| 医保政策更新 | 目录调整/限定条件变化 | L2 EVIDENCE_SOURCES + L3 |
| 合规审查知识 | 药品推广法规/学术声明规范 | L3 compliance SOP补充 |
| 生信工具更新 | OpenClaw 新技能/工具版本变化 | L3 openclaw SOP |
| 健康科普素材 | 常见健康误区/循证生活方式建议 | L1 RULES |
| 证据来源验证 | 验证 L2 EVIDENCE_SOURCES 中的链接可用性 | L2 更新 |

## 学习流程

### Step 1: 确定学习目标
- 从方向池中选择一个方向
- 设定具体目标（如"学习 2024 ESC 房颤指南的抗凝策略更新"）
- 预估轮次（一般 5-10 轮足够）

### Step 2: 搜索定位
```
web_search("具体搜索词")
```
- 目标是获取高质量 URL，不是在摘要中找答案
- 优先级：权威指南 > 系统综述 > 专家共识 > 一般文献
- 搜索词使用通用医学术语，禁止包含用户信息

### Step 3: 深度阅读
**首选 browse_and_learn（不依赖浏览器连接）**：
```
browse_and_learn(url="具体URL")
```
- 自动获取内容 + 触发知识提炼
- 不需要篡改猴/TMWebDriver
- 每个主题阅读 1-2 篇即可

**备选（仅在篡改猴已连接时）**：
```
browser_navigate(url="...")  → browser_get_content() → 提炼
```
⚠️ 如果篡改猴未连接，**禁止使用** browser_* 系列工具，会导致卡死。

### Step 3.5: Token 控制
- 每个学习主题深度阅读不超过 2-3 个页面
- 提炼完知识后及时进入 Step 4，避免无目标浏览
- 总轮次控制在 15 轮以内

### Step 4: 知识固化
根据 L0 信息分类决策树决定存储位置：
- **通用规则** → `file_patch` L1 [RULES]（1句压缩）
- **疾病/流程 SOP** → `file_write` L3_sops/
- **环境事实** → `file_patch` L2
- **健康管理工具映射** → `file_patch` L1 [HEALTH_MANAGEMENT]
- 必须标注来源和证据等级（T1-T6）

### Step 5: 产出报告
```
file_write("./autonomous_reports/report_YYYYMMDD_HHMMSS.md", 内容)
```
报告模板：
```
# 自主学习报告
- 方向: [学习方向]
- 目标: [具体目标]
- 来源: [URL/文献]
- 产出: [更新了哪些文件]
- 证据等级: T[n]
- 耗时轮次: N
```

## 推荐学习源

| 资源 | URL | 适用场景 | 证据等级 |
|------|-----|---------|---------|
| GeneReviews | ncbi.nlm.nih.gov/books/ | 遗传病诊断 | T1-T2 |
| PubMed | pubmed.ncbi.nlm.nih.gov/ | 文献检索 | T4 |
| NICE Guidelines | nice.org.uk/guidance/ | 英国指南 | T1 |
| WHO | who.int/publications | 全球指南 | T1 |
| PharmGKB | pharmgkb.org/ | 药物基因组 | T2-T4 |
| UpToDate | uptodate.com/ | 临床决策 | T1-T2 |
| 国家药监局 | nmpa.gov.cn/ | 药品说明书 | T3 |
| 国家医保局 | nhsa.gov.cn/ | 医保目录 | T3 |

## 禁止事项
- 不存储未经验证的推测
- 不照抄大段原文，提炼关键规则
- 不使用不确定的浏览器工具（篡改猴未连接时）
- 搜索时禁止包含用户个人信息
