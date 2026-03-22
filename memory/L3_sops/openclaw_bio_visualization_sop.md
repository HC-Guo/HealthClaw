# gptomics 生物数据可视化 SOP
> 热图、火山图、PCA/UMAP、GO 富集图、生存曲线、circos
> 包含 11 个 OpenClaw skill 的压缩迁移。

---

### bio-data-visualization-circos-plots
**用途**: 
```
pip install pyCircos
```

### bio-data-visualization-color-palettes
**用途**: 
```
import seaborn as sns

sns.heatmap(data, cmap='RdBu_r', center=0, vmin=-2, vmax=2)
```

### bio-data-visualization-genome-browser-tracks
**用途**: 
```
[hic_matrix]
file = matrix.cool
title = Hi-C
height = 10
depth = 1000000
min_value = 0
max_value = 100
transform = log1p
colormap = RdYlBu_r
show_masked_bins = false
```

### bio-data-visualization-genome-tracks
**用途**: 
```
# pyGenomeTracks with BED regions
pyGenomeTracks --tracks tracks.ini --BED regions.bed \
    --outFileName multi_region.pdf --dpi 150
```

### bio-data-visualization-ggplot2-fundamentals
**用途**: 
```
library(ggplot2)

# Grammar of graphics: data + aesthetics + geometry
ggplot(data, aes(x = var1, y = var2)) +
    geom_point()
```

### bio-data-visualization-heatmaps-clustering
**用途**: 
```
# pheatmap to file
pheatmap(mat, filename = 'heatmap.pdf', width = 8, height = 10)

# ComplexHeatmap to file
pdf('heatmap.pdf', width = 8, height = 10)
draw(ht)
dev.off()
```

### bio-data-visualization-interactive-visualization
**用途**: 
```
# plotly - works automatically in Jupyter
fig.show()

# bokeh
from bokeh.io import output_notebook, show
output_notebook()
show(p)
```

### bio-data-visualization-multipanel-figures
**用途**: 
```
# Python
fig.savefig('figure1.pdf', bbox_inches='tight')
fig.savefig('figure1.png', dpi=300, bbox_inches='tight')
```

### bio-data-visualization-specialized-omics-plots
**用途**: 
```
library(survival)
library(survminer)

fit <- survfit(Surv(time, status) ~ group, data = df)
ggsurvplot(fit, data = df, risk.table = TRUE, pval = TRUE,
           palette = c('#4DBBD5', '#E64B35'),
           legend.labs = c('Low', 'High'))
```

### bio-data-visualization-upset-plots
**用途**: 
```
# Python
fig = plt.figure(figsize=(10, 6))
upset.plot(fig=fig)
plt.savefig('upset.pdf', bbox_inches='tight')
plt.savefig('upset.png', dpi=300, bbox_inches='tight')
```

### bio-data-visualization-volcano-customization
**用途**: 
```
# Python
plt.savefig('volcano.pdf', bbox_inches='tight')
plt.savefig('volcano.png', dpi=300, bbox_inches='tight')
```
