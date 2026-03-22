# gene_panel_analyzer.py
"""
疾病特异性基因面板批量分析工具
整合 variant_parser + pathogenicity_classifier，按疾病面板一键分析
"""

import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field

# 兄弟模块引用（同目录）
import sys
sys.path.insert(0, str(Path(__file__).parent))
from variant_parser import VariantParser, Variant
from pathogenicity_classifier import PathogenicityClassifier, ACMGClass


@dataclass
class GenePanelResult:
    """基因面板分析结果"""
    panel_name: str
    disease: str
    genes_analyzed: List[str]
    total_variants_found: int
    actionable_findings: List[Dict]    # 致病/可能致病变异
    vus_findings: List[Dict]           # VUS变异
    benign_findings_count: int
    risk_summary: str                  # "高遗传风险" / "中等" / "低/未发现"
    recommendations: List[str]

    def to_dict(self) -> dict:
        return {
            "panel": self.panel_name,
            "disease": self.disease,
            "genes": self.genes_analyzed,
            "total_variants": self.total_variants_found,
            "actionable": self.actionable_findings,
            "vus": self.vus_findings,
            "benign_count": self.benign_findings_count,
            "risk_summary": self.risk_summary,
            "recommendations": self.recommendations,
        }

    def clinical_report(self) -> str:
        lines = [
            f"━━━ 基因面板分析报告 ━━━",
            f"面板: {self.panel_name}",
            f"关联疾病: {self.disease}",
            f"分析基因: {', '.join(self.genes_analyzed)}",
            f"检出变异总数: {self.total_variants_found}",
            f"",
            f"【风险总结】{self.risk_summary}",
            f"",
        ]
        if self.actionable_findings:
            lines.append(f"▸ 临床可操作发现 ({len(self.actionable_findings)}):")
            for f in self.actionable_findings:
                lines.append(f"  • {f['gene']} - {f['variant_id']}: "
                           f"{f['classification']} ({f['consequence']})")
                if f.get('evidence_codes'):
                    lines.append(f"    证据: {', '.join(f['evidence_codes'])}")
        else:
            lines.append("▸ 未发现临床可操作的致病变异")

        if self.vus_findings:
            lines.append(f"\n▸ 意义不明变异 VUS ({len(self.vus_findings)}):")
            for f in self.vus_findings[:5]:  # 最多显示5个
                lines.append(f"  • {f['gene']} - {f['variant_id']}: {f['consequence']}")
            if len(self.vus_findings) > 5:
                lines.append(f"  ... 及另外 {len(self.vus_findings)-5} 个VUS")

        lines.append(f"\n【建议】")
        for r in self.recommendations:
            lines.append(f"  → {r}")

        return "\n".join(lines)


