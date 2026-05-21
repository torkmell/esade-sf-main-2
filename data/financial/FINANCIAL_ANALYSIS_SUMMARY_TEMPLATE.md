# Financial Analysis Summary: [Company Name]

**Ticker:** [Bloomberg ticker]  
**Yahoo Finance ticker:** [yf_ticker]  
**ISIN:** [ISIN]  
**Sector:** [BICS sector]  
**Country:** [country]  
**Analysis date:** [YYYY-MM-DD]  
**Analyst:** [name or "AI-generated — human review required"]  
**Data vintage:** [date of most recent data used]

---

## 1. Data Availability and Confidence

| Data item | Status | Source | Period | Confidence |
|-----------|--------|--------|--------|-----------|
| Price data | AVAILABLE / MISSING | yfinance | 2020–2025 | HIGH / MEDIUM / LOW |
| Benchmark data | AVAILABLE / MISSING | EXW1.DE (STOXX 600 proxy) | 2020–2025 | HIGH / MEDIUM / LOW |
| Revenue | AVAILABLE / MISSING / TO BE COLLECTED | Annual report / yfinance | FY20XX | HIGH / MEDIUM / LOW |
| EBIT | AVAILABLE / MISSING / TO BE COLLECTED | Annual report | FY20XX | HIGH / MEDIUM / LOW |
| EBITDA | AVAILABLE / MISSING / TO BE COLLECTED | Annual report / calculated | FY20XX | HIGH / MEDIUM / LOW |
| Net debt | AVAILABLE / MISSING / TO BE COLLECTED | Annual report / calculated | FY20XX | HIGH / MEDIUM / LOW |
| ROE | AVAILABLE / MISSING / TO BE COLLECTED | yfinance .info | FY20XX | MEDIUM |
| D/E ratio | AVAILABLE / MISSING / TO BE COLLECTED | yfinance .info | FY20XX | MEDIUM |
| Valuation multiples | TO BE COLLECTED | Financial terminal / annual report | — | LOW |

**Overall data confidence:** HIGH / MEDIUM / LOW  
**Reason:** [brief explanation]

---

## 2. Market Performance

| Metric | Value | Benchmark | vs. Benchmark |
|--------|-------|-----------|---------------|
| 1Y total return | % | % (EXW1.DE) | +/- pp |
| 3Y annualised return | % | % | +/- pp |
| 5Y annualised return | % | % | +/- pp |
| Annualised volatility | % | — | — |
| Maximum drawdown | % | — | — |
| Sharpe ratio | x | — | — |
| Beta vs STOXX 600 | x | 1.0 | — |

**Interpretation:** [2–3 sentences on what the return and risk profile suggest]

---

## 3. Risk Profile

- **Volatility assessment:** [above / below / within sector median; exclusion flag if >40%]
- **Drawdown context:** [worst loss; when it occurred; recovery]
- **Beta:** [defensive (<0.8), market-neutral (0.8–1.2), amplified (>1.2); exclusion flag if >1.5]
- **Sharpe:** [above/below 0.5 threshold; interpretation]
- **Financial risk flag:** LOW / MEDIUM / HIGH / UNKNOWN

---

## 4. Profitability

| Metric | FY20XX | FY20XX-1 | Trend | Sector context |
|--------|--------|---------|-------|----------------|
| Revenue (EUR m) | | | ↑ / ↓ / → | — |
| Revenue growth 3Y CAGR | % | — | — | — |
| EBIT margin | % | % | ↑ / ↓ | — |
| EBITDA margin | % | % | ↑ / ↓ | — |
| Net margin | % | % | ↑ / ↓ | — |
| ROE | % | % | ↑ / ↓ | — |

**Note for banks / insurers:** Replace above with sector-specific equivalents (NIM, combined ratio, SCR coverage, ROE).

**Interpretation:** [2–3 sentences]

---

## 5. Balance Sheet Resilience

| Metric | Value | Interpretation |
|--------|-------|---------------|
| Net debt (EUR m) | | Positive = indebted; negative = net cash |
| Net debt / EBITDA | x | <2x low; 2–4x moderate; >4x high |
| Interest coverage | x | >3x safe; <1.5x stress |
| Free cash flow margin | % | Positive = self-funding |
| D/E ratio | x | From yfinance .info |

**Note for banks / insurers:** Replace above with CET1 ratio, loan loss ratio, SCR coverage.

**Interpretation:** [2–3 sentences]

---

## 6. Valuation

| Metric | Value | Sector median | Flag |
|--------|-------|--------------|------|
| P/E ratio | x | x | CHEAP / FAIR / EXPENSIVE / UNKNOWN |
| EV/EBITDA | x | x | CHEAP / FAIR / EXPENSIVE / UNKNOWN |
| EV/Sales | x | x | CHEAP / FAIR / EXPENSIVE / UNKNOWN |
| Dividend yield | % | % | — |

**Valuation flag:** CHEAP / FAIR / EXPENSIVE / UNKNOWN  
**Interpretation:** [1–2 sentences]

---

## 7. Key Financial Strengths

- [Strength 1 — with evidence]
- [Strength 2 — with evidence]
- [Strength 3 — with evidence]

---

## 8. Key Financial Risks

- [Risk 1 — with evidence]
- [Risk 2 — with evidence]
- [Risk 3 — with evidence]

---

## 9. Portfolio Implication

**Recommendation:** INCLUDE / EXCLUDE / WATCHLIST / HUMAN_REVIEW_REQUIRED  
**Rationale:** [2–3 sentences combining financial quality and ESG/greenwashing context]

---

## 10. Human Review Items

- [ ] Verify [specific metric] against primary annual report (page X)
- [ ] Confirm currency conversion for [metric if non-EUR]
- [ ] Check whether sector-specific metrics apply (bank / insurer / PE)
- [ ] Cross-check yfinance .info values against published financial statements

---

## 11. Source List

| Source | Type | Period | Local path | Confidence |
|--------|------|--------|-----------|-----------|
| financial_metrics_2026-05-12.csv | Calculated (NB04) | FY2024 | outputs/scores/ | MEDIUM |
| tier1_annual_report_2025.pdf | Company report | FY2024 | data/rag/reports/.../company_reports/ | HIGH (if verified) |

---

## 12. Limitations

- [Limitation 1 — e.g. yfinance .info data may lag 1–2 quarters]
- [Limitation 2 — e.g. no EBITDA or margin data collected yet]
- [Limitation 3 — e.g. beta is NaN — insufficient overlap with benchmark]
- This summary is AI-generated and has not been independently audited. Human verification required before any investment decision.
