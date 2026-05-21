# SusFin — AI-Agent Sustainable Portfolio Pipeline

**ESADE MSc Finance — final group assignment.** An AI-agent research pipeline
that turns raw ESG and market data into an auditable, long-only European equity
portfolio, with a full methodology trail.

> Academic prototype — **not** a regulated product or investment advice.

## What it produces

A **20-stock** long-only European equity portfolio, selected from a ~289-company
universe through a chain of specialised AI agents:

| Metric | Value |
|--------|-------|
| Holdings | 20, across 7 sectors |
| Weighted ESG score | 83.1 / 100 (vs 79.3 screened universe) |
| Weighted Sharpe (5y) | 0.63 |
| WACI (carbon) | ~156 tCO₂e/$M revenue |
| Greenwashing 8-Test | 20 / 20 PASS — 0 excluded, 0 watchlisted |
| Benchmark | STOXX Europe 600 |

## The pipeline

Specialised agents, orchestrated in n8n.cloud; each step is a Jupyter notebook,
AI-generated and human-verified:

`01 Mandate → 02 Data Ingestion → 03 Data Quality → 06 Document Intelligence →
agent10 Financial Analysis → 05 ESG & Climate → 07 Biodiversity →
08 EU Regulation → 09 Greenwashing 8-Test → 10 Portfolio Construction →
Optimisation → 11 Human Review → 12 Reporting`

## Repository layout

| Path | Contents |
|------|----------|
| `notebooks/` | The agent pipeline (run in canonical order — see `CLAUDE.md`) |
| `scripts/` | Helper scripts (8-Test screening, dashboard builder, report exports) |
| `outputs/scores/`, `outputs/portfolio/` | Master datasets, scores, the final portfolio |
| `outputs/rag/` | Greenwashing 8-Test results + the per-company report |
| `outputs/reports/` | Charts and the portfolio factsheet |
| `outputs/dashboard/` | `esade_dashboard.html` — self-contained live demo dashboard |
| `data/provided/` | Course-provided datasets (largest CSV is git-ignored — see below) |
| `data/rag/` | RAG workbook, SBTi / TPI data (the PDF corpus is git-ignored) |
| `docs/`, `Final_Deliverables/` | Reference framework + generated reports |
| `CLAUDE.md`, `ONBOARDING.md` | Full project context and onboarding guide |

## Data not in this repo

This repository contains the team's own work — the pipeline, the analysis and
all generated outputs. Two categories of **input** data are deliberately
**git-ignored** and must be obtained separately to re-run the pipeline:

- **Course-provided datasets** (`data/provided/equityBicsV2.csv`,
  `esgEnvironmentalSocialConsolidatedV4.csv`, `esgGovernanceConsolidatedV4.csv`,
  `legalEntityEuTaxonomy.csv`) — supplied by the course; obtain from the course
  data pack. Not republished here.
- **RAG corpus** (`data/rag/corpus/`) — ~120 company sustainability / annual
  reports (~1 GB). Source: each company's investor-relations page.

All analysis outputs derived from these inputs *are* included (see `outputs/`).

## Running it

See `CLAUDE.md` for full setup. In short: install Python 3.11, run `setup.bat`
(installs packages + Jupyter kernel), then `launch_jupyter.bat`, and run the
notebooks in the canonical order above.

For a quick look at the result without running anything, open
`outputs/dashboard/esade_dashboard.html` in any browser.
