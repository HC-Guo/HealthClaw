#!/usr/bin/env python3
"""
OpenClaw Medical Skills → SEDA Framework Batch Converter
=========================================================
Reads all 869+ SKILL.md files from OpenClaw, extracts structured data,
merges by domain, and generates:
  - L1 index entries  (memory/L1_openclaw_skills_index.md)
  - L3 SOP files      (memory/L3_sops/openclaw_*.md)
  - Tool schemas      (assets/openclaw_tools_schema.json)
"""

import os, re, json, yaml, pathlib, textwrap
from collections import defaultdict

OPENCLAW_DIR = "/Users/guohc/Downloads/OpenClaw-Medical-Skills/skills"
SEDA_DIR = "/Users/guohc/Downloads/Self-evolving_diagnosis_agent"

# ── Merge mapping: skill name prefix/keyword → merged group ──────────────
# Each group becomes ONE L3 SOP + ONE schema section
MERGE_RULES = {
    # ── General Tools ──
    "general_tools": {
        "label": "通用工具集",
        "desc": "浏览器自动化、多引擎搜索、深度研究、文档处理（PDF/DOCX/XLSX/PPTX）",
        "match": [
            "agent-browser", "multi-search-engine", "deep-research",
            "find-skills", "wikipedia-search", "pdf", "docx", "xlsx", "pptx",
            "doc-coauthoring",
        ],
    },
    # ── Literature & Search ──
    "literature_search": {
        "label": "文献检索与搜索引擎",
        "desc": "PubMed/arXiv/bioRxiv/medRxiv/Semantic Scholar 等文献搜索和综述生成",
        "match": [
            "pubmed-search", "pubmed-database", "literature-search",
            "literature-review", "arxiv-search", "medrxiv-search",
            "biomedical-search", "biorxiv-database", "openalex-database",
            "bgpt-paper-search", "medical-specialty-briefs",
            "medical-research-toolkit", "patents-search",
        ],
    },
    # ── Clinical & Medical ──
    "clinical_medical": {
        "label": "临床医疗工具",
        "desc": "临床报告、决策支持、FHIR、预授权、USMLE、患者文档、医学实体提取",
        "match": [
            "clinical-reports", "clinical-decision-support", "clinical-trials",
            "clinicaltrials-database", "clinical-trial-protocol",
            "prior-auth-review", "fhir-developer", "usmle",
            "medical-entity-extractor", "patiently-ai", "medical-imaging-review",
        ],
    },
    # ── Drug Discovery & Safety ──
    "drug_discovery": {
        "label": "药物发现与安全",
        "desc": "药物研究、再利用、DDI 预测、药物警戒、ADMET、不良事件检测",
        "match": [
            "tooluniverse-drug-", "tooluniverse-adverse-event",
            "tooluniverse-pharmacovigilance", "tooluniverse-binder-discovery",
            "tooluniverse-chemical-", "drug-discovery-search",
            "drug-labels-search", "drugbank-", "chembl-",
            "agentd-drug-discovery",
        ],
    },
    # ── Genomic Databases ──
    "genomic_databases": {
        "label": "基因组与变异数据库",
        "desc": "ClinVar、Ensembl、NCBI Gene、GEO、ENA、GWAS Catalog、COSMIC 等",
        "match": [
            "clinvar-database", "clinpgx-database", "cosmic-database",
            "ensembl-database", "gene-database", "geo-database",
            "ena-database", "gwas-database", "gget", "pysam",
            "bindingdb-database",
        ],
    },
    # ── Protein & Structure Databases ──
    "protein_databases": {
        "label": "蛋白质与结构数据库",
        "desc": "UniProt、PDB、AlphaFold DB、STRING、KEGG、Reactome、BRENDA 等",
        "match": [
            "alphafold-database", "pdb-database", "pdb",
            "uniprot-database", "string-database",
            "kegg-database", "reactome-database", "brenda-database",
            "opentargets-database", "fda-database", "bioservices",
            "open-targets-search", "zinc-database",
        ],
    },
    # ── Metabolomics Databases ──
    "metabolomics_databases": {
        "label": "代谢组学数据库",
        "desc": "HMDB、PubChem、Metabolomics Workbench 及代谢组分析",
        "match": [
            "hmdb-database", "pubchem-database",
            "metabolomics-workbench-database",
            "tooluniverse-metabolomics",
        ],
    },
    # ── Variant Analysis ──
    "variant_analysis": {
        "label": "变异分析与解读",
        "desc": "VCF 处理、ACMG 分级、体细胞变异解读、结构变异、PRS",
        "match": [
            "tooluniverse-variant-", "tooluniverse-cancer-variant",
            "tooluniverse-structural-variant", "tooluniverse-polygenic-risk",
        ],
    },
    # ── GWAS Tools ──
    "gwas_tools": {
        "label": "GWAS 分析工具",
        "desc": "GWAS 关联分析、精细定位、SNP 解读、药物靶点发现",
        "match": [
            "tooluniverse-gwas-",
        ],
    },
    # ── Clinical Trial Matching & Design ──
    "clinical_trials_tools": {
        "label": "临床试验设计与匹配",
        "desc": "试验可行性评估、患者匹配、指南检索",
        "match": [
            "tooluniverse-clinical-trial-",
            "tooluniverse-clinical-guidelines",
            "clinical-trials-search",
        ],
    },
    # ── Disease Research ──
    "disease_research": {
        "label": "疾病研究与精准医学",
        "desc": "疾病研究报告、罕见病诊断、精准肿瘤学、免疫治疗响应预测",
        "match": [
            "tooluniverse-disease-research",
            "tooluniverse-rare-disease",
            "tooluniverse-precision-oncology",
            "tooluniverse-precision-medicine",
            "tooluniverse-infectious-disease",
            "tooluniverse-immunotherapy-response",
        ],
    },
    # ── Single-cell & Spatial Omics ──
    "single_cell_spatial": {
        "label": "单细胞与空间组学",
        "desc": "scRNA-seq 分析 (Scanpy/scVI)、空间转录组、轨迹分析、细胞注释、CellxGENE",
        "match": [
            "anndata", "scanpy", "scvi-tools", "single-cell-rna-qc",
            "cellxgene-census", "single-", "spatial-",
            "tooluniverse-single-cell", "tooluniverse-spatial-",
        ],
    },
    # ── Bulk RNA-seq ──
    "bulk_rnaseq": {
        "label": "Bulk RNA-seq 分析",
        "desc": "DESeq2 差异表达、批次校正、WGCNA、PPI、反卷积",
        "match": [
            "pydeseq2", "bulk-", "tooluniverse-rnaseq-deseq2",
            "tooluniverse-expression-data",
        ],
    },
    # ── Multi-omics & Systems Biology ──
    "multi_omics": {
        "label": "多组学整合与系统生物学",
        "desc": "多组学整合、通路分析、基因富集、网络药理学、系统生物学建模",
        "match": [
            "tooluniverse-multi-omics", "tooluniverse-multiomic-",
            "tooluniverse-gene-enrichment", "tooluniverse-systems-biology",
            "tooluniverse-network-pharmacology",
            "gsea-enrichment", "tcga-preprocessing",
        ],
    },
    # ── Proteomics & Mass Spec ──
    "proteomics": {
        "label": "蛋白质组学与质谱",
        "desc": "质谱分析 (matchms/pyOpenMS)、蛋白互作、蛋白结构检索",
        "match": [
            "matchms", "pyopenms", "flowio",
            "tooluniverse-proteomics-analysis",
            "tooluniverse-protein-interactions",
            "tooluniverse-protein-structure-retrieval",
        ],
    },
    # ── Protein Design & Engineering ──
    "protein_design": {
        "label": "蛋白质设计与工程",
        "desc": "AlphaFold/RFdiffusion/ProteinMPNN/BindCraft 结构预测与从头设计",
        "match": [
            "alphafold", "esm", "boltz", "chai", "rfdiffusion",
            "bindcraft", "binder-design", "proteinmpnn", "ligandmpnn",
            "solublempnn", "foldseek", "ipsae", "protein-design-workflow",
            "protein-qc", "cell-free-expression", "binding-characterization",
            "adaptyv", "aav-vector-design", "antibody-design",
            "tooluniverse-protein-therapeutic",
            "tooluniverse-antibody-engineering",
        ],
    },
    # ── Cheminformatics ──
    "cheminformatics": {
        "label": "化学信息学",
        "desc": "RDKit、分子对接 (DiffDock)、分子特征、QSAR、深度学习药物发现",
        "match": [
            "rdkit", "datamol", "medchem", "diffdock", "molfeat",
            "deepchem", "torchdrug", "torch_geometric", "pytdc", "cobrapy",
        ],
    },
    # ── Bioinformatics Pipelines ──
    "bioinfo_pipelines": {
        "label": "生信流程与工具",
        "desc": "Biopython、nf-core、FASTQ 分析、DeepTools、GRN 推断、LaminDB",
        "match": [
            "biopython", "scikit-bio", "etetoolkit", "deeptools",
            "nextflow-development", "fastq-analysis", "geniml", "gtars",
            "arboreto", "lamindb", "dnanexus-integration", "latchbio-integration",
        ],
    },
    # ── Immune & Repertoire ──
    "immunology": {
        "label": "免疫学与免疫库分析",
        "desc": "TCR/BCR 分析、CRISPR 筛选、免疫库测序",
        "match": [
            "tooluniverse-immune-repertoire",
            "tooluniverse-crispr-screen",
        ],
    },
    # ── Epigenomics ──
    "epigenomics": {
        "label": "表观基因组学",
        "desc": "甲基化分析、染色质可及性、组蛋白修饰",
        "match": [
            "tooluniverse-epigenomics",
        ],
    },
    # ── Phylogenetics ──
    "phylogenetics": {
        "label": "系统发育分析",
        "desc": "序列比对、进化树构建、进化度量",
        "match": [
            "tooluniverse-phylogenetics",
        ],
    },
    # ── Target Research ──
    "target_research": {
        "label": "药物靶点研究",
        "desc": "靶点情报、验证、成药性、序列检索",
        "match": [
            "tooluniverse-target-research",
            "tooluniverse-drug-target-validation",
            "tooluniverse-sequence-retrieval",
        ],
    },
    # ── Statistical & Image Analysis ──
    "statistics_imaging": {
        "label": "统计建模与影像分析",
        "desc": "生物医学统计建模、显微镜图像分析、生存分析",
        "match": [
            "tooluniverse-statistical-modeling",
            "tooluniverse-image-analysis",
            "scikit-survival",
        ],
    },
    # ── Literature Deep Research ──
    "literature_deep": {
        "label": "深度文献研究",
        "desc": "靶点消歧、证据分级、假说生成",
        "match": [
            "tooluniverse-literature-deep-research",
        ],
    },
    # ── Health & Wellness ──
    "health_wellness": {
        "label": "健康管理与生活方式",
        "desc": "营养、睡眠、健身、心理健康、中医体质",
        "match": [
            "adhd-daily-planner", "nutrition", "sleep", "fitness",
            "wellness", "mental-health", "tcm", "health-",
        ],
    },
    # ── Medical Device & Regulatory ──
    "meddev_regulatory": {
        "label": "医疗器械与法规",
        "desc": "FDA 510(k)、CE 认证、IEC 62304、ISO 14971、EU MDR 合规",
        "match": [
            "meddev-", "iec-", "iso-", "fda-regulatory",
            "eu-mdr", "510k", "regulatory",
        ],
    },
    # ── Bio single-cell ──
    "bio_single_cell": {
        "label": "gptomics 单细胞分析",
        "desc": "单细胞 RNA-seq QC、聚类、注释、轨迹、细胞通讯",
        "match": ["bio-single-cell"],
    },
    # ── Bio spatial transcriptomics ──
    "bio_spatial": {
        "label": "gptomics 空间转录组",
        "desc": "空间转录组预处理、解卷积、空间变异基因、域注释",
        "match": ["bio-spatial-transcriptomics"],
    },
    # ── Bio data visualization ──
    "bio_visualization": {
        "label": "gptomics 生物数据可视化",
        "desc": "热图、火山图、PCA/UMAP、GO 富集图、生存曲线、circos",
        "match": ["bio-data-visualization"],
    },
    # ── Bio clinical databases ──
    "bio_clinical_db": {
        "label": "gptomics 临床数据库",
        "desc": "ClinVar、PharmGKB、OMIM、HPO、OrphaNet 查询",
        "match": ["bio-clinical-databases"],
    },
    # ── Bio genome assembly & engineering ──
    "bio_genome": {
        "label": "gptomics 基因组组装与工程",
        "desc": "基因组组装、基因组工程、比较基因组学、基因组区间",
        "match": [
            "bio-genome-assembly", "bio-genome-engineering",
            "bio-comparative-genomics", "bio-genome-intervals",
        ],
    },
    # ── Bio variant calling ──
    "bio_variant": {
        "label": "gptomics 变异检测",
        "desc": "变异检测、拷贝数变异、相位/填充、群体遗传学",
        "match": [
            "bio-variant-calling", "bio-copy-number",
            "bio-phasing-imputation", "bio-population-genetics",
        ],
    },
    # ── Bio read QC & alignment ──
    "bio_reads": {
        "label": "gptomics 测序读长 QC 与比对",
        "desc": "FASTQ QC、reads 比对、比对文件操作、索引、排序、MSA",
        "match": [
            "bio-read-qc", "bio-read-alignment", "bio-alignment-",
            "bio-long-read",
        ],
    },
    # ── Bio CRISPR screens ──
    "bio_crispr": {
        "label": "gptomics CRISPR 筛选",
        "desc": "CRISPR 文库分析、essentiality scoring、引物设计",
        "match": ["bio-crispr-screens", "bio-primer-design"],
    },
    # ── Bio epigenomics (ChIP/ATAC/Hi-C/CLIP) ──
    "bio_epigenomics": {
        "label": "gptomics 表观基因组学",
        "desc": "ChIP-seq、ATAC-seq、Hi-C、CLIP-seq、表观转录组、小 RNA",
        "match": [
            "bio-chipseq", "bio-atac-seq", "bio-hi-c", "bio-clip-seq",
            "bio-epitranscriptomics", "bio-small-rna",
        ],
    },
    # ── Bio flow cytometry ──
    "bio_flow_cytometry": {
        "label": "gptomics 流式细胞术",
        "desc": "流式数据分析、设门、补偿、高维聚类",
        "match": ["bio-flow-cytometry"],
    },
    # ── Bio metagenomics & microbiome ──
    "bio_metagenomics": {
        "label": "gptomics 宏基因组与微生物组",
        "desc": "宏基因组分析、16S/ITS、微生物组、多样性",
        "match": ["bio-metagenomics", "bio-microbiome"],
    },
    # ── Bio proteomics & metabolomics ──
    "bio_proteomics_metab": {
        "label": "gptomics 蛋白质组与代谢组",
        "desc": "质谱蛋白质组、成像质谱、代谢组学",
        "match": ["bio-proteomics", "bio-imaging-mass", "bio-metabolomics"],
    },
    # ── Bio immunology (TCR/BCR) ──
    "bio_immunology": {
        "label": "gptomics 免疫信息学",
        "desc": "TCR/BCR 库分析、免疫组库、克隆性",
        "match": ["bio-tcr-bcr"],
    },
    # ── Bio RNA quantification & differential expression ──
    "bio_rnaseq": {
        "label": "gptomics RNA 定量与差异表达",
        "desc": "RNA 定量、差异表达分析、Ribo-seq、表达矩阵",
        "match": [
            "bio-rna-quantification", "bio-differential-expression",
            "bio-ribo-seq", "bio-expression-matrix",
        ],
    },
    # ── Bio pathway & systems biology ──
    "bio_pathway": {
        "label": "gptomics 通路与系统生物学",
        "desc": "通路分析、因果基因组学、流行病学基因组学、系统生物学",
        "match": [
            "bio-pathway", "bio-causal-genomics",
            "bio-epidemiological-genomics", "bio-systems-biology",
        ],
    },
    # ── Bio multi-omics ──
    "bio_multi_omics": {
        "label": "gptomics 多组学整合",
        "desc": "多组学整合、实验设计",
        "match": ["bio-multi-omics", "bio-experimental-design"],
    },
    # ── Bio ML & workflows ──
    "bio_ml_workflows": {
        "label": "gptomics ML 与工作流",
        "desc": "生物信息 ML、工作流管理、ADMET 预测",
        "match": [
            "bio-machine-learning", "bio-workflow-management",
            "bio-workflows", "bio-admet-prediction",
        ],
    },
    # ── Bio structure ──
    "bio_structure": {
        "label": "gptomics 结构生物学",
        "desc": "PDB 结构分析、系统发育树、结构生物学",
        "match": [
            "bio-pdb-structure", "bio-phylo-tree",
            "bio-structural-biology", "bio-phylo-distance",
            "bio-phylo-modern-tree",
        ],
    },
    # ── Bio sequence operations ──
    "bio_sequence_ops": {
        "label": "gptomics 序列操作",
        "desc": "序列读写、过滤、切片、反向互补、翻译、相似性搜索、BLAST",
        "match": [
            "bio-seq-objects", "bio-sequence-", "bio-filter-sequences",
            "bio-reverse-complement", "bio-transcription-translation",
            "bio-similarity-searching", "bio-blast-searches",
            "bio-local-blast", "bio-consensus-sequences",
            "bio-codon-usage", "bio-motif-search",
            "bio-write-sequences", "bio-read-sequences",
        ],
    },
    # ── Bio file formats & I/O ──
    "bio_file_io": {
        "label": "gptomics 文件格式与 I/O",
        "desc": "FASTQ/BAM/VCF/BED 文件操作、格式转换、压缩、批量下载",
        "match": [
            "bio-format-conversion", "bio-compressed-files",
            "bio-batch-downloads", "bio-batch-processing",
            "bio-bedgraph-handling", "bio-sam-bam-basics",
            "bio-fastq-quality", "bio-paired-end-fastq",
            "bio-pileup-generation", "bio-duplicate-handling",
            "bio-basecalling", "bio-sra-data",
            "bio-reference-operations",
        ],
    },
    # ── Bio VCF & variant annotation ──
    "bio_vcf_ops": {
        "label": "gptomics VCF 与变异注释",
        "desc": "VCF 解析、操作、统计、变异注释、标准化、GATK",
        "match": [
            "bio-vcf-basics", "bio-vcf-manipulation", "bio-vcf-statistics",
            "bio-variant-annotation", "bio-variant-normalization",
            "bio-gatk-variant-calling",
        ],
    },
    # ── Bio methylation ──
    "bio_methylation": {
        "label": "gptomics 甲基化分析",
        "desc": "Bismark 比对、甲基化检测、DMR、MethylKit",
        "match": [
            "bio-methylation-",
        ],
    },
    # ── Bio splicing & isoform ──
    "bio_splicing": {
        "label": "gptomics 剪接与亚型分析",
        "desc": "差异剪接、剪接定量、亚型转换、sashimi 图",
        "match": [
            "bio-differential-splicing", "bio-isoform-switching",
            "bio-splicing-", "bio-sashimi-plots",
        ],
    },
    # ── Bio DE (differential expression core) ──
    "bio_diff_expr": {
        "label": "gptomics 差异表达核心",
        "desc": "DESeq2/edgeR 基础、DE 结果处理、RNA-seq QC",
        "match": [
            "bio-de-deseq2", "bio-de-edger", "bio-de-results",
            "bio-rnaseq-qc",
        ],
    },
    # ── Bio NCBI Entrez ──
    "bio_entrez": {
        "label": "gptomics NCBI Entrez",
        "desc": "Entrez 搜索/获取/链接、GEO 数据、UniProt 访问",
        "match": [
            "bio-entrez-", "bio-geo-data", "bio-uniprot-access",
        ],
    },
    # ── Bio liquid biopsy & cfDNA ──
    "bio_liquid_biopsy": {
        "label": "gptomics 液体活检与 cfDNA",
        "desc": "cfDNA 预处理、ctDNA 突变检测、液体活检管线、肿瘤分数估计",
        "match": [
            "bio-cfdna-preprocessing", "bio-ctdna-mutation-detection",
            "bio-liquid-biopsy-pipeline", "bio-tumor-fraction-estimation",
            "bio-longitudinal-monitoring", "bio-methylation-based-detection",
            "bio-fragment-analysis",
        ],
    },
    # ── Bio immunoinformatics ──
    "bio_immunoinformatics": {
        "label": "gptomics 免疫信息学",
        "desc": "表位预测、MHC 结合、新抗原预测、TCR-表位结合、免疫原性评分",
        "match": [
            "bio-immunoinformatics-",
        ],
    },
    # ── Bio long-read ──
    "bio_longread": {
        "label": "gptomics 长读长测序",
        "desc": "长读长比对、QC、Medaka、结构变异",
        "match": [
            "bio-longread-",
        ],
    },
    # ── Bio cheminformatics ──
    "bio_cheminformatics": {
        "label": "gptomics 化学信息学",
        "desc": "分子描述符、分子 I/O、子结构搜索、虚拟筛选、反应枚举、限制酶",
        "match": [
            "bio-molecular-descriptors", "bio-molecular-io",
            "bio-substructure-search", "bio-virtual-screening",
            "bio-reaction-enumeration", "bio-restriction-",
        ],
    },
    # ── Bio reporting ──
    "bio_reporting": {
        "label": "gptomics 报告生成",
        "desc": "自动化 QC 报告、Jupyter/Quarto/RMarkdown 报告、图片导出",
        "match": [
            "bio-reporting-",
        ],
    },
    # ── Bio research tools ──
    "bio_research_tools": {
        "label": "gptomics 研究工具",
        "desc": "生物标志物签名工作室",
        "match": [
            "bio-research-tools-",
        ],
    },
    # ── Remaining specific matches ──
    "misc_specific": {
        "label": "补充专项技能",
        "desc": "GWAS-PRS、甲基化 GPT、系统发育、USPTO 专利",
        "match": [
            "gwas-prs", "epigenomics-methylgpt-agent",
            "phylogenetics", "uspto-database",
        ],
    },
    # ── BioOS agents ──
    "bioos_agents": {
        "label": "BioOS 扩展智能体",
        "desc": "肿瘤学、血液学、免疫治疗、单细胞、药物设计、临床 AI、研究基础设施",
        "match": [
            "bioos-", "autonomous-oncology", "tumor-", "cancer-agent",
            "hematology-", "immunology-agent", "cell-therapy-",
        ],
    },
    # ── ClawBio pipelines ──
    "clawbio": {
        "label": "ClawBio 编排管道",
        "desc": "scRNA 编排、GWAS 管道、祖先分析、药物基因组学、结构生物学文献综合",
        "match": [
            "clawbio-", "claw-bio", "orchestrat",
        ],
    },
    # ── Data Science & Visualization ──
    "data_science": {
        "label": "数据科学与可视化",
        "desc": "统计分析、数据处理、科学可视化、公共卫生、时序分析",
        "match": [
            "ai-analyzer", "bayesian-", "data-", "matplotlib",
            "plotly", "seaborn", "visualization", "epidemiology",
            "r-stat", "scipy", "numpy", "pandas",
        ],
    },
    # ── Simulation & Ontology ──
    "simulation_ontology": {
        "label": "计算模拟与本体论",
        "desc": "本体验证、数值求解器、网格生成、材料模拟",
        "match": [
            "ontology", "simulation", "mesh-", "solver",
            "fenics", "openfoam", "materials-",
        ],
    },
    # ── Lab Automation ──
    "lab_automation": {
        "label": "实验室自动化",
        "desc": "实验室设备集成、自动化工作流、LIMS",
        "match": [
            "benchling", "lab-", "lims", "opentrons",
        ],
    },
    # ── Dev Workflow ──
    "dev_workflow": {
        "label": "开发工作流技能",
        "desc": "代码审查、CI/CD、项目管理、文档工具、调试、Git",
        "match": [
            "obra-", "dev-", "git-", "docker", "ci-cd",
            "receiving-code-review", "requesting-code-review",
            "finishing-a-development-branch", "subagent-driven-development",
            "systematic-debugging", "test-driven-development",
            "using-git-worktrees", "using-superpowers",
            "verification-before-completion", "dispatching-parallel-agents",
            "executing-plans", "writing-plans", "writing-skills",
            "slurm-job-script-generator", "performance-profiling",
            "search-strategy", "goal-analyzer",
        ],
    },
    # ── Oncology & Cancer Agents ──
    "oncology_agents": {
        "label": "肿瘤学与癌症智能体",
        "desc": "癌症代谢、液体活检、MRD 检测、HRD 分析、CNV、克隆造血、肿瘤免疫微环境",
        "match": [
            "cancer-metabolism-agent", "bone-marrow-ai-agent", "cnv-caller-agent",
            "ctdna-dynamics-mrd-agent", "hrd-analysis-agent",
            "liquid-biopsy-analytics-agent", "mrd-edge-detection-agent",
            "myeloma-mrd-agent", "mpn-", "pan-cancer-",
            "precision-oncology-agent", "tme-immune-profiling-agent",
            "pdx-model-analysis-agent", "chromosomal-instability-agent",
            "chip-clonal-hematopoiesis-agent", "coagulation-thrombosis-agent",
            "hemoglobinopathy-analysis-agent", "organoid-drug-response-agent",
        ],
    },
    # ── Clinical NLP / EHR ──
    "clinical_nlp_ehr": {
        "label": "临床 NLP 与电子病历",
        "desc": "临床文本提取、病历摘要、诊断推理、EHR/FHIR 集成、护理协调",
        "match": [
            "clinical-nlp-extractor", "clinical-note-summarization",
            "clinical-diagnostic-reasoning", "chatehr-clinician-assistant",
            "ehr-fhir-integration", "care-coordination", "claims-appeals",
            "prior-auth-coworker", "digital-twin-clinical-agent",
            "emergency-card", "treatment-plans", "trial-eligibility-agent",
            "trialgpt-matching", "fhir-development",
        ],
    },
    # ── Drug Discovery Agents (expanded) ──
    "drug_discovery_agents": {
        "label": "药物发现智能体",
        "desc": "AI 驱动药物发现、分子进化、分子胶、PROTAC、冷冻电镜药物设计",
        "match": [
            "chematagent-drug-discovery", "chemcrow-drug-discovery",
            "medea-therapeutic-discovery", "molecule-evolution-agent",
            "molecular-glue-discovery-agent", "protac-design-agent",
            "tpd-ternary-complex-agent", "cryoem-ai-drug-design-agent",
            "drug-interaction-checker", "drug-photo",
            "modern-drug-rehab-computer",
        ],
    },
    # ── Immune & Cell Therapy (expanded) ──
    "immune_cell_therapy": {
        "label": "免疫学与细胞治疗",
        "desc": "免疫检查点、NK 细胞、T 细胞耗竭、TCR/pMHC、细胞因子风暴、CAR-T、衰老",
        "match": [
            "immune-checkpoint-combination-agent", "nk-cell-therapy-agent",
            "tcell-exhaustion-analysis-agent", "tcr-pmhc-prediction-agent",
            "tcr-repertoire-analysis-agent", "cytokine-storm-analysis-agent",
            "cart-design-optimizer-agent", "cellular-senescence-agent",
            "armored-cart-design-agent",
        ],
    },
    # ── Genomic/Genetic Agents ──
    "genomic_agents": {
        "label": "基因组学智能体",
        "desc": "基因面板设计、基因组比较、gnomAD、VCF 注释、ACMG 解读、PRS、长读长测序",
        "match": [
            "gene-panel-design-agent", "genome-compare", "gnomad-database",
            "cbioportal-database", "gwas-lookup", "varcadd-pathogenicity",
            "variant-interpretation-acmg", "vcf-annotator",
            "multi-ancestry-prs-agent", "prs-net-deep-learning-agent",
            "popeve-variant-predictor-agent", "long-read-sequencing-agent",
            "ngs-analysis", "seq-wrangler",
        ],
    },
    # ── Additional Databases ──
    "additional_databases": {
        "label": "补充科学数据库",
        "desc": "InterPro、JASPAR、GTEx、Monarch、DepMap、Imaging Data Commons",
        "match": [
            "interpro-database", "jaspar-database", "gtex-database",
            "monarch-database", "depmap", "imaging-data-commons",
            "tiledbvcf", "datacommons-client",
        ],
    },
    # ── Medical Imaging & Pathology ──
    "medical_imaging": {
        "label": "医学影像与病理",
        "desc": "DICOM、数字病理、放射组学、多模态影像融合、放射报告",
        "match": [
            "pydicom", "pathml", "multimodal-medical-imaging",
            "radgpt-radiology-reporter", "computational-pathology-agent",
            "histolab", "radiomics-pathomics-fusion-agent",
            "multimodal-radpath-fusion-agent",
        ],
    },
    # ── Pharmacogenomics ──
    "pharmacogenomics": {
        "label": "药物基因组学",
        "desc": "基因-药物交互、CPIC 指南、基因型导向用药",
        "match": [
            "pharmacogenomics-agent", "pharmgx-reporter", "clinpgx",
        ],
    },
    # ── Scientific Writing & Research ──
    "scientific_writing": {
        "label": "科学写作与研究",
        "desc": "论文撰写、文献综合、同行评审、科研基金、海报、幻灯片",
        "match": [
            "scientific-writing", "scientific-manuscript", "scientific-brainstorming",
            "scientific-critical-thinking", "scientific-problem-selection",
            "scientific-schematics", "scientific-slides", "paper-2-web",
            "latex-posters", "peer-review", "research-grants",
            "research-literature", "research-lookup", "lit-synthesizer",
            "leads-literature-mining", "knowledge-synthesis",
            "hypothesis-generation", "citation-management",
            "markdown-mermaid-writing", "brainstorming", "infographics",
            "open-notebook", "repro-enforcer",
        ],
    },
    # ── Data Science & ML (expanded) ──
    "ml_tools": {
        "label": "机器学习与数据工具",
        "desc": "scikit-learn、PyTorch Lightning、SHAP、statsmodels、Polars、Dask、UMAP",
        "match": [
            "dask", "polars", "scikit-learn", "shap", "statsmodels", "vaex",
            "umap-learn", "pymc", "pymoo", "pytorch-lightning", "networkx",
            "transformers", "torch-geometric", "timesfm-forecasting",
            "simpy", "exploratory-data-analysis", "profile-report",
            "statistical-analysis", "pyhealth", "markitdown",
        ],
    },
    # ── Lab & Platform Integration (expanded) ──
    "lab_platform": {
        "label": "实验室与平台集成",
        "desc": "LabArchive、Labstep、Ginkgo、OMERO、protocols.io、机器人",
        "match": [
            "labarchive-integration", "labstep", "ginkgo-cloud-lab",
            "protocolsio-integration", "omero-integration", "pylabrobot",
            "instrument-data-to-allotrope", "galaxy-bridge",
            "virtual-lab-agent",
        ],
    },
    # ── Mental Health ──
    "mental_health": {
        "label": "心理健康与危机干预",
        "desc": "心理分析、危机检测、悲伤陪伴、康复社区",
        "match": [
            "grief-companion", "jungian-psychologist", "psychologist-analyst",
            "recovery-community-moderator", "crisis-detection-intervention-ai",
            "crisis-response-protocol", "hrv-alexithymia-expert",
        ],
    },
    # ── Health Analyzers (expanded) ──
    "health_analyzers": {
        "label": "健康分析器",
        "desc": "家庭健康、职业健康、旅行健康、可穿戴设备、减重、康复",
        "match": [
            "family-health-analyzer", "occupational-health-analyzer",
            "travel-health-analyzer", "wearable-analysis-agent",
            "weightloss-analyzer", "wellally-tech", "rehabilitation-analyzer",
            "speech-pathology-ai",
        ],
    },
    # ── Metagenomics & Microbiome ──
    "metagenomics": {
        "label": "宏基因组学与微生物组",
        "desc": "宏基因组分析、微生物组、16S/ITS",
        "match": [
            "claw-metagenomics", "lobster-bioinformatics",
        ],
    },
    # ── Single-cell Agents (expanded to catch more) ──
    "singlecell_agents": {
        "label": "单细胞分析智能体",
        "desc": "CellAgent、scFoundation、RNA 速度、cfRNA、通用注释器",
        "match": [
            "cellagent-annotation", "bioinformatics-singlecell",
            "cellfree-rna-agent", "rna-velocity-agent",
            "scfoundation-model-agent", "scrna-qc", "scvelo",
            "universal-single-cell-annotator", "nicheformer-spatial-agent",
            "deep-visual-proteomics-agent", "exosome-ev-analysis-agent",
        ],
    },
    # ── Molecular Dynamics / Structural ──
    "molecular_dynamics": {
        "label": "分子动力学与结构预测",
        "desc": "分子动力学模拟、蛋白结构预测、冷冻电镜",
        "match": [
            "molecular-dynamics", "protein-structure-prediction",
            "struct-predictor", "time-resolved-cryoem-agent",
        ],
    },
    # ── Bioinfo Platforms / Agents ──
    "bioinfo_platforms": {
        "label": "生信平台与通用智能体",
        "desc": "BioKernel、BioMaster、BioMNI、CompBioAgent、MCPMed、KRAGEN",
        "match": [
            "biokernel", "biomaster-workflows", "biomcp-server",
            "biomni", "biomni-general-agent", "biomni-research-agent",
            "compbioagent-explorer", "mcpmed-bioinformatics-server",
            "kragen-knowledge-graph", "biomedical-data-analysis",
        ],
    },
    # ── CRISPR Tools ──
    "crispr_tools": {
        "label": "CRISPR 工具",
        "desc": "sgRNA 设计、脱靶预测",
        "match": [
            "crispr-guide-design", "crispr-offtarget-predictor",
        ],
    },
    # ── Compliance & Regulatory (expanded) ──
    "compliance_regulatory": {
        "label": "合规与法规",
        "desc": "HIPAA、医疗器械法规、数据合规",
        "match": [
            "hipaa-compliance", "equity-scorer",
        ],
    },
    # ── Chemistry / Chemical tools ──
    "chemistry_agents": {
        "label": "化学工具与智能体",
        "desc": "化学性质查询、化学智能体",
        "match": [
            "chemical-property-lookup", "chemist-analyst", "chemistry-agent",
            "glycoengineering",
        ],
    },
    # ── Neuroscience ──
    "neuroscience": {
        "label": "神经科学工具",
        "desc": "NeuroKit2、Neuropixels 分析",
        "match": [
            "neurokit2", "neuropixels-analysis",
        ],
    },
    # ── Misc Computational ──
    "misc_computational": {
        "label": "数值计算与杂项",
        "desc": "数值积分、收敛研究、参数优化、时间步进、Zarr",
        "match": [
            "numerical-integration", "numerical-stability",
            "convergence-study", "parameter-optimization",
            "time-stepping", "post-processing", "zarr-python",
            "differentiation-schemes",
        ],
    },
    # ── Search & Knowledge ──
    "search_knowledge": {
        "label": "搜索与知识工具",
        "desc": "Perplexity 搜索、语义相似度、ClawBio 工具",
        "match": [
            "perplexity-search", "claw-semantic-sim", "claw-ancestry-pca",
        ],
    },
    # ── Analyst Personas ──
    "analyst_personas": {
        "label": "分析师人格",
        "desc": "生物学家/流行病学家/生物信息学家分析师角色",
        "match": [
            "biologist-analyst", "epidemiologist-analyst",
        ],
    },
    # ── Misc Agents (catch remaining) ──
    "misc_agents": {
        "label": "其他专业智能体",
        "desc": "MAGE 抗体、UKB 导航、SIMO 多组学、HypoGenic 等",
        "match": [
            "mage-antibody-generator", "ukb-navigator",
            "simo-multiomics-integration-agent", "hypogenic",
            "pyzotero", "aeon",
        ],
    },
}

