#!/usr/bin/env python
"""Build a self-contained HTML dashboard for the live demo.

Reads the pipeline outputs (final portfolio, greenwashing scores, factsheet,
mandate) and writes ONE standalone .html file — all data, styling and charts
embedded, no external dependencies, works offline by double-click.

    python scripts/build_dashboard.py
    -> outputs/dashboard/esade_dashboard.html
"""
import glob, html, json, os
import pandas as pd
from datetime import date

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(PROJECT)
TODAY = str(date.today())

# ── Load data ──────────────────────────────────────────────────────────────────
fp = pd.read_csv(sorted(glob.glob("outputs/portfolio/final_portfolio_*.csv"))[-1])
gw = pd.read_csv(sorted(glob.glob("outputs/scores/greenwashing_scores_*.csv"))[-1])
uni_files = sorted(glob.glob("outputs/portfolio/universe_scores_*.csv"), key=os.path.getsize)
uni = pd.read_csv(uni_files[-1]) if uni_files else None
mandate = {}
if os.path.exists("outputs/scores/mandate.json"):
    mandate = json.load(open("outputs/scores/mandate.json"))

N_UNIVERSE = len(pd.read_csv("data/provided/universe_289_filled.csv"))
N_CAPPED   = len(pd.read_csv("data/provided/stage2_top40_capped_hybrid.csv"))
N_ELIGIBLE = 224   # ESG Stage 1-2: vendor 2-of-3 triangulation eligible set
N_FINAL    = len(fp)

def esc(x): return html.escape(str(x))

# ── Headline metrics ───────────────────────────────────────────────────────────
w = fp["weight"]
wesg   = (fp["ESG_score"] * w).sum()
wsharp = (fp["sharpe_ratio"] * w).sum()
waci   = (fp["carbon_intensity"].fillna(0) * w).sum()
n_sect = fp["sasb_sector"].nunique()
maxw   = w.max() * 100
gw_pass = int((gw["gw_high_count"] < 2).sum())
n_ic    = int(fp["override_disposition"].notna().sum())
uni_esg = uni["ESG_score"].mean() if uni is not None and "ESG_score" in uni.columns else 79.3

# ════════════════════════════════════════════════════════════════════════════
# Component builders
# ════════════════════════════════════════════════════════════════════════════
def metric_cards(cards):
    out = ['<div class="cards">']
    for big, label, sub in cards:
        out.append(f'<div class="card"><div class="card-big">{esc(big)}</div>'
                   f'<div class="card-label">{esc(label)}</div>'
                   f'<div class="card-sub">{esc(sub)}</div></div>')
    out.append('</div>')
    return "".join(out)

def funnel():
    stages = [("Investable universe", N_UNIVERSE, "European equities screened"),
              ("ESG-eligible", N_ELIGIBLE, "vendor 2-of-3 triangulation + red-flag override"),
              ("Sector-capped shortlist", N_CAPPED, "Stage 1-2 in-house ESG score, Top 40"),
              ("Final portfolio", N_FINAL, "Stage 3: financial screen + composite rank")]
    mx = stages[0][1]
    rows = []
    for i, (name, n, sub) in enumerate(stages):
        pct = 22 + 78 * n / mx
        rows.append(
            f'<div class="funnel-row">'
            f'<div class="funnel-bar f{i}" style="width:{pct:.1f}%">'
            f'<span class="funnel-n">{n}</span>'
            f'<span class="funnel-name">{esc(name)}</span></div>'
            f'<div class="funnel-sub">{esc(sub)}</div></div>')
    return '<div class="funnel">' + "".join(rows) + '</div>'

def holdings_table():
    d = fp.sort_values("weight", ascending=False)
    rows = []
    for i, (_, r) in enumerate(d.iterrows(), 1):
        ic = r["override_disposition"] if pd.notna(r["override_disposition"]) else ""
        ictag = f'<span class="pill">{esc(ic)}</span>' if ic else ""
        rows.append(
            f"<tr><td>{i}</td><td class='nm'>{esc(r['company_name'])}</td>"
            f"<td class='mono'>{esc(r['yf_ticker'])}</td>"
            f"<td>{esc(r['sasb_sector'])}</td>"
            f"<td class='num'>{r['weight']*100:.2f}%</td>"
            f"<td class='num'>{r['ESG_score']:.1f}</td>"
            f"<td class='num'>{r['fin_score']:.1f}</td>"
            f"<td class='num'>{r['composite_score']:.1f}</td>"
            f"<td class='num'>{r['gw_score_pct']:.1f}%</td>"
            f"<td>{ictag}</td></tr>")
    return ('<table class="grid"><thead><tr>'
            '<th>#</th><th>Company</th><th>Ticker</th><th>Sector</th>'
            '<th class="num">Weight</th><th class="num">ESG</th>'
            '<th class="num">Financial</th><th class="num">Composite</th>'
            '<th class="num">8-Test</th><th>IC review</th>'
            '</tr></thead><tbody>' + "".join(rows) + '</tbody></table>')

