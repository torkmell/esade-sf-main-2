# External Evidence Search Plan
## ESADE Sustainable Finance — 8-Test Greenwashing Screen
**Created:** 2026-05-16  
**Purpose:** Guide efficient collection of external evidence for 20 portfolio holdings  
**Status:** 219 open gaps across 20 companies (source_collection_tracker.csv)

---

## How to Use This Plan

Work **by source type batch**, not company by company. Each source type (SBTi, CDP, TPI) can be checked for all 20 companies in a single session at the same website.

When you find a source:
1. Save PDF to `data/rag/reports/{FOLDER}/external_evidence/`
2. Rename using convention: `companyname_source-type_description_year.pdf`
3. For non-PDF sources (dashboards, webpages): create a source note `.md` file instead
4. Update `source_collection_tracker.csv` row: fill `source_url`, `date_accessed`, `downloaded_file_name`, `local_file_path`, set `source_found = YES`
5. If not found: set `source_found = NO`, fill `search_query_used`, note what was checked

---

## Company Tier Classification

Tier A = final holding with material climate claims AND/OR high sector controversy risk → 3–5 sources  
Tier B = final holding with moderate claims or lower controversy risk → 2–3 sources  
Tier C = holding with very limited ESG exposure or minimal sustainability claims → 1–2 sources

| Ticker | Company | Tier | Rationale |
|--------|---------|------|-----------|
| SKWA | SSAB AB | A | HYBRIT fossil-free steel is the core claim; heavy industry; no SBTi or GHG assurance confirmed |
| 9TG | Gaztransport Et Technigaz SA | A | LNG sector; transition plan present but unvalidated; high greenwashing risk in energy |
| IHCB | SBM Offshore NV | A | Offshore oil/gas equipment; scope 3 flag; energy sector transition risk |
| NOH1 | Norsk Hydro ASA | A | Aluminum heavy industry; 81 carbon mentions + renewable claims; biodiversity risk |
| G7W | Games Workshop Group PLC | A | Highest portfolio weight (6.18%); net zero 2050 claim but NO 2030 milestone found — red flag |
| BSI | BE Semiconductor Industries NV | A | Net zero claim + no near-term milestone; SBTi unvalidated; semiconductor water use |
| IFX | Infineon Technologies AG | A | "72.5% by 2030" target stated; needs SBTi confirmation; richest sustainability report |
| SOAN | UnipolSai Assicurazioni SpA | A | 3 risk flags: no SBTi, no GHG assurance, net zero claim unvalidated; insurance sector |
| ASME | ASML Holding NV | B | TCFD report exists; well-documented; SBTi unconfirmed |
| AVS | ASM International NV | B | CDP response already present; still needs TPI and controversy check |
| IGQ5 | 3i Group PLC | B | PE firm; portfolio-level SBTi reference found; "ten23" subsidiary SBTi mentioned |
| MLT | Mycronic AB | B | Climate target claim; SBTi mentioned in docs but not confirmed externally |
| DP9 | Diploma PLC | B | SBTi and net zero stated in short sustainability report; needs external confirmation |
| 2NN | NN Group NV | B | Insurance/financials; assurance claims in report; controversy check needed |
| 1SQ | Swissquote Group Holding SA | B | Financial sector; rich sustainability report with assurance; needs external validation |
| 2FE | Ferrari NV | B | Image-heavy PDF issue (4 risk flags); consumer discretionary; limited claims to verify |
| SGM | STMicroelectronics NV | B | "Carbon neutral" claim present; semiconductor; sustainability-at-a-glance document |
| 19V | VAT Group AG | C | Swiss semiconductor; moderate sustainability content; limited controversy risk |
| CJ2 | Ringkjoebing Landbobank A/S | C | Danish bank; extremely sparse ESG — only CSRD mention; no substantive claims to test |
| 1AE | Argenx SE | C | Pharmaceutical/biotech; minimal climate exposure; only 2030 mention |

---

