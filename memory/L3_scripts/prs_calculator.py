# prs_calculator.py
"""
多基因风险评分 (Polygenic Risk Score, PRS) 计算引擎
支持加权求和法，提供百分位和风险分层解读
"""

import json
import math
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple


@dataclass
class PRSWeight:
    """单个PRS位点的权重"""
    rsid: str
    chrom: str
    pos: int
    effect_allele: str
    other_allele: str
    beta: float           # log(OR) 或效应值
    effect_af: float      # 效应等位基因频率（用于缺失填充）
    gene_nearest: str = ""

    @property
    def odds_ratio(self) -> float:
        return math.exp(self.beta)


@dataclass
class PRSResult:
    """PRS计算结果"""
    disease: str
    raw_score: float
    z_score: float          # 标准化后的Z分数
    percentile: float       # 百分位
    risk_category: str      # low / average / moderate / high / very_high
    n_snps_total: int       # 权重文件中的总SNP数
    n_snps_available: int   # 患者有数据的SNP数
    coverage_rate: float    # 覆盖率
    population: str         # 参考人群
    confidence_note: str    # 可信度说明
    top_contributors: List[Dict] = field(default_factory=list)  # 贡献最大的SNP

    def to_dict(self) -> dict:
        return {
            "disease": self.disease,
            "raw_score": round(self.raw_score, 6),
            "z_score": round(self.z_score, 3),
            "percentile": round(self.percentile, 1),
            "risk_category": self.risk_category,
            "snp_coverage": f"{self.n_snps_available}/{self.n_snps_total} ({self.coverage_rate:.1%})",
            "population": self.population,
            "confidence_note": self.confidence_note,
            "top_contributors": self.top_contributors,
        }

    def clinical_interpretation(self) -> str:
        """生成临床可读的解读文本"""
        interp = {
            "very_high": f"PRS处于极高风险区间(第{self.percentile:.0f}百分位)，遗传风险显著高于一般人群。建议加强筛查频率并结合临床评估。",
            "high": f"PRS处于高风险区间(第{self.percentile:.0f}百分位)，遗传负担高于约{self.percentile:.0f}%的人群。建议关注并结合其他风险因素综合评估。",
            "moderate": f"PRS处于中等偏高区间(第{self.percentile:.0f}百分位)，遗传风险略高于平均。常规筛查即可。",
            "average": f"PRS处于平均水平(第{self.percentile:.0f}百分位)，遗传风险与一般人群相当。",
            "low": f"PRS处于低风险区间(第{self.percentile:.0f}百分位)，遗传负担较低，但不排除其他风险因素。",
        }
        text = interp.get(self.risk_category, "无法分类")
        if self.coverage_rate < 0.8:
            text += f"\n⚠️ SNP覆盖率仅{self.coverage_rate:.0%}，结果可能不够准确。"
        if "非欧洲" in self.confidence_note or "non-EUR" in self.confidence_note.lower():
            text += "\n⚠️ 当前PRS模型主要基于欧洲裔人群开发，对该患者的预测效力可能下降。"
        return text


