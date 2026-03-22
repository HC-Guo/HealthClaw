# 神经科学工具 SOP
> NeuroKit2、Neuropixels 分析
> 包含 2 个 OpenClaw skill 的压缩迁移。

---

### neurokit2
**用途**: Comprehensive biosignal processing toolkit for analyzing physiological data including ECG, EEG, EDA, RSP, PPG, EMG, and EOG signals. Use this skill when processing cardiovascular signals, brain act...
```
uv pip install neurokit2
```

### neuropixels-analysis
**用途**: Neuropixels neural recording analysis. Load SpikeGLX/OpenEphys data, preprocess, motion correction, Kilosort4 spike sorting, quality metrics, Allen/IBL curation, AI-assisted visual analysis, for Ne...
```
python scripts/export_to_phy.py metrics/analyzer --output phy_export/
```