## Batch 1 — SBTi Target Dashboard (Priority: HIGH)
**Where:** science-basedtargets.org → Companies tab → search each company name  
**Format:** Dashboard/webpage — create source note `.md` for each result  
**Time estimate:** 20–30 minutes for all 20 companies  
**8-test use:** Test 4 (time horizon), Test 5 (external validation), Test 6 (scope)

Check each company below. For each: note whether they have (a) a committed target, (b) a validated near-term target, (c) a validated long-term/net zero target, or (d) no target listed.

| Ticker | Company | SBTi search name | Priority |
|--------|---------|-----------------|---------|
| SKWA | SSAB AB | "SSAB" | HIGH |
| G7W | Games Workshop Group PLC | "Games Workshop" | HIGH |
| BSI | BE Semiconductor Industries NV | "BE Semiconductor" OR "Besi" | HIGH |
| IFX | Infineon Technologies AG | "Infineon Technologies" | HIGH |
| SOAN | UnipolSai Assicurazioni SpA | "UnipolSai" OR "Unipol" | HIGH |
| 9TG | Gaztransport Et Technigaz SA | "Gaztransport" OR "GTT" | HIGH |
| IHCB | SBM Offshore NV | "SBM Offshore" | HIGH |
| NOH1 | Norsk Hydro ASA | "Norsk Hydro" | HIGH |
| ASME | ASML Holding NV | "ASML" | HIGH |
| AVS | ASM International NV | "ASM International" | HIGH |
| IGQ5 | 3i Group PLC | "3i Group" | HIGH |
| MLT | Mycronic AB | "Mycronic" | HIGH |
| DP9 | Diploma PLC | "Diploma" | HIGH |
| 2NN | NN Group NV | "NN Group" | MEDIUM |
| 1SQ | Swissquote Group Holding SA | "Swissquote" | MEDIUM |
| 2FE | Ferrari NV | "Ferrari" | MEDIUM |
| SGM | STMicroelectronics NV | "STMicroelectronics" | MEDIUM |
| 19V | VAT Group AG | "VAT Group" | MEDIUM |
| CJ2 | Ringkjoebing Landbobank A/S | "Ringkjoebing Landbobank" | LOW |
| 1AE | Argenx SE | "argenx" | LOW |

**File naming:** `{companyname}_sbti_dashboard_note_{year}.md`  
**Examples:**  
- `ssab_sbti_dashboard_note_2026.md`  
- `games_workshop_sbti_dashboard_note_2026.md`

---

## Batch 2 — CDP Climate Score (Priority: HIGH)
**Where:** cdp.net → scores/data → search company; also check if company published a CDP response  
**Note:** CDP scores are often paywalled. Check if your institution has access. The score letter (A/A-/B/B-/C/D/F) is sometimes publicly listed.  
**Format:** Webpage or PDF — source note if webpage, download if PDF available  
**8-test use:** Test 5 (external validation), Test 7 (consistency — capex vs. claims)

| Ticker | Company | CDP search name | Priority |
|--------|---------|----------------|---------|
| SKWA | SSAB AB | "SSAB AB" | HIGH |
| G7W | Games Workshop Group PLC | "Games Workshop" | HIGH |
| BSI | BE Semiconductor Industries NV | "Besi" OR "BE Semiconductor" | HIGH |
| IFX | Infineon Technologies AG | "Infineon" | HIGH |
| SOAN | UnipolSai Assicurazioni SpA | "UnipolSai" | HIGH |
| 9TG | Gaztransport Et Technigaz SA | "GTT" | HIGH |
| IHCB | SBM Offshore NV | "SBM Offshore" | HIGH |
| NOH1 | Norsk Hydro ASA | "Norsk Hydro" | HIGH |
| ASME | ASML Holding NV | "ASML" | HIGH |
| IGQ5 | 3i Group PLC | "3i Group" | HIGH |
| MLT | Mycronic AB | "Mycronic" | HIGH |
| DP9 | Diploma PLC | "Diploma" | HIGH |
| 2NN | NN Group NV | "NN Group" | MEDIUM |
| 1SQ | Swissquote Group Holding SA | "Swissquote" | MEDIUM |
| 2FE | Ferrari NV | "Ferrari NV" | MEDIUM |
| SGM | STMicroelectronics NV | "STMicroelectronics" | MEDIUM |
| CJ2 | Ringkjoebing Landbobank A/S | "Ringkjoebing" | LOW |
| 1AE | Argenx SE | "argenx" | LOW |
| 19V | VAT Group AG | "VAT Group" | LOW |
| AVS | ASM International NV | Already has CDP response in company_reports | SKIP |

