"""
UKBAgentHandler - Self-Evolving MedicalClaw 的核心 Handler
继承 GenericAgentHandler，新增 UKB 诊断专用工具
"""
import os, sys, json, time, re
from datetime import datetime
from agent_loop import BaseHandler, StepOutcome, try_call_generator
from ga import (GenericAgentHandler, smart_format, file_read, file_patch,
                log_memory_access, code_run, ask_user, format_error,
                driver as tmwd_driver, _ensure_driver_ready as tmwd_ensure,
                web_scan as tmwd_web_scan, web_execute_js as tmwd_web_execute_js,
                cdp_execute, ensure_cdp_config, is_cdp_available)

# ============ 工具后端导入 ============
from tools.clinical_tools import ClinicalDataLoader
from tools.genomic_tools import GenomicAnalyzer
from tools.proteomic_tools import ProteomicAnalyzer
from tools.imaging_tools import ImagingAnalyzer
from tools.integration_tools import MultiOmicsIntegrator
from tools.interpretation import GeneticInterpreter, ProteomicInterpreter, WearableInterpreter
from evolution.episode_writer import EpisodeWriter
from evolution.strategy_distiller import StrategyDistiller
from tools.bioinfo_tools import blast_search, david_enrichment, interpro_scan, run_bioinfo_cli
from tools.health_data_store import HealthDataStore
from tools.wearable_tools import WearableDataStore
from tools.wearable_importer import WearableDataImporter


_DIAGNOSIS_KEYWORDS = [
    '患者', '诊断', '基因', '变异', 'PRS', '蛋白', '影像', '病理', '风险评估',
    'UKB', 'eid', 'BRCA', 'APOE', 'load_patient', 'submit_diagnosis',
    '癌', '瘤', '综合征', '遗传', '突变', '致病', 'ClinVar',
    '病历', '质控', 'ICD', '编码', '编目', '病案首页', '用药审查',
    '临床路径', '路径偏差', '医保预审', '合规审查', '审阅材料', '证据分级',
    '影像', 'CT', 'MRI', '超声', 'X光', 'PET', '内镜', '结节', '磁共振',
]
_PROFESSIONAL_KEYWORDS = [
    'BLAST', 'DAVID', 'InterPro', 'eQTL', '通路', 'pathway', '组学',
    'pipeline', 'bioinformatics', '基因组', '转录组', '蛋白质组',
    'openclaw', 'CRISPR', '单细胞', 'spatial',
]


def _query_needs_diagnosis(query):
    """检查用户查询是否涉及诊断/医学分析场景"""
    q = query.lower()
    return any(kw.lower() in q for kw in _DIAGNOSIS_KEYWORDS)


def _query_needs_professional(query):
    """检查用户查询是否涉及专业生信/OpenClaw工具"""
    q = query.lower()
    return any(kw.lower() in q for kw in _PROFESSIONAL_KEYWORDS)


def _load_l1_sections(path, sections=None):
    """按 section 加载 L1 索引的指定区域，sections=None 时加载全部"""
    if not os.path.exists(path):
        return ""
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    if sections is None:
        return content
    result_lines = []
    current_section = None
    for line in content.split('\n'):
        if line.strip().startswith('## ['):
            sec_name = line.strip().lstrip('#').strip().strip('[]')
            current_section = sec_name
        if current_section and any(s.upper() in current_section.upper() for s in sections):
            result_lines.append(line)
        elif current_section is None:
            result_lines.append(line)
    return '\n'.join(result_lines)


def get_global_memory(user_query=""):
    """按需加载全局记忆：根据用户查询意图决定注入哪些记忆区域，节省 token。
    - 始终注入: 记忆结构说明、L1 的 RULES/HEALTH_MANAGEMENT/USER_PROFILE/INFRA/PHONE CONTROL/PHONE_APP_FLOWS
    - 诊断场景追加: L1 疾病映射(HIGH-FREQ/MID-FREQ/LOW-FREQ) + 策略建议
    - 专业场景追加: OpenClaw 技能索引
    """
    prompt = "\n"
    try:
        with open('assets/insight_fixed_structure.txt', 'r', encoding='utf-8') as f:
            structure = f.read()
        prompt += f"\n[Memory]\n"
        prompt += f'cwd = {os.path.abspath("./temp")} （用./引用）\n'
        prompt += structure + '\n'
    except FileNotFoundError:
        pass

    l1_path = 'memory/L1_disease_insight.txt'
    always_sections = ['RULES', 'HEALTH_MANAGEMENT', 'USER_PROFILE', 'USER_TAGS',
                       'INFRA', 'PHONE CONTROL', 'PHONE_APP_FLOWS']
    l1_core = _load_l1_sections(l1_path, always_sections)
    if l1_core.strip():
        prompt += f"../memory/L1_disease_insight.txt (核心区域):\n{l1_core}\n"

    if _query_needs_diagnosis(user_query):
        diagnosis_sections = ['HIGH-FREQ MAPPING', 'MID-FREQ MAPPING', 'LOW-FREQ KEYWORDS']
        l1_diag = _load_l1_sections(l1_path, diagnosis_sections)
        if l1_diag.strip():
            prompt += f"\n[诊断模式 — 疾病索引已加载]\n{l1_diag}\n"

        strategy_path = 'memory/L4_episodes/disease_strategy.json'
        if os.path.exists(strategy_path):
            try:
                with open(strategy_path, 'r', encoding='utf-8') as f:
                    strategy = json.load(f)
                if strategy:
                    prompt += "\n[Strategy Hints - 从历史病例蒸馏的工具使用策略]\n"
                    for disease, s in list(strategy.items())[:10]:
                        prompt += f"  {disease} ({s.get('total_cases',0)}例): "
                        for tool, u in s.get('tool_utility', {}).items():
                            prompt += f"{tool}={u.get('recommendation','?')}({u.get('usefulness_rate',0):.0%}) "
                        prompt += "\n"
            except (json.JSONDecodeError, KeyError):
                pass

    if _query_needs_professional(user_query):
        openclaw_index = 'memory/L1_openclaw_skills_index.md'
        if os.path.exists(openclaw_index):
            try:
                with open(openclaw_index, 'r', encoding='utf-8') as f:
                    oc_content = f.read()
                prompt += "\n[OpenClaw Skills Index - 869 个医疗 AI 技能索引，按组检索 L3 SOP]\n"
                prompt += oc_content + "\n"
            except Exception:
                pass

    return prompt


MAX_BROWSER_ELEMENTS = 20

_BROWSER_FALLBACK_MSG = (
    "篡改猴/TMWebDriver 未连接，browser_* 系列工具不可用。\n"
    "替代方案：使用 web_search 获取搜索结果，或 browse_and_learn(url=...) 直接读取页面内容。"
)


def _quick_browser_check():
    """2 秒内快速检查 TMWebDriver 是否可用，避免长时间等待卡死。
    返回 (ok: bool, error_msg: str|None)"""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        result = s.connect_ex(('127.0.0.1', 18766))
        s.close()
        if result != 0:
            return False, _BROWSER_FALLBACK_MSG
    except Exception:
        return False, _BROWSER_FALLBACK_MSG

    if tmwd_driver is None:
        return False, _BROWSER_FALLBACK_MSG

    try:
        sessions = tmwd_driver.get_all_sessions()
        if not sessions:
            return False, _BROWSER_FALLBACK_MSG + "\n（TMWebDriver 已连接但无活跃浏览器标签页）"
    except Exception:
        return False, _BROWSER_FALLBACK_MSG

    return True, None


def _tmwd_navigate_and_get_elements(url):
    """用 TMWebDriver（篡改猴）跳转并返回 title + 可点击元素列表，与 pc-agent-loop 一致"""
    ok, err = tmwd_ensure(timeout=10)
    if not ok:
        return {"status": "error", "msg": err}
    try:
        tmwd_driver.jump(url, timeout=10)
        time.sleep(1.5)
        js = """return JSON.stringify({
            title: document.title,
            url: location.href,
            elements: [].slice.call(document.querySelectorAll('a, button, [onclick]'))
                .map(function(e,i){ return {index: i, tag: e.tagName.toLowerCase(),
                    text: (e.innerText||e.textContent||'').slice(0,80), href: (e.href||'') }; })
        });"""
        out = tmwd_web_execute_js(js)
        if out.get("status") != "success":
            return {"status": "error", "msg": out.get("error", "JS 执行失败")}
        raw = out.get("js_return") or out.get("data")
        data = json.loads(raw) if isinstance(raw, str) else raw
        elements = data.get("elements", [])
        return {"status": "ok", "title": data.get("title", ""), "url": data.get("url", ""),
                "elements": elements, "element_count": len(elements)}
    except Exception as e:
        return {"status": "error", "msg": str(e)}


