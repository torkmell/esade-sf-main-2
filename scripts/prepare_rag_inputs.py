#!/usr/bin/env python3
"""
RAG Preparation Workflow — scripts/prepare_rag_inputs.py

Semi-automated source tracking and prompt generation for the ESADE Sustainable
Finance pipeline. Prepares inputs for the manual 8-Test greenwashing screening.

Run from project root:
    python scripts/prepare_rag_inputs.py

What this does:
  1.  Reads the final portfolio (20 companies)
  2.  Creates data/rag/reports/{ticker}_{name}/ folders
  3.  Loads manual source URLs from data/rag/manual_source_urls.csv
  4.  Attempts PDF downloads where direct links are provided
  5.  Pulls Tier 3 context from outputs/scores/ CSVs
  6.  Writes outputs/rag/source_register.csv  (machine-managed audit trail)
  7.  Generates {ticker}_8test_prompt.txt per company folder
  8.  Creates outputs/rag/rag_screening_summary.csv  (empty template)
  9.  Initialises outputs/rag/portfolio_change_log.csv  (headers only)

What this does NOT do:
  - Write to or modify the RAG Screening Sheet workbook
  - Overwrite analyst judgements, ratings, or verdicts
  - Run greenwashing scoring
  - Change portfolio weights or selection logic
"""

import csv
import glob
import json
import logging
import os
import re
import sys
from datetime import date, datetime
from pathlib import Path

# ── optional dependencies ──────────────────────────────────────────────────────
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    print("ERROR: pandas is required.  Activate the project venv and retry.")
    sys.exit(1)

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# ─── PATHS ─────────────────────────────────────────────────────────────────────
ROOT          = Path(__file__).resolve().parent.parent
DATA_RAG      = ROOT / "data"  / "rag"
REPORTS_DIR   = DATA_RAG / "reports"
OUTPUTS_RAG   = ROOT / "outputs" / "rag"
OUTPUTS_PORT  = ROOT / "outputs" / "portfolio"
OUTPUTS_SCORE = ROOT / "outputs" / "scores"

MANUAL_URLS = DATA_RAG / "manual_source_urls.csv"
SOURCE_REG  = OUTPUTS_RAG / "source_register.csv"
RAG_SUMMARY = OUTPUTS_RAG / "rag_screening_summary.csv"
CHANGE_LOG  = OUTPUTS_RAG / "portfolio_change_log.csv"

TODAY = str(date.today())
NOW   = datetime.now().isoformat(timespec="seconds")
DOWNLOAD_TIMEOUT = 30
MAX_PDF_MB       = 50

