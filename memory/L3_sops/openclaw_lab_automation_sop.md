# 实验室自动化 SOP
> 实验室设备集成、自动化工作流、LIMS
> 包含 4 个 OpenClaw skill 的压缩迁移。

---

### benchling-integration
**用途**: Benchling R&D platform integration. Access registry (DNA, proteins), inventory, ELN entries, workflows via API, build Benchling Apps, query Data Warehouse, for lab data management automation.
```
# Stable release
uv pip install benchling-sdk
# or with Poetry
poetry add benchling-sdk
```

### lab-results
**用途**: 
```
python3 Skills/Anthropic_Health_Stack/Lab_Results/coworker.py
```

### opentrons-integration
**用途**: Lab automation platform for Flex/OT-2 robots. Write Protocol API v2 protocols, liquid handling, hardware modules (heater-shaker, thermocycler), labware management, for automated pipetting workflows.
```
# Turn lights on
protocol.set_rail_lights(on=True)

# Turn lights off
protocol.set_rail_lights(on=False)
```

### opentrons-protocol-agent
**用途**: 
```
# Agent writes the file to disk
python3 -m opentrons.simulate generated_protocol.py
```