# ── Fallback group for unmatched skills ──
FALLBACK_GROUP = "other_medical"
FALLBACK_META = {
    "label": "其他医疗与科研技能",
    "desc": "未归入主要类别的专业技能",
}


def parse_skill_md(filepath):
    """Parse a SKILL.md file → dict with name, description, content, code_blocks."""
    text = pathlib.Path(filepath).read_text(encoding="utf-8", errors="replace")

    front_matter = {}
    body = text
    fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if fm_match:
        try:
            front_matter = yaml.safe_load(fm_match.group(1)) or {}
        except Exception:
            pass
        body = text[fm_match.end():]

    code_blocks = re.findall(r"```[\w]*\n(.*?)```", body, re.DOTALL)

    name = front_matter.get("name", "")
    description = front_matter.get("description", "")

    sections = {}
    current_section = "intro"
    sections[current_section] = []
    for line in body.split("\n"):
        hm = re.match(r"^#{1,3}\s+(.*)", line)
        if hm:
            current_section = hm.group(1).strip().lower()
            sections[current_section] = []
        else:
            sections.setdefault(current_section, []).append(line)

    for k in sections:
        sections[k] = "\n".join(sections[k]).strip()

    return {
        "name": name,
        "description": description,
        "front_matter": front_matter,
        "body_length": len(body),
        "code_blocks": code_blocks,
        "sections": sections,
    }


