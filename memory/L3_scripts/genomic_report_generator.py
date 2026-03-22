# genomic_report_generator.py
"""
综合基因组分析报告生成器
整合所有分析模块的结果，输出结构化临床报告
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field

import sys
sys.path.insert(0, str(Path(__file__).parent))
from variant_parser import VariantParser, Variant
from prs_calculator import PRSCalculator, PRSResult
from pathogenicity_classifier import PathogenicityClassifier, ClassificationResult, ACMGClass
from gene_panel_analyzer import GenePanelAnalyzer, GenePanelResult


@dataclass
class GenomicReport:
    """综合基因组分析报告"""
    report_id: str
    generated_at: str
    patient_info: Dict[str, Any]

    # 各模块结果
    panel_results: List[GenePanelResult] = field(default_factory=list)
    prs_results: List[PRSResult] = field(default_factory=list)
    rare_variant_findings: List[Dict] = field(default_factory=list)
    overall_summary: str = ""
    overall_risk_level: str = ""  # HIGH / MODERATE / LOW
    priority_actions: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "report_id": self.report_id,
            "generated_at": self.generated_at,
            "patient": self.patient_info,
            "overall_risk": self.overall_risk_level,
            "overall_summary": self.overall_summary,
            "priority_actions": self.priority_actions,
            "panels": [p.to_dict() for p in self.panel_results],
            "prs": [p.to_dict() for p in self.prs_results],
            "rare_variants": self.rare_variant_findings,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    def to_clinical_text(self) -> str:
        """生成完整临床文本报告"""
        lines = [
            "╔══════════════════════════════════════════════════════╗",
            "║          综合基因组分析报告                          ║",
            "╚══════════════════════════════════════════════════════╝",
            f"报告编号: {self.report_id}",
            f"生成时间: {self.generated_at}",
            "",
        ]

        # 患者信息
        pi = self.patient_info
        lines.append("【患者信息】")
        for k, v in pi.items():
            label_map = {"eid": "ID", "age": "年龄", "sex": "性别",
                        "family_history": "家族史", "disease_context": "疾病背景"}
            label = label_map.get(k, k)
            lines.append(f"  {label}: {v}")
        lines.append("")

        # 综合风险评级
        risk_emoji = {"HIGH": "🔴", "MODERATE": "🟡", "LOW": "🟢"}.get(self.overall_risk_level, "⚪")
        lines.append(f"{'='*55}")
        lines.append(f"  综合遗传风险评级: {risk_emoji} {self.overall_risk_level}")
        lines.append(f"{'='*55}")
        lines.append(f"\n{self.overall_summary}\n")

        # 优先行动项
        if self.priority_actions:
            lines.append("【优先行动项】")
            for i, action in enumerate(self.priority_actions, 1):
                lines.append(f"  {i}. {action}")
            lines.append("")

        # 疾病面板结果
        if self.panel_results:
            lines.append("━" * 55)
            lines.append("一、疾病基因面板分析")
            lines.append("━" * 55)
            for pr in self.panel_results:
                lines.append(pr.clinical_report())
                lines.append("")

        # PRS结果
        if self.prs_results:
            lines.append("━" * 55)
            lines.append("二、多基因风险评分 (PRS)")
            lines.append("━" * 55)
            for prs in self.prs_results:
                lines.append(prs.clinical_summary())
                lines.append("")

        # 罕见变异发现
        if self.rare_variant_findings:
            lines.append("━" * 55)
            lines.append("三、其他罕见变异发现")
            lines.append("━" * 55)
            for rv in self.rare_variant_findings:
                lines.append(f"  • {rv['gene']} {rv.get('variant_id','')}: "
                           f"{rv.get('classification','?')} - {rv.get('consequence','')}")

        # 免责声明
        lines.extend([
            "",
            "─" * 55,
            "【声明】本报告基于计算分析生成，仅供临床参考。",
            "变异致病性分类遵循ACMG/AMP标准框架但需人工复核。",
            "所有临床决策应由遗传咨询师和主治医师共同评估。",
            "─" * 55,
        ])

        return "\n".join(lines)


class GenomicReportGenerator:
    """
    综合基因组报告生成器

    工作流:
    1. 加载/解析变异数据
    2. 运行指定的疾病面板分析
    3. 计算PRS (如提供权重)
    4. 扫描其他罕见致病变异
    5. 综合评估，生成报告
    """

    def __init__(self):
        self.parser = VariantParser()
        self.classifier = PathogenicityClassifier()
        self.panel_analyzer = GenePanelAnalyzer()
        self.prs_calculator = PRSCalculator()

    def generate_report(
        self,
        patient_info: Dict[str, Any],
        variants: Optional[List[Variant]] = None,
        vcf_path: Optional[str] = None,
        panels: Optional[List[str]] = None,
        prs_diseases: Optional[List[str]] = None,
        scan_all_rare: bool = True,
        genotype_data: Optional[Dict[str, int]] = None,
    ) -> GenomicReport:
        """
        生成综合基因组报告

        Args:
            patient_info: 患者基本信息 {eid, age, sex, ...}
            variants: 已解析的变异列表 (与vcf_path二选一)
            vcf_path: VCF文件路径
            panels: 要分析的面板名列表 (None=自动选择)
            prs_diseases: 要计算PRS的疾病列表
            scan_all_rare: 是否扫描所有罕见编码变异
            genotype_data: PRS用的基因型数据 {rsID: dosage}
        """
        # 准备变异数据
        if variants is None and vcf_path:
            self.parser.parse_vcf(vcf_path, patient_info.get("eid"))
            variants = self.parser.variants
        elif variants is None:
            variants = []

        report = GenomicReport(
            report_id=f"GR-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            patient_info=patient_info,
        )

        # 1. 面板分析
        if panels is None:
            panels = self._auto_select_panels(patient_info)

        for panel_name in panels:
            try:
                result = self.panel_analyzer.analyze_from_variants(variants, panel_name)
                report.panel_results.append(result)
            except ValueError:
                pass  # 跳过未知面板

        # 2. PRS计算
        if prs_diseases and genotype_data:
            for disease in prs_diseases:
                try:
                    prs_result = self.prs_calculator.calculate(
                        disease, genotype_data,
                        population=patient_info.get("ancestry", "EUR")
                    )
                    report.prs_results.append(prs_result)
                except ValueError:
                    pass

        # 3. 扫描罕见致病变异(面板外)
        if scan_all_rare and variants:
            panel_genes = set()
            for p in panels:
                panel_genes.update(
                    g.upper() for g in self.panel_analyzer.get_panel_genes(p)
                )
            report.rare_variant_findings = self._scan_rare_variants(
                variants, exclude_genes=panel_genes
            )

        # 4. 综合评估
        self._compute_overall_assessment(report)

        return report

    def _auto_select_panels(self, patient_info: Dict) -> List[str]:
        """根据患者信息自动选择相关面板"""
        context = patient_info.get("disease_context", "").lower()
        panels = []

        mapping = {
            "breast": "hereditary_breast_ovarian",
            "ovarian": "hereditary_breast_ovarian",
            "brca": "hereditary_breast_ovarian",
            "cholesterol": "familial_hypercholesterolemia",
            "fh": "familial_hypercholesterolemia",
            "ldl": "familial_hypercholesterolemia",
            "colon": "lynch_syndrome",
            "colorectal": "lynch_syndrome",
            "lynch": "lynch_syndrome",
            "cardiac": "cardiovascular_genetic",
            "cardiovascular": "cardiovascular_genetic",
            "cad": "cardiovascular_genetic",
            "heart": "cardiovascular_genetic",
            "alzheimer": "alzheimer_risk",
            "dementia": "alzheimer_risk",
        }

        for keyword, panel in mapping.items():
            if keyword in context and panel not in panels:
                panels.append(panel)

        # 默认：至少分析心血管
        if not panels:
            panels = ["cardiovascular_genetic"]

        return panels

    def _scan_rare_variants(self, variants: List[Variant],
                             exclude_genes: set,
                             af_threshold: float = 0.01) -> List[Dict]:
        """扫描面板外的罕见编码变异"""
        findings = []
        for v in variants:
            if v.gene.upper() in exclude_genes:
                continue
            if not v.is_coding:
                continue
            if v.af_global > af_threshold and v.af_global >= 0:
                continue

            features = {
                "gene": v.gene,
                "consequence": v.consequence,
                "af_global": v.af_global,
                "clinvar": v.clinvar_significance,
                "clinvar_stars": v.clinvar_review_stars,
            }
            result = self.classifier.classify(features,
                                              f"{v.chrom}:{v.pos}{v.ref}>{v.alt}")

            if result.classification in (ACMGClass.PATHOGENIC,
                                         ACMGClass.LIKELY_PATHOGENIC,
                                         ACMGClass.VUS):
                findings.append({
                    "gene": v.gene,
                    "variant_id": result.variant_id,
                    "consequence": v.consequence,
                    "classification": result.classification.value,
                    "af": v.af_global,
                })

        # 按致病性排序
        order = {"Pathogenic": 0, "Likely Pathogenic": 1, "VUS": 2}
        findings.sort(key=lambda x: order.get(x["classification"], 9))
        return findings[:20]  # 最多返回20个

    def _compute_overall_assessment(self, report: GenomicReport):
        """综合所有结果计算总体评估"""
        risk_signals = []
        actions = []

        # 面板发现
        for pr in report.panel_results:
            if pr.actionable_findings:
                for af in pr.actionable_findings:
                    risk_signals.append(("HIGH" if af.get("in_high_risk_gene") else "MODERATE",
                                        f"{af['gene']} {af['classification']}"))
                    actions.append(f"[{pr.disease}] {af['gene']} 致病变异 - 建议遗传咨询")

        # PRS
        for prs in report.prs_results:
            if prs.risk_category in ("very_high", "high"):
                risk_signals.append(("MODERATE",
                                    f"{prs.disease} PRS={prs.percentile:.0f}th"))
                actions.append(f"[{prs.disease}] 多基因高风险(第{prs.percentile:.0f}百分位) - 加强筛查")

        # 罕见变异
        for rv in report.rare_variant_findings:
            if rv["classification"] == "Pathogenic":
                risk_signals.append(("MODERATE", f"{rv['gene']} 致病变异(面板外)"))

        # 确定总体风险
        if any(r[0] == "HIGH" for r in risk_signals):
            report.overall_risk_level = "HIGH"
        elif any(r[0] == "MODERATE" for r in risk_signals):
            report.overall_risk_level = "MODERATE"
        else:
            report.overall_risk_level = "LOW"

        # 生成摘要
        if risk_signals:
            details = "; ".join(f"{r[1]}" for r in risk_signals[:5])
            report.overall_summary = (
                f"检出 {len(risk_signals)} 个遗传风险信号: {details}。"
                f"建议结合临床表型和家族史进行综合评估。"
            )
        else:
            report.overall_summary = (
                "未检出已知高外显率致病变异或显著多基因风险。"
                "遗传风险评估为低，但不排除未覆盖基因/区域的变异。"
            )

        report.priority_actions = actions if actions else ["常规健康管理，无需特殊遗传学干预"]

    @classmethod
    def quick_report(cls, patient_info: Dict, variant_dicts: List[Dict],
                     panels: List[str] = None) -> str:
        """
        快速生成报告的便捷接口

        Args:
            patient_info: {eid, age, sex, disease_context, ...}
            variant_dicts: [{gene, consequence, af_global, clinvar, ...}]
            panels: 面板名列表
        Returns:
            临床文本报告字符串
        """
        variants = []
        for vd in variant_dicts:
            v = Variant(
                chrom=vd.get("chrom", ""),
                pos=int(vd.get("pos", 0)),
                ref=vd.get("ref", "N"),
                alt=vd.get("alt", "N"),
                gene=vd.get("gene", ""),
                consequence=vd.get("consequence", ""),
                af_global=float(vd.get("af_global", -1)),
                clinvar_significance=vd.get("clinvar", ""),
                clinvar_review_stars=int(vd.get("clinvar_stars", 0)),
                zygosity=vd.get("zygosity", "het"),
            )
            variants.append(v)

        gen = cls()
        report = gen.generate_report(
            patient_info=patient_info,
            variants=variants,
            panels=panels,
        )
        return report.to_clinical_text()


if __name__ == "__main__":
    # 自检: 模拟一个完整分析流程
    patient = {
        "eid": "TEST001",
        "age": 45,
        "sex": "Female",
        "disease_context": "breast_cancer",
        "family_history": "母亲50岁乳腺癌",
    }
    test_variants = [
        {"gene": "BRCA1", "consequence": "frameshift", "af_global": 0.00002,
         "clinvar": "Pathogenic", "clinvar_stars": 2, "chrom": "chr17", "pos": 43094464},
        {"gene": "ATM", "consequence": "missense", "af_global": 0.003,
         "clinvar": "", "chrom": "chr11", "pos": 108200000},
        {"gene": "LDLR", "consequence": "stop_gained", "af_global": 0.00001,
         "clinvar": "Pathogenic", "clinvar_stars": 3, "chrom": "chr19", "pos": 11200000},
        {"gene": "TP53", "consequence": "synonymous", "af_global": 0.15,
         "chrom": "chr17", "pos": 7600000},
    ]

    text_report = GenomicReportGenerator.quick_report(patient, test_variants)

    # 验证
    assert "BRCA1" in text_report
    assert "HIGH" in text_report or "高" in text_report
    assert "报告编号" in text_report

    print("✅ genomic_report_generator.py 自检通过")
    print(f"  报告长度: {len(text_report)} 字符")
    print("\n--- 报告预览(前30行) ---")
    for line in text_report.split("\n")[:30]:
        print(line)