**File naming:** `{companyname}_cdp_climate_score_note_{year}.md` or `{companyname}_cdp_climate_score_{year}.pdf`

---

## Batch 3 — Transition Pathway Initiative (Priority: MEDIUM)
**Where:** transitionpathwayinitiative.org → Assessments → search company  
**Note:** TPI covers energy, materials, industrials, financials, and selected other sectors. Tech/pharma companies may not be listed. If not listed, note "Not covered by TPI" in the source note.  
**Format:** Webpage PDF export or source note  
**8-test use:** Test 3 (baseline), Test 4 (time horizon), Test 5 (external validation)

| Ticker | Company | TPI sector | Priority |
|--------|---------|-----------|---------|
| SKWA | SSAB AB | Steel / Materials | HIGH |
| NOH1 | Norsk Hydro ASA | Aluminium / Materials | HIGH |
| 9TG | Gaztransport Et Technigaz SA | Oil & Gas Equipment | HIGH |
| IHCB | SBM Offshore NV | Oil & Gas | HIGH |
| SOAN | UnipolSai Assicurazioni SpA | Insurance | HIGH |
| 2NN | NN Group NV | Insurance / Financials | HIGH |
| G7W | Games Workshop Group PLC | Consumer Goods | MEDIUM |
| IFX | Infineon Technologies AG | Technology Hardware | MEDIUM |
| ASME | ASML Holding NV | Technology Hardware | MEDIUM |
| BSI | BE Semiconductor Industries NV | Technology Hardware | MEDIUM |
| 2FE | Ferrari NV | Automobiles | MEDIUM |
| MLT | Mycronic AB | Industrials | MEDIUM |
| 1SQ | Swissquote Group Holding SA | Diversified Financials | MEDIUM |
| IGQ5 | 3i Group PLC | Private Equity / Financials | MEDIUM |
| AVS | ASM International NV | Technology Hardware | LOW |
| DP9 | Diploma PLC | Industrials | LOW |
| SGM | STMicroelectronics NV | Technology Hardware | LOW |
| 19V | VAT Group AG | Industrials | LOW |
| CJ2 | Ringkjoebing Landbobank A/S | Banks | LOW |
| 1AE | Argenx SE | Pharmaceuticals | LOW |

**File naming:** `{companyname}_tpi_management_quality_{year}.md` or `{companyname}_tpi_management_quality_{year}.pdf`  
**Note:** If company not in TPI database, create source note with: "Company not listed in TPI database as of [date accessed]."

---

## Batch 4 — Climate Action 100+ Benchmark (Priority: MEDIUM)
**Where:** climateaction100.org → Company Benchmark → search company  
**Note:** CA100+ focuses on the world's largest emitters — smaller companies in the portfolio likely NOT listed. If not listed, a brief note is sufficient.  
**Format:** Dashboard — source note for each  
**8-test use:** Test 5 (external validation), Test 7 (consistency)

Expected coverage (CA100+ focus sectors):
- Likely listed: NOH1 (aluminium/materials), SKWA (steel), possibly IHCB, 9TG
- Unlikely listed: small-cap UK, Danish bank, pharma, consumer goods

