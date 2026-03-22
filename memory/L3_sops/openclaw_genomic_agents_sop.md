# 基因组学智能体 SOP
> 基因面板设计、基因组比较、gnomAD、VCF 注释、ACMG 解读、PRS、长读长测序
> 包含 14 个 OpenClaw skill 的压缩迁移。

---

### cbioportal-database
**用途**: Query cBioPortal for cancer genomics data including somatic mutations, copy number alterations, gene expression, and survival data across hundreds of cancer studies. Essential for cancer target val...
```
# Download TCGA BRCA data
wget https://cbioportal-datahub.s3.amazonaws.com/brca_tcga.tar.gz
```
**注意**: **Know your study IDs**: Use the Swagger UI or `GET /studies` to find the correct study ID; **Use sample lists**: Each study has an `all` sample list and subsets; always specify the appropriate one; **TCGA vs. GENIE**: TCGA data is comprehensive but older; GENIE has more recent clinical sequencing data

### gene-panel-design-agent
**用途**: 
```
python3 Skills/Genomics/Gene_Panel_Design_Agent/panel_designer.py \
    --disease solid_tumor \
    --gene_sources nccn,civic,oncokb \
    --platform hybcap \
    --target_size 1.5mb \
    --include_fusions true \
    --include_cnv_backbone true \
    --output panel_design/
```

### genome-compare
**用途**: Compare your genome to George Church (PGP-1) and estimate ancestry composition via IBS and EM admixture
```
python clawbio.py run compare --demo
```

### gnomad-database
**用途**: Query gnomAD (Genome Aggregation Database) for population allele frequencies, variant constraint scores (pLI, LOEUF), and loss-of-function intolerance. Essential for variant pathogenicity interpret...
```
import requests

def query_gnomad_sv(gene_symbol):
    """Query structural variants overlapping a gene."""
    url = "https://gnomad.broadinstitute.org/api"

    query = """
    query SVsByGene($gene_symbol: String!) {
      gene(gene_symbol: $gene_symbol, reference_genome: GRCh38) {
        structural_variants {
          variant_id
          type
          chrom
          pos
          end
          af
          ac
          an
        }
      }
    }
    """

    response = requests.post(url,
# ... (truncated)
```
**注意**: **Use gnomAD v4 (gnomad_r4)** for the most current data; use v2 (gnomad_r2_1) only for GRCh37 compatibility; **Handle null responses**: Variants not observed in gnomAD are not necessarily pathogenic — absence is informative; **Distinguish exome vs. genome data**: Genome data has more uniform coverage; exome data is larger but may have coverage gaps

### gwas-lookup
**用途**: Federated variant lookup across 9 genomic databases — GWAS Catalog, Open Targets, PheWeb (UKB, FinnGen, BBJ), GTEx, eQTL Catalogue, and more.
```
output_directory/
├── report.md                    # Full markdown report
├── raw_results.json             # Raw API responses (debug)
├── tables/
│   ├── gwas_associations.csv
│   ├── phewas_ukb.csv
│   ├── phewas_finngen.csv
│   ├── phewas_bbj.csv
│   ├── eqtl_associations.csv
│   └── credible_sets.csv
├── figures/
│   ├── gwas_traits_dotplot.png
│   └── allele_freq_populations.png
└── reproducibility/
    ├── commands.sh
    └── api_versions.json
```

### long-read-sequencing-agent
**用途**: 
```
python3 Skills/Genomics/Long_Read_Sequencing_Agent/longread_analyzer.py \
    --input cancer_hifi.bam \
    --platform pacbio_hifi \
    --reference GRCh38.fa \
    --sv_calling sniffles2 \
    --methylation true \
    --phasing true \
    --output longread_results/
```

### multi-ancestry-prs-agent
**用途**: 
```
python3 Skills/Precision_Medicine/Multi_Ancestry_PRS_Agent/calc_prs.py \
    --genotypes patient_genotypes.vcf.gz \
    --ancestry admixed_AFR_EUR \
    --local_ancestry lai_segments.bed \
    --trait coronary_artery_disease \
    --method prs_csx \
    --gwas_summary_stats eur_gwas.txt,afr_gwas.txt \
    --calibration_cohort 1kg_admixed \
    --output prs_results/
```

### ngs-analysis
**用途**: 
```
featureCounts -T 8 -p -B -C \
    -a genes.gtf \
    -o counts.txt \
    *.bam
```

### popeve-variant-predictor-agent
**用途**: 
```
python3 Skills/Genomics/PopEVE_Variant_Predictor_Agent/popeve_predict.py \
    --vcf patient_exome.vcf \
    --genome GRCh38 \
    --ancestry EUR \
    --gene_panel rare_disease_genes.txt \
    --min_score 0.5 \
    --output pathogenicity_scores.tsv
```

### prs-net-deep-learning-agent
**用途**: 
```
python3 Skills/Precision_Medicine/PRS_Net_Deep_Learning_Agent/prs_net_predict.py \
    --genotypes cohort_genotypes.vcf.gz \
    --ppi_network string_ppi.graphml \
    --trait type2_diabetes \
    --model_weights prs_net_t2d_v1.pt \
    --interpret_pathways true \
    --ancestry_calibration multi \
    --output prs_net_results/
```

### seq-wrangler
**用途**: Sequence QC, alignment, and BAM processing. Wraps FastQC, BWA/Bowtie2, SAMtools for automated read-to-BAM pipelines.

### varcadd-pathogenicity
**用途**: 
**触发条件**: **Variant Prioritization**: Ranking candidate variants in rare disease cases.; **VUS Interpretation**: Assessing variants of uncertain significance.; **Research**: Annotating novel variants in population studies.
```
varcadd score --input patient.vcf --output scored.vcf
```

### variant-interpretation-acmg
**用途**: 
```
python3 Skills/Genomics/Variant_Interpretation/acmg_classifier.py \
    --evidence "PVS1,PM2"
```

### vcf-annotator
**用途**: Annotate VCF variants with VEP, ClinVar, gnomAD frequencies, and ancestry-aware context. Generates prioritised variant reports.
