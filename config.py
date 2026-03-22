"""
Self-Evolving MedicalClaw - 配置文件
支持 API 调用和本地模型两种模式
"""
import os

# ============ LLM 后端配置 ============
# 模式: "api" 或 "local"
LLM_MODE = os.environ.get("SEDA_LLM_MODE", "api")

# --- API 模式配置 ---
# 在 mykey.py 中配置 API key（兼容 pc-agent-loop 格式）
# 支持 Claude / OpenAI-compatible / Xai / Sider 等多后端

# --- 本地模型配置 ---
LOCAL_MODEL_CONFIG = {
    "model_path": os.environ.get("SEDA_MODEL_PATH", ""),
    "api_base": os.environ.get("SEDA_LOCAL_API_BASE", "http://localhost:8000/v1"),
    "model_name": os.environ.get("SEDA_LOCAL_MODEL_NAME", "local-model"),
    "max_tokens": 4096,
    "temperature": 0.3,
}

# ============ 感知层配置 ============
# Base LLM 用于将原始数据转化为患者摘要
PERCEPTION_LLM_CONFIG = {
    "mode": os.environ.get("SEDA_PERCEPTION_MODE", "api"),
    "api_base": os.environ.get("SEDA_PERCEPTION_API_BASE", "http://localhost:8000/v1"),
    "model_name": os.environ.get("SEDA_PERCEPTION_MODEL", ""),
    "api_key": os.environ.get("SEDA_PERCEPTION_API_KEY", ""),
}

# ============ UKB 数据路径 ============
UKB_DATA_CONFIG = {
    "phenotype_file": os.environ.get("UKB_PHENOTYPE_FILE", ""),
    "genotype_dir": os.environ.get("UKB_GENOTYPE_DIR", ""),
    "proteomics_file": os.environ.get("UKB_PROTEOMICS_FILE", ""),
    "imaging_dir": os.environ.get("UKB_IMAGING_DIR", ""),
    "prs_weights_dir": os.environ.get("UKB_PRS_WEIGHTS_DIR", ""),
    "annotation_db": os.environ.get("UKB_ANNOTATION_DB", ""),
}

# ============ Agent 配置 ============
AGENT_CONFIG = {
    "max_turns": 40,
    "distill_threshold": 20,
    "max_tool_calls_per_case": 10,
    "enable_autonomous_exploration": False,
}

# ============ 记忆配置 ============
MEMORY_CONFIG = {
    "l1_max_lines": 80,
    "l4_episodes_file": "memory/L4_episodes/case_episodes.jsonl",
    "l4_strategy_file": "memory/L4_episodes/disease_strategy.json",
    "distill_log_file": "memory/L4_episodes/distill_log.txt",
    "auto_extract_min_turns": 4,
    "user_data_dir": "memory/user_data",
    "lifestyle_log_retention_days": 90,
    "conversation_log_max_entries": 500,
    "evidence_citation_level": "standard",   # strict / standard / relaxed
    "audit_trail_enabled": True,
}

# ============ Wearable Data Config ============
WEARABLE_CONFIG = {
    "db_path": os.environ.get("SEDA_WEARABLE_DB_PATH", "temp/wearable/wearable_data.db"),
    "upload_dir": os.environ.get("SEDA_WEARABLE_UPLOAD_DIR", "temp/wearable_uploads"),
    "supported_sources": ["xiaomi_export_dir", "huawei_export_dir", "gpx_file", "huawei_api", "xiaomi_api"],
    "default_trend_period": "30d",
}
