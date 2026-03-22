# 数据科学与可视化 SOP
> 统计分析、数据处理、科学可视化、公共卫生、时序分析
> 包含 13 个 OpenClaw skill 的压缩迁移。

---

### ai-analyzer
**用途**: AI驱动的综合健康分析系统，整合多维度健康数据、识别异常模式、预测健康风险、提供个性化建议。支持智能问答和AI健康报告生成。
```
const profile = readFile('data/profile.json');
```

### bayesian-optimizer
**用途**: 
```
python3 Skills/Mathematics/Probability_Statistics/bayesian_optimization.py \
    --history "[[20, 7.0, 0.5], [25, 6.5, 0.6]]" \
    --bounds "[[10, 40], [5, 9]]" \
    --output next_experiment.json
```

### bio-de-visualization
**用途**: Visualize differential expression results using DESeq2/edgeR built-in functions. Covers plotMA, plotDispEsts, plotCounts, plotBCV, sample distance heatmaps, and p-value histograms. Use when visuali...
```
plotDispEsts(dds, main = 'Dispersion Estimates')
```

### data-stats-analysis
**用途**: Perform statistical tests, hypothesis testing, correlation analysis, and multiple testing corrections using scipy and statsmodels. Works with ANY LLM provider (GPT, Gemini, Claude, etc.).
```
if p_value < 0.001:
    print(f"p < 0.001")
else:
    print(f"p = {p_value:.4f}")
```

### data-transform
**用途**: Transform, clean, reshape, and preprocess data using pandas and numpy. Works with ANY LLM provider (GPT, Gemini, Claude, etc.).
```
df_combined = pd.concat([df1, df2], ignore_index=True)
```

### data-visualization-biomedical
**用途**: 
```
def save_figure(fig, filename, formats=['pdf', 'png', 'svg']):
    """Save in multiple formats for journals."""
    for fmt in formats:
        fig.savefig(f"{filename}.{fmt}", format=fmt, dpi=300, 
                    bbox_inches='tight', facecolor='white', edgecolor='none')
    print(f"Saved: {filename}.{{{'|'.join(formats)}}}")
```

### data-visualization-expert
**用途**: 
**触发条件**: **Reports:** Summarizing key metrics or KPIs.; **Exploration:** Initial data analysis (EDA) to find trends/outliers.; **Publication:** Generating figures for papers or presentations.; **Comparison:** Comparing models, cohorts, or experimental groups.
```
# Agent prompt:
"Visualize the distribution of 'Age' vs 'Income' from customers.csv"
# Triggers generation of `plot_age_income.py` using Seaborn scatterplot.
```

### data-viz-plots
**用途**: Create publication-quality plots and visualizations using matplotlib and seaborn. Works with ANY LLM provider (GPT, Gemini, Claude, etc.).
```
ax.scatter(x, y, s=5, alpha=0.3, edgecolors='none')
```

### geopandas
**用途**: Python library for working with geospatial vector data including shapefiles, GeoJSON, and GeoPackage files. Use when working with geographic data for spatial analysis, geometric operations, coordin...
```
uv pip install geopandas
```
**注意**: before spatial operations; for area and distance calculations; before spatial joins or overlays

### matplotlib
**用途**: Low-level plotting library for full customization. Use when you need fine-grained control over every plot element, creating novel plot types, or integrating with specific scientific workflows. Expo...
```
python scripts/plot_template.py
```

### plotly
**用途**: Interactive visualization library. Use when you need hover info, zoom, pan, or web-embeddable charts. Best for dashboards, exploratory analysis, and presentations. For static publication figures us...
```
uv pip install dash
```

### scientific-visualization
**用途**: Create publication figures with matplotlib/seaborn/plotly. Multi-panel layouts, error bars, significance markers, colorblind-safe, export PDF/EPS/TIFF, for journal-ready scientific plots.
```
sns.set_palette('colorblind')
```

### seaborn
**用途**: Statistical visualization with pandas integration. Use for quick exploration of distributions, relationships, and categorical comparisons with attractive defaults. Best for box plots, violin plots,...
```
sns.heatmap(correlation_matrix, cmap='vlag', center=0)
```