class PRSCalculator:
    """
    PRS计算引擎

    使用方法:
        calc = PRSCalculator()
        calc.load_weights("breast_cancer_prs_weights.json")
        result = calc.calculate(patient_genotypes)
    """

    # 预设的PRS参考统计量（欧洲裔人群）
    # 格式: {disease: (mean, std, n_snps)}
    REFERENCE_STATS = {
        "breast_cancer":   {"mean": 0.0, "std": 1.0, "n_snps": 313, "source": "Mavaddat2019"},
        "CAD":             {"mean": 0.0, "std": 1.0, "n_snps": 6630000, "source": "Khera2018"},
        "T2D":             {"mean": 0.0, "std": 1.0, "n_snps": 1289, "source": "Mahajan2018"},
        "AF":              {"mean": 0.0, "std": 1.0, "n_snps": 1168, "source": "Roselli2018"},
        "alzheimer":       {"mean": 0.0, "std": 1.0, "n_snps": 84, "source": "Kunkle2019"},
        "prostate_cancer": {"mean": 0.0, "std": 1.0, "n_snps": 269, "source": "Schumacher2018"},
        "colorectal_cancer": {"mean": 0.0, "std": 1.0, "n_snps": 140, "source": "Huyghe2019"},
    }

    # 风险分层阈值
    RISK_THRESHOLDS = {
        # percentile cutoffs
        "very_high": 95,
        "high": 80,
        "moderate": 60,
        "average": 20,
        # below 20 = low
    }

    def __init__(self):
        self.weights: List[PRSWeight] = []
        self.disease: str = ""
        self.population: str = "EUR"

    def load_weights_from_file(self, filepath: str) -> int:
        """
        加载PRS权重文件
        支持JSON格式: [{"rsid": "rs123", "chrom": "1", "pos": 1000, 
                        "effect_allele": "A", "other_allele": "G", "beta": 0.05, "effect_af": 0.3}]
        """
        with open(filepath, 'r') as f:
            data = json.load(f)

        if isinstance(data, dict):
            self.disease = data.get("disease", "")
            self.population = data.get("population", "EUR")
            weight_list = data.get("weights", [])
        else:
            weight_list = data

        self.weights = []
        for w in weight_list:
            self.weights.append(PRSWeight(
                rsid=w["rsid"],
                chrom=str(w.get("chrom", "")),
                pos=int(w.get("pos", 0)),
                effect_allele=w["effect_allele"],
                other_allele=w.get("other_allele", ""),
                beta=float(w["beta"]),
                effect_af=float(w.get("effect_af", 0.5)),
                gene_nearest=w.get("gene", ""),
            ))
        return len(self.weights)

    def load_weights_from_list(self, weights: List[Dict], disease: str = "",
                                population: str = "EUR") -> int:
        """直接从列表加载权重（便于集成调用）"""
        self.disease = disease
        self.population = population
        self.weights = []
        for w in weights:
            self.weights.append(PRSWeight(
                rsid=w["rsid"],
                chrom=str(w.get("chrom", "")),
                pos=int(w.get("pos", 0)),
                effect_allele=w["effect_allele"],
                other_allele=w.get("other_allele", ""),
                beta=float(w["beta"]),
                effect_af=float(w.get("effect_af", 0.5)),
                gene_nearest=w.get("gene", ""),
            ))
        return len(self.weights)

    def calculate(self, patient_genotypes: Dict[str, str],
                  disease: Optional[str] = None,
                  impute_missing: bool = True,
                  ancestry: str = "EUR") -> PRSResult:
        """
        计算PRS
        Args:
            patient_genotypes: {rsid: genotype} 如 {"rs123": "AG", "rs456": "TT"}
            disease: 疾病名（用于查参考统计量）
            impute_missing: 缺失位点是否用人群频率填充
            ancestry: 患者祖源（影响参考统计量选择）
        Returns:
            PRSResult
        """
        disease = disease or self.disease
        if not self.weights:
            raise ValueError("未加载权重。请先调用 load_weights_from_file 或 load_weights_from_list。")

        raw_score = 0.0
        n_available = 0
        contributions = []  # (rsid, gene, contribution, beta)

        for w in self.weights:
            gt = patient_genotypes.get(w.rsid)

            if gt is not None:
                dosage = self._genotype_to_dosage(gt, w.effect_allele, w.other_allele)
                n_available += 1
            elif impute_missing:
                dosage = 2 * w.effect_af  # 用人群频率填充
            else:
                continue

            contribution = dosage * w.beta
            raw_score += contribution
            contributions.append((w.rsid, w.gene_nearest, contribution, w.beta))

        # 标准化
        ref = self.REFERENCE_STATS.get(disease, {"mean": 0.0, "std": 1.0})
        z_score = (raw_score - ref["mean"]) / ref["std"] if ref["std"] > 0 else 0.0

        # Z分数 → 百分位 (正态近似)
        percentile = self._z_to_percentile(z_score)

        # 风险分层
        risk_category = self._categorize_risk(percentile)

        # 覆盖率
        coverage = n_available / len(self.weights) if self.weights else 0

        # 可信度说明
        confidence_notes = []
        if coverage < 0.8:
            confidence_notes.append(f"SNP覆盖率偏低({coverage:.0%})")
        if ancestry != "EUR":
            confidence_notes.append(f"非欧洲裔({ancestry})，PRS效力可能下降")
        confidence_note = "; ".join(confidence_notes) if confidence_notes else "可信度良好"

        # Top贡献SNP
        contributions.sort(key=lambda x: abs(x[2]), reverse=True)
        top_n = min(10, len(contributions))
        top_contributors = [
            {"rsid": c[0], "gene": c[1], "contribution": round(c[2], 5), "beta": round(c[3], 5)}
            for c in contributions[:top_n]
        ]

        return PRSResult(
            disease=disease,
            raw_score=raw_score,
            z_score=z_score,
            percentile=percentile,
            risk_category=risk_category,
            n_snps_total=len(self.weights),
            n_snps_available=n_available,
            coverage_rate=coverage,
            population=ancestry,
            confidence_note=confidence_note,
            top_contributors=top_contributors,
        )

    @staticmethod
    def _genotype_to_dosage(genotype: str, effect_allele: str, other_allele: str) -> float:
        """
        基因型 → 效应等位基因剂量
        "AA" with effect_allele="A" → 2.0
        "AG" with effect_allele="A" → 1.0
        "GG" with effect_allele="A" → 0.0
        也处理 "A/G" 和 "0/1" 格式
        """
        gt = genotype.replace('/', '').replace('|', '').upper()
        ea = effect_allele.upper()

        # 数字格式: 0=ref, 1=alt
        if gt in ("01", "10"):
            return 1.0
        if gt == "11":
            return 2.0
        if gt == "00":
            return 0.0

        # 字母格式
        if len(gt) == 2:
            return sum(1 for a in gt if a == ea)

        return 1.0  # 无法解析时返回杂合(保守估计)

    @staticmethod
    def _z_to_percentile(z: float) -> float:
        """Z分数转百分位(标准正态CDF近似)"""
        # Abramowitz & Stegun 近似
        if z < -8:
            return 0.01
        if z > 8:
            return 99.99
        a1 = 0.254829592
        a2 = -0.284496736
        a3 = 1.421413741
        a4 = -1.453152027
        a5 = 1.061405429
        p = 0.3275911
        sign = 1 if z >= 0 else -1
        x = abs(z) / math.sqrt(2)
        t = 1.0 / (1.0 + p * x)
        y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * math.exp(-x * x)
        cdf = 0.5 * (1.0 + sign * y)
        return cdf * 100

    def _categorize_risk(self, percentile: float) -> str:
        if percentile >= self.RISK_THRESHOLDS["very_high"]:
            return "very_high"
        elif percentile >= self.RISK_THRESHOLDS["high"]:
            return "high"
        elif percentile >= self.RISK_THRESHOLDS["moderate"]:
            return "moderate"
        elif percentile >= self.RISK_THRESHOLDS["average"]:
            return "average"
        else:
            return "low"

    @classmethod
    def quick_prs(cls, disease: str, patient_genotypes: Dict[str, str],
                  weights: List[Dict], ancestry: str = "EUR") -> Dict:
        """一步完成PRS计算的便捷接口"""
        calc = cls()
        calc.load_weights_from_list(weights, disease=disease)
        result = calc.calculate(patient_genotypes, ancestry=ancestry)
        return result.to_dict()