def classify_skill(skill_dir_name, parsed):
    """Return the merge group key for a skill."""
    name_lower = skill_dir_name.lower()
    desc_lower = (parsed.get("description") or "").lower()

    for group_key, group in MERGE_RULES.items():
        for pattern in group["match"]:
            if pattern.endswith("-"):
                if name_lower.startswith(pattern):
                    return group_key
            else:
                if name_lower == pattern or name_lower.startswith(pattern + "-"):
                    return group_key
                if pattern in name_lower:
                    return group_key

    return FALLBACK_GROUP


def compress_skill_for_sop(parsed, dir_name):
    """Compress a single skill into a compact SOP entry (≤15 lines)."""
    lines = []
    name = parsed["name"] or dir_name
    desc = parsed["description"] or ""
    if len(desc) > 200:
        desc = desc[:197] + "..."
    lines.append(f"### {name}")
    lines.append(f"**用途**: {desc}")

    when_to_use = parsed["sections"].get("when to use", "")
    if when_to_use:
        items = re.findall(r"[-*]\s+(.*)", when_to_use)
        if items:
            lines.append("**触发条件**: " + "; ".join(items[:4]))

    code = parsed["code_blocks"]
    if code:
        shortest = min(code, key=len)
        if len(shortest) > 500:
            shortest = shortest[:500] + "\n# ... (truncated)"
        lines.append("```")
        lines.append(shortest.strip())
        lines.append("```")

    best = parsed["sections"].get("best practices", "") or parsed["sections"].get("guidelines", "")
    if best:
        rules = re.findall(r"[-*]\s+(.*)", best)
        if rules:
            lines.append("**注意**: " + "; ".join(rules[:3]))

    limits = parsed["sections"].get("limitations", "") or parsed["sections"].get("important", "")
    if limits:
        items = re.findall(r"[-*]\s+(.*)", limits)
        if items:
            lines.append("**限制**: " + "; ".join(items[:2]))

    return "\n".join(lines)


