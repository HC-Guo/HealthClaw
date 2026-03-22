# gptomics 报告生成 SOP
> 自动化 QC 报告、Jupyter/Quarto/RMarkdown 报告、图片导出
> 包含 5 个 OpenClaw skill 的压缩迁移。

---

### bio-reporting-automated-qc-reports
**用途**: 
```
from multiqc import run as multiqc_run

# Run programmatically
multiqc_run(analysis_dir='results/', outdir='qc_report/')
```

### bio-reporting-figure-export
**用途**: 
```
library(ggplot2)

p <- ggplot(data, aes(x, y)) + geom_point() +
  theme_classic(base_size = 8) +
  theme(text = element_text(family = 'Arial'))

# PDF for vector graphics
ggsave('figure1.pdf', p, width = 3.5, height = 3, units = 'in')

# High-res PNG
ggsave('figure1.png', p, width = 3.5, height = 3, units = 'in', dpi = 300)

# TIFF (some journals require)
ggsave('figure1.tiff', p, width = 3.5, height = 3, units = 'in',
       dpi = 300, compression = 'lzw')
```

### bio-reporting-jupyter-reports
**用途**: 
```
# Parameters (tag this cell as "parameters")
input_file = 'default.csv'
output_dir = 'results/'
fdr_threshold = 0.05
```
**注意**: Keep analysis code in cells, explanatory text in markdown; Use parameters for all configurable values; Include version information and timestamps

### bio-reporting-quarto-reports
**用途**: 
```

```

### bio-reporting-rmarkdown-reports
**用途**: 
```

```
