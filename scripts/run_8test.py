#!/usr/bin/env python
"""
8-Test greenwashing runner — sets up the run.

For every final-portfolio holding it assembles a per-company "work pack":
  data/rag/corpus/<NN_company>/_8test/
    source_text.txt  -- extracted text of the primary sustainability report
                        (page-marked, from data/rag/corpus/)
    prompt.txt       -- the 8-Test prompt, company name filled in
    manifest.txt     -- which PDF was used as primary + the other PDFs available

The assessment step then reads each work pack and writes
  outputs/rag/greenwash_<TICKER>.json   (schema per notebooks/09_greenwashing.ipynb)
which NB09 imports and scores (HIGH>=3 -> exclude, HIGH==2 -> watchlist).

Run from anywhere:  python scripts/run_8test.py
Requires: pandas, pypdf.
"""
import glob, os
import pandas as pd
from pypdf import PdfReader

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(PROJECT)

# ── Final 20 holdings + capped rank (rank -> corpus folder NN) ─────────────────
port_file = sorted(glob.glob("outputs/portfolio/final_portfolio_*.csv"))[-1]
port   = pd.read_csv(port_file)
capped = pd.read_csv("data/provided/stage2_top40_capped_hybrid.csv")
rank   = dict(zip(capped["factset_name"], capped["Sector-capped rank"]))
print(f"Holdings: {len(port)}  (from {os.path.basename(port_file)})\n")

# ── 8-Test prompt — mirrors notebooks/09_greenwashing.ipynb ───────────────────
PROMPT = """You are an ESG forensic analyst. For {company} ({ticker}), analyse the
most recent sustainability report — its full page-marked text is in source_text.txt
in this folder — and assess each of the 8 greenwashing dimensions.

For each dimension provide: (a) direct quote with page number, (b) numeric value or
factual statement, (c) red-flag rating LOW / MED / HIGH / MISSING, (d) 1-2 sentences
of reasoning. If a dimension has no information, mark it MISSING — never invent.

Output ONLY valid JSON, saved as outputs/rag/greenwash_{ticker}.json:
{{
  "ticker": "{ticker}", "company_name": "{company}",
  "extraction_date": "YYYY-MM-DD", "analyst_note": "...",
  "dimensions": {{
    "specificity":  {{"quote": null, "page": null, "value": null, "rating": null, "reasoning": null}},
    "metric":       {{"quote": null, "page": null, "value": null, "rating": null, "reasoning": null}},
    "baseline":     {{"quote": null, "page": null, "value": null, "rating": null, "reasoning": null}},
    "target":       {{"quote": null, "page": null, "value": null, "rating": null, "reasoning": null}},
    "time_horizon": {{"quote": null, "page": null, "value": null, "rating": null, "reasoning": null}},
    "scope":        {{"quote": null, "page": null, "value": null, "rating": null, "reasoning": null}},
    "verification": {{"quote": null, "page": null, "value": null, "rating": null, "reasoning": null}},
    "consistency":  {{"quote": null, "page": null, "value": null, "rating": null, "reasoning": null}}
  }}
}}
Red-flag guidance: specificity LOW=exact wording / HIGH=vague; metric LOW=numeric /
HIGH=no numbers; baseline LOW=reference present / HIGH=absent or cherry-picked;
target LOW=binding / HIGH=non-binding or missing; time_horizon LOW=near-term /
HIGH=2050+ only; scope LOW=clear coverage / HIGH=ambiguous; verification
LOW=externally assured / HIGH=self-reported; consistency LOW=capex matches claims /
HIGH=contradiction."""

# ── Pick the primary sustainability report from a folder's PDFs ───────────────
PREFER = ["sustainab", "integrated", "responsib", "non-financial", "esg",
          "climate", "tcfd", "universal-registration", "registration", "iar", "annual"]
AVOID  = ["financial-statement", "financial report", "governance", "modern-slavery",
          "modern slavery", "comptes", "factbook", "policy view", "corp-gov",
          "tables", "criteria", "data reporting", "key_indicators", "key indicators",
          "graph", "proxy", "pay-gap", "-spo"]

