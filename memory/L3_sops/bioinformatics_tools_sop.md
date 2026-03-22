# 生信工具集 SOP（Agent 集成）

> 对应表格中的 12 类生信任务。集成方式：**API 直接调用** vs **CLI 通过 code_run/run_bioinfo_cli 执行**。

---

## 1. 工具分类总览

| 描述 | 典型用途 | 工具 | 集成方式 | Agent 工具名 |
|------|----------|------|----------|--------------|
| 序列相似性搜索 | 找同源基因/蛋白 | BLAST | **API** (NCBI) | `blast_search` |
| DNA reads 比对 | WGS | BWA | CLI | `run_bioinfo_cli` (tool=bwa) |
| RNA-seq mapping | 转录组 | HISAT2 / STAR | CLI | `run_bioinfo_cli` (tool=hisat2/star) |
| 差异表达分析 | RNA-seq | DESeq2 | CLI (R) | `run_bioinfo_cli` (tool=deseq2) 或 code_run 跑 R |
| SNP/indel 检测 | 基因变异 | GATK | CLI | `run_bioinfo_cli` (tool=gatk) |
| 蛋白结构域分析 | 功能预测 | InterProScan | **API** (EBI) | `interpro_scan` |
| 富集分析 | 通路分析 | DAVID | **API** (需邮箱) | `david_enrichment` |
| 蛋白 3D 结构预测 | 结构生物学 | AlphaFold | CLI (Python/GPU) | `run_bioinfo_cli` (tool=alphafold) |
| 基因组组装 | 从 reads 组装 | SPAdes/MEGAHIT 等 | CLI | `run_bioinfo_cli` (tool=spades) |
| 原核基因组注释 | 注释 | Prokka | CLI | `run_bioinfo_cli` (tool=prokka) |
| 基因功能注释服务 | 注释 | RAST | Web（无稳定 API） | 建议 browse_and_learn + 人工或 code_run 调网页 |

- **可直接 API 调用的**：BLAST、InterProScan、DAVID（共 3 类），已封装为 Agent 工具。
- **通过 CLI 执行的**：BWA、HISAT2、STAR、DESeq2、GATK、AlphaFold、SPAdes、Prokka（8 类），需本机/容器安装对应软件，通过 `run_bioinfo_cli` 或 `code_run` 调用。
- **RAST**：以 Web 为主，无统一 REST 接口时，用 `browse_and_learn` 或 `code_run` 按需对接。

---

## 2. API 类工具使用要点

### 2.1 blast_search（BLAST）

- **何时用**：需要找同源序列、验证基因/蛋白身份、跨物种比对。
- **参数**：`program`(blastn/blastp/blastx/tblastn/tblastx)、`database`(如 nr, swissprot)、`query`(序列或 FASTA 路径)、`evalue`(默认 1e-5)。
- **限制**：NCBI 建议每 10 秒不超过 1 次请求；单次结果轮询不超过 1 次/分钟；24h 超 100 次可能被限流。需提供 `email`。
- **返回**：JSON/文本格式的 hit 列表、e-value、identity 等。

### 2.2 interpro_scan（InterProScan）

- **何时用**：蛋白序列功能/结构域注释、GO/ pathway 推断。
- **参数**：`sequences`(FASTA 路径或序列列表)、`appl`(可选，如 Pfam, ProSite)。
- **限制**：EBI REST 单次最多约 100 条序列；大文件建议本地装 InterProScan 用 `run_bioinfo_cli`。
- **返回**：结构域、GO 等注释摘要。

### 2.3 david_enrichment（DAVID）

- **何时用**：基因列表通路/GO 富集、功能聚类。
- **参数**：`gene_ids`(基因 ID 列表)、`id_type`(如 ENTREZ_GENE_ID)、`species`、`categories`(如 GOTERM_BP_FAT)。
- **前置**：需在 DAVID 官网用邮箱注册并配置 API（若使用官方 Web Service）。
- **返回**：富集项、p-value、FDR 等。

---

## 3. CLI 类工具使用要点

统一通过 **run_bioinfo_cli** 调用，参数：`tool`、`input_path`/`input_fasta`、`output_dir`、`extra_args`（可选）。

| tool 取值 | 典型命令/环境 | 前置条件 |
|-----------|----------------|----------|
| bwa | bwa mem ref.fa R1.fq R2.fq | 已安装 BWA，索引已建 |
| hisat2 | hisat2 -x index -1 R1 -2 R2 | 已安装 HISAT2，索引已建 |
| star | STAR --runMode alignReads ... | 已安装 STAR，索引已建 |
| gatk | gatk HaplotypeCaller ... | 已安装 GATK，Java 可用 |
| deseq2 | Rscript run_deseq2.R count_matrix.csv ... | R + DESeq2 已安装 |
| prokka | prokka genome.fna --outdir out | 已安装 Prokka |
| spades | spades.py -1 R1 -2 R2 -o out | 已安装 SPAdes |
| alphafold | 需 Python 环境与 GPU，见官方文档 | 环境较重，建议单独队列 |

- **原则**：调用前用 `file_read` 确认输入路径存在；输出写至 `output_dir`，避免覆盖。若本机未安装对应二进制，工具会返回「请先安装 XXX 并配置 PATH」，可写入 L2 记录安装路径。

---

## 4. 与 L1/L2 的同步

- **L1**：新增「生信分析」场景时，在 L1 加关键词→工具映射，例如：`同源搜索|blast_search`、`通路富集|david_enrichment`、`RNA-seq 比对|run_bioinfo_cli star`。
- **L2**：若固定使用某 BLAST 数据库路径、DAVID 配置、或本地 InterProScan/CLI 安装路径，可写入 L2 的 `## [BIOINFO_PATHS]` 或 `## [ANALYSIS_CONFIGS]`，供 Agent 按需读取。

---

## 5. 信息分类决策树（本 SOP 对应）

- 任务为「单次生信分析、可复现」→ 按本 SOP 选 API 工具或 run_bioinfo_cli。
- 若形成**可复用的流程/坑点**（如「某物种 BWA 参数」）→ 写入 L3 或本 SOP 的补充小节，并同步 L1。
