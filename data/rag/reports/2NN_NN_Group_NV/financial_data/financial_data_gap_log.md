# Financial Data Gap Log: NN Group NV

**Ticker (Bloomberg):** 2NN  
**Ticker (Yahoo Finance):** NN.AS  
**ISIN:** NL0010773842  
**Sector:** Financials (Insurance)  
**Country:** NL  
**Company folder:** data/rag/reports/2NN_NN_Group_NV/  
**Created:** 2026-05-16  
**Status:** TO BE COLLECTED — no financial metrics verified yet
> **Sector note:** Insurance — replace EBIT/EBITDA with: combined ratio, SCR coverage, investment yield.

---

## 1. Available Financial Evidence

Files currently in `company_reports/` that contain financial statements:

| File | Type | Period | Local path | Notes |
|------|------|--------|-----------|-------|
| tier1_annual_report_2025.pdf (342pp) | Annual/Sustainability Report | FY2024/2025 | data/rag/reports/2NN_NN_Group_NV/company_reports/tier1_annual_report_2025.pdf | — |
| tier2_annual_report_2024.pdf (415pp) | Annual/Sustainability Report | FY2024/2025 | data/rag/reports/2NN_NN_Group_NV/company_reports/tier2_annual_report_2024.pdf | — |

> **Note:** Price data and calculated metrics are stored centrally in `data/financial/`, not per-company.  
> Run `scripts/financial/fetch_price_data_template.py` to download prices.  
> Run `scripts/financial/calculate_market_metrics_template.py` to compute return/vol/Sharpe/beta.  
> Use `scripts/financial/extract_financials_from_reports_prompt.md` to extract fundamentals from annual report PDFs.

---

## 2. Required Financial Data

| Data item | Needed for metric | Current status | Preferred source | Fallback source | Priority | Notes |
|-----------|------------------|----------------|-----------------|----------------|---------|-------|
| Combined ratio | financial_risk_flag | TO BE COLLECTED | Annual report | — | HIGH | Insurance metric: <100% = underwriting profit |
| SCR coverage ratio | balance_sheet_resilience | TO BE COLLECTED | Annual report / Solvency II disclosure | Regulatory filing | HIGH | Solvency II key metric |
| Investment yield | profitability | TO BE COLLECTED | Annual report | — | HIGH | — |
| Gross written premium | revenue_latest | TO BE COLLECTED | Annual report | yfinance .info | HIGH | Use GWP not total revenue |
| Revenue growth 3Y | revenue_growth_3y | TO BE COLLECTED | Annual report | — | MEDIUM | — |
| Return on equity (ROE) | profitability | TO BE COLLECTED | yfinance .info or annual report | — | HIGH | — |
| 1Y / 3Y / 5Y price return | return_1y, return_3y, return_5y | TO BE COLLECTED | yfinance ({yf}) | — | HIGH | Run fetch_price_data_template.py |
| Annualised volatility | annualized_volatility | TO BE COLLECTED | Calculated from prices | — | HIGH | — |
| Max drawdown | max_drawdown | TO BE COLLECTED | Calculated from prices | — | HIGH | — |
| Sharpe ratio | sharpe_ratio | TO BE COLLECTED | Calculated from prices | — | HIGH | — |
| Beta vs benchmark | beta_vs_benchmark | TO BE COLLECTED | Calculated vs EXW1.DE | — | MEDIUM | — |

---

## 3. Missing Source List

**Structured data (run scripts to collect):**
- [ ] Price data: yfinance ticker `NN.AS` — run `fetch_price_data_template.py`
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
  yfinance: yf.download("NN.AS", start="2020-01-01", end="2025-01-01")

Annual report (if not already in company_reports/):
  "NN Group NV annual report 2024 PDF investor relations"
  "NN Group NV financial statements 2024"
  site:2nn.com annual report 2024

Fundamental extraction (paste into Claude Projects with annual report PDF):
  See: scripts/financial/extract_financials_from_reports_prompt.md

Valuation multiples:
  "NN Group NV EV EBITDA 2024 valuation"
  "NN Group NV PE ratio 2024"
  "2NN trailing PE EV EBITDA"
```

---

## 5. Human Review Items

- [ ] Verify at least 3 extracted financial values against the source PDF (page number + exact value)
- [ ] Confirm all values are in EUR or note the reporting currency
- [ ] Check whether sector-specific metrics apply (see sector note above)
- [ ] Confirm beta is not NaN — if NaN, check whether yf_ticker `NN.AS` has sufficient price overlap with EXW1.DE
- [ ] After verification, update `data/financial/financial_agent_outputs.csv` and `data/financial/financial_data_tracker.csv`
- [ ] Log extraction in `data/financial/financial_audit_log.csv`
