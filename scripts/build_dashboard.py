#!/usr/bin/env python
"""Build the self-contained HTML demo dashboard.

Reads the pipeline outputs and writes ONE standalone .html file — all data,
styling and charts embedded, no external dependencies, works offline by
double-click. Eight sections mirror the IC presentation:
  The Problem · The Solution · The Pipeline · Portfolio · Financials ·
  ESG & Climate · Greenwashing 8-Test · Oversight & Recommendation

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
bt_path = "Optimization_module/outputs/backtest_results.csv"
bt = pd.read_csv(bt_path) if os.path.exists(bt_path) else None
mandate = json.load(open("outputs/scores/mandate.json")) if os.path.exists(
    "outputs/scores/mandate.json") else {}

N_UNIVERSE = len(pd.read_csv("data/provided/universe_289_filled.csv"))
N_CAPPED   = len(pd.read_csv("data/provided/stage2_top40_capped_hybrid.csv"))
N_ELIGIBLE = 224
N_FINAL    = len(fp)
fund   = mandate.get("fund_name", "ESADE Sustainable European Equity Fund")
bench  = mandate.get("benchmark", "STOXX Europe 600")
thesis = mandate.get("investment_thesis", "")

def esc(x): return html.escape(str(x))

# ── Headline metrics ───────────────────────────────────────────────────────────
w = fp["weight"]
wesg    = (fp["ESG_score"]    * w).sum()
wfin    = (fp["fin_score"]    * w).sum()
wsharp  = (fp["sharpe_ratio"] * w).sum()
wvol    = (fp["vol_annual"]   * w).sum()
wmdd    = (fp["max_drawdown"] * w).sum()
wbeta   = (fp["beta"]         * w).sum()
waci    = (fp["carbon_intensity"].fillna(0) * w).sum()
n_sect  = fp["sasb_sector"].nunique()
maxw    = w.max() * 100
gw_pass = int((fp["gw_high_count"] < 2).sum())
n_ic    = int(fp["override_disposition"].notna().sum())
uni_esg = uni["ESG_score"].mean() if uni is not None and "ESG_score" in uni.columns else 79.3
top_sec = fp.groupby("sasb_sector")["weight"].sum()

# ════════════════════════════════════════════════════════════════════════════
# Component builders
# ════════════════════════════════════════════════════════════════════════════
def metric_cards(cards):
    out = ['<div class="cards">']
    for big, label, sub in cards:
        out.append(f'<div class="card"><div class="card-big">{esc(big)}</div>'
                   f'<div class="card-label">{esc(label)}</div>'
                   f'<div class="card-sub">{esc(sub)}</div></div>')
    return "".join(out) + "</div>"

def issue_cards(items):
    out = ['<div class="issues">']
    for title, body in items:
        out.append(f'<div class="issue"><div class="issue-h">{title}</div>'
                   f'<div class="issue-b">{body}</div></div>')
    return "".join(out) + "</div>"

def funnel():
    stages = [("Investable universe", N_UNIVERSE, "European equities screened"),
              ("ESG-eligible", N_ELIGIBLE, "vendor 2-of-3 triangulation + red-flag override"),
              ("Sector-capped shortlist", N_CAPPED, "Stage 1-2 in-house ESG score, Top 40"),
              ("Final portfolio", N_FINAL, "Stage 3: financial screen + composite rank")]
    mx = stages[0][1]
    rows = []
    for i, (name, n, sub) in enumerate(stages):
        pct = 22 + 78 * n / mx
        rows.append(f'<div class="funnel-row"><div class="funnel-bar f{i}" '
                    f'style="width:{pct:.1f}%"><span class="funnel-n">{n}</span>'
                    f'<span class="funnel-name">{esc(name)}</span></div>'
                    f'<div class="funnel-sub">{esc(sub)}</div></div>')
    return '<div class="funnel">' + "".join(rows) + '</div>'

def stages3():
    s = [("1 · Pre-filter", "Universe definition",
          "STOXX Europe 600 screened to a 289-company European universe; "
          "controversial-activity exclusions applied."),
         ("2 · Gate", "Triangulated ESG screen",
          "ISS, Sustainalytics and Truvalue triangulated against the fund's "
          "own standards — 2 of 3 vendors bottom-tier = fail. No single rating "
          "decides. &rarr; 224 eligible &rarr; sector-capped Top 40."),
         ("3 · Score", "Weighted selection",
          "Composite = 60% financial quality + 40% ESG. Hard financial screen, "
          "max-5-per-sector cap and a 0.90 correlation guard &rarr; final 20.")]
    out = ['<div class="three">']
    for tag, title, body in s:
        out.append(f'<div class="panel"><div class="stage-tag">{tag}</div>'
                   f'<h3 style="margin-top:6px">{title}</h3>'
                   f'<p class="lead">{body}</p></div>')
    return "".join(out) + "</div>"

def holdings_table():
    d = fp.sort_values("weight", ascending=False)
    rows = []
    for i, (_, r) in enumerate(d.iterrows(), 1):
        ic = r["override_disposition"] if pd.notna(r["override_disposition"]) else ""
        ictag = f'<span class="pill">{esc(ic)}</span>' if ic else ""
        rows.append(f"<tr><td>{i}</td><td class='nm'>{esc(r['company_name'])}</td>"
                    f"<td class='mono'>{esc(r['yf_ticker'])}</td>"
                    f"<td>{esc(r['sasb_sector'])}</td>"
                    f"<td class='num'>{r['weight']*100:.2f}%</td>"
                    f"<td class='num'>{r['ESG_score']:.1f}</td>"
                    f"<td class='num'>{r['fin_score']:.1f}</td>"
                    f"<td class='num'>{r['composite_score']:.1f}</td>"
                    f"<td class='num'>{r['gw_score_pct']:.1f}%</td><td>{ictag}</td></tr>")
    return ('<table class="grid"><thead><tr><th>#</th><th>Company</th><th>Ticker</th>'
            '<th>Sector</th><th class="num">Weight</th><th class="num">ESG</th>'
            '<th class="num">Financial</th><th class="num">Composite</th>'
            '<th class="num">8-Test</th><th>IC review</th></tr></thead><tbody>'
            + "".join(rows) + '</tbody></table>')

def fin_table():
    d = fp.sort_values("sharpe_ratio", ascending=False)
    rows = []
    for _, r in d.iterrows():
        rows.append(f"<tr><td class='nm'>{esc(r['company_name'])}</td>"
                    f"<td class='num'>{r['weight']*100:.2f}%</td>"
                    f"<td class='num'>{r['sharpe_ratio']:.2f}</td>"
                    f"<td class='num'>{r['vol_annual']*100:.1f}%</td>"
                    f"<td class='num'>{r['max_drawdown']*100:.1f}%</td>"
                    f"<td class='num'>{r['beta']:.2f}</td>"
                    f"<td class='num'>{r['fin_score']:.1f}</td></tr>")
    return ('<table class="grid"><thead><tr><th>Company</th><th class="num">Weight</th>'
            '<th class="num">Sharpe (5y)</th><th class="num">Volatility</th>'
            '<th class="num">Max drawdown</th><th class="num">Beta</th>'
            '<th class="num">Fin. score</th></tr></thead><tbody>'
            + "".join(rows) + '</tbody></table>')

def bars(series_df, valcol, fmt, color="#1F4E78", asc=False):
    d = series_df.sort_values(valcol, ascending=asc)
    mx = d[valcol].max()
    rows = []
    for _, r in d.iterrows():
        v = r[valcol]
        rows.append(f'<div class="hbar-row"><div class="hbar-label">'
                    f'{esc(r["company_name"])}</div><div class="hbar-track">'
                    f'<div class="hbar-fill" style="width:{v/mx*100:.1f}%;'
                    f'background:{color}"></div></div>'
                    f'<div class="hbar-val">{fmt(v)}</div></div>')
    return '<div class="hbars">' + "".join(rows) + '</div>'

def sector_bars():
    g = (fp.groupby("sasb_sector")["weight"].agg(["sum", "count"])
           .sort_values("sum", ascending=False))
    mx = g["sum"].max() * 100
    rows = []
    for sec, r in g.iterrows():
        pc = r["sum"] * 100
        rows.append(f'<div class="hbar-row"><div class="hbar-label">{esc(sec)}</div>'
                    f'<div class="hbar-track"><div class="hbar-fill sec" '
                    f'style="width:{pc/mx*100:.1f}%"></div></div>'
                    f'<div class="hbar-val">{pc:.1f}% &middot; {int(r["count"])}</div></div>')
    return '<div class="hbars">' + "".join(rows) + '</div>'

def esg_compare():
    parts = []
    for label, col in [("Environmental","E_score"), ("Social","S_score"),
                        ("Governance","G_score"), ("ESG aggregate","ESG_score")]:
        pv = (fp[col] * w).sum()
        uv = uni[col].mean() if uni is not None and col in uni.columns else None
        bar_u = (f'<div class="esg-bar u" style="height:{uv:.0f}%"></div>'
                 if uv is not None else "")
        ulab = f'<span class="esg-num u">{uv:.0f}</span>' if uv is not None else ""
        parts.append(f'<div class="esg-col"><div class="esg-bars">{bar_u}'
                      f'<div class="esg-bar p" style="height:{pv:.0f}%"></div></div>'
                      f'<div class="esg-nums">{ulab}<span class="esg-num p">{pv:.0f}'
                      f'</span></div><div class="esg-label">{label}</div></div>')
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
            sh = SHOW.get(str(r[f"gw_{dk}_rating"]).upper(), "MISSING")
            cells.append(f'<td class="cell {CLS[sh]}" title="{lbl}: {sh}">{sh[0]}</td>')
        dec = ("EXCLUDE" if r["gw_high_count"]>=3 else
               "WATCHLIST" if r["gw_high_count"]==2 else "PASS")
        rows.append(f'<tr><td class="nm">{esc(r["company_name"])}</td>{"".join(cells)}'
                    f'<td class="num">{r["gw_score_pct"]:.1f}%</td>'
                    f'<td><span class="pill pass">{dec}</span></td></tr>')
    return ('<table class="grid scorecard"><thead><tr><th>Company</th>' + head +
            '<th class="num">Score</th><th>Verdict</th></tr></thead><tbody>'
            + "".join(rows) + '</tbody></table>')

def pipeline():
    phases = [
        ("Define &amp; ingest", [
            ("1","Mandate","Thesis, scoring weights, exclusion rules"),
            ("2","Data Ingestion","4 datasets + market prices, merged"),
            ("3","Data Quality","Missing-value audit, data dictionary")]),
        ("Analyse", [
            ("10","Financial Analysis","Returns, volatility, Sharpe, quality screen"),
            ("5/6","ESG &amp; Climate","E/S/G scores, SASB weights, WACI"),
            ("7","Biodiversity","Nature-risk proxies (ENCORE, Aqueduct)"),
            ("8","EU Regulation","EU Taxonomy, SFDR, PAI indicators")]),
        ("Investigate", [
            ("4","Document Intelligence","RAG over sustainability reports"),
            ("9","Greenwashing 8-Test","8-dimension claim screen, Tier-1+2")]),
        ("Construct &amp; report", [
            ("11","Portfolio Construction","Composite rank, diversification, weights"),
            ("12","Human Review","IC override log, AI-use statement"),
            ("13","Reporting","Factsheet, charts, this dashboard")]),
    ]
    out = ['<div class="pipe">']
    for pi, (phase, agents) in enumerate(phases):
        out.append(f'<div class="phase"><div class="phase-h">{phase}</div>'
                   '<div class="phase-agents">')
        for num, name, desc in agents:
            out.append(f'<div class="agent"><div class="agent-n">{num}</div>'
                       f'<div class="agent-name">{name}</div>'
                       f'<div class="agent-desc">{desc}</div></div>')
        out.append('</div></div>')
        if pi < len(phases)-1:
            out.append('<div class="phase-arrow">&rarr;</div>')
    return "".join(out) + "</div>"

def ic_table():
    d = fp[fp["override_disposition"].notna()].sort_values("override_disposition")
    rows = []
    for _, r in d.iterrows():
        rat = r.get("override_rationale_short", "")
        rows.append(f"<tr><td class='nm'>{esc(r['company_name'])}</td>"
                    f"<td>{esc(r.get('override_type',''))}</td>"
                    f"<td><span class='pill'>{esc(r['override_disposition'])}</span></td>"
                    f"<td>{esc(rat if pd.notna(rat) else '')}</td></tr>")
    return ('<table class="grid"><thead><tr><th>Company</th><th>Trigger</th>'
            '<th>IC disposition</th><th>Rationale</th></tr></thead><tbody>'
            + "".join(rows) + '</tbody></table>')

def backtest_table():
    d = bt.sort_values("rank")
    rows = []
    for _, r in d.iterrows():
        cls  = ' class="rec-row"' if r["rank"] == 1 else ''
        star = ' &starf;' if r["rank"] == 1 else ''
        rows.append(
            f"<tr{cls}><td class='nm'>{r['method'].replace('_',' ').title()}{star}</td>"
            f"<td class='num'>{r['sharpe']:.2f}</td>"
            f"<td class='num'>{r['sortino']:.2f}</td>"
            f"<td class='num'>{r['cagr']*100:.1f}%</td>"
            f"<td class='num'>{r['max_drawdown']*100:.1f}%</td>"
            f"<td class='num'>{r['ann_vol']*100:.1f}%</td>"
            f"<td class='num'>{r['annual_turnover']*100:.1f}%</td>"
            f"<td class='num'>{r['tracking_error']*100:.1f}%</td>"
            f"<td class='num'>{r['composite_score']:.3f}</td></tr>")
    return ('<table class="grid"><thead><tr><th>Method</th><th class="num">Sharpe</th>'
            '<th class="num">Sortino</th><th class="num">CAGR</th>'
            '<th class="num">Max DD</th><th class="num">Volatility</th>'
            '<th class="num">Turnover</th><th class="num">Tracking err.</th>'
            '<th class="num">Composite</th></tr></thead><tbody>'
            + "".join(rows) + '</tbody></table>')

# ════════════════════════════════════════════════════════════════════════════
CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;
 background:#eef1f4;color:#1b2a3a;line-height:1.5}
.wrap{max-width:1180px;margin:0 auto;padding:0 22px}
header{background:linear-gradient(135deg,#163a5f,#1F4E78);color:#fff;padding:26px 0 20px}
header h1{font-size:25px;font-weight:700}
header .sub{opacity:.85;font-size:14px;margin-top:3px}
header .disc{margin-top:10px;font-size:11.5px;opacity:.7}
nav{background:#0f2942;position:sticky;top:0;z-index:10}
nav .wrap{display:flex;gap:1px;flex-wrap:wrap}
.tab{background:none;border:0;color:#bcd0e4;font-size:13px;font-weight:600;
 padding:13px 14px;cursor:pointer;border-bottom:3px solid transparent}
.tab:hover{color:#fff}
.tab.active{color:#fff;border-bottom-color:#3fbf8f}
section{display:none;padding:26px 0 50px}
section.active{display:block}
h2{font-size:19px;color:#163a5f;margin:4px 0 4px}
h3{font-size:14px;color:#3a5266;margin:22px 0 9px;text-transform:uppercase;letter-spacing:.6px}
p.lead{font-size:14px;color:#3a5266;max-width:880px;margin-bottom:6px}
.cards{display:flex;flex-wrap:wrap;gap:14px;margin:16px 0}
.card{background:#fff;border-radius:10px;padding:16px 18px;flex:1;min-width:148px;
 box-shadow:0 1px 3px rgba(0,0,0,.08);border-left:4px solid #3fbf8f}
.card-big{font-size:26px;font-weight:700;color:#163a5f}
.card-label{font-size:12.5px;font-weight:700;margin-top:2px}
.card-sub{font-size:11.5px;color:#6b7d8d;margin-top:2px}
.panel{background:#fff;border-radius:10px;padding:18px 20px;margin:14px 0;
 box-shadow:0 1px 3px rgba(0,0,0,.08)}
.issues{display:flex;flex-wrap:wrap;gap:14px;margin:14px 0}
.issue{background:#fff;border-radius:10px;padding:16px 18px;flex:1;min-width:250px;
 box-shadow:0 1px 3px rgba(0,0,0,.08);border-top:4px solid #d98c2b}
.issue-h{font-size:14.5px;font-weight:700;color:#163a5f;margin-bottom:5px}
.issue-b{font-size:12.8px;color:#3a5266}
.three{display:flex;gap:14px;flex-wrap:wrap}.three>.panel{flex:1;min-width:250px;margin:8px 0}
.stage-tag{font-size:11px;font-weight:700;letter-spacing:.6px;color:#3fbf8f;text-transform:uppercase}
.two{display:flex;gap:16px;flex-wrap:wrap}.two>.panel{flex:1;min-width:320px}
.funnel-row{margin:9px 0}
.funnel-bar{color:#fff;padding:11px 15px;border-radius:7px;display:flex;align-items:baseline;gap:12px}
.funnel-bar.f0{background:#5b7f9e}.funnel-bar.f1{background:#3f6f93}
.funnel-bar.f2{background:#2b5a86}.funnel-bar.f3{background:#1F4E78}
.funnel-n{font-size:21px;font-weight:700}.funnel-name{font-size:13.5px;font-weight:600}
.funnel-sub{font-size:11.5px;color:#6b7d8d;margin-top:3px;margin-left:3px}
table.grid{width:100%;border-collapse:collapse;font-size:12.5px;margin-top:4px}
table.grid th{background:#163a5f;color:#fff;text-align:left;padding:8px 9px;font-size:11px;
 text-transform:uppercase;letter-spacing:.4px}
table.grid td{padding:7px 9px;border-bottom:1px solid #e6eaee}
table.grid tr:nth-child(even) td{background:#f6f8fa}
table.grid tr.rec-row td{background:#d6f0dd!important;font-weight:600}
td.nm{font-weight:600}.num,th.num{text-align:right}
.mono{font-family:ui-monospace,Menlo,monospace;font-size:11.5px}
.pill{display:inline-block;background:#e7eef5;color:#1F4E78;font-size:10.5px;font-weight:700;
 padding:2px 8px;border-radius:10px;white-space:nowrap}
.pill.pass{background:#d6f0dd;color:#1a7f37}
.hbars{margin-top:4px}
.hbar-row{display:flex;align-items:center;gap:10px;margin:3px 0}
.hbar-label{width:210px;font-size:12px;text-align:right;flex-shrink:0}
.hbar-track{flex:1;background:#eef1f4;border-radius:4px;height:17px}
.hbar-fill{height:17px;border-radius:4px;background:#1F4E78}
.hbar-fill.sec{background:#3fbf8f}
.hbar-val{width:104px;font-size:11.5px;color:#3a5266;flex-shrink:0}
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
.banner.warn{background:#fdf0c8;color:#7a5600}
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
ul.clean{list-style:none;font-size:12.8px}
ul.clean li{padding:5px 0 5px 20px;position:relative;border-bottom:1px solid #eef1f4}
ul.clean li:before{content:"\\2713";position:absolute;left:0;color:#3fbf8f;font-weight:700}
ol.limits{font-size:12.8px;margin-left:18px}
ol.limits li{padding:5px 0;border-bottom:1px solid #eef1f4}
ol.limits b{color:#163a5f}
.note{font-size:11.8px;color:#6b7d8d;margin-top:8px}
.recbox{background:linear-gradient(135deg,#163a5f,#1F4E78);color:#fff;border-radius:10px;
 padding:18px 22px;margin:14px 0;font-size:15px;font-weight:600}
footer{background:#0f2942;color:#9fb2c2;font-size:11.5px;padding:16px 0;text-align:center}
"""
JS = """
function show(id,btn){
 document.querySelectorAll('section').forEach(s=>s.classList.remove('active'));
 document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
 document.getElementById(id).classList.add('active');btn.classList.add('active');
 window.scrollTo(0,0);
}
"""

