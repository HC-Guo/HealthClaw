"""
临床数据加载工具 - 从 UKB phenotype 文件读取结构化数据并转化为自然语言摘要
"""
import os, json

class ClinicalDataLoader:
    """加载 UKB 临床数据并生成患者摘要"""

    def __init__(self):
        from config import UKB_DATA_CONFIG
        self.phenotype_file = UKB_DATA_CONFIG.get("phenotype_file", "")
        self._cache = {}

    def load(self, eid: str) -> dict:
        """
        加载患者临床数据。
        实际实现需要读取 UKB phenotype 文件（如 .tab/.csv）。
        当前为框架占位，返回模拟数据结构。
        """
        if eid in self._cache:
            return self._cache[eid]

        # TODO: 替换为真实的 UKB 数据读取逻辑
        # 示例: pd.read_csv(self.phenotype_file, sep='\t').query(f'eid == {eid}')
        data = self._load_from_ukb(eid)
        self._cache[eid] = data
        return data

    def _load_from_ukb(self, eid: str) -> dict:
        """
        真实实现入口 - 从 UKB 文件读取
        需要根据实际数据格式实现
        """
        if self.phenotype_file and os.path.exists(self.phenotype_file):
            return self._read_phenotype_file(eid)

        return {
            "eid": eid,
            "status": "placeholder",
            "demographics": {"age": None, "sex": None, "bmi": None, "ethnicity": None},
            "vitals": {"systolic_bp": None, "diastolic_bp": None, "heart_rate": None},
            "biochemistry": {},
            "medical_history": [],
            "family_history": [],
            "medications": [],
            "imaging_summary": "",
            "_note": "数据占位 - 请在 config.py 中配置 UKB_PHENOTYPE_FILE 路径"
        }

    def _read_phenotype_file(self, eid: str) -> dict:
        """从实际 UKB phenotype 文件读取 - 需根据数据格式自定义"""
        # TODO: 实现真实数据读取
        # 典型 UKB 表型文件字段映射:
        # Field 31 = Sex, Field 21003 = Age, Field 21001 = BMI
        # Field 4080 = Systolic BP, Field 4079 = Diastolic BP
        # Field 30780 = LDL-C, Field 30750 = HbA1c
        raise NotImplementedError(
            f"请实现 _read_phenotype_file 方法，从 {self.phenotype_file} 读取患者 {eid} 的数据"
        )

    def format_summary(self, data: dict) -> str:
        """将结构化数据转化为自然语言患者摘要"""
        if data.get("status") == "placeholder":
            return (
                f"[患者档案 - 模拟模式]\n"
                f"患者 EID: {data['eid']}\n"
                f"数据状态: 占位数据（未连接真实 UKB 数据源）\n"
                f"请在 config.py 中配置 UKB_PHENOTYPE_FILE 路径以加载真实数据。"
            )

        d = data.get("demographics", {})
        v = data.get("vitals", {})
        bio = data.get("biochemistry", {})

        sex_str = {"0": "女", "1": "男", 0: "女", 1: "男"}.get(d.get("sex"), str(d.get("sex", "未知")))
        lines = [
            f"[患者档案]",
            f"基本信息: {sex_str}/{d.get('age', '?')}岁, BMI={d.get('bmi', '?')}, 民族={d.get('ethnicity', '未知')}",
            f"生命体征: 血压={v.get('systolic_bp', '?')}/{v.get('diastolic_bp', '?')}mmHg, 心率={v.get('heart_rate', '?')}",
        ]

        if bio:
            lines.append("生化指标:")
            for name, info in bio.items():
                val = info if isinstance(info, (int, float)) else info.get("value", "?")
                assessment = ""
                if isinstance(info, dict) and "assessment" in info:
                    assessment = f" ({info['assessment']})"
                lines.append(f"  - {name}: {val}{assessment}")

        mh = data.get("medical_history", [])
        if mh:
            lines.append(f"既往史: {', '.join(mh)}")

        fh = data.get("family_history", [])
        if fh:
            lines.append(f"家族史: {', '.join(fh)}")

        meds = data.get("medications", [])
        if meds:
            lines.append(f"用药: {', '.join(meds)}")

        img = data.get("imaging_summary", "")
        if img:
            lines.append(f"影像发现: {img}")

        return "\n".join(lines)
