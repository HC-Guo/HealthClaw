# gptomics ML 与工作流 SOP
> 生物信息 ML、工作流管理、ADMET 预测
> 包含 44 个 OpenClaw skill 的压缩迁移。

---

### bio-admet-prediction
**用途**: Predicts ADMET properties using ADMETlab 3.0 API or DeepChem models. Estimates bioavailability, CYP inhibition, hERG liability, and 119 toxicity endpoints with uncertainty quantification. Filters f...
```
import requests
import pandas as pd

def predict_admet_batch(smiles_list, api_url='https://admetlab3.scbdd.com/api/predict'):
    '''
    Predict ADMET properties using ADMETlab 3.0 API.

    Note: SwissADME has NO API - it is web-only.
    '''
    payload = {
        'smiles': smiles_list
    }

    response = requests.post(api_url, json=payload)
    response.raise_for_status()

    return pd.DataFrame(response.json())

# Example usage
# smiles = ['CCO', 'c1ccccc1O', 'CC(=O)Oc1ccccc1C(=O)O']
# 
# ... (truncated)
```

### bio-machine-learning-atlas-mapping
**用途**: 
```
import scanpy as sc

# Combine reference and query for visualization
adata_combined = adata_ref.concatenate(adata_query, batch_key='dataset', batch_categories=['reference', 'query'])

# Use latent space for neighbors/UMAP
sc.pp.neighbors(adata_combined, use_rep='X_scVI')
sc.tl.umap(adata_combined)
sc.pl.umap(adata_combined, color=['dataset', 'cell_type'], save='_transfer.png')
```

### bio-machine-learning-biomarker-discovery
**用途**: 
```
from mrmr import mrmr_classif

# K: Number of features to select; start with 50-100 for omics
selected_features = mrmr_classif(X=X, y=pd.Series(y), K=50)
X_selected = X[selected_features]
```

### bio-machine-learning-model-validation
**用途**: 
```
from sklearn.model_selection import LeaveOneOut, cross_val_predict

# Use for very small datasets (n < 30)
loo = LeaveOneOut()
y_pred = cross_val_predict(pipe, X, y, cv=loo, method='predict_proba')[:, 1]
auc = roc_auc_score(y, y_pred)
print(f'LOO AUC: {auc:.3f}')
```

### bio-machine-learning-omics-classifiers
**用途**: 
```
import pandas as pd

importances = pipe.named_steps['clf'].feature_importances_
feature_imp = pd.DataFrame({'feature': X.columns, 'importance': importances})
feature_imp = feature_imp.sort_values('importance', ascending=False).head(20)
```

### bio-machine-learning-prediction-explanation
**用途**: 
```
# Shows how SHAP value varies with feature value
# Automatically colors by interacting feature
shap.plots.scatter(shap_values[:, 'GENE1'], color=shap_values, show=False)
plt.savefig('shap_dependence.png', dpi=150, bbox_inches='tight')
```

### bio-machine-learning-survival-analysis
**用途**: 
```
# Test PH assumption
cph.check_assumptions(df, p_value_threshold=0.05, show_plots=True)
```

### bio-workflow-management-cwl-workflows
**用途**: 
```
# Run with Docker
cwltool --docker workflow.cwl job.yaml

# Run with Singularity
cwltool --singularity workflow.cwl job.yaml
```

### bio-workflow-management-nextflow-pipelines
**用途**: 
```
process ALIGN {
    label 'process_high'
    // ...
}
```

### bio-workflow-management-snakemake-workflows
**用途**: 
```
# Run with Singularity
snakemake --use-singularity --singularity-args "-B /data"
```

### bio-workflow-management-wdl-workflows
**用途**: 
```
{
    "rnaseq.fastq_1": "data/sample1_R1.fq.gz",
    "rnaseq.fastq_2": "data/sample1_R2.fq.gz",
    "rnaseq.salmon_index": "ref/salmon_index",
    "rnaseq.threads": 8
}
```

### bio-workflows-atacseq-pipeline
**用途**: 
```
# Convert to BED and shift
bedtools bamtobed -i aligned/${sample}.dedup.bam | \
    awk 'BEGIN{OFS="\t"} {if($6=="+"){$2=$2+4} else if($6=="-"){$3=$3-5} print}' | \
    sort -k1,1 -k2,2n > aligned/${sample}.shifted.bed
```

### bio-workflows-biomarker-pipeline
**用途**: 
```
import pandas as pd
import joblib

# Save biomarker panel
feature_names = X_train.columns[selected_idx].tolist()
pd.DataFrame({'feature': feature_names}).to_csv('biomarker_panel.csv', index=False)

# Save model and scaler for deployment
joblib.dump(clf, 'biomarker_classifier.joblib')
joblib.dump(scaler, 'feature_scaler.joblib')
```

