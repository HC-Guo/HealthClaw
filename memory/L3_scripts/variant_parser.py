# variant_parser.py
"""
变异数据解析与过滤工具
支持 VCF 格式和 UKB 提取格式的变异数据解析
"""

import csv
import json
import re
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Tuple


@dataclass
class Variant:
    """单个变异的数据结构"""
    chrom: str
    pos: int
    ref: str
    alt: str
    rsid: str = ""
    gene: str = ""
    consequence: str = ""          # missense, nonsense, frameshift, synonymous, intronic...
    af_global: float = -1.0        # 全球等位基因频率
    af_population: Dict[str, float] = field(default_factory=dict)  # 按人群的AF
    clinvar_significance: str = ""  # pathogenic, likely_pathogenic, VUS, benign...
    clinvar_review_stars: int = 0
    zygosity: str = ""             # het, hom, hemizygous
    quality: float = 0.0
    genotype: str = ""             # 0/1, 1/1 等
    extra: Dict = field(default_factory=dict)

    @property
    def is_rare(self) -> bool:
        """MAF < 1% 视为罕见变异"""
        return 0 <= self.af_global < 0.01

    @property
    def is_coding(self) -> bool:
        coding_types = {"missense", "nonsense", "frameshift", "splice_donor",
                        "splice_acceptor", "start_lost", "stop_gained", "stop_lost",
                        "inframe_insertion", "inframe_deletion"}
        return self.consequence.lower() in coding_types

    @property
    def is_lof(self) -> bool:
        """是否为功能丧失变异 (Loss of Function)"""
        lof_types = {"nonsense", "frameshift", "splice_donor", "splice_acceptor",
                     "stop_gained", "start_lost"}
        return self.consequence.lower() in lof_types

    @property
    def is_clinically_significant(self) -> bool:
        return self.clinvar_significance.lower() in {"pathogenic", "likely_pathogenic"}

    def to_dict(self) -> dict:
        d = asdict(self)
        d["is_rare"] = self.is_rare
        d["is_coding"] = self.is_coding
        d["is_lof"] = self.is_lof
        d["is_clinically_significant"] = self.is_clinically_significant
        return d