class UKBAgentHandler(GenericAgentHandler):
    """UKB 诊断 Agent Handler，继承 GenericAgentHandler 的基础工具，新增医学诊断工具"""

    def __init__(self, parent, last_history=None, cwd='./', autonomous=False):
        super().__init__(parent, last_history, cwd)
        self.autonomous = autonomous
        self.current_patient = None
        self.current_disease = None
        self.evidence_buffer = []
        self.tool_call_log = []
        self.confidence_before_tools = None

        self.clinical_loader = ClinicalDataLoader()
        self.genomic_analyzer = GenomicAnalyzer()
        self.proteomic_analyzer = ProteomicAnalyzer()
        self.imaging_analyzer = ImagingAnalyzer()
        self.integrator = MultiOmicsIntegrator()
        self.genetic_interp = GeneticInterpreter()
        self.proteomic_interp = ProteomicInterpreter()
        self.episode_writer = EpisodeWriter()
        self.strategy_distiller = StrategyDistiller()
        self.wearable_store = WearableDataStore()
        self.wearable_importer = WearableDataImporter(self.wearable_store)
        self.wearable_interp = WearableInterpreter()
        self.health_store = HealthDataStore()

    # ================================================================
    #  数据加载工具
    # ================================================================

    def do_load_patient(self, args, response):
        """加载患者基础临床数据，返回自然语言摘要"""
        eid = args.get("eid", "")
        disease_context = args.get("disease_context", "")
        if not eid:
            return StepOutcome({"status": "error", "msg": "缺少 eid 参数"},
                               next_prompt=self._get_anchor_prompt())

        self.current_patient = eid
        self.current_disease = disease_context
        self.evidence_buffer = []
        self.tool_call_log = []

        yield f"[Action] Loading patient {eid} clinical data...\n"
        try:
            clinical_data = self.clinical_loader.load(eid)
            summary = self.clinical_loader.format_summary(clinical_data)
        except Exception as e:
            summary = f"[模拟数据] 患者 {eid} 的临床数据加载失败({e})，请检查数据路径配置。"
            clinical_data = {"eid": eid, "status": "simulated"}

        self.evidence_buffer.append({"source": "clinical", "data": clinical_data})
        self.tool_call_log.append(("load_patient", 0.01))

        yield f"[Result]\n{summary}\n"
        return StepOutcome(
            data={"status": "success", "summary": summary},
            next_prompt=self._get_anchor_prompt() +
                f"\n[患者已加载] 基础临床数据如上。请分析是否需要进一步检索基因或蛋白数据。"
        )

    # ================================================================
    #  基因组查询工具
    # ================================================================

    def do_query_genetic_risk(self, args, response):
        """查询患者特定基因区域的变异信息或计算PRS"""
        if not self.current_patient:
            return StepOutcome({"status": "error", "msg": "请先 load_patient"},
                               next_prompt=self._get_anchor_prompt())

        mode = args.get("query_mode", "by_gene")
        targets = args.get("targets", [])

        yield f"[Action] Querying genetic data: mode={mode}, targets={targets}\n"
        try:
            if mode == "by_gene":
                result = self.genomic_analyzer.query_gene_variants(self.current_patient, targets)
                interpreted = self.genetic_interp.interpret_variants(result)
            elif mode == "by_pathway":
                result = self.genomic_analyzer.query_pathway(self.current_patient, targets)
                interpreted = self.genetic_interp.interpret_pathway(result)
            elif mode == "by_prs":
                disease = targets[0] if targets else self.current_disease
                result = self.genomic_analyzer.calculate_prs(self.current_patient, disease)
                interpreted = self.genetic_interp.interpret_prs(result)
            else:
                interpreted = f"未知查询模式: {mode}"
                result = {}
        except Exception as e:
            interpreted = f"[基因组查询异常] {e}"
            result = {"status": "error", "msg": str(e)}

        self.evidence_buffer.append({"source": "genetic", "mode": mode, "data": result})
        self.tool_call_log.append(("query_genetic_risk", 0.2))

        yield f"[Result]\n{interpreted}\n"
        return StepOutcome(
            data={"status": "success", "result": interpreted},
            next_prompt=self._get_anchor_prompt()
        )

    # ================================================================
    #  蛋白质组查询工具
    # ================================================================

    def do_query_proteomics(self, args, response):
        """查询患者特定蛋白质的表达水平"""
        if not self.current_patient:
            return StepOutcome({"status": "error", "msg": "请先 load_patient"},
                               next_prompt=self._get_anchor_prompt())

        proteins = args.get("proteins", [])
        return_format = args.get("return_format", "z_score")

        yield f"[Action] Querying proteomic data: {proteins}\n"
        try:
            result = self.proteomic_analyzer.query(self.current_patient, proteins, return_format)
            interpreted = self.proteomic_interp.interpret_panel(result)
        except Exception as e:
            interpreted = f"[蛋白质组查询异常] {e}"
            result = {"status": "error", "msg": str(e)}

        self.evidence_buffer.append({"source": "proteomic", "data": result})
        self.tool_call_log.append(("query_proteomics", 0.05))

        yield f"[Result]\n{interpreted}\n"
        return StepOutcome(
            data={"status": "success", "result": interpreted},
            next_prompt=self._get_anchor_prompt()
        )

    # ================================================================
    #  影像详情查询工具
    # ================================================================

    def do_query_imaging_detail(self, args, response):
        """查询患者影像数据的详细特征"""
        if not self.current_patient:
            return StepOutcome({"status": "error", "msg": "请先 load_patient"},
                               next_prompt=self._get_anchor_prompt())

        modality = args.get("modality", "")
        yield f"[Action] Querying imaging detail: {modality}\n"
        try:
            result = self.imaging_analyzer.query(self.current_patient, modality)
            interpreted = result.get("summary", str(result))
        except Exception as e:
            interpreted = f"[影像查询异常] {e}"
            result = {"status": "error", "msg": str(e)}

        self.evidence_buffer.append({"source": "imaging", "modality": modality, "data": result})
        self.tool_call_log.append(("query_imaging_detail", 0.1))

        yield f"[Result]\n{interpreted}\n"
        return StepOutcome(
            data={"status": "success", "result": interpreted},
            next_prompt=self._get_anchor_prompt()
        )

    # ================================================================
    #  多组学整合分析工具
    # ================================================================

    def do_gene_protein_integration(self, args, response):
        """对已检索的基因和蛋白数据进行整合分析"""
        gene_ev = [e for e in self.evidence_buffer if e["source"] == "genetic"]
        prot_ev = [e for e in self.evidence_buffer if e["source"] == "proteomic"]

        if not gene_ev or not prot_ev:
            return StepOutcome(
                {"status": "error", "msg": "需要先同时查询基因和蛋白数据才能做整合分析"},
                next_prompt=self._get_anchor_prompt()
            )

        yield f"[Action] Integrating gene-protein evidence...\n"
        try:
            result = self.integrator.integrate(gene_ev, prot_ev)
            interpreted = result.get("summary", str(result))
        except Exception as e:
            interpreted = f"[整合分析异常] {e}"
            result = {"status": "error"}

        self.tool_call_log.append(("gene_protein_integration", 0.5))
        yield f"[Result]\n{interpreted}\n"
        return StepOutcome(
            data={"status": "success", "result": interpreted},
            next_prompt=self._get_anchor_prompt()
        )

    # ================================================================
    #  情景记忆工具
    # ================================================================

    def do_import_wearable_data(self, args, response):
        eid = args.get("eid") or self.current_patient
        source_type = args.get("source_type", "xiaomi_export_dir")
        path = args.get("path", "")

        if not eid or not path:
            return StepOutcome({"status": "error", "msg": "Need eid and path"}, next_prompt=self._get_anchor_prompt())

        self.current_patient = eid
        yield f"[Action] Importing wearable data: {source_type} from {path}\n"
        result = self.wearable_importer.import_source(eid, source_type, path)
        interpreted = self.wearable_interp.summarize_import(result)
        if result.get("status") == "success":
            self.tool_call_log.append(("import_wearable_data", 0.03))
        yield f"[Result]\n{interpreted}\n"
        return StepOutcome(data=result, next_prompt=self._get_anchor_prompt())

    def do_query_wearable_trend(self, args, response):
        eid = args.get("eid") or self.current_patient
        period = args.get("period", "30d")
        if not eid:
            return StepOutcome({"status": "error", "msg": "Need eid or load_patient first"}, next_prompt=self._get_anchor_prompt())

        result = self.wearable_store.query_trend(eid, period)
        if result.get("status") == "success":
            self.evidence_buffer = [e for e in self.evidence_buffer if e.get("source") != "wearable_trend"]
            self.evidence_buffer.append({
                "source": "wearable_trend",
                "period": period,
                "aggregated": result.get("aggregated", {}),
                "baselines": result.get("baselines", {}),
                "quality": result.get("quality", {}),
                "raw": result,
            })
            self.tool_call_log.append(("query_wearable_trend", 0.05))
        interpreted = self.wearable_interp.summarize_status(result, focus="general")
        yield f"[Result]\n{interpreted}\n"
        return StepOutcome(data=result, next_prompt=self._get_anchor_prompt())

    def do_summarize_wearable_status(self, args, response):
        eid = args.get("eid") or self.current_patient
        period = args.get("period", "30d")
        focus = args.get("focus", "general")
        if not eid:
            return StepOutcome({"status": "error", "msg": "Need eid or load_patient first"}, next_prompt=self._get_anchor_prompt())

        result = self.wearable_store.query_trend(eid, period)
        interpreted = self.wearable_interp.summarize_status(result, focus=focus)
        if result.get("status") == "success":
            self.tool_call_log.append(("summarize_wearable_status", 0.08))
        yield f"[Result]\n{interpreted}\n"
        return StepOutcome(data={"status": result.get("status"), "summary": interpreted, "trend": result}, next_prompt=self._get_anchor_prompt())

    def do_detect_wearable_anomalies(self, args, response):
        eid = args.get("eid") or self.current_patient
        lookback_days = int(args.get("lookback_days", 30))
        sensitivity = args.get("sensitivity", "medium")
        if not eid:
            return StepOutcome({"status": "error", "msg": "Need eid or load_patient first"}, next_prompt=self._get_anchor_prompt())

        result = self.wearable_store.detect_anomalies(eid, lookback_days, sensitivity)
        interpreted = self.wearable_interp.summarize_anomalies(result.get("anomalies", []), lookback_days, sensitivity)
        if result.get("status") == "success":
            self.tool_call_log.append(("detect_wearable_anomalies", 0.1))
            self.evidence_buffer = [e for e in self.evidence_buffer if e.get("source") != "wearable_anomalies"]
            self.evidence_buffer.append({"source": "wearable_anomalies", "raw": result, "anomalies": result.get("anomalies", [])})
        yield f"[Result]\n{interpreted}\n"
        return StepOutcome(data=result, next_prompt=self._get_anchor_prompt())

    def do_integrate_clinical_wearable(self, args, response):
        eid = args.get("eid") or self.current_patient
        period = args.get("period", "30d")
        if not eid:
            return StepOutcome({"status": "error", "msg": "Need eid or load_patient first"}, next_prompt=self._get_anchor_prompt())

        clinical = None
        wearable = None
        for ev in self.evidence_buffer:
            if ev.get("source") == "clinical":
                clinical = ev.get("data")
            if ev.get("source") == "wearable_trend":
                wearable = ev.get("raw")
        if wearable is None:
            wearable = self.wearable_store.query_trend(eid, period)

        findings = self._analyze_clinical_wearable_correlation(clinical or {}, wearable)
        interpreted = self.wearable_interp.summarize_integration(findings, wearable)
        if wearable.get("status") == "success":
            self.tool_call_log.append(("integrate_clinical_wearable", 0.3))
        yield f"[Result]\n{interpreted}\n"
        return StepOutcome(data={"status": "success", "findings": findings, "summary": interpreted}, next_prompt=self._get_anchor_prompt())

    def _analyze_clinical_wearable_correlation(self, clinical, wearable):
        agg = wearable.get("aggregated", {}) if isinstance(wearable, dict) else {}
        findings = []
        vitals = clinical.get("vitals", {}) if isinstance(clinical, dict) else {}
        demo = clinical.get("demographics", {}) if isinstance(clinical, dict) else {}
        labs = clinical.get("labs", {}) if isinstance(clinical, dict) else {}

        systolic_bp = self._safe_number(vitals.get("systolic_bp") or vitals.get("sbp") or clinical.get("systolic_bp"))
        bmi = self._safe_number(demo.get("bmi") or clinical.get("bmi"))
        hba1c = self._safe_number(labs.get("hba1c") or clinical.get("hba1c"))

        resting_hr = self._safe_number(agg.get("night_resting_hr"))
        steps = self._safe_number(agg.get("avg_steps"))
        sleep_hours = self._safe_number(agg.get("avg_sleep_hours"))
        spo2 = self._safe_number(agg.get("avg_spo2"))

        if resting_hr is not None and systolic_bp is not None and resting_hr >= 80 and systolic_bp >= 140:
            findings.append("Elevated resting heart rate together with hypertension suggests higher cardiovascular strain.")
        if steps is not None and bmi is not None and steps < 5000 and bmi >= 28:
            findings.append("Low daily activity combined with elevated BMI supports lifestyle-driven metabolic risk.")
        if sleep_hours is not None and hba1c is not None and sleep_hours < 6 and hba1c >= 6.5:
            findings.append("Short sleep duration may be aggravating glycemic control burden.")
        if spo2 is not None and spo2 < 92:
            findings.append("Average SpO2 is low enough to justify cardiopulmonary or sleep-disordered breathing review.")
        if not findings and agg:
            findings.append("Wearable data provides baseline lifestyle context but does not yet trigger a strong rule-based interaction.")
        return findings

    def _safe_number(self, value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def do_recall_similar_cases(self, args, response):
        """从情景记忆中检索相似病例的处理经验（规则匹配，不用向量库）"""
        disease = args.get("disease", self.current_disease or "")
        key_features = args.get("key_features", [])

        yield f"[Action] Recalling similar cases for: {disease}, features={key_features}\n"
        episodes_path = os.path.join(os.path.dirname(__file__),
                                     'memory/L4_episodes/case_episodes.jsonl')
        cases = self._rule_based_case_retrieval(episodes_path, disease, key_features)

        if cases:
            formatted = self._format_case_memories(cases)
            yield f"[Found {len(cases)} similar cases]\n"
        else:
            formatted = "未找到相似病例经验。建议按 L1 索引推荐的标准流程进行。"

        return StepOutcome(
            data={"status": "success", "cases_count": len(cases)},
            next_prompt=self._get_anchor_prompt() + f"\n[情景记忆]\n{formatted}"
        )

    def _rule_based_case_retrieval(self, episodes_path, disease, key_features, max_results=5):
        if not os.path.exists(episodes_path):
            return []
        scored = []
        try:
            with open(episodes_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    ep = json.loads(line)
                    score = 0
                    if ep.get("disease", "") == disease:
                        score += 10
                    tag_overlap = set(ep.get("tags", [])) & set(key_features)
                    score += len(tag_overlap) * 2
                    if ep.get("outcome_correct") is not None:
                        score += 3
                    cc = ep.get("confidence_change", {})
                    conf_lift = abs(cc.get("after_tools", 0) - cc.get("before_tools", 0))
                    if conf_lift > 0.3:
                        score += 5
                    if score > 0:
                        scored.append((score, ep))
        except Exception:
            return []
        scored.sort(key=lambda x: -x[0])
        return [ep for _, ep in scored[:max_results]]

    def _format_case_memories(self, cases):
        lines = []
        for i, c in enumerate(cases, 1):
            tools_info = ", ".join(
                f"{t}({'有用' if c.get('tools_useful',{}).get(t) else '无增量'})"
                for t in c.get("tools_used", [])
            )
            cc = c.get("confidence_change", {})
            lines.append(
                f"Case#{i} [{c.get('disease','')}] {c.get('patient_profile','')}\n"
                f"  工具: {tools_info}\n"
                f"  置信度: {cc.get('before_tools','?')}→{cc.get('after_tools','?')}\n"
                f"  经验: {c.get('key_lesson','')}"
            )
        return "\n".join(lines)

    # ================================================================
    #  诊断提交工具
    # ================================================================

    def do_submit_diagnosis(self, args, response):
        """提交最终诊断结果，记录推理轨迹"""
        diagnosis = args.get("diagnosis", "")
        confidence = args.get("confidence", 0.5)
        evidence_summary = args.get("evidence_summary", "")
        tools_contributed = args.get("tools_contributed", [])

        yield f"[Action] Submitting diagnosis: {diagnosis} (confidence={confidence})\n"

        trajectory = {
            "patient": self.current_patient,
            "disease": self.current_disease,
            "diagnosis": diagnosis,
            "confidence": confidence,
            "evidence_summary": evidence_summary,
            "tools_used": [t for t, _ in self.tool_call_log],
            "tools_contributed": tools_contributed,
            "total_cost": sum(c for _, c in self.tool_call_log),
            "evidence_count": len(self.evidence_buffer),
            "timestamp": time.strftime('%Y-%m-%d %H:%M')
        }

        traj_dir = os.path.join(os.path.dirname(__file__), 'temp', 'trajectories')
        os.makedirs(traj_dir, exist_ok=True)
        traj_file = os.path.join(traj_dir, f"{self.current_patient}_{int(time.time())}.json")
        with open(traj_file, 'w', encoding='utf-8') as f:
            json.dump(trajectory, f, ensure_ascii=False, indent=2)

        yield f"[Trajectory saved] {traj_file}\n"
        return StepOutcome(data=trajectory, next_prompt=None)

    # ================================================================
    #  反思写入工具
    # ================================================================

    def do_write_case_reflection(self, args, response):
        """对当前病例进行反思，写入情景记忆(L4)"""
        tools_useful = args.get("tools_useful", {})
        key_lesson = args.get("key_lesson", "")
        confidence_before = args.get("confidence_before_tools", self.confidence_before_tools or 0.5)
        confidence_after = args.get("confidence_after_tools", 0.5)
        tags = args.get("tags", [])

        episode = {
            "episode_id": f"EP_{time.strftime('%Y%m%d')}_{int(time.time()) % 10000:04d}",
            "disease": self.current_disease or "",
            "patient_profile": args.get("patient_profile", ""),
            "tools_used": [t for t, _ in self.tool_call_log],
            "tools_useful": tools_useful,
            "confidence_change": {
                "before_tools": confidence_before,
                "after_tools": confidence_after
            },
            "key_lesson": key_lesson,
            "outcome_correct": None,
            "tags": tags,
            "timestamp": time.strftime('%Y-%m-%d %H:%M')
        }

        yield f"[Action] Writing case reflection to L4...\n"
        self.episode_writer.write(episode)
        yield f"[Saved] Episode {episode['episode_id']}\n"

        new_count = self.episode_writer.count_since_last_distill()
        hint = ""
        from config import AGENT_CONFIG
        threshold = AGENT_CONFIG.get("distill_threshold", 20)
        if new_count >= threshold:
            hint = f"\n[SYSTEM] 已积累 {new_count} 个新病例经验（阈值={threshold}），建议调用 distill_experience。"

        return StepOutcome(
            data={"status": "success", "episode_id": episode["episode_id"]},
            next_prompt=self._get_anchor_prompt() + hint
        )

    # ================================================================
    #  经验蒸馏工具
    # ================================================================

    def do_distill_experience(self, args, response):
        """从情景记忆中蒸馏出策略统计，更新 disease_strategy.json"""
        yield f"[Action] Distilling experience from case episodes...\n"
        try:
            result = self.strategy_distiller.distill()
            yield f"[Result] Distilled strategy for {len(result)} diseases\n"
            for d, s in result.items():
                yield f"  {d}: {s.get('total_cases',0)} cases, "
                for t, u in s.get('tool_utility', {}).items():
                    yield f"{t}={u.get('recommendation','?')} "
                yield "\n"
        except Exception as e:
            result = {"error": str(e)}
            yield f"[Error] Distillation failed: {e}\n"

        prompt = (
            self._get_anchor_prompt() +
            "\n[蒸馏完成] 请检查策略统计结果。如果发现了新的通用规则，"
            "请用 file_patch 更新 L1 的 RULES 部分。"
        )
        return StepOutcome(data=result, next_prompt=prompt)

    # ================================================================
    #  生信工具 (BLAST / DAVID / InterProScan / CLI)
    # ================================================================

    def do_blast_search(self, args, response):
        """BLAST 序列相似性搜索，调用 NCBI API。详见 L3 bioinformatics_tools_sop。"""
        query = args.get("query", "")
        program = args.get("program", "blastp")
        database = args.get("database", "swissprot")
        evalue = float(args.get("evalue", 1e-5))
        yield f"[Action] BLAST: program={program}, db={database}\n"
        try:
            out = blast_search(query=query, program=program, database=database, evalue=evalue)
        except Exception as e:
            out = {"status": "error", "msg": str(e)}
        if out.get("status") == "success":
            hits = out.get("hits", [])
            summary = f"共 {len(hits)} 个 hit。前几条: " + "; ".join(
                f"{h.get('id','')} {h.get('def','')}" for h in hits[:5]
            )
        else:
            summary = out.get("msg", str(out))
        yield f"[Result] {summary}\n"
        return StepOutcome(data=out, next_prompt=self._get_anchor_prompt())

    def do_david_enrichment(self, args, response):
        """DAVID 基因列表富集分析。未配置 API 时返回使用说明。详见 L3 bioinformatics_tools_sop。"""
        gene_ids = args.get("gene_ids", [])
        if isinstance(gene_ids, str):
            gene_ids = [g.strip() for g in gene_ids.replace(",", " ").split() if g.strip()]
        id_type = args.get("id_type", "ENTREZ_GENE_ID")
        species = args.get("species", "human")
        email = args.get("email", "")
        yield f"[Action] DAVID enrichment: {len(gene_ids)} genes\n"
        out = david_enrichment(gene_ids=gene_ids, id_type=id_type, species=species, email=email or None)
        summary = out.get("msg", str(out))
        yield f"[Result] {summary}\n"
        return StepOutcome(data=out, next_prompt=self._get_anchor_prompt())

    def do_interpro_scan(self, args, response):
        """InterProScan 蛋白结构域/功能注释，调用 EBI REST。详见 L3 bioinformatics_tools_sop。"""
        sequences = args.get("sequences", "")
        appl = args.get("appl", "")
        email = args.get("email", "agent@local")
        yield f"[Action] InterProScan submit...\n"
        try:
            out = interpro_scan(sequences=sequences, appl=appl or None, email=email)
        except Exception as e:
            out = {"status": "error", "msg": str(e)}
        summary = (out.get("result", "")[:500] if out.get("status") == "success" else out.get("msg", str(out)))
        yield f"[Result] {summary}\n"
        return StepOutcome(data=out, next_prompt=self._get_anchor_prompt())

    def do_run_bioinfo_cli(self, args, response):
        """运行生信 CLI：bwa/hisat2/star/prokka/spades 等。需本机已安装并配置 PATH。详见 L3 bioinformatics_tools_sop。"""
        tool = args.get("tool", "")
        input_path = args.get("input_path", "")
        input_path2 = args.get("input_path2", "")
        output_dir = args.get("output_dir", "")
        extra_args = args.get("extra_args", [])
        reference_index = args.get("reference_index", "")
        timeout = int(args.get("timeout", 3600))
        yield f"[Action] run_bioinfo_cli: tool={tool}\n"
        out = run_bioinfo_cli(
            tool=tool,
            input_path=input_path or None,
            input_path2=input_path2 or None,
            output_dir=output_dir or None,
            extra_args=extra_args,
            reference_index=reference_index or None,
            timeout=timeout,
        )
        summary = out.get("msg", "") + ("\n" + (out.get("stdout", "") or "")[:800] if out.get("stdout") else "")
        yield f"[Result] {summary}\n"
        return StepOutcome(data=out, next_prompt=self._get_anchor_prompt())

    # ================================================================
    #  联网搜索工具 (带自动 fallback)
    # ================================================================

    @staticmethod
    def _assess_result_quality(results):
        """评估搜索结果质量：返回 'good' / 'low' / 'empty'"""
        if not results:
            return 'empty'
        has_snippet = sum(1 for r in results if len(r.get('snippet', r.get('title', ''))) > 40)
        has_url = sum(1 for r in results if r.get('url', '').startswith('http'))
        if has_snippet >= 2 or (len(results) >= 3 and has_url >= 2):
            return 'good'
        return 'low'

    def do_web_search(self, args, response):
        """联网搜索，空结果或低质量结果时自动升级到浏览器深度搜索"""
        query = args.get("query", "")
        source = args.get("source", "pubmed")
        max_results = args.get("max_results", 5)

        if not query:
            return StepOutcome({"status": "error", "msg": "缺少 query 参数"},
                               next_prompt=self._get_anchor_prompt())

        yield f"[Action] Web search: source={source}, query={query}\n"

        # === 第一层：专业 API ===
        result = None
        try:
            result = self._execute_web_search(query, source, max_results)
        except Exception as e:
            yield f"[Warn] API search failed: {e}\n"
            result = {"source": source, "results": [], "error": str(e)}

        quality = self._assess_result_quality(result.get("results", []))

        # === 第二层：DuckDuckGo HTML fallback ===
        if quality == 'empty':
            yield f"[Fallback] API返回空，尝试 DuckDuckGo 搜索...\n"
            try:
                ddg_result = self._search_duckduckgo(query, max_results)
                if ddg_result.get("results"):
                    result = ddg_result
                    quality = self._assess_result_quality(ddg_result["results"])
                    yield f"[Fallback] DuckDuckGo 找到 {len(ddg_result['results'])} 条结果 (质量: {quality})\n"
            except Exception as e:
                yield f"[Fallback] DuckDuckGo 也失败: {e}\n"

        # === 第三层：接管浏览器搜索（空或低质量结果时，普通/自主模式均可） ===
        need_browser = quality in ('empty', 'low')
        if need_browser:
            reason = "结果为空" if quality == 'empty' else "结果质量偏低（摘要过短/缺少URL）"
            yield f"[Browser] {reason}，启动浏览器深度搜索...\n"
            try:
                browser_result = self._browser_search_fallback(query, max_results)
                if browser_result.get("results"):
                    br_quality = self._assess_result_quality(browser_result["results"])
                    if quality == 'empty' or br_quality == 'good':
                        result = browser_result
                        quality = br_quality
                    else:
                        result["results"].extend(browser_result["results"])
                        result["source"] = f"{result.get('source','')}_+_browser"
                    yield f"[Browser] 浏览器搜索找到 {len(browser_result['results'])} 条结果\n"
                else:
                    yield f"[Browser] 浏览器搜索也未找到结果\n"
            except Exception as e:
                yield f"[Browser] 浏览器不可用: {e}\n"

        formatted = self._format_search_results(result)
        yield formatted + "\n"

        fallback_info = ""
        if quality == 'empty':
            fallback_info = ("\n[提示] 所有搜索渠道均未找到结果。你可以：\n"
                             "1. 换关键词重试\n"
                             "2. 用 browse_and_learn 直接访问特定网站\n"
                             "3. 用 browser_search 或 browser_navigate 深度搜索/打开页面\n")
        elif quality == 'low':
            fallback_info = ("\n[提示] 搜索结果质量偏低，摘要信息不足。建议：\n"
                             "1. 用 browse_and_learn 或 browser_navigate 打开具体URL深度阅读原文\n"
                             "2. 用 browser_search 重新搜索权威来源\n")

        return StepOutcome(
            data=result,
            next_prompt=self._get_anchor_prompt() + f"\n[搜索结果 质量={quality}]\n{formatted}" + fallback_info
        )

    def _execute_web_search(self, query, source, max_results):
        import requests

        if source == "pubmed":
            return self._search_pubmed(query, max_results)
        elif source == "google":
            return self._search_duckduckgo(query, max_results)
        elif source == "gene":
            return self._search_gene_info(query)
        elif source == "protein":
            return self._search_protein_info(query)
        elif source == "clinvar":
            return self._search_clinvar(query)
        else:
            return self._search_pubmed(query, max_results)

    def _search_pubmed(self, query, max_results=5):
        import requests
        base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        r = requests.get(f"{base}/esearch.fcgi", params={
            "db": "pubmed", "term": query, "retmax": max_results,
            "retmode": "json", "sort": "relevance"
        }, timeout=15)
        data = r.json()
        ids = data.get("esearchresult", {}).get("idlist", [])
        if not ids:
            return {"source": "pubmed", "query": query, "results": []}

        r2 = requests.get(f"{base}/esummary.fcgi", params={
            "db": "pubmed", "id": ",".join(ids), "retmode": "json"
        }, timeout=15)
        summaries = r2.json().get("result", {})
        results = []
        for pid in ids:
            info = summaries.get(pid, {})
            if isinstance(info, dict) and "title" in info:
                authors = info.get("authors", [])
                first_author = authors[0].get("name", "") if authors else ""
                results.append({
                    "pmid": pid,
                    "title": info.get("title", ""),
                    "journal": info.get("source", ""),
                    "year": info.get("pubdate", "")[:4],
                    "first_author": first_author,
                })
        return {"source": "pubmed", "query": query, "count": len(results), "results": results}

    def _search_duckduckgo(self, query, max_results=5):
        """DuckDuckGo HTML 搜索 - 比直接爬 Google 更稳定"""
        import requests
        r = requests.get("https://html.duckduckgo.com/html/",
                         params={"q": query},
                         headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"},
                         timeout=15)
        results = []
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(r.text, 'html.parser')
            for item in soup.select('.result'):
                title_el = item.select_one('.result__a')
                snippet_el = item.select_one('.result__snippet')
                url_el = item.select_one('.result__url')
                if title_el:
                    results.append({
                        "title": title_el.get_text(strip=True),
                        "snippet": snippet_el.get_text(strip=True) if snippet_el else "",
                        "url": url_el.get_text(strip=True) if url_el else "",
                    })
                if len(results) >= max_results:
                    break
        except ImportError:
            import re as _re
            for m in _re.finditer(r'class="result__a"[^>]*>([^<]+)</a>', r.text):
                results.append({"title": m.group(1).strip(), "snippet": "", "url": ""})
                if len(results) >= max_results:
                    break
        return {"source": "duckduckgo", "query": query, "results": results}

    def _browser_search_fallback(self, query, max_results=5):
        """浏览器搜索回退：DuckDuckGo 优先，TMWebDriver 打开 Bing 兜底（与 pc-agent-loop 一致）"""
        try:
            ddg = self._search_duckduckgo(query, max_results)
            if ddg.get("results"):
                return {"source": "browser_duckduckgo", "query": query, "results": ddg["results"]}
        except Exception:
            pass

        try:
            from urllib.parse import quote
            ok, err = tmwd_ensure(timeout=8)
            if not ok:
                return {"source": "browser", "results": [], "error": err}
            search_url = "https://www.bing.com/search?q=" + quote(query)
            tmwd_driver.jump(search_url, timeout=12)
            time.sleep(2)
            scan = tmwd_web_scan(tabs_only=False)
            if scan.get("status") != "success" or not scan.get("content"):
                return {"source": "browser", "results": [], "error": "Bing 页面未返回内容"}
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(scan["content"], "html.parser")
            results = []
            for item in soup.select(".b_algo")[:max_results]:
                title_el = item.select_one("h2 a")
                snippet_el = item.select_one(".b_caption p")
                if title_el:
                    results.append({
                        "title": title_el.get_text(strip=True),
                        "url": title_el.get("href", ""),
                        "snippet": snippet_el.get_text(strip=True)[:200] if snippet_el else "",
                    })
            if results:
                return {"source": "browser_bing", "query": query, "results": results}
        except Exception as e:
            return {"source": "browser", "results": [], "error": f"搜索失败: {e}"}

        return {"source": "browser", "results": [], "error": "所有搜索渠道均无结果"}

    def _search_gene_info(self, gene_name):
        import requests
        r = requests.get(f"https://rest.ensembl.org/lookup/symbol/homo_sapiens/{gene_name}",
                         headers={"Content-Type": "application/json"}, timeout=15)
        if r.status_code == 200:
            data = r.json()
            info = {
                "gene": gene_name,
                "description": data.get("description", ""),
                "biotype": data.get("biotype", ""),
                "chromosome": data.get("seq_region_name", ""),
                "start": data.get("start"), "end": data.get("end"),
                "strand": data.get("strand"),
            }
            return {"source": "ensembl", "results": [info]}
        return {"source": "ensembl", "results": [], "error": f"HTTP {r.status_code}"}

    def _search_protein_info(self, protein_name):
        import requests
        r = requests.get(f"https://rest.uniprot.org/uniprotkb/search",
                         params={"query": f"{protein_name} AND organism_id:9606",
                                 "format": "json", "size": 3},
                         timeout=15)
        if r.status_code == 200:
            entries = r.json().get("results", [])
            results = []
            for e in entries:
                results.append({
                    "accession": e.get("primaryAccession", ""),
                    "name": e.get("proteinDescription", {}).get("recommendedName", {}).get("fullName", {}).get("value", ""),
                    "gene": ", ".join(g.get("geneName", {}).get("value", "") for g in e.get("genes", [])),
                    "function": (e.get("comments", [{}])[0].get("texts", [{}])[0].get("value", ""))[:300] if e.get("comments") else "",
                })
            return {"source": "uniprot", "query": protein_name, "results": results}
        return {"source": "uniprot", "results": [], "error": f"HTTP {r.status_code}"}

    def _search_clinvar(self, query):
        import requests
        base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        r = requests.get(f"{base}/esearch.fcgi", params={
            "db": "clinvar", "term": query, "retmax": 5, "retmode": "json"
        }, timeout=15)
        ids = r.json().get("esearchresult", {}).get("idlist", [])
        if not ids:
            return {"source": "clinvar", "query": query, "results": []}
        r2 = requests.get(f"{base}/esummary.fcgi", params={
            "db": "clinvar", "id": ",".join(ids), "retmode": "json"
        }, timeout=15)
        summaries = r2.json().get("result", {})
        results = []
        for cid in ids:
            info = summaries.get(cid, {})
            if isinstance(info, dict):
                results.append({
                    "clinvar_id": cid,
                    "title": info.get("title", ""),
                    "clinical_significance": info.get("clinical_significance", {}).get("description", ""),
                    "gene": ", ".join(g.get("symbol", "") for g in info.get("genes", [])),
                })
        return {"source": "clinvar", "query": query, "results": results}

    @staticmethod
    def _format_search_results(result):
        source = result.get("source", "")
        items = result.get("results", [])
        if not items:
            return f"[{source}] 未找到相关结果。"
        lines = [f"[{source}] 找到 {len(items)} 条结果:"]
        for i, item in enumerate(items, 1):
            if source == "pubmed":
                lines.append(f"  {i}. [{item.get('year','')}] {item.get('title','')}")
                lines.append(f"     {item.get('first_author','')} - {item.get('journal','')} (PMID:{item.get('pmid','')})")
            elif source == "ensembl":
                lines.append(f"  基因: {item.get('gene','')} (chr{item.get('chromosome','')}:{item.get('start','')}-{item.get('end','')})")
                lines.append(f"  描述: {item.get('description','')}")
            elif source == "uniprot":
                lines.append(f"  {i}. {item.get('name','')} ({item.get('accession','')})")
                lines.append(f"     基因: {item.get('gene','')}  功能: {item.get('function','')[:150]}")
            elif source == "clinvar":
                lines.append(f"  {i}. {item.get('title','')} - {item.get('clinical_significance','')}")
                lines.append(f"     基因: {item.get('gene','')} (ClinVar ID: {item.get('clinvar_id','')})")
            elif source in ("duckduckgo", "browser_google", "browser_scan"):
                lines.append(f"  {i}. {item.get('title','')}")
                if item.get('snippet'):
                    lines.append(f"     {item.get('snippet','')[:200]}")
                if item.get('url'):
                    lines.append(f"     URL: {item.get('url','')}")
            else:
                lines.append(f"  {i}. {item.get('snippet', str(item)[:200])}")
        return "\n".join(lines)

    # ================================================================
    #  自主浏览学习工具
    # ================================================================

    def do_browse_and_learn(self, args, response):
        """自主浏览网页学习诊断知识，提取内容供Agent分析和记忆"""
        url = args.get("url", "")
        topic = args.get("topic", "")
        learn_goal = args.get("learn_goal", "")

        if not url and not topic:
            return StepOutcome({"status": "error", "msg": "需要提供 url 或 topic"},
                               next_prompt=self._get_anchor_prompt())

        pages_content = []

        if url:
            yield f"[Action] 浏览网页: {url}\n"
            content = self._fetch_page_content(url)
            if content:
                pages_content.append({"url": url, "content": content})
                yield f"[Fetched] {len(content)} chars from {url}\n"
            else:
                yield f"[Warn] 无法获取 {url} 的内容\n"

        if topic and not pages_content:
            yield f"[Action] 围绕主题搜索学习资源: {topic}\n"
            urls_to_visit = self._find_learning_resources(topic)
            for u in urls_to_visit[:3]:
                yield f"[Browsing] {u}\n"
                content = self._fetch_page_content(u)
                if content:
                    pages_content.append({"url": u, "content": content})
                    yield f"[Fetched] {len(content)} chars\n"

        if not pages_content:
            yield "[Action] 尝试通过 TMWebDriver（篡改猴）浏览器直接访问...\n"
            target_url = url or f"https://www.google.com/search?q={topic}+diagnostic+guidelines"
            try:
                ok, err = tmwd_ensure(timeout=8)
                if not ok:
                    yield f"[Browser] {err}\n"
                else:
                    tmwd_driver.jump(target_url, timeout=10)
                    time.sleep(1.5)
                    out = tmwd_web_execute_js("return document.body.innerText.slice(0,5000);")
                    if out.get("status") == "success":
                        content = (out.get("js_return") or out.get("data")) or ""
                        if content:
                            pages_content.append({"url": target_url, "content": content})
                            yield f"[Browser] 获取到 {len(content)} chars\n"
                    else:
                        yield f"[Browser] 页面读取失败: {out.get('error', '?')}\n"
            except Exception as e:
                yield f"[Browser] TMWebDriver 不可用: {e}\n"

        if not pages_content:
            return StepOutcome(
                {"status": "empty", "msg": "无法获取任何页面内容"},
                next_prompt=self._get_anchor_prompt() +
                    "\n[学习失败] 所有获取渠道均失败。可尝试换URL或用 browser_navigate 手动浏览（需篡改猴已连接）。"
            )

        combined = ""
        for p in pages_content:
            combined += f"\n--- Source: {p['url']} ---\n"
            combined += p["content"][:5000]
            combined += "\n"

        if len(combined) > 12000:
            combined = combined[:12000] + "\n...[内容过长已截断]"

        prompt = (
            self._get_anchor_prompt() +
            f"\n[学习材料] 以下是从网页获取的内容（主题: {topic or url}）:\n"
            f"学习目标: {learn_goal or '提取诊断相关知识'}\n\n"
            f"{combined}\n\n"
            "[指令] 请分析以上内容，提取有价值的诊断知识。如果发现:\n"
            "- 通用诊断规则 → 用 file_patch 更新 L1 的 [RULES]\n"
            "- 疾病特异流程 → 用 file_write 写入 L3 SOP\n"
            "- 环境事实(人群数据等) → 用 file_patch 更新 L2\n"
            "- 如果内容不够有价值，可以跳过不存储。\n"
        )

        return StepOutcome(
            data={"status": "success", "pages": len(pages_content),
                  "total_chars": sum(len(p["content"]) for p in pages_content)},
            next_prompt=prompt
        )

    def _fetch_page_content(self, url):
        """获取网页内容：先用 requests（快/省 token），失败则用 Playwright（能渲染 JS）"""
        import requests as _req
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            r = _req.get(url, headers=headers, timeout=20)
            r.raise_for_status()
            try:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(r.text, 'html.parser')
                for tag in soup(['script', 'style', 'nav', 'footer', 'header',
                                 'aside', 'iframe', 'noscript']):
                    tag.decompose()
                text = soup.get_text(separator='\n', strip=True)
            except ImportError:
                import re as _re
                text = _re.sub(r'<script[^>]*>.*?</script>', '', r.text, flags=_re.DOTALL)
                text = _re.sub(r'<style[^>]*>.*?</style>', '', text, flags=_re.DOTALL)
                text = _re.sub(r'<[^>]+>', ' ', text)
                text = _re.sub(r'\s+', ' ', text).strip()
            lines = [l.strip() for l in text.split('\n') if l.strip() and len(l.strip()) > 10]
            content = '\n'.join(lines)
            if len(content) > 200:
                return content
        except Exception:
            pass

        try:
            ok, err = tmwd_ensure(timeout=8)
            if not ok:
                return ""
            tmwd_driver.jump(url, timeout=10)
            time.sleep(1.5)
            out = tmwd_web_execute_js("return document.body.innerText.slice(0,5000);")
            if out.get("status") != "success":
                return ""
            raw = out.get("js_return") or out.get("data")
            return (raw[:5000] if raw else "") or ""
        except Exception:
            return ""

    def _find_learning_resources(self, topic):
        """根据主题查找学习资源 URL 列表"""
        MEDICAL_SOURCES = [
            ("https://medlineplus.gov/", "MedlinePlus"),
            ("https://www.cdc.gov/", "CDC"),
            ("https://www.who.int/", "WHO"),
            ("https://www.ncbi.nlm.nih.gov/books/", "NCBI Books / GeneReviews"),
        ]
        urls = []
        try:
            ddg = self._search_duckduckgo(f"{topic} diagnosis guidelines site:nih.gov OR site:who.int", 5)
            for item in ddg.get("results", []):
                u = item.get("url", "")
                if u and u.startswith("http"):
                    urls.append(u)
        except Exception:
            pass

        if not urls:
            safe_topic = topic.replace(' ', '+')
            urls = [
                f"https://medlineplus.gov/search/?query={safe_topic}",
                f"https://www.ncbi.nlm.nih.gov/books/?term={safe_topic}",
            ]
        return urls[:5]

    # ================================================================
    #  Playwright 浏览器工具 — 搜索→点击→深度阅读
    # ================================================================

    def do_browser_navigate(self, args, response):
        url = args.get("url", "")
        if not url:
            return StepOutcome({"status": "error", "msg": "缺少 url"})
        ok, err = _quick_browser_check()
        if not ok:
            return StepOutcome({"status": "error", "msg": err})
        yield f"[Browser] 正在打开（篡改猴）: {url}\n"
        try:
            result = _tmwd_navigate_and_get_elements(url)
        except Exception as e:
            return StepOutcome({"status": "error", "msg": str(e)})
        if result.get("status") == "error":
            return StepOutcome(result)
        elements_text = self._format_browser_elements(result.get("elements", []))
        yield f"[Browser] 页面: {result.get('title', '?')} ({result.get('element_count', 0)} 个交互元素)\n"
        return StepOutcome(
            data=result,
            next_prompt=self._get_anchor_prompt() +
                f"\n[浏览器] 已打开: {result.get('title', '?')} ({result.get('url', '')})\n"
                f"可交互元素:\n{elements_text}\n"
                "你可以用 browser_click 点击元素，用 browser_get_content 获取页面正文。"
        )

    def do_browser_click(self, args, response):
        selector = args.get("selector", "")
        if not selector:
            return StepOutcome({"status": "error", "msg": "缺少 selector"})
        ok, err = _quick_browser_check()
        if not ok:
            return StepOutcome({"status": "error", "msg": err})
        yield f"[Browser] 点击（篡改猴）: {selector}\n"
        try:
            ok, err = tmwd_ensure(timeout=8)
            if not ok:
                return StepOutcome({"status": "error", "msg": err})
            selector = selector.strip()
            if re.match(r'^\[\s*\d+\s*\]$', selector):
                idx = int(re.search(r'\d+', selector).group())
                js = f"var el = document.querySelectorAll('a, button, [onclick]')[{idx}]; if(el){{ el.click(); return 'clicked'; }} return 'not_found';"
            else:
                esc = selector.replace('\\', '\\\\').replace("'", "\\'")
                js = f"var el = document.querySelector('{esc}'); if(el){{ el.click(); return 'clicked'; }} return 'not_found';"
            out = tmwd_web_execute_js(js)
            if out.get("status") != "success":
                return StepOutcome({"status": "error", "msg": out.get("error", "JS 执行失败")})
            time.sleep(1.5)
            js2 = """return JSON.stringify({ title: document.title, url: location.href, elements: [].slice.call(document.querySelectorAll('a, button, [onclick]')).map(function(e,i){ return {index: i, tag: e.tagName.toLowerCase(), text: (e.innerText||e.textContent||'').slice(0,80), href: (e.href||'') }; }); });"""
            out2 = tmwd_web_execute_js(js2)
            if out2.get("status") != "success":
                result = {"status": "ok", "title": "", "url": "", "elements": [], "element_count": 0}
            else:
                raw = out2.get("js_return") or out2.get("data")
                data = json.loads(raw) if isinstance(raw, str) else {}
                result = {"status": "ok", "title": data.get("title", ""), "url": data.get("url", ""),
                          "elements": data.get("elements", []), "element_count": len(data.get("elements", []))}
            elements_text = self._format_browser_elements(result.get("elements", []))
            yield f"[Browser] 跳转到: {result.get('title', '?')}\n"
            return StepOutcome(
                data=result,
                next_prompt=self._get_anchor_prompt() +
                    f"\n[浏览器] 当前页面: {result.get('title', '?')} ({result.get('url', '')})\n"
                    f"可交互元素:\n{elements_text}\n"
                    "可用 browser_get_content 获取正文，browser_back 返回上一页。"
            )
        except Exception as e:
            return StepOutcome({"status": "error", "msg": str(e)})

    def do_browser_get_content(self, args, response):
        ok, err = _quick_browser_check()
        if not ok:
            return StepOutcome({"status": "error", "msg": err})
        yield "[Browser] 正在提取页面内容（篡改猴）...\n"
        try:
            ok, err = tmwd_ensure(timeout=8)
            if not ok:
                return StepOutcome({"status": "error", "msg": err})
            out = tmwd_web_execute_js("return document.body.innerText.slice(0,5000);")
            if out.get("status") != "success":
                return StepOutcome({"status": "error", "msg": out.get("error", "获取失败")})
            content = (out.get("js_return") or out.get("data")) or ""
            title_url_js = "return JSON.stringify({ title: document.title, url: location.href });"
            out2 = tmwd_web_execute_js(title_url_js)
            title, url = "?", ""
            if out2.get("status") == "success":
                raw = out2.get("js_return") or out2.get("data")
                if raw:
                    d = json.loads(raw) if isinstance(raw, str) else {}
                    title, url = d.get("title", "?"), d.get("url", "")
            yield f"[Browser] 获取到 {len(content)} 字符"
            if len(content) >= 5000:
                yield " (已截断至 5000 字符)"
            yield "\n"
            return StepOutcome(
                data={"status": "ok", "chars": len(content)},
                next_prompt=self._get_anchor_prompt() +
                    f"\n[页面内容] {title} ({url})\n"
                    f"{content}\n\n"
                    "[指令] 请分析以上内容。如果包含有价值的诊断知识：\n"
                    "- 通用规则 → file_patch 更新 L1 [RULES]\n"
                    "- 疾病SOP → file_write 写入 L3_sops/\n"
                    "- 如需继续阅读，可用 browser_scroll 滚动后再 browser_get_content。"
            )
        except Exception as e:
            return StepOutcome({"status": "error", "msg": str(e)})

    def do_browser_search(self, args, response):
        query = args.get("query", "")
        if not query:
            return StepOutcome({"status": "error", "msg": "缺少 query"})
        yield f"[Browser] 搜索: {query}\n"
        result = None
        try:
            ddg = self._search_duckduckgo(query, 8)
            if ddg.get("results"):
                result = {"status": "ok", "query": query, "source": "duckduckgo",
                          "results": ddg["results"], "count": len(ddg["results"])}
                yield f"[Browser] DuckDuckGo 找到 {len(ddg['results'])} 条\n"
        except Exception as e:
            yield f"[Browser] DuckDuckGo 失败: {e}\n"
        if not result or not result.get("results"):
            yield "[Browser] 回退到 TMWebDriver（篡改猴）Bing 搜索...\n"
            try:
                br = self._browser_search_fallback(query, 8)
                if br.get("results"):
                    result = {"status": "ok", "query": query, "source": br.get("source", "browser"),
                              "results": br["results"], "count": len(br["results"])}
            except Exception as e:
                return StepOutcome({"status": "error", "msg": str(e)})
        if not result or result.get("status") == "error":
            return StepOutcome(result or {"status": "error", "msg": "搜索无结果"})
        items = result.get("results", [])
        formatted = ""
        for i, item in enumerate(items):
            formatted += f"  [{i}] {item.get('title', '?')}\n"
            if item.get("snippet"):
                formatted += f"      {item['snippet'][:120]}\n"
            if item.get("url"):
                formatted += f"      URL: {item['url']}\n"
        yield f"[Browser] 找到 {len(items)} 条结果\n"
        return StepOutcome(
            data=result,
            next_prompt=self._get_anchor_prompt() +
                f"\n[浏览器搜索结果] query={query}\n{formatted}\n"
                "💡 请选择感兴趣的结果，用 browser_navigate(url=...) 深度阅读原文。\n"
                "搜索摘要信息量有限，深度阅读才能提炼有价值的知识。"
        )

    def do_browser_back(self, args, response):
        ok, err = _quick_browser_check()
        if not ok:
            return StepOutcome({"status": "error", "msg": err})
        try:
            ok, err = tmwd_ensure(timeout=8)
            if not ok:
                return StepOutcome({"status": "error", "msg": err})
            tmwd_web_execute_js("window.history.back();")
            time.sleep(1)
            return StepOutcome(data={"status": "ok", "msg": "已后退"})
        except Exception as e:
            return StepOutcome({"status": "error", "msg": str(e)})

    def do_browser_scroll(self, args, response):
        direction = args.get("direction", "down")
        ok, err = _quick_browser_check()
        if not ok:
            return StepOutcome({"status": "error", "msg": err})
        try:
            ok, err = tmwd_ensure(timeout=8)
            if not ok:
                return StepOutcome({"status": "error", "msg": err})
            delta = -400 if direction == "up" else 400
            tmwd_web_execute_js(f"window.scrollBy(0, {delta});")
            return StepOutcome(data={"status": "ok"},
                               next_prompt=self._get_anchor_prompt() +
                               "\n已滚动页面。可用 browser_get_content 获取当前可见内容。")
        except Exception as e:
            return StepOutcome({"status": "error", "msg": str(e)})

    # ================================================================
    #  CDP 桥工具 — 截图 / 通用 CDP / Cookies / Tabs
    # ================================================================

    def do_browser_screenshot(self, args, response):
        """截取当前页面截图（CDP 优先，不可用时自动 fallback 到 JS canvas 方案）"""
        import base64
        save_path = args.get("save_path", "")
        if not save_path:
            save_path = os.path.join("temp", f"screenshot_{int(time.time())}.png")
        os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)

        b64_data = None
        method_used = None

        if is_cdp_available():
            yield "[Browser] 通过 CDP 截图中（超时 6s）...\n"
            try:
                resp = cdp_execute({"cmd": "cdp", "method": "Page.captureScreenshot",
                                    "params": {"format": "png"}}, timeout=6)
                if resp.get("ok") and isinstance(resp.get("data"), dict):
                    b64_data = resp["data"].get("data", "")
                if not b64_data and isinstance(resp.get("data"), dict):
                    b64_data = resp.get("data", {}).get("data", "")
                if b64_data:
                    method_used = "CDP"
                else:
                    yield f"[Browser] CDP 截图未返回数据: {resp.get('error', '未知')}，尝试 fallback...\n"
            except Exception as e:
                yield f"[Browser] CDP 截图异常: {str(e)[:100]}，尝试 fallback...\n"
        else:
            yield "[Browser] CDP 桥不可用，使用 JS canvas fallback 截图...\n"

        if not b64_data:
            try:
                js_fallback = """
(function(){
  try {
    var w = Math.min(window.innerWidth || 1280, 1280);
    var h = Math.min(window.innerHeight || 800, 960);
    var c = document.createElement('canvas');
    c.width = w; c.height = h;
    var ctx = c.getContext('2d');
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, w, h);
    ctx.font = 'bold 14px monospace';
    ctx.fillStyle = '#222';
    ctx.fillText('Page: ' + document.title, 10, 20);
    ctx.fillText('URL: ' + location.href, 10, 38);
    ctx.fillText('Size: ' + w + 'x' + h + '  Elements: ' + document.querySelectorAll('*').length, 10, 56);
    ctx.strokeStyle = '#ccc';
    ctx.beginPath(); ctx.moveTo(10, 65); ctx.lineTo(w - 10, 65); ctx.stroke();
    ctx.font = '12px monospace';
    ctx.fillStyle = '#444';
    var text = '';
    try { text = document.body.innerText || ''; } catch(e) { text = '(cannot read body)'; }
    var lines = text.substring(0, 3000).split(String.fromCharCode(10));
    var y = 82;
    for (var i = 0; i < lines.length && y < h - 10; i++) {
      var line = lines[i].substring(0, 150);
      if (line.length > 0) { ctx.fillText(line, 10, y); y += 15; }
    }
    var dataUrl = c.toDataURL('image/png');
    return dataUrl.split(',')[1] || 'ERR:empty_data';
  } catch(e) { return 'ERR:' + e.message; }
})()
"""
                result = tmwd_web_execute_js(js_fallback)
                if result.get("status") == "success":
                    raw = result.get("js_return") or result.get("data") or ""
                    if raw and not raw.startswith("ERR:"):
                        b64_data = raw
                        method_used = "JS canvas fallback"
                    else:
                        return StepOutcome({"status": "error", "msg": f"JS fallback 也失败: {raw[:200]}"})
                else:
                    return StepOutcome({"status": "error", "msg": f"JS 执行失败: {result.get('error', '未知')}"})
            except Exception as e:
                return StepOutcome({"status": "error", "msg": f"所有截图方式均失败: {format_error(e)}"})

        try:
            with open(save_path, "wb") as f:
                f.write(base64.b64decode(b64_data))
            size_kb = os.path.getsize(save_path) // 1024
            yield f"[Browser] 截图已保存 ({method_used}): {save_path} ({size_kb}KB)\n"
            return StepOutcome(
                data={"status": "ok", "path": save_path, "size_kb": size_kb, "method": method_used},
                next_prompt=self._get_anchor_prompt() +
                    f"\n[截图] 已通过 {method_used} 保存到 {save_path} ({size_kb}KB)。"
                    "\n可用 code_run 打开查看，或传给 LLM 视觉分析。"
            )
        except Exception as e:
            return StepOutcome({"status": "error", "msg": f"保存截图失败: {format_error(e)}"})

    def do_cdp_command(self, args, response):
        """通用 CDP 命令执行（高级工具，用于 isTrusted 事件派发、DOM 操作等）"""
        method = args.get("method", "")
        params = args.get("params", {})
        use_batch = args.get("batch", False)

        if not method and not use_batch:
            return StepOutcome({"status": "error", "msg": "需要 method 或 batch 参数"})

        if not is_cdp_available():
            return StepOutcome({"status": "error", "msg": "CDP 桥不可用。请在 chrome://extensions/ 检查 TMWD CDP Bridge 扩展状态，如 Service Worker 无效请移除后重新加载。"})

        yield f"[CDP] 执行: {method or 'batch'}\n"
        try:
            if use_batch:
                commands = args.get("commands", [])
                if not commands:
                    return StepOutcome({"status": "error", "msg": "batch 模式需要 commands 列表"})
                resp = cdp_execute({"cmd": "batch", "commands": commands}, timeout=8)
            else:
                resp = cdp_execute({"cmd": "cdp", "method": method, "params": params}, timeout=8)

            if resp.get("ok") or resp.get("data"):
                yield f"[CDP] 成功\n"
                data_preview = json.dumps(resp, ensure_ascii=False)
                if len(data_preview) > 500:
                    data_preview = data_preview[:500] + "..."
                return StepOutcome(
                    data=resp,
                    next_prompt=self._get_anchor_prompt() +
                        f"\n[CDP 结果] {data_preview}"
                )
            else:
                return StepOutcome({"status": "error",
                                    "msg": resp.get("error", "CDP 命令失败")})
        except Exception as e:
            return StepOutcome({"status": "error", "msg": f"CDP 执行失败: {format_error(e)}"})

    def do_browser_cookies(self, args, response):
        """获取当前页面的 Cookie 列表"""
        if not is_cdp_available():
            return StepOutcome({"status": "error", "msg": "CDP 桥不可用，无法获取 Cookies。请检查 chrome://extensions/ 中 TMWD CDP Bridge 扩展状态。"})
        yield "[Browser] 获取 Cookies...\n"
        try:
            resp = cdp_execute({"cmd": "cookies"}, timeout=5)
            if resp.get("ok"):
                cookies = resp.get("data", [])
                yield f"[Browser] 获取到 {len(cookies)} 个 Cookie\n"
                return StepOutcome(data={"status": "ok", "cookies": cookies, "count": len(cookies)})
            return StepOutcome({"status": "error", "msg": resp.get("error", "获取 Cookies 失败")})
        except Exception as e:
            return StepOutcome({"status": "error", "msg": str(e)})

    def do_browser_tabs(self, args, response):
        """通过 CDP 桥列出或切换浏览器标签页"""
        if not is_cdp_available():
            return StepOutcome({"status": "error", "msg": "CDP 桥不可用，无法操作标签页。请检查 chrome://extensions/ 中 TMWD CDP Bridge 扩展状态。"})
        action = args.get("action", "list")
        tab_id = args.get("tab_id")
        yield f"[Browser] Tabs: {action}\n"
        try:
            if action == "switch" and tab_id:
                resp = cdp_execute({"cmd": "tabs", "method": "switch", "tabId": int(tab_id)}, timeout=5)
            else:
                resp = cdp_execute({"cmd": "tabs"}, timeout=5)
            if resp.get("ok"):
                tabs = resp.get("data", [])
                lines = [f"  [{t.get('id')}] {'→ ' if t.get('active') else '  '}{t.get('title','?')[:60]}  {t.get('url','')[:80]}"
                         for t in tabs]
                yield f"[Browser] {len(tabs)} 个标签页\n"
                return StepOutcome(
                    data={"status": "ok", "tabs": tabs},
                    next_prompt=self._get_anchor_prompt() +
                        f"\n[标签页列表]\n" + "\n".join(lines) +
                        "\n可用 browser_tabs(action='switch', tab_id=N) 切换标签页。"
                )
            return StepOutcome({"status": "error", "msg": resp.get("error", "获取标签页失败")})
        except Exception as e:
            return StepOutcome({"status": "error", "msg": str(e)})

    def _format_browser_elements(self, elements):
        if not elements:
            return "  (无可交互元素)"
        lines = []
        for el in elements[:MAX_BROWSER_ELEMENTS]:
            idx = el.get("index", "?")
            tag = el.get("tag", "?")
            text = el.get("text", "")
            href = el.get("href", "")
            line = f"  [{idx}] <{tag}> {text}"
            if href and not href.startswith("javascript:"):
                line += f"  → {href[:80]}"
            lines.append(line)
        if len(elements) > MAX_BROWSER_ELEMENTS:
            lines.append(f"  ... 还有 {len(elements) - MAX_BROWSER_ELEMENTS} 个元素")
        return '\n'.join(lines)

    # ================================================================
    #  手机控制工具 (ADB)
    # ================================================================

    def do_phone_control(self, args, response):
        """通过ADB控制连接的Android手机"""
        from tools.phone_control import (
            check_connection, screenshot, tap, swipe, input_text,
            press_key, launch_app, ui_dump, scroll_down, scroll_up,
            get_current_app, list_installed_apps
        )
        action = args.get("action", "")
        if not action:
            return StepOutcome(
                data={"status": "error", "msg": "缺少 action 参数"},
                next_prompt=self._get_anchor_prompt() + "\n[错误] phone_control 需要指定 action 参数。"
            )

        yield f"[Phone] 执行操作: {action}\n"

        try:
            if action == "check_connection":
                ok, info = check_connection()
                status_msg = "✅ 手机已连接" if ok else "❌ 手机未连接"
                return StepOutcome(
                    data={"status": "ok" if ok else "error", "connected": ok, "info": info},
                    next_prompt=self._get_anchor_prompt() + f"\n[手机连接状态]\n{status_msg}\n{info}\n\n请根据连接状态决定下一步操作。"
                )

            elif action == "screenshot":
                b64, path = screenshot()
                if b64 is None:
                    return StepOutcome(
                        data={"status": "error", "msg": path},
                        next_prompt=self._get_anchor_prompt() + f"\n[错误] 截图失败: {path}"
                    )
                return StepOutcome(
                    data={"status": "ok", "msg": f"截图已保存: {path}", "path": path, "size": f"{len(b64)//1024}KB"},
                    next_prompt=self._get_anchor_prompt() + f"\n[截图成功] 已保存到 {path}，大小 {len(b64)//1024}KB。\n如需分析屏幕内容，请使用 phone_screen_analyze 工具。"
                )

            elif action == "tap":
                x, y = args.get("x", 0), args.get("y", 0)
                if not x or not y:
                    return StepOutcome(
                        data={"status": "error", "msg": "tap 需要 x, y 坐标"},
                        next_prompt=self._get_anchor_prompt() + "\n[错误] tap 操作需要提供 x 和 y 坐标参数。"
                    )
                ok, msg = tap(x, y)
                time.sleep(0.5)
                return StepOutcome(
                    data={"status": "ok" if ok else "error", "msg": msg},
                    next_prompt=self._get_anchor_prompt() + f"\n[点击操作] 已点击坐标 ({x}, {y})。\n建议用 ui_dump 或 phone_screen_analyze 确认操作结果。"
                )

            elif action == "swipe":
                x1, y1 = args.get("x", args.get("x1", 0)), args.get("y", args.get("y1", 0))
                x2, y2 = args.get("x2", 0), args.get("y2", 0)
                if not all([x1, y1, x2, y2]):
                    return StepOutcome(
                        data={"status": "error", "msg": "swipe 需要 x,y (起点) 和 x2,y2 (终点)"},
                        next_prompt=self._get_anchor_prompt() + "\n[错误] swipe 操作需要提供起点 (x,y) 和终点 (x2,y2) 坐标。"
                    )
                ok, msg = swipe(x1, y1, x2, y2, args.get("duration", 300))
                time.sleep(0.5)
                return StepOutcome(
                    data={"status": "ok" if ok else "error", "msg": msg},
                    next_prompt=self._get_anchor_prompt() + f"\n[滑动操作] 已从 ({x1},{y1}) 滑动到 ({x2},{y2})。\n建议用 ui_dump 确认页面变化。"
                )

            elif action == "input_text":
                text = args.get("text", "")
                if not text:
                    return StepOutcome(
                        data={"status": "error", "msg": "input_text 需要 text 参数"},
                        next_prompt=self._get_anchor_prompt() + "\n[错误] input_text 需要提供 text 参数。"
                    )
                ok, msg = input_text(text)
                return StepOutcome(
                    data={"status": "ok" if ok else "error", "msg": msg},
                    next_prompt=self._get_anchor_prompt() + f"\n[文本输入] 已输入文字: {text}"
                )

            elif action == "press_key":
                key = args.get("key", "back")
                ok, msg = press_key(key)
                time.sleep(0.3)
                return StepOutcome(
                    data={"status": "ok" if ok else "error", "msg": msg},
                    next_prompt=self._get_anchor_prompt() + f"\n[按键操作] 已按下 {key} 键。"
                )

            elif action == "launch_app":
                app = args.get("app", "")
                if not app:
                    return StepOutcome(
                        data={"status": "error", "msg": "launch_app 需要 app 参数"},
                        next_prompt=self._get_anchor_prompt() + "\n[错误] launch_app 需要提供 app 参数（App名称或包名）。"
                    )
                ok, msg = launch_app(app)
                time.sleep(2)
                if ok:
                    next_prompt = self._get_anchor_prompt() + f"\n[启动App] {msg}\n等待2秒后，建议用 ui_dump 或 phone_screen_analyze 查看App界面。"
                else:
                    next_prompt = self._get_anchor_prompt() + f"\n[启动App 失败] {msg}\n请根据用户描述与上述本机已安装列表自行做关键词/语义匹配选包重试；若列表中无相关包则停止任务并向用户说明或建议其说出具体应用名称。"
                return StepOutcome(
                    data={"status": "ok" if ok else "error", "msg": msg},
                    next_prompt=next_prompt
                )

            elif action == "ui_dump":
                keyword = args.get("keyword")
                clickable_only = args.get("clickable_only", False)
                nodes, summary = ui_dump(keyword, clickable_only)
                cur = get_current_app()
                header = f"当前App: {cur.get('package','?')} / {cur.get('activity','?')}\n\n"
                full_summary = header + summary
                return StepOutcome(
                    data={"status": "ok", "msg": full_summary, "elements_count": len(nodes), "nodes": nodes},
                    next_prompt=self._get_anchor_prompt() + f"\n[UI元素列表]\n{full_summary}\n\n根据UI元素决定下一步操作（点击、滑动等）。"
                )

            elif action == "scroll_down":
                ok, msg = scroll_down()
                time.sleep(0.5)
                return StepOutcome(
                    data={"status": "ok" if ok else "error", "msg": msg},
                    next_prompt=self._get_anchor_prompt() + "\n[滚动] 已向下滚动一屏。建议用 ui_dump 查看新内容。"
                )

            elif action == "scroll_up":
                ok, msg = scroll_up()
                time.sleep(0.5)
                return StepOutcome(
                    data={"status": "ok" if ok else "error", "msg": msg},
                    next_prompt=self._get_anchor_prompt() + "\n[滚动] 已向上滚动一屏。建议用 ui_dump 查看新内容。"
                )

            elif action == "current_app":
                cur = get_current_app()
                return StepOutcome(
                    data={"status": "ok", "current": cur},
                    next_prompt=self._get_anchor_prompt() + f"\n[当前App] 包名: {cur.get('package','?')}, Activity: {cur.get('activity','?')}"
                )

            elif action == "list_apps":
                keyword = args.get("keyword")
                apps = list_installed_apps(keyword)
                if isinstance(apps, str):
                    return StepOutcome(
                        data={"status": "error", "msg": apps},
                        next_prompt=self._get_anchor_prompt() + f"\n[错误] 获取App列表失败: {apps}"
                    )
                apps_list = "\n".join(apps[:20])
                return StepOutcome(
                    data={"status": "ok", "apps": apps[:50], "total": len(apps)},
                    next_prompt=self._get_anchor_prompt() + f"\n[已安装App列表] 共 {len(apps)} 个，前20个:\n{apps_list}"
                )
            else:
                return StepOutcome(
                    data={"status": "error", "msg": f"未知操作: {action}"},
                    next_prompt=self._get_anchor_prompt() + f"\n[错误] 未知操作: {action}。\n可用操作: check_connection, screenshot, tap, swipe, input_text, press_key, launch_app, ui_dump, scroll_down, scroll_up, current_app, list_apps"
                )
        except Exception as e:
            return StepOutcome(
                data={"status": "error", "msg": f"手机操作失败: {format_error(e)}"},
                next_prompt=self._get_anchor_prompt() + f"\n[异常] 手机操作失败: {format_error(e)}"
            )

    def do_phone_screen_analyze(self, args, response):
        """截取手机屏幕并用LLM视觉分析"""
        from tools.phone_control import screenshot, check_connection, get_current_app

        question = args.get("question", "描述当前手机屏幕内容，列出可操作的按钮和文字")
        yield "[Phone] 截取手机屏幕并分析...\n"

        b64, path = screenshot()
        if b64 is None:
            # 连接检查只在“截图失败”时按需触发，避免在成功路径上反复确认连接
            ok, info = check_connection()
            if not ok:
                return StepOutcome(
                    data={"status": "error", "msg": f"手机未连接: {info}"},
                    next_prompt=self._get_anchor_prompt() + f"\n[错误] 手机未连接: {info}\n请先用 phone_control(action='check_connection') 检查连接。"
                )
            return StepOutcome(
                data={"status": "error", "msg": f"截图失败: {path}"},
                next_prompt=self._get_anchor_prompt() + f"\n[错误] 截图失败: {path}"
            )

        cur = get_current_app()
        prompt = (
            f"你是一个手机屏幕分析助手。这是一张 Android 手机截图。\n"
            f"当前App: {cur.get('package','unknown')}\n\n"
            f"请回答: {question}\n\n"
            f"要求:\n"
            f"1. 描述当前页面是什么App/什么功能\n"
            f"2. 列出主要文字内容\n"
            f"3. 列出可以点击的按钮/图标及其大致坐标区域（上/中/下，左/中/右）\n"
            f"4. 建议下一步操作\n"
            f"5. 如果是列表/菜单，列出各项内容和对应坐标"
        )

        try:
            from sidercall import LLMSession
            import mykey
            cfg = getattr(mykey, 'oai_config', {})
            if not cfg.get('apikey'):
                return StepOutcome(
                    data={"status": "error", "msg": "视觉分析需要配置LLM API。截图已保存: " + path},
                    next_prompt=self._get_anchor_prompt() + f"\n[错误] 视觉分析需要配置支持图片的LLM API（如 GPT-4o）。\n截图已保存到: {path}\n你可以手动查看截图，或配置 mykey.py 中的 oai_config。"
                )
            vision_model = cfg.get('model', 'gpt-4o-mini')
            if 'thinking' in vision_model:
                for k in ['oai_config2', 'oai_config3', 'oai_config4']:
                    alt = getattr(mykey, k, {})
                    if alt.get('apikey'):
                        cfg = alt
                        vision_model = alt.get('model', vision_model)
                        break

            session = LLMSession(
                api_key=cfg['apikey'],
                api_base=cfg.get('apibase', 'https://api.openai.com'),
                model=vision_model,
                context_win=4000
            )
            analysis = session.ask(prompt, image_base64=b64)
            yield f"[Vision] 分析完成\n"
            return StepOutcome(
                data={
                    "status": "ok",
                    "analysis": analysis,
                    "screenshot_path": path,
                    "current_app": cur
                },
                next_prompt=self._get_anchor_prompt() + f"\n[屏幕视觉分析]\n当前App: {cur.get('package','?')}\n\n{analysis}\n\n根据分析结果决定下一步操作（点击、滑动、输入等）。"
            )
        except Exception as e:
            return StepOutcome(
                data={
                    "status": "error",
                    "msg": f"视觉分析失败: {format_error(e)}\n截图已保存: {path}",
                    "screenshot_path": path
                },
                next_prompt=self._get_anchor_prompt() + f"\n[异常] 视觉分析失败: {format_error(e)}\n截图已保存到: {path}\n可以尝试用 ui_dump 获取文本UI元素作为替代方案。"
            )

    # ================================================================
    #  健康管家工具（能力域 2-5）
    # ================================================================

    def do_load_user_profile(self, args, response):
        """加载用户健康画像"""
        yield "[Action] Loading user profile...\n"
        profile = self.health_store.load_profile()
        summary_parts = []
        if profile.get('basic_info'):
            summary_parts.append(f"基本信息: {json.dumps(profile['basic_info'], ensure_ascii=False)}")
        if profile.get('chronic_diseases'):
            summary_parts.append(f"慢病: {', '.join(str(d) for d in profile['chronic_diseases'])}")
        if profile.get('allergies'):
            summary_parts.append(f"过敏: {', '.join(str(a) for a in profile['allergies'])}")
        if profile.get('medications'):
            active = [m for m in profile['medications'] if isinstance(m, dict) and m.get('active', True)]
            if active:
                summary_parts.append(f"当前用药: {', '.join(m.get('drug_name','?') for m in active)}")
        if profile.get('health_goals'):
            summary_parts.append(f"健康目标: {', '.join(str(g) for g in profile['health_goals'])}")
        summary = '\n'.join(summary_parts) if summary_parts else '(画像为空，请通过对话逐步完善)'
        yield f"[Result]\n{summary}\n"
        return StepOutcome(
            data={"status": "success", "profile": profile},
            next_prompt=self._get_anchor_prompt() + "\n[用户画像已加载] 请根据画像为用户提供个性化服务。"
        )

    def do_update_user_profile(self, args, response):
        """更新用户健康画像字段"""
        field = args.get('field', '')
        action = args.get('action', 'set')
        data = args.get('data', {})
        yield f"[Action] Updating profile: {field} ({action})\n"
        result = self.health_store.update_profile_field(field, action, data)
        yield f"[Result] {result}\n"
        return StepOutcome(data=result, next_prompt=self._get_anchor_prompt())

    def do_parse_checkup_report(self, args, response):
        """解析体检报告（文本形式，图片由 LLM 多模态直接处理）"""
        report_text = args.get('report_text', '')
        report_date = args.get('report_date', time.strftime('%Y-%m-%d'))
        hospital = args.get('hospital', '')
        yield f"[Action] Parsing checkup report (date={report_date})...\n"
        if not report_text:
            return StepOutcome(
                {"status": "info", "msg": "未提供报告文本。如果用户上传了图片，请直接用多模态能力读取图片内容，提取指标后调用此工具传入结构化数据。"},
                next_prompt=self._get_anchor_prompt()
            )
        path = self.health_store.append_checkup(report_date, {"raw_text": report_text}, hospital)
        yield f"[Result] 报告已保存到 {path}\n"
        yield "请提取报告中的关键指标（指标名、数值、单位、参考范围），然后用 interpret_indicator 逐个解读。\n"
        return StepOutcome(
            data={"status": "success", "saved_to": path, "date": report_date},
            next_prompt=self._get_anchor_prompt() +
                "\n[体检报告已保存] 请从报告中提取结构化指标，逐个解读并与历史数据对比。"
        )

    def do_interpret_indicator(self, args, response):
        """解读健康指标"""
        indicator = args.get('indicator', '')
        value = args.get('value')
        unit = args.get('unit', '')
        yield f"[Action] Interpreting: {indicator} = {value} {unit}\n"
        profile = self.health_store.load_profile()
        trend_data = self.health_store.get_indicator_trend(indicator)
        context = {
            "indicator": indicator, "value": value, "unit": unit,
            "user_age": profile.get('basic_info', {}).get('age'),
            "user_sex": profile.get('basic_info', {}).get('sex'),
            "chronic_diseases": profile.get('chronic_diseases', []),
            "medications": [m.get('drug_name') for m in profile.get('medications', []) if isinstance(m, dict) and m.get('active')],
            "history_trend": trend_data[-5:] if trend_data else [],
        }
        yield f"[Context] {json.dumps(context, ensure_ascii=False)}\n"
        return StepOutcome(
            data=context,
            next_prompt=self._get_anchor_prompt() +
                f"\n[指标解读] 请基于以上上下文，用通俗语言解读 {indicator}={value}{unit}，包括：正常范围、当前状态、可能原因、生活建议。如有历史趋势请分析变化。"
        )

    def do_compare_checkup_history(self, args, response):
        """对比历次体检数据"""
        indicators = args.get('indicators', [])
        yield "[Action] Comparing checkup history...\n"
        history = self.health_store.get_checkup_history()
        if len(history) < 2:
            return StepOutcome(
                {"status": "info", "msg": f"体检记录不足（当前{len(history)}次），至少需要2次才能对比。"},
                next_prompt=self._get_anchor_prompt()
            )
        yield f"[Result] Found {len(history)} checkup records\n"
        return StepOutcome(
            data={"status": "success", "records": history, "requested_indicators": indicators},
            next_prompt=self._get_anchor_prompt() +
                "\n[体检对比] 请分析各次体检数据的变化趋势，标注恶化/改善/稳定的指标。"
        )

    def do_get_health_timeline(self, args, response):
        """获取指标时间线趋势"""
        indicator = args.get('indicator', '')
        period = args.get('period', '1y')
        yield f"[Action] Getting timeline for {indicator} (period={period})...\n"
        trend = self.health_store.get_indicator_trend(indicator, period)
        if not trend:
            return StepOutcome(
                {"status": "info", "msg": f"未找到 {indicator} 的历史数据。"},
                next_prompt=self._get_anchor_prompt()
            )
        yield f"[Result] {len(trend)} data points\n"
        return StepOutcome(data={"indicator": indicator, "trend": trend},
                           next_prompt=self._get_anchor_prompt())

    def do_manage_medication(self, args, response):
        """管理用药"""
        action = args.get('action', 'list')
        drug_name = args.get('drug_name', '')
        yield f"[Action] Medication: {action} {drug_name}\n"

        if action == 'list':
            meds = self.health_store.load_medications()
            active = [m for m in meds if m.get('active', True)]
            inactive = [m for m in meds if not m.get('active', True)]
            result = {"active": active, "inactive_count": len(inactive)}
        elif action == 'add':
            result = self.health_store.add_medication(
                drug_name, args.get('dosage', ''), args.get('frequency', ''), args.get('reason', ''))
        elif action == 'stop':
            result = self.health_store.stop_medication(drug_name, args.get('reason', ''))
        elif action == 'detail':
            meds = self.health_store.load_medications()
            found = [m for m in meds if drug_name.lower() in m.get('drug_name', '').lower()]
            result = {"matches": found} if found else {"status": "info", "msg": f"未找到: {drug_name}"}
        else:
            result = {"status": "error", "msg": f"未知操作: {action}"}

        yield f"[Result] {smart_format(result)}\n"
        return StepOutcome(data=result, next_prompt=self._get_anchor_prompt())

    def do_check_drug_interaction(self, args, response):
        """检查药物相互作用"""
        new_drug = args.get('new_drug', '')
        meds = self.health_store.load_medications()
        active_drugs = [m.get('drug_name') for m in meds if m.get('active', True)]
        yield f"[Action] Checking drug interactions: current={active_drugs}, new={new_drug or '(check existing)'}\n"
        check_list = active_drugs + ([new_drug] if new_drug else [])
        if len(check_list) < 2:
            return StepOutcome(
                {"status": "info", "msg": "药物不足2种，无需检查交互。"},
                next_prompt=self._get_anchor_prompt()
            )
        return StepOutcome(
            data={"drugs_to_check": check_list, "new_drug": new_drug},
            next_prompt=self._get_anchor_prompt() +
                f"\n[药物交互检查] 请基于药学知识分析以下药物之间的相互作用风险: {', '.join(check_list)}。如不确定，请用 web_search 查询。"
        )

    def do_set_health_reminder(self, args, response):
        """设置健康提醒"""
        rtype = args.get('type', 'custom')
        title = args.get('title', '')
        schedule = args.get('schedule', '')
        note = args.get('note', '')
        yield f"[Action] Setting reminder: {title} ({schedule})\n"
        result = self.health_store.add_reminder(rtype, title, schedule, note)
        yield f"[Result] {result}\n"
        return StepOutcome(data=result, next_prompt=self._get_anchor_prompt())

    def do_list_reminders(self, args, response):
        """列出提醒"""
        status_filter = args.get('status', 'pending')
        reminders = self.health_store.load_reminders()
        if status_filter != 'all':
            reminders = [r for r in reminders if r.get('status') == status_filter]
        yield f"[Result] {len(reminders)} reminders ({status_filter})\n"
        return StepOutcome(data={"reminders": reminders, "count": len(reminders)},
                           next_prompt=self._get_anchor_prompt())

    def do_log_lifestyle(self, args, response):
        """记录生活方式数据"""
        category = args.get('category', '')
        data = args.get('data', {})
        timestamp = args.get('timestamp', '')
        yield f"[Action] Logging {category} data\n"
        result = self.health_store.append_lifestyle_log(category, data, timestamp or None)
        yield f"[Result] {result}\n"
        return StepOutcome(data=result, next_prompt=self._get_anchor_prompt())

    def do_analyze_lifestyle(self, args, response):
        """分析生活方式"""
        period = args.get('period', '1w')
        focus = args.get('focus', 'overall')
        days_map = {'1w': 7, '2w': 14, '1m': 30, '3m': 90}
        days = days_map.get(period, 7)
        yield f"[Action] Analyzing lifestyle (period={period}, focus={focus})...\n"
        records = self.health_store.read_lifestyle_log(
            category=focus if focus != 'overall' else None, days=days)
        if not records:
            return StepOutcome(
                {"status": "info", "msg": f"过去 {days} 天无{focus}记录。请先用 log_lifestyle 记录数据。"},
                next_prompt=self._get_anchor_prompt()
            )
        yield f"[Result] {len(records)} records in {days} days\n"
        return StepOutcome(
            data={"records": records, "period": period, "focus": focus},
            next_prompt=self._get_anchor_prompt() +
                f"\n[生活方式分析] 请基于以上 {len(records)} 条记录，分析用户的{focus}习惯，给出具体改善建议。"
        )

    def do_health_risk_screening(self, args, response):
        """健康风险初筛"""
        focus = args.get('focus_diseases', [])
        yield "[Action] Health risk screening...\n"
        profile = self.health_store.load_profile()
        try:
            with open(self.health_store._path('latest_indicators.json'), 'r', encoding='utf-8') as f:
                indicators = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            indicators = {}
        context = {
            "profile": profile,
            "latest_indicators": indicators,
            "focus_diseases": focus,
        }
        yield f"[Context] Profile loaded, {len(indicators)} indicators available\n"
        return StepOutcome(
            data=context,
            next_prompt=self._get_anchor_prompt() +
                "\n[风险筛查] 请基于用户画像和最新指标，评估常见慢病风险（心血管、糖尿病、高血压等）。注意标注「仅供参考，请咨询医生」。"
        )

    # ================================================================
    #  专业医疗工具（能力域 6/7/8）
    # ================================================================

    def do_medication_review(self, args, response):
        """全面用药审查：DDI + 疾病禁忌 + 过敏交叉 + 特殊人群"""
        drugs = args.get('drugs', [])
        new_drug = args.get('new_drug', '')
        check_scope = args.get('check_scope', 'full')
        yield f"[Action] Medication review (scope={check_scope})\n"

        profile = self.health_store.load_profile()
        if not drugs:
            meds = self.health_store.load_medications()
            drugs = [m.get('drug_name') for m in meds if m.get('active', True)]
        all_drugs = drugs + ([new_drug] if new_drug else [])

        if len(all_drugs) < 1:
            return StepOutcome(
                {"status": "info", "msg": "无用药记录，请先通过 manage_medication 添加用药。"},
                next_prompt=self._get_anchor_prompt()
            )

        try:
            with open(self.health_store._path('latest_indicators.json'), 'r', encoding='utf-8') as f:
                indicators = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            indicators = {}

        context = {
            "drugs": drugs,
            "new_drug": new_drug,
            "check_scope": check_scope,
            "profile": {
                "age": profile.get('basic_info', {}).get('age'),
                "sex": profile.get('basic_info', {}).get('sex'),
                "allergies": profile.get('allergies', []),
                "chronic_diseases": profile.get('chronic_diseases', []),
                "pregnant_or_lactating": profile.get('basic_info', {}).get('pregnant_or_lactating', False),
            },
            "indicators": {
                "eGFR": indicators.get('eGFR', {}).get('value'),
                "ALT": indicators.get('ALT', {}).get('value') or indicators.get('谷丙转氨酶', {}).get('value'),
                "AST": indicators.get('AST', {}).get('value') or indicators.get('谷草转氨酶', {}).get('value'),
                "INR": indicators.get('INR', {}).get('value'),
                "SCr": indicators.get('肌酐', {}).get('value') or indicators.get('SCr', {}).get('value'),
            },
        }

        yield f"[Context] {len(all_drugs)} drugs, allergies={context['profile']['allergies']}\n"

        scope_instructions = {
            'full': "请按 medication_review_sop 进行全面审查：DDI + 药物-疾病禁忌 + 过敏交叉反应 + 特殊人群(孕哺/老年Beers) + 剂量合理性。",
            'ddi_only': "仅检查药物-药物相互作用(DDI)。",
            'allergy_only': "仅检查药物与已知过敏的交叉反应。",
            'dosage_only': "仅检查剂量是否需要根据肝肾功能调整。",
        }

        return StepOutcome(
            data=context,
            next_prompt=self._get_anchor_prompt() +
                f"\n[用药审查] 药物列表: {', '.join(all_drugs)}\n"
                f"{scope_instructions.get(check_scope, scope_instructions['full'])}\n"
                "对每个发现的问题，按风险分级：🔴禁忌 🟠严重 🟡中等 🟢轻微。\n"
                "每项含：涉及药物、交互机制、临床后果、建议措施。\n"
                "不确定的交互请用 web_search 确认（搜索时用通用名，禁止含用户信息）。\n"
                "禁忌级问题必须强烈建议就医。末尾标注「以上审查仅供参考，用药调整请咨询医生或药师」。"
        )

    def do_extract_medical_record(self, args, response):
        """将非结构化病历文本抽取为结构化 JSON"""
        raw_text = args.get('raw_text', '')
        record_type = args.get('record_type', 'inpatient')
        yield f"[Action] Extracting medical record (type={record_type}, len={len(raw_text)})\n"

        if not raw_text or len(raw_text) < 20:
            return StepOutcome(
                {"status": "error", "msg": "病历文本过短或为空，请提供完整病历内容。"},
                next_prompt=self._get_anchor_prompt()
            )

        return StepOutcome(
            data={"status": "extracting", "raw_length": len(raw_text), "record_type": record_type},
            next_prompt=self._get_anchor_prompt() +
                f"\n[病历抽取] 请将以下病历文本抽取为标准结构化JSON。\n"
                f"病历类型: {record_type}\n"
                "输出格式:\n"
                "```json\n"
                "{\n"
                '  "chief_complaint": "主诉",\n'
                '  "hpi": "现病史",\n'
                '  "past_history": "既往史",\n'
                '  "personal_history": "个人史",\n'
                '  "family_history": "家族史",\n'
                '  "allergy_history": "过敏史",\n'
                '  "physical_exam": {"general": "...", "related": "..."},\n'
                '  "auxiliary_exam": [{"name": "检查名", "result": "结果", "date": "日期"}],\n'
                '  "diagnoses": [{"rank": 1, "text": "主诊断"}, {"rank": 2, "text": "其他诊断"}],\n'
                '  "treatment_plan": "治疗方案",\n'
                '  "medications": [{"drug": "药名", "dosage": "剂量", "frequency": "频次"}],\n'
                '  "timeline": [{"date": "...", "event": "..."}]\n'
                "}\n"
                "```\n"
                "要求: 严格从原文提取，缺失字段标为 null，不要推测编造。\n\n"
                f"--- 原始病历 ---\n{raw_text[:8000]}\n--- 病历结束 ---"
        )

    def do_check_medical_record(self, args, response):
        """对结构化病历进行智能质控"""
        structured_record = args.get('structured_record', {})
        check_level = args.get('check_level', 'standard')
        yield f"[Action] Medical record QC (level={check_level})\n"

        if not structured_record:
            return StepOutcome(
                {"status": "error", "msg": "请先用 extract_medical_record 提取结构化病历。"},
                next_prompt=self._get_anchor_prompt()
            )

        profile = self.health_store.load_profile()
        allergies = profile.get('allergies', [])

        context = {
            "record": structured_record,
            "check_level": check_level,
            "known_allergies": allergies,
        }

        level_desc = {
            'strict': "三甲医院标准：检查所有维度，包括叙事结构和鉴别诊断完整性",
            'standard': "常规标准：检查一致性、完整性、禁忌、证据充分性",
            'basic': "基础标准：仅检查致命错误（矛盾/禁忌/时间线错误）",
        }

        yield f"[Context] Record has {len(structured_record.get('diagnoses', []))} diagnoses, level={check_level}\n"
        return StepOutcome(
            data=context,
            next_prompt=self._get_anchor_prompt() +
                f"\n[病历质控] 请按 medical_record_qc_sop 对以下结构化病历进行质控。\n"
                f"检查级别: {level_desc.get(check_level, level_desc['standard'])}\n"
                f"已知过敏: {allergies if allergies else '无记录'}\n\n"
                "检查维度:\n"
                "🔴 错误级: 主诉-诊断矛盾、时间逻辑错误、过敏药禁忌、诊断缺证据\n"
                "🟡 警告级: 缺少关键阴性、家族史/过敏史缺失、查体不完整、用药缺剂量\n"
                "🟢 建议级: 叙事结构不完整、可补充的鉴别诊断\n\n"
                "输出格式: 质控得分(0-100) + 分级问题列表(每项含: level, field, description, suggestion)\n"
                "对缺失字段提供模板化补全草稿。\n"
                "涉及诊断判断时标注「以临床医生判断为准」。\n\n"
                f"结构化病历:\n{json.dumps(structured_record, ensure_ascii=False, indent=2)[:6000]}"
        )

    def do_suggest_icd_codes(self, args, response):
        """为诊断和操作推荐 ICD 编码"""
        diagnoses = args.get('diagnoses', [])
        procedures = args.get('procedures', [])
        icd_version = args.get('icd_version', 'ICD-10')
        yield f"[Action] ICD coding ({icd_version}): {len(diagnoses)} diagnoses, {len(procedures)} procedures\n"

        if not diagnoses:
            return StepOutcome(
                {"status": "error", "msg": "请提供至少一个诊断。可先用 extract_medical_record 从病历中提取。"},
                next_prompt=self._get_anchor_prompt()
            )

        return StepOutcome(
            data={"diagnoses": diagnoses, "procedures": procedures, "icd_version": icd_version},
            next_prompt=self._get_anchor_prompt() +
                f"\n[ICD编码] 请按 icd_coding_sop 为以下诊断/操作推荐 {icd_version} 编码。\n\n"
                f"主诊断: {diagnoses[0]}\n"
                + (f"其他诊断: {', '.join(diagnoses[1:])}\n" if len(diagnoses) > 1 else "")
                + (f"手术/操作: {', '.join(procedures)}\n" if procedures else "")
                + "\n对每个诊断:\n"
                "1. 给出前3个候选编码 + 中文描述\n"
                "2. 标注置信度(高/中/低)\n"
                "3. 低置信度时请用 web_search 确认（搜索 \"ICD-10 [诊断名] 编码\"）\n"
                "4. 说明编码选择的依据\n"
                "5. 如果诊断表述不够具体，建议更精确的诊断描述\n\n"
                "编码仅为辅助建议，最终以编码员/医师审定为准。"
        )

    def do_validate_icd_combination(self, args, response):
        """检查 ICD 编码组合的规则合规性"""
        main_code = args.get('main_diagnosis_code', '')
        other_codes = args.get('other_codes', [])
        procedure_codes = args.get('procedure_codes', [])
        yield f"[Action] Validating ICD combination: main={main_code}, others={len(other_codes)}\n"

        if not main_code:
            return StepOutcome(
                {"status": "error", "msg": "请提供主诊断编码。"},
                next_prompt=self._get_anchor_prompt()
            )

        all_codes = [main_code] + other_codes
        return StepOutcome(
            data={"main": main_code, "others": other_codes, "procedures": procedure_codes},
            next_prompt=self._get_anchor_prompt() +
                f"\n[编码核验] 请检查以下ICD编码组合是否合规:\n"
                f"主诊断: {main_code}\n"
                f"其他诊断: {', '.join(other_codes) if other_codes else '无'}\n"
                f"手术操作: {', '.join(procedure_codes) if procedure_codes else '无'}\n\n"
                "检查项:\n"
                "1. 主诊断选择是否合理（消耗资源最多/危害最大）\n"
                "2. 是否应使用合并编码（如糖尿病+并发症→E11.x）\n"
                "3. 有无互斥的排除码\n"
                "4. 手术操作与诊断是否一致\n"
                "5. 编码是否足够具体（能否编到更细的亚目）\n\n"
                "输出: 每项检查的通过/不通过 + 修正建议。"
        )

    # ================================================================
    #  证据分级 / 合规审查（能力域 9/10/11）
    # ================================================================

    def _get_evidence_citation_level(self):
        """从 config 读取当前证据引用档位"""
        try:
            from config import MEMORY_CONFIG
            return MEMORY_CONFIG.get("evidence_citation_level", "standard")
        except ImportError:
            return "standard"

    def do_check_pathway_compliance(self, args, response):
        """临床路径偏差检查 + 医保预审"""
        diagnoses = args.get('diagnoses', [])
        treatment_plan = args.get('treatment_plan', {})
        check_type = args.get('check_type', 'both')
        pathway_version = args.get('pathway_version', '')
        yield f"[Action] Pathway compliance check (type={check_type})\n"

        if not diagnoses:
            return StepOutcome(
                {"status": "error", "msg": "请提供至少一个诊断。"},
                next_prompt=self._get_anchor_prompt()
            )

        profile = self.health_store.load_profile()
        meds = self.health_store.load_medications()
        active_meds = [m.get('drug_name') for m in meds if m.get('active', True)]

        context = {
            "diagnoses": diagnoses,
            "treatment_plan": treatment_plan,
            "check_type": check_type,
            "pathway_version": pathway_version,
            "insurance_type": profile.get('basic_info', {}).get('insurance_type', '未知'),
            "current_medications": active_meds,
        }

        yield f"[Context] {len(diagnoses)} diagnoses, check_type={check_type}\n"

        check_instructions = []
        if check_type in ('pathway', 'both'):
            check_instructions.append(
                "**路径偏差检查**: 匹配该诊断的临床路径（优先用内置知识，不确定时 web_search 搜索"
                "「XX病 临床路径 卫健委」），逐项比对住院天数/必做检查/禁做项目/用药规范/手术时机/出院标准。"
            )
        if check_type in ('insurance', 'both'):
            check_instructions.append(
                "**医保预审**: 检查适应症匹配/限定条件/自费项目/大额预警/重复收费。"
            )

        return StepOutcome(
            data=context,
            next_prompt=self._get_anchor_prompt() +
                f"\n[临床路径合规审查] 按 clinical_pathway_compliance_sop + evidence_grading_framework_sop 执行。\n"
                f"使用 strict 证据引用档位。\n"
                f"主诊断: {diagnoses[0]}\n"
                + (f"路径版本: {pathway_version}\n" if pathway_version else "")
                + f"诊疗方案: {json.dumps(treatment_plan, ensure_ascii=False)[:2000]}\n\n"
                + "\n".join(check_instructions) + "\n\n"
                "每个偏差/风险项输出: 偏差描述 + 路径/目录要求(原文) + 实际情况 + 📎证据[T?] + 风险等级(🔴/🟡/🟢) + 建议措施。\n"
                "对每条结论调用 record_evidence_citation 记录审计链。\n"
                "搜索时禁止包含患者个人信息。\n"
                "末尾标注「本报告仅为辅助审查，最终以医保部门/路径管理委员会审定为准」。"
        )

    def do_review_compliance_material(self, args, response):
        """合规材料审阅与自动引用"""
        text = args.get('text', '')
        material_type = args.get('material_type', 'academic')
        review_scope = args.get('review_scope', 'full')
        yield f"[Action] Compliance material review (type={material_type}, scope={review_scope}, len={len(text)})\n"

        if not text or len(text) < 30:
            return StepOutcome(
                {"status": "error", "msg": "材料文本过短，请提供完整内容。"},
                next_prompt=self._get_anchor_prompt()
            )

        scope_desc = {
            'full': "全面审阅：医学声明验证 + 引用核查 + 合规性检查",
            'claims_only': "仅审阅医学声明的准确性和证据支撑",
            'references_only': "仅核查引用文献的真实性和匹配度",
        }

        return StepOutcome(
            data={"status": "reviewing", "material_type": material_type,
                  "review_scope": review_scope, "text_length": len(text)},
            next_prompt=self._get_anchor_prompt() +
                f"\n[合规材料审阅] 按 compliance_review_sop + evidence_grading_framework_sop 执行。\n"
                f"使用 strict 证据引用档位。\n"
                f"材料类型: {material_type}\n"
                f"审阅范围: {scope_desc.get(review_scope, scope_desc['full'])}\n\n"
                "步骤:\n"
                "1. 拆解材料，提取所有医学声明和引用标注\n"
                "2. 逐条声明验证：检查引用匹配 + 证据分级(T1-T6) + 合规性\n"
                "   - 超适应症推广/夸大疗效/隐藏风险/过时引用/绝对化措辞\n"
                "   - 低置信度时用 web_search 验证 PMID/DOI\n"
                "3. 每条问题标注: 位置 + 原文 + 问题类型 + 严重程度(🔴/🟡/🟢) + 建议修改\n"
                "4. 自动生成/补全参考文献列表\n"
                "5. 对每条结论调用 record_evidence_citation 记录审计链\n"
                "末尾标注「本审阅仅为辅助，最终以医学事务/法务部门审定为准」。\n\n"
                f"--- 待审阅材料 ---\n{text[:8000]}\n--- 材料结束 ---"
        )

    def do_record_evidence_citation(self, args, response):
        """将证据引用记录到审计链"""
        conclusion = args.get('conclusion', '')
        evidence_tier = args.get('evidence_tier', 'T6')
        source = args.get('source', '')
        snippet = args.get('citation_snippet', '')
        sop_used = args.get('sop_used', '')

        if not conclusion or not source:
            return StepOutcome(
                {"status": "error", "msg": "conclusion 和 source 不能为空。"},
                next_prompt=self._get_anchor_prompt()
            )

        tool_chain = [t.get('tool', '') for t in self.tracker.turn_summaries[-3:]
                      if t.get('tool')]

        self.tracker.record_citation(
            turn=self._current_turn,
            conclusion=conclusion,
            evidence_tier=evidence_tier,
            source=source,
            citation_snippet=snippet,
            tool_chain=tool_chain,
            sop_used=sop_used,
            evidence_level_override=self._get_evidence_citation_level(),
        )

        return StepOutcome(
            data={"status": "recorded", "tier": evidence_tier, "source": source[:80]},
            next_prompt=self._get_anchor_prompt() +
                f"\n[审计记录] 已记录证据引用: [{evidence_tier}] {source[:80]}"
        )

    # ================================================================
    #  影像报告解读（能力域 12）
    # ================================================================

    def do_parse_imaging_report(self, args, response):
        """影像报告结构化解读"""
        report_text = args.get('report_text', '')
        modality = args.get('modality', 'CT')
        yield f"[Action] Parsing imaging report (modality={modality}, len={len(report_text)})\n"

        if not report_text or len(report_text) < 20:
            return StepOutcome(
                {"status": "error", "msg": "报告文本过短或为空，请提供完整的影像检查报告。"},
                next_prompt=self._get_anchor_prompt()
            )

        profile = self.health_store.load_profile()
        chronic = profile.get('chronic_diseases', [])
        allergies = profile.get('allergies', [])
        age = profile.get('basic_info', {}).get('age')

        modality_names = {
            'CT': 'CT', 'MRI': 'MRI（磁共振）', 'US': '超声',
            'XR': 'X光', 'PET': 'PET-CT', 'endoscopy': '内镜',
        }

        context = {
            "modality": modality,
            "text_length": len(report_text),
            "patient_age": age,
            "chronic_diseases": chronic,
        }

        yield f"[Context] modality={modality}, patient chronic={chronic}\n"

        return StepOutcome(
            data=context,
            next_prompt=self._get_anchor_prompt() +
                f"\n[影像报告解读] 按 imaging_report_interpretation_sop 执行。\n"
                f"检查类型: {modality_names.get(modality, modality)}\n"
                + (f"用户已知慢病: {', '.join(chronic)}\n" if chronic else "")
                + (f"用户年龄: {age}岁\n" if age else "")
                + "\n请完成以下步骤:\n"
                "1. 结构化抽取: 检查类型/部位/日期/对比剂/发现列表/结论/建议\n"
                "2. 逐项异常解读:\n"
                "   - 严重程度分级: 🔴紧急 🟠尽快就诊 🟡定期随访 🟢无需处理\n"
                "   - 通俗翻译: 将专业术语翻译为患者能理解的语言\n"
                "   - 引用分级标准（如 Lung-RADS/TI-RADS/BI-RADS/LI-RADS/PI-RADS）\n"
                "3. 综合建议: 建议科室 + 下一步检查 + 随访计划\n"
                "4. 🔴级别发现必须醒目、最先提示，强烈建议就医\n"
                "末尾标注「以上解读仅供参考，具体诊疗请咨询相关科室医生」\n\n"
                f"--- 影像报告 ---\n{report_text[:8000]}\n--- 报告结束 ---"
        )

    def do_compare_imaging_reports(self, args, response):
        """影像报告随访对比"""
        current = args.get('current_report', '')
        prior = args.get('prior_report', '')
        focus = args.get('focus_findings', [])
        yield f"[Action] Comparing imaging reports (current={len(current)}, prior={len(prior)})\n"

        if not current or not prior:
            return StepOutcome(
                {"status": "error", "msg": "请提供当前报告和既往报告。"},
                next_prompt=self._get_anchor_prompt()
            )

        return StepOutcome(
            data={"status": "comparing", "current_len": len(current),
                  "prior_len": len(prior), "focus": focus},
            next_prompt=self._get_anchor_prompt() +
                "\n[影像随访对比] 按 imaging_report_interpretation_sop Step 3 执行。\n"
                + (f"重点关注: {', '.join(focus)}\n" if focus else "")
                + "\n对比维度:\n"
                "1. 大小变化: 增大/缩小/稳定（附数值和百分比）\n"
                "2. 形态变化: 边界/密度/信号/血流\n"
                "3. 新发病灶 + 消失病灶\n"
                "4. 整体趋势: 好转 / 稳定 / 进展\n\n"
                "每个变化标注严重程度(🔴🟠🟡🟢)和建议。\n"
                "末尾标注「以上对比仅供参考，请咨询医生」\n\n"
                f"--- 当前报告 ---\n{current[:5000]}\n--- 当前结束 ---\n\n"
                f"--- 既往报告 ---\n{prior[:5000]}\n--- 既往结束 ---"
        )

    # ================================================================
    #  覆写锚点提示和轮次补丁
    # ================================================================

    def _get_anchor_prompt(self):
        prompt = super()._get_anchor_prompt()

        if self.current_patient and self.current_disease:
            strategy_path = os.path.join(os.path.dirname(__file__),
                                         'memory/L4_episodes/disease_strategy.json')
            if os.path.exists(strategy_path):
                try:
                    with open(strategy_path, 'r', encoding='utf-8') as f:
                        all_strategy = json.load(f)
                    s = all_strategy.get(self.current_disease)
                    if s:
                        prompt += f"\n<strategy_hint disease=\"{self.current_disease}\">\n"
                        prompt += f"基于 {s.get('total_cases',0)} 个历史病例的经验:\n"
                        for tool, util in s.get('tool_utility', {}).items():
                            prompt += (f"  - {tool}: 建议={util.get('recommendation','?')}, "
                                      f"有用率={util.get('usefulness_rate',0):.0%}\n")
                        rec = s.get('recommended_tool_sequence', '')
                        if rec:
                            prompt += f"推荐流程: {rec}\n"
                        prompt += "</strategy_hint>"
                except (json.JSONDecodeError, KeyError):
                    pass

        return prompt

    def next_prompt_patcher(self, next_prompt, outcome, turn):
        next_prompt = super().next_prompt_patcher(next_prompt, outcome, turn)

        new_count = self.episode_writer.count_since_last_distill()
        from config import AGENT_CONFIG
        threshold = AGENT_CONFIG.get("distill_threshold", 20)
        if new_count >= threshold and turn % 5 == 0:
            next_prompt += (
                f"\n[SYSTEM] 已积累 {new_count} 个新病例经验，建议调用 distill_experience 更新策略。"
            )
        return next_prompt