| Ticker | Company | Priority |
|--------|---------|---------|
| NOH1 | Norsk Hydro ASA | HIGH |
| SKWA | SSAB AB | HIGH |
| IHCB | SBM Offshore NV | HIGH |
| 9TG | Gaztransport Et Technigaz SA | HIGH |
| SGM | STMicroelectronics NV | MEDIUM |
| IFX | Infineon Technologies AG | MEDIUM |
| ASME | ASML Holding NV | MEDIUM |
| 2FE | Ferrari NV | MEDIUM |
| Remaining 12 | All others | LOW — check but expect not listed |

**File naming:** `{companyname}_ca100_benchmark_note_{year}.md`

---

## Batch 5 — Controversy Check (Priority: HIGH for Tier A companies)
**Where:** Google News, Reuters, FT.com, Bloomberg, RepRisk (if accessible), InfluenceMap  
**Format:** Source note linking to article; do NOT save full paywalled articles  
**8-test use:** Test 7 (consistency — capex vs. claims), Test 8 (materiality)

Search queries to use (copy-paste ready):

```
SKWA:  "SSAB" greenwashing OR controversy OR fine OR emission OR penalty 2023 OR 2024 OR 2025
9TG:   "Gaztransport" OR "GTT" greenwashing OR controversy OR LNG OR emission 2023 OR 2024 OR 2025
IHCB:  "SBM Offshore" greenwashing OR controversy OR oil OR fine OR regulatory 2023 OR 2024 OR 2025
NOH1:  "Norsk Hydro" greenwashing OR controversy OR aluminium OR fine 2023 OR 2024 OR 2025
G7W:   "Games Workshop" greenwashing OR controversy OR sustainability OR emission 2023 OR 2024 OR 2025
BSI:   "BE Semiconductor" OR "Besi" greenwashing OR controversy OR sustainability 2023 OR 2024 OR 2025
IFX:   "Infineon Technologies" greenwashing OR controversy OR fine OR emission 2023 OR 2024 OR 2025
SOAN:  "UnipolSai" OR "Unipol" greenwashing OR controversy OR fine 2023 OR 2024 OR 2025
ASME:  "ASML" greenwashing OR controversy OR sustainability OR fine 2023 OR 2024 OR 2025
2FE:   "Ferrari" greenwashing OR controversy OR emission OR carbon neutral 2023 OR 2024 OR 2025
SGM:   "STMicroelectronics" greenwashing OR controversy OR fine OR carbon 2023 OR 2024 OR 2025
NOH1 (InfluenceMap): "Norsk Hydro" lobbying OR industry association OR fossil fuel
9TG (InfluenceMap):  "GTT" OR "Gaztransport" lobbying OR LNG infrastructure
```

**Note on InfluenceMap:** influencemap.org tracks corporate climate lobbying. Particularly relevant for NOH1 and 9TG given sector.

**File naming:** `{companyname}_controversy_news_note_{year}.md`

| Ticker | Priority | Key concern |
|--------|---------|------------|
| SKWA | HIGH | HYBRIT claim veracity; steel carbon intensity |
| 9TG | HIGH | LNG lock-in argument; transition plan credibility |
| IHCB | HIGH | Scope 3 from client operations; offshore oil association |
| NOH1 | HIGH | Aluminium production emissions vs. renewable claims |
| G7W | HIGH | Net zero 2050 without 2030 milestone — is this credible? |
| SOAN | HIGH | Insurance company underwriting fossil fuels while claiming net zero |
| 2FE | HIGH | "Carbon neutral" claim for luxury cars — methodology? |
| BSI | HIGH | No near-term milestone despite net zero claim |
| IFX | MEDIUM | Science-based 72.5% — validate independence |
| ASME | MEDIUM | Supply chain Scope 3 from semiconductor manufacturing |
| SGM | MEDIUM | "Carbon neutral" claim in sustainability-at-a-glance |
| AVS | LOW | Already has CDP response; lower controversy risk |
| IGQ5 | LOW | PE firm — portfolio-level claims, limited direct exposure |
| Remaining 7 | LOW | Run basic search; document if no results |

