# ONBOARDING — ESADE Sustainable Finance Pipeline

Read this first if you're a new teammate, or starting a fresh Claude session on
this project. It captures the project state, the agreed methodology, and the
non-obvious decisions — so you don't re-discover or accidentally undo them.

---

## 1. What this project is

An AI-agent research pipeline for the **ESADE MSc Finance group assignment**. It
screens a ~289-company European equity universe and constructs a **20-stock
long-only sustainable portfolio**, with a methodology report and live demo.

- **Deadline:** Friday 22 May 2026, 18:15–20:15 (presentation + Q&A)
- **Assessment:** written report 60%, presentation/demo/Q&A 40%
- It is an **academic prototype** — not investment advice or a regulated product.

## 2. Where things are

- **Active project folder:** `esade-sf-main 2/` — do all work here. (A sibling
  `esade-sf-main/` exists; it is an older byte-identical copy — ignore it.)
- **Pipeline notebooks:** `notebooks/01_…` through `12_…` (run in order).
- **Outputs:** `outputs/portfolio/`, `outputs/scores/`, `outputs/reports/`.
- **Read `CLAUDE.md`** in the repo root for the full pipeline reference.

## 3. Current state (as of 2026-05-21)

| Notebook / artefact | State |
|---|---|
| 01 Mandate · 02 Data Ingestion · 03 Data Quality | Done |
| agent10 Financial Analysis · 05 ESG & Climate · 07 Biodiversity · 08 EU Reg | Done |
| **10 Portfolio Construction** | ✅ **Reworked (Stage 3), run, verified — final 20** |
| **11 Human Review** | ✅ Reworked, runs — *team must write ≥3 override rationales* |
| **12 Reporting** | ✅ Reworked, run — charts + factsheet regenerated |
| Pipeline diagram (`generate_pipeline_diagram.py`) | ✅ Updated to Stage 3 |
| **09 Greenwashing** | ⏳ **Blocked** — needs RAG Operator (see §7) |
| Written report (5,000–6,500 words) | ⏳ Not started |

## 4. The portfolio methodology

**Stage 1 + 2 (ESG Specialist)** — produced *before* this work:
289 companies → vendor eligibility (2-of-3 across Truvalue / Sustainalytics /
ISS + fossil-fuel exclusion + red-flag override) → **224 eligible** → in-house
ESG scoring (10 indicators, SASB-weighted, sector-relative z-scores) → ranked →
**Top 40**, in a sector-capped variant (max 6 / sector).
Inputs: `data/provided/stage2_top40_capped_hybrid.csv`,
`data/provided/capped40_with_watchlists.csv`.

**Stage 3 (NB10 — `10_portfolio_construction.ipynb`)** — the reworked notebook:
1. Candidate pool = the **capped Top 40** (not the full universe).
2. Map each company to a verified Yahoo Finance ticker (hardcoded dict).
3. **Recover 8 companies** dropped by upstream ticker-join bugs — 5 from the
   financial-metrics file, 3 (Klépierre, MERLIN, Inditex) via a `yfinance`
   price download.
4. **Financial screen as a hard exclusion** *before* ranking: drop any company
   with `financial_verdict` EXCLUDED_GATE / EXCLUDED_METRIC or `gate_verdict`
   GATE_FAIL. No median imputation.
5. **Composite score = 60% financial + 40% ESG.** Financial score recomputed
   uniformly from Sharpe / volatility / drawdown / beta percentile ranks.
6. **Select 20** greedily down the ranking, enforcing **max 5 per SASB sector**
   (≤25%) and a 0.90 correlation guard. Weights ∝ composite, capped at 10%.
7. Watchlisted holdings reaching the final 20 → IC-override worksheet rows.

## 5. The final portfolio (20 holdings)

