"""
Genomic analysis tools backed by PLINK .bed/.bim/.fam files.
"""
from __future__ import annotations

import csv
import json
import math
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np

try:
    from bed_reader import open_bed
except Exception:  # pragma: no cover - optional UKB/PLINK dependency
    open_bed = None


class GenomicAnalyzer:
    """PLINK-backed genomic analysis helper."""

    BUILTIN_PATHWAYS = {
        "DNA_REPAIR": ["BRCA1", "BRCA2", "PALB2", "ATM", "CHEK2", "RAD51C", "RAD51D"],
        "BRCA_HR": ["BRCA1", "BRCA2", "PALB2", "BARD1", "RAD51C", "RAD51D", "BRIP1"],
        "PI3K_AKT": ["PIK3CA", "PIK3R1", "AKT1", "AKT2", "PTEN", "MTOR"],
        "LIPID": ["APOB", "LDLR", "PCSK9", "LPA", "APOE", "CETP"],
        "THROMBOSIS": ["F5", "F2", "SERPINC1", "PROC", "PROS1"],
        "CARDIOMYOPATHY": ["MYBPC3", "MYH7", "TNNT2", "TNNI3", "LMNA", "DSP"],
    }
    REGION_PATTERN = re.compile(r"^(?:chr)?([A-Za-z0-9]+):(\d+)-(\d+)$", re.IGNORECASE)

    def __init__(self):
        from config import UKB_DATA_CONFIG

        self.genotype_dir = UKB_DATA_CONFIG.get("genotype_dir", "")
        self.prs_weights_dir = UKB_DATA_CONFIG.get("prs_weights_dir", "")
        self.annotation_db = UKB_DATA_CONFIG.get("annotation_db", "")

        self._plink_prefix: Optional[Path] = None
        self._bed = None
        self._sample_index: Optional[Dict[str, int]] = None
        self._variant_lookup: Optional[Dict[str, int]] = None
        self._variant_keys: Optional[Dict[str, int]] = None
        self._variant_annotations: Optional[Dict[str, dict]] = None
        self._gene_coords: Optional[Dict[str, List[dict]]] = None

    def query_gene_variants(self, eid: str, gene_list: list) -> dict:
        """Query a sample's variants within genes or explicit genomic regions."""
        try:
            sample_idx = self._get_sample_index(eid)
            self._ensure_dataset()
        except Exception as exc:
            return {
                "eid": str(eid),
                "variants_found": [],
                "genes_without_findings": list(gene_list or []),
                "_note": str(exc),
            }

        variants_found = []
        genes_without_findings = []
        inspected_regions = []

        for gene in gene_list or []:
            regions = self._resolve_gene_regions(gene)
            if not regions:
                genes_without_findings.append(gene)
                continue

            gene_results = []
            for region in regions:
                inspected_regions.append(region)
                variant_indices = self._get_variant_indices_for_region(
                    region["chrom"], region["start"], region["end"]
                )
                if not variant_indices:
                    continue
                gene_results.extend(self._collect_variants_for_sample(sample_idx, gene, variant_indices))

            if gene_results:
                variants_found.extend(gene_results)
            else:
                genes_without_findings.append(gene)

        variants_found.sort(
            key=lambda item: (
                self._clinvar_rank(item.get("clinvar")),
                self._consequence_rank(item.get("consequence")),
                item.get("chrom", ""),
                item.get("pos", 0),
            ),
            reverse=True,
        )
        variants_found = variants_found[:200]

        return {
            "eid": str(eid),
            "variants_found": variants_found,
            "genes_without_findings": genes_without_findings,
            "inspected_regions": inspected_regions,
            "dataset_info": self.get_dataset_summary(),
        }

    def query_pathway(self, eid: str, pathway_list: list) -> dict:
        """Expand pathway names into genes and reuse gene-level querying."""
        expanded_genes = []
        unresolved = []
        pathway_map = {}
        for pathway in pathway_list or []:
            genes = self._resolve_pathway_genes(pathway)
            if genes:
                pathway_map[pathway] = genes
                expanded_genes.extend(genes)
            else:
                unresolved.append(pathway)

        unique_genes = list(dict.fromkeys(expanded_genes))
        result = self.query_gene_variants(eid, unique_genes)
        result["pathways"] = pathway_list or []
        result["pathway_gene_map"] = pathway_map
        if unresolved:
            result["unresolved_pathways"] = unresolved
            note = "Missing pathway mapping for: " + ", ".join(unresolved)
            if result.get("_note"):
                result["_note"] = f"{result['_note']}; {note}"
            else:
                result["_note"] = note
        return result

    def calculate_prs(self, eid: str, disease: str) -> dict:
        """Calculate a PRS from local weight files and the PLINK genotype matrix."""
        try:
            sample_idx = self._get_sample_index(eid)
            self._ensure_dataset()
            weights_meta = self._load_prs_weights(disease)
        except Exception as exc:
            return {
                "eid": str(eid),
                "disease": disease,
                "prs_score": None,
                "percentile": None,
                "risk_category": "unknown",
                "_note": str(exc),
            }

        weights = weights_meta["weights"]
        matched_indices = []
        aligned = []

        for row in weights:
            matched = self._match_weight_to_variant(row)
            if matched is None:
                continue
            variant_idx, dosage_transform = matched
            matched_indices.append(variant_idx)
            aligned.append((row, variant_idx, dosage_transform))

        if not aligned:
            return {
                "eid": str(eid),
                "disease": disease,
                "prs_score": None,
                "percentile": None,
                "risk_category": "unknown",
                "_note": f"No PRS variants from '{disease}' matched the PLINK dataset.",
            }

        geno = self._bed.read(np.s_[sample_idx, matched_indices], dtype="float32", order="C")[0]
        raw_score = 0.0
        expected_mean = 0.0
        expected_var = 0.0
        n_observed = 0
        n_imputed = 0
        used_variants = []

        for idx, (row, variant_idx, dosage_transform) in enumerate(aligned):
            dosage_a1 = float(geno[idx])
            dosage_effect = dosage_transform(dosage_a1)
            effect_af = self._safe_float(row.get("effect_af"), default=None)
            beta = self._safe_float(row.get("beta"), default=0.0)

            if dosage_effect is None or math.isnan(dosage_effect):
                if effect_af is None:
                    continue
                dosage_effect = 2.0 * effect_af
                n_imputed += 1
            else:
                n_observed += 1

            raw_score += dosage_effect * beta
            if effect_af is not None:
                expected_mean += 2.0 * effect_af * beta
                expected_var += 2.0 * effect_af * (1.0 - effect_af) * (beta ** 2)

            annotation = self._variant_annotation_for_index(variant_idx)
            used_variants.append(
                {
                    "rsid": str(row.get("rsid") or self._bed.sid[variant_idx]),
                    "chrom": str(self._bed.chromosome[variant_idx]),
                    "pos": int(self._bed.bp_position[variant_idx]),
                    "effect_allele": str(row.get("effect_allele", "")),
                    "other_allele": str(row.get("other_allele", "")),
                    "beta": beta,
                    "dosage_effect_allele": round(float(dosage_effect), 4),
                    "contribution": round(float(dosage_effect * beta), 6),
                    "gene": annotation.get("gene") or row.get("gene", ""),
                }
            )

        std = math.sqrt(expected_var) if expected_var > 0 else None
        z_score = (raw_score - expected_mean) / std if std else None
        percentile = self._z_to_percentile(z_score) if z_score is not None else None
        risk_category = self._categorize_percentile(percentile)

        used_variants.sort(key=lambda item: abs(item.get("contribution", 0.0)), reverse=True)
        coverage_rate = len(aligned) / len(weights) if weights else 0.0

        note_parts = []
        if coverage_rate < 0.8:
            note_parts.append(f"PRS SNP coverage is {coverage_rate:.1%}; interpret cautiously.")
        if n_imputed:
            note_parts.append(f"{n_imputed} SNPs used allele-frequency imputation.")
        if weights_meta.get("population") and weights_meta["population"] != "mixed":
            note_parts.append(f"Reference population: {weights_meta['population']}.")

        return {
            "eid": str(eid),
            "disease": disease,
            "prs_score": round(float(raw_score), 6),
            "percentile": None if percentile is None else round(float(percentile), 2),
            "risk_category": risk_category,
            "z_score": None if z_score is None else round(float(z_score), 4),
            "coverage_rate": round(float(coverage_rate), 4),
            "n_weights_total": len(weights),
            "n_weights_matched": len(aligned),
            "n_observed": n_observed,
            "n_imputed": n_imputed,
            "top_contributors": used_variants[:15],
            "weights_file": weights_meta.get("weights_file", ""),
            "note": " ".join(note_parts) if note_parts else "",
        }

    def get_dataset_summary(self) -> dict:
        """Expose basic dataset metadata for debugging and status output."""
        try:
            self._ensure_dataset()
        except Exception as exc:
            return {"status": "error", "message": str(exc)}

        prefix = str(self._plink_prefix) if self._plink_prefix else ""
        return {
            "status": "success",
            "plink_prefix": prefix,
            "samples": int(self._bed.iid_count),
            "variants": int(self._bed.sid_count),
        }

    def query_variant_by_rsid(self, eid: str, rsids: Iterable[str]) -> dict:
        """Small helper for direct rsID-based querying."""
        try:
            sample_idx = self._get_sample_index(eid)
            self._ensure_dataset()
        except Exception as exc:
            return {"eid": str(eid), "variants": [], "_note": str(exc)}

        indices = []
        labels = []
        for rsid in rsids:
            idx = self._variant_lookup.get(str(rsid))
            if idx is not None:
                indices.append(idx)
                labels.append(rsid)

        variants = self._collect_variants_for_sample(sample_idx, "", indices)
        for item, label in zip(variants, labels):
            item["query_rsid"] = label
        return {"eid": str(eid), "variants": variants}

    def _ensure_dataset(self):
        if self._bed is not None:
            return
        if open_bed is None:
            raise ImportError("Optional dependency 'bed_reader' is not installed; PLINK genomic tools are unavailable.")

        prefix = self._resolve_plink_prefix()
        bed_path = prefix.with_suffix(".bed")
        bim_path = prefix.with_suffix(".bim")
        fam_path = prefix.with_suffix(".fam")
        self._bed = open_bed(
            str(bed_path),
            count_A1=True,
            bim_location=str(bim_path),
            fam_location=str(fam_path),
        )
        self._sample_index = self._build_sample_index()
        self._variant_lookup, self._variant_keys = self._build_variant_lookup()

    def _resolve_plink_prefix(self) -> Path:
        if self._plink_prefix is not None:
            return self._plink_prefix

        if not self.genotype_dir:
            raise FileNotFoundError("UKB_GENOTYPE_DIR is not configured.")

        raw = Path(self.genotype_dir)
        candidates = []

        if raw.is_file() and raw.suffix.lower() in {".bed", ".bim", ".fam"}:
            candidates.append(raw.with_suffix(""))
        elif raw.is_file():
            candidates.append(raw)
        elif raw.is_dir():
            for bed_file in sorted(raw.rglob("*.bed")):
                prefix = bed_file.with_suffix("")
                if prefix.with_suffix(".bim").exists() and prefix.with_suffix(".fam").exists():
                    candidates.append(prefix)
        else:
            suffix_candidates = [raw.with_suffix(ext) for ext in (".bed", ".bim", ".fam")]
            if any(path.exists() for path in suffix_candidates):
                candidates.append(raw)

        if not candidates:
            raise FileNotFoundError(
                f"No complete PLINK trio (.bed/.bim/.fam) found under '{self.genotype_dir}'."
            )
        if len(candidates) > 1:
            candidates.sort(key=lambda item: len(str(item)))
        self._plink_prefix = candidates[0]
        return self._plink_prefix

    def _build_sample_index(self) -> Dict[str, int]:
        mapping = {}
        for idx in range(self._bed.iid_count):
            iid = str(self._bed.iid[idx])
            fid = str(self._bed.fid[idx])
            keys = {iid, fid, f"{fid}:{iid}"}
            if iid.isdigit():
                keys.add(str(int(iid)))
            for key in keys:
                mapping.setdefault(key, idx)
        return mapping

    def _build_variant_lookup(self) -> Tuple[Dict[str, int], Dict[str, int]]:
        rsid_map = {}
        coord_map = {}
        for idx in range(self._bed.sid_count):
            rsid = str(self._bed.sid[idx])
            chrom = self._normalize_chr(self._bed.chromosome[idx])
            pos = int(self._bed.bp_position[idx])
            if rsid and rsid != ".":
                rsid_map.setdefault(rsid, idx)
            coord_map[f"{chrom}:{pos}"] = idx
        return rsid_map, coord_map

    def _get_sample_index(self, eid: str) -> int:
        self._ensure_dataset()
        key = str(eid)
        if key in self._sample_index:
            return self._sample_index[key]
        if key.isdigit():
            key = str(int(key))
            if key in self._sample_index:
                return self._sample_index[key]
        raise KeyError(f"Sample '{eid}' not found in PLINK .fam.")

    def _resolve_gene_regions(self, gene: str) -> List[dict]:
        region = self._parse_region(gene)
        if region:
            return [region]
        return self._load_gene_coords().get(str(gene).upper(), [])

    def _parse_region(self, text: str) -> Optional[dict]:
        match = self.REGION_PATTERN.match(str(text).strip())
        if not match:
            return None
        chrom, start, end = match.groups()
        return {
            "gene": text,
            "chrom": self._normalize_chr(chrom),
            "start": int(start),
            "end": int(end),
            "source": "explicit_region",
        }

    def _load_gene_coords(self) -> Dict[str, List[dict]]:
        if self._gene_coords is not None:
            return self._gene_coords

        coords = {}
        paths = self._discover_annotation_files(kind="gene")
        for path in paths:
            for row in self._iter_gene_coordinate_rows(path):
                gene = row["gene"].upper()
                coords.setdefault(gene, []).append(row)
        self._gene_coords = coords
        return self._gene_coords

    def _load_variant_annotations(self) -> Dict[str, dict]:
        if self._variant_annotations is not None:
            return self._variant_annotations

        annotations = {}
        for path in self._discover_annotation_files(kind="variant"):
            for row in self._iter_variant_annotation_rows(path):
                keys = self._annotation_keys(row)
                for key in keys:
                    annotations[key] = row
        self._variant_annotations = annotations
        return self._variant_annotations

    def _discover_annotation_files(self, kind: str) -> List[Path]:
        if not self.annotation_db:
            return []

        path = Path(self.annotation_db)
        if path.is_file():
            if kind == "gene":
                return [path] if path.suffix.lower() in {".gtf", ".gff", ".gff3", ".tsv", ".csv", ".txt", ".bed"} else []
            return [path] if path.suffix.lower() in {".json", ".tsv", ".csv", ".txt"} else []

        if not path.is_dir():
            return []

        gene_names = ("gene", "genes", "gene_coordinates", "gene_coord", "annotation")
        variant_names = ("variant", "variants", "clinvar", "annotation", "annotations")
        accepted = {".gtf", ".gff", ".gff3", ".tsv", ".csv", ".txt", ".bed", ".json"}
        matches = []
        for child in sorted(path.iterdir()):
            if child.suffix.lower() not in accepted:
                continue
            name = child.stem.lower()
            keys = gene_names if kind == "gene" else variant_names
            if any(token in name for token in keys):
                matches.append(child)
        return matches

    def _iter_gene_coordinate_rows(self, path: Path):
        suffix = path.suffix.lower()
        if suffix in {".gtf", ".gff", ".gff3"}:
            yield from self._iter_gtf_gene_rows(path)
            return

        delimiter = "\t" if suffix in {".tsv", ".bed", ".txt"} else ","
        with path.open("r", encoding="utf-8", errors="ignore") as handle:
            reader = csv.DictReader(handle, delimiter=delimiter)
            for row in reader:
                gene = row.get("gene") or row.get("gene_name") or row.get("symbol") or row.get("name")
                chrom = row.get("chrom") or row.get("chr") or row.get("chromosome")
                start = row.get("start") or row.get("txStart")
                end = row.get("end") or row.get("txEnd")
                if not gene or not chrom or not start or not end:
                    continue
                yield {
                    "gene": str(gene).upper(),
                    "chrom": self._normalize_chr(chrom),
                    "start": int(float(start)),
                    "end": int(float(end)),
                    "source": path.name,
                }

    def _iter_gtf_gene_rows(self, path: Path):
        with path.open("r", encoding="utf-8", errors="ignore") as handle:
            for line in handle:
                if not line or line.startswith("#"):
                    continue
                parts = line.rstrip("\n").split("\t")
                if len(parts) < 9:
                    continue
                feature = parts[2].lower()
                if feature not in {"gene", "transcript"}:
                    continue
                attrs = self._parse_gtf_attributes(parts[8])
                gene = attrs.get("gene_name") or attrs.get("gene") or attrs.get("gene_id") or attrs.get("Name")
                if not gene:
                    continue
                yield {
                    "gene": str(gene).split(".")[0].upper(),
                    "chrom": self._normalize_chr(parts[0]),
                    "start": int(parts[3]),
                    "end": int(parts[4]),
                    "source": path.name,
                }

    def _iter_variant_annotation_rows(self, path: Path):
        suffix = path.suffix.lower()
        if suffix == ".json":
            with path.open("r", encoding="utf-8", errors="ignore") as handle:
                data = json.load(handle)
            rows = data.get("variants", data) if isinstance(data, dict) else data
            for row in rows or []:
                normalized = self._normalize_variant_row(row, path.name)
                if normalized:
                    yield normalized
            return

        delimiter = "\t" if suffix in {".tsv", ".txt"} else ","
        with path.open("r", encoding="utf-8", errors="ignore") as handle:
            reader = csv.DictReader(handle, delimiter=delimiter)
            for row in reader:
                normalized = self._normalize_variant_row(row, path.name)
                if normalized:
                    yield normalized

    def _normalize_variant_row(self, row: dict, source: str) -> Optional[dict]:
        if not isinstance(row, dict):
            return None
        chrom = row.get("chrom") or row.get("chr") or row.get("chromosome")
        pos = row.get("pos") or row.get("position") or row.get("bp") or row.get("bp_position")
        rsid = row.get("rsid") or row.get("sid") or row.get("id") or row.get("snp")
        if not rsid and not (chrom and pos):
            return None
        return {
            "rsid": str(rsid) if rsid else "",
            "chrom": self._normalize_chr(chrom) if chrom else "",
            "pos": int(float(pos)) if pos else 0,
            "gene": str(row.get("gene") or row.get("gene_name") or row.get("symbol") or ""),
            "consequence": str(row.get("consequence") or row.get("effect") or row.get("annotation") or "unknown"),
            "clinvar": str(row.get("clinvar") or row.get("clinical_significance") or "unknown"),
            "maf": self._safe_float(row.get("maf") or row.get("af") or row.get("gnomad_af")),
            "source": source,
        }

    def _annotation_keys(self, row: dict) -> List[str]:
        keys = []
        rsid = row.get("rsid")
        if rsid:
            keys.append(str(rsid))
        chrom = row.get("chrom")
        pos = row.get("pos")
        if chrom and pos:
            keys.append(f"{chrom}:{pos}")
        return keys

    def _resolve_pathway_genes(self, pathway: str) -> List[str]:
        key = str(pathway).strip().upper().replace("-", "_").replace(" ", "_")
        return self.BUILTIN_PATHWAYS.get(key, [])

    def _get_variant_indices_for_region(self, chrom: str, start: int, end: int) -> List[int]:
        chrom = self._normalize_chr(chrom)
        chromosomes = np.array([self._normalize_chr(ch) for ch in self._bed.chromosome])
        positions = np.array(self._bed.bp_position, dtype=np.int64)
        mask = (chromosomes == chrom) & (positions >= int(start)) & (positions <= int(end))
        return np.where(mask)[0].tolist()

    def _collect_variants_for_sample(self, sample_idx: int, gene: str, variant_indices: List[int]) -> List[dict]:
        if not variant_indices:
            return []

        geno = self._bed.read(np.s_[sample_idx, variant_indices], dtype="float32", order="C")[0]
        variants = []
        for local_idx, variant_idx in enumerate(variant_indices):
            dosage = float(geno[local_idx])
            if math.isnan(dosage):
                continue
            genotype = self._dosage_to_genotype(
                dosage,
                str(self._bed.allele_1[variant_idx]),
                str(self._bed.allele_2[variant_idx]),
            )
            annotation = self._variant_annotation_for_index(variant_idx)
            if annotation.get("gene") and gene and annotation["gene"].upper() != gene.upper() and not self._parse_region(gene):
                continue
            variants.append(
                {
                    "gene": annotation.get("gene") or gene,
                    "rsid": str(self._bed.sid[variant_idx]),
                    "chrom": str(self._bed.chromosome[variant_idx]),
                    "pos": int(self._bed.bp_position[variant_idx]),
                    "genotype": genotype,
                    "dosage_a1": round(dosage, 4),
                    "allele_1": str(self._bed.allele_1[variant_idx]),
                    "allele_2": str(self._bed.allele_2[variant_idx]),
                    "consequence": annotation.get("consequence", "unknown"),
                    "clinvar": annotation.get("clinvar", "unknown"),
                    "maf": annotation.get("maf"),
                }
            )
        return variants

    def _variant_annotation_for_index(self, variant_idx: int) -> dict:
        annotations = self._load_variant_annotations()
        rsid = str(self._bed.sid[variant_idx])
        key = f"{self._normalize_chr(self._bed.chromosome[variant_idx])}:{int(self._bed.bp_position[variant_idx])}"
        return annotations.get(rsid) or annotations.get(key) or {}

    def _load_prs_weights(self, disease: str) -> dict:
        if not self.prs_weights_dir:
            raise FileNotFoundError("UKB_PRS_WEIGHTS_DIR is not configured.")

        base = Path(self.prs_weights_dir)
        candidate_names = self._candidate_weight_names(disease)
        files = []

        if base.is_file():
            files = [base]
        elif base.is_dir():
            for name in candidate_names:
                for suffix in (".json", ".tsv", ".csv", ".txt"):
                    candidate = base / f"{name}{suffix}"
                    if candidate.exists():
                        files.append(candidate)
                        break
                if files:
                    break
            if not files:
                files = sorted(
                    [item for item in base.iterdir() if item.suffix.lower() in {".json", ".tsv", ".csv", ".txt"}]
                )
        else:
            raise FileNotFoundError(f"PRS weights path '{self.prs_weights_dir}' does not exist.")

        if not files:
            raise FileNotFoundError(f"No PRS weight file found for disease '{disease}'.")

        weights_file = files[0]
        population = "mixed"
        weights = []
        if weights_file.suffix.lower() == ".json":
            with weights_file.open("r", encoding="utf-8", errors="ignore") as handle:
                data = json.load(handle)
            if isinstance(data, dict):
                population = str(data.get("population", population))
                disease = str(data.get("disease", disease))
                weight_rows = data.get("weights", [])
            else:
                weight_rows = data
            for row in weight_rows:
                normalized = self._normalize_weight_row(row)
                if normalized:
                    weights.append(normalized)
        else:
            delimiter = "\t" if weights_file.suffix.lower() in {".tsv", ".txt"} else ","
            with weights_file.open("r", encoding="utf-8", errors="ignore") as handle:
                reader = csv.DictReader(handle, delimiter=delimiter)
                for row in reader:
                    normalized = self._normalize_weight_row(row)
                    if normalized:
                        weights.append(normalized)

        if not weights:
            raise ValueError(f"PRS weight file '{weights_file}' contains no usable rows.")

        return {
            "disease": disease,
            "population": population.lower(),
            "weights_file": str(weights_file),
            "weights": weights,
        }

    def _candidate_weight_names(self, disease: str) -> List[str]:
        clean = str(disease).strip().lower()
        alias = clean.replace(" ", "_").replace("-", "_")
        return [alias, clean.replace(" ", ""), clean]

    def _normalize_weight_row(self, row: dict) -> Optional[dict]:
        rsid = row.get("rsid") or row.get("sid") or row.get("snp") or row.get("id")
        chrom = row.get("chrom") or row.get("chr") or row.get("chromosome")
        pos = row.get("pos") or row.get("bp") or row.get("position")
        effect_allele = row.get("effect_allele") or row.get("ea") or row.get("a1")
        other_allele = row.get("other_allele") or row.get("nea") or row.get("a2")
        beta = row.get("beta") or row.get("weight") or row.get("effect") or row.get("log_or")
        if beta is None or (not rsid and not (chrom and pos)):
            return None
        return {
            "rsid": str(rsid) if rsid else "",
            "chrom": self._normalize_chr(chrom) if chrom else "",
            "pos": int(float(pos)) if pos else 0,
            "effect_allele": str(effect_allele or "").upper(),
            "other_allele": str(other_allele or "").upper(),
            "beta": float(beta),
            "effect_af": self._safe_float(
                row.get("effect_af") or row.get("eaf") or row.get("af") or row.get("freq")
            ),
            "gene": str(row.get("gene") or row.get("nearest_gene") or ""),
        }

    def _match_weight_to_variant(self, row: dict):
        rsid = row.get("rsid")
        chrom = row.get("chrom")
        pos = row.get("pos")
        variant_idx = None
        if rsid:
            variant_idx = self._variant_lookup.get(rsid)
        if variant_idx is None and chrom and pos:
            variant_idx = self._variant_keys.get(f"{chrom}:{pos}")
        if variant_idx is None:
            return None

        allele_1 = str(self._bed.allele_1[variant_idx]).upper()
        allele_2 = str(self._bed.allele_2[variant_idx]).upper()
        effect = str(row.get("effect_allele", "")).upper()
        other = str(row.get("other_allele", "")).upper()

        if effect and effect == allele_1:
            return variant_idx, lambda dosage_a1: dosage_a1
        if effect and effect == allele_2:
            return variant_idx, lambda dosage_a1: np.nan if math.isnan(float(dosage_a1)) else 2.0 - float(dosage_a1)
        if not effect and other:
            if other == allele_1:
                return variant_idx, lambda dosage_a1: np.nan if math.isnan(float(dosage_a1)) else 2.0 - float(dosage_a1)
            if other == allele_2:
                return variant_idx, lambda dosage_a1: dosage_a1
        if not effect:
            return variant_idx, lambda dosage_a1: dosage_a1
        return None

    def _dosage_to_genotype(self, dosage_a1: float, allele_1: str, allele_2: str) -> str:
        dosage = int(round(float(dosage_a1)))
        if dosage <= 0:
            return f"{allele_2}/{allele_2}"
        if dosage == 1:
            return f"{allele_1}/{allele_2}"
        return f"{allele_1}/{allele_1}"

    def _clinvar_rank(self, value: Optional[str]) -> int:
        text = str(value or "").lower()
        if "pathogenic" in text and "likely" not in text:
            return 5
        if "likely_pathogenic" in text or "likely pathogenic" in text:
            return 4
        if "vus" in text or "uncertain" in text:
            return 3
        if "benign" in text:
            return 2
        if text and text != "unknown":
            return 1
        return 0

    def _consequence_rank(self, value: Optional[str]) -> int:
        text = str(value or "").lower()
        if any(token in text for token in ("frameshift", "stop_gained", "splice", "nonsense")):
            return 5
        if any(token in text for token in ("missense", "protein_altering")):
            return 4
        if any(token in text for token in ("synonymous", "utr")):
            return 2
        if text and text != "unknown":
            return 1
        return 0

    def _categorize_percentile(self, percentile: Optional[float]) -> str:
        if percentile is None:
            return "unknown"
        if percentile >= 95:
            return "very_high"
        if percentile >= 80:
            return "high"
        if percentile >= 60:
            return "moderate"
        if percentile <= 20:
            return "low"
        return "average"

    def _z_to_percentile(self, z_score: Optional[float]) -> Optional[float]:
        if z_score is None:
            return None
        return 100.0 * 0.5 * (1.0 + math.erf(float(z_score) / math.sqrt(2.0)))

    def _normalize_chr(self, chrom) -> str:
        text = str(chrom).strip()
        if text.lower().startswith("chr"):
            text = text[3:]
        return text.upper()

    def _parse_gtf_attributes(self, text: str) -> Dict[str, str]:
        attrs = {}
        for chunk in text.strip().strip(";").split(";"):
            chunk = chunk.strip()
            if not chunk:
                continue
            if "=" in chunk:
                key, value = chunk.split("=", 1)
            elif " " in chunk:
                key, value = chunk.split(" ", 1)
            else:
                continue
            attrs[key.strip()] = value.strip().strip('"')
        return attrs

    def _safe_float(self, value, default=np.nan):
        if value in (None, "", "."):
            return default
        try:
            return float(value)
        except (TypeError, ValueError):
            return default