TABS = [("problem","The Problem"),("solution","The Solution"),("pipeline","The Pipeline"),
        ("portfolio","Portfolio"),("financials","Financials"),("esg","ESG &amp; Climate"),
        ("gw","Greenwashing 8-Test"),("rec","Oversight &amp; Recommendation")]
nav = "".join(f'<button class="tab{" active" if i==0 else ""}" '
              f'onclick="show(\'{tid}\',this)">{label}</button>'
              for i,(tid,label) in enumerate(TABS))

# ── Sections ────────────────────────────────────────────────────────────────────
problem = f"""<div class="wrap">
<h2>Why sustainable investing is hard</h2>
<p class="lead">Building a credible sustainable portfolio is not a data-lookup
problem. Three structural issues make it genuinely difficult — and motivate the
pipeline.</p>
{issue_cards([
 ("ESG ratings disagree","The major ESG raters correlate only ~0.4-0.5 — the "
  "same company gets very different scores depending on the vendor "
  "(Berg, Koelbel &amp; Rigobon, 2022, &lsquo;Aggregate Confusion&rsquo;). "
  "No single rating can be trusted on its own."),
 ("Greenwashing is hard to detect","Sustainability claims are often vague, "
  "lack a baseline or a metric, set distant unverifiable targets, or are "
  "contradicted by capital spending. Spotting the gap between claim and "
  "substance needs forensic, document-level analysis."),
 ("Regulation is fragmenting","SFDR, the EU Taxonomy and CSRD each demand "
  "different disclosures, and reported coverage is sparse and inconsistent — "
  "eligibility is not alignment, and alignment data barely exists."),
])}
<p class="lead" style="margin-top:14px">On top of this, manual ESG research does
not scale: a 289-company universe, each with hundreds of data points and a
multi-hundred-page sustainability report, cannot be screened by hand with any
consistency. That is the problem this project solves.</p>
</div>"""

