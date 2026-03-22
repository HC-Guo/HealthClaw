# gptomics 通路与系统生物学 SOP
> 通路分析、因果基因组学、流行病学基因组学、系统生物学
> 包含 21 个 OpenClaw skill 的压缩迁移。

---

### bio-causal-genomics-colocalization-analysis
**用途**: Test whether two traits share a causal variant at a genomic locus using Bayesian colocalization with coloc. Computes posterior probabilities for shared vs distinct causal variants between GWAS and ...
```
# When only p-values are available, use MAF to approximate
gwas_pval <- list(
  pvalues = gwas_df$P,
  MAF = gwas_df$MAF,
  snp = gwas_df$SNP,
  position = gwas_df$POS,
  type = 'cc',
  s = 0.3,
  N = 50000
)

result <- coloc.abf(dataset1 = gwas_pval, dataset2 = eqtl_data)
```

### bio-causal-genomics-fine-mapping
**用途**: Identify likely causal variants within GWAS loci using SuSiE for sum of single effects regression and FINEMAP for shotgun stochastic search. Computes posterior inclusion probabilities and credible ...
```
# Read LD matrix into R
ld <- as.matrix(read.table('ld_matrix.ld'))

# Ensure positive semi-definite (numerical issues can violate this)
# Add small ridge to diagonal if needed
eigenvalues <- eigen(ld, only.values = TRUE)$values
if (any(eigenvalues < 0)) {
  ld <- ld + diag(abs(min(eigenvalues)) + 1e-6, nrow(ld))
}
```

### bio-causal-genomics-mediation-analysis
**用途**: Decompose genetic effects into direct and indirect paths through mediating variables using the mediation R package. Tests whether gene expression, methylation, or other molecular phenotypes mediate...
```
# For testing many potential mediators simultaneously (e.g., all CpG sites)
# install.packages('HIMA')
library(HIMA)

# X: treatment (genotype), M: high-dimensional mediators, Y: outcome
# HIMA uses penalized regression to select significant mediators

result <- hima(
  X = dat$genotype,
  Y = dat$disease,
  M = as.matrix(dat[, mediator_cols]),
  COV.XM = as.matrix(dat[, covariate_cols]),
  Y.family = 'binomial',
  M.family = 'gaussian',
  penalty = 'MCP'    # Minimax concave penalty (default)
)
# ... (truncated)
```

### bio-causal-genomics-mendelian-randomization
**用途**: Estimate causal effects between exposures and outcomes using genetic variants as instrumental variables with TwoSampleMR. Implements IVW, MR-Egger, weighted median, and MR-PRESSO methods for robust...
```
library(TwoSampleMR)

# Scatter plot: SNP-exposure vs SNP-outcome effects with method slopes
mr_scatter_plot(results, dat)

# Forest plot: Individual SNP and combined estimates
mr_forest_plot(single)

# Leave-one-out plot
mr_leaveoneout_plot(loo)

# Funnel plot: Precision vs causal estimate (asymmetry = pleiotropy)
mr_funnel_plot(single)
```

### bio-causal-genomics-pleiotropy-detection
**用途**: Detect and correct for horizontal pleiotropy in Mendelian randomization analyses using MR-PRESSO for outlier removal, MR-Egger regression for directional pleiotropy, and Steiger filtering for varia...
```
library(TwoSampleMR)

# Steiger test: Verify each instrument explains more variance in
# the exposure than the outcome. Instruments failing this test
# may act through a reverse causal pathway.

steiger <- steiger_filtering(dat)

# Keep only correctly oriented instruments
dat_steiger <- steiger[steiger$steiger_dir == TRUE, ]
cat('Instruments passing Steiger filter:', nrow(dat_steiger), 'of', nrow(steiger), '\n')

# Re-run MR with filtered instruments
results_steiger <- mr(dat_steiger)
print(resu
# ... (truncated)
```

