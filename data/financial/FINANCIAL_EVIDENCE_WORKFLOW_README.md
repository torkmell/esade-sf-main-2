# Financial Evidence Workflow — ESADE Sustainable Finance

**Created:** 2026-05-16  
**Complements:** RAG_EVIDENCE_WORKFLOW_README.md (ESG / Greenwashing)

---

## What This Workflow Is

The Financial Evidence workflow provides the structured financial evidence layer for the portfolio construction pipeline. It answers whether each company is **financially credible** — not just whether its ESG claims hold up.

This is not a pure document RAG. Financial data is different from ESG data:
- Most of it is **structured** (prices, ratios, margins) and can be fetched via APIs or calculated from raw data.
- Some of it is **document-based** (annual report financial statements, segment breakdowns, management guidance) and requires targeted extraction.
- All of it must be **auditable**: every metric must trace back to a source, a calculation, or an explicit placeholder.

---

## Why Financial Data Is Different from ESG RAG

| Dimension | ESG RAG | Financial Evidence |
|-----------|---------|-------------------|
| Data type | Unstructured (PDF, dashboards) | Structured (prices, ratios) + targeted document extraction |
| Primary source | Company sustainability reports | yfinance API + annual report financial statements |
| External validation | SBTi, CDP, TPI, NGO | Benchmark comparison, assurance statements |
| Key risk | Greenwashing (claims without substance) | Data staleness, yfinance approximation, sector metric mismatch |
| Output format | Evidence gap logs, 8-test JSON | Metrics CSV, financial scores CSV, financial gap logs |
| Human review trigger | Watchlist / exclusion decisions | Missing data, sector metric adjustment, vol/beta flag |

---

## Folder Structure

```
data/financial/
  raw_prices/              Daily adjusted close prices downloaded from yfinance
  raw_fundamentals/        Fundamental data (ROE, D/E, revenue) from yfinance .info or annual reports
  raw_benchmark/           Benchmark price data (EXW1.DE = STOXX Europe 600 proxy)
  calculated_metrics/      Output CSVs from calculation scripts
  source_notes/            Source note .md files for non-CSV / non-PDF sources
  audit_logs/              Per-run audit entries (supplement to financial_audit_log.csv)
  financial_data_tracker.csv        One row per portfolio company — data availability
  financial_metric_dictionary.csv   Definitions, formulas, sources for every metric
  financial_audit_log.csv           Timestamped log of every download, calculation, extraction
  financial_agent_outputs.csv       Final metric output per company (current fill state: PARTIAL)
  FINANCIAL_EVIDENCE_WORKFLOW_README.md  (this file)
  FINANCIAL_ANALYSIS_SUMMARY_TEMPLATE.md
  FINANCIAL_AGENT_JSON_SCHEMA.json
  source_notes/
    FINANCIAL_SOURCE_NOTE_TEMPLATE.md

scripts/financial/
  fetch_price_data_template.py                Download prices to raw_prices/
  calculate_market_metrics_template.py        Calculate return, vol, Sharpe, beta
  financial_scoring_template.py               Build composite financial quality score
  extract_financials_from_reports_prompt.md   Claude Projects prompt for PDF extraction

data/rag/reports/{FOLDER}/financial_data/    Per-company financial gap log and summaries
```

---

## Where Raw Data Lives

| Data | Location | Format |
|------|---------|--------|
| Downloaded prices | `data/financial/raw_prices/raw_prices_{date}.csv` | Daily OHLCV, one column per ticker |
| Benchmark prices | `data/financial/raw_benchmark/benchmark_EXW1.DE_{date}.csv` | Daily adjusted close |
| Fundamental data from yfinance | Embedded in `outputs/scores/financial_metrics_{date}.csv` | CSV, one row per ticker |
| Annual report extractions | `data/rag/reports/{FOLDER}/financial_data/financial_analysis_summary.md` | Markdown with JSON tables |

---

## Where Calculated Metrics Live

| Output | Location | Produced by |
|--------|---------|------------|
| Market metrics | `data/financial/calculated_metrics/market_metrics_{date}.csv` | `calculate_market_metrics_template.py` |
| Financial scores | `data/financial/calculated_metrics/financial_scores_{date}.csv` | `financial_scoring_template.py` |
| Financial agent outputs | `data/financial/financial_agent_outputs.csv` | Populated manually after verification |

---

## How Source Notes Work

For any financial data source that is not a CSV or PDF (a webpage, a dashboard, a yfinance API call, a Bloomberg terminal result), create a source note in `data/financial/source_notes/` using `FINANCIAL_SOURCE_NOTE_TEMPLATE.md`.

Source notes must include:
- URL (or "MANUAL DOWNLOAD - URL UNKNOWN")
- Date accessed
- Data period
- Relevant metrics
- Human verification status

---

## How Annual Reports Are Used

Annual reports in `data/rag/reports/{FOLDER}/company_reports/` contain the authoritative financial statements. Use them to:

1. **Verify** yfinance .info values (revenue, ROE, debt) — yfinance may lag or misclassify.
2. **Extract** metrics not available from yfinance (EBIT, EBITDA, net debt breakdown, FCF).
3. **Document** management guidance and one-off items.