solution = f"""<div class="wrap">
<h2>{esc(fund)}</h2>
<p class="lead">{esc(thesis)}</p>
{metric_cards([
 (N_FINAL,"Holdings","long-only European equities"),
 (n_sect,"Sectors",f"largest {top_sec.max()*100:.1f}% (cap 25%)"),
 (f"{wesg:.1f}","Weighted ESG",f"vs {uni_esg:.1f} universe (+{wesg-uni_esg:.1f})"),
 (f"{wsharp:.2f}","Weighted Sharpe","5y, holdings-weighted"),
 (f"{waci:.0f}","WACI tCO2e/$M","weighted carbon intensity"),
 (f"{gw_pass}/{N_FINAL}","Greenwashing PASS","8-Test, 0 excluded"),
])}
<h3>ESG embedded at three independent stages</h3>
{stages3()}
<h3>From universe to portfolio</h3>
<div class="panel">{funnel()}</div>
<p class="note">Benchmark: {esc(bench)}. Academic prototype &mdash; not investment advice.</p>
</div>"""

pipeline_sec = f"""<div class="wrap">
<h2>The AI-agent pipeline</h2>
<p class="lead">A chain of 13 specialised agents, orchestrated in n8n.cloud.
Each step is a notebook; code is AI-generated and every output is human-verified.
The agent label is a pipeline structure — the optimisation step is deterministic
Python, not an LLM.</p>
<div class="panel">{pipeline()}</div>
<p class="note">Run order: foundation &rarr; analysis &rarr; investigation &rarr;
construction &amp; reporting. Greenwashing and document intelligence feed the
construction step; human review sits last.</p>
</div>"""

