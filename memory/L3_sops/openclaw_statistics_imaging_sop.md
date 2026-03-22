# 统计建模与影像分析 SOP
> 生物医学统计建模、显微镜图像分析、生存分析
> 包含 3 个 OpenClaw skill 的压缩迁移。

---

### scikit-survival
**用途**: Comprehensive toolkit for survival analysis and time-to-event modeling in Python using scikit-survival. Use this skill when working with censored survival data, performing time-to-event analysis, f...
```
from sksurv.metrics import integrated_brier_score

ibs = integrated_brier_score(y_train, y_test, survival_functions, times)
```
**注意**: for SVMs and regularized Cox models; instead of Harrell's when censoring > 40%; (C-index, integrated Brier score, time-dependent AUC)

### tooluniverse-image-analysis
**用途**: Production-ready microscopy image analysis and quantitative imaging data skill for colony morphometry, cell counting, fluorescence quantification, and statistical analysis of imaging-derived measur...
```
pip install pandas numpy scipy statsmodels patsy scikit-image opencv-python-headless tifffile
```

### tooluniverse-statistical-modeling
**用途**: Perform statistical modeling and regression analysis on biomedical datasets. Supports linear regression, logistic regression (binary/ordinal/multinomial), mixed-effects models, Cox proportional haz...
**触发条件**: "What is the odds ratio of X associated with Y?"; "What is the hazard ratio for treatment?"; "Fit a linear regression of Y on X1, X2, X3"; "Perform ordinal logistic regression for severity outcome"
```
statsmodels>=0.14.0
scikit-learn>=1.3.0
lifelines>=0.27.0
pandas>=2.0.0
numpy>=1.24.0
scipy>=1.10.0
```