### bio-workflows-chipseq-pipeline
**用途**: 
```
FASTQ files (IP + Input)
    |
    v
[1. QC & Trimming] -----> fastp
    |
    v
[2. Alignment] ---------> Bowtie2
    |
    v
[3. BAM Processing] ----> sort, markdup, filter
    |
    v
[4. Peak Calling] ------> MACS3
    |
    v
[5. QC] ----------------> FRiP, fingerprint plots
    |
    v
[6. Annotation] --------> ChIPseeker
    |
    v
Annotated peaks + QC report
```

### bio-workflows-clip-pipeline
**用途**: 
```
FASTQ → QC → UMI extract → Trim adapters → Align → Filter → Dedup → Peak call → Annotate → Motifs
```

### bio-workflows-cnv-pipeline
**用途**: 
```
# For each sample
for bam in *.bam; do
    sample=$(basename $bam .bam)

    # Target coverage
    cnvkit.py coverage $bam targets.bed \
        -o coverage/${sample}.targetcoverage.cnn

    # Antitarget coverage
    cnvkit.py coverage $bam antitargets.bed \
        -o coverage/${sample}.antitargetcoverage.cnn
done
```

### bio-workflows-crispr-editing-pipeline
**用途**: 
```
pip install crisprscan biopython pandas numpy matplotlib

conda install -c bioconda primer3-py cas-offinder

# Python packages for scoring
pip install crisprtools  # if available
```

### bio-workflows-crispr-screen-pipeline
**用途**: 
```
# For enrichment screens (e.g., drug resistance)
mageck test \
    -k counts.txt \
    -t Resistant_Rep1,Resistant_Rep2 \
    -c Sensitive \
    -n positive_screen \
    --gene-lfc-method alphamedian
```

### bio-workflows-cytometry-pipeline
**用途**: 
```
# CyTOF-specific settings
sce <- prepData(fs, panel, md,
                transform = TRUE,
                cofactor = 5,  # CyTOF uses cofactor 5
                FACS = FALSE)  # Not flow cytometry

# Bead normalization should be done upstream (Fluidigm software)
```

### bio-workflows-expression-to-pathways
**用途**: 
```
library(ReactomePA)

reactome <- enrichPathway(gene = sig_entrez$ENTREZID,
                          organism = 'human',
                          pvalueCutoff = 0.05,
                          readable = TRUE)
```

### bio-workflows-fastq-to-variants
**用途**: 
```
samtools flagstat aligned/${sample}.bam
```

### bio-workflows-genome-assembly-pipeline
**用途**: 
```
# NanoPlot for long-read QC
NanoPlot --fastq reads.fastq.gz \
    --outdir nanoplot_output \
    --threads 8
```

### bio-workflows-gwas-pipeline
**用途**: 
```
# Calculate principal components
plink2 --bfile study_pruned \
    --pca 10 \
    --out study_pca

# The eigenvec file contains PCs for use as covariates
```

### bio-workflows-hic-pipeline
**用途**: 
```
import cooler
import cooltools

# Load matrix
clr = cooler.Cooler('sample.mcool::resolutions/10000')

# Balance (ICE normalization)
cooltools.balance_cooler(clr, store=True, mad_max=5)

# Or via command line
# cooler balance sample.mcool::resolutions/10000
```

### bio-workflows-imc-pipeline
**用途**: 
```
# Spatial interactions with tumor
tumor_cells = adata[adata.obs['cell_type'] == 'Tumor'].obs_names
sq.gr.ligrec(adata, cluster_key='cell_type', source_groups=['Tumor'],
             target_groups=['T cells', 'Macrophages'])
```

### bio-workflows-longread-sv-pipeline
**用途**: 
```
samtools flagstat aligned.bam
samtools depth -a aligned.bam | awk '{sum+=$3} END {print "Average coverage:",sum/NR}'
```

### bio-workflows-merip-pipeline
**用途**: 
```
FASTQ → QC → Align IP+Input → Peak calling → Annotation → Differential → Visualization
```

### bio-workflows-metabolic-modeling-pipeline
**用途**: 
```
pip install cobra carveme memote escher pandas numpy matplotlib seaborn

conda install -c bioconda diamond
```

### bio-workflows-metabolomics-pipeline
**用途**: 
```
# Adjust peak width for lipids
cwp_lipid <- CentWaveParam(
    peakwidth = c(10, 60),  # Broader peaks
    ppm = 15,
    snthresh = 5
)

# Use LipidMaps for annotation
```