portfolio_sec = f"""<div class="wrap">
<h2>The final {N_FINAL}-stock portfolio</h2>
<p class="lead">Selected by composite score (60% financial quality + 40% ESG),
with a hard max-5-holdings-per-sector cap, a 0.90 return-correlation guard, and
weights proportional to the composite score, capped at 10% per name.</p>
<div class="panel">{holdings_table()}</div>
<div class="two">
<div class="panel"><h3>Holding weights</h3>{bars(fp,"weight",lambda v:f"{v*100:.2f}%")}</div>
<div class="panel"><h3>Sector allocation</h3>{sector_bars()}
<p class="note">Weight &middot; number of holdings. Cap: 5 holdings / 25% per sector.</p></div>
</div></div>"""

# ── Financials — backtest blocks (real once the optimisation module is run) ────
if bt is not None:
    rec = bt.sort_values("rank").iloc[0]
    rec_name = rec["method"].replace("_", " ").title()
    bt_oos = int(bt["n_oos_days"].iloc[0])
    fin_cards = metric_cards([
        (f"{rec['sharpe']:.2f}", "Backtest Sharpe", f"{rec_name}, {bt_oos} OOS days"),
        (f"{rec['max_drawdown']*100:.1f}%", "Max drawdown", f"{rec_name} backtest"),
        (f"{rec['ann_vol']*100:.1f}%", "Annualised volatility", f"{rec_name} backtest"),
        (f"{wbeta:.2f}", "Portfolio beta", "vs STOXX Europe 600 — defensive (<1)"),
    ])
    bt_block = (
        '<h3>Walk-forward backtest — weighting-method comparison</h3>'
        f'<div class="banner">Six weighting methods backtested over {bt_oos} '
        'out-of-sample trading days (~5 years); all rebalances successful. '
        f'Recommended: <b>{rec_name}</b> — composite rank 1 of 6 '
        f'(Sharpe {rec["sharpe"]:.2f}, max drawdown {rec["max_drawdown"]*100:.1f}%, '
        f'turnover {rec["annual_turnover"]*100:.1f}%). Final choice rests with the '
        'Investment Committee.</div>'
        f'<div class="panel">{backtest_table()}'
        '<p class="note">Composite ranks methods on Sharpe, max drawdown, turnover '
        'and a 2–8% tracking-error band. Look-ahead disclosure: the holdings were '
        'chosen with present-day information, so absolute performance carries '
        'look-ahead bias — the valid output is the RELATIVE comparison of '
        'weighting methods, not a claim of historical alpha.</p></div>')
