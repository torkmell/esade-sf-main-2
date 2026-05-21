# RAG Evidence Workflow — ESADE Sustainable Finance

## Purpose

This workflow supports the 8-Test greenwashing and claim-verification screen for
the 20 companies in the final portfolio. The goal is not to summarise company
reports. The goal is to test whether companies actually do what they claim.

Every conclusion entered into the RAG Screening Sheet workbook must be traceable
to a specific source file, page number, or verified URL. Conclusions without
traceable evidence are invalid for submission.

---

## The Core Distinction: Company Claims vs. External Verification

**Company reports show what a company says about itself.**
Annual reports, sustainability reports, TCFD disclosures, and CSRD filings are
written and controlled by the company. They establish the claims to be tested —
they are not proof that those claims are true.

**External evidence tests whether the claims hold up.**
SBTi target dashboards, CDP scores, Transition Pathway Initiative assessments,
third-party GHG assurance statements, NGO reports, and regulatory notices are
produced independently of the company. These are the sources that can corroborate,
qualify, or contradict what the company has said.

Rule: a PASS rating on any of the 8 greenwashing dimensions requires at least one
piece of corroborating external evidence, or a clearly verifiable and auditable
primary disclosure (e.g. an externally assured emissions figure with a named
auditor and standard cited). Company claims alone are insufficient for a strong
greenwashing conclusion.

---

## Folder Structure

Each company has a dedicated folder under `data/rag/reports/`:

```
data/rag/reports/
  TICKER_Company_Name/
    TICKER_8test_prompt.txt       Analysis prompt — paste Step 5 into Claude Projects
    company_reports/              Tier 1: primary company disclosures (tier1_*.pdf)
    external_evidence/            Tier 2: external verification sources (tier2_*.pdf)
    rag_outputs/
      evidence_gap_log.md         Gap tracker and 8-Test dimension status
```

### Tier definitions

| Tier | Meaning | Examples |
|------|---------|---------|
| Tier 1 (`tier1_*`) | Primary company disclosures — what the company says | Annual report, sustainability report, TCFD, CSRD, ESRS, CDP response authored by company |
| Tier 2 (`tier2_*`) | External verification — independent of the company | SBTi dashboard, CDP score, TPI assessment, Climate Action 100+, NGO report, GHG assurance statement, regulatory enforcement notice |
| Tier 3 | Quantitative pipeline data — from ESADE course CSVs | ESG scores, WACI, biodiversity scores, EU Taxonomy data (embedded in the analysis prompt, not a PDF) |

Naming is mandatory. Files must begin with `tier1_` or `tier2_` before upload to
Claude Projects. Claude uses the filename prefix to apply the correct evidence
hierarchy when running the 8-Test analysis.

---

## source_collection_tracker.csv

Located at the project root. One row per file (existing or gap).

**Columns and how to use them:**

| Column | Meaning |
|--------|---------|
| `company_name` / `ticker` | Which company |
| `company_folder` | Relative path to the company folder |
| `company_reports_available` | YES if any Tier 1 files exist |
| `company_report_files` | Filename, if this row represents an existing file |
| `source_gap` | Description of a missing source (blank if this row is an existing file) |
| `source_type_needed` | Type of missing source: `company_report`, `external_verification`, `external_assurance` |
| `priority` | HIGH = needed for 8-Test dimensions 4, 5, 7, 8; MEDIUM = useful but not blocking |
| `search_query_used` | Record the exact search string used to find the source |
| `source_found` | YES / NO |
| `source_title` | Title of the source document |
| `source_url` | Direct URL used to access or download the source |
| `date_accessed` | Date the source was accessed or downloaded |
| `downloaded_file_name` | Exact filename saved locally |
| `local_file_path` | Relative path to the saved file |
| `source_relevance` | HIGH / MEDIUM / LOW |
| `used_in_8_test` | YES / NO / PARTIAL — filled in after Claude Projects analysis |
| `notes` | Any flags, anomalies, or reviewer observations |