### bio-workflows-metagenomics-pipeline
**用途**: 
```
# Classify reads
for sample in sample1 sample2 sample3; do
    kraken2 --db kraken2_db \
        --threads 8 \
        --paired \
        --report kraken/${sample}.report \
        --output kraken/${sample}.output \
        host_removed/${sample}_R1.fq.gz \
        host_removed/${sample}_R2.fq.gz
done
```

### bio-workflows-methylation-pipeline
**用途**: 
```
deduplicate_bismark \
    --bam \
    -p \
    -o deduplicated/ \
    aligned/sample_R1_val_1_bismark_bt2_pe.bam
```

### bio-workflows-microbiome-pipeline
**用途**: 
```
# V3-V4 (~460bp): truncLen = c(280, 200)
# V4 (~253bp): truncLen = c(240, 160)
# V1-V3 (~500bp): truncLen = c(260, 220)
```

### bio-workflows-multi-omics-pipeline
**用途**: 
```
# MOFA+ for single-cell
library(MOFA2)
mofa <- create_mofa_from_Seurat(seurat_obj, groups = 'cell_type',
                                 assays = c('RNA', 'ATAC'))
```

### bio-workflows-multiome-pipeline
**用途**: 
```
# QC metrics
seurat_obj[['percent.mt']] <- PercentageFeatureSet(seurat_obj, pattern = '^MT-')

# Filter
seurat_obj <- subset(seurat_obj,
    nCount_RNA > 1000 &
    nCount_RNA < 25000 &
    percent.mt < 20
)

# Normalize RNA
seurat_obj <- SCTransform(seurat_obj, assay = 'RNA', verbose = FALSE)

# PCA
seurat_obj <- RunPCA(seurat_obj, assay = 'SCT', verbose = FALSE)
```

### bio-workflows-neoantigen-pipeline
**用途**: 
```
pip install pvactools mhcflurry vatools

mhcflurry-downloads fetch

conda install -c bioconda vep arcashla optitype
```

### bio-workflows-outbreak-pipeline
**用途**: 
```
conda install -c bioconda mlst abricate snippy iqtree fasttree

pip install treetime transphylo biopython pandas matplotlib

# R packages for TransPhylo
Rscript -e "install.packages('TransPhylo')"
```

### bio-workflows-proteomics-pipeline
**用途**: 
```
# Load DIA-NN report
diann <- read.delim('report.tsv')

# Pivot to matrix
library(tidyr)
protein_matrix <- diann %>%
    select(Protein.Group, Run, PG.MaxLFQ) %>%
    pivot_wider(names_from = Run, values_from = PG.MaxLFQ)

# Then proceed with normalization and limma
```

### bio-workflows-riboseq-pipeline
**用途**: 
```
FASTQ → Preprocessing → rRNA removal → Alignment → P-site → TE → ORF calling
```

### bio-workflows-rnaseq-to-de
**用途**: 
```
# Count reads per gene
featureCounts -T 8 -p --countReadPairs \
    -a genes.gtf \
    -o counts.txt \
    aligned/*_Aligned.sortedByCoord.out.bam
```

### bio-workflows-scrnaseq-pipeline
**用途**: 
```
# SCTransform (recommended for most analyses)
seurat_obj <- SCTransform(seurat_obj, vars.to.regress = 'percent.mt', verbose = FALSE)
```

### bio-workflows-smrna-pipeline
**用途**: 
```
FASTQ → cutadapt trim → miRDeep2 → Quantification → DESeq2 → Target prediction
```

### bio-workflows-somatic-variant-pipeline
**用途**: 
```
gatk LearnReadOrientationModel \
    -I f1r2.tar.gz \
    -O read-orientation-model.tar.gz
```

### bio-workflows-spatial-pipeline
**用途**: 
```
# Gene expression in space
genes = ['EPCAM', 'VIM', 'PTPRC', 'COL1A1']
sc.pl.spatial(adata, color=genes, ncols=2, spot_size=1.5, cmap='viridis')
plt.savefig('marker_genes_spatial.pdf')

# Cluster markers in space
sc.tl.rank_genes_groups(adata, 'leiden', method='wilcoxon')
sc.pl.rank_genes_groups_dotplot(adata, n_genes=5)
plt.savefig('cluster_markers.pdf')

# Save
adata.write('spatial_analyzed.h5ad')
```

### bio-workflows-tcr-pipeline
**用途**: 
```
FASTQ → MiXCR align → Assemble → Export → VDJtools diversity → Visualization
```