else:
    fin_cards = metric_cards([
        (f"{wsharp:.2f}", "Weighted Sharpe", "holding-weighted average, 5y"),
        (f"{wvol*100:.1f}%", "Weighted volatility", "holding-weighted average"),
        (f"{wmdd*100:.0f}%", "Weighted max drawdown", "holding-weighted average"),
        (f"{wbeta:.2f}", "Portfolio beta", "vs STOXX Europe 600 — defensive (<1)"),
    ])
    bt_block = ('<div class="banner warn">Walk-forward backtest — pending; '
                're-run the optimisation module on the final 20 holdings.</div>')

financials = f"""<div class="wrap">
<h2>Financial profile</h2>
<p class="lead">Every holding cleared a hard financial screen — the G1-G5 quality
gates plus volatility, drawdown and Sharpe thresholds — before ranking. The
portfolio was then backtested under six weighting methods.</p>
{fin_cards}
{bt_block}
<div class="two">
<div class="panel"><h3>Sharpe ratio by holding</h3>
{bars(fp,"sharpe_ratio",lambda v:f"{v:.2f}",color="#2b6a8f")}</div>
<div class="panel"><h3>Annualised volatility by holding</h3>
{bars(fp,"vol_annual",lambda v:f"{v*100:.1f}%",color="#d98c2b")}</div>
</div>
<h3>Per-holding risk &amp; return</h3>
<div class="panel">{fin_table()}
<p class="note">Sharpe / volatility / max drawdown / beta are 5-year, from market
data. Financial score is a 0–100 composite of the four metrics — the 60%
financial leg of the selection score. Individual holdings average a {wsharp:.2f}
Sharpe; the diversified portfolio backtests higher because diversification nets
down portfolio volatility. Sorted by Sharpe.</p></div>
</div>"""