# ─── LOGGING ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ─── 8-TEST FRAMEWORK ──────────────────────────────────────────────────────────
EIGHT_TESTS = [
    ("SPECIFICITY",
     "  PASS:    Named asset / product / division with exact, verifiable claim.\n"
     "  PARTIAL: General direction stated with some constraint.\n"
     "  FAIL:    'Committed to sustainability' or equivalent vague language only.\n"
     "  MISSING: No sustainability claim found in documents reviewed."),

    ("METRIC",
     "  PASS:    Specific number with unit and context (%, tCO₂e, GWh, m³, etc.).\n"
     "  PARTIAL: Direction stated but no quantity given.\n"
     "  FAIL:    Number present but misleading or restated after restructuring.\n"
     "  MISSING: No quantitative data found on this topic."),

    ("BASELINE",
     "  PASS:    Explicit baseline year + value, stable methodology.\n"
     "  PARTIAL: Baseline year stated but no value; or methodology changed.\n"
     "  FAIL:    Baseline cherry-picked or shifted post-acquisition/disposal.\n"
     "  MISSING: No baseline information in documents reviewed."),

    ("TARGET",
     "  PASS:    SBTi-approved OR legally binding OR board-approved with governance.\n"
     "  PARTIAL: Company-stated target only, non-binding.\n"
     "  FAIL:    No target exists; or target contradicts stated behaviour.\n"
     "  MISSING: No target information found."),

    ("TIME HORIZON",
     "  PASS:    Near-term date ≤2030 with reported interim progress.\n"
     "  PARTIAL: Long-term date only (>2040); or near-term with no progress reported.\n"
     "  FAIL:    No date given; or date stated with no evidence of progress.\n"
     "  MISSING: No time-related information found."),

    ("SCOPE",
     "  PASS:    Named entities, Scopes 1/2/3, geographies all clearly defined.\n"
     "  PARTIAL: 'Most operations' or 'core business' without clear definition.\n"
     "  FAIL:    Ambiguous scope likely excluding problem assets or activities.\n"
     "  MISSING: No scope definition found."),

    ("VERIFICATION",
     "  PASS:    Named verifier + standard (ISAE 3000/3410) + reasonable assurance.\n"
     "  PARTIAL: Limited assurance only; or verification of a subset of data only.\n"
     "  FAIL:    Self-reported only; or 'reviewed by management' with no external party.\n"
     "  MISSING: No assurance statement found in documents reviewed."),

    ("CONSISTENCY",
     "  PASS:    Capex aligned with claims; no contradictory lobbying; no controversy.\n"
     "  PARTIAL: Some capex misalignment; minor contradiction; minor controversy.\n"
     "  FAIL:    Capex directly contradicts claim; active contradictory lobbying; severe controversy.\n"
     "  MISSING: Insufficient capex or lobbying disclosure to assess."),
]

JSON_SCHEMA = """{
  "ticker": "<BLOOMBERG_TICKER>",
  "company_name": "<COMPANY_NAME>",
  "extraction_date": "<YYYY-MM-DD>",
  "analyst_note": "<overall assessment, 1-2 sentences>",
  "dimensions": {
    "specificity":  {"quote": null, "page": null, "value": null, "rating": "PASS|PARTIAL|FAIL|MISSING", "reasoning": ""},
    "metric":       {"quote": null, "page": null, "value": null, "rating": "PASS|PARTIAL|FAIL|MISSING", "reasoning": ""},
    "baseline":     {"quote": null, "page": null, "value": null, "rating": "PASS|PARTIAL|FAIL|MISSING", "reasoning": ""},
    "target":       {"quote": null, "page": null, "value": null, "rating": "PASS|PARTIAL|FAIL|MISSING", "reasoning": ""},
    "time_horizon": {"quote": null, "page": null, "value": null, "rating": "PASS|PARTIAL|FAIL|MISSING", "reasoning": ""},
    "scope":        {"quote": null, "page": null, "value": null, "rating": "PASS|PARTIAL|FAIL|MISSING", "reasoning": ""},
    "verification": {"quote": null, "page": null, "value": null, "rating": "PASS|PARTIAL|FAIL|MISSING", "reasoning": ""},
    "consistency":  {"quote": null, "page": null, "value": null, "rating": "PASS|PARTIAL|FAIL|MISSING", "reasoning": ""}
  }
}"""

SOURCE_REG_FIELDS = [
    "bloomberg_ticker", "yf_ticker", "company_name",
    "source_tier", "source_type", "source_title", "source_year",
    "source_url", "local_path", "download_status",
    "source_quality_flag", "manually_verified", "verification_notes",
    "ingestion_timestamp",
]

SUMMARY_FIELDS = [
    "bloomberg_ticker", "company_name", "final_rag_verdict",
    "greenwashing_risk_score", "worst_dimension", "watchlist_trigger",
    "exclusion_trigger", "evidence_confidence", "verification_status",
    "key_evidence_quote", "source_document",
]

CHANGE_LOG_FIELDS = [
    "timestamp", "bloomberg_ticker", "company_name",
    "previous_status", "new_status", "action_taken",
    "triggering_module", "triggering_reason",
    "supporting_evidence_summary", "source_document", "source_url",
    "evidence_confidence", "analyst_override", "override_reason",
    "replacement_company_if_any",
]