| # | Company | Sector | Weight |
|---|---|---|---|
| 1 | Zurich Insurance | Financials | 6.24% |
| 2 | SBM Offshore | Extractives & Minerals | 6.09% |
| 3 | Swiss Prime Site | Infrastructure | 6.05% |
| 4 | ABB | Resource Transformation | 5.39% |
| 5 | Klépierre | Infrastructure | 5.38% |
| 6 | MERLIN Properties | Infrastructure | 5.19% |
| 7 | Galenica | Health Care | 5.17% |
| 8 | E.ON | Infrastructure | 5.14% |
| 9 | AIB Group | Financials | 5.11% |
| 10 | UCB | Health Care | 4.88% |
| 11 | AstraZeneca | Health Care | 4.87% |
| 12 | Aegon | Financials | 4.75% |
| 13 | Lloyds Banking | Financials | 4.74% |
| 14 | Alfa Laval | Resource Transformation | 4.64% |
| 15 | Norsk Hydro | Extractives & Minerals | 4.50% |
| 16 | Tele2 | Technology & Communications | 4.46% |
| 17 | Inditex | Consumer Goods | 4.45% |
| 18 | Orion | Health Care | 4.39% |
| 19 | Swedish Orphan Biovitrum | Health Care | 4.36% |
| 20 | Subsea 7 | Extractives & Minerals | 4.20% |

Mandate-compliant: 20 holdings · weights = 100% · max 6.24% (<10%) · 7 sectors ·
largest sector 23.7% (<25%) · WACI 155.8 tCO₂e/$M.

## 6. Key things to know (non-obvious — don't undo these)

- **Two ticker systems.** ESG/biodiversity/EU data use Bloomberg-style tickers;
  prices/financials use Yahoo Finance tickers. They don't map directly. NB10
  bypasses the broken joins with a hardcoded name→Yahoo-ticker map.
- **The 8-company recovery.** Notebook 02 (master build, 289→279) and notebook
  05 (ESG import, 224→213) silently dropped 8 of the capped 40 via ticker-join
  bugs. NB10 routes around them; the bugs in 02/05 themselves are *not* fixed.
- **7 companies fail the financial screen:** AIXTRON (GATE_FAIL) + L'Oréal,
  Rentokil, Logitech, Arcadis, Moncler, Sweco (negative 5-year Sharpe). Final 20
  is selected from the 33 survivors.
- **Sector-median imputation.** The recovered companies had no carbon / E-S-G /
  biodiversity / nature-risk data; NB10 Step 1c imputes these from the GICS
  *sector* median (tagged `sector_median_imputed`). EU Taxonomy is *not* imputed.
- **EU Taxonomy data is sparse** — most holdings lack it, by data-source design.
  This is a disclosed report limitation, not a pipeline gap.
- **Greenwashing has not run** (NB09). `gw_exclude`/`gw_watchlist` are default
  `False` placeholders, not real assessments.
- **`fin_score` is the financial score used for ranking** — recomputed uniformly
  in NB10. The legacy `composite_financial_score` column was dropped.

## 7. Open items

1. **NB09 Greenwashing (blocked).** Needs the RAG Operator: collect company
   sustainability PDFs (0 currently), run the prepared `data/rag/reports/*/
   *_8test_prompt.txt` prompts in Claude Projects, save JSON outputs to
   `outputs/rag/`. Do **not** fabricate these — they require real source docs.
2. **NB11 override rationales.** `ic_overrides_watchlist_*.csv` lists 8
   watchlisted holdings; the team must write the rationale + sign-off for ≥3.
3. **Written report, slide deck, demo video.**

## 8. Running the pipeline

Team workflow is normally **Google Colab** (paste notebook cells, run). Colab
has pandas / numpy / yfinance / openpyxl / matplotlib pre-installed.

To run locally without Xcode tools, use `uv` (standalone Python):
```
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python pandas numpy yfinance openpyxl matplotlib
```
Then run notebooks top-to-bottom (Kernel → Restart & Run All) in this order:
**10 → 11 → 12**, then `python generate_pipeline_diagram.py`.
NB10 Step 1b and the diagram need an **internet connection** (yfinance).

After NB10, verify: 20 holdings · weights sum to 100% · max ≤10% · ≥5 sectors ·
largest sector ≤25%.

## 9. Outputs reference (all dated `2026-05-21`)

- `outputs/portfolio/final_portfolio_2026-05-21.csv` — **the final 20 holdings**
- `outputs/portfolio/universe_scores_2026-05-21.csv` — all 40, tagged
  SELECTED / NOT_SELECTED / EXCLUDED
- `outputs/portfolio/exclusions.csv` — the 7 financial-screen exclusions
- `outputs/scores/ic_overrides_watchlist_2026-05-21.csv` — 8 watchlist IC rows
- `outputs/scores/human_overrides_2026-05-21.csv` — override log
- `outputs/reports/` — `portfolio_weights.png`, `esg_comparison.png`,
  `sector_allocation.png`, `ai_use_statement_2026-05-21.txt`, `pipeline_diagram.png`
