#!/usr/bin/env python
"""
8-Test greenwashing assessments — the remaining 12 holdings.

Same method as _8test_assess_watchlist.py: each dimension rated LOW/MED/HIGH/
MISSING per notebooks/09_greenwashing.ipynb, grounded in verbatim page-cited
quotes from each company's primary sustainability report (data/rag/corpus/).
Writes outputs/rag/greenwash_<TICKER>.json (NB09 imports and scores).
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
 "ticker": "ALFA.ST", "company_name": "Alfa Laval AB",
 "analyst_note": "Strong climate disclosure — near-dated net-zero (Scope 1+2 by 2027), explicit 2020 baseline, SBTi-approved targets, full scope coverage. One MED: emissions-data assurance level not crisply evidenced in the extract.",
 "dimensions": {
   "specificity":  D("The ambition is to achieve net zero scope 1 and 2 GHG emissions by 2027", 18, "net zero S1+2 by 2027", "LOW", "Specific, near-dated net-zero ambition with defined scope coverage."),
   "metric":       D("Reduction scope 1 & 2 (base year 2020) 95%", 18, "95% S1+2; 50% S3", "LOW", "Quantified reduction percentages for Scope 1+2 and Scope 3."),
   "baseline":     D("Reduction scope 1 & 2 (base year 2020)", 18, "2020", "LOW", "Explicit 2020 base year, used consistently."),
   "target":       D("approved by SBTi as compatible with limiting global warming", 33, "SBTi-approved, 1.5C", "LOW", "Targets approved by the SBTi as 1.5C-compatible."),
   "time_horizon": D("net zero scope 1 and 2 GHG emissions by 2027 ... value chain by 2050", 18, "2027 + 2050", "LOW", "Near-dated 2027 operations target alongside the 2050 value-chain endpoint."),
   "scope":        D("upstream and downstream scope 3 GHG emissions", 27, "S1+2+3", "LOW", "Scope 1, 2 and upstream/downstream Scope 3 covered."),
   "verification": D("validated by an external body other than company auditors", 27, "external validation referenced", "MED", "External validation is referenced and a transition plan was prepared, but the assurance level of the emissions data is not crisply evidenced in the extract."),
   "consistency":  D("During 2025, Alfa Laval prepared a transition plan for climate", 30, "transition plan; lobbying disclosed", "LOW", "Documented transition plan; political-lobbying activity disclosed; no contradiction surfaced."),
 }},
{
 "ticker": "AGN.AS", "company_name": "Aegon Ltd.",
 "analyst_note": "Asset-owner climate disclosure (NZAOA member). Quantified 2030 targets on a 2019 baseline; two MED flags — the targets are NZAOA/Paris-aligned rather than shown as SBTi-validated, and the climate transition plan disclosure is still being developed.",
 "dimensions": {
   "specificity":  D("the carbon footprint by 30% by 2030 and achieving net-zero", 33, "net-zero by 2050", "LOW", "Specific carbon-footprint and net-zero ambitions as an NZAOA signatory."),
   "metric":       D("activities by 75% by 2030 compared to a 2019 baseline", 23, "50% / 75% by 2030", "LOW", "Quantified portfolio-decarbonisation targets."),
   "baseline":     D("assets by 50% against a 2019 baseline", 23, "2019", "LOW", "Explicit 2019 base year."),
   "target":       D("science-based targets aligned with the Paris Agreement", 310, "Paris/NZAOA-aligned; SBTi not confirmed", "MED", "Targets are science-based- and NZAOA-aligned, but the extract does not confirm formal SBTi validation."),
   "time_horizon": D("ambitions for 2030 ... net-zero greenhouse gas emissions by 2050", 23, "2030 + 2050", "LOW", "Near-term 2030 targets present alongside the 2050 endpoint."),
   "scope":        D("of its carbon footprint relates to scope 3 greenhouse gas [emissions]", 32, "S1+2+3", "LOW", "Operational Scope 1+2 and investment-footprint Scope 3 covered."),
   "verification": D("The report of the independent auditor is issued with the ESEF reporting package", 3, "externally assured", "MED", "An assurance provider is referenced but the assurance level of the sustainability data is not crisply evidenced."),
   "consistency":  D("[Aegon does not yet have] a climate transition plan but is taking steps to disclose one", 309, "transition plan in development; no contradiction", "LOW", "Capital-allocation discussed and no contradiction surfaced; the report candidly notes its full climate transition plan disclosure is still being developed."),
 }},
{
 "ticker": "LLOY.L", "company_name": "Lloyds Banking Group plc",
 "analyst_note": "Detailed bank climate disclosure — absolute and financed-emissions targets on explicit 2018/2019 baselines, SBTi-/IPCC-benchmarked to 1.5C, ISAE 3000 limited assurance. One MED (limited assurance level).",
 "dimensions": {
   "specificity":  D("a real-economy transition to net zero", 21, "net-zero transition", "LOW", "Net-zero ambition framed for the bank's own operations and its lending book."),
   "metric":       D("Absolute emissions from a 2018/2019 baseline include scope 1, 2 and 3", 63, "absolute + financed-emissions targets", "LOW", "Quantified absolute and financed-emissions targets across scopes."),
   "baseline":     D("Baseline year determined by ambition (2018 for Bank, 2019 for Scottish Widows)", 65, "2018 / 2019", "LOW", "Explicit baseline years, documented per business."),
   "target":       D("pathway as defined by SBTi and IPCC ... benchmarking against SBTi criteria", 68, "SBTi/IPCC 1.5C-benchmarked", "LOW", "Sectoral targets benchmarked to SBTi and IPCC 1.5C pathways — binding sectoral commitments."),
   "time_horizon": D("By 2030 ... scopes by 2045", 21, "2030 + 2045", "LOW", "Near-term 2030 milestones present."),
   "scope":        D("key performance indicators (KPIs) relating to scopes 1-3", 22, "S1+2+3 financed", "LOW", "Scopes 1, 2 and Scope 3 financed emissions covered."),
   "verification": D("independent limited assurance over certain ... Assurance Engagements 3000 (Revised)", 3, "ISAE 3000 limited assurance", "MED", "Externally assured to ISAE 3000, but a limited assurance level."),
   "consistency":  D("transition plan sets out how we are positioning", 61, "transition plan present", "LOW", "Documented transition plan and a Client Transition Plan process; no contradiction surfaced."),
 }},
{
 "ticker": "SBMO.AS", "company_name": "SBM Offshore NV",
 "analyst_note": "Offshore-energy contractor. Disclosure is structured (2016 base year, intermediary 2030 targets, ISAE limited assurance) but four MED flags reflect an offset-reliant near-term 'climate neutral' claim, SBTi-guideline-based (not validated) targets, and a fossil-linked capex profile that the company discloses transparently.",
 "dimensions": {
   "specificity":  D("Including the use of certified climate projects to compensate any residual scope 1 and 2 emissions", 12, "climate neutral 2025 via offsets", "MED", "The near-term 'Climate Neutral by 2025' claim relies on offset/compensation credits — disclosed transparently, but a weaker claim form than gross reduction."),
   "metric":       D("Source 100% renewable energy by 2030", 11, "100% renewables 2030; net zero 2050", "LOW", "Quantified renewable-energy and climate-neutrality targets."),
   "baseline":     D("The 2016 base year considers the emissions performance of 202 kg CO2e/tonnes of HC", 12, "2016", "LOW", "Explicit 2016 base year."),
   "target":       D("targets based on guidelines of the Science Based Targets [initiative]", 101, "SBTi-guideline-based, not validated", "MED", "Targets are built on SBTi guidelines but the extract does not confirm formal SBTi validation."),
   "time_horizon": D("net zero by 2050, with intermediary targets for 2030", 21, "2025 / 2030 / 2050", "LOW", "Near-term 2025/2030 milestones present alongside the 2050 endpoint."),
   "scope":        D("Climate Neutral by 2025 for Scope 1 and [2] ... intensity for Scope 3 - Downstream", 11, "S1+2+3", "LOW", "Scope 1, 2 and a Scope 3 downstream intensity measure covered."),
   "verification": D("Limited Assurance Report of the Independent [auditor]", 3, "limited assurance", "MED", "Externally assured, but a limited assurance level."),
   "consistency":  D("The CAPEX related to oil-related activities in 2025 is [disclosed]", 104, "fossil-linked capex disclosed", "MED", "Oil-related capex is disclosed alongside new-energy capital allocation; the capex profile remains fossil-linked — a genuine consistency watch-point, disclosed transparently."),
 }},
{
 "ticker": "ZURN.SW", "company_name": "Zurich Insurance Group Ltd",
 "analyst_note": "Insurer climate disclosure — net-zero-business ambition with a launched transition plan, quantified targets on explicit 2019/2022 baselines, PCAF-based insurance-associated emissions, independent assurance report. One MED (assurance level).",
 "dimensions": {
   "specificity":  D("our climate transition plan towards our ambition to become a net-zero business by [2050]", 6, "net-zero business by 2050", "LOW", "Net-zero-business ambition anchored to a launched climate transition plan."),
   "metric":       D("60 percent reduction by 2025", 3, "60% by 2025", "LOW", "Quantified reduction targets against stated baselines."),
   "baseline":     D("Compared with our 2019 baseline", 3, "2019 / 2022", "LOW", "Explicit 2019 (and 2022) baseline years."),
   "target":       D("credible science-based targets", 4, "science-based targets", "LOW", "Quantified, baseline-anchored science-based targets across operations and portfolio."),
   "time_horizon": D("60 percent reduction by 2025 ... By 2030, we will engage", 3, "2025 / 2030 + 2050", "LOW", "Near-term 2025/2030 targets present."),
   "scope":        D("scope 1 and 2 for our customers' emissions using the ... PCAF ... methodology", 4, "S1+2 + PCAF insurance-associated", "LOW", "Operational Scope 1+2 and PCAF insurance-associated emissions covered."),
   "verification": D("Independent assurance report", 219, "external assurance", "MED", "An independent assurance report is provided; the assurance level is not crisply stated in the extract."),
   "consistency":  D("progress in implementing our climate transition plan", 6, "transition plan; trade-association activity disclosed", "LOW", "Climate transition plan in implementation; trade-association participation disclosed; no contradiction surfaced."),
 }},
{
 "ticker": "ABBN.SW", "company_name": "ABB Ltd.",
 "analyst_note": "CSRD/ESRS Sustainability Statement. Strong throughout — SBTi-validated Net-Zero-Standard targets, explicit 2019/2022 baselines, KPMG limited assurance, disclosed climate capex. One MED (limited assurance level).",
 "dimensions": {
   "specificity":  D("reaching net zero by 2050 ... aligned with the Corporate Net-Zero Standard of the Science Based [Targets initiative]", 53, "net zero by 2050, SBTi Net-Zero Standard", "LOW", "Specific net-zero commitment aligned to the SBTi Corporate Net-Zero Standard."),
   "metric":       D("emissions by at least 80% by [2030] ... by 25% by 2030 and by 90% by [2050]", 50, "80% S1+2 by 2030", "LOW", "Quantified near- and long-term reduction percentages."),
   "baseline":     D("79 percent in our scope 1 and 2 GHG emissions compared to 2019", 6, "2019 (S1+2) / 2022 (S3)", "LOW", "Explicit base years — 2019 for Scope 1+2, 2022 for Scope 3."),
   "target":       D("Our emissions reduction targets have been validated by the Science Based Targets initiative (SBTi)", 6, "SBTi-validated, Net-Zero Standard", "LOW", "Targets validated by the SBTi and confirmed against its Net-Zero Standard."),
   "time_horizon": D("near-term (2030) and long-term (2050) targets", 42, "2030 + 2050", "LOW", "Near-term 2030 targets present alongside the 2050 endpoint."),
   "scope":        D("emissions from our own operations (scope 1 and 2) as well as indirect emissions from our value chain (scope 3)", 6, "S1+2+3", "LOW", "Scopes 1, 2 and 3 covered."),
   "verification": D("limited assurance regarding the statutory sustainability statement", 15, "KPMG limited assurance", "MED", "Externally assured by KPMG, but a limited assurance level."),
   "consistency":  D("In 2025, we allocated $11.8 million in capital expenditure (CapEx) to climate [action]", 57, "climate capex disclosed", "LOW", "Climate capex disclosed and a Climate Transition Plan documented; consistent with stated commitments."),
 }},
{
 "ticker": "SPSN.SW", "company_name": "Swiss Prime Site AG",
 "analyst_note": "SOURCE LIMITATION: assessed from Swiss Prime's 16-page ESG summary booklet; the company's full disclosures are split across separate E/S/G reports. 'baseline' and 'consistency' are marked MISSING because they are absent from this summary booklet, not necessarily from the company's full reporting — recommend re-assessing against Report_2025_en.pdf.",
 "dimensions": {
   "specificity":  D("net-zero operations in our property portfolio by 2040", 3, "net-zero operations by 2040", "LOW", "Specific net-zero-operations commitment for the property portfolio."),
   "metric":       D("a clear focus on decarbonisation, the circular [economy]", 7, "net-zero-2040 goal; interim % not in booklet", "MED", "A net-zero-2040 goal and a decarbonisation pathway are stated, but no quantified interim emissions-reduction percentage appears in this summary booklet."),
   "baseline":     D(None, None, "no baseline stated in this document", "MISSING", "No emissions baseline year appears in the 16-page ESG booklet used as source; likely disclosed in the company's full sustainability report."),
   "target":       D("On the one hand, we are aiming for net-zero operations in our property portfolio by 2040", 3, "net-zero 2040 target; no SBTi validation shown", "MED", "A net-zero-2040 target is stated, but the booklet shows no external/SBTi validation."),
   "time_horizon": D("Net zero in the property portfolio by 2040", 6, "2040 + 2030 milestone", "LOW", "2040 net-zero endpoint (not 2050+) with a 2030 circular-construction milestone."),
   "scope":        D("Scope 1: Owner-controlled energy supply ... Scope 2 ... Scope 3: Indirect emissions", 8, "S1+2+3", "LOW", "All three scopes explicitly defined."),
   "verification": D("independent audits, we also ensure that our investments", 10, "no assurance statement in this booklet", "MED", "The summary booklet presents no external assurance statement on the sustainability data; assurance, if any, sits in the full report."),
   "consistency":  D(None, None, "no capex/transition-plan content in this document", "MISSING", "The 16-page ESG booklet contains no capex or transition-plan detail to assess; likely in the company's full sustainability report."),
 }},
{
 "ticker": "UCB.BR", "company_name": "UCB S.A.",
 "analyst_note": "Pharma integrated annual report. Strong climate disclosure — SBTi-Net-Zero-standard-aligned targets, 90% absolute reduction vs an explicit 2019 base year, transition plan fully embedded in capital allocation, externally assured. One MED (assurance level).",
 "dimensions": {
   "specificity":  D("UCB is committed to net zero ... SBTi Net-Zero standard", 28, "net zero, SBTi Net-Zero standard", "LOW", "Specific net-zero commitment aligned to the SBTi Net-Zero standard."),
   "metric":       D("Absolute CO2e reduction by 90% vs 2019 base year", 56, "90% absolute reduction", "LOW", "Quantified absolute reduction targets."),
   "baseline":     D("by 73% vs 2019 base year", 56, "2019", "LOW", "Explicit 2019 base year, used consistently."),
   "target":       D("with CO2e target aligned with SBTi", 17, "SBTi-aligned", "LOW", "Emissions targets aligned with the SBTi; transition plan validated by the Executive Committee."),
   "time_horizon": D("across the 2030, 2040 and 2050 horizons ... emissions by 2045", 55, "2030 + 2045", "LOW", "Near-term 2030 milestones present alongside a ~2045 net-zero horizon."),
   "scope":        D("Absolute reduction in Scope 1, 2 and 3 (except scope 3 category 1)", 33, "S1+2+3", "LOW", "Scopes 1, 2 and 3 covered (Scope 3 category 1 exclusion disclosed)."),
   "verification": D("Statement and Financials section, are assured by Forvis Mazars", 3, "externally assured (Forvis Mazars)", "MED", "Externally assured by Forvis Mazars; the assurance level is not crisply stated in the extract."),
   "consistency":  D("UCB's ten-year climate transition plan is fully embedded ... capital allocation", 55, "transition plan embedded in capital allocation", "LOW", "Transition plan fully embedded in capital allocation; capex assessed under climate scenarios; consistent."),
 }},
{
 "ticker": "AZN.L", "company_name": "AstraZeneca PLC",
 "analyst_note": "Pharma annual report. Strong climate disclosure — SBTi-verified Net-Zero-Standard targets, 98% near-term absolute target on a 2015 baseline, independent sustainability assurance. One MED (assurance level). NOTE: a 2025 China legal matter appears in the external controversy screen — that is a governance/legal item, separate from the sustainability-claim quality assessed by the 8-Test.",
 "dimensions": {
   "specificity":  D("the aim of achieving science-based net zero ... to achieve net zero by 2045", 9, "science-based net zero by 2045", "LOW", "Specific, science-based net-zero commitment with a defined year."),
   "metric":       D("We have a near-term target of 98% absolute [reduction]", 44, "98% near-term absolute", "LOW", "Quantified absolute reduction target with reported progress (89% achieved Scope 1+2)."),
   "baseline":     D("2015 baseline), part of our Ambition Zero", 13, "2015", "LOW", "Explicit 2015 base year."),
   "target":       D("our SBTi-verified Net-Zero Corporate Standard targets in line with SBTi timelines", 44, "SBTi-verified, Net-Zero Standard", "LOW", "Targets verified by the SBTi against its Net-Zero Corporate Standard, 1.5C-aligned."),
   "time_horizon": D("to achieve net zero by 2045", 9, "2030 milestones + 2045", "LOW", "Near-term 2030 ambitions present alongside a 2045 net-zero endpoint."),
   "scope":        D("focused on cutting Scope 3 emissions with [suppliers]", 7, "S1+2+3", "LOW", "Scopes 1, 2 and 3 covered, with a Scope 3 supplier focus."),
   "verification": D("Independent Sustainability Assurance Report", 220, "external sustainability assurance", "MED", "An independent sustainability assurance report is provided; the assurance level is not crisply stated in the extract."),
   "consistency":  D("Transition plan for climate change", 44, "transition plan; capex disclosed", "LOW", "Documented climate transition plan; capital-allocation and capex priorities disclosed; no contradiction surfaced."),
 }},
{
 "ticker": "EOAN.DE", "company_name": "E.ON SE",
 "analyst_note": "Utility/grid annual report. Strong climate disclosure — SBTi-validated near-term 2030 targets, climate neutrality by 2040 on a 2019 baseline, full scope coverage, lobbying disclosed. One MED (assurance level). (E.ON's high carbon intensity reflects its sector; the 8-Test assesses claim quality, which is robust.)",
 "dimensions": {
   "specificity":  D("reduce our own carbon emissions and aim to achieve climate neutrality by 2040", 6, "climate neutrality by 2040", "LOW", "Specific climate-neutrality commitment with a defined year and a 'Path to Climate Neutrality'."),
   "metric":       D("Scope 1 + 2 total (location-based) 5.21 5.64 -8%", 142, "quantified emissions + 2030 targets", "LOW", "Emissions quantified and reported year-on-year against 2030 targets."),
   "baseline":     D("Scope 1, 2, and 3 emissions relative to a 2019 baseline", 92, "2019", "LOW", "Explicit 2019 base year covering all scopes."),
   "target":       D("In 2022 the Science Based Target initiative ('SBTi') validated that E.ON's current near-term 2030 climate targets are consistent with the Paris Agreement's 1.5C target", 97, "SBTi-validated 2030 targets", "LOW", "Near-term 2030 targets validated by the SBTi as 1.5C-consistent."),
   "time_horizon": D("aim to achieve climate neutrality by 2040", 6, "2030 + 2040", "LOW", "SBTi-validated near-term 2030 targets present alongside the 2040 endpoint."),
   "scope":        D("covers Scope 1, 2, and 3", 92, "S1+2+3", "LOW", "Group-wide climate targets cover Scopes 1, 2 and 3 by business unit."),
   "verification": D("Assurance Report in Relation to the [sustainability disclosures]", 2, "external assurance", "MED", "An assurance report on the sustainability disclosures is provided; the assurance level is not crisply stated in the extract."),
   "consistency":  D("public lobbying. The information is shared in-house", 90, "transition plan; lobbying disclosed", "LOW", "Documented transition plan; trade-association and lobbying activity disclosed; network-focused capex aligns with the transition."),
 }},
{
 "ticker": "TEL2-B.ST", "company_name": "Tele2 AB Class B",
 "analyst_note": "Telecom annual & sustainability report. Strong climate disclosure — science-based targets 1.5C-aligned, near-dated net-zero (2035) with 2027/2029 milestones, 2019 baseline, KPMG limited assurance. One MED (limited assurance level).",
 "dimensions": {
   "specificity":  D("aiming for net zero greenhouse gas [emissions] ... targeting net-zero by 2035", 68, "net-zero by 2035", "LOW", "Specific, near-dated net-zero target."),
   "metric":       D("target of 30% take-back by 2030 ... Reduction of Scope 1 and 2", 13, "quantified S1+2 + circularity targets", "LOW", "Quantified emissions and circularity targets with reported progress."),
   "baseline":     D("Compared to 2019, Tele2's Scope 1 and [2]", 13, "2019", "LOW", "Explicit 2019 base year."),
   "target":       D("the Science Based Targets initiative and includes ... align with the 1.5C ambition", 68, "science-based targets, 1.5C", "LOW", "Science-based targets aligned to a 1.5C ambition via the Climate Transition Plan."),
   "time_horizon": D("emissions in Scope 1 and 2 by 2029 ... net-zero by 2035", 13, "2027 / 2029 + 2035", "LOW", "Near-term 2027/2029 milestones present alongside the 2035 net-zero endpoint."),
   "scope":        D("data (Scopes 1-3) is reported in line with the Greenhouse Gas Protocol", 46, "S1+2+3", "LOW", "Scopes 1, 2 and 3 reported per the GHG Protocol."),
   "verification": D("Tele2's auditor KPMG has conducted a limited assurance", 11, "KPMG limited assurance", "MED", "Externally assured by KPMG, but a limited assurance level."),
   "consistency":  D("Climate Transition Plan that align with the 1.5C ambition", 66, "transition plan; capex disclosed", "LOW", "Documented Climate Transition Plan; capex disclosed; no contradiction surfaced."),
 }},
{
 "ticker": "SUBC.OL", "company_name": "Subsea 7 S.A.",
 "analyst_note": "Offshore-energy contractor; assessed from the annual report (no standalone sustainability report). Four MED + one MISSING reflect a 2050-only net-zero horizon, targets that SBTi explicitly does not validate for the sector (candidly disclosed), a fossil-linked capex profile, and a baseline not surfaced in the report. No HIGH flags.",
 "dimensions": {
   "specificity":  D("Net-Zero Scope 1 and 2 GHG emissions by 2050 ... through its decarbonisation plan", 90, "net-zero S1+2 by 2050", "LOW", "Specific net-zero commitment for the company's own fleet (Scope 1+2) via a decarbonisation plan."),
   "metric":       D("own targets to reduce Scope 1 and 2 emissions", 39, "reduction targets stated; % not surfaced", "MED", "Scope 1 intensity is reported and reduction targets are stated, but a quantified reduction percentage is not surfaced in the extract."),
   "baseline":     D(None, None, "no emissions baseline year surfaced", "MISSING", "No emissions baseline year is evident in the extract from the annual report."),
   "target":       D("are not accepted as part of the Science Based Targets initiative (SBTi). Subsea7 continues to monitor this position", 94, "own targets; SBTi does not accept the sector", "MED", "Subsea 7 has set its own GHG targets but candidly discloses that the SBTi does not currently accept its sector — so the targets are not third-party-validated."),
   "time_horizon": D("Net-Zero Scope 1 and 2 GHG emissions by 2050", 90, "2050 endpoint; near-term milestone unclear", "MED", "The headline climate horizon is the 2050 net-zero endpoint; a near-term interim climate milestone is not crisply evidenced."),
   "scope":        D("operations (Scope 1 and 2) ... upstream value chain (Scope 3)", 92, "S1+2+3", "LOW", "Scope 1, 2 and upstream Scope 3 covered."),
   "verification": D("Limited Assurance Report on [the sustainability information]", 3, "limited assurance", "MED", "Externally assured, but a limited assurance level."),
   "consistency":  D("capital expenditure in Renewables was $69 million", 25, "renewables capex disclosed; profile still oil-linked", "MED", "Renewables capex is disclosed, but the bulk of the capex profile remains offshore-oil-linked — a genuine consistency watch-point, disclosed transparently."),
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
    miss  = sum(1 for d in a["dimensions"].values() if d["rating"] == "MISSING")
    print(f"  {a['ticker']:<11} {a['company_name'][:32]:<33} HIGH={highs} MED={meds} MISSING={miss}  -> {path}")

print(f"\n{len(ASSESS)} greenwashing assessments written to outputs/rag/")