# ─── HELPERS ───────────────────────────────────────────────────────────────────

def clean_name(name):
    s = re.sub(r"[^\w\s-]", "", str(name))
    s = re.sub(r"\s+", "_", s.strip())
    return s[:40]


def folder_name(ticker, name):
    return f"{ticker}_{clean_name(name)}"


def sfmt(v, spec=".1f", default="N/A"):
    try:
        return format(float(v), spec)
    except (TypeError, ValueError):
        return default


# ─── DATA LOADERS ──────────────────────────────────────────────────────────────

def load_portfolio():
    files = sorted(glob.glob(str(OUTPUTS_PORT / "final_portfolio_*.csv")))
    if not files:
        log.error(f"No final_portfolio_*.csv found in {OUTPUTS_PORT}")
        sys.exit(1)
    df = pd.read_csv(files[-1])
    log.info(f"Portfolio: {Path(files[-1]).name}  ({len(df)} companies)")
    return df


def load_scores():
    scores = {}
    for key, pat in [
        ("esg",          "esg_scores_*.csv"),
        ("biodiversity", "biodiversity_scores_*.csv"),
        ("eu",           "eu_regulation_*.csv"),
        ("financial",    "financial_metrics_*.csv"),
    ]:
        files = sorted(glob.glob(str(OUTPUTS_SCORE / pat)))
        if files:
            scores[key] = pd.read_csv(files[-1])
            log.info(f"  Scores/{key}: {Path(files[-1]).name}")
    return scores


def get_tier3(row, scores):
    bb   = str(row["ticker"])
    yf   = str(row.get("yf_ticker", ""))
    lines = [
        "TIER 3 — QUANTITATIVE CONTEXT FROM PIPELINE DATA",
        "(Cross-check consistency with company claims. Do not cite as primary evidence.)",
        "",
    ]
    if "esg" in scores:
        r = scores["esg"][scores["esg"]["ticker"] == bb]
        if not r.empty:
            r = r.iloc[0]
            lines += [
                f"  ESG Score:          {sfmt(r.get('ESG_score'))} / 100",
                f"    E Score:          {sfmt(r.get('E_score'))}",
                f"    S Score:          {sfmt(r.get('S_score'))}",
                f"    G Score:          {sfmt(r.get('G_score'))}",
                f"  Carbon Intensity:   {sfmt(r.get('carbon_intensity'))} tCO₂e/€m rev"
                f"  [source: {r.get('ci_source','N/A')}]",
            ]
        else:
            lines.append("  ESG data: NOT FOUND")

    if "financial" in scores:
        r = scores["financial"][scores["financial"]["ticker"] == yf]
        if not r.empty:
            r = r.iloc[0]
            lines += [
                f"  Sharpe Ratio:       {sfmt(r.get('sharpe_ratio'), '.3f')}",
                f"  Annual Return:      {sfmt(r.get('annual_return_pct'))}%",
                f"  Annual Volatility:  {sfmt(r.get('annual_volatility_pct'))}%",
            ]

    if "biodiversity" in scores:
        r = scores["biodiversity"][scores["biodiversity"]["ticker"] == bb]
        if not r.empty:
            r = r.iloc[0]
            lines += [
                f"  Nature Risk Tier:   {r.get('nature_risk_tier', 'N/A')}",
                f"  Biodiversity Score: {sfmt(r.get('biodiversity_score'))}",
                f"  ENCORE Score:       {sfmt(r.get('encore_score'))}",
                f"  WRI Aqueduct Score: {sfmt(r.get('aqueduct_score'))}",
            ]

    if "eu" in scores:
        r = scores["eu"][scores["eu"]["ticker"] == bb]
        if not r.empty:
            r = r.iloc[0]
            lines += [
                f"  EU Taxonomy Eligible: {sfmt(r.get('taxonomy_eligible_pct'))}%",
                f"  EU Taxonomy Aligned:  {sfmt(r.get('taxonomy_aligned_pct'))}%",
            ]

    return "\n".join(lines)


def load_manual_urls():
    urls = {}
    if not MANUAL_URLS.exists():
        log.warning(f"manual_source_urls.csv not found — no pre-registered sources")
        return urls
    with open(MANUAL_URLS, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            tick = (row.get("bloomberg_ticker") or "").strip()
            if tick:
                urls.setdefault(tick, []).append(row)
    total = sum(len(v) for v in urls.values())
    log.info(f"Manual URLs: {total} entries for {len(urls)} tickers")
    return urls


# ─── DOWNLOAD ──────────────────────────────────────────────────────────────────

def safe_download(url, dest, ticker, title):
    """Attempt PDF download. Returns (status, notes). Never raises."""
    if not HAS_REQUESTS:
        return "NOT_ATTEMPTED", "requests not installed — pip install requests"
    if not url or url.strip().upper() in ("", "N/A", "PENDING", "TBD"):
        return "NOT_ATTEMPTED", "No URL provided"
    try:
        resp = requests.get(
            url.strip(), timeout=DOWNLOAD_TIMEOUT,
            headers={"User-Agent": "ESADE-Finance-Research/1.0"},
            stream=True, allow_redirects=True,
        )
        if resp.status_code != 200:
            return "FAILED", f"HTTP {resp.status_code}"
        ct = resp.headers.get("content-type", "")
        if "pdf" not in ct.lower() and not url.lower().endswith(".pdf"):
            return "FAILED", f"Not a PDF (content-type: {ct[:50]})"
        cl = int(resp.headers.get("content-length", 0))
        if cl and cl / 1_048_576 > MAX_PDF_MB:
            return "FAILED", f"File exceeds {MAX_PDF_MB} MB limit"
        Path(dest).parent.mkdir(parents=True, exist_ok=True)
        with open(dest, "wb") as f:
            for chunk in resp.iter_content(8192):
                f.write(chunk)
        size_mb = Path(dest).stat().st_size / 1_048_576
        return "DOWNLOADED", f"{size_mb:.1f} MB"
    except Exception as exc:
        return "FAILED", str(exc)[:120]


# ─── PROMPT GENERATION ─────────────────────────────────────────────────────────

def fmt_sources(entries, tier_label):
    if not entries:
        return f"  [No {tier_label} sources collected yet — download and save to this company folder]"
    lines = []
    for e in entries:
        title  = e.get("source_title", "Untitled")
        year   = e.get("source_year", "")
        stype  = e.get("source_type", "")
        local  = e.get("local_path", "")
        line   = f"  • {title}"
        if year:  line += f" ({year})"
        if stype: line += f"  [{stype}]"
        if local:
            line += f"\n    Local: {local}"
        lines.append(line)
    return "\n".join(lines)


def generate_prompt(row, manual_urls, scores, folder):
    bb   = str(row["ticker"])
    yf   = str(row.get("yf_ticker", ""))
    name = str(row.get("idBbGlobalCompanyName", bb))
    sect = str(row.get("bics_sector", ""))
    wt   = float(row.get("weight", 0)) * 100

    t1 = [e for e in manual_urls.get(bb, []) if e.get("source_tier", "") == "Tier 1"]
    t2 = [e for e in manual_urls.get(bb, []) if e.get("source_tier", "") == "Tier 2"]

    test_blocks = "\n\n".join(
        f"  DIMENSION {i+1} — {dname}\n{criteria}"
        for i, (dname, criteria) in enumerate(EIGHT_TESTS)
    )
    tier3_text = get_tier3(row, scores)

    sep = "=" * 70

    lines = [
        sep,
        "ESADE SUSTAINABLE FINANCE — 8-TEST GREENWASHING ANALYSIS PROMPT",
        sep,
        f"Company:              {name}",
        f"Bloomberg Ticker:     {bb}",
        f"Yahoo Finance Ticker: {yf}",
        f"Sector:               {sect}",
        f"Portfolio Weight:     {wt:.1f}%",
        f"Analysis Date:        {TODAY}",
        f"Company Folder:       data/rag/reports/{folder.name}/",
        "",
        sep,
        "STEP 1 — UPLOAD TIER 1 SOURCES TO CLAUDE PROJECTS",
        sep,
        f"Tier 1 = primary company disclosures. Upload these PDFs to a dedicated",
        f"Claude Project for {name} before running the analysis prompt.",
        "",
        fmt_sources(t1, "Tier 1"),
        "",
        "Document types to collect (most recent year available):",
        "  • Sustainability / ESG report",
        "  • Annual report (sustainability and climate sections)",
        "  • TCFD report or standalone climate disclosure",
        "  • CSRD / ESRS disclosure (if published)",
        "  • SBTi commitment letter or CDP submission",
        "",
        "MANDATORY naming convention — files MUST start with tier1_:",
        f"    tier1_sustainability_report_YYYY.pdf",
        f"    tier1_annual_report_YYYY.pdf",
        f"    tier1_climate_report_YYYY.pdf",
        f"  → Save to:  data/rag/reports/{folder.name}/",
        "  → Upload to the Claude Project for this company.",
        "",
        sep,
        "STEP 2 — COLLECT TIER 2 EXTERNAL SOURCES",
        sep,
        "Tier 2 = external verification. Use to challenge or corroborate Tier 1 claims.",
        "Do NOT substitute for Tier 1. Do NOT treat as primary evidence.",
        "",
        fmt_sources(t2, "Tier 2"),
        "",
        "Sources to collect:",
        "  • SBTi target dashboard:  sciencebasedtargets.org/companies",
        "  • CDP score and response:  cdp.net",
        "  • NGO investigative reports (ClientEarth, InfluenceMap, etc.)",
        "  • Regulatory enforcement actions (EU, national regulators)",
        "  • Credible news investigations (FT, Reuters, Bloomberg Green)",
        "",
        "MANDATORY naming convention — files MUST start with tier2_:",
        f"    tier2_sbti_dashboard_YYYY.pdf",
        f"    tier2_cdp_response_YYYY.pdf",
        f"    tier2_ngo_report_YYYY.pdf",
        f"  → Save to:  data/rag/reports/{folder.name}/",
        "  → Upload to the same Claude Project as the Tier 1 documents.",
        "",
        sep,
        "STEP 3 — TIER 3 QUANTITATIVE CONTEXT (from pipeline data)",
        sep,
        tier3_text,
        "",
        sep,
        "STEP 4 — ANTI-HALLUCINATION RULES  (read before starting)",
        sep,
        "1.  NEVER invent quotes, page numbers, or evidence.",
        "2.  NEVER fabricate source metadata or citations.",
        "3.  NEVER infer ESG claims not explicitly stated in the documents.",
        "4.  NEVER create synthetic citations or fake references.",
        "5.  Mark ALL missing evidence as:       MISSING",
        "6.  Mark ALL unverified information as: UNVERIFIED",
        "7.  If a source cannot be accessed, do NOT guess its contents.",
        "8.  Separate Tier 1 claims from Tier 2 verification explicitly.",
        "9.  If evidence is ambiguous, state the ambiguity — do not resolve it.",
        "10. Include direct verbatim quotes with page numbers wherever available.",
        "",
        sep,
        "STEP 5 — PASTE THIS PROMPT INTO CLAUDE PROJECTS",
        sep,
        "(Upload Tier 1 PDFs to the Claude Project first, then paste this prompt.)",
        "",
        f"You are an ESG forensic analyst. Using ONLY the documents in this project,",
        f"assess {name} ({bb}) across 8 greenwashing dimensions.",
        "Do not use prior knowledge not grounded in the uploaded documents.",
        "",
        "DOCUMENT HIERARCHY — read this before analysing any file:",
        "  Documents are named with a prefix that defines their authority level.",
        "",
        "  tier1_*  =  Primary company disclosures (sustainability reports, annual",
        "               reports, TCFD, CSRD). These are AUTHORITATIVE.",
        "               → Quote directly with page numbers.",
        "               → Use as primary evidence for all 8 dimensions.",
        "",
        "  tier2_*  =  External verification (SBTi, CDP, NGO, news investigations).",
        "               → Use ONLY to corroborate or challenge Tier 1 claims.",
        "               → NEVER cite as primary evidence.",
        "               → NEVER use to override a Tier 1 finding.",
        "",
        "  No prefix  =  Treat as Tier 1 (conservative default).",
        "",
        "  Hierarchy rules you must follow:",
        "    1. A claim found in tier1_* is primary evidence — cite it.",
        "    2. A claim found ONLY in tier2_* must be flagged explicitly:",
        '       "Tier 2 only — no Tier 1 corroboration found."',
        "    3. If tier1_* and tier2_* contradict each other, flag the",
        "       contradiction explicitly — do not silently resolve it.",
        "    4. A Goldman Sachs report, analyst note, or news article uploaded",
        "       as tier2_* is supporting context only, never authoritative.",
        "",
        "For each dimension provide:",
        "  (a) Direct verbatim quote from a tier1_* source, with page number",
        "  (b) Corroboration or contradiction from tier2_* sources (if available)",
        "  (c) Rating: PASS / PARTIAL / FAIL / MISSING",
        "  (d) Reasoning in 2-3 sentences",
        "",
        "Anti-hallucination rules:",
        "  - Never invent quotes, page numbers, or source references.",
        "  - Never infer claims not explicitly stated in the documents.",
        "  - Mark missing evidence as MISSING — never guess.",
        "  - State ambiguity explicitly; do not resolve it artificially.",
        "  - Always identify which tier a source belongs to when citing it.",
        "",
        "Quantitative context from pipeline data (do not cite as primary evidence):",
        tier3_text,
        "",
        "8-TEST FRAMEWORK:",
        "",
        test_blocks,
        "",
        "Output ONLY valid JSON in exactly this structure:",
        "",
        JSON_SCHEMA,
        "",
        sep,
        "STEP 6 — FILL IN THE RAG WORKBOOK",
        sep,
        "After completing the Claude Projects analysis:",
        "",
        "  1. Open:  data/rag/RAG_Screening_Sheet_Workbook_v1.xlsx",
        "  2. Sheet: RAG Screening Sheet",
        f"  3. Find the row for Bloomberg ticker: {bb}",
        "  4. Enter ratings in the 8-Test columns:",
        "       CJ — 8-Test 1: Specificity     →  PASS / PARTIAL / FAIL / MISSING",
        "       CK — 8-Test 2: Metric          →  PASS / PARTIAL / FAIL / MISSING",
        "       CL — 8-Test 3: Baseline        →  PASS / PARTIAL / FAIL / MISSING",
        "       CM — 8-Test 4: Target          →  PASS / PARTIAL / FAIL / MISSING",
        "       CN — 8-Test 5: Time Horizon    →  PASS / PARTIAL / FAIL / MISSING",
        "       CO — 8-Test 6: Scope           →  PASS / PARTIAL / FAIL / MISSING",
        "       CP — 8-Test 7: Verification    →  PASS / PARTIAL / FAIL / MISSING",
        "       CQ — 8-Test 8: Consistency     →  PASS / PARTIAL / FAIL / MISSING",
        "  5. Key evidence quote              →  column DC",
        "  6. Evidence page reference         →  column DE",
        "  7. Verdict rationale               →  column DX",
        "  8. Evidence Confidence (1-5)       →  column DF",
        "  9. Verification Status             →  column DH",
        " 10. Save the workbook.",
        "",
        "IMPORTANT: The workbook is the authoritative human-reviewed layer.",
        "Automation never overwrites analyst judgements.",
        "",
        sep,
        "STEP 7 — SAVE JSON OUTPUT (optional but recommended)",
        sep,
        f"Save the completed JSON to: outputs/rag/greenwash_{bb}.json",
        "Notebook 09 reads both the workbook and JSON files.",
        "The workbook takes priority if both exist for the same ticker.",
        "",
    ]
    return "\n".join(lines)


# ─── OUTPUTS ───────────────────────────────────────────────────────────────────

def write_source_register(portfolio, manual_urls, download_log):
    rows = []
    ticker_info = {r["ticker"]: r for _, r in portfolio.iterrows()}

    # Entries from manual_source_urls.csv
    for bb, entries in manual_urls.items():
        info = ticker_info.get(bb, {})
        yf   = str(info.get("yf_ticker", "")) if hasattr(info, "get") else ""
        name = str(info.get("idBbGlobalCompanyName", bb)) if hasattr(info, "get") else bb
        for e in entries:
            url = (e.get("source_url") or "").strip()
            key = f"{bb}|{e.get('source_type','')}|{url}"
            dl_status, dl_notes = download_log.get(key, ("NOT_ATTEMPTED", ""))
            local = e.get("local_path", "")
            rows.append({
                "bloomberg_ticker":    bb,
                "yf_ticker":           yf,
                "company_name":        name,
                "source_tier":         e.get("source_tier", ""),
                "source_type":         e.get("source_type", ""),
                "source_title":        e.get("source_title", ""),
                "source_year":         e.get("source_year", ""),
                "source_url":          url,
                "local_path":          local,
                "download_status":     dl_status,
                "source_quality_flag": e.get("source_quality_flag", ""),
                "manually_verified":   "",
                "verification_notes":  dl_notes or e.get("notes", ""),
                "ingestion_timestamp": NOW,
            })

    # Tier 3 reference row per portfolio company
    for _, r in portfolio.iterrows():
        rows.append({
            "bloomberg_ticker":    r["ticker"],
            "yf_ticker":           r.get("yf_ticker", ""),
            "company_name":        r.get("idBbGlobalCompanyName", r["ticker"]),
            "source_tier":         "Tier 3",
            "source_type":         "pipeline_scores",
            "source_title":        "ESADE Pipeline — ESG / Financial / Biodiversity / EU Taxonomy CSVs",
            "source_year":         TODAY[:4],
            "source_url":          "",
            "local_path":          "outputs/scores/",
            "download_status":     "AVAILABLE",
            "source_quality_flag": "PIPELINE_GENERATED",
            "manually_verified":   "N/A",
            "verification_notes":  (
                "Machine-generated from Bloomberg ESG + Yahoo Finance + "
                "ENCORE + EU Taxonomy. Not primary evidence."
            ),
            "ingestion_timestamp": NOW,
        })

    OUTPUTS_RAG.mkdir(parents=True, exist_ok=True)
    with open(SOURCE_REG, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=SOURCE_REG_FIELDS)
        w.writeheader()
        w.writerows(rows)
    log.info(f"Source register: {SOURCE_REG.name}  ({len(rows)} entries)")


def init_rag_summary(portfolio):
    if RAG_SUMMARY.exists():
        log.info(f"rag_screening_summary.csv already exists — not overwriting")
        return
    rows = []
    for _, r in portfolio.iterrows():
        rows.append({
            "bloomberg_ticker":       r["ticker"],
            "company_name":           r.get("idBbGlobalCompanyName", r["ticker"]),
            "final_rag_verdict":      "PENDING",
            "greenwashing_risk_score": "",
            "worst_dimension":        "",
            "watchlist_trigger":      "",
            "exclusion_trigger":      "",
            "evidence_confidence":    "",
            "verification_status":    "",
            "key_evidence_quote":     "",
            "source_document":        "",
        })
    with open(RAG_SUMMARY, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=SUMMARY_FIELDS)
        w.writeheader()
        w.writerows(rows)
    log.info(f"RAG summary template: {RAG_SUMMARY.name}  ({len(rows)} rows)")


def init_change_log():
    if CHANGE_LOG.exists():
        log.info(f"portfolio_change_log.csv already exists — not overwriting")
        return
    with open(CHANGE_LOG, "w", newline="", encoding="utf-8") as f:
        csv.DictWriter(f, fieldnames=CHANGE_LOG_FIELDS).writeheader()
    log.info(f"Portfolio change log initialised: {CHANGE_LOG.name}")


# ─── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    log.info("=" * 60)
    log.info("RAG Preparation Workflow — ESADE Sustainable Finance")
    log.info("=" * 60)

    OUTPUTS_RAG.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    portfolio   = load_portfolio()
    scores      = load_scores()
    manual_urls = load_manual_urls()
    download_log = {}

    log.info(f"\nProcessing {len(portfolio)} companies...\n")

    for _, row in portfolio.iterrows():
        bb   = str(row["ticker"])
        name = str(row.get("idBbGlobalCompanyName", bb))
        wt   = float(row.get("weight", 0)) * 100
        fn   = folder_name(bb, name)
        folder = REPORTS_DIR / fn

        log.info(f"  {bb:<6}  {name:<35}  {wt:.1f}%")
        folder.mkdir(parents=True, exist_ok=True)

        # Attempt downloads for manual URLs
        for e in manual_urls.get(bb, []):
            url    = (e.get("source_url") or "").strip()
            stype  = (e.get("source_type") or "document").lower()
            stier  = (e.get("source_tier") or "tier1").replace(" ", "").lower()
            syear  = e.get("source_year", TODAY[:4])
            title  = e.get("source_title", "report")
            _safe  = re.sub(r"[^\w-]", "_", title)[:35]
            fname  = f"{stier}_{_safe}_{syear}.pdf"
            dest   = folder / fname

            if dest.exists():
                e["local_path"] = str(dest.relative_to(ROOT))
                download_log[f"{bb}|{stype}|{url}"] = ("ALREADY_EXISTS", "")
            else:
                status, notes = safe_download(url, dest, bb, title)
                e["local_path"] = str(dest.relative_to(ROOT)) if dest.exists() else ""
                download_log[f"{bb}|{stype}|{url}"] = (status, notes)
                if status == "DOWNLOADED":
                    log.info(f"    ✓ Downloaded: {fname}")
                elif status == "FAILED":
                    log.warning(f"    ✗ Download failed ({title}): {notes}")

        # Generate 8-test prompt
        prompt = generate_prompt(row, manual_urls, scores, folder)
        prompt_file = folder / f"{bb}_8test_prompt.txt"
        with open(prompt_file, "w", encoding="utf-8") as f:
            f.write(prompt)

    log.info("")
    write_source_register(portfolio, manual_urls, download_log)
    init_rag_summary(portfolio)
    init_change_log()

    log.info("")
    log.info("=" * 60)
    log.info("Done. Files written:")
    log.info(f"  Company folders:  data/rag/reports/  ({len(portfolio)} folders)")
    log.info(f"  8-Test prompts:   {{ticker}}_8test_prompt.txt  (one per company)")
    log.info(f"  Source register:  outputs/rag/source_register.csv")
    log.info(f"  RAG summary:      outputs/rag/rag_screening_summary.csv")
    log.info(f"  Change log:       outputs/rag/portfolio_change_log.csv")
    log.info("")
    log.info("Next steps:")
    log.info("  1. For each company: download PDFs from the company IR page.")
    log.info("     Name them tier1_sustainability_report_YYYY.pdf etc.")
    log.info("     Save to data/rag/reports/{ticker}_*/")
    log.info("  2. Upload PDFs to Claude Projects for that company.")
    log.info("  3. Open {ticker}_8test_prompt.txt, paste Step 5 into Claude Projects.")
    log.info("  4. Fill ratings into the RAG Screening Sheet workbook.")
    log.info("  5. Run notebooks in order: 09 → 10 → 12")
    log.info("=" * 60)


if __name__ == "__main__":
    main()
