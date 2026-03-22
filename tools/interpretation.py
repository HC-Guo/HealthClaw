"""
解读层 - 将原始分析结果转化为 Agent 可理解的自然语言
这是工具后端中最关键的一层：解读质量直接决定 Agent 的推理上限
"""


class GeneticInterpreter:
    """基因组结果解读器"""

    def interpret_variants(self, result: dict) -> str:
        """将基因变异查询结果转化为自然语言"""
        if result.get("_note"):
            return f"[基因组数据] {result['_note']}"

        lines = []
        variants = result.get("variants_found", [])
        no_findings = result.get("genes_without_findings", [])

        if variants:
            lines.append("检出变异:")
            for v in variants:
                clinvar = v.get("clinvar", "未知")
                consequence = v.get("consequence", "未知")
                maf = v.get("maf", "?")
                lines.append(
                    f"  - {v.get('gene','?')} / {v.get('rsid','?')}: "
                    f"基因型={v.get('genotype','?')}, "
                    f"功能={consequence}, "
                    f"致病性={clinvar}, "
                    f"MAF={maf}"
                )
                significance = self._get_clinical_significance(v)
                if significance:
                    lines.append(f"    临床意义: {significance}")

        if no_findings:
            lines.append(f"未检出已知致病变异的基因: {', '.join(no_findings)}")
            lines.append(
                "注意: 未检出不代表完全排除遗传风险 "
                "(1)检测覆盖范围有限 (2)可能存在未收录的罕见变异"
            )

        if not variants and not no_findings:
            lines.append("未进行基因变异查询或无结果。")

        return "\n".join(lines)

    def interpret_pathway(self, result: dict) -> str:
        """将通路分析结果转化为自然语言"""
        if result.get("_note"):
            return f"[通路分析] {result['_note']}"
        return f"通路分析结果: {result}"

    def interpret_prs(self, result: dict) -> str:
        """将 PRS 结果转化为自然语言"""
        if result.get("_note"):
            return f"[PRS 计算] {result['_note']}"

        disease = result.get("disease", "?")
        percentile = result.get("percentile")
        category = result.get("risk_category", "unknown")

        if percentile is None:
            return f"{disease} 的 PRS 计算未完成。请检查数据配置。"

        lines = [
            f"{disease} 多基因风险评分 (PRS):",
            f"  人群百分位: 第 {percentile} 百分位",
            f"  风险分类: {category}",
        ]

        if percentile >= 95:
            lines.append("  ⚠ 极高多基因风险: 高于 95% 的人群")
        elif percentile >= 80:
            lines.append("  偏高风险: 高于 80% 的人群")
        elif percentile <= 20:
            lines.append("  低风险: 低于 80% 的人群")
        else:
            lines.append("  风险在正常范围内")

        lines.append(
            "注意: PRS 反映常见变异的累积效应，不包含高外显率罕见变异。"
            "如患者同时携带高外显率致病变异，PRS 的增量价值较小。"
        )
        return "\n".join(lines)

    def _get_clinical_significance(self, variant: dict) -> str:
        """根据 ClinVar 注释生成临床意义描述"""
        clinvar = variant.get("clinvar", "").lower()
        gene = variant.get("gene", "")
        consequence = variant.get("consequence", "")

        if clinvar == "pathogenic":
            return f"ClinVar 判定为致病性变异。需结合疾病表型和家族史综合评估临床影响。"
        elif clinvar == "likely_pathogenic":
            return f"ClinVar 判定为可能致病。建议结合其他证据进一步确认。"
        elif clinvar == "vus" or clinvar == "uncertain_significance":
            return f"临床意义不明(VUS)。目前证据不足以判定致病性。"
        elif clinvar == "benign" or clinvar == "likely_benign":
            return ""
        return ""


class ProteomicInterpreter:
    """蛋白质组结果解读器"""

    def interpret_panel(self, result: dict) -> str:
        """将蛋白质查询结果转化为自然语言"""
        if result.get("_note"):
            return f"[蛋白质组数据] {result['_note']}"

        lines = []
        proteins = result.get("results", [])
        missing = result.get("proteins_missing", [])

        if proteins:
            lines.append("蛋白质检测结果:")
            elevated = []
            reduced = []
            normal = []
            for p in proteins:
                name = p.get("protein", "?")
                z = p.get("z_score")
                pct = p.get("percentile")
                status = p.get("status", "unknown")

                z_str = f"z={z:.1f}" if z is not None else "z=?"
                pct_str = f"P{pct:.0f}" if pct is not None else ""
                detail = f"  - {name}: {z_str} {pct_str}"

                if status == "elevated" or (z is not None and z > 2):
                    detail += " ↑ 显著升高"
                    elevated.append(name)
                elif status == "reduced" or (z is not None and z < -2):
                    detail += " ↓ 显著降低"
                    reduced.append(name)
                else:
                    detail += " 正常范围"
                    normal.append(name)
                lines.append(detail)

            if elevated:
                lines.append(f"\n综合解读: {', '.join(elevated)} 显著升高")
            if reduced:
                lines.append(f"  {', '.join(reduced)} 显著降低")
            if not elevated and not reduced:
                lines.append("\n综合解读: 所有检测蛋白在正常范围内")

        if missing:
            lines.append(f"\n缺失数据: {', '.join(missing)} (该患者可能不在 Olink 检测队列中)")

        return "\n".join(lines) if lines else "无蛋白质数据。"


