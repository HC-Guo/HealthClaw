# 通用工具集 SOP
> 浏览器自动化、多引擎搜索、深度研究、文档处理（PDF/DOCX/XLSX/PPTX）
> 包含 19 个 OpenClaw skill 的压缩迁移。

---

### agent-browser
**用途**: Browse the web for any task — research topics, read articles, interact with web apps, fill forms, take screenshots, extract data, and test web pages. Use whenever a browser would be useful, not jus...
```
agent-browser eval "document.title"   # Run JavaScript
```

### deep-research
**用途**: Execute autonomous multi-step deep research on any topic. Use when the user asks for comprehensive research, literature reviews, competitive analysis, topic deep-dives, or wants to understand a com...
**触发条件**: User wants a thorough understanding of a topic (medical condition, drug, treatment, technology); User asks for a literature review or evidence summary; User wants competitive or landscape analysis; User wants to investigate an open question with multiple angles
```
# Use multi-search-engine for broad web coverage
# Use pubmed-search for peer-reviewed medical literature
# Use agent-browser to read full-text articles and retrieve content blocked by snippets
```

### deep-research-swarm
**用途**: 
```
python3 src/research/agents/agent_coordinator.py --topic "mRNA cancer vaccines" --depth "deep"
```

### doc-coauthoring
**用途**: Guide users through a structured workflow for co-authoring documentation. Use when user wants to write documentation, proposals, technical specs, decision docs, or similar structured content. This ...

### docx
**用途**: Use this skill whenever the user wants to create, read, edit, or manipulate Word documents (.docx files). Triggers include: any mention of 'Word doc', 'word document', '.docx', or requests to produ...
```
python scripts/office/validate.py doc.docx
```

### docx
**用途**: Comprehensive document creation, editing, and analysis with support for tracked changes, comments, formatting preservation, and text extraction. When Claude needs to work with professional document...
```
pdftoppm -jpeg -r 150 document.pdf page
```

### find-skills
**用途**: Helps users discover and install agent skills when they ask questions like "how do I do X", "find a skill for X", "is there a skill that can...", or express interest in extending capabilities. This...
```
npx skills find [query]
```

### multi-search-engine
**用途**: Multi search engine integration with 17 engines (8 CN + 9 Global). Supports advanced search operators, time filters, site search, privacy engines, and WolframAlpha knowledge queries. No API keys re...
```
// Basic search
web_fetch({"url": "https://www.google.com/search?q=python+tutorial"})

// Site-specific
web_fetch({"url": "https://www.google.com/search?q=site:github.com+react"})

// File type
web_fetch({"url": "https://www.google.com/search?q=machine+learning+filetype:pdf"})

// Time filter (past week)
web_fetch({"url": "https://www.google.com/search?q=ai+news&tbs=qdr:w"})

// Privacy search
web_fetch({"url": "https://duckduckgo.com/html/?q=privacy+tools"})

// DuckDuckGo Bangs
web_fetch({"url
# ... (truncated)
```

### pdf
**用途**: Use this skill whenever the user wants to do anything with PDF files. This includes reading or extracting text/tables from PDFs, combining or merging multiple PDFs into one, splitting PDFs apart, r...
```
# Merge
pdftk file1.pdf file2.pdf cat output merged.pdf

# Split
pdftk input.pdf burst

# Rotate
pdftk input.pdf rotate 1east output rotated.pdf
```

### pdf
**用途**: Comprehensive PDF manipulation toolkit for extracting text and tables, creating new PDFs, merging/splitting documents, and handling forms. When Claude needs to fill in a PDF form or programmaticall...
```
# Merge
pdftk file1.pdf file2.pdf cat output merged.pdf

# Split
pdftk input.pdf burst

# Rotate
pdftk input.pdf rotate 1east output rotated.pdf
```

### pdf-processing
**用途**: Extract text and tables from PDF files, fill forms, merge documents. Use when working with PDF files or when the user mentions PDFs, forms, or document extraction.
```
import pdfplumber

with pdfplumber.open("document.pdf") as pdf:
    text = pdf.pages[0].extract_text()
    print(text)
```

### pdf-processing-pro
**用途**: Production-ready PDF processing with forms, tables, OCR, validation, and batch operations. Use when working with complex PDF workflows in production environments, processing large volumes of PDFs, ...
```
chmod +x scripts/*.py
```
**注意**: before processing; in custom scripts; for debugging

### pptx
**用途**: Use this skill any time a .pptx file is involved in any way — as input, output, or both. This includes: creating slide decks, pitch decks, or presentations; reading, parsing, or extracting text fro...
```
python -m markitdown output.pptx
```

### pptx
**用途**: Presentation creation, editing, and analysis. When Claude needs to work with presentations (.pptx files) for: (1) Creating new presentations, (2) Modifying or editing content, (3) Working with layo...
```
pdftoppm -jpeg -r 150 template.pdf slide
```

### pptx-posters
**用途**: Create research posters using HTML/CSS that can be exported to PDF or PPTX. Use this skill ONLY when the user explicitly requests PowerPoint/PPTX poster format. For standard research posters, use l...
```
<img src="figures/hero.png" class="hero-image">
```

### tooluniverse-literature-deep-research
**用途**: Conduct comprehensive literature research with target disambiguation, evidence grading, and structured theme extraction. Creates a detailed report with mandatory completeness checklist, biological ...
```
*OA Status: Best-effort (Unpaywall not configured)*
```
**限制**: [If full text not available, or if only review evidence exists]; Prefer ToolUniverse literature tools (Europe PMC / PubMed / PMC / Semantic Scholar) over general web browsing.

### wikipedia-search
**用途**: Search and fetch structured content from Wikipedia using the MediaWiki API for reliable, encyclopedic information
**触发条件**: **Encyclopedic knowledge** — Factual information about people, places, events, concepts; **Historical information** — Well-documented historical facts, dates, and events; **Scientific and technical concepts** — Definitions, explanations, and overviews; **Biographical information** — Details about notable people
```
python3 -m pip install Wikipedia-API --user
```

### xlsx
**用途**: Use this skill any time a spreadsheet file is the primary input or output. This means any task where the user wants to: open, read, edit, or fix an existing .xlsx, .xlsm, .csv, or .tsv file (e.g., ...
```
python scripts/recalc.py output.xlsx 30
```

### xlsx
**用途**: Comprehensive spreadsheet creation, editing, and analysis with support for formulas, formatting, data analysis, and visualization. When Claude needs to work with spreadsheets (.xlsx, .xlsm, .csv, ....
```
python recalc.py output.xlsx 30
```
