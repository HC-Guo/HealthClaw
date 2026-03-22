# gptomics 空间转录组 SOP
> 空间转录组预处理、解卷积、空间变异基因、域注释
> 包含 11 个 OpenClaw skill 的压缩迁移。

---

### bio-spatial-transcriptomics-image-analysis
**用途**: Process and analyze tissue images from spatial transcriptomics data using Squidpy. Extract image features, segment cells/nuclei, and compute morphological features from H&E or IF images. Use when p...
```
import squidpy as sq
import scanpy as sc
import numpy as np
import matplotlib.pyplot as plt
from skimage import io, filters, segmentation
```

### bio-spatial-transcriptomics-spatial-communication
**用途**: Analyze cell-cell communication in spatial transcriptomics data using ligand-receptor analysis with Squidpy. Infer intercellular signaling, identify communication pathways, and visualize interactio...
```
import squidpy as sq
import scanpy as sc
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
```

### bio-spatial-transcriptomics-spatial-data-io
**用途**: Load spatial transcriptomics data from Visium, Xenium, MERFISH, Slide-seq, and other platforms using Squidpy and SpatialData. Read Space Ranger outputs, convert formats, and access spatial coordina...
```
# Stereo-seq (BGI)
sdata = sdio.stereoseq('path/to/stereoseq/output/')
```

### bio-spatial-transcriptomics-spatial-deconvolution
**用途**: Estimate cell type composition in spatial transcriptomics spots using reference-based deconvolution. Use cell2location, RCTD, SPOTlight, or Tangram to infer cell type proportions from scRNA-seq ref...
```
import scanpy as sc
import anndata as ad
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
```

### bio-spatial-transcriptomics-spatial-domains
**用途**: Identify spatial domains and tissue regions in spatial transcriptomics data using Squidpy and Scanpy. Cluster spots considering both expression and spatial context to define anatomical regions. Use...
```
import squidpy as sq
import scanpy as sc
import numpy as np
import matplotlib.pyplot as plt
```

### bio-spatial-transcriptomics-spatial-multiomics
**用途**: Analyze high-resolution spatial platforms like Slide-seq, Stereo-seq, and Visium HD. Use when working with subcellular resolution or high-density spatial data.
```
# Visium HD produces bin files at multiple resolutions
# Load 8µm binned data (recommended starting point)
adata = sc.read_h5ad('visium_hd_8um.h5ad')

# Downsample to 16µm if needed for initial analysis
# Original 2µm data available for detailed analysis
```

### bio-spatial-transcriptomics-spatial-neighbors
**用途**: Build spatial neighbor graphs for spatial transcriptomics data using Squidpy. Compute k-nearest neighbors, Delaunay triangulation, and radius-based connectivity for downstream spatial analyses. Use...
```
import squidpy as sq
import scanpy as sc
import numpy as np
```

### bio-spatial-transcriptomics-spatial-preprocessing
**用途**: Quality control, filtering, normalization, and feature selection for spatial transcriptomics data. Calculate QC metrics, filter spots/cells, normalize counts, and identify highly variable genes. Us...
```
# Scale for PCA (use log-normalized data)
sc.pp.scale(adata, max_value=10)
```

### bio-spatial-transcriptomics-spatial-proteomics
**用途**: Analyzes spatial proteomics data from CODEX, IMC, and MIBI platforms including cell segmentation and protein colocalization. Use when working with multiplexed imaging data, analyzing protein spatia...
```
# Log transform intensities
sm.pp.log1p(adata)

# Rescale markers (0-1 per marker)
sm.pp.rescale(adata)

# Combat batch correction if multiple FOVs
sm.pp.combat(adata, batch_key='fov')
```

### bio-spatial-transcriptomics-spatial-statistics
**用途**: Compute spatial statistics for spatial transcriptomics data using Squidpy. Calculate Moran's I, Geary's C, spatial autocorrelation, co-occurrence analysis, and neighborhood enrichment. Use when com...
```
import squidpy as sq
import scanpy as sc
import pandas as pd
import numpy as np
```

### bio-spatial-transcriptomics-spatial-visualization
**用途**: Visualize spatial transcriptomics data using Squidpy and Scanpy. Create tissue plots with gene expression, clusters, and annotations overlaid on histology images. Use when visualizing spatial expre...
```
import squidpy as sq
import scanpy as sc
import matplotlib.pyplot as plt
```