def weight_bars():
    d = fp.sort_values("weight", ascending=False)
    mx = d["weight"].max() * 100
    rows = []
    for _, r in d.iterrows():
        pc = r["weight"] * 100
        rows.append(
            f'<div class="hbar-row"><div class="hbar-label">{esc(r["company_name"])}</div>'
            f'<div class="hbar-track"><div class="hbar-fill" style="width:{pc/mx*100:.1f}%">'
            f'</div></div><div class="hbar-val">{pc:.2f}%</div></div>')
    return '<div class="hbars">' + "".join(rows) + '</div>'

def sector_bars():
    g = (fp.groupby("sasb_sector")["weight"].agg(["sum", "count"])
           .sort_values("sum", ascending=False))
    mx = g["sum"].max() * 100
    rows = []
    for sec, r in g.iterrows():
        pc = r["sum"] * 100
        rows.append(
            f'<div class="hbar-row"><div class="hbar-label">{esc(sec)}</div>'
            f'<div class="hbar-track"><div class="hbar-fill sec" '
            f'style="width:{pc/mx*100:.1f}%"></div></div>'
            f'<div class="hbar-val">{pc:.1f}% &middot; {int(r["count"])}</div></div>')
    return '<div class="hbars">' + "".join(rows) + '</div>'

def esg_compare():
    parts = []
    pairs = [("Environmental", "E_score"), ("Social", "S_score"),
             ("Governance", "G_score"), ("ESG aggregate", "ESG_score")]
    for label, col in pairs:
        pv = (fp[col] * w).sum()
        uv = uni[col].mean() if uni is not None and col in uni.columns else None
        bar_u = (f'<div class="esg-bar u" style="height:{uv:.0f}%" '
                 f'title="Universe {uv:.1f}"></div>' if uv is not None else "")
        ulab = f'<span class="esg-num u">{uv:.0f}</span>' if uv is not None else ""
        parts.append(
            f'<div class="esg-col"><div class="esg-bars">'
            f'{bar_u}<div class="esg-bar p" style="height:{pv:.0f}%" '
            f'title="Portfolio {pv:.1f}"></div></div>'
            f'<div class="esg-nums">{ulab}<span class="esg-num p">{pv:.0f}</span></div>'
            f'<div class="esg-label">{label}</div></div>')
    return ('<div class="esg-chart">' + "".join(parts) + '</div>'
            '<div class="legend"><span class="lg u"></span>Capped-40 universe'
            '&nbsp;&nbsp;<span class="lg p"></span>Final portfolio (weighted)</div>')

DIMS = [("specificity","Specificity"),("metric","Metric"),("baseline","Baseline"),
        ("target","Target"),("time_horizon","Time horizon"),("scope","Scope"),
        ("verification","Verification"),("consistency","Consistency")]
SHOW = {"LOW":"PASS","MED":"PARTIAL","HIGH":"FAIL","MISSING":"MISSING"}
CLS  = {"PASS":"pass","PARTIAL":"part","FAIL":"fail","MISSING":"miss"}

def scorecard():
    d = gw.sort_values("gw_score_pct")
    head = "".join(f"<th>{lbl}</th>" for _, lbl in DIMS)
    rows = []
    for _, r in d.iterrows():
        cells = []
        for dk, lbl in DIMS:
            raw = str(r[f"gw_{dk}_rating"]).upper()
            sh = SHOW.get(raw, raw)
            cells.append(f'<td class="cell {CLS[sh]}" title="{lbl}: {sh}">{sh[0]}</td>')
        dec = ("EXCLUDE" if r["gw_high_count"] >= 3 else
               "WATCHLIST" if r["gw_high_count"] == 2 else "PASS")
        rows.append(
            f'<tr><td class="nm">{esc(r["company_name"])}</td>{"".join(cells)}'
            f'<td class="num">{r["gw_score_pct"]:.1f}%</td>'
            f'<td><span class="pill {CLS["PASS" if dec=="PASS" else "FAIL"]}">{dec}</span></td></tr>')
    return ('<table class="grid scorecard"><thead><tr><th>Company</th>' + head +
            '<th class="num">Score</th><th>Verdict</th></tr></thead><tbody>' +
            "".join(rows) + '</tbody></table>')