class VariantParser:
    """
    变异数据解析器
    支持 VCF 和 TSV（UKB提取格式）
    """

    # 标准基因区域坐标 (GRCh38) - 常用癌症/心血管基因
    GENE_REGIONS = {
        "BRCA1": ("chr17", 43044295, 43125364),
        "BRCA2": ("chr13", 32315474, 32400266),
        "PALB2": ("chr16", 23603160, 23641310),
        "ATM":   ("chr11", 108222484, 108369102),
        "CHEK2": ("chr22", 28687743, 28742422),
        "TP53":  ("chr17", 7668402, 7687550),
        "LDLR":  ("chr19", 11089362, 11133830),
        "PCSK9": ("chr1",  55038942, 55064852),
        "APOB":  ("chr2",  21001429, 21044073),
        "LPA":   ("chr6",  160531462, 160664275),
        "APOE":  ("chr19", 44905754, 44909393),
        "TCF7L2":("chr10", 112950147, 113167678),
        "PITX2": ("chr4",  111538444, 111558522),
        "PTEN":  ("chr10", 87863113, 87971930),
        "MLH1":  ("chr3",  36993332, 37050918),
        "MSH2":  ("chr2",  47403067, 47710367),
    }

    def __init__(self):
        self.variants: List[Variant] = []
        self._parse_warnings: List[str] = []

    def parse_vcf(self, filepath: str, sample_id: Optional[str] = None) -> List[Variant]:
        """
        解析VCF文件
        Args:
            filepath: VCF文件路径
            sample_id: 如多样本VCF，指定样本ID
        """
        self.variants = []
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"VCF文件不存在: {filepath}")

        header_cols = []
        sample_idx = 9  # 默认第一个样本

        open_func = open
        if str(filepath).endswith('.gz'):
            import gzip
            open_func = gzip.open

        with open_func(filepath, 'rt') as f:
            for line in f:
                line = line.strip()
                if line.startswith('##'):
                    continue
                if line.startswith('#CHROM'):
                    header_cols = line.split('\t')
                    if sample_id and sample_id in header_cols:
                        sample_idx = header_cols.index(sample_id)
                    continue
                if not line:
                    continue

                fields = line.split('\t')
                if len(fields) < 8:
                    continue

                chrom, pos, rsid, ref, alt = fields[0], fields[1], fields[2], fields[3], fields[4]

                # 解析INFO字段
                info = self._parse_info(fields[7])

                # 解析样本基因型
                genotype = ""
                zygosity = ""
                if len(fields) > sample_idx:
                    gt_data = fields[sample_idx].split(':')
                    genotype = gt_data[0]
                    zygosity = self._determine_zygosity(genotype)

                # 跳过纯合参考
                if genotype in ("0/0", "0|0", "./."):
                    continue

                for alt_allele in alt.split(','):
                    v = Variant(
                        chrom=chrom,
                        pos=int(pos),
                        ref=ref,
                        alt=alt_allele,
                        rsid=rsid if rsid != '.' else "",
                        gene=info.get('GENE', info.get('ANN_GENE', '')),
                        consequence=info.get('CSQ', info.get('ANN_EFFECT', '')),
                        af_global=float(info.get('AF', info.get('gnomAD_AF', -1))),
                        clinvar_significance=info.get('CLNSIG', ''),
                        zygosity=zygosity,
                        genotype=genotype,
                        quality=float(fields[5]) if fields[5] != '.' else 0.0,
                    )
                    self.variants.append(v)

        return self.variants

    def parse_tsv(self, filepath: str, column_map: Optional[Dict] = None) -> List[Variant]:
        """
        解析TSV格式变异表（UKB提取格式或自定义表格）
        Args:
            filepath: TSV文件路径
            column_map: 列名映射 {标准名: 文件中的列名}
        """
        default_map = {
            "chrom": "chrom", "pos": "pos", "ref": "ref", "alt": "alt",
            "rsid": "rsid", "gene": "gene", "consequence": "consequence",
            "af_global": "af", "clinvar_significance": "clinvar",
            "genotype": "genotype"
        }
        if column_map:
            default_map.update(column_map)

        self.variants = []
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                v = Variant(
                    chrom=row.get(default_map["chrom"], ""),
                    pos=int(row.get(default_map["pos"], 0)),
                    ref=row.get(default_map["ref"], ""),
                    alt=row.get(default_map["alt"], ""),
                    rsid=row.get(default_map["rsid"], ""),
                    gene=row.get(default_map["gene"], ""),
                    consequence=row.get(default_map["consequence"], ""),
                    af_global=float(row.get(default_map["af_global"], -1)),
                    clinvar_significance=row.get(default_map["clinvar_significance"], ""),
                    genotype=row.get(default_map["genotype"], ""),
                )
                v.zygosity = self._determine_zygosity(v.genotype)
                self.variants.append(v)
        return self.variants

    def filter_by_gene(self, genes: List[str]) -> List[Variant]:
        """按基因名过滤"""
        gene_set = {g.upper() for g in genes}
        return [v for v in self.variants if v.gene.upper() in gene_set]

    def filter_by_region(self, chrom: str, start: int, end: int) -> List[Variant]:
        """按基因组区域过滤"""
        chrom_norm = chrom if chrom.startswith("chr") else f"chr{chrom}"
        return [v for v in self.variants
                if self._normalize_chrom(v.chrom) == chrom_norm
                and start <= v.pos <= end]

    def filter_by_gene_region(self, gene_name: str, padding: int = 5000) -> List[Variant]:
        """按预定义基因区域过滤（带上下游padding）"""
        gene_upper = gene_name.upper()
        if gene_upper not in self.GENE_REGIONS:
            self._parse_warnings.append(f"基因 {gene_name} 不在预定义区域列表中")
            return self.filter_by_gene([gene_name])
        chrom, start, end = self.GENE_REGIONS[gene_upper]
        return self.filter_by_region(chrom, start - padding, end + padding)

    def filter_rare_coding(self, maf_threshold: float = 0.01) -> List[Variant]:
        """提取罕见编码变异 — 最常用的致病变异筛选"""
        return [v for v in self.variants
                if v.is_coding and (v.af_global < 0 or v.af_global < maf_threshold)]

    def filter_lof(self) -> List[Variant]:
        """提取所有功能丧失(LoF)变异"""
        return [v for v in self.variants if v.is_lof]

    def filter_clinvar_pathogenic(self) -> List[Variant]:
        """提取ClinVar标注为致病/可能致病的变异"""
        return [v for v in self.variants if v.is_clinically_significant]

    def get_summary(self) -> Dict:
        """生成变异统计摘要"""
        total = len(self.variants)
        if total == 0:
            return {"total": 0, "message": "无变异数据"}

        coding = [v for v in self.variants if v.is_coding]
        rare = [v for v in self.variants if v.is_rare]
        lof = [v for v in self.variants if v.is_lof]
        pathogenic = [v for v in self.variants if v.is_clinically_significant]

        genes = set(v.gene for v in self.variants if v.gene)

        return {
            "total_variants": total,
            "coding_variants": len(coding),
            "rare_variants": len(rare),
            "lof_variants": len(lof),
            "clinvar_pathogenic": len(pathogenic),
            "genes_affected": sorted(genes),
            "pathogenic_details": [v.to_dict() for v in pathogenic],
            "lof_details": [v.to_dict() for v in lof],
        }

    @staticmethod
    def _parse_info(info_str: str) -> Dict[str, str]:
        result = {}
        for item in info_str.split(';'):
            if '=' in item:
                k, v = item.split('=', 1)
                result[k] = v
            else:
                result[item] = "true"
        return result

    @staticmethod
    def _determine_zygosity(genotype: str) -> str:
        gt = genotype.replace('|', '/')
        alleles = gt.split('/')
        if len(alleles) != 2:
            return "unknown"
        if alleles[0] == alleles[1] and alleles[0] != '0':
            return "hom"
        elif alleles[0] != alleles[1] and '0' not in alleles:
            return "compound_het"
        elif alleles[0] != alleles[1]:
            return "het"
        return "ref"

    @staticmethod
    def _normalize_chrom(chrom: str) -> str:
        return chrom if chrom.startswith("chr") else f"chr{chrom}"


