# 合规与法规 SOP
> HIPAA、医疗器械法规、数据合规
> 包含 2 个 OpenClaw skill 的压缩迁移。

---

### equity-scorer
**用途**: Compute HEIM diversity and equity metrics from VCF or ancestry data. Generates heterozygosity, FST, PCA plots, and a composite HEIM Equity Score with markdown reports.
```
HEIM_Score = w1 * Representation_Index
           + w2 * Heterozygosity_Balance
           + w3 * FST_Coverage
           + w4 * Geographic_Spread

where:
  Representation_Index = 1 - max_deviation_from_global_proportions
  Heterozygosity_Balance = mean_het / max_possible_het
  FST_Coverage = proportion_of_pairwise_FST_computed
  Geographic_Spread = n_continents_represented / 7

Default weights: w1=0.35, w2=0.25, w3=0.20, w4=0.20
```

### hipaa-compliance
**用途**: Ensure HIPAA compliance when handling PHI (Protected Health Information). Use when writing code that accesses user health data, check-ins, journal entries, or any sensitive information. Activates f...
```
import { requestBreakGlassAccess } from '@/lib/hipaa/break-glass';

// This creates enhanced audit trail
const access = await requestBreakGlassAccess(
  adminId,
  targetUserId,
  'Emergency support required - user reported crisis'
);
```
