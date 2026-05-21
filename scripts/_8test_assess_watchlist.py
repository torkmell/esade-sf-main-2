#!/usr/bin/env python
"""
8-Test greenwashing assessments — the 8 watchlisted holdings.

Each dimension is rated LOW / MED / HIGH / MISSING per notebooks/09_greenwashing.ipynb.
Quotes are verbatim page-cited extracts from each company's primary sustainability
report (data/rag/corpus/<NN>/_8test/source_text.txt); page numbers are the source
PDF pages. Where the report is silent a dimension is marked MISSING — nothing is
invented. Writes outputs/rag/greenwash_<TICKER>.json (NB09 imports and scores).
"""
import json, os

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(PROJECT)
DATE = "2026-05-21"

def D(quote, page, value, rating, reasoning):
    return {"quote": quote, "page": page, "value": value,
            "rating": rating, "reasoning": reasoning}

ASSESS = [
{
 "ticker": "NHY.OL", "company_name": "Norsk Hydro ASA",
 "analyst_note": "High disclosure quality — quantified near-term targets, explicit 2018 baseline, full scope coverage. Two MED flags: the trajectory is not shown as SBTi-validated, and external assurance of the emissions data is not evidenced in this report.",
 "dimensions": {
   "specificity":  D("Hydro's target is to be a net-zero company by 2050 or [earlier]", 22, "net-zero by 2050", "LOW", "Defined net-zero company commitment with a stated year, backed by near-term 2025/2030 targets."),
   "metric":       D("10 percent reduction by 2025 and 30 percent by 2030 against 2018 baseline", 21, "30% by 2030", "LOW", "Quantified absolute reduction targets with explicit percentages."),
   "baseline":     D("Reduction in greenhouse gas emissions against 2018 baseline", 3, "2018", "LOW", "Explicit baseline year, used consistently across targets."),
   "target":       D("Hydro's target is to be a net-zero company by 2050 or [earlier]", 22, "company-stated, not SBTi-validated", "MED", "Targets are quantified and tracked, but the report shows no SBTi validation of the decarbonisation trajectory."),
   "time_horizon": D("30 percent by 2030 against 2018 baseline", 21, "2030 near-term + 2050", "LOW", "Near-term 2025/2030 milestones present alongside the 2050 endpoint."),
   "scope":        D("Comprises material upstream Scope 3 categories", 21, "S1+2+3", "LOW", "Scope 1, 2 and material upstream Scope 3 covered, with Scope 3 targets."),
   "verification": D("Independent auditors report", 8, "financial audit; sustainability assurance not evidenced", "MED", "An independent auditor's report covers the financial statements; the extract does not clearly evidence external assurance of the emissions data."),
   "consistency":  D("Hydro's capital allocation is based on strategic priorities", 24, "no contradiction found", "LOW", "Capital-allocation framework disclosed; no capex or lobbying contradiction with stated climate commitments surfaced."),
 }},
{
 "ticker": "A5G.IR", "company_name": "AIB Group plc",
 "analyst_note": "Source is AIB's 38-page Climate Transition Plan — strong on specificity, metrics, baselines and SBTi validation. Verification rated MED only because this standalone document is not the externally assured report.",
 "dimensions": {
   "specificity":  D("Commitment to decarbonise our own operations by 2030 and our customer [lending portfolio by 2050]", 6, "operations 2030 / portfolio 2050", "LOW", "Specific dual commitment for operations and the lending book."),
   "metric":       D("Set SBTi-approved financed emissions targets for 75% of our loan book", 6, "75% of loan book; 51% by 2030", "LOW", "Quantified financed-emissions and green-lending targets."),
   "baseline":     D("by 2030 from a 2019 baseline", 7, "2019 ops / 2021 sectors", "LOW", "Explicit baseline years — 2019 for operations, 2021 for material sector portfolios."),
   "target":       D("we have a number of validated targets in place for our key sectors through the SBTi", 10, "SBTi-validated", "LOW", "SBTi-validated sector targets, referenced to a 1.5C pathway."),
   "time_horizon": D("decarbonise our own operations by 2030", 6, "2030 near-term + 2050", "LOW", "Near-term 2030 targets present alongside the 2050 portfolio goal."),
   "scope":        D("(GHG Scope 3 financed emissions)", 20, "S1+2+3 financed", "LOW", "Scope 1, 2 and Scope 3 financed emissions covered — the material scope for a bank."),
   "verification": D(None, None, "no assurance statement in this document", "MED", "This is a standalone Climate Transition Plan and carries no external assurance statement; assurance, if any, sits in AIB's separate annual financial report."),
   "consistency":  D("This Climate Transition Plan looks to bring [transition planning together]", 2, "transition plan; green-lending progress reported", "LOW", "Dedicated transition plan with reported progress (35% of new lending green/transition); no contradiction surfaced."),
 }},
{
 "ticker": "LI.PA", "company_name": "Klepierre SA",
 "analyst_note": "Universal Registration Document. SBTi-validated 2030 net-zero trajectory across Scopes 1-3 with reported progress; only verification rated MED (climate-data assurance not clearly evidenced in the extract).",
 "dimensions": {
   "specificity":  D("the Group's 2030 net-zero commitment (scopes 1 and 2)", 55, "net-zero by 2030 (S1+2)", "LOW", "Specific, near-dated net-zero commitment via the Act4Good strategy."),
   "metric":       D("helped reduce scopes 1 and 2 carbon emissions intensity by 9%", 29, "SBTi trajectory; 9% achieved", "LOW", "SBTi-validated decarbonisation trajectory with reported quantified progress."),
   "baseline":     D("of scopes 1 & 2 between 2017 and 2025", 20, "2017", "LOW", "2017 baseline underpins the SBTi-validated trajectory."),
   "target":       D("SBTi-validated decarbonization trajectory for Scopes 1, 2 & 3 by 2030", 25, "SBTi-validated, 1.5C", "LOW", "SBTi-validated trajectory; the report states Klepierre exceeds its SBTi-approved target."),
   "time_horizon": D("net-zero by 2030", 6, "2030", "LOW", "Net-zero endpoint set at 2030 — near-dated and verifiable rather than long-deferred."),
   "scope":        D("SBTi-validated decarbonization trajectory for Scopes 1, 2 & 3 by 2030", 25, "S1+2+3", "LOW", "Scopes 1, 2 and 3 covered by the validated trajectory."),
   "verification": D(None, None, "operational audits shown; climate-data assurance not evidenced", "MED", "The extract evidences operational third-party audits but not a clear external assurance statement on the climate/emissions disclosures."),
   "consistency":  D("Klepierre maintains a disciplined, accretive approach to capital allocation", 31, "no contradiction found", "LOW", "Capital allocation and EPRA capex disclosed; no contradiction with the net-zero strategy surfaced."),
 }},
{
 "ticker": "MRL.MC", "company_name": "MERLIN Properties SOCIMI, S.A.",
 "analyst_note": "EINF non-financial statement. Strong across all eight dimensions — documented Pathway to Net Zero, SBTi-validated targets, 2018 baseline, independent review report, disclosed green capex.",
 "dimensions": {
   "specificity":  D("MERLIN launched its 'Pathway to Net Zero' strategy, a roadmap", 5, "Pathway to Net Zero; net-zero 2030", "LOW", "Named, documented net-zero strategy with reported implementation progress."),
   "metric":       D("Reduction of operational carbon: 85% reduction in operational carbon from baseline (2018)", 5, "85% reduction", "LOW", "Quantified operational-carbon reduction target with reported progress."),
   "baseline":     D("85% from the base year (2018) to 2028, for Scopes 1 and 2", 31, "2018", "LOW", "Explicit 2018 base year."),
   "target":       D("net zero carbon company by 2030, in line with the science-based targets (SBTi)", 30, "SBTi-validated, 1.5C", "LOW", "SBTi-validated targets (validated Feb 2023 per the SBTi registry), 1.5C-aligned."),
   "time_horizon": D("net zero carbon company by 2030", 30, "2028 / 2030", "LOW", "Near-term 2028/2030 targets — no long-deferral."),
   "scope":        D("Scope 3 greenhouse gas (GHG) emissions", 92, "S1+2+3", "LOW", "Scopes 1, 2 and 3 reported, with a Scope 3 tenant-engagement target."),
   "verification": D("transparency, which is backed by independent third-party validation", 6, "independent review report", "LOW", "An independent review report is provided; externally audited information is referenced."),
   "consistency":  D("The CapEx associated with the Decarbonisation Plan for these measures in 2025 was EUR 10.3 [million]", 32, "green capex disclosed", "LOW", "Green capex tied explicitly to the Decarbonisation Plan; consistent with stated commitments."),
 }},
{
 "ticker": "GALE.SW", "company_name": "Galenica AG",
 "analyst_note": "Galenica is mid-transition: a net-zero-2050 commitment and a documented transition plan, but SBTi targets are committed-not-yet-validated. Four MED flags (metric, target, time horizon, verification); no HIGH flags — consistent with the IC 'MONITOR' disposition.",
 "dimensions": {
   "specificity":  D("aim to achieve net zero emissions by 2050", 65, "net zero by 2050", "LOW", "Clear net-zero commitment supported by a documented transition plan."),
   "metric":       D("Galenica commits to reducing absolute Scope 1+2 greenhouse gas [emissions]", 87, "commitment stated; validated % pending", "MED", "An absolute Scope 1+2 reduction commitment is stated, but no validated headline percentage is surfaced — consistent with SBTi commitment-not-yet-validated status."),
   "baseline":     D("65% by 2035 compared to 2023 base year", 75, "2023", "LOW", "Explicit 2023 base year referenced for reduction targets."),
   "target":       D("pathways in line with the Science Based Targets (SBTi)", 65, "SBTi committed, not yet validated", "MED", "An SBTi commitment is registered but validated targets are pending (SBTi 'Committed' status) — weaker than a validated target."),
   "time_horizon": D("aim to achieve net zero emissions by 2050", 65, "2050 endpoint; near-term unclear", "MED", "The headline horizon is the long-dated 2050 net-zero; a near-term (<=2030) climate milestone is not clearly evidenced in the report."),
   "scope":        D("Other GHG emissions (Scope 3) tCO2e 396,400", 12, "S1+2+3", "LOW", "Scope 1+2 reported and a full Scope 3 screen completed and reported."),
   "verification": D("2025 Data externally assured (limited assurance)", 95, "limited assurance", "MED", "Externally assured, but only to a limited assurance level."),
   "consistency":  D("The transition plan - and thus the consistent management of our energy", 91, "transition plan present", "LOW", "Documented transition plan; no capex or lobbying contradiction surfaced."),
 }},
{
 "ticker": "ITX.MC", "company_name": "Industria de Diseno Textil, S.A.",
 "analyst_note": "Strong, detailed climate disclosure — SBTi-approved targets to 2030 and a SBTi-approved 2040 net-zero target, explicit 2018 baseline, full scope coverage, EY external verification. One MED (limited assurance level).",
 "dimensions": {
   "specificity":  D("Achieve net-zero emissions, reducing at least 90% of our carbon [emissions]", 26, "net zero by 2040, 90% reduction", "LOW", "Specific net-zero target with a defined reduction percentage."),
   "metric":       D("Reduce scope 1 and 2 GHG emissions by 95% by 2040", 41, "95% S1+2; 90% S3 by 2040", "LOW", "Detailed quantified targets across scopes and interim years."),
   "baseline":     D("emissions by 20% by 2027, as compared to 2018", 41, "2018", "LOW", "Explicit 2018 baseline."),
   "target":       D("Our 2030 emissions reduction targets are approved by the Science Based Targets initiative (SBTi)", 41, "SBTi-approved incl. net-zero", "LOW", "SBTi-approved 2030 targets and a SBTi-approved 2040 net-zero target."),
   "time_horizon": D("GHG emission reduction targets through 2027, 2030 and 2040", 40, "2027 / 2030 / 2040", "LOW", "Multiple near-term milestones (2027, 2030) — not 2050-only."),
   "scope":        D("E1.I1 Scope 1, 2 and 3 greenhouse gas (GHG) emissions", 31, "S1+2+3", "LOW", "Scopes 1, 2 and 3 covered with scope-specific targets."),
   "verification": D("verified by an independent third-party, Ernst & Young", 16, "EY limited assurance", "MED", "Externally verified by EY, but to a limited assurance level."),
   "consistency":  D("We have a Climate Transition Plan, which evidences Inditex's [commitment]", 38, "transition plan; no documented contradiction", "LOW", "Documented Climate Transition Plan; no capex or lobbying contradiction evidenced in the report (fast-fashion volume-growth tension is a sector watch-point, not a documented contradiction)."),
 }},
{
 "ticker": "ORNBV.HE", "company_name": "Orion Oyj Class B",
 "analyst_note": "Source is the CSRD sustainability statement within Orion's financial-statement documents. SBTi-approved 70%-by-2030 target, explicit 2023 baseline, full scope coverage, limited assurance. One MED (assurance level).",
 "dimensions": {
   "specificity":  D("Orion has committed to reach net-zero emissions by 2050", 63, "net-zero by 2050", "LOW", "Defined net-zero commitment; the report candidly acknowledges the challenges of achieving it."),
   "metric":       D("target to reduce its absolute Scope 1 and 2 emissions by 70% by 2030 from a 2023 baseline", 62, "70% by 2030", "LOW", "Quantified absolute reduction target."),
   "baseline":     D("by 70% by 2030 from a 2023 baseline", 62, "2023", "LOW", "Explicit 2023 base year."),
   "target":       D("target has been approved by the Science Based Targets initiative (SBTi)", 62, "SBTi-approved, 1.5C", "LOW", "SBTi-approved near-term targets, 1.5C-aligned."),
   "time_horizon": D("absolute Scope 1 and 2 emissions by 70% by 2030", 62, "2030 near-term + 2050", "LOW", "Near-term 2030 target plus the 2050 endpoint."),
   "scope":        D("E1-6 Gross Scopes 1, 2, 3 and Total GHG emissions", 50, "S1+2+3", "LOW", "Scopes 1, 2 and 3 reported; a Scope 3 supplier-engagement goal is set."),
   "verification": D("The sustainability statement is subject to limited assurance by a sustainability reporting assurance provider", 25, "limited assurance", "MED", "Externally assured, but to a limited assurance level."),
   "consistency":  D("Orion does not disclose additional details of its climate transition plan, including division specific [plans], beyond what is reported under E1-1", 24, "transition plan reported; granularity limited (disclosed)", "LOW", "Transition plan reported under ESRS E1-1 and capex disclosed; the report candidly notes limited transition-plan granularity — a disclosed limitation rather than a contradiction."),
 }},
{
 "ticker": "SOBI.ST", "company_name": "Swedish Orphan Biovitrum AB",
 "analyst_note": "The 8-Test of Sobi's sustainability claims is clean — SBTi-validated targets, explicit 2023 baseline, near-term 2029 target, full scope coverage. NOTE: the IC PENDING_RAG flag concerns the Truvalue Laggard NEWS signal (a controversy screen), which is separate from the claim-quality assessed here; this 8-Test does not flag Sobi.",
 "dimensions": {
   "specificity":  D("Net zero 2050 (long-term)", 54, "net zero by 2050", "LOW", "Net-zero commitment stated, backed by near-term targets."),
   "metric":       D("40 per cent by 2029 versus 2023", 9, "40% by 2029", "LOW", "Quantified near-term reduction target."),
   "baseline":     D("compared with the 2023 base year", 28, "2023", "LOW", "Explicit 2023 base year."),
   "target":       D("The SBTi validated Sobi's climate targets.", 25, "SBTi-validated", "LOW", "Climate targets validated by the Science Based Targets initiative."),
   "time_horizon": D("40 per cent by 2029 versus 2023", 9, "2029 near-term + 2050", "LOW", "Near-term 2029 target present alongside the 2050 net-zero endpoint."),
   "scope":        D("Sobi's value chain emissions (scope 3) represent [a material share]", 28, "S1+2+3", "LOW", "Scope 1, 2 and value-chain Scope 3 covered, with a supplier-engagement target."),
   "verification": D("Auditor's limited assurance report", 3, "limited assurance", "MED", "Externally assured, but to a limited assurance level."),
   "consistency":  D("The transition plan is integrated into the financial [statements]", 56, "transition plan integrated", "LOW", "Transition plan integrated with the financials; EU Taxonomy capex disclosed; no contradiction surfaced."),
 }},
]

os.makedirs("outputs/rag", exist_ok=True)
for a in ASSESS:
    rec = {"ticker": a["ticker"], "company_name": a["company_name"],
           "extraction_date": DATE, "analyst_note": a["analyst_note"],
           "dimensions": a["dimensions"]}
    path = f"outputs/rag/greenwash_{a['ticker']}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rec, f, indent=2, ensure_ascii=True)
    highs = sum(1 for d in a["dimensions"].values() if d["rating"] == "HIGH")
    meds  = sum(1 for d in a["dimensions"].values() if d["rating"] == "MED")
    print(f"  {a['ticker']:<10} {a['company_name'][:34]:<35} HIGH={highs} MED={meds}  -> {path}")

print(f"\n{len(ASSESS)} greenwashing assessments written to outputs/rag/")
print("Run NB09 to score them (HIGH>=3 -> exclude, HIGH==2 -> watchlist).")
