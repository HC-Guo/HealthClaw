# 计算模拟与本体论 SOP
> 本体验证、数值求解器、网格生成、材料模拟
> 包含 7 个 OpenClaw skill 的压缩迁移。

---

### linear-solvers
**用途**: Select and configure linear solvers for systems Ax=b in dense and sparse problems. Use when choosing direct vs iterative methods, diagnosing convergence issues, estimating conditioning, selecting p...
```
python3 scripts/preconditioner_advisor.py --matrix-type nonsymmetric --sparse --stagnation --json
```
**限制**: **Large dense matrices**: Direct solvers may run out of memory; **Highly indefinite**: Standard preconditioners may fail

### mesh-generation
**用途**: Plan and evaluate mesh generation for numerical simulations. Use when choosing grid resolution, checking aspect ratios/skewness, estimating mesh quality constraints, or planning adaptive mesh refin...
```
python3 scripts/grid_sizing.py --length 0.001 --resolution 200 --json
```
**限制**: **2D/3D only**: No unstructured mesh generation; **Quality metrics**: Basic aspect ratio and skewness only

### nonlinear-solvers
**用途**: Select and configure nonlinear solvers for f(x)=0 or min F(x). Use for Newton methods, quasi-Newton (BFGS, L-BFGS), Broyden, Anderson acceleration, diagnosing convergence issues, choosing line sear...
```
python3 scripts/convergence_analyzer.py --residuals 1,0.8,0.6,0.5,0.4,0.3,0.2,0.15,0.12,0.1 --json
```
**限制**: **No global convergence guarantee**: All methods may fail for pathological problems; **Jacobian accuracy**: Finite-difference Jacobian may be inaccurate near discontinuities

### ontology-explorer
**用途**: Parse, navigate, and query materials science ontology structure (classes, properties, hierarchy). Use when exploring an ontology like CMSO, understanding class relationships, finding properties for...
```
What do you need?
├── Understand overall ontology structure
│   └── class_browser.py --ontology cmso --list-roots
├── Inspect a specific class
│   └── class_browser.py --ontology cmso --class <name>
├── Find properties for a class
│   └── property_lookup.py --ontology cmso --class <name>
├── Look up a specific property
│   └── property_lookup.py --ontology cmso --property <name>
├── Search for a concept
│   ├── class_browser.py --ontology cmso --search <term>
│   └── property_lookup.py --ontolog
# ... (truncated)
```
**限制**: Only supports OWL/XML format (not Turtle, JSON-LD, or N-Triples); Does not support OWL reasoning or inference (e.g., does not compute transitive closures)

### ontology-mapper
**用途**: Map materials science terms, crystal structures, and sample descriptions to ontology classes and properties. Supports any ontology registered in ontology_registry.json. Use when translating natural...
```
{
  "ontology": "asmo",
  "synonyms": { "simulation method": "Simulation Method", ... },
  "property_synonyms": { "timestep": "has timestep", ... },
  "material_type_rules": { "keyword_rules": [...], "default": "Material" },
  "sample_schema": { "sample_class": "Simulation", ... },
  "crystal_output": { "base_classes": [...], "property_map": {...} },
  "annotation_routing": { "unit_cell_indicators": [...], ... }
}
```
**限制**: Concept mapping uses string matching and a per-ontology synonym table; it does not understand arbitrary natural language; Crystal system validation checks basic constraints only (not all crystallographic rules)

### ontology-validator
**用途**: Validate material sample annotations and data structures against ontology constraints. Use when checking if CMSO annotations are correct, verifying that required properties are present, or validati...
```
What do you need to validate?
├── An annotation (classes and properties are correct)
│   └── schema_checker.py --ontology cmso --annotation '<json>'
├── Completeness of a class annotation
│   └── completeness_checker.py --ontology cmso --class <name> --provided <props>
└── Object property relationships
    └── relationship_checker.py --ontology cmso --relationships '<json>'
```
**限制**: Constraints file is manually curated, not derived from OWL axioms; Does not validate data types (e.g., whether a value is actually a float vs string)

### simulation-validator
**用途**: Validate simulations before, during, and after execution. Use for pre-flight checks, runtime monitoring, post-run validation, diagnosing failed simulations, checking convergence, detecting NaN/Inf,...
```
python3 scripts/failure_diagnoser.py --log simulation.log --json
```
**限制**: **Not a real-time monitor**: Scripts analyze logs after-the-fact; **Regex-based**: Log parsing depends on pattern matching; may miss unusual formats