Use the prompt in `scripts/financial/extract_financials_from_reports_prompt.md` with Claude Projects to extract structured data. Always verify at least 3 values manually against the source PDF before accepting the extraction.

**Important:** Annual reports are Tier 1 company disclosures. They are authoritative for financial statement data but not for ESG claims (which require external validation per the ESG RAG workflow).

---

## How the Financial Audit Log Works

Every download, calculation, and extraction must be logged in `data/financial/financial_audit_log.csv`.

Each row records:
- timestamp
- which company and ticker
- action type (PRICE_DOWNLOAD / FUNDAMENTAL_DOWNLOAD / DOCUMENT_EXTRACTION / SCORE_CALCULATION / EXCLUSION_APPLIED / TRACKER_UPDATED)
- input and output files
- source name and URL
- assumptions made
- issues found
- whether human review is required

The audit log is the trail that makes every financial conclusion reproducible and contestable.

---

## How This Connects to ESG RAG and Portfolio Construction

```
ESG RAG                         Financial Evidence
───────────────────────         ─────────────────────────────────
Company reports (tier1_*)  →    Annual report financial statements
External evidence (tier2_*) →   Benchmark comparison, vol/beta
8-test greenwashing screen  →   Financial risk flag + quality score
Evidence gap logs           →   Financial data gap logs
source_collection_tracker   →   financial_data_tracker
rag_workflow_status         →   financial_audit_log
                    ↓                       ↓
            Portfolio construction (notebook 10)
            ─────────────────────────────────────
            ESG_WEIGHT = 55%
            SHARPE_WEIGHT = 30%
            BIO_WEIGHT = 10%
            EU_WEIGHT = 5%
            ESG_FLOOR = 10th percentile (currently 50.1)
            VOL_CAP = 40%
            MAX_WEIGHT = 10% per stock
```

**Key principle:** A company must pass BOTH screens to be a strong portfolio candidate.

- Passing ESG screening but failing financial robustness → WATCHLIST (financial risk)
- Passing financial screening but failing greenwashing → WATCHLIST (ESG risk)  
- Failing both → likely EXCLUDE
- Passing both → INCLUDE (subject to human review)

---

## Sector-Specific Metric Adjustments

Standard industrial metrics (EBIT, EBITDA, net debt/EBITDA, FCF) are not applicable to all sectors. The following companies require adjusted metrics:

| Ticker | Company | Sector | Standard metrics to replace |
|--------|---------|--------|---------------------------|
| CJ2 | Ringkjoebing Landbobank | Banking | NIM, CET1 ratio, loan loss ratio, ROE |
| SOAN | UnipolSai | Insurance | Combined ratio, SCR coverage, investment yield |
| 2NN | NN Group | Insurance | Combined ratio, SCR coverage, investment yield |
| IGQ5 | 3i Group | Private Equity | NAV, portfolio return, carried interest |

The metric dictionary (`financial_metric_dictionary.csv`) flags these sectors in the `limitations` column.

---

## Non-Hallucination Rules

1. **Do not invent data.** If a metric is unknown, write `null` in the CSV or JSON schema, or `TO BE COLLECTED` in text fields.
2. **Do not use placeholder numbers** (e.g. do not write 5.0% for a margin you haven't sourced).
3. **Every metric must trace to a source.** If you cannot name the source file and approximate page, the value should not be in the output.
4. **yfinance .info is a secondary source.** Use it for initial screening only. Verify material values against the primary annual report before entering into the workbook.
5. **The financial quality score is relative and incomplete.** The valuation pillar is currently MISSING (no EV/EBITDA or P/E collected). Do not present the score as final until all pillars have data.

---

## Human Verification Requirements

- All financial metrics in `financial_agent_outputs.csv` are marked `human_review_required = YES` until verified.
- Verify at least **30% of extracted values** against the source PDF (match page number and exact value).
- **100% verification** required for any metric that drives an exclusion or watchlist decision.
- Banks and insurers (CJ2, SOAN, 2NN, IGQ5) require **human analyst review** of sector-specific metrics — automated scripts do not support these sectors.
- The financial quality score must be reviewed by a human before being used in the portfolio construction workbook.

---

## What to Do Next

1. Run `scripts/financial/fetch_price_data_template.py` to download and cache raw prices.
2. Run `scripts/financial/calculate_market_metrics_template.py` to produce `market_metrics_{date}.csv`.
3. Run `scripts/financial/financial_scoring_template.py` to produce `financial_scores_{date}.csv`.
4. For each company, open `data/rag/reports/{FOLDER}/company_reports/tier1_annual_report_*.pdf` and run the extraction prompt in `scripts/financial/extract_financials_from_reports_prompt.md`.
5. Transfer verified values into `data/financial/financial_agent_outputs.csv`.
6. Log each step in `data/financial/financial_audit_log.csv`.
7. Update `data/financial/financial_data_tracker.csv` as data becomes available.
8. Update each company's `financial_data/financial_data_gap_log.md` as gaps are closed.