**Workflow:** rows with `source_found = NO` are your collection task list.
Work through HIGH priority gaps first. When you find and download a source, update
the row: fill in `source_url`, `date_accessed`, `downloaded_file_name`,
`local_file_path`, and change `source_found` to YES.

---

## rag_workflow_status.csv

Located at the project root. One row per company. Tracks the overall progress of
the RAG workflow for each company through to completion.

| Column | Meaning |
|--------|---------|
| `company_reports_audited` | YES once all available Tier 1 files are identified |
| `evidence_gap_log_created` | YES once `evidence_gap_log.md` exists in `rag_outputs/` |
| `external_evidence_collected` | NO / PARTIAL / YES based on how many Tier 2 gaps remain |
| `eight_test_completed` | YES once Claude Projects analysis is done and workbook filled |
| `human_verification_required` | Always YES — no 8-Test conclusion is accepted without human review |
| `human_verification_completed` | YES once the analyst has spot-checked quotes and page numbers |
| `status` | READY_FOR_8_TEST / IN_PROGRESS / COMPLETE / DOCUMENTS_NEEDED |

Update this file after completing each stage for each company.

---

## Auditability Rules

1. **Every 8-Test rating must be traceable.** For each PASS / PARTIAL / FAIL /
   MISSING rating entered in the RAG Screening Sheet, there must be a corresponding
   entry in `source_collection_tracker.csv` that identifies the source file and
   the local path where it is stored.

2. **Every quote must have a page number.** If Claude Projects returns a quote
   without a page number, verify manually before entering it in the workbook.

3. **Company reports are the starting point, not the conclusion.** A claim found
   only in a company's own sustainability report can support a PARTIAL rating at
   best. A PASS rating requires corroboration from an independent external source.

4. **MISSING means no evidence found — not that the evidence does not exist.**
   If a dimension is marked MISSING, record in the evidence gap log what sources
   were checked and what searches were attempted.

5. **No fabrication.** If a source URL, page number, quote, or finding cannot be
   verified from a real document in the `company_reports/` or `external_evidence/`
   folder, it must not appear in the workbook. Mark it MISSING.

6. **30% of all extractions must be manually verified** against the source PDF
   (check that the verbatim quote and page number match the actual document).
   100% of any company on the watchlist or exclusion list must be verified.

---

## Recommended Next Steps

1. Open `rag_workflow_status.csv` — identify all companies with status
   `READY_FOR_8_TEST` (those that have Tier 1 documents already).

2. For each company, open `rag_outputs/evidence_gap_log.md` and review the gap
   list. Collect HIGH-priority missing external sources (SBTi, CDP, GHG assurance)
   before running the Claude Projects analysis. Save them to `external_evidence/`
   with a `tier2_` prefix.

3. Open `TICKER_8test_prompt.txt`. Upload all PDFs from `company_reports/` and
   `external_evidence/` to a Claude Project for that company. Paste Step 5 of
   the prompt into the Claude Projects chat.

4. Copy the JSON output. Fill ratings into the RAG Screening Sheet workbook
   (columns CJ–CQ). Record key quotes, page numbers, and rationale.

5. Update `rag_outputs/evidence_gap_log.md` and `rag_workflow_status.csv` to
   reflect completion.

6. After all 20 companies are done, run notebook 09 to apply exclusion rules.

---

## IFX (Infineon Technologies) — Duplicate Flag

`IFX_Infineon_Technologies_AG` contains both:
- `company_reports/tier1_sustainability_report_2024.pdf`
- `external_evidence/tier2_sustainability_report_2024.pdf`

These files share an identical base name. They may be the same document saved
twice with different tier prefixes, or they may be different versions of the same
report. Do not delete either file until you have opened both and confirmed whether
they are identical. If they are identical, delete the `tier2_` copy and reclassify
the document as Tier 1 only.