def build_schema_entry(parsed, dir_name):
    """Build a minimal tool schema dict for one skill."""
    name = (parsed["name"] or dir_name).replace("-", "_").replace(" ", "_").lower()
    desc = parsed["description"] or ""
    if len(desc) > 300:
        desc = desc[:300]

    params = {"query": {"type": "string", "description": "查询/输入内容"}}

    code = "\n".join(parsed["code_blocks"])
    url_match = re.search(r'(https?://[^\s"\']+)', code)
    if url_match:
        params["url"] = {"type": "string", "description": f"API endpoint (e.g. {url_match.group(1)[:80]})"}

    return {
        "name": name,
        "description": desc,
        "parameters": {
            "type": "object",
            "properties": params,
            "required": ["query"],
        },
    }


def main():
    skills_root = pathlib.Path(OPENCLAW_DIR)
    seda = pathlib.Path(SEDA_DIR)

    all_skills = {}
    groups = defaultdict(list)

    skill_dirs = sorted([d for d in skills_root.iterdir() if d.is_dir()])
    print(f"[1/5] Scanning {len(skill_dirs)} skill directories ...")

    for sd in skill_dirs:
        skill_file = sd / "SKILL.md"
        if not skill_file.exists():
            sub_skills = list(sd.rglob("SKILL.md"))
            if sub_skills:
                skill_file = sub_skills[0]
            else:
                continue

        parsed = parse_skill_md(skill_file)
        dir_name = sd.name
        group = classify_skill(dir_name, parsed)
        all_skills[dir_name] = {"parsed": parsed, "group": group}
        groups[group].append(dir_name)

    print(f"[2/5] Classified {len(all_skills)} skills into {len(groups)} groups")
    for g, members in sorted(groups.items(), key=lambda x: -len(x[1])):
        print(f"  {g}: {len(members)} skills")

    # ── Generate L1 Index ──
    print("[3/5] Generating L1 index ...")
    l1_lines = ["# OpenClaw Skills → SEDA L1 索引", ""]
    l1_lines.append(f"> 共 {len(all_skills)} 个技能，合并为 {len(groups)} 组。自动生成，勿手动编辑。")
    l1_lines.append("")
    l1_lines.append("| 组 | 标签 | 技能数 | 关键词 | L3 SOP |")
    l1_lines.append("|---|---|---|---|---|")

    for group_key in sorted(groups.keys()):
        members = groups[group_key]
        meta = MERGE_RULES.get(group_key, FALLBACK_META)
        keywords = set()
        for m in members:
            p = all_skills[m]["parsed"]
            name_words = re.split(r"[-_ ]", m)
            keywords.update(w.lower() for w in name_words if len(w) > 2)
            desc_words = re.split(r"[\s,;]+", (p.get("description") or ""))
            keywords.update(w.lower() for w in desc_words if len(w) > 3 and w.isalpha())
        kw_str = ", ".join(sorted(keywords)[:15])
        sop_file = f"openclaw_{group_key}_sop.md"
        l1_lines.append(f"| {group_key} | {meta['label']} | {len(members)} | {kw_str} | `L3_sops/{sop_file}` |")

    l1_path = seda / "memory" / "L1_openclaw_skills_index.md"
    l1_path.write_text("\n".join(l1_lines), encoding="utf-8")
    print(f"  → {l1_path}")

    # ── Generate L3 SOPs ──
    print("[4/5] Generating L3 SOP files ...")
    sops_dir = seda / "memory" / "L3_sops"
    sops_dir.mkdir(exist_ok=True)
    total_sop = 0

    for group_key in sorted(groups.keys()):
        members = groups[group_key]
        meta = MERGE_RULES.get(group_key, FALLBACK_META)
        sop_lines = [
            f"# {meta['label']} SOP",
            f"> {meta['desc']}",
            f"> 包含 {len(members)} 个 OpenClaw skill 的压缩迁移。",
            "",
            "---",
            "",
        ]
        for m in sorted(members):
            p = all_skills[m]["parsed"]
            entry = compress_skill_for_sop(p, m)
            sop_lines.append(entry)
            sop_lines.append("")

        sop_path = sops_dir / f"openclaw_{group_key}_sop.md"
        sop_path.write_text("\n".join(sop_lines), encoding="utf-8")
        total_sop += 1

    print(f"  → Generated {total_sop} SOP files in {sops_dir}")

    # ── Generate Tool Schemas ──
    print("[5/5] Generating tool schemas ...")
    schema_groups = {}
    seen_names = set()

    for group_key in sorted(groups.keys()):
        members = groups[group_key]
        meta = MERGE_RULES.get(group_key, FALLBACK_META)
        group_schemas = []

        for m in sorted(members):
            p = all_skills[m]["parsed"]
            entry = build_schema_entry(p, m)
            base_name = entry["name"]
            if base_name in seen_names:
                entry["name"] = f"{group_key}_{base_name}"
            seen_names.add(entry["name"])
            group_schemas.append(entry)

        schema_groups[group_key] = {
            "group_label": meta["label"],
            "group_description": meta["desc"],
            "skill_count": len(members),
            "tools": group_schemas,
        }

    schema_path = seda / "assets" / "openclaw_tools_schema.json"
    schema_path.write_text(
        json.dumps(schema_groups, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"  → {schema_path}")

    # ── Summary ──
    print("\n" + "=" * 60)
    print(f"转换完成!")
    print(f"  技能总数: {len(all_skills)}")
    print(f"  合并组数: {len(groups)}")
    print(f"  L1 索引: {l1_path}")
    print(f"  L3 SOP:  {sops_dir}/openclaw_*.md ({total_sop} files)")
    print(f"  Schema:  {schema_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
