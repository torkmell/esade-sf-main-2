# Financial Data Gap Log: 3i Group PLC

**Ticker (Bloomberg):** IGQ5  
**Ticker (Yahoo Finance):** III.L  
**ISIN:** GB00B1YW4409  
**Sector:** Financials (PE)  
**Country:** GB  
**Company folder:** data/rag/reports/IGQ5_3i_Group_PLC/  
**Created:** 2026-05-16  
**Status:** TO BE COLLECTED — no financial metrics verified yet
> **Sector note:** Private equity/investment company — replace EBIT/EBITDA with: NAV, portfolio return, carried interest.

---

## 1. Available Financial Evidence

Files currently in `company_reports/` that contain financial statements:

| File | Type | Period | Local path | Notes |
|------|------|--------|-----------|-------|
| tier1_annual_report_and_accounts_2025.pdf (220pp) | Annual/Sustainability Report | FY2024/2025 | data/rag/reports/IGQ5_3i_Group_PLC/company_reports/tier1_annual_report_and_accounts_2025.pdf | — |
| tier1_sustainability_section_extract_annual_report_2025.pdf (30pp) | Annual/Sustainability Report | FY2024/2025 | data/rag/reports/IGQ5_3i_Group_PLC/company_reports/tier1_sustainability_section_extract_annual_report_2025.pdf | — |
| tier2_annual_report_and_accounts_2024.pdf (226pp) | Annual/Sustainability Report | FY2024/2025 | data/rag/reports/IGQ5_3i_Group_PLC/company_reports/tier2_annual_report_and_accounts_2024.pdf | — |

> **Note:** Price data and calculated metrics are stored centrally in `data/financial/`, not per-company.  
> Run `scripts/financial/fetch_price_data_template.py` to download prices.  
> Run `scripts/financial/calculate_market_metrics_template.py` to compute return/vol/Sharpe/beta.  
> Use `scripts/financial/extract_financials_from_reports_prompt.md` to extract fundamentals from annual report PDFs.

---

## 2. Required Financial Data

| Data item | Needed for metric | Current status | Preferred source | Fallback source | Priority | Notes |
|-----------|------------------|----------------|-----------------|----------------|---------|-------|
| Net Asset Value (NAV) | financial_quality_score | TO BE COLLECTED | Annual report | — | HIGH | PE/investment metric |
| NAV per share | valuation | TO BE COLLECTED | Annual report | — | HIGH | — |
| Portfolio total return | return_1y | TO BE COLLECTED | Annual report | — | HIGH | — |
| Carried interest / fee income | profitability | TO BE COLLECTED | Annual report | — | MEDIUM | — |
| Return on equity (ROE) | profitability | TO BE COLLECTED | yfinance .info or annual report | — | HIGH | — |
| Revenue (management fees + carried interest) | revenue_latest | TO BE COLLECTED | Annual report | yfinance .info | MEDIUM | Non-standard revenue base |
| 1Y / 3Y / 5Y price return | return_1y, return_3y, return_5y | TO BE COLLECTED | yfinance ({yf}) | — | HIGH | Run fetch_price_data_template.py |
| Annualised volatility | annualized_volatility | TO BE COLLECTED | Calculated from prices | — | HIGH | — |
| Max drawdown | max_drawdown | TO BE COLLECTED | Calculated from prices | — | HIGH | — |
| Sharpe ratio | sharpe_ratio | TO BE COLLECTED | Calculated from prices | — | HIGH | — |
| Beta vs benchmark | beta_vs_benchmark | TO BE COLLECTED | Calculated vs EXW1.DE | — | MEDIUM | — |

---

## 3. Missing Source List

**Structured data (run scripts to collect):**
- [ ] Price data: yfinance ticker `III.L` — run `fetch_price_data_template.py`
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
  yfinance: yf.download("III.L", start="2020-01-01", end="2025-01-01")

Annual report (if not already in company_reports/):
  "3i Group PLC annual report 2024 PDF investor relations"
  "3i Group PLC financial statements 2024"
  site:igq5.com annual report 2024

Fundamental extraction (paste into Claude Projects with annual report PDF):
  See: scripts/financial/extract_financials_from_reports_prompt.md

Valuation multiples:
  "3i Group PLC EV EBITDA 2024 valuation"
  "3i Group PLC PE ratio 2024"
  "IGQ5 trailing PE EV EBITDA"
```

---

## 5. Human Review Items

- [ ] Verify at least 3 extracted financial values against the source PDF (page number + exact value)
- [ ] Confirm all values are in EUR or note the reporting currency
- [ ] Check whether sector-specific metrics apply (see sector note above)
- [ ] Confirm beta is not NaN — if NaN, check whether yf_ticker `III.L` has sufficient price overlap with EXW1.DE
- [ ] After verification, update `data/financial/financial_agent_outputs.csv` and `data/financial/financial_data_tracker.csv`
- [ ] Log extraction in `data/financial/financial_audit_log.csv`
