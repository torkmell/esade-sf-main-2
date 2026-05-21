# Financial Data Gap Log: Swissquote Group Holding SA

**Ticker (Bloomberg):** 1SQ  
**Ticker (Yahoo Finance):** SQN.SW  
**ISIN:** CH0010675863  
**Sector:** Financials  
**Country:** CH  
**Company folder:** data/rag/reports/1SQ_Swissquote_Group_Holding_SA/  
**Created:** 2026-05-16  
**Status:** TO BE COLLECTED — no financial metrics verified yet
> **Sector note:** Broker/bank — consider NIM and trading income metrics alongside standard margins.

---

## 1. Available Financial Evidence

Files currently in `company_reports/` that contain financial statements:

| File | Type | Period | Local path | Notes |
|------|------|--------|-----------|-------|
| tier1_sustainability_report_2025.pdf (85pp) | Annual/Sustainability Report | FY2024/2025 | data/rag/reports/1SQ_Swissquote_Group_Holding_SA/company_reports/tier1_sustainability_report_2025.pdf | — |
| tier2_sustainability_report_2024.pdf (71pp) | Annual/Sustainability Report | FY2024/2025 | data/rag/reports/1SQ_Swissquote_Group_Holding_SA/company_reports/tier2_sustainability_report_2024.pdf | — |
| tier1_business_report_2025.pdf (24pp) | Annual/Sustainability Report | FY2024/2025 | data/rag/reports/1SQ_Swissquote_Group_Holding_SA/company_reports/tier1_business_report_2025.pdf | — |

> **Note:** Price data and calculated metrics are stored centrally in `data/financial/`, not per-company.  
> Run `scripts/financial/fetch_price_data_template.py` to download prices.  
> Run `scripts/financial/calculate_market_metrics_template.py` to compute return/vol/Sharpe/beta.  
> Use `scripts/financial/extract_financials_from_reports_prompt.md` to extract fundamentals from annual report PDFs.

---

## 2. Required Financial Data

| Data item | Needed for metric | Current status | Preferred source | Fallback source | Priority | Notes |
|-----------|------------------|----------------|-----------------|----------------|---------|-------|
| 1Y / 3Y / 5Y price return | return_1y, return_3y, return_5y | TO BE COLLECTED | yfinance (SQN.SW) | — | HIGH | Run fetch_price_data_template.py |
| Annualised volatility | annualized_volatility | TO BE COLLECTED | Calculated from prices | — | HIGH | — |
| Max drawdown | max_drawdown | TO BE COLLECTED | Calculated from prices | — | HIGH | — |
| Sharpe ratio | sharpe_ratio | TO BE COLLECTED | Calculated from prices | — | HIGH | — |
| Beta vs benchmark | beta_vs_benchmark | TO BE COLLECTED | Calculated vs EXW1.DE | — | MEDIUM | — |
| Revenue (EUR m) | revenue_latest | TO BE COLLECTED | Annual report income statement | yfinance .info | HIGH | Currency: convert to EUR if needed |
| Revenue growth 3Y CAGR | revenue_growth_3y | TO BE COLLECTED | Annual report | yfinance .info | HIGH | — |
| EBIT | ebit_margin_latest | TO BE COLLECTED | Annual report income statement | — | HIGH | — |
| EBITDA | ebitda_margin_latest | TO BE COLLECTED | Annual report (or EBIT + D&A) | — | HIGH | May need to calculate |
| Net income | net_margin_latest | TO BE COLLECTED | Annual report income statement | yfinance .info | HIGH | — |
| Return on equity (ROE) | profitability | PARTIAL (yfinance .info) | yfinance .info | Annual report | MEDIUM | Verify against annual report |
| Total financial debt | net_debt | TO BE COLLECTED | Annual report balance sheet | — | HIGH | — |
| Cash and equivalents | net_debt | TO BE COLLECTED | Annual report balance sheet | — | HIGH | — |
| Net debt | net_debt_to_ebitda | TO BE COLLECTED | Calculated: total debt minus cash | — | HIGH | — |
| Interest expense | interest_coverage | TO BE COLLECTED | Annual report income statement | — | HIGH | — |
| Operating cash flow | free_cash_flow_margin | TO BE COLLECTED | Annual report cash flow statement | yfinance .info | HIGH | — |
| Capital expenditure (capex) | free_cash_flow_margin | TO BE COLLECTED | Annual report cash flow statement | yfinance .info | HIGH | — |
| P/E ratio | valuation | TO BE COLLECTED | Financial terminal or yfinance .info | — | MEDIUM | — |
| EV/EBITDA | valuation | TO BE COLLECTED | Financial terminal or annual report | — | MEDIUM | — |
| Dividend yield | dividend_yield | TO BE COLLECTED | yfinance .info | Annual report | LOW | — |

---

## 3. Missing Source List

**Structured data (run scripts to collect):**
- [ ] Price data: yfinance ticker `SQN.SW` — run `fetch_price_data_template.py`
- [ ] Benchmark: EXW1.DE — downloaded alongside prices
- [ ] Calculated metrics: run `calculate_market_metrics_template.py` after price download

**Document-based data (extract from annual report):**
- [ ] Revenue, EBIT, EBITDA from income statement — use extraction prompt with annual report PDF
- [ ] Net debt breakdown (total debt + cash) from balance sheet
- [ ] Operating cash flow + capex from cash flow statement
- [ ] Interest expense from income statement
- [ ] Management guidance / outlook section

**Valuation data (requires financial terminal or manual collection):**
- [ ] P/E ratio — yfinance .info (`trailingPE`) or financial terminal
- [ ] EV/EBITDA — yfinance .info (`enterpriseToEbitda`) or financial terminal
- [ ] EV/Sales — yfinance .info (`enterpriseToRevenue`) or financial terminal

---

## 4. Suggested Search / Retrieval Queries

```
Price data:
  yfinance: yf.download("SQN.SW", start="2020-01-01", end="2025-01-01")

Annual report (if not already in company_reports/):
  "Swissquote Group Holding SA annual report 2024 PDF investor relations"
  "Swissquote Group Holding SA financial statements 2024"
  site:1sq.com annual report 2024

Fundamental extraction (paste into Claude Projects with annual report PDF):
  See: scripts/financial/extract_financials_from_reports_prompt.md

Valuation multiples:
  "Swissquote Group Holding SA EV EBITDA 2024 valuation"
  "Swissquote Group Holding SA PE ratio 2024"
  "1SQ trailing PE EV EBITDA"
```

---

## 5. Human Review Items

- [ ] Verify at least 3 extracted financial values against the source PDF (page number + exact value)
- [ ] Confirm all values are in EUR or note the reporting currency
- [ ] Check whether sector-specific metrics apply (see sector note above)
- [ ] Confirm beta is not NaN — if NaN, check whether yf_ticker `SQN.SW` has sufficient price overlap with EXW1.DE
- [ ] After verification, update `data/financial/financial_agent_outputs.csv` and `data/financial/financial_data_tracker.csv`
- [ ] Log extraction in `data/financial/financial_audit_log.csv`
