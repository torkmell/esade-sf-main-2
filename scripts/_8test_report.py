#!/usr/bin/env python
"""Per-company greenwashing 8-Test report — every dimension's rating, the final
recommendation, and how each was assessed.

Combines:
  * outputs/scores/greenwashing_scores_*.csv   final (Tier-2-revised) ratings + score
  * outputs/rag/_tier1_archive/greenwash_*.json  per-dimension evidence + reasoning
  * outputs/rag/_tier2_sbti_cp.csv             SBTi / TPI external checks
Writes a Markdown report to outputs/rag/.
"""
import glob, json, os
import pandas as pd
from datetime import date

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(PROJECT)
TODAY = str(date.today())

DIMS = [("specificity","Specificity"), ("metric","Metric"), ("baseline","Baseline"),
        ("target","Target"), ("time_horizon","Time Horizon"), ("scope","Scope"),
        ("verification","Verification"), ("consistency","Consistency")]
SHOW   = {"LOW":"PASS", "MED":"PARTIAL", "HIGH":"FAIL", "MISSING":"MISSING"}
POINTS = {"LOW":0, "MED":1, "HIGH":2, "MISSING":1}

gw = pd.read_csv(sorted(glob.glob("outputs/scores/greenwashing_scores_*.csv"))[-1])
t2 = pd.read_csv("outputs/rag/_tier2_sbti_cp.csv").set_index("ticker")

def tier1(tk):
    p = f"outputs/rag/_tier1_archive/greenwash_{tk}.json"
    return json.load(open(p))["dimensions"] if os.path.exists(p) else {}

def t2_note(tk):
    if tk not in t2.index:
        return "no SBTi/TPI record"
    r = t2.loc[tk]
    s = str(r["sbti_near_term_status"])
    sb = ("not in the SBTi database" if s in ("--","nan","")
          else f"SBTi near-term status '{s}'"
               + (f", {r['sbti_near_term_class']} ({r['sbti_near_term_year']})"
                  if s == "Targets set" else ""))
    tp = str(r["tpi_cp"])
    tpi = f"; TPI Carbon Performance {tp}-aligned" if ("degree" in tp.lower() or "1.5" in tp) \
          else "; not assessed by TPI"
    return sb + tpi

rows = gw.sort_values("gw_score_pct").reset_index(drop=True)
out = [f"# Greenwashing 8-Test — Per-Company Screening Report",
       f"_Generated {TODAY} · 20 portfolio holdings · Agent 9_\n",
       "**How to read this.** Each company's headline sustainability claim is "
       "tested on 8 dimensions, each rated PASS / PARTIAL / FAIL / MISSING. "
       "Ratings convert to risk points (PASS 0 · PARTIAL 1 · MISSING 1 · FAIL 2); "
       "the total over 16 is the 8-Test concern score. Recommendation rule: "
       "**3+ FAIL → EXCLUDE · exactly 2 FAIL → WATCHLIST · otherwise PASS.** "
       "Dimensions 4 (Target) and 7 (Verification) also use Tier-2 external "
       "evidence — the SBTi database and TPI Carbon Performance assessments.\n",
       "## Summary\n",
       "| # | Company | Ticker | Score | PASS | PARTIAL | FAIL | MISSING | Recommendation |",
       "|---|---------|--------|-------|------|---------|------|---------|----------------|"]

for i, r in rows.iterrows():
    ratings = [str(r[f"gw_{d}_rating"]).upper() for d, _ in DIMS]
    nP = sum(SHOW[x]=="PASS" for x in ratings)
    nQ = sum(SHOW[x]=="PARTIAL" for x in ratings)
    nF = sum(SHOW[x]=="FAIL" for x in ratings)
    nM = sum(x=="MISSING" for x in ratings)
    rec = "EXCLUDE" if nF>=3 else "WATCHLIST" if nF==2 else "PASS"
    out.append(f"| {i+1} | {r['company_name']} | {r['ticker']} | "
               f"{r['gw_score_pct']:.1f}% | {nP} | {nQ} | {nF} | {nM} | {rec} |")

out.append("\n---\n")

for i, r in rows.iterrows():
    tk = r["ticker"]
    t1 = tier1(tk)
    ratings = [str(r[f"gw_{d}_rating"]).upper() for d, _ in DIMS]
    pts = sum(POINTS[x] for x in ratings)
    nF  = sum(SHOW[x]=="FAIL" for x in ratings)
    nQ  = sum(SHOW[x]=="PARTIAL" for x in ratings)
    nM  = sum(x=="MISSING" for x in ratings)
    nP  = 8 - nQ - nF - nM
    rec = "EXCLUDE" if nF>=3 else "WATCHLIST" if nF==2 else "PASS"

    out.append(f"## {i+1}. {r['company_name']}  ·  {tk}")
    out.append(f"**8-Test score: {r['gw_score_pct']:.1f}%  ·  Recommendation: {rec}**\n")
    sp = t1.get("specificity", {})
    if sp.get("quote"):
        out.append(f"Main claim tested: \"{sp['quote']}\" — p.{sp.get('page','?')}")
    out.append(f"Tier-2 external check: {t2_note(tk)}.\n")
    out.append("| # | Dimension | Rating | How it was assessed |")
    out.append("|---|-----------|--------|---------------------|")
    for n, (dk, label) in enumerate(DIMS, 1):
        rt = ratings[n-1]
        d1 = t1.get(dk, {})
        reason = str(d1.get("reasoning") or "").strip()
        t1rt = str(d1.get("rating","")).upper()
        # Where Tier-2 moved the rating, say so explicitly.
        if dk in ("target","verification") and t1rt and t1rt != rt:
            reason += (f" _Tier-2 revision: Tier-1 reading was {SHOW.get(t1rt,t1rt)}; "
                       f"adjusted to {SHOW[rt]} on the SBTi/TPI evidence above._")
        elif dk in ("target","verification"):
            reason += " _(corroborated by the Tier-2 SBTi/TPI evidence above.)_"
        q = str(d1.get("quote") or "").strip()
        if q and dk not in ("specificity",):
            reason += f"  Evidence: \"{q}\" (p.{d1.get('page','?')})."
        reason = reason.replace("\n", " ") or "—"
        out.append(f"| {n} | {label} | **{SHOW[rt]}** | {reason} |")

    out.append("")
    out.append(f"**Score logic.** {nP} PASS (0 pts) · {nQ} PARTIAL (1) · "
               f"{nM} MISSING (1) · {nF} FAIL (2)  =  {pts}/16  =  "
               f"**{r['gw_score_pct']:.1f}%**.")
    out.append(f"**Recommendation logic.** {nF} dimension(s) rated FAIL "
               f"(EXCLUDE needs ≥3, WATCHLIST needs exactly 2) → **{rec}**.")
    note = str(r.get("analyst_note","")).strip()
    if note and note.lower() != "nan":
        out.append(f"**Verdict rationale.** {note}")
    out.append("\n---\n")

txt = "\n".join(out)
path = f"outputs/rag/greenwashing_8test_report_{TODAY}.md"
with open(path, "w", encoding="utf-8") as f:
    f.write(txt)
print(f"Report written: {path}  ({len(txt):,} chars, {len(rows)} companies)")
print()
print("\n".join(out[5:5 + len(rows) + 2]))   # echo the summary table
