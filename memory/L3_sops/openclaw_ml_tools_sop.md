# 机器学习与数据工具 SOP
> scikit-learn、PyTorch Lightning、SHAP、statsmodels、Polars、Dask、UMAP
> 包含 20 个 OpenClaw skill 的压缩迁移。

---

### dask
**用途**: Distributed computing for larger-than-RAM pandas/NumPy workflows. Use when you need to scale existing pandas/NumPy code beyond memory or across clusters. Best for parallel file processing, distribu...
```
sample = ddf.head(1000)  # Small sample
# Test logic, then scale to full dataset
```

### exploratory-data-analysis
**用途**: Perform comprehensive exploratory data analysis on scientific data files across 200+ file formats. This skill should be used when analyzing any scientific data file to understand its structure, con...
```
try:
    from Bio import SeqIO
except ImportError:
    print("Install Biopython: uv pip install biopython")
```

### markitdown
**用途**: Convert files and office documents to Markdown. Supports PDF, DOCX, PPTX, XLSX, images (with OCR), audio (with transcription), HTML, CSV, JSON, XML, ZIP, YouTube URLs, EPubs and more.
```
pip install 'markitdown[pdf]'  # For PDF support
```

### networkx
**用途**: Comprehensive toolkit for creating, analyzing, and visualizing complex networks and graphs in Python. Use when working with network/graph data structures, analyzing relationships between entities, ...
```
G = nx.erdos_renyi_graph(n=100, p=0.1, seed=42)
pos = nx.spring_layout(G, seed=42)
```

### polars
**用途**: Fast in-memory DataFrame library for datasets that fit in RAM. Use when pandas is too slow but data still fits in memory. Lazy evaluation, parallel execution, Apache Arrow backend. Best for 1-100GB...
```
uv pip install polars
```

### profile-report
**用途**: Unified personal genomic profile report — reads a PatientProfile JSON and synthesizes all skill results into a single "Your Genomic Profile" document.
```
python clawbio.py run profile --demo
```

### pyhealth
**用途**: Comprehensive healthcare AI toolkit for developing, testing, and deploying machine learning models with clinical data. This skill should be used when working with electronic health records (EHR), c...
```
uv pip install pyhealth
```

### pymc-bayesian-modeling
**用途**: Bayesian modeling with PyMC. Build hierarchical models, MCMC (NUTS), variational inference, LOO/WAIC comparison, posterior checks, for probabilistic programming and inference.
```
idata = pm.sample(draws=2000, tune=1000, chains=4, target_accept=0.9)
```

### pymoo
**用途**: Multi-objective optimization framework. NSGA-II, NSGA-III, MOEA/D, Pareto fronts, constraint handling, benchmarks (ZDT, DTLZ), for engineering design and optimization problems.
```
uv pip install pymoo
```

### pytorch-lightning
**用途**: Deep learning framework (PyTorch Lightning). Organize PyTorch code into LightningModules, configure Trainers for multi-GPU/TPU, implement data pipelines, callbacks, logging (W&B, TensorBoard), dist...
```
trainer = L.Trainer(max_epochs=10, accelerator="gpu", devices=2)
   trainer.fit(model, train_loader)  # or trainer.fit(model, datamodule=dm)
```

### scikit-learn
**用途**: Machine learning in Python with scikit-learn. Use when working with supervised learning (classification, regression), unsupervised learning (clustering, dimensionality reduction), model evaluation,...
```
python scripts/clustering_analysis.py
```

### shap
**用途**: Model interpretability and explainability using SHAP (SHapley Additive exPlanations). Use this skill when explaining machine learning model predictions, computing feature importance, generating SHA...
```
# Basic installation
uv pip install shap

# With visualization dependencies
uv pip install shap matplotlib

# Latest version
uv pip install -U shap
```

### simpy
**用途**: Process-based discrete-event simulation framework in Python. Use this skill when building simulations of systems with processes, queues, resources, and time-based events such as manufacturing syste...
```
import simpy.rt

env = simpy.rt.RealtimeEnvironment(factor=1.0)  # 1:1 time mapping
# factor=0.5 means 1 sim unit = 0.5 seconds (2x faster)
```

### statistical-analysis
**用途**: Statistical analysis toolkit. Hypothesis tests (t-test, ANOVA, chi-square), regression, correlation, Bayesian stats, power analysis, assumption checks, APA reporting, for academic research.
```
from pingouin import compute_effsize_from_t

# For t-test
d, ci = compute_effsize_from_t(
    t_statistic,
    nx=len(group1),
    ny=len(group2),
    eftype='cohen'
)
print(f"d = {d:.2f}, 95% CI [{ci[0]:.2f}, {ci[1]:.2f}]")
```
**注意**: when possible to distinguish confirmatory from exploratory; before interpreting results; with confidence intervals

### statsmodels
**用途**: Statistical modeling toolkit. OLS, GLM, logistic, ARIMA, time series, hypothesis tests, diagnostics, AIC/BIC, for rigorous statistical inference and econometric analysis.
```
# Find information about specific models
grep -r "Quantile Regression" references/

# Find diagnostic tests
grep -r "Breusch-Pagan" references/stats_diagnostics.md

# Find time series guidance
grep -r "SARIMAX" references/time_series.md
```

### timesfm-forecasting
**用途**: Zero-shot time series forecasting with Google's TimesFM foundation model. Use for any univariate time series (sales, sensors, energy, vitals, weather) without training a custom model. Supports CSV/...
```
python scripts/check_system.py
```

### torch-geometric
**用途**: Graph Neural Networks (PyG). Node/graph classification, link prediction, GCN, GAT, GraphSAGE, heterogeneous graphs, molecular property prediction, for geometric deep learning.
```
uv pip install torch_geometric
```

### transformers
**用途**: This skill should be used when working with pre-trained transformer models for natural language processing, computer vision, audio, or multimodal tasks. Use for text generation, classification, que...
```
uv pip install timm pillow
```

### umap-learn
**用途**: UMAP dimensionality reduction. Fast nonlinear manifold learning for 2D/3D visualization, clustering preprocessing (HDBSCAN), supervised/parametric UMAP, for high-dimensional data.
```
uv pip install umap-learn
```

### vaex
**用途**: Use this skill for processing and analyzing large tabular datasets (billions of rows) that exceed available RAM. Vaex excels at out-of-core DataFrame operations, lazy evaluation, fast aggregations,...
```
# No memory overhead - computed on the fly
df['age_squared'] = df.age ** 2
df['full_name'] = df.first_name + ' ' + df.last_name
df['is_adult'] = df.age >= 18
```
**注意**: for optimal performance with large datasets; instead of materializing data to save memory; using `delay=True` when performing multiple calculations