# === 便捷函数 ===

def extract_gene_variants(vcf_path: str, genes: List[str], sample_id: str = None) -> Dict:
    """一步到位：从VCF中提取指定基因的变异并返回摘要"""
    parser = VariantParser()
    parser.parse_vcf(vcf_path, sample_id)
    results = {}
    for gene in genes:
        gene_vars = parser.filter_by_gene_region(gene)
        results[gene] = {
            "total": len(gene_vars),
            "coding": [v.to_dict() for v in gene_vars if v.is_coding],
            "lof": [v.to_dict() for v in gene_vars if v.is_lof],
            "pathogenic": [v.to_dict() for v in gene_vars if v.is_clinically_significant],
        }
    return results


def quick_scan_pathogenic(vcf_path: str, sample_id: str = None) -> List[Dict]:
    """快速扫描所有ClinVar致病变异"""
    parser = VariantParser()
    parser.parse_vcf(vcf_path, sample_id)
    return [v.to_dict() for v in parser.filter_clinvar_pathogenic()]


if __name__ == "__main__":
    # 自检
    v = Variant(chrom="chr17", pos=43094464, ref="C", alt="T", gene="BRCA1",
                consequence="missense", af_global=0.0001,
                clinvar_significance="Pathogenic", zygosity="het")
    assert v.is_rare
    assert v.is_coding
    assert v.is_clinically_significant
    assert not v.is_lof
    print("✅ variant_parser.py 自检通过")
    print(f"  预定义基因区域: {len(VariantParser.GENE_REGIONS)} 个")