class WearableInterpreter:
    """Turn structured wearable trend data into concise clinical language."""

    def summarize_status(self, trend: dict, focus: str = "general") -> str:
        if trend.get("status") != "success":
            return trend.get("message", "No wearable data available.")

        agg = trend.get("aggregated", {})
        deltas = trend.get("deltas", {})
        quality = trend.get("quality", {})
        exercise = trend.get("exercise_summary", {})

        lines = [f"[Wearable {focus} summary] period={trend.get('period')}"]
        if focus in {"general", "cardiovascular"}:
            lines.append(
                f"Resting-related heart rate: {self._fmt(agg.get('night_resting_hr'))} bpm; "
                f"overall avg HR {self._fmt(agg.get('avg_heart_rate'))} bpm."
            )
            if deltas.get("delta_hr_from_baseline") is not None:
                lines.append(f"Heart rate vs 30d baseline: {self._signed(deltas['delta_hr_from_baseline'])} bpm.")
        if focus in {"general", "metabolic"}:
            lines.append(
                f"Activity: {self._fmt(agg.get('avg_steps'))} steps/day, "
                f"{exercise.get('session_count', 0)} exercise sessions, total distance {self._fmt(agg.get('total_distance'))} m."
            )
            if deltas.get("delta_steps_from_baseline") is not None:
                lines.append(f"Steps vs 30d baseline: {self._signed(deltas['delta_steps_from_baseline'])}.")
        if focus in {"general", "sleep", "metabolic"}:
            lines.append(
                f"Sleep: {self._fmt(agg.get('avg_sleep_hours'))} h/night, avg SpO2 {self._fmt(agg.get('avg_spo2'))}."
            )
            if deltas.get("delta_sleep_from_baseline") is not None:
                lines.append(f"Sleep vs 30d baseline: {self._signed(deltas['delta_sleep_from_baseline'])} h.")
        if agg.get("avg_stress") is not None:
            lines.append(f"Average stress score: {self._fmt(agg.get('avg_stress'))}.")

        flags = trend.get("flags") or []
        if flags:
            lines.append(f"Flags: {', '.join(flags)}.")
        lines.append(
            f"Data quality: coverage={self._fmt(quality.get('coverage'))}, "
            f"days={quality.get('days_available', 0)}, flag={quality.get('quality_flag', 'unknown')}."
        )
        return "\n".join(lines)

    def summarize_import(self, result: dict) -> str:
        if result.get("status") != "success":
            return result.get("message", "Import failed.")
        return (
            f"Imported {result.get('records_imported', 0)} records and {result.get('sessions_imported', 0)} sessions. "
            f"Preview: {result.get('trend_preview', {})}"
        )

    def summarize_anomalies(self, anomalies: list, lookback_days: int, sensitivity: str) -> str:
        if not anomalies:
            return f"No persistent wearable anomalies detected in the last {lookback_days} days (sensitivity={sensitivity})."
        lines = [f"[Wearable anomalies] lookback={lookback_days}d sensitivity={sensitivity}"]
        for item in anomalies:
            lines.append(
                f"- {item.get('metric')}: {item.get('explanation')} | severity={item.get('severity')} | "
                f"current={self._fmt(item.get('current_value'))} baseline={self._fmt(item.get('baseline_value'))} "
                f"delta={self._signed(item.get('delta'))} duration={item.get('duration_days')}d"
            )
        return "\n".join(lines)

    def summarize_integration(self, findings: list, trend: dict) -> str:
        if not findings:
            return "Clinical and wearable signals do not show a strong rule-based interaction yet."
        lines = ["[Clinical + wearable integration]"]
        lines.extend(f"- {item}" for item in findings)
        quality = trend.get("quality", {})
        lines.append(
            f"Data quality context: coverage={self._fmt(quality.get('coverage'))}, days={quality.get('days_available', 0)}."
        )
        return "\n".join(lines)

    def _fmt(self, value):
        if value is None:
            return "NA"
        if isinstance(value, float):
            return f"{value:.2f}"
        return str(value)

    def _signed(self, value):
        if value is None:
            return "NA"
        return f"{value:+.2f}"