class GenePanelAnalyzer:
    """
    疾病基因面板分析器

    内置多种临床常用面板定义，整合变异解析+致病性分级
    """

    # 内置面板定义: {面板名: {disease, genes, high_risk_genes, follow_up}}
    BUILTIN_PANELS = {
        "hereditary_breast_ovarian": {
            "disease": "遗传性乳腺癌/卵巢癌",
            "genes": ["BRCA1", "BRCA2", "PALB2", "ATM", "CHEK2", "TP53",
                      "PTEN", "CDH1", "STK11", "NF1", "RAD51C", "RAD51D", "BARD1"],
            "high_risk_genes": ["BRCA1", "BRCA2", "PALB2", "TP53"],
            "moderate_risk_genes": ["ATM", "CHEK2", "RAD51C", "RAD51D", "BARD1"],
            "recommendations_if_positive": [
                "建议遗传咨询并讨论风险管理策略",
                "根据NCCN指南调整筛查频率(如乳腺MRI)",
                "评估预防性手术选项",
                "一级亲属建议行级联检测",
            ],
            "recommendations_if_negative": [
                "未检出高外显率致病变异",
                "风险评估应结合家族史和临床因素",
                "考虑多基因风险评分(PRS)作为补充",
            ],
        },
        "familial_hypercholesterolemia": {
            "disease": "家族性高胆固醇血症(FH)",
            "genes": ["LDLR", "APOB", "PCSK9", "LDLRAP1"],
            "high_risk_genes": ["LDLR"],
            "moderate_risk_genes": ["APOB", "PCSK9"],
            "recommendations_if_positive": [
                "确认FH诊断，启动强化降脂治疗",
                "目标LDL-C根据变异类型调整",
                "家系级联筛查（50%一级亲属携带风险）",
                "必要时考虑PCSK9抑制剂",
            ],
            "recommendations_if_negative": [
                "未检出单基因FH致病变异",
                "高LDL-C可能为多基因或继发性原因",
                "继续标准血脂管理",
            ],
        },
        "lynch_syndrome": {
            "disease": "Lynch综合征(遗传性非息肉性结直肠癌)",
            "genes": ["MLH1", "MSH2", "MSH6", "PMS2", "EPCAM"],
            "high_risk_genes": ["MLH1", "MSH2"],
            "moderate_risk_genes": ["MSH6", "PMS2"],
            "recommendations_if_positive": [
                "确认Lynch综合征诊断",
                "制定终身癌症监测计划(结肠镜/妇科等)",
                "一级亲属级联检测",
                "考虑预防性手术(视具体基因)",
            ],
            "recommendations_if_negative": [
                "未检出MMR基因致病变异",
                "如高度怀疑，考虑肿瘤组织MMR/MSI检测",
            ],
        },
        "cardiovascular_genetic": {
            "disease": "遗传性心血管病",
            "genes": ["LDLR", "APOB", "PCSK9", "LPA", "MYBPC3", "MYH7",
                      "SCN5A", "KCNQ1", "KCNH2", "LMNA", "RYR2"],
            "high_risk_genes": ["LDLR", "MYBPC3", "MYH7", "SCN5A"],
            "moderate_risk_genes": ["KCNQ1", "KCNH2", "LMNA"],
            "recommendations_if_positive": [
                "根据具体基因制定监测和治疗方案",
                "心脏影像评估(心超/心脏MRI)",
                "家系级联检测",
                "部分基因型可能需要ICD评估",
            ],
            "recommendations_if_negative": [
                "未检出已知心血管遗传病致病变异",
                "不排除表观遗传或未知基因变异",
            ],
        },
        "alzheimer_risk": {
            "disease": "阿尔茨海默病遗传风险",
            "genes": ["APOE", "TREM2", "SORL1", "ABCA7", "APP", "PSEN1", "PSEN2"],
            "high_risk_genes": ["APP", "PSEN1", "PSEN2"],
            "moderate_risk_genes": ["APOE", "TREM2", "SORL1"],
            "recommendations_if_positive": [
                "遗传咨询（注意心理影响）",
                "加强认知功能监测",
                "关注可改变的风险因素(运动/饮食/社交等)",
                "考虑参与临床试验",
            ],
            "recommendations_if_negative": [
                "未检出已知致病/高风险变异",
                "散发性AD占大多数，多基因+环境共同作用",
            ],
        },
    }

    def __init__(self):
        self.parser = VariantParser()
        self.classifier = PathogenicityClassifier()

    def analyze_from_variants(self, variants: List[Variant],
                               panel_name: str,
                               custom_panel: Optional[Dict] = None) -> GenePanelResult:
        """
        从已解析的变异列表分析

        Args:
            variants: Variant对象列表
            panel_name: 内置面板名 或 自定义面板名
            custom_panel: 自定义面板定义（同BUILTIN_PANELS格式）
        """
        panel = custom_panel or self.BUILTIN_PANELS.get(panel_name)
        if not panel:
            available = list(self.BUILTIN_PANELS.keys())
            raise ValueError(f"未知面板: {panel_name}。可用面板: {available}")

        genes = panel["genes"]
        high_risk_genes = set(panel.get("high_risk_genes", []))

        # 按基因过滤变异
        gene_set = {g.upper() for g in genes}
        panel_variants = [v for v in variants if v.gene.upper() in gene_set]

        # 对每个编码变异做致病性分级
        actionable = []
        vus_list = []
        benign_count = 0

        for v in panel_variants:
            if not v.is_coding:
                continue

            features = {
                "gene": v.gene,
                "consequence": v.consequence,
                "af_global": v.af_global,
                "clinvar": v.clinvar_significance,
                "clinvar_stars": v.clinvar_review_stars,
                "lof_known_mechanism": v.gene.upper() in PathogenicityClassifier.LOF_GENES,
            }
            result = self.classifier.classify(features,
                                              variant_id=f"{v.chrom}:{v.pos}{v.ref}>{v.alt}")

            finding = {
                "gene": v.gene,
                "variant_id": result.variant_id,
                "consequence": v.consequence,
                "classification": result.classification.value,
                "evidence_codes": [e.code for e in result.evidence_met],
                "zygosity": v.zygosity,
                "af": v.af_global,
                "in_high_risk_gene": v.gene.upper() in high_risk_genes,
            }

            if result.classification in (ACMGClass.PATHOGENIC, ACMGClass.LIKELY_PATHOGENIC):
                actionable.append(finding)
            elif result.classification == ACMGClass.VUS:
                vus_list.append(finding)
            else:
                benign_count += 1

        # 风险总结
        risk = self._summarize_risk(actionable, high_risk_genes)

        # 建议
        if actionable:
            recs = panel.get("recommendations_if_positive", ["建议遗传咨询"])
        else:
            recs = panel.get("recommendations_if_negative", ["未发现致病变异"])
        if vus_list:
            recs.append(f"发现{len(vus_list)}个VUS，可关注后续重分类更新")

        return GenePanelResult(
            panel_name=panel_name,
            disease=panel["disease"],
            genes_analyzed=genes,
            total_variants_found=len(panel_variants),
            actionable_findings=actionable,
            vus_findings=vus_list,
            benign_findings_count=benign_count,
            risk_summary=risk,
            recommendations=recs,
        )

    def analyze_from_vcf(self, vcf_path: str, panel_name: str,
                          sample_id: str = None,
                          custom_panel: Dict = None) -> GenePanelResult:
        """从VCF文件直接分析"""
        self.parser.parse_vcf(vcf_path, sample_id)
        return self.analyze_from_variants(self.parser.variants, panel_name, custom_panel)

    def list_panels(self) -> Dict[str, str]:
        """列出所有可用面板"""
        return {name: p["disease"] for name, p in self.BUILTIN_PANELS.items()}

    def get_panel_genes(self, panel_name: str) -> List[str]:
        """获取面板包含的基因列表"""
        panel = self.BUILTIN_PANELS.get(panel_name)
        return panel["genes"] if panel else []

    @staticmethod
    def _summarize_risk(actionable: List[Dict], high_risk_genes: set) -> str:
        if not actionable:
            return "低遗传风险：未发现致病性变异"

        high_risk_hits = [f for f in actionable if f.get("in_high_risk_gene")]
        if high_risk_hits:
            genes_hit = set(f["gene"] for f in high_risk_hits)
            return f"高遗传风险：在高外显率基因 {', '.join(genes_hit)} 中发现致病变异"

        genes_hit = set(f["gene"] for f in actionable)
        return f"中等遗传风险：在 {', '.join(genes_hit)} 中发现致病变异"

    @classmethod
    def quick_panel_check(cls, variants_data: List[Dict], panel_name: str) -> Dict:
        """
        快速面板分析便捷接口
        variants_data: [{gene, consequence, af_global, clinvar, ...}]
        """
        # 构造Variant对象
        variants = []
        for vd in variants_data:
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

        analyzer = cls()
        result = analyzer.analyze_from_variants(variants, panel_name)
        return result.to_dict()


