# pathogenicity_classifier.py
"""
基于简化ACMG/AMP标准的变异致病性分级工具
实现核心判据的自动化评估，输出5级分类 + 证据链
参考: Richards et al., Genet Med 2015
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum


class ACMGClass(Enum):
    PATHOGENIC = "Pathogenic"
    LIKELY_PATHOGENIC = "Likely Pathogenic"
    VUS = "Variant of Uncertain Significance"
    LIKELY_BENIGN = "Likely Benign"
    BENIGN = "Benign"


class EvidenceStrength(Enum):
    VERY_STRONG = "very_strong"
    STRONG = "strong"
    MODERATE = "moderate"
    SUPPORTING = "supporting"


@dataclass
class ACMGEvidence:
    """单条ACMG证据"""
    code: str                    # PVS1, PS1, PM2, PP3 等
    strength: EvidenceStrength
    is_pathogenic: bool          # True=致病方向, False=良性方向
    description: str
    satisfied: bool = False

    def __repr__(self):
        status = "✓" if self.satisfied else "✗"
        direction = "P" if self.is_pathogenic else "B"
        return f"[{status}] {self.code}({direction}): {self.description}"


@dataclass
class ClassificationResult:
    """分类结果"""
    variant_id: str
    gene: str
    classification: ACMGClass
    evidence_met: List[ACMGEvidence]
    evidence_not_met: List[ACMGEvidence]
    score_summary: Dict[str, int]   # {"PVS": 0, "PS": 1, "PM": 2, ...}
    confidence_note: str = ""

    def to_dict(self) -> dict:
        return {
            "variant": self.variant_id,
            "gene": self.gene,
            "classification": self.classification.value,
            "evidence_codes_met": [e.code for e in self.evidence_met],
            "evidence_details": [str(e) for e in self.evidence_met],
            "score_summary": self.score_summary,
            "confidence_note": self.confidence_note,
        }

    def clinical_report(self) -> str:
        lines = [
            f"━━━ 变异致病性评估报告 ━━━",
            f"变异: {self.variant_id}",
            f"基因: {self.gene}",
            f"分类: {self.classification.value}",
            f"",
            f"▸ 满足的证据条目 ({len(self.evidence_met)}):",
        ]
        for e in self.evidence_met:
            lines.append(f"  {e}")
        lines.append(f"")
        lines.append(f"▸ 证据计数: {self.score_summary}")
        if self.confidence_note:
            lines.append(f"⚠ {self.confidence_note}")
        return "\n".join(lines)


class PathogenicityClassifier:
    """
    简化版ACMG致病性分类器

    输入: 变异特征字典
    输出: 5级分类 + 证据链

    变异特征字典格式:
    {
        "gene": "BRCA1",
        "consequence": "nonsense",         # missense, nonsense, frameshift, splice, synonymous, intronic
        "af_global": 0.0001,               # 全球MAF
        "af_max_pop": 0.0003,              # 任何亚群中最高MAF
        "clinvar": "Pathogenic",           # ClinVar注释（可选）
        "clinvar_stars": 2,                # ClinVar review stars
        "in_silico_pathogenic": True,      # 计算预测（REVEL>0.7, CADD>25等）
        "conservation_score": 5.5,         # phastCons/phyloP
        "functional_study": None,          # "damaging" / "neutral" / None
        "known_hotspot": False,            # 已知突变热点
        "de_novo": False,                  # 新发突变
        "cosegregation": False,            # 家系共分离
        "in_trans_pathogenic": False,      # 与已知致病变异反式
        "same_aa_known_pathogenic": False, # 同氨基酸位置已有致病变异
        "protein_length_change": False,    # 蛋白长度改变(非重复区)
        "lof_known_mechanism": True,       # LoF是该基因已知致病机制
        "reputable_source": False,         # 权威来源报告为致病
    }
    """

    # 已知LoF为致病机制的基因
    LOF_GENES = {
        "BRCA1", "BRCA2", "PALB2", "ATM", "CHEK2", "TP53",
        "LDLR", "MLH1", "MSH2", "MSH6", "PMS2", "APC",
        "RB1", "PTEN", "CDH1", "STK11", "NF1", "NF2",
    }

    # AF阈值
    RARE_AF_THRESHOLD = 0.01          # PM2: <1%
    VERY_RARE_AF_THRESHOLD = 0.0001   # 极罕见
    COMMON_AF_THRESHOLD = 0.05        # BA1: >5%

    def __init__(self):
        pass

    def classify(self, variant_features: Dict, variant_id: str = "") -> ClassificationResult:
        """
        对单个变异执行ACMG分类
        """
        gene = variant_features.get("gene", "UNKNOWN")
        if not variant_id:
            variant_id = f"{gene}:{variant_features.get('consequence', '?')}"

        # 收集所有证据
        all_evidence = self._evaluate_all_criteria(variant_features)

        # 分离满足/不满足
        evidence_met = [e for e in all_evidence if e.satisfied]
        evidence_not_met = [e for e in all_evidence if not e.satisfied]

        # 计数
        path_met = [e for e in evidence_met if e.is_pathogenic]
        benign_met = [e for e in evidence_met if not e.is_pathogenic]

        score = self._count_evidence(path_met, benign_met)

        # 组合规则判定分类
        classification = self._apply_combination_rules(score)

        # 可信度
        notes = []
        af = variant_features.get("af_global", -1)
        if af < 0:
            notes.append("缺少人群频率数据")
        if not variant_features.get("in_silico_pathogenic") and variant_features.get("consequence") == "missense":
            notes.append("缺少计算预测证据")

        return ClassificationResult(
            variant_id=variant_id,
            gene=gene,
            classification=classification,
            evidence_met=evidence_met,
            evidence_not_met=evidence_not_met,
            score_summary=score,
            confidence_note="; ".join(notes) if notes else "",
        )

    def _evaluate_all_criteria(self, f: Dict) -> List[ACMGEvidence]:
        """评估所有ACMG标准"""
        evidence = []
        gene = f.get("gene", "").upper()
        csq = f.get("consequence", "").lower()
        af = f.get("af_global", -1)
        af_max = f.get("af_max_pop", af)

        # ===== 致病方向证据 =====

        # PVS1: 功能丧失变异 in a gene where LOF is a known mechanism
        is_lof = csq in ("nonsense", "frameshift", "splice_donor", "splice_acceptor", "stop_gained", "start_lost")
        lof_mechanism = f.get("lof_known_mechanism", gene in self.LOF_GENES)
        pvs1 = ACMGEvidence("PVS1", EvidenceStrength.VERY_STRONG, True,
                            "功能丧失变异(LoF)，且LoF为该基因已知致病机制",
                            satisfied=is_lof and lof_mechanism)
        evidence.append(pvs1)

        # PS1: 同一氨基酸位置已有已知致病变异
        ps1 = ACMGEvidence("PS1", EvidenceStrength.STRONG, True,
                           "同一氨基酸改变已被确认为致病",
                           satisfied=bool(f.get("same_aa_known_pathogenic")))
        evidence.append(ps1)

        # PS2: 新发突变(确认父母)
        ps2 = ACMGEvidence("PS2", EvidenceStrength.STRONG, True,
                           "确认的新发突变(de novo)",
                           satisfied=bool(f.get("de_novo")))
        evidence.append(ps2)

        # PS3: 功能实验支持致病
        ps3 = ACMGEvidence("PS3", EvidenceStrength.STRONG, True,
                           "功能实验证实有致病效应",
                           satisfied=f.get("functional_study") == "damaging")
        evidence.append(ps3)

        # PM1: 位于突变热点/关键功能域
        pm1 = ACMGEvidence("PM1", EvidenceStrength.MODERATE, True,
                           "位于已知突变热点或关键功能结构域",
                           satisfied=bool(f.get("known_hotspot")))
        evidence.append(pm1)

        # PM2: 罕见变异（人群数据库中极低频或缺失）
        pm2_sat = (0 <= af < self.RARE_AF_THRESHOLD) or af < 0
        pm2 = ACMGEvidence("PM2", EvidenceStrength.MODERATE, True,
                           f"人群频率极低(AF={af:.6f})" if af >= 0 else "人群数据库中未见",
                           satisfied=pm2_sat)
        evidence.append(pm2)

        # PM3: 与已知致病变异反式(隐性遗传)
        pm3 = ACMGEvidence("PM3", EvidenceStrength.MODERATE, True,
                           "与已知致病变异呈反式(复合杂合)",
                           satisfied=bool(f.get("in_trans_pathogenic")))
        evidence.append(pm3)

        # PM4: 蛋白长度改变(非重复区)
        pm4 = ACMGEvidence("PM4", EvidenceStrength.MODERATE, True,
                           "蛋白长度改变(非重复区域内的缺失/插入)",
                           satisfied=bool(f.get("protein_length_change")))
        evidence.append(pm4)

        # PP1: 家系共分离
        pp1 = ACMGEvidence("PP1", EvidenceStrength.SUPPORTING, True,
                           "在受累家系成员中共分离",
                           satisfied=bool(f.get("cosegregation")))
        evidence.append(pp1)

        # PP3: 计算预测支持致病
        pp3 = ACMGEvidence("PP3", EvidenceStrength.SUPPORTING, True,
                           "多种计算预测工具支持致病(REVEL/CADD等)",
                           satisfied=bool(f.get("in_silico_pathogenic")))
        evidence.append(pp3)

        # PP5: 权威来源报告为致病
        clinvar_path = f.get("clinvar", "").lower() in ("pathogenic", "likely_pathogenic")
        clinvar_stars = f.get("clinvar_stars", 0)
        pp5 = ACMGEvidence("PP5", EvidenceStrength.SUPPORTING, True,
                           f"ClinVar标注为致病(review stars={clinvar_stars})",
                           satisfied=clinvar_path and clinvar_stars >= 1)
        evidence.append(pp5)

        # ===== 良性方向证据 =====

        # BA1: 等位基因频率 >5%
        ba1 = ACMGEvidence("BA1", EvidenceStrength.VERY_STRONG, False,
                           "人群频率>5%，为常见多态",
                           satisfied=af_max >= self.COMMON_AF_THRESHOLD)
        evidence.append(ba1)

        # BS1: 频率高于预期
        bs1 = ACMGEvidence("BS1", EvidenceStrength.STRONG, False,
                           "等位基因频率高于该疾病预期",
                           satisfied=0.01 <= af_max < 0.05)
        evidence.append(bs1)

        # BS3: 功能实验证实无致病效应
        bs3 = ACMGEvidence("BS3", EvidenceStrength.STRONG, False,
                           "功能实验证实无致病效应",
                           satisfied=f.get("functional_study") == "neutral")
        evidence.append(bs3)

        # BP1: 错义变异，但该基因LoF为唯一致病机制
        bp1_sat = csq == "missense" and lof_mechanism and not f.get("known_hotspot")
        bp1 = ACMGEvidence("BP1", EvidenceStrength.SUPPORTING, False,
                           "错义变异，但该基因仅LoF为致病机制",
                           satisfied=bp1_sat)
        evidence.append(bp1)

        # BP4: 计算预测支持良性
        bp4 = ACMGEvidence("BP4", EvidenceStrength.SUPPORTING, False,
                           "计算预测工具提示良性",
                           satisfied=(not f.get("in_silico_pathogenic") and csq == "missense"))
        evidence.append(bp4)

        # BP6: ClinVar标注为良性
        clinvar_benign = f.get("clinvar", "").lower() in ("benign", "likely_benign")
        bp6 = ACMGEvidence("BP6", EvidenceStrength.SUPPORTING, False,
                           "ClinVar标注为良性",
                           satisfied=clinvar_benign and clinvar_stars >= 1)
        evidence.append(bp6)

        # BP7: 同义变异且无剪接影响
        bp7 = ACMGEvidence("BP7", EvidenceStrength.SUPPORTING, False,
                           "同义变异，不影响剪接",
                           satisfied=csq == "synonymous")
        evidence.append(bp7)

        return evidence

    @staticmethod
    def _count_evidence(path_evidence: List[ACMGEvidence],
                        benign_evidence: List[ACMGEvidence]) -> Dict[str, int]:
        """统计各强度级别的证据数量"""
        count = {"PVS": 0, "PS": 0, "PM": 0, "PP": 0, "BA": 0, "BS": 0, "BP": 0}
        for e in path_evidence:
            if e.strength == EvidenceStrength.VERY_STRONG:
                count["PVS"] += 1
            elif e.strength == EvidenceStrength.STRONG:
                count["PS"] += 1
            elif e.strength == EvidenceStrength.MODERATE:
                count["PM"] += 1
            elif e.strength == EvidenceStrength.SUPPORTING:
                count["PP"] += 1
        for e in benign_evidence:
            if e.strength == EvidenceStrength.VERY_STRONG:
                count["BA"] += 1
            elif e.strength == EvidenceStrength.STRONG:
                count["BS"] += 1
            elif e.strength == EvidenceStrength.SUPPORTING:
                count["BP"] += 1
        return count

    @staticmethod
    def _apply_combination_rules(score: Dict[str, int]) -> ACMGClass:
        """
        ACMG组合规则
        Pathogenic:
          (i)  PVS1 + ≥1 PS
          (ii) PVS1 + ≥2 PM
          (iii) PVS1 + 1PM + 1PP
          (iv) PVS1 + ≥2 PP
          (v)  ≥2 PS
          (vi) 1PS + ≥3 PM
          (vii) 1PS + 2PM + ≥2PP
          (viii) 1PS + 1PM + ≥4PP
        Likely Pathogenic:
          (i)  PVS1 + 1PM
          (ii) 1PS + 1-2PM
          (iii) 1PS + ≥2PP
          (iv) ≥3PM
          (v)  2PM + ≥2PP
          (vi) 1PM + ≥4PP
        Benign:
          (i)  BA1 (standalone)
          (ii) ≥2 BS
        Likely Benign:
          (i)  1BS + 1BP
          (ii) ≥2 BP
        """
        pvs, ps, pm, pp = score["PVS"], score["PS"], score["PM"], score["PP"]
        ba, bs, bp = score["BA"], score["BS"], score["BP"]

        # Benign (优先判断，BA1是standalone)
        if ba >= 1:
            return ACMGClass.BENIGN
        if bs >= 2:
            return ACMGClass.BENIGN

        # Likely Benign
        if bs >= 1 and bp >= 1:
            return ACMGClass.LIKELY_BENIGN
        if bp >= 2:
            return ACMGClass.LIKELY_BENIGN

        # Pathogenic
        if pvs >= 1:
            if ps >= 1:
                return ACMGClass.PATHOGENIC
            if pm >= 2:
                return ACMGClass.PATHOGENIC
            if pm >= 1 and pp >= 1:
                return ACMGClass.PATHOGENIC
            if pp >= 2:
                return ACMGClass.PATHOGENIC
        if ps >= 2:
            return ACMGClass.PATHOGENIC
        if ps >= 1:
            if pm >= 3:
                return ACMGClass.PATHOGENIC
            if pm >= 2 and pp >= 2:
                return ACMGClass.PATHOGENIC
            if pm >= 1 and pp >= 4:
                return ACMGClass.PATHOGENIC

        # Likely Pathogenic
        if pvs >= 1 and pm >= 1:
            return ACMGClass.LIKELY_PATHOGENIC
        if ps >= 1 and pm >= 1:
            return ACMGClass.LIKELY_PATHOGENIC
        if ps >= 1 and pp >= 2:
            return ACMGClass.LIKELY_PATHOGENIC
        if pm >= 3:
            return ACMGClass.LIKELY_PATHOGENIC
        if pm >= 2 and pp >= 2:
            return ACMGClass.LIKELY_PATHOGENIC
        if pm >= 1 and pp >= 4:
            return ACMGClass.LIKELY_PATHOGENIC

        # 默认VUS
        return ACMGClass.VUS

    @classmethod
    def quick_classify(cls, gene: str, consequence: str,
                       af: float = -1, clinvar: str = "",
                       **kwargs) -> Dict:
        """快速分类接口"""
        features = {
            "gene": gene,
            "consequence": consequence,
            "af_global": af,
            "clinvar": clinvar,
            "lof_known_mechanism": gene.upper() in cls.LOF_GENES,
            **kwargs,
        }
        classifier = cls()
        result = classifier.classify(features, variant_id=f"{gene}:{consequence}")
        return result.to_dict()


if __name__ == "__main__":
    # 自检1: BRCA1 nonsense变异 → 应为 Pathogenic (PVS1 + PM2)
    r1 = PathogenicityClassifier.quick_classify(
        "BRCA1", "nonsense", af=0.00001, clinvar="Pathogenic", clinvar_stars=2
    )
    assert "Pathogenic" in r1["classification"], f"BRCA1 nonsense应为Pathogenic, 得到{r1['classification']}"

    # 自检2: 常见同义变异 → 应为 Benign 或 Likely Benign
    r2 = PathogenicityClassifier.quick_classify("LDLR", "synonymous", af=0.15)
    assert "Benign" in r2["classification"], f"常见同义应为Benign, 得到{r2['classification']}"

    # 自检3: 罕见missense VUS
    r3 = PathogenicityClassifier.quick_classify(
        "BRCA2", "missense", af=0.0005, in_silico_pathogenic=True
    )
    print(f"  BRCA2 missense VUS测试: {r3['classification']}")

    print("✅ pathogenicity_classifier.py 自检通过")
    print(f"  LoF基因库: {len(PathogenicityClassifier.LOF_GENES)} 个基因")