---

## Batch 6 — Third-Party GHG Assurance Statement (Priority: HIGH)
**Where:** Company investor relations page → sustainability/ESG section → look for "Assurance statement" or "Independent Assurance Report"  
**Note:** This is often a 1–3 page PDF linked separately from the main sustainability report. Some companies embed it inside the sustainability report — check whether the report already in `company_reports/` contains an assurance statement (search the PDF text for "assurance", "verification", "PwC", "KPMG", "DNV", "Bureau Veritas").  
**8-test use:** Test 5 (external validation)

| Ticker | Company | Notes | Priority |
|--------|---------|-------|---------|
| SKWA | SSAB AB | Assurance mentioned in report | HIGH |
| G7W | Games Workshop Group PLC | Assurance mentioned in report | HIGH |
| BSI | BE Semiconductor Industries NV | Assurance mentioned in report | HIGH |
| MLT | Mycronic AB | Assurance mentioned in report | HIGH |
| SOAN | UnipolSai Assicurazioni SpA | No assurance found in scan | HIGH |
| 9TG | Gaztransport Et Technigaz SA | No assurance found | HIGH |
| IHCB | SBM Offshore NV | Assurance mentioned | HIGH |
| 2NN | NN Group NV | Assurance mentioned | HIGH |
| 2FE | Ferrari NV | Assurance mentioned | HIGH |
| NOH1 | Norsk Hydro ASA | No assurance confirmed in scan | HIGH |
| IFX | Infineon Technologies AG | Assurance mentioned | HIGH |
| AVS | ASM International NV | Assurance mentioned in CDP response | MEDIUM |
| CJ2 | Ringkjoebing Landbobank A/S | No assurance found | MEDIUM |
| 1AE | Argenx SE | Assurance mentioned | MEDIUM |
| DP9 | Diploma PLC | Assurance mentioned in sustainability report | MEDIUM |
| Remaining 5 | 1SQ, ASME, SGM, 19V, IGQ5 | Check IR page | MEDIUM |

**File naming:** `{companyname}_ghg_assurance_statement_{year}.pdf`  
**If embedded in existing report:** Note this in source_collection_tracker.csv under the existing report row, and add note: "Assurance statement embedded in [filename], page [X]."

---

## Batch 7 — Biodiversity / Nature Risk (Priority: MEDIUM for relevant sectors)

These sources apply across multiple companies. One session per source type covers all relevant holdings.

### 7a. ENCORE (sector-level nature dependency / impact)
**Where:** encorenature.org → Impact and Dependency Wheel → select sector  
**Relevant sectors in portfolio:** Technology Hardware (semiconductors), Industrials, Materials (aluminium, steel), Financials, Consumer Discretionary  
**Format:** Download sector page or screenshot → save as source note  
**8-test use:** Test 8 (materiality — is biodiversity material to the sector?)

| Sector | Companies | Priority |
|--------|---------|---------|
| Materials (Steel/Aluminium) | SKWA, NOH1 | HIGH |
| Technology Hardware | ASME, AVS, BSI, IFX, SGM | MEDIUM |
| Energy Equipment (LNG/Offshore) | 9TG, IHCB | HIGH |
| Consumer Discretionary | G7W, 2FE | MEDIUM |
| Industrials | DP9, MLT, 19V | LOW |
| Financials/Insurance | 1SQ, 2NN, CJ2, IGQ5, SOAN | LOW |
| Health Care | 1AE | LOW |

**File naming:** One file per sector, placed in ALL relevant company folders:  
`encore_nature_risk_{sector}_note_2026.md`  
**Note:** This is a SHARED SOURCE — place in each relevant company's `external_evidence/` folder.

### 7b. WRI Aqueduct Water Risk Atlas
**Where:** wri.org/aqueduct → Water Risk Atlas → check company HQ country / key production sites  
**Relevant companies:** NOH1 (Norway), SKWA (Sweden/Finland), IFX (Germany/Malaysia/Kulim), AVS (Netherlands/Asia), BSI (Netherlands)  
**Format:** Source note with water risk score for relevant geography  
**8-test use:** Test 8 (materiality — water risk in operations)

```
Search method: Go to Aqueduct map → identify company's primary manufacturing location(s) → note baseline water stress score
```

**File naming:** `{companyname}_wri_aqueduct_water_risk_note_2026.md`

---

## Batch 8 — EU Taxonomy / Green Revenue Evidence (Priority: MEDIUM)
**Where:** Company reports (already have), or ESMA/regulator filings, or Bloomberg ESG  
**Note:** The `legalEntityEuTaxonomy.csv` course data already contains eligibility estimates. What is missing is *reported alignment* (which is often unavailable) and DNSH compliance evidence.  
**Relevant companies:** Those with non-zero `taxonomy_eligible_pct` in the portfolio data

| Ticker | taxonomy_eligible_pct | Priority |
|--------|----------------------|---------|
| AVS | 0.0% | SKIP |
| BSI | Already has some eligibility | MEDIUM |
| ASME | EU taxonomy mentioned in report | MEDIUM |
| NOH1 | Energy transition — check DNSH | HIGH |
| SKWA | Steel — check DNSH | HIGH |
| SGM | Semiconductor — check DNSH | MEDIUM |
| IFX | Semiconductor — check DNSH | MEDIUM |
| 2NN | Insurance taxonomy alignment | MEDIUM |

**File naming:** `{companyname}_eu_taxonomy_alignment_note_{year}.md`

---

## Shared Source Notes (Multi-Company)

Some sources apply to multiple companies. Create ONE note and place a copy in each relevant company's `external_evidence/` folder.

| Source | Relevant companies | Notes |
|--------|-------------------|-------|
| ENCORE Technology Hardware impact wheel | ASME, AVS, BSI, IFX, SGM | Single note, 5 copies |
| ENCORE Materials/Steel/Aluminium | SKWA, NOH1 | Single note, 2 copies |
| ENCORE Energy Equipment | 9TG, IHCB | Single note, 2 copies |
| WRI Aqueduct regional maps | NOH1, SKWA, IFX, AVS, BSI | One note per geography |

---

## Collection Priority Order

**Do in this order to get maximum evidence with minimum time:**

1. **SBTi batch** (20 lookups, ~30 min) → highest 8-test impact, covers all 20 companies
2. **CDP batch** (19 lookups, ~30 min) → high impact for test 5
3. **Controversy search** (Tier A only: 8 companies, ~60 min) → highest greenwashing risk
4. **GHG assurance** (check existing reports first, then IR pages, ~45 min) → test 5
5. **TPI batch** (20 lookups, ~20 min) → often quick — many companies may not be listed
6. **CA100+ batch** (focused on 4–5 companies, ~15 min) → only material for heavy industry
7. **ENCORE + WRI Aqueduct** (sector-level, ~45 min) → biodiversity/nature test 8
8. **EU Taxonomy** (check existing CSV + company reports first) → test 7 consistency

---

## Companies Most Under-Evidenced

Ranked by urgency (most gaps + highest greenwashing risk):

1. **SKWA (SSAB)** — HYBRIT claim is the boldest in the portfolio; no external validation of any dimension
2. **9TG (GTT)** — LNG sector; energy transition claims with no external validation
3. **SOAN (UnipolSai)** — 3 risk flags; insurance with net zero claim; no external evidence
4. **G7W (Games Workshop)** — highest portfolio weight; net zero 2050 with no 2030 milestone
5. **BSI (BE Semiconductor)** — net zero without near-term milestone; water-intensive operations
6. **IHCB (SBM Offshore)** — offshore oil equipment; scope 3 unverified
7. **NOH1 (Norsk Hydro)** — heavy industrial; renewable + biodiversity claims both need validation
8. **2FE (Ferrari)** — image-heavy PDF means claims not fully extracted; "carbon neutral" claim

---

## File-Ready Naming Examples

Below are ready-to-use filenames for expected sources. Fill in after downloading.

```
ssab_sbti_dashboard_note_2026.md
ssab_tpi_management_quality_2026.pdf
ssab_cdp_climate_score_note_2026.md
ssab_ghg_assurance_statement_2025.pdf
ssab_controversy_news_note_2026.md

gtt_sbti_dashboard_note_2026.md
gtt_tpi_management_quality_2026.pdf
gtt_cdp_climate_score_note_2026.md
gtt_controversy_news_note_2026.md

sbm_offshore_sbti_dashboard_note_2026.md
sbm_offshore_tpi_management_quality_2026.pdf
sbm_offshore_cdp_climate_score_note_2026.md
sbm_offshore_ghg_assurance_statement_2025.pdf
sbm_offshore_controversy_news_note_2026.md

norsk_hydro_sbti_dashboard_note_2026.md
norsk_hydro_tpi_management_quality_2026.pdf
norsk_hydro_ca100_benchmark_note_2026.md
norsk_hydro_wri_aqueduct_water_risk_note_2026.md
norsk_hydro_controversy_news_note_2026.md

games_workshop_sbti_dashboard_note_2026.md
games_workshop_cdp_climate_score_note_2026.md
games_workshop_controversy_news_note_2026.md
games_workshop_ghg_assurance_statement_2025.pdf

be_semiconductor_sbti_dashboard_note_2026.md
be_semiconductor_cdp_climate_score_note_2026.md
be_semiconductor_ghg_assurance_statement_2025.pdf
be_semiconductor_wri_aqueduct_water_risk_note_2026.md

infineon_sbti_dashboard_note_2026.md
infineon_tpi_management_quality_2026.pdf
infineon_cdp_climate_score_note_2026.md
infineon_ghg_assurance_statement_2025.pdf

unipolsai_sbti_dashboard_note_2026.md
unipolsai_tpi_management_quality_2026.pdf
unipolsai_cdp_climate_score_note_2026.md
unipolsai_controversy_news_note_2026.md
```

---

## Source Note Template

When you find a non-PDF source (dashboard, webpage, news article), save it as a `.md` file using this template:

```markdown
# Source Note

Company: [Full company name]
Ticker: [Bloomberg ticker]
Source type: [sbti_dashboard / cdp_score / tpi_assessment / ca100_benchmark / controversy_news / ghg_assurance / encore / wri_aqueduct / eu_taxonomy]
Source title: [Official title of the source or page]
URL: [Full URL — or "MANUAL DOWNLOAD - URL UNKNOWN" if downloaded without URL]
Date accessed: [YYYY-MM-DD]
Publication date: [YYYY-MM-DD or "UNKNOWN"]
Local file path: data/rag/reports/{FOLDER}/external_evidence/{filename}
Relevant 8-test area: [Test 1 / Test 2 / ... / Test 8 — list all that apply]
Relevant finding: [One paragraph — what does this source say? Quote verbatim where possible]
How it supports or challenges company claim: [Does this corroborate or contradict what the company report says?]
Limitations: [E.g., score paywalled — only letter grade visible; or: assessment date older than company report]
Human verification status: NOT VERIFIED
Notes: [Any flags — e.g., "company name spelled differently on SBTi dashboard", "TPI not covering this sector"]
```

---

## Audit Trail Rules

- Every external evidence file must have a matching row in `source_collection_tracker.csv`
- Every source note must include `Date accessed`
- Every source must reference which 8-test dimension(s) it supports
- If a company is not found in SBTi / TPI / CA100+, that itself is a finding — create a source note recording the negative result
- Shared sector sources (ENCORE, WRI Aqueduct) must appear in each relevant company folder AND in `source_collection_tracker.csv` once per company it applies to
- Do not run 8-test conclusions until explicitly asked — this plan is for evidence collection only
