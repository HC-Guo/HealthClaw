# 科学写作与研究 SOP
> 论文撰写、文献综合、同行评审、科研基金、海报、幻灯片
> 包含 23 个 OpenClaw skill 的压缩迁移。

---

### brainstorming
**用途**: You MUST use this before any creative work - creating features, building components, adding functionality, or modifying behavior. Explores user intent, requirements and design before implementation.
```
digraph brainstorming {
    "Explore project context" [shape=box];
    "Ask clarifying questions" [shape=box];
    "Propose 2-3 approaches" [shape=box];
    "Present design sections" [shape=box];
    "User approves design?" [shape=diamond];
    "Write design doc" [shape=box];
    "Invoke writing-plans skill" [shape=doublecircle];

    "Explore project context" -> "Ask clarifying questions";
    "Ask clarifying questions" -> "Propose 2-3 approaches";
    "Propose 2-3 approaches" -> "Present desig
# ... (truncated)
```

### citation-management
**用途**: Comprehensive citation management for academic research. Search Google Scholar and PubMed for papers, extract accurate metadata, validate citations, and generate properly formatted BibTeX entries. ...
```
python scripts/generate_schematic.py "your diagram description" -o figures/output.png
```

### hypothesis-generation
**用途**: Generate testable hypotheses. Formulate from observations, design experiments, explore competing explanations, develop predictions, propose mechanisms, for scientific inquiry across domains.
```
python scripts/generate_schematic.py "your diagram description" -o figures/output.png
```

### infographics
**用途**: Create professional infographics using Nano Banana Pro AI with smart iterative refinement. Uses Gemini 3 Pro for quality review. Integrates research-lookup and web search for accurate data. Support...
```
"market is growing"
```

### knowledge-synthesis
**用途**: 
```
The team decided to use REST for the API redesign. [direct statement]
```

### latex-posters
**用途**: Create professional research posters in LaTeX using beamerposter, tikzposter, or baposter. Support for conference presentations, academic posters, and scientific communication. Includes layout desi...
```
mkdir -p figures
```

### leads-literature-mining
**用途**: 
**触发条件**: **Systematic Reviews**: Screening thousands of abstracts for inclusion criteria.; **Data Extraction**: Pulling specific metrics (e.g., hazard ratios, sample sizes) from full-text PDFs.; **Evidence Synthesis**: Aggregating findings across multiple studies.
```
python -m leads.review --topic "CAR-T solid tumors" --criteria ./criteria.json
```

### lit-synthesizer
**用途**: Search PubMed and bioRxiv, summarise papers with LLM, build citation graphs, and generate literature review sections.

### markdown-mermaid-writing
**用途**: Comprehensive markdown and Mermaid diagram writing skill. Use when creating any scientific document, report, analysis, or visualization. Establishes text-based diagrams as the default documentation...
```
radar-beta
...
```

### open-notebook
**用途**: Self-hosted, open-source alternative to Google NotebookLM for AI-powered research and document analysis. Use when organizing research materials into notebooks, ingesting diverse content sources (PD...
```
# Create a human note
response = requests.post(f"{BASE_URL}/notes", json={
    "title": "Key Findings",
    "content": "TMB correlates with immunotherapy response in NSCLC...",
    "note_type": "human",
    "notebook_id": notebook_id
})
```

### paper-2-web
**用途**: This skill should be used when converting academic papers into promotional and presentation formats including interactive websites (Paper2Web), presentation videos (Paper2Video), and conference pos...
```
mkdir -p input/xhs_paper/
# Generates Chinese promotional content
```

### peer-review
**用途**: Systematic peer review toolkit. Evaluate methodology, statistics, design, reproducibility, ethics, figure integrity, reporting standards, for manuscript and grant review across disciplines.
```
python scripts/generate_schematic.py "your diagram description" -o figures/output.png
```

### repro-enforcer
**用途**: Export any bioinformatics analysis as a reproducible bundle with Conda environment, Singularity container definition, and Nextflow pipeline.

### research-grants
**用途**: Write competitive research proposals for NSF, NIH, DOE, and DARPA. Agency-specific formatting, review criteria, budget preparation, broader impacts, significance statements, innovation narratives, ...
```
python scripts/generate_schematic.py "your diagram description" -o figures/output.png
```

### research-literature
**用途**: 
```
python3 Skills/Anthropic_Health_Stack/Research_Literature/coworker.py
```

### research-lookup
**用途**: Look up current research information using Perplexity's Sonar Pro Search or Sonar Reasoning Pro models through OpenRouter. Automatically selects the best model based on query complexity. Search aca...
```
[Topic] + [Specific Aspect] + [Time Frame] + [Type of Information]
```

### scientific-brainstorming
**用途**: Research ideation partner. Generate hypotheses, explore interdisciplinary connections, challenge assumptions, develop methodologies, identify research gaps, for creative scientific problem-solving.

### scientific-critical-thinking
**用途**: Evaluate research rigor. Assess methodology, experimental design, statistical validity, biases, confounding, evidence quality (GRADE, Cochrane ROB), for critical analysis of scientific claims.
```
python scripts/generate_schematic.py "your diagram description" -o figures/output.png
```

### scientific-manuscript
**用途**: 
```
1. Smith JA, Jones BC. Title of article. Blood. 2024;143(5):567-578.
```

### scientific-problem-selection
**用途**: This skill should be used when scientists need help with research problem selection, project ideation, troubleshooting stuck projects, or strategic scientific decisions. Use this skill when users a...
```
SKILL 1: Intuition Pumps
         | (generates idea)
         v
SKILL 2: Risk Assessment
         | (evaluates feasibility)
         v
SKILL 3: Optimization Function
         | (defines success metrics)
         v
SKILL 4: Parameter Strategy
         | (determines flexibility)
         v
SKILL 5: Decision Tree
         | (plans execution and evaluation)
         v
SKILL 6: Adversity Planning
         | (prepares for failure modes)
         v
SKILL 7: Problem Inversion
         | (provides pivot 
# ... (truncated)
```

### scientific-schematics
**用途**: Create publication-quality scientific diagrams using Nano Banana 2 AI with smart iterative refinement. Uses Gemini 3.1 Pro Preview for quality review. Only regenerates if quality is below threshold...
```
Scientific diagram guidelines + User request
```

### scientific-slides
**用途**: Build slide decks and presentations for research talks. Use this for making PowerPoint slides, conference presentations, seminar talks, research presentations, thesis defense slides, or any scienti...
```
python scripts/generate_schematic.py "your diagram description" -o figures/output.png
```

### scientific-writing
**用途**: Core skill for the deep research and writing tool. Write scientific manuscripts in full paragraphs (never bullet points). Use two-stage process: (1) create section outlines with key points using re...
```
python scripts/generate_schematic.py "your diagram description" -o figures/output.png
```