# Explicit primary-document overrides (filename substring, lower-case) for folders
# where no single obvious sustainability report exists or the heuristic mis-picks.
OVERRIDE = {
    "A5G.IR":  "climate-transition-plan",     # AIB    - claim-dense climate doc
    "ABBN.SW": "sustainability statement",    # ABB    - CSRD / ESRS statement
    "AZN.L":   "astrazeneca_ar_2025",         # AstraZeneca - annual report
    "MRL.MC":  "einf-version-ingles",         # MERLIN - non-financial info statement
    "SUBC.OL": "annual-report.pdf",           # Subsea 7 - not the old 2022 TCFD
    "SPSN.SW": "esg-booklet",                 # Swiss Prime - consolidated ESG booklet
    "ZURN.SW": "sustainability-report-2025",  # Zurich - sustainability report
    "LI.PA":   "enregistrement-universel",    # Klepierre - universal registration doc
}

def pick_primary(pdfs, ticker):
    ov = OVERRIDE.get(ticker)
    if ov:
        for p in pdfs:
            if ov in os.path.basename(p).lower():
                return p
    def score(p):
        n = os.path.basename(p).lower()
        s = 0.0
        for i, k in enumerate(PREFER):
            if k in n:
                s += (len(PREFER) - i)
                break
        for k in AVOID:
            if k in n:
                s -= 20
        s += min(os.path.getsize(p) / 5e6, 3.0)   # tie-break: bigger doc, capped
        return s
    return max(pdfs, key=score)

def extract(pdf):
    reader = PdfReader(pdf)
    pages = []
    for i, pg in enumerate(reader.pages, 1):
        try:
            t = pg.extract_text() or ""
        except Exception:
            t = ""
        if t.strip():
            pages.append(f"[page {i}]\n{t}")
    return "\n\n".join(pages), len(reader.pages)

# ── Build a work pack per holding ─────────────────────────────────────────────
rows = []
for _, h in port.iterrows():
    name, tkr = h["company_name"], h["yf_ticker"]
    r = rank.get(name)
    folders = glob.glob(f"data/rag/corpus/{int(r):02d}_*") if pd.notna(r) else []
    if not folders:
        rows.append((name, tkr, "!! no corpus folder", 0)); continue
    folder = folders[0]
    pdfs = sorted(glob.glob(f"{folder}/**/*.pdf", recursive=True))
    if not pdfs:
        rows.append((name, tkr, "!! no PDFs in folder", 0)); continue

    primary = pick_primary(pdfs, tkr)
    try:
        text, npages = extract(primary)
    except Exception as e:
        rows.append((name, tkr, f"!! extract failed: {e}", 0)); continue

    wp = os.path.join(folder, "_8test")
    os.makedirs(wp, exist_ok=True)
    with open(os.path.join(wp, "source_text.txt"), "w", encoding="utf-8") as f:
        f.write(f"# {name} ({tkr})\n# primary source: {os.path.basename(primary)}  ({npages} pages)\n\n{text}")
    with open(os.path.join(wp, "prompt.txt"), "w", encoding="utf-8") as f:
        f.write(PROMPT.format(company=name, ticker=tkr))
    with open(os.path.join(wp, "manifest.txt"), "w", encoding="utf-8") as f:
        f.write(f"PRIMARY (used for 8-Test): {os.path.basename(primary)}\n\n"
                f"Other PDFs in this folder (use if the primary pick is wrong):\n" +
                "\n".join("  - " + os.path.basename(p) for p in pdfs if p != primary))
    rows.append((name, tkr, os.path.basename(primary), npages))

# ── Report ────────────────────────────────────────────────────────────────────
print(f"{'COMPANY':<33}{'TICKER':<11}{'PRIMARY DOC / STATUS':<48}PAGES")
print("-" * 98)
for name, tkr, doc, pg in rows:
    print(f"{name[:32]:<33}{tkr:<11}{doc[:47]:<48}{pg if pg else ''}")

ok = sum(1 for *_, pg in rows if pg)
print(f"\n{ok}/{len(rows)} work packs assembled -> data/rag/corpus/<NN_company>/_8test/")
print("Each pack: source_text.txt + prompt.txt + manifest.txt")
print("RUN STEP: assess each work pack -> outputs/rag/greenwash_<TICKER>.json (NB09 reads these).")