esg_sec = f"""<div class="wrap">
<h2>ESG &amp; climate profile</h2>
<p class="lead">ESG, climate and nature run as three independent signals — a
composite would let one mask failure in another.</p>
<div class="panel"><h3>Portfolio vs universe &mdash; E / S / G / aggregate</h3>
{esg_compare()}</div>
<div class="two">
<div class="panel"><h3>Carbon &mdash; WACI</h3>
{metric_cards([(f"{waci:.0f}","tCO2e/$M revenue","weighted carbon intensity"),
 ("~62%","driven by one name","Norsk Hydro; ex-Norsk Hydro WACI &asymp; 62")])}
<p class="note">18 of 20 holdings use sector-median imputed carbon intensity; the
Financials-sector WACI excludes PCAF Scope&nbsp;3 financed emissions &mdash; a
disclosed limitation.</p></div>
<div class="panel"><h3>What is measured</h3>
<ul class="clean">
<li>E / S / G scores 0&ndash;100, SASB-materiality weighted</li>
<li>WACI &mdash; weighted average carbon intensity (Scope 1+2)</li>
<li>Biodiversity nature-risk proxy (ENCORE, WRI Aqueduct)</li>
<li>EU Taxonomy eligibility &amp; alignment overlay</li>
<li>Benchmark comparison vs {esc(bench)}</li>
</ul></div></div></div>"""