### bio-epidemiological-genomics-amr-surveillance
**用途**: Detect and track antimicrobial resistance genes using AMRFinderPlus and ResFinder with epidemiological context. Monitor resistance trends and identify emerging resistance patterns. Use when screeni...
```
# ResFinder for acquired resistance genes
# Web: https://cge.cbs.dtu.dk/services/ResFinder/

# Command line via KMA
kma -i reads_1.fq reads_2.fq -o output -t_db resfinder_db -1t1

# Or use CGE Docker
docker run --rm -v $(pwd):/data cgetools/resfinder \
    -i /data/genome.fasta -o /data/results -db_res /db/resfinder_db
```

### bio-epidemiological-genomics-pathogen-typing
**用途**: Perform multi-locus sequence typing (MLST), core genome MLST, and SNP-based strain typing for bacterial isolate characterization using mlst and chewBBACA. Use when identifying strain types, trackin...
```
# chewBBACA for cgMLST
pip install chewbbaca

# Download or create schema
chewBBACA.py DownloadSchema -sp "Salmonella enterica" -o schema_dir

# Run cgMLST
chewBBACA.py AlleleCall -i genomes/ -g schema_dir -o results/

# Analyze results
chewBBACA.py ExtractCgMLST -i results/results_alleles.tsv \
    -o cgmlst_results.tsv --threshold 0.95
```

### bio-epidemiological-genomics-phylodynamics
**用途**: Construct time-scaled phylogenies and infer evolutionary dynamics using TreeTime and BEAST2 for outbreak analysis. Estimate divergence times, molecular clock rates, and ancestral states. Use when d...
```
def extract_skyline(treetime_results_dir):
    '''Extract coalescent skyline from TreeTime output

    Skyline shows effective population size over time.
    Useful for:
    - Detecting population expansions (outbreak growth)
    - Identifying bottlenecks
    - Estimating R0 from growth rate
    '''
    import json

    with open(f'{treetime_results_dir}/skyline.json') as f:
        skyline = json.load(f)

    times = skyline['times']
    Ne = skyline['Ne']  # Effective population size

    retu
# ... (truncated)
```

### bio-epidemiological-genomics-transmission-inference
**用途**: Infer pathogen transmission networks and identify likely transmission pairs using TransPhylo and outbreak reconstruction algorithms. Estimate who-infected-whom from genomic and epidemiological data...
```
# Analyze TransPhylo output

# Get median transmission tree
med_tree <- medTTree(res)

# Plot transmission tree
plot(med_tree)

# Get R0 estimate
r0_samples <- res$record[, 'off.r']
cat('R0 estimate:', median(r0_samples), '\n')
cat('95% CI:', quantile(r0_samples, c(0.025, 0.975)), '\n')

# Identify superspreaders
# Count number infected by each case
infections_per_case <- table(med_tree$ttree[, 'infector'])
superspreaders <- names(infections_per_case[infections_per_case > 3])
```

### bio-epidemiological-genomics-variant-surveillance
**用途**: Assign pathogen lineages and track variants using Nextclade and pangolin for viral surveillance. Monitor variant prevalence and identify emerging variants of concern. Use when classifying viral seq...
```
# Install pangolin
pip install pangolin

# Update lineage definitions
pangolin --update

# Run lineage assignment
pangolin sequences.fasta -o pangolin_results.csv

# With specific version
pangolin sequences.fasta --analysis-mode accurate -o results.csv
```

### bio-pathway-enrichment-visualization
**用途**: Visualize enrichment results using enrichplot package functions. Use when creating publication-quality figures from clusterProfiler results. Covers dotplot, barplot, cnetplot, emapplot, gseaplot2, ...
```
upsetplot(ego)

# Limit to specific number of terms
upsetplot(ego, n = 10)
```

### bio-pathway-go-enrichment
**用途**: Gene Ontology over-representation analysis using clusterProfiler enrichGO. Use when identifying biological functions enriched in a gene list from differential expression or other analyses. Supports...
```
# Remove redundant GO terms (keeps representative terms)
ego_simplified <- simplify(ego, cutoff = 0.7, by = 'p.adjust', select_fun = min)
```

### bio-pathway-gsea
**用途**: Gene Set Enrichment Analysis using clusterProfiler gseGO and gseKEGG. Use when analyzing ranked gene lists to find coordinated expression changes in gene sets without arbitrary significance cutoffs...
```
results_df <- as.data.frame(gse_go)
write.csv(results_df, 'gsea_go_results.csv', row.names = FALSE)

# Get leading edge genes for a term
leading_edge <- strsplit(results_df$core_enrichment[1], '/')[[1]]
```

### bio-pathway-kegg-pathways
**用途**: KEGG pathway and module enrichment analysis using clusterProfiler enrichKEGG and enrichMKEGG. Use when identifying metabolic and signaling pathways over-represented in a gene list. Supports 4000+ o...
```
# Find organism codes
search_kegg_organism('mouse')
search_kegg_organism('zebrafish')
```

### bio-pathway-reactome
**用途**: Reactome pathway enrichment using ReactomePA package. Use when analyzing gene lists against Reactome's curated peer-reviewed pathway database. Performs over-representation analysis and GSEA with vi...
```
results_df <- as.data.frame(pathway_result)
write.csv(results_df, 'reactome_enrichment.csv', row.names = FALSE)

# Key columns: ID, Description, GeneRatio, BgRatio, pvalue, p.adjust, geneID, Count
```

### bio-pathway-wikipathways
**用途**: WikiPathways enrichment using clusterProfiler and rWikiPathways. Use when analyzing gene lists against community-curated open-source pathways. Performs over-representation analysis and GSEA for 30+...
```
results_df <- as.data.frame(wp_result)
write.csv(results_df, 'wikipathways_enrichment.csv', row.names = FALSE)
```

### bio-systems-biology-context-specific-models
**用途**: 
```
def create_tissue_model(generic_model, gtex_expression, tissue='liver'):
    '''Create tissue-specific model from GTEx expression data

    GTEx provides median TPM for 54 human tissues.
    Download from: https://gtexportal.org/home/datasets
    '''
    import pandas as pd

    # Load GTEx median expression
    gtex = pd.read_csv(gtex_expression, sep='\t')

    # Extract tissue column
    tissue_col = [c for c in gtex.columns if tissue.lower() in c.lower()][0]
    expression = dict(zip(gtex['ge
# ... (truncated)
```

### bio-systems-biology-flux-balance-analysis
**用途**: 
```
from cobra.flux_analysis import loopless_solution

# Remove thermodynamically infeasible loops
# Important for realistic flux predictions

solution = loopless_solution(model)
```

### bio-systems-biology-gene-essentiality
**用途**: 
```
import cobra
from cobra.flux_analysis import single_gene_deletion

model = cobra.io.load_model('textbook')

# Perform all single gene deletions
# Returns growth rate with each gene knocked out
deletion_results = single_gene_deletion(model)

# deletion_results is a DataFrame with:
# - ids: gene IDs (frozenset)
# - growth: growth rate after deletion
# - status: solver status

# Find essential genes (no growth when deleted)
# Essential: growth < 0.01 (allowing for numerical tolerance)
essential = d
# ... (truncated)
```

### bio-systems-biology-metabolic-reconstruction
**用途**: 
```
# Install CarveMe
pip install carveme

# Basic reconstruction from protein FASTA
carve genome.faa -o model.xml

# Specify output format
carve genome.faa -o model.xml --format sbml
carve genome.faa -o model.json --format json

# Gap-fill for specific media
carve genome.faa -o model.xml --gapfill M9

# Available media: M9, LB, M9[glc], M9[glyc], etc.
```

### bio-systems-biology-model-curation
**用途**: 
```
# Install memote
pip install memote

# Run full quality report
memote report snapshot model.xml --filename report.html

# Quick score
memote run model.xml

# Continuous integration testing
memote run --pytest-args "--tb=short" model.xml
```
