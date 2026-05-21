# Financial Statement Extraction Prompt
## Reusable prompt for extracting financial data from annual reports in Claude Projects

---

## How to use this prompt

1. Upload the company's annual report PDF to a Claude Project.
2. Paste the prompt below into the Claude Projects chat.
3. Replace `[COMPANY NAME]` and `[FISCAL YEAR]` with the correct values.
4. Copy the JSON output and save it to:
   `data/rag/reports/{FOLDER}/financial_data/financial_analysis_summary.md`
   (or paste into `financial_agent_outputs.csv` after human review).

---

## Prompt (paste into Claude Projects)

```
You are a financial analyst. Your task is to extract key financial statement metrics
from the annual report for [COMPANY NAME] for fiscal year [FISCAL YEAR].

Source file: [FILENAME OF THE PDF YOU UPLOADED]

IMPORTANT RULES:
1. Do NOT fabricate values. If a value is not present in the document, write null.
2. Do NOT estimate, interpolate, or infer values that are not explicitly stated.
3. Every value you return must include: source file name, page number or location,
   the exact unit as stated in the document, and the fiscal year it applies to.
4. If a value is on a page you cannot read (e.g., scanned/image page), note this.
5. Mark each value as REPORTED (taken directly from the document) or
   CALCULATED (derived by you from reported values — show your formula).
6. If the document reports in a non-EUR currency, state the currency — do not convert.
7. Return your output as a JSON array as specified below.

Extract the following metrics from the income statement, balance sheet,
and cash flow statement:

FROM THE INCOME STATEMENT:
- Revenue (total net sales or equivalent)
- EBIT (operating profit before interest and tax)
- EBITDA (if explicitly reported; if not, note that D&A would need to be added to EBIT)
- Net income attributable to shareholders
- Interest expense
- Income tax expense
- Depreciation and amortisation (if separately disclosed)

FROM THE BALANCE SHEET:
- Total assets
- Total financial debt (short-term + long-term borrowings or equivalent)
- Cash and cash equivalents
- Net debt (total debt minus cash — CALCULATE this if not reported, show formula)
- Total equity

FROM THE CASH FLOW STATEMENT:
- Operating cash flow
- Capital expenditure (capex) — usually shown as "purchase of property, plant and equipment"
- Free cash flow (if explicitly reported; otherwise CALCULATE as operating CF minus capex)

ADDITIONAL ITEMS (if available):
- Segment revenue breakdown (if the company reports multiple segments)
- Management financial guidance or outlook (exact quote with page number)
- Any restatements or one-off items flagged by management

Return your output as a JSON array. Each element must follow this schema exactly:

[
  {
    "metric": "Revenue",
    "value": 1234.5,
    "unit": "EUR millions",
    "fiscal_year": "FY2024",
    "source_file": "tier1_annual_report_2025.pdf",
    "page_or_location": "p.142 Consolidated Income Statement",
    "reported_or_calculated": "REPORTED",
    "formula_if_calculated": null,
    "confidence": "HIGH",
    "notes": null
  },
  {
    "metric": "Net Debt",
    "value": 456.7,
    "unit": "EUR millions",
    "fiscal_year": "FY2024",
    "source_file": "tier1_annual_report_2025.pdf",
    "page_or_location": "Calculated from p.156 balance sheet",
    "reported_or_calculated": "CALCULATED",
    "formula_if_calculated": "Total Debt (789.0) - Cash (332.3) = 456.7",
    "confidence": "MEDIUM",
    "notes": "Total debt includes IFRS 16 lease liabilities — may inflate leverage vs. pre-IFRS 16 comparisons"
  }
]

Confidence levels:
- HIGH: value clearly stated, unit unambiguous, page confirmed
- MEDIUM: value found but unit or period requires inference
- LOW: value inferred or from a note rather than a primary statement
- NULL: value not found in the document

After the JSON, add a SHORT SUMMARY (5–8 bullet points) of the company's
key financial characteristics based on what you extracted.
```

---

## After receiving Claude's output

1. Verify at least 3 values manually against the PDF (page number check).
2. Save the raw JSON output as:
   `data/rag/reports/{FOLDER}/financial_data/financial_analysis_summary.md`
3. Transfer verified values into `data/financial/financial_agent_outputs.csv`.
4. Log the extraction in `data/financial/financial_audit_log.csv` with:
   - action_type = DOCUMENT_EXTRACTION
   - source file name
   - which metrics were extracted
   - confidence level
   - human_review_required = YES until manual spot-check is complete
5. Mark `human_verification_status = VERIFIED` only after spot-check.

---

## Sector-specific notes

**Banks (CJ2 Ringkjoebing Landbobank, IGQ5 3i Group):**
Replace EBIT / EBITDA with: Net interest margin, CET1 ratio, loan loss provision, return on equity.
Add: "Extract net interest income, total loans, non-performing loan ratio, and CET1 capital ratio."

**Insurers (SOAN UnipolSai, 2NN NN Group):**
Replace EBIT / EBITDA with: Combined ratio, SCR coverage ratio, investment yield, solvency II ratio.
Add: "Extract gross written premium, combined ratio, investment income, and Solvency II SCR coverage."

**PE / Investment companies (IGQ5 3i Group):**
Replace standard metrics with: Net asset value (NAV), portfolio return, carried interest, fee income.
Add: "Extract total portfolio NAV, realised vs unrealised gains, and management fee income."