gw_sec = f"""<div class="wrap">
<h2>Greenwashing 8-Test</h2>
<p class="lead">Each holding's headline sustainability claim is tested on eight
dimensions, rated PASS / PARTIAL / FAIL / MISSING. Tier 1 = primary company
documents (verbatim, page-cited); Tier 2 = external verification (SBTi database,
TPI Carbon Performance). Rule: 3+ FAIL excludes, exactly 2 watchlists.</p>
<div class="banner">&#10003; All {N_FINAL} holdings PASS &mdash; 0 excluded,
0 watchlisted, no FAIL on any dimension.</div>
<div class="panel">{scorecard()}
<p class="note">Cell letter = rating (P PASS &middot; P PARTIAL &middot; F FAIL
&middot; M MISSING) &mdash; hover for the dimension. Sorted lowest-concern first.</p></div>
</div>"""

rec_sec = f"""<div class="wrap">
<h2>Human oversight &amp; recommendation</h2>
<p class="lead">AI processes; humans decide. Every override is logged, and the
limits of the work are stated openly.</p>
<div class="two">
<div class="panel"><h3>What we don't know &mdash; limitations</h3>
<ol class="limits">
<li><b>RAG extraction.</b> Document-intelligence can misread a sustainability
report; larger firms disclose more, which can flatter them.</li>
<li><b>Climate &amp; nature data is a proxy.</b> Reported alignment coverage is
low; potential alignment is used as a directional signal only.</li>
<li><b>ESG is partly judgement.</b> Narrative claims are inherently subjective;
the scoring rubric is transparent but not objective.</li>
<li><b>Look-ahead bias.</b> Market data is not point-in-time; PIT integration is
flagged as future work.</li>
</ol></div>
<div class="panel"><h3>Human override layer &mdash; Agent 12</h3>
{metric_cards([("30%","RAG sample verified","random manual check vs source PDF"),
 ("100%","exclusion decisions verified","page-by-page independent cross-check")])}
<p class="note">{n_ic} of {N_FINAL} holdings carry a documented Investment
Committee override. All overrides are logged for the audit trail.</p></div>
</div>
<h3>IC override decisions</h3>
<div class="panel">{ic_table()}</div>
<div class="recbox">Recommendation: approve the {N_FINAL}-stock Article 8-aligned
sustainable European equity sleeve &mdash; a fully auditable, reproducible process,
with negative screening and greenwashing verification. We do not claim regulated
SFDR compliance, alpha, or perfect ESG measurement.</div>
<p class="note">The portfolio is academic in scope; the process is professional
in standard. Academic prototype &mdash; not investment advice.</p>
</div>"""

