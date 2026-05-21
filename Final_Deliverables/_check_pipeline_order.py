"""Inspect each pipeline notebook/script for file READS (inputs) and WRITES (outputs)
to verify the proposed run order is dependency-consistent."""
import json, re, sys, os
sys.stdout.reconfigure(encoding="utf-8")

ROOT = r"C:\Users\ionva\Desktop\Sustainable Finance Project"

STEPS = [
    ("01 Mandate",                 r"notebooks\01_mandate.ipynb"),
    ("02 Data Ingestion",          r"notebooks\02_data_ingestion.ipynb"),
    ("03 Data Quality",            r"notebooks\03_data_quality.ipynb"),
    ("06 Document Intelligence",   r"notebooks\06_document_intelligence.ipynb"),
    ("agent10 Financial Analysis", r"notebooks\agent10_financial_analysis.ipynb"),
    ("05 ESG & Climate",           r"notebooks\05_esg_climate.ipynb"),
    ("07 Biodiversity",            r"notebooks\07_biodiversity.ipynb"),
    ("08 EU Regulation",           r"notebooks\08_eu_regulation.ipynb"),
    ("09 Greenwashing",            r"notebooks\09_greenwashing.ipynb"),
    ("10 Portfolio Construction",  r"notebooks\10_portfolio_construction.ipynb"),
    ("Opt Optimisation",           r"Optimization_module\run_pipeline.py"),
    ("11 Human Review",            r"notebooks\11_human_review.ipynb"),
    ("12 Reporting",               r"notebooks\12_reporting.ipynb"),
]

# Keywords we care about for I/O detection
READ_PATTERNS = [
    r"pd\.read_csv\([^)]+",
    r"pd\.read_excel\([^)]+",
    r"open\([^)]+\)",
    r"glob\.glob\([^)]+",
    r"json\.load\(",
    r"from\s+pathlib.*read_text",
]
WRITE_PATTERNS = [
    r"\.to_csv\(\s*[\"'][^\"']+[\"']",
    r"\.to_excel\(\s*[\"'][^\"']+[\"']",
    r"json\.dump\(",
    r"\.savefig\(\s*[\"'][^\"']+[\"']",
    r"\.write_text\(",
    r"\.save\(\s*[\"'][^\"']+[\"']",
]

# Filename patterns we want to extract specifically
FILENAME_PATTERNS = [
    "mandate.json",
    "master_dataset", "prices_",
    "data_dictionary", "outlier_flags",
    "rag_extractions", "RAG_Screening_Sheet", "greenwash",
    "financial_metrics", "financial_screen_passed", "financial_exclusions",
    "esg_scores", "Portfolio_Screening_Output", "ESG Data_Factset",
    "biodiversity_scores",
    "eu_regulation", "pai_indicators", "sfdr_compliance",
    "greenwashing_scores",
    "final_portfolio", "universe_scores", "exclusions.csv", "optimization_input",
    "human_overrides", "ai_use_statement",
    "portfolio_weights", "esg_comparison", "sector_allocation",
    "pipeline_diagram", "financial_screen_chart",
]

def get_cell_sources(path):
    if path.endswith(".ipynb"):
        with open(path, "r", encoding="utf-8") as f:
            nb = json.load(f)
        return ["".join(c.get("source", [])) for c in nb["cells"] if c["cell_type"] == "code"]
    else:
        with open(path, "r", encoding="utf-8") as f:
            return [f.read()]

def find_filenames(src, patterns):
    found = set()
    for pat in patterns:
        for m in re.finditer(r"[\w\-\.]+" + re.escape(pat) + r"[\w\-\.\*]*\.(?:csv|json|xlsx|png|txt)", src):
            found.add(m.group(0))
        for m in re.finditer(re.escape(pat) + r"[\w\-\.\*]*\.(?:csv|json|xlsx|png|txt)", src):
            found.add(m.group(0))
    return found

def classify_io(src):
    reads = set(); writes = set()
    # Find lines containing read or write patterns, then extract filenames from those lines
    lines = src.split("\n")
    for line in lines:
        is_read  = any(re.search(p, line) for p in READ_PATTERNS)
        is_write = any(re.search(p, line) for p in WRITE_PATTERNS)
        if is_read or is_write:
            for fp in FILENAME_PATTERNS:
                if fp in line:
                    if is_write: writes.add(fp)
                    elif is_read: reads.add(fp)
    return reads, writes

for label, rel in STEPS:
    full = os.path.join(ROOT, rel)
    if not os.path.exists(full):
        print(f"\n=== {label}  [MISSING: {rel}] ===")
        continue
    print(f"\n=== {label}  ({rel}) ===")
    sources = get_cell_sources(full)
    all_src = "\n".join(sources)
    reads, writes = classify_io(all_src)
    if reads:
        print("  READS : " + ", ".join(sorted(reads)))
    else:
        print("  READS : (none detected)")
    if writes:
        print("  WRITES: " + ", ".join(sorted(writes)))
    else:
        print("  WRITES: (none detected)")
