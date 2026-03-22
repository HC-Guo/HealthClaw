# 实验室与平台集成 SOP
> LabArchive、Labstep、Ginkgo、OMERO、protocols.io、机器人
> 包含 9 个 OpenClaw skill 的压缩迁移。

---

### galaxy-bridge
**用途**: Galaxy tool discovery, intelligent recommendation, and execution — 8,000+ bioinformatics tools from usegalaxy.org with multi-signal scoring and workflow suggestions
```
output_dir/
├── report.md              # Analysis summary with methods and results
├── result.json            # Machine-readable: tool ID, version, parameters, output paths
├── galaxy_outputs/        # Raw outputs downloaded from Galaxy
│   ├── fastqc_report.html
│   └── ...
└── reproducibility/
    ├── commands.sh        # Galaxy API calls to reproduce
    ├── environment.yml    # Tool versions and Galaxy server info
    └── checksums.sha256   # SHA-256 of all inputs and outputs
```

### ginkgo-cloud-lab
**用途**: Submit and manage protocols on Ginkgo Bioworks Cloud Lab (cloud.ginkgo.bio), a web-based interface for autonomous lab execution on Reconfigurable Automation Carts (RACs). Use when the user wants to...

### instrument-data-to-allotrope
**用途**: Convert laboratory instrument output files (PDF, CSV, Excel, TXT) to Allotrope Simple Model (ASM) JSON format or flattened 2D CSV. Use this skill when scientists need to standardize instrument data...
```
pip install allotropy --break-system-packages
```

### labarchive-integration
**用途**: Electronic lab notebook API integration. Access notebooks, manage entries/attachments, backup notebooks, integrate with Protocols.io/Jupyter/REDCap, for programmatic ELN workflows.
```
python3 scripts/setup_config.py
```
**注意**: Implement appropriate delays between API calls to avoid throttling; Always wrap API calls in try-except blocks with appropriate logging; Store credentials in environment variables or secure config files (never in code)

### labstep
**用途**: Interact with the Labstep electronic lab notebook API using labstepPy. Query experiments, protocols, resources, inventory, and other lab entities.
```
exps = user.getExperiments(search_query='PCR', count=20)
for e in exps:
    print(e.id, e.name)
```

### omero-integration
**用途**: Microscopy data management platform. Access images via Python, retrieve datasets, analyze pixels, manage ROIs/annotations, batch processing, for high-content screening and microscopy workflows.
```
uv pip install omero-py
```

### protocolsio-integration
**用途**: Integration with protocols.io API for managing scientific protocols. This skill should be used when working with protocols.io to search, create, update, or publish protocols; manage protocol steps ...
```
https://protocols.io/api/v3
```

### pylabrobot
**用途**: Laboratory automation toolkit for controlling liquid handlers, plate readers, pumps, heater shakers, incubators, centrifuges, and analytical equipment. Use this skill when automating laboratory wor...
```
# Setup plate reader
from pylabrobot.plate_reading import PlateReader
from pylabrobot.plate_reading.clario_star_backend import CLARIOstarBackend

pr = PlateReader(name="CLARIOstar", backend=CLARIOstarBackend())
await pr.setup()

# Set temperature and read
await pr.set_temperature(37)
await pr.open()
# (manually or robotically load plate)
await pr.close()
data = await pr.read_absorbance(wavelength=450)
```

### virtual-lab-agent
**用途**: 
```
python3 Skills/Clinical/Virtual_Lab_Agent/virtual_lab.py \
    --research_question "Design nanobodies against SARS-CoV-2 spike variants" \
    --team_config immunologist,comp_bio,ml_specialist \
    --literature_scope "nanobody,SARS-CoV-2,spike,variants" \
    --experimental_type computational,in_silico \
    --validation_method binding_prediction,md_simulation \
    --output_format research_report \
    --output virtual_lab_results/
```
