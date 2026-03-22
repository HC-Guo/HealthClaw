# 化学工具与智能体 SOP
> 化学性质查询、化学智能体
> 包含 4 个 OpenClaw skill 的压缩迁移。

---

### chemical-property-lookup
**用途**: 

### chemist-analyst
**用途**: Analyzes events through chemistry lens using molecular structure, reaction mechanisms, thermodynamics,
kinetics, and analytical techniques (spectroscopy, chromatography, mass spectrometry).
Provide...

### chemistry-agent
**用途**: 
```
python3 src/chemistry/main.py --target "Aspirin" --task "retrosynthesis"
```

### glycoengineering
**用途**: Analyze and engineer protein glycosylation. Scan sequences for N-glycosylation sequons (N-X-S/T), predict O-glycosylation hotspots, and access curated glycoengineering tools (NetOGlyc, GlycoShield,...
```
Typical complex biantennary N-glycan:
Neu5Ac-Gal-GlcNAc-Man\
                       Man-GlcNAc-GlcNAc-[Asn]
Neu5Ac-Gal-GlcNAc-Man/
(±Core Fuc at innermost GlcNAc)
```
**注意**: **Start with NetNGlyc/NetOGlyc** for computational prediction before experimental validation; **Verify with mass spectrometry**: Glycoproteomics (Byonic, Mascot) for site-specific glycan profiling; **Consider site context**: Not all predicted sequons are actually glycosylated (accessibility, cell type, protein conformation)