if __name__ == "__main__":
    # 自检: 模拟乳腺癌面板分析
    test_variants = [
        {"gene": "BRCA1", "consequence": "frameshift", "af_global": 0.00002,
         "clinvar": "Pathogenic", "clinvar_stars": 2, "chrom": "chr17", "pos": 43094464},
        {"gene": "ATM", "consequence": "missense", "af_global": 0.003,
         "clinvar": "", "chrom": "chr11", "pos": 108200000},
        {"gene": "CHEK2", "consequence": "synonymous", "af_global": 0.12,
         "chrom": "chr22", "pos": 28700000},
    ]
    result = GenePanelAnalyzer.quick_panel_check(test_variants, "hereditary_breast_ovarian")
    assert len(result["actionable"]) >= 1, "应至少检出BRCA1 frameshift为致病"
    assert "高遗传风险" in result["risk_summary"]

    # 列出所有面板
    analyzer = GenePanelAnalyzer()
    panels = analyzer.list_panels()

    print("✅ gene_panel_analyzer.py 自检通过")
    print(f"  内置面板: {len(panels)} 个")
    for name, disease in panels.items():
        genes = analyzer.get_panel_genes(name)
        print(f"    • {name}: {disease} ({len(genes)}基因)")
    print(f"  致病发现: {result['actionable'][0]['gene']} - {result['actionable'][0]['classification']}")