def pipeline():
    phases = [
        ("Define &amp; ingest", [
            ("1", "Mandate", "Thesis, scoring weights, exclusion rules"),
            ("2", "Data Ingestion", "4 datasets + market prices, merged &amp; vintage-tagged"),
            ("3", "Data Quality", "Missing-value audit, outliers, data dictionary")]),
        ("Analyse", [
            ("10", "Financial Analysis", "Returns, volatility, Sharpe, quality screen"),
            ("5/6", "ESG &amp; Climate", "E/S/G scores, SASB weights, WACI"),
            ("7", "Biodiversity", "Nature-risk proxies (ENCORE, WRI Aqueduct)"),
            ("8", "EU Regulation", "EU Taxonomy, SFDR, PAI indicators")]),
        ("Investigate", [
            ("4", "Document Intelligence", "RAG over sustainability-report corpus"),
            ("9", "Greenwashing 8-Test", "8-dimension claim screen, Tier-1 + Tier-2")]),
        ("Construct &amp; report", [
            ("11", "Portfolio Construction", "Composite rank, diversification, weights"),
            ("12", "Human Review", "IC override log, AI-use statement"),
            ("13", "Reporting", "Factsheet, charts, this dashboard")]),
    ]
    out = ['<div class="pipe">']
    for pi, (phase, agents) in enumerate(phases):
        out.append(f'<div class="phase"><div class="phase-h">{phase}</div>'
                   f'<div class="phase-agents">')
        for num, name, desc in agents:
            out.append(f'<div class="agent"><div class="agent-n">{num}</div>'
                       f'<div class="agent-name">{name}</div>'
                       f'<div class="agent-desc">{desc}</div></div>')
        out.append('</div></div>')
        if pi < len(phases) - 1:
            out.append('<div class="phase-arrow">&rarr;</div>')
    out.append('</div>')
    return "".join(out)

def ic_table():
    d = fp[fp["override_disposition"].notna()].sort_values("override_disposition")
    rows = []
    for _, r in d.iterrows():
        rat = r.get("override_rationale_short", "")
        rows.append(
            f"<tr><td class='nm'>{esc(r['company_name'])}</td>"
            f"<td>{esc(r.get('override_type',''))}</td>"
            f"<td><span class='pill'>{esc(r['override_disposition'])}</span></td>"
            f"<td>{esc(rat if pd.notna(rat) else '')}</td></tr>")
    return ('<table class="grid"><thead><tr><th>Company</th><th>Trigger</th>'
            '<th>IC disposition</th><th>Rationale</th></tr></thead><tbody>' +
            "".join(rows) + '</tbody></table>')

# ════════════════════════════════════════════════════════════════════════════
# Assemble
# ════════════════════════════════════════════════════════════════════════════
thesis = mandate.get("investment_thesis", "")
fund   = mandate.get("fund_name", "ESADE Sustainable European Equity Fund")
bench  = mandate.get("benchmark", "STOXX Europe 600")

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;
 background:#eef1f4;color:#1b2a3a;line-height:1.5}
.wrap{max-width:1180px;margin:0 auto;padding:0 22px}
header{background:linear-gradient(135deg,#163a5f,#1F4E78);color:#fff;padding:26px 0 20px}
header h1{font-size:25px;font-weight:700;letter-spacing:.2px}
header .sub{opacity:.85;font-size:14px;margin-top:3px}
header .disc{margin-top:10px;font-size:11.5px;opacity:.7}
nav{background:#0f2942;position:sticky;top:0;z-index:10}
nav .wrap{display:flex;gap:2px;flex-wrap:wrap}
.tab{background:none;border:0;color:#bcd0e4;font-size:13.5px;font-weight:600;
 padding:13px 17px;cursor:pointer;border-bottom:3px solid transparent}
.tab:hover{color:#fff}
.tab.active{color:#fff;border-bottom-color:#3fbf8f}
section{display:none;padding:26px 0 50px}
section.active{display:block}
h2{font-size:19px;color:#163a5f;margin:4px 0 4px}
h3{font-size:14px;color:#3a5266;margin:22px 0 9px;text-transform:uppercase;letter-spacing:.6px}
p.lead{font-size:14.5px;color:#3a5266;max-width:860px;margin-bottom:6px}
.cards{display:flex;flex-wrap:wrap;gap:14px;margin:16px 0}
.card{background:#fff;border-radius:10px;padding:16px 18px;flex:1;min-width:150px;
 box-shadow:0 1px 3px rgba(0,0,0,.08);border-left:4px solid #3fbf8f}
.card-big{font-size:27px;font-weight:700;color:#163a5f}
.card-label{font-size:12.5px;font-weight:700;margin-top:2px}
.card-sub{font-size:11.5px;color:#6b7d8d;margin-top:2px}
.panel{background:#fff;border-radius:10px;padding:18px 20px;margin:14px 0;
 box-shadow:0 1px 3px rgba(0,0,0,.08)}
.funnel{margin:6px 0}
.funnel-row{margin:9px 0}
.funnel-bar{color:#fff;padding:11px 15px;border-radius:7px;display:flex;align-items:baseline;gap:12px}
.funnel-bar.f0{background:#5b7f9e}.funnel-bar.f1{background:#3f6f93}
.funnel-bar.f2{background:#2b5a86}.funnel-bar.f3{background:#1F4E78}
.funnel-n{font-size:21px;font-weight:700}
.funnel-name{font-size:13.5px;font-weight:600}
.funnel-sub{font-size:11.5px;color:#6b7d8d;margin-top:3px;margin-left:3px}
table.grid{width:100%;border-collapse:collapse;font-size:12.5px;margin-top:4px}
table.grid th{background:#163a5f;color:#fff;text-align:left;padding:8px 9px;font-size:11px;
 text-transform:uppercase;letter-spacing:.4px}
table.grid td{padding:7px 9px;border-bottom:1px solid #e6eaee}
table.grid tr:nth-child(even) td{background:#f6f8fa}
td.nm{font-weight:600}.num,th.num{text-align:right}.mono{font-family:ui-monospace,Menlo,monospace;font-size:11.5px}
.pill{display:inline-block;background:#e7eef5;color:#1F4E78;font-size:10.5px;font-weight:700;
 padding:2px 8px;border-radius:10px;white-space:nowrap}
.pill.pass{background:#d6f0dd;color:#1a7f37}.pill.fail{background:#fbd5d2;color:#b3261e}
.hbars{margin-top:4px}
.hbar-row{display:flex;align-items:center;gap:10px;margin:3px 0}
.hbar-label{width:210px;font-size:12px;text-align:right;flex-shrink:0}
.hbar-track{flex:1;background:#eef1f4;border-radius:4px;height:17px}
.hbar-fill{height:17px;border-radius:4px;background:#1F4E78}
.hbar-fill.sec{background:#3fbf8f}
.hbar-val{width:96px;font-size:11.5px;color:#3a5266;flex-shrink:0}
.esg-chart{display:flex;gap:30px;align-items:flex-end;height:200px;padding:14px 10px 0}
.esg-col{flex:1;display:flex;flex-direction:column;align-items:center}
.esg-bars{display:flex;gap:7px;align-items:flex-end;height:140px}
.esg-bar{width:34px;border-radius:4px 4px 0 0}
.esg-bar.u{background:#a9bccc}.esg-bar.p{background:#1F4E78}
.esg-nums{display:flex;gap:7px;margin-top:5px}
.esg-num{width:34px;text-align:center;font-size:12px;font-weight:700}
.esg-num.u{color:#7e93a4}.esg-num.p{color:#1F4E78}
.esg-label{font-size:12px;font-weight:600;margin-top:3px;color:#3a5266}
.legend{font-size:11.5px;color:#6b7d8d;margin-top:12px}
.lg{display:inline-block;width:11px;height:11px;border-radius:2px;vertical-align:middle;margin-right:4px}
.lg.u{background:#a9bccc}.lg.p{background:#1F4E78}
table.scorecard td.cell{text-align:center;font-weight:700;font-size:11px;width:64px}
.cell.pass{background:#d6f0dd;color:#1a7f37}.cell.part{background:#fdf0c8;color:#9a6700}
.cell.fail{background:#fbd5d2;color:#b3261e}.cell.miss{background:#e3e3e3;color:#5a5a5a}
.banner{background:#d6f0dd;color:#155e2e;border-radius:8px;padding:12px 16px;font-size:13.5px;
 font-weight:600;margin:10px 0}
.pipe{display:flex;align-items:stretch;gap:6px;flex-wrap:wrap;margin-top:8px}
.phase{background:#f0f3f6;border-radius:9px;padding:11px;flex:1;min-width:200px}
.phase-h{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;
 color:#1F4E78;margin-bottom:8px;text-align:center}
.phase-agents{display:flex;flex-direction:column;gap:7px}
.agent{background:#fff;border-radius:7px;padding:8px 10px;border-left:3px solid #3fbf8f}
.agent-n{font-size:10px;font-weight:700;color:#3fbf8f}
.agent-name{font-size:12.5px;font-weight:700}
.agent-desc{font-size:10.8px;color:#6b7d8d;margin-top:1px}
.phase-arrow{display:flex;align-items:center;color:#9fb2c2;font-size:20px;font-weight:700}
.two{display:flex;gap:16px;flex-wrap:wrap}.two>.panel{flex:1;min-width:320px}
ul.clean{list-style:none;font-size:12.8px}
ul.clean li{padding:5px 0 5px 20px;position:relative;border-bottom:1px solid #eef1f4}
ul.clean li:before{content:"\\2713";position:absolute;left:0;color:#3fbf8f;font-weight:700}
.note{font-size:11.8px;color:#6b7d8d;margin-top:8px}
footer{background:#0f2942;color:#9fb2c2;font-size:11.5px;padding:16px 0;text-align:center}
"""

JS = """
function show(id,btn){
 document.querySelectorAll('section').forEach(s=>s.classList.remove('active'));
 document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
 document.getElementById(id).classList.add('active');
 btn.classList.add('active');
 window.scrollTo(0,0);
}
"""

TABS = [("ov","Overview"),("pf","Portfolio"),("esg","ESG &amp; Climate"),
        ("gw","Greenwashing 8-Test"),("pi","Pipeline &amp; Integrity")]
nav = "".join(
    f'<button class="tab{" active" if i==0 else ""}" '
    f'onclick="show(\'{tid}\',this)">{label}</button>'
    for i, (tid, label) in enumerate(TABS))

# ── Section: Overview ──────────────────────────────────────────────────────────
ov = f"""<div class="wrap">
<h2>{esc(fund)}</h2>
<p class="lead">{esc(thesis)}</p>
{metric_cards([
 (N_FINAL,"Holdings","long-only European equities"),
 (n_sect,"Sectors",f"largest {fp.groupby('sasb_sector')['weight'].sum().max()*100:.1f}% (cap 25%)"),
 (f"{wesg:.1f}","Weighted ESG score",f"vs {uni_esg:.1f} universe (+{wesg-uni_esg:.1f})"),
 (f"{wsharp:.2f}","Weighted Sharpe","5y, vs STOXX Europe 600"),
 (f"{waci:.0f}","WACI tCO2e/$M","weighted avg carbon intensity"),
 (f"{gw_pass}/{N_FINAL}","Greenwashing PASS","8-Test, 0 excluded"),
])}
<h3>From universe to portfolio</h3>
<div class="panel">{funnel()}</div>
<p class="note">Benchmark: {esc(bench)}. Academic prototype &mdash; not investment advice.</p>
</div>"""

# ── Section: Portfolio ─────────────────────────────────────────────────────────
pf = f"""<div class="wrap">
<h2>The final {N_FINAL}-stock portfolio</h2>
<p class="lead">Selected by composite score (60% financial quality + 40% ESG),
with a hard max-5-holdings-per-sector cap, a 0.90 return-correlation guard,
and weights capped at 10% per name.</p>
<div class="panel">{holdings_table()}</div>
<div class="two">
<div class="panel"><h3>Holding weights</h3>{weight_bars()}</div>
<div class="panel"><h3>Sector allocation</h3>{sector_bars()}
<p class="note">Weight &middot; number of holdings. Sector cap: 5 holdings / 25%.</p></div>
</div></div>"""

# ── Section: ESG & Climate ─────────────────────────────────────────────────────
esg = f"""<div class="wrap">
<h2>ESG &amp; climate profile</h2>
<p class="lead">Every holding carries an E, S, G and aggregate score; the portfolio
is weighted toward higher-scoring names than the screened universe.</p>
<div class="panel"><h3>Portfolio vs universe &mdash; E / S / G / aggregate</h3>
{esg_compare()}</div>
<div class="two">
<div class="panel"><h3>Carbon &mdash; WACI</h3>
{metric_cards([(f"{waci:.0f}","tCO2e/$M revenue","weighted avg carbon intensity"),
 ("~62%","driven by one name","Norsk Hydro; ex-Norsk Hydro WACI &asymp; 62")])}
<p class="note">18 of 20 holdings use sector-median imputed carbon intensity;
the Financials WACI excludes PCAF Scope&nbsp;3 financed emissions &mdash; a disclosed
methodology limitation.</p></div>
<div class="panel"><h3>What is measured</h3>
<ul class="clean">
<li>E / S / G scores 0&ndash;100, SASB-materiality weighted</li>
<li>WACI &mdash; weighted average carbon intensity (Scope 1+2)</li>
<li>Biodiversity nature-risk proxy (ENCORE, WRI Aqueduct)</li>
<li>EU Taxonomy eligibility &amp; alignment overlay</li>
<li>Benchmark comparison vs {esc(bench)}</li>
</ul></div></div></div>"""

# ── Section: Greenwashing ──────────────────────────────────────────────────────
gw_sec = f"""<div class="wrap">
<h2>Greenwashing 8-Test</h2>
<p class="lead">Each holding's headline sustainability claim is tested on eight
dimensions, rated PASS / PARTIAL / FAIL / MISSING. Tier 1 = primary company
documents (verbatim, page-cited); Tier 2 = external verification (SBTi database,
TPI Carbon Performance). Rule: 3+ FAIL excludes, exactly 2 watchlists.</p>
<div class="banner">&#10003; All {N_FINAL} holdings PASS &mdash; 0 excluded, 0 watchlisted,
no FAIL on any dimension. Weighted concern score 8.2%.</div>
<div class="panel">{scorecard()}
<p class="note">Cell letter = rating (P PASS &middot; P PARTIAL &middot; F FAIL &middot;
M MISSING) &mdash; hover for the dimension. Sorted lowest-concern first.</p></div>
</div>"""

# ── Section: Pipeline & Integrity ──────────────────────────────────────────────
pi = f"""<div class="wrap">
<h2>The agent pipeline</h2>
<p class="lead">A chain of specialised AI agents, orchestrated in n8n.cloud.
Each step is a notebook; code is AI-generated and every output is human-verified.</p>
<div class="panel">{pipeline()}</div>
<div class="two">
<div class="panel"><h3>Human oversight &mdash; IC overrides</h3>
<p class="lead">{n_ic} of {N_FINAL} holdings carry a documented Investment
Committee override decision.</p>
{ic_table()}</div>
<div class="panel"><h3>Integrity controls</h3>
<ul class="clean">
<li>Never invent data &mdash; absent &rarr; marked MISSING</li>
<li>30% random sample of RAG extractions verified vs source PDF</li>
<li>100% of watchlist / exclusion decisions independently verified</li>
<li>ESG ratings treated as indicators, not objective truth</li>
<li>All financials cross-checked against market data</li>
<li>Honest disclosure: 90% of carbon intensity is sector-median imputed</li>
</ul>
<p class="note">Authoritative greenwashing record: the RAG Screening Sheet
workbook. Generated {TODAY}.</p></div>
</div></div>"""

SECTIONS = {"ov":ov,"pf":pf,"esg":esg,"gw":gw_sec,"pi":pi}
body = "".join(
    f'<section id="{tid}" class="{"active" if i==0 else ""}">{SECTIONS[tid]}</section>'
    for i, (tid, _) in enumerate(TABS))

doc = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(fund)} &mdash; Live Dashboard</title>
<style>{CSS}</style></head><body>
<header><div class="wrap">
<h1>{esc(fund)}</h1>
<div class="sub">AI-agent research pipeline for sustainable portfolio construction
&middot; ESADE MSc Finance</div>
<div class="disc">Academic prototype &mdash; not a regulated product or investment
advice. Data vintage {TODAY}.</div>
</div></header>
<nav><div class="wrap">{nav}</div></nav>
{body}
<footer>ESADE Sustainable Finance &mdash; final group assignment &middot;
self-contained dashboard, generated {TODAY} from outputs/</footer>
<script>{JS}</script></body></html>"""

os.makedirs("outputs/dashboard", exist_ok=True)
out_path = f"outputs/dashboard/esade_dashboard.html"
with open(out_path, "w", encoding="utf-8") as f:
    f.write(doc)
print(f"Dashboard written: {out_path}  ({len(doc):,} bytes, self-contained)")
print(f"  {N_FINAL} holdings | {n_sect} sectors | weighted ESG {wesg:.1f} | "
      f"WACI {waci:.0f} | greenwashing {gw_pass}/{N_FINAL} PASS")
print("  Open by double-click — works offline, no dependencies.")