# === 内置示例权重（用于演示和测试） ===

DEMO_WEIGHTS = {
    "breast_cancer": [
        {"rsid": "rs2981582", "chrom": "10", "pos": 123337335, "effect_allele": "T",
         "other_allele": "C", "beta": 0.26, "effect_af": 0.38, "gene": "FGFR2"},
        {"rsid": "rs3803662", "chrom": "16", "pos": 52586341, "effect_allele": "A",
         "other_allele": "G", "beta": 0.20, "effect_af": 0.25, "gene": "TOX3"},
        {"rsid": "rs13387042", "chrom": "2", "pos": 217905832, "effect_allele": "A",
         "other_allele": "G", "beta": 0.12, "effect_af": 0.50, "gene": "2q35"},
        {"rsid": "rs889312", "chrom": "5", "pos": 56031884, "effect_allele": "C",
         "other_allele": "A", "beta": 0.13, "effect_af": 0.28, "gene": "MAP3K1"},
        {"rsid": "rs13281615", "chrom": "8", "pos": 128355618, "effect_allele": "G",
         "other_allele": "A", "beta": 0.08, "effect_af": 0.40, "gene": "8q24"},
    ],
    "CAD": [
        {"rsid": "rs4977574", "chrom": "9", "pos": 22098574, "effect_allele": "G",
         "other_allele": "A", "beta": 0.29, "effect_af": 0.46, "gene": "9p21.3"},
        {"rsid": "rs646776", "chrom": "1", "pos": 109818530, "effect_allele": "T",
         "other_allele": "C", "beta": 0.15, "effect_af": 0.18, "gene": "SORT1"},
        {"rsid": "rs515135", "chrom": "2", "pos": 21263900, "effect_allele": "G",
         "other_allele": "C", "beta": 0.11, "effect_af": 0.83, "gene": "APOB"},
        {"rsid": "rs11206510", "chrom": "1", "pos": 55496039, "effect_allele": "T",
         "other_allele": "C", "beta": 0.15, "effect_af": 0.82, "gene": "PCSK9"},
    ],
}


if __name__ == "__main__":
    # 自检：用demo权重和模拟基因型测试
    calc = PRSCalculator()
    calc.load_weights_from_list(DEMO_WEIGHTS["breast_cancer"], disease="breast_cancer")

    # 模拟一个高风险基因型（所有效应等位基因纯合）
    high_risk_gt = {w["rsid"]: w["effect_allele"] * 2 for w in DEMO_WEIGHTS["breast_cancer"]}
    result = calc.calculate(high_risk_gt, ancestry="EUR")
    assert result.risk_category in ("high", "very_high"), f"Expected high risk, got {result.risk_category}"

    # 模拟一个低风险基因型（所有非效应等位基因纯合）
    low_risk_gt = {w["rsid"]: w["other_allele"] * 2 for w in DEMO_WEIGHTS["breast_cancer"]}
    result_low = calc.calculate(low_risk_gt, ancestry="EUR")
    assert result_low.percentile < result.percentile

    print("✅ prs_calculator.py 自检通过")
    print(f"  高风险模拟: Z={result.z_score:.2f}, 百分位={result.percentile:.1f}, 类别={result.risk_category}")
    print(f"  低风险模拟: Z={result_low.z_score:.2f}, 百分位={result_low.percentile:.1f}, 类别={result_low.risk_category}")
    print(f"  支持疾病: {list(PRSCalculator.REFERENCE_STATS.keys())}")