# gptomics 蛋白质组与代谢组 SOP
> 质谱蛋白质组、成像质谱、代谢组学
> 包含 23 个 OpenClaw skill 的压缩迁移。

---

### bio-imaging-mass-cytometry-cell-segmentation
**用途**: Cell segmentation from multiplexed tissue images. Covers deep learning (Cellpose, Mesmer) and classical approaches for nuclear and whole-cell segmentation. Use when extracting single-cell data from...
```
from skimage.segmentation import expand_labels

# If only nuclear segmentation available, expand to approximate cells
nuclear_masks = masks  # From nuclear segmentation
expanded_masks = expand_labels(nuclear_masks, distance=10)

print(f'Expanded masks from nuclei')
```

### bio-imaging-mass-cytometry-data-preprocessing
**用途**: Load and preprocess imaging mass cytometry (IMC) and MIBI data. Covers MCD/TIFF handling, hot pixel removal, and image normalization. Use when starting IMC analysis from raw MCD files or preparing ...
```
# panel.csv
channel,name,keep,ilastik
1,DNA1,1,1
2,CD45,1,1
3,CD3,1,0
4,CD8,1,0
5,CD4,1,0
```

### bio-imaging-mass-cytometry-interactive-annotation
**用途**: Interactive cell type annotation for IMC data. Covers napari-based annotation, marker-guided labeling, training data generation, and annotation validation. Use when manually annotating cell types f...
```
import napari
import numpy as np
from skimage import io
import pandas as pd

# Load IMC image stack
image_stack = io.imread('imc_image.tiff')  # (C, H, W)
segmentation_mask = io.imread('cell_segmentation.tiff')

# Create napari viewer
viewer = napari.Viewer()

# Add channels as separate layers for visualization
channel_names = ['CD45', 'CD3', 'CD68', 'panCK', 'DNA']
for i, name in enumerate(channel_names):
    viewer.add_image(image_stack[i], name=name, visible=False, colormap='gray', blending='
# ... (truncated)
```

### bio-imaging-mass-cytometry-phenotyping
**用途**: Cell type assignment from marker expression in IMC data. Covers manual gating, clustering, and automated classification approaches. Use when assigning cell types to segmented IMC cells based on pro...
```
# Add annotations to adata
adata.write('imc_phenotyped.h5ad')

# Export cell types
adata.obs[['cell_id', 'cell_type', 'centroid_x', 'centroid_y']].to_csv('cell_phenotypes.csv', index=False)
```

### bio-imaging-mass-cytometry-quality-metrics
**用途**: Quality metrics for IMC data including signal-to-noise, channel correlation, tissue integrity, and acquisition QC. Use when assessing data quality before analysis or troubleshooting problematic acq...
```
def assess_dynamic_range(channel, percentiles=(1, 99)):
    '''Assess if channel uses full dynamic range.'''
    low, high = np.percentile(channel, percentiles)
    channel_range = high - low
    max_possible = channel.max()

    utilized = channel_range / max_possible if max_possible > 0 else 0

    return {
        'range_low': low,
        'range_high': high,
        'range_utilized': utilized,
        'adequate': utilized > 0.1
    }

for i, name in enumerate(channel_names):
    dr = assess_
# ... (truncated)
```

### bio-imaging-mass-cytometry-spatial-analysis
**用途**: Spatial analysis of cell neighborhoods and interactions in IMC data. Covers neighbor graphs, spatial statistics, and interaction testing. Use when analyzing spatial relationships between cell types...
```
# Permutation test for interactions
sq.gr.interaction_matrix(adata, cluster_key='cell_type', normalized=True)

# Get interaction matrix
interaction = adata.uns['cell_type_interactions']
```

### bio-metabolomics-lipidomics
**用途**: Specialized lipidomics analysis for lipid identification, quantification, and pathway interpretation. Covers LC-MS lipidomics with LipidSearch, MS-DIAL, and LipidMaps annotation. Use when analyzing...
```
# Parse lipid names to extract class, chain info
lipid_data <- annotate_lipids(lipid_data)

# View lipid classes
table(rowData(lipid_data)$Class)

# Chain length and saturation
plot_chain_distribution(lipid_data)
```

### bio-metabolomics-metabolite-annotation
**用途**: Metabolite identification from m/z and retention time. Covers database matching, MS/MS spectral matching, and confidence level assignment. Use when assigning compound identities to detected feature...
```
# Molecular formula and structure prediction
sirius \
    --input sample.ms \
    --output sirius_results \
    --database hmdb \
    formula \
    fingerid

# Output structure:
# sirius_results/
#   compound_1/
#     formula_candidates.tsv
#     fingerid_candidates.tsv
```

### bio-metabolomics-msdial-preprocessing
**用途**: MS-DIAL-based metabolomics preprocessing as alternative to XCMS. Covers peak detection, alignment, annotation, and export for downstream analysis. Use when processing MS-DIAL output files for R/Pyt...
```
# MS-DIAL console application for batch processing
# Available on Windows

# Create parameter file (msdial_param.txt)
# See MS-DIAL documentation for all parameters

# Run MS-DIAL console
MsdialConsoleApp.exe lcmsdda -i input_folder -o output_folder -m msdial_param.txt
```

### bio-metabolomics-normalization-qc
**用途**: Quality control and normalization for metabolomics data. Covers QC-based correction, batch effect removal, and data transformation methods. Use when correcting technical variation in metabolomics d...
```
# Simple sum normalization
tic_normalize <- function(data) {
    row_sums <- rowSums(data, na.rm = TRUE)
    normalized <- data / row_sums * median(row_sums)
    return(normalized)
}

data_tic <- tic_normalize(data)
```

### bio-metabolomics-pathway-mapping
**用途**: Map metabolites to biological pathways using KEGG, Reactome, and MetaboAnalyst. Perform pathway enrichment and topology analysis. Use when interpreting metabolomics results in the context of bioche...
```
library(ReactomePA)
library(clusterProfiler)

# Convert to Reactome IDs (if available)
reactome_ids <- c('R-HSA-70171', 'R-HSA-1428517')  # Example

# Enrichment
enriched <- enrichPathway(gene = reactome_ids, organism = 'human', pvalueCutoff = 0.05)
print(enriched)
```

### bio-metabolomics-statistical-analysis
**用途**: Statistical analysis for metabolomics data. Covers univariate testing, multivariate methods (PCA, PLS-DA), and biomarker discovery. Use when identifying differentially abundant metabolites or build...
```
library(ropls)

# OPLS-DA
oplsda <- opls(data, groups, predI = 1, orthoI = NA)

# Summary
print(oplsda)

# Scores plot
plot(oplsda, typeVc = 'x-score')

# S-plot (loadings vs correlation)
plot(oplsda, typeVc = 'x-loading')

# VIP
vip_scores <- getVipVn(oplsda)
top_vip <- sort(vip_scores, decreasing = TRUE)[1:20]
```

### bio-metabolomics-targeted-analysis
**用途**: Targeted metabolomics analysis using MRM/SRM with standard curves. Covers absolute quantification, method validation, and quality assessment. Use when quantifying specific metabolites using calibra...
```
# Final results table
results_final <- data.frame(
    sample = samples$sample,
    concentration_nM = round(samples$concentration, 2),
    concentration_uM = round(samples$concentration / 1000, 4),
    cv_percent = round(samples$cv, 1),
    qc_flag = ifelse(samples$cv > 20, 'FAIL', 'PASS')
)

write.csv(results_final, 'targeted_results.csv', row.names = FALSE)
```

### bio-metabolomics-xcms-preprocessing
**用途**: XCMS3 workflow for LC-MS/MS metabolomics preprocessing. Covers peak detection, retention time alignment, correspondence (grouping), and gap filling. Use when processing raw LC-MS data into a featur...
```
# MatchedFilter for profile/continuum data
mfp <- MatchedFilterParam(
    binSize = 0.1,
    fwhm = 30,
    snthresh = 10,
    step = 0.1,
    mzdiff = 0.8
)

xdata_profile <- findChromPeaks(raw_data, param = mfp)
```

### bio-proteomics-data-import
**用途**: Load and parse mass spectrometry data formats including mzML, mzXML, and quantification tool outputs like MaxQuant proteinGroups.txt. Use when starting a proteomics analysis with raw or processed M...
```
library(MSnbase)

raw_data <- readMSData('sample.mzML', mode = 'onDisk')
spectra <- spectra(raw_data)
header_info <- fData(raw_data)
```

### bio-proteomics-dia-analysis
**用途**: Data-independent acquisition (DIA) proteomics analysis with DIA-NN and other tools. Use when analyzing DIA mass spectrometry data with library-free or library-based workflows for deep proteome prof...
```
# DIA-NN MBR is automatic with --reanalyse flag
# First pass: identifies peptides per run
# Second pass: transfers IDs between runs

diann \
    --f *.mzML \
    --lib library.tsv \
    --reanalyse \
    --out report_mbr.tsv
```

