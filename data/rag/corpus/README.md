# RAG Document Corpus — Capped Top 40

Source documents for the greenwashing 8-Test (Agent 9 / `09_greenwashing.ipynb`)
and Document Intelligence extraction (Agent 4 / `06_document_intelligence.ipynb`).
One folder per capped-Top-40 company, numbered in capped-rank order (`01` = rank 1).

- **120 PDFs across 40 company folders** — sustainability statements, integrated /
  annual reports, financial statements, governance reports.
- **`ESG_External_Research.md`** + **`ESG_External_Research_Summary.xlsx`** — a
  tier-1 external controversy screen of all 40 names over a rolling 6-month
  window (5 in-window findings, 2 borderline, 33 clean).

## How this feeds the pipeline

NB06 and NB09 do **not** read these PDFs directly — they read the JSON *outputs*
of the RAG step. The workflow:

1. The RAG Operator opens a Claude Project for a company and uploads that
   company's PDFs from its folder here.
2. Runs the **NB06 extraction prompt** (`06_document_intelligence.ipynb`, Step 1)
   → saves the result as `outputs/rag/doc_intel_<TICKER>.json`.
3. Runs the **8-Test greenwashing prompt** (`09_greenwashing.ipynb`, Step 1; the
   per-company prompts are in `data/rag/reports/<COMPANY>/<X>_8test_prompt.txt`)
   → saves the result for NB09 to read.
4. NB06 / NB09 then read those JSON outputs and score the portfolio.

So this corpus is the **input** to the (human) RAG step — it does not itself
produce the doc-intel or 8-Test scores.

## Priority

The final portfolio is 20 holdings and greenwashing review is required for all
of them — prioritise the 20 held names (and the watchlisted ones) for the
8-Test. **SOBI** (folder `32`) is the explicit `PENDING_RAG` item: its Truvalue
Laggard triggers need verification before final sign-off (see the IC Override
Notes memo).

Corpus copied from `SusFin_Archive`, 21 May 2026.