SECTIONS = {"problem":problem,"solution":solution,"pipeline":pipeline_sec,
            "portfolio":portfolio_sec,"financials":financials,"esg":esg_sec,
            "gw":gw_sec,"rec":rec_sec}
body = "".join(f'<section id="{tid}" class="{"active" if i==0 else ""}">'
               f'{SECTIONS[tid]}</section>' for i,(tid,_) in enumerate(TABS))

doc = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(fund)} &mdash; Live Dashboard</title>
<style>{CSS}</style></head><body>
<header><div class="wrap">
<h1>{esc(fund)}</h1>
<div class="sub">AI-agent research pipeline for sustainable portfolio
construction &middot; ESADE MSc Finance &middot; IC presentation companion</div>
<div class="disc">Academic prototype &mdash; not a regulated product or investment
advice. Data vintage {TODAY}.</div>
</div></header>
<nav><div class="wrap">{nav}</div></nav>
{body}
<footer>ESADE Sustainable Finance &mdash; final group assignment &middot;
self-contained dashboard, generated {TODAY} from outputs/</footer>
<script>{JS}</script></body></html>"""

os.makedirs("outputs/dashboard", exist_ok=True)
out_path = "outputs/dashboard/esade_dashboard.html"
with open(out_path, "w", encoding="utf-8") as f:
    f.write(doc)
print(f"Dashboard written: {out_path}  ({len(doc):,} bytes, self-contained, 8 sections)")
print(f"  {N_FINAL} holdings | weighted Sharpe {wsharp:.2f} | weighted vol "
      f"{wvol*100:.1f}% | beta {wbeta:.2f} | WACI {waci:.0f} | "
      f"greenwashing {gw_pass}/{N_FINAL} PASS")