### bio-proteomics-differential-abundance
**用途**: Statistical testing for differentially abundant proteins between conditions. Covers limma and MSstats workflows with multiple testing correction. Use when identifying proteins with significant abun...
```
# Volcano plot
library(ggplot2)

ggplot(results, aes(x = log2FC, y = -log10(adj.P.Val))) +
    geom_point(aes(color = significant), alpha = 0.6) +
    geom_hline(yintercept = -log10(0.05), linetype = 'dashed') +
    geom_vline(xintercept = c(-1, 1), linetype = 'dashed') +
    scale_color_manual(values = c('grey', 'red')) +
    theme_minimal()
```

### bio-proteomics-peptide-identification
**用途**: Peptide-spectrum matching and protein identification from MS/MS data. Use when identifying peptides from tandem mass spectra. Covers database searching, spectral library matching, and FDR estimatio...
```
library(MSnbase)

# Read mzIdentML results
psms <- readMzIdData('results.mzid')

# Filter to 1% FDR
psms_filtered <- psms[psms$qvalue <= 0.01, ]

# Unique peptides per protein
peptide_counts <- table(psms_filtered$accession)
```

### bio-proteomics-protein-inference
**用途**: Protein grouping and inference from peptide identifications. Use when resolving protein ambiguity from shared peptides. Handles protein groups and protein-level FDR control using parsimony and prob...
```
library(ProteinInference)

# From peptide-protein mapping
protein_groups <- infer_proteins(
    peptides = psm_data$peptide,
    proteins = psm_data$protein,
    method = 'parsimony'
)

# Count unique peptides per group
protein_groups$n_unique <- sapply(protein_groups$peptides, function(p) {
    sum(sapply(p, function(pep) length(peptide_to_protein[[pep]]) == 1))
})
```

### bio-proteomics-proteomics-qc
**用途**: Quality control and assessment for proteomics data. Use when evaluating proteomics data quality before downstream analysis. Covers sample metrics, missing value patterns, replicate correlation, bat...
```
library(limma)
library(ggplot2)

# Intensity distribution
plotDensities(protein_matrix, legend = FALSE, main = 'Intensity Distributions')

# MA plots between samples
for (i in 2:ncol(protein_matrix)) {
    plotMA(protein_matrix[, c(1, i)], main = paste('MA:', colnames(protein_matrix)[i]))
}

# MDS plot (similar to PCA)
plotMDS(protein_matrix, col = as.numeric(sample_info$condition))
```

### bio-proteomics-ptm-analysis
**用途**: Post-translational modification analysis including phosphorylation, acetylation, and ubiquitination. Covers site localization, motif analysis, and quantitative PTM analysis. Use when analyzing phos...
```
PTM_MASSES = {
    'Phosphorylation': 79.966331,      # STY
    'Oxidation': 15.994915,             # M
    'Acetylation': 42.010565,           # K, N-term
    'Methylation': 14.015650,           # KR
    'Dimethylation': 28.031300,         # KR
    'Trimethylation': 42.046950,        # K
    'Ubiquitination': 114.042927,       # K (GlyGly remnant)
    'Deamidation': 0.984016,            # NQ
    'Carbamidomethyl': 57.021464,       # C (fixed mod from IAA)
}
```

### bio-proteomics-quantification
**用途**: Protein quantification from mass spectrometry data including label-free (LFQ, intensity-based), isobaric labeling (TMT, iTRAQ), and metabolic labeling (SILAC) approaches. Use when extracting protei...
```
def spectral_count_normalize(counts, total_spectra):
    '''Normalized spectral abundance factor (NSAF)'''
    # Divide by protein length, then by total
    nsaf = counts / total_spectra
    return nsaf / nsaf.sum()
```

### bio-proteomics-spectral-libraries
**用途**: Build, manage, and search spectral libraries for proteomics. Use when creating or working with spectral libraries for DIA analysis. Covers DDA-based library generation, predicted libraries (Prosit,...
```
# Required columns
PrecursorMz    ProductMz    Annotation    ProteinId    GeneName
PeptideSequence    ModifiedSequence    PrecursorCharge
FragmentCharge    FragmentType    FragmentSeriesNumber
NormalizedRetentionTime    LibraryIntensity
```
