"""
Generates: notebooks/04b_fundamental_quality.ipynb

A 6-metric financial-quality screening agent implementing the framework
documented in docs/financial_filtering_framework/ (Version 2 — six metrics).

The notebook scores companies on:
    M-01 ROIC – WACC Spread          22%
    M-02 FCF Conversion Rate         22%
    M-03 FCCR + Net Debt / EBITDA    18%
    M-04 Sloan Accruals Ratio        13%
    M-05 EBITDA Margin CV            13%
    M-06 Dividend Sustainability     12%

Plus a Layer-1 binary pre-screen (dividend cuts > 2 in last 5 years → hard exclude).

Output: outputs/scores/fundamental_quality_YYYY-MM-DD.csv
"""

import nbformat as nbf
import os

NB_PATH = r"C:\Users\ionva\Desktop\Sustainable Finance Project\notebooks\04b_fundamental_quality.ipynb"

nb = nbf.v4.new_notebook()
cells = []

# ── Cell 0: title ─────────────────────────────────────────────────────────────
cells.append(nbf.v4.new_markdown_cell("""# Notebook 04b — Fundamental Quality Screen (6-Metric Framework)

**Agent:** Financial Quality Filter — Version 2 (M-01 to M-06)
**Source documents:** `docs/financial_filtering_framework/` (financial_filtering_agent copy.html, version 2.pdf)
**Purpose:** Complement the price-based screen in `04_financial_analysis.ipynb` with accounting-based fundamental quality signals.

---

## The 6 metrics

| Metric | Pillar | Weight |
|--------|--------|--------|
| **M-01** ROIC – WACC Spread | Capital efficiency | 22% |
| **M-02** FCF Conversion Rate (FCF/EBITDA + FCF/Net Income) | Cash quality | 22% |
| **M-03** FCCR + Net Debt / EBITDA | Balance-sheet stability | 18% |
| **M-04** Sloan Accruals Ratio | Earnings quality | 13% |
| **M-05** EBITDA Margin CV | Margin resilience | 13% |
| **M-06** Dividend Sustainability Index | Income reliability | 12% |
| **Total** | | **100%** |

### Layer-1 binary pre-screen
Companies with more than 2 dividend cuts in the observation window are excluded before scoring, regardless of how well they score on M-01 to M-05.

---

## Data source

This notebook fetches fundamentals via **yfinance** (`Ticker.financials`, `.cashflow`, `.balance_sheet`). yfinance typically provides 4–5 years of annual data — sufficient for the 5-year median checks the framework requires, with the caveat that the 10-year dividend-cut count is approximated using the available 5-year window.

## Output

`outputs/scores/fundamental_quality_YYYY-MM-DD.csv` — one row per ticker with all six metric scores (0–100), the weighted composite, hard-floor pass/fail flags, and the Layer-1 binary pre-screen result.
"""))

# ── Cell 1: imports + config ──────────────────────────────────────────────────
cells.append(nbf.v4.new_code_cell("""import os, sys, json, time, warnings
from datetime import date
from pathlib import Path
import numpy as np
import pandas as pd
import yfinance as yf

warnings.filterwarnings("ignore")
pd.set_option("display.max_columns", 60)

ROOT = Path(r"C:\\\\Users\\\\ionva\\\\Desktop\\\\Sustainable Finance Project")
SCORES_DIR = ROOT / "outputs" / "scores"
PORTFOLIO_DIR = ROOT / "outputs" / "portfolio"
CACHE_DIR = ROOT / "data" / "market" / "fundamentals_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

VINTAGE = str(date.today())
print(f"Vintage: {VINTAGE}")
print(f"Scores out: {SCORES_DIR}")
print(f"Cache:     {CACHE_DIR}")"""))

# ── Cell 2: universe scope ────────────────────────────────────────────────────
cells.append(nbf.v4.new_markdown_cell("""## Step 1 — Define universe scope

The 6-metric screen runs against a configurable universe. Default: **portfolio + Deep Review companies** (~40 names) — tractable for yfinance fetches in a few minutes. Set `UNIVERSE_SCOPE = 'all'` to run against the full 167-company universe (10–15 minutes)."""))

cells.append(nbf.v4.new_code_cell("""# ── Universe scope ──────────────────────────────────────────────
# Options: 'portfolio'   — final 20 holdings only
#          'deep_review' — 20 holdings + 20 next-rank candidates
#          'all'         — full 167-company universe
UNIVERSE_SCOPE = "deep_review"

# Load tickers
master = pd.read_csv(SCORES_DIR / "master_dataset_2026-05-12.csv",
                     usecols=["ticker", "yf_ticker", "idBbGlobalCompanyName",
                              "classificationLevelName1"])
master = master.rename(columns={"classificationLevelName1": "bics_sector"})

portfolio = pd.read_csv(PORTFOLIO_DIR / "final_portfolio_2026-05-14.csv",
                        usecols=["ticker"])

if UNIVERSE_SCOPE == "portfolio":
    tickers = portfolio["ticker"].tolist()
elif UNIVERSE_SCOPE == "deep_review":
    # 20 portfolio holdings + next 20 by ESG_score (among non-portfolio)
    portfolio_tickers = portfolio["ticker"].tolist()
    universe_scores = pd.read_csv(PORTFOLIO_DIR / "universe_scores_2026-05-14.csv")
    near_misses = (universe_scores[~universe_scores["ticker"].isin(portfolio_tickers)]
                   .sort_values("ESG_score", ascending=False)
                   .head(20)["ticker"].tolist())
    tickers = portfolio_tickers + near_misses
else:
    tickers = master["ticker"].tolist()

# Filter master to selected tickers, with yf_ticker bridge
universe = master[master["ticker"].isin(tickers)].copy()
universe = universe.dropna(subset=["yf_ticker"]).reset_index(drop=True)

print(f"Universe scope: {UNIVERSE_SCOPE}")
print(f"Tickers selected: {len(universe)}")
universe.head(10)"""))

# ── Cell 3: sector WACC constants ─────────────────────────────────────────────
cells.append(nbf.v4.new_markdown_cell("""## Step 2 — Sector WACC estimates

WACC by sector cannot be computed from yfinance for individual companies (would need detailed capital-structure data + risk-free rate + equity risk premium per market). Instead, we use **Damodaran-style sector-level estimates for Western Europe**, calibrated to early-2026 rate environment.

Hard floor (M-01): 5-year median ROIC – sector WACC > 0%. Hard fail if the sector spread is non-positive."""))

cells.append(nbf.v4.new_code_cell("""# Sector WACC estimates (Damodaran-aligned, Western Europe 2026)
SECTOR_WACC = {
    "Energy":                 0.085,
    "Materials":              0.085,
    "Industrials":            0.080,
    "Consumer Discretionary": 0.085,
    "Consumer Staples":       0.070,
    "Health Care":            0.075,
    "Financials":             0.075,
    "Technology":             0.095,
    "Communications":         0.080,
    "Utilities":              0.065,
    "Real Estate":            0.070,
    "Communication Services": 0.080,
}
DEFAULT_WACC = 0.080
print("Sector WACC table loaded.")
for k, v in SECTOR_WACC.items():
    print(f"  {k:25s}  {v*100:.1f}%")"""))

# ── Cell 4: fetcher with caching ──────────────────────────────────────────────
cells.append(nbf.v4.new_markdown_cell("""## Step 3 — Fetch financial statements via yfinance

For each ticker we pull three statements:
- **Income statement** (`.financials`) — Revenue, EBITDA, EBIT, Net Income, Interest Expense
- **Cash flow** (`.cashflow`) — Free Cash Flow, Capital Expenditure, Cash Dividends Paid, Repurchases, Cash Taxes
- **Balance sheet** (`.balance_sheet`) — Total Assets, Total Debt, Cash, Invested Capital, Total Liabilities

Results are cached to a parquet file per ticker so re-runs are instant."""))

cells.append(nbf.v4.new_code_cell("""def fetch_fundamentals(yf_ticker, force_refresh=False):
    \"\"\"Fetch + cache financials, cashflow, balance_sheet for one ticker.
       Returns dict of three DataFrames (or None for any that failed).\"\"\"
    safe_name = yf_ticker.replace(".", "_").replace("/", "_")
    cache_paths = {
        "fin":  CACHE_DIR / f"{safe_name}__fin.parquet",
        "cf":   CACHE_DIR / f"{safe_name}__cf.parquet",
        "bs":   CACHE_DIR / f"{safe_name}__bs.parquet",
    }
    out = {}
    if not force_refresh and all(p.exists() for p in cache_paths.values()):
        try:
            for k, p in cache_paths.items():
                out[k] = pd.read_parquet(p)
            return out
        except Exception:
            pass  # fall through to refetch

    try:
        t = yf.Ticker(yf_ticker)
        for key, getter in [("fin", lambda: t.financials),
                            ("cf",  lambda: t.cashflow),
                            ("bs",  lambda: t.balance_sheet)]:
            try:
                df = getter()
                if df is None or df.empty:
                    out[key] = None
                else:
                    df.columns = [pd.to_datetime(c) for c in df.columns]
                    df.to_parquet(cache_paths[key])
                    out[key] = df
            except Exception as e:
                out[key] = None
    except Exception as e:
        out = {"fin": None, "cf": None, "bs": None}
    return out

def safe_row(df, row_name):
    \"\"\"Return a numeric Series for row_name if present, else empty Series.\"\"\"
    if df is None or row_name not in df.index:
        return pd.Series(dtype=float)
    s = pd.to_numeric(df.loc[row_name], errors="coerce")
    return s.dropna()

print("Fetcher ready.")"""))

# ── Cell 5: fetch loop ────────────────────────────────────────────────────────
cells.append(nbf.v4.new_code_cell("""# Pull data for every ticker in universe (may take 2–10 minutes depending on scope)
results = {}
errors = []

print(f"Fetching fundamentals for {len(universe)} companies...")
for i, row in universe.iterrows():
    yt = row["yf_ticker"]
    try:
        results[row["ticker"]] = fetch_fundamentals(yt)
        if (i + 1) % 10 == 0:
            print(f"  [{i+1}/{len(universe)}] fetched")
    except Exception as e:
        errors.append((row["ticker"], yt, str(e)))
        results[row["ticker"]] = {"fin": None, "cf": None, "bs": None}

print(f"\\nDone. Fetched: {len(results)}. Errors: {len(errors)}.")"""))

# ── Cell 6: M-01 ──────────────────────────────────────────────────────────────
cells.append(nbf.v4.new_markdown_cell("""## Step 4 — M-01: ROIC – WACC Spread (22%)

**Formula:**
```
ROIC  =  NOPAT / Invested Capital
NOPAT ≈ EBIT × (1 − effective_tax_rate)
Spread = ROIC_5yr_median − sector_WACC
```

**Hard floors:**
- 5-year median spread > 0%
- Minimum ROIC > 8%
- ≤ 1 year of negative spread out of 5

If `EBIT` is unavailable, we fall back to `EBITDA × 0.85` as a coarse proxy.
If `Invested Capital` is unavailable, we use `Stockholders Equity + Total Debt`.
Tax rate defaults to **25%** if `Tax Rate For Calcs` row absent."""))

cells.append(nbf.v4.new_code_cell("""def compute_m01(ticker, sector, bundle):
    fin, bs = bundle["fin"], bundle["bs"]
    ebit = safe_row(fin, "EBIT")
    if ebit.empty:
        ebitda = safe_row(fin, "EBITDA")
        ebit = ebitda * 0.85   # coarse proxy
    tax_rate = safe_row(fin, "Tax Rate For Calcs")
    if tax_rate.empty:
        tax_rate = pd.Series([0.25] * len(ebit), index=ebit.index)
    tax_rate = tax_rate.clip(lower=0, upper=0.5)

    invested_cap = safe_row(bs, "Invested Capital")
    if invested_cap.empty:
        eq = safe_row(bs, "Stockholders Equity")
        debt = safe_row(bs, "Total Debt")
        invested_cap = (eq + debt).dropna()

    # align indices
    idx = ebit.index.intersection(invested_cap.index).intersection(tax_rate.index)
    if len(idx) < 3:
        return {"m01_roic_med": np.nan, "m01_wacc": np.nan, "m01_spread": np.nan,
                "m01_neg_years": np.nan, "m01_hard_pass": False}
    ebit_a = ebit.loc[idx]
    tax_a  = tax_rate.loc[idx]
    inv_a  = invested_cap.loc[idx]
    nopat  = ebit_a * (1 - tax_a)
    roic   = (nopat / inv_a).replace([np.inf, -np.inf], np.nan).dropna()
    if len(roic) < 3:
        return {"m01_roic_med": np.nan, "m01_wacc": np.nan, "m01_spread": np.nan,
                "m01_neg_years": np.nan, "m01_hard_pass": False}
    wacc = SECTOR_WACC.get(sector, DEFAULT_WACC)
    roic_med = roic.median()
    spread   = roic_med - wacc
    neg_years = int((roic - wacc < 0).sum())
    hard_pass = (spread > 0) and (roic_med > 0.08) and (neg_years <= 1)
    return {"m01_roic_med": roic_med, "m01_wacc": wacc, "m01_spread": spread,
            "m01_neg_years": neg_years, "m01_hard_pass": bool(hard_pass)}

# quick smoke test on first ticker
demo = next(iter(results))
sector_demo = universe[universe["ticker"]==demo]["bics_sector"].iloc[0]
print(f"M-01 test on {demo} ({sector_demo}):")
print(compute_m01(demo, sector_demo, results[demo]))"""))

# ── Cell 7: M-02 ──────────────────────────────────────────────────────────────
cells.append(nbf.v4.new_markdown_cell("""## Step 5 — M-02: FCF Conversion (22%)

**Dual-signal:**
- **Signal A:** 5-year median FCF/EBITDA ≥ 45%
- **Signal B:** 5-year median FCF/Net Income ≥ 80%

Both gates must pass. If Signal B fails, an accrual flag is raised that is cross-checked against M-04 in the composite calculation."""))

cells.append(nbf.v4.new_code_cell("""def compute_m02(ticker, bundle):
    fin, cf = bundle["fin"], bundle["cf"]
    fcf = safe_row(cf, "Free Cash Flow")
    ebitda = safe_row(fin, "EBITDA")
    ni     = safe_row(fin, "Net Income")
    if fcf.empty or ebitda.empty:
        return {"m02_fcf_ebitda": np.nan, "m02_fcf_ni": np.nan,
                "m02_signal_a": False, "m02_signal_b": False,
                "m02_accrual_flag": False, "m02_hard_pass": False}
    idx_a = fcf.index.intersection(ebitda.index)
    idx_b = fcf.index.intersection(ni.index)
    sig_a = (fcf.loc[idx_a] / ebitda.loc[idx_a]).replace([np.inf,-np.inf], np.nan).dropna()
    sig_b = (fcf.loc[idx_b] / ni.loc[idx_b]).replace([np.inf,-np.inf], np.nan).dropna()
    if len(sig_a) < 3 or len(sig_b) < 3:
        return {"m02_fcf_ebitda": np.nan, "m02_fcf_ni": np.nan,
                "m02_signal_a": False, "m02_signal_b": False,
                "m02_accrual_flag": False, "m02_hard_pass": False}
    med_a = sig_a.median()
    med_b = sig_b.median()
    pass_a = med_a >= 0.45
    pass_b = med_b >= 0.80
    accrual_flag = not pass_b   # signal B failure ⇒ check M-04
    return {"m02_fcf_ebitda": med_a, "m02_fcf_ni": med_b,
            "m02_signal_a": bool(pass_a), "m02_signal_b": bool(pass_b),
            "m02_accrual_flag": bool(accrual_flag),
            "m02_hard_pass": bool(pass_a and pass_b)}

print(f"M-02 test on {demo}: {compute_m02(demo, results[demo])}")"""))

# ── Cell 8: M-03 ──────────────────────────────────────────────────────────────
cells.append(nbf.v4.new_markdown_cell("""## Step 6 — M-03: FCCR + Net Debt/EBITDA (18%)

**FCCR:** `(EBITDA − CapEx − Cash Taxes) / Interest Expense`
**Net Debt/EBITDA:** `(Total Debt − Cash & Equivalents) / EBITDA`

**Hard floors:**
- Trailing FCCR ≥ 2.5×
- 5yr minimum annual FCCR ≥ 1.75×
- Net Debt/EBITDA ≤ 3.0× (≤ 5.0× for Utilities/Real Estate carve-out)

The −20% EBITDA stress test from the source document is computed and reported, but the binary pass uses the base-case FCCR."""))

cells.append(nbf.v4.new_code_cell("""def compute_m03(ticker, sector, bundle):
    fin, cf, bs = bundle["fin"], bundle["cf"], bundle["bs"]
    ebitda    = safe_row(fin, "EBITDA")
    interest  = safe_row(fin, "Interest Expense").abs()
    capex     = safe_row(cf, "Capital Expenditure").abs()
    cash_tax  = safe_row(cf, "Income Tax Paid Supplemental Data").abs()
    total_debt= safe_row(bs, "Total Debt")
    cash      = safe_row(bs, "Cash And Cash Equivalents")
    if ebitda.empty or interest.empty:
        return {"m03_fccr_trailing": np.nan, "m03_fccr_min": np.nan,
                "m03_fccr_stress": np.nan, "m03_netdebt_ebitda": np.nan,
                "m03_hard_pass": False}
    idx = ebitda.index.intersection(interest.index)
    if capex.empty: capex = pd.Series(0.0, index=idx)
    if cash_tax.empty: cash_tax = pd.Series(0.0, index=idx)
    idx2 = idx.intersection(capex.index).intersection(cash_tax.index)
    if len(idx2) < 3:
        return {"m03_fccr_trailing": np.nan, "m03_fccr_min": np.nan,
                "m03_fccr_stress": np.nan, "m03_netdebt_ebitda": np.nan,
                "m03_hard_pass": False}
    num = ebitda.loc[idx2] - capex.loc[idx2] - cash_tax.loc[idx2]
    fccr = (num / interest.loc[idx2]).replace([np.inf,-np.inf], np.nan).dropna()
    if fccr.empty:
        return {"m03_fccr_trailing": np.nan, "m03_fccr_min": np.nan,
                "m03_fccr_stress": np.nan, "m03_netdebt_ebitda": np.nan,
                "m03_hard_pass": False}
    fccr_trailing = float(fccr.iloc[0]) if not fccr.empty else np.nan
    fccr_min      = float(fccr.min())
    stress_num    = ebitda.loc[idx2] * 0.80 - capex.loc[idx2] - cash_tax.loc[idx2]
    fccr_stress   = float((stress_num / interest.loc[idx2]).replace([np.inf,-np.inf], np.nan).dropna().median())

    # Net Debt / EBITDA
    idx_nd = total_debt.index.intersection(ebitda.index)
    if cash.empty:
        cash = pd.Series(0.0, index=idx_nd)
    idx_nd = idx_nd.intersection(cash.index)
    if len(idx_nd) >= 1:
        net_debt_ebitda = float(((total_debt.loc[idx_nd] - cash.loc[idx_nd]) / ebitda.loc[idx_nd]).iloc[0])
    else:
        net_debt_ebitda = np.nan

    nd_ceiling = 5.0 if sector in ("Utilities", "Real Estate") else 3.0
    hard_pass = (
        not np.isnan(fccr_trailing) and fccr_trailing >= 2.5 and
        not np.isnan(fccr_min)      and fccr_min >= 1.75 and
        (np.isnan(net_debt_ebitda)   or net_debt_ebitda <= nd_ceiling)
    )
    return {"m03_fccr_trailing": fccr_trailing, "m03_fccr_min": fccr_min,
            "m03_fccr_stress": fccr_stress, "m03_netdebt_ebitda": net_debt_ebitda,
            "m03_hard_pass": bool(hard_pass)}

print(f"M-03 test on {demo}: {compute_m03(demo, sector_demo, results[demo])}")"""))

# ── Cell 9: M-04 ──────────────────────────────────────────────────────────────
cells.append(nbf.v4.new_markdown_cell("""## Step 7 — M-04: Sloan Accruals Ratio (13%)

**Balance-sheet method (Sloan 1996):**
```
NOA  =  (Total Assets − Cash) − (Total Liabilities − Total Debt)
Sloan Accruals = ΔNOA / Average Total Assets
```

**Scoring:**
- 5yr avg accruals < −2% → 100 pts (very conservative accounting)
- 5yr avg ≈ 2–5% → 50 pts (neutral)
- 5yr avg > 8% → 0 pts (aggressive accruals)

Cross-flag with M-02 Signal B: a company failing both is sent to mandatory analytical review."""))

cells.append(nbf.v4.new_code_cell("""def compute_m04(ticker, bundle):
    bs = bundle["bs"]
    total_assets = safe_row(bs, "Total Assets")
    cash = safe_row(bs, "Cash And Cash Equivalents")
    total_liab = safe_row(bs, "Total Liabilities Net Minority Interest")
    total_debt = safe_row(bs, "Total Debt")
    if total_assets.empty or total_liab.empty:
        return {"m04_sloan_avg": np.nan, "m04_score_pts": np.nan, "m04_hard_pass": False}
    idx = total_assets.index.intersection(total_liab.index)
    if cash.empty: cash = pd.Series(0.0, index=idx)
    if total_debt.empty: total_debt = pd.Series(0.0, index=idx)
    idx = idx.intersection(cash.index).intersection(total_debt.index)
    if len(idx) < 3:
        return {"m04_sloan_avg": np.nan, "m04_score_pts": np.nan, "m04_hard_pass": False}
    noa = (total_assets.loc[idx] - cash.loc[idx]) - (total_liab.loc[idx] - total_debt.loc[idx])
    noa = noa.sort_index()
    delta = noa.diff().dropna()
    avg_assets = total_assets.loc[idx].sort_index().rolling(2).mean().dropna()
    common = delta.index.intersection(avg_assets.index)
    accruals = (delta.loc[common] / avg_assets.loc[common]).replace([np.inf,-np.inf], np.nan).dropna()
    if accruals.empty:
        return {"m04_sloan_avg": np.nan, "m04_score_pts": np.nan, "m04_hard_pass": False}
    avg_accr = float(accruals.mean())
    if   avg_accr < -0.02:  pts = 100
    elif avg_accr <  0.02:  pts = 75
    elif avg_accr <  0.05:  pts = 50
    elif avg_accr <  0.08:  pts = 25
    else:                   pts = 0
    hard_pass = avg_accr <= 0.08
    return {"m04_sloan_avg": avg_accr, "m04_score_pts": float(pts),
            "m04_hard_pass": bool(hard_pass)}

print(f"M-04 test on {demo}: {compute_m04(demo, results[demo])}")"""))

# ── Cell 10: M-05 ─────────────────────────────────────────────────────────────
cells.append(nbf.v4.new_markdown_cell("""## Step 8 — M-05: EBITDA Margin CV (13%)

For each available year: `EBITDA_margin = EBITDA / Total Revenue`.
Coefficient of variation: `CV = stdev / mean` over 5 years.

**Hard floor:** CV < 35% (cyclical companies above this threshold are flagged for margin instability).
**Scoring:** lower CV = higher score (linear within the universe by percentile rank)."""))

cells.append(nbf.v4.new_code_cell("""def compute_m05(ticker, bundle):
    fin = bundle["fin"]
    ebitda  = safe_row(fin, "EBITDA")
    revenue = safe_row(fin, "Total Revenue")
    if ebitda.empty or revenue.empty:
        return {"m05_ebitda_margin_mean": np.nan, "m05_cv": np.nan, "m05_hard_pass": False}
    idx = ebitda.index.intersection(revenue.index)
    if len(idx) < 3:
        return {"m05_ebitda_margin_mean": np.nan, "m05_cv": np.nan, "m05_hard_pass": False}
    margins = (ebitda.loc[idx] / revenue.loc[idx]).replace([np.inf,-np.inf], np.nan).dropna()
    if len(margins) < 3 or margins.mean() == 0:
        return {"m05_ebitda_margin_mean": np.nan, "m05_cv": np.nan, "m05_hard_pass": False}
    mean = float(margins.mean())
    cv   = float(margins.std() / abs(mean))
    hard_pass = cv < 0.35
    return {"m05_ebitda_margin_mean": mean, "m05_cv": cv, "m05_hard_pass": bool(hard_pass)}

print(f"M-05 test on {demo}: {compute_m05(demo, results[demo])}")"""))

# ── Cell 11: M-06 + Layer-1 ───────────────────────────────────────────────────
cells.append(nbf.v4.new_markdown_cell("""## Step 9 — M-06: Dividend Sustainability Index (12%) + Layer-1 Pre-Screen

**Three sub-signals:**
1. **FCF Dividend Cover (50% of M-06)** — `FCF / |Dividends Paid|`, target ≥ 2× sustained
2. **Dividend Continuity (35%)** — % of years dividend ≥ prior year (over available 5-year window)
3. **Payout Discipline (15%)** — `(|Dividends| + |Buybacks|) / FCF`, target 40–75% range

**Layer-1 binary pre-screen:** Companies with more than 2 dividend cuts (year-over-year drop > 5%) in the observation window are hard-excluded regardless of other metric scores.

Companies that paid no dividends in any year (e.g. ASML, Argenx) receive M-06 = NaN and are *not* excluded by Layer-1 — the framework distinguishes 'unable to pay' from 'chose not to pay'."""))

cells.append(nbf.v4.new_code_cell("""def compute_m06(ticker, bundle):
    cf = bundle["cf"]
    div = safe_row(cf, "Cash Dividends Paid")
    if div.empty:
        div = safe_row(cf, "Common Stock Dividend Paid")
    fcf = safe_row(cf, "Free Cash Flow")
    buyback = safe_row(cf, "Repurchase Of Capital Stock")

    # No dividends ever ⇒ growth compounder, exempt from M-06 scoring
    if div.empty or (div.abs().sum() == 0):
        return {"m06_pays_dividend": False, "m06_fcf_cover": np.nan,
                "m06_continuity_pct": np.nan, "m06_payout": np.nan,
                "m06_cuts": 0, "m06_layer1_pass": True, "m06_score_pts": np.nan,
                "m06_hard_pass": True}

    div_abs = div.abs().sort_index()
    # FCF cover
    if fcf.empty:
        fcf_cover_med = np.nan
    else:
        idx = fcf.index.intersection(div_abs.index)
        fcf_cover_med = float((fcf.loc[idx] / div_abs.loc[idx]).replace([np.inf,-np.inf], np.nan).dropna().median()) if len(idx) >= 1 else np.nan

    # Continuity: % of years div >= prior year (allow 1% tolerance)
    div_series = div_abs.values
    if len(div_series) >= 2:
        years_up = sum(div_series[i] >= div_series[i-1] * 0.99 for i in range(1, len(div_series)))
        continuity_pct = float(years_up / (len(div_series) - 1))
    else:
        continuity_pct = np.nan

    # Dividend cuts (year-over-year drop > 5%)
    if len(div_series) >= 2:
        cuts = sum(div_series[i] < div_series[i-1] * 0.95 for i in range(1, len(div_series)))
    else:
        cuts = 0
    layer1_pass = cuts <= 2

    # Payout discipline
    if fcf.empty:
        payout = np.nan
    else:
        idx_p = fcf.index.intersection(div_abs.index)
        if not buyback.empty:
            idx_p = idx_p.intersection(buyback.index)
            payout_total = (div_abs.loc[idx_p] + buyback.abs().loc[idx_p])
        else:
            payout_total = div_abs.loc[idx_p]
        payout = float((payout_total / fcf.loc[idx_p]).replace([np.inf,-np.inf], np.nan).dropna().median()) if len(idx_p) >= 1 else np.nan

    # Score (0-100): blend the three sub-signals
    def sub_score(value, low, high, lower_better=False):
        if pd.isna(value): return np.nan
        if lower_better:
            if value <= low: return 100
            if value >= high: return 0
            return 100 * (high - value) / (high - low)
        else:
            if value >= high: return 100
            if value <= low: return 0
            return 100 * (value - low) / (high - low)

    s1 = sub_score(fcf_cover_med, low=1.0, high=2.5)            # ≥2× ⇒ 100
    s2 = sub_score(continuity_pct, low=0.5, high=1.0)            # 100% continuous ⇒ 100
    # Payout discipline: target 40-75%. Penalise both ends.
    if pd.isna(payout):
        s3 = np.nan
    else:
        if 0.40 <= payout <= 0.75: s3 = 100
        elif payout < 0.40:        s3 = max(0, 100 * payout / 0.40)
        else:                      s3 = max(0, 100 * (1.5 - payout) / (1.5 - 0.75))
    weights = [(s1, 0.5), (s2, 0.35), (s3, 0.15)]
    valid = [(s, w) for s, w in weights if not pd.isna(s)]
    if valid:
        wsum = sum(w for _, w in valid)
        score_pts = sum(s * w for s, w in valid) / wsum
    else:
        score_pts = np.nan

    hard_pass = layer1_pass and (not pd.isna(score_pts) and score_pts >= 50)
    return {"m06_pays_dividend": True, "m06_fcf_cover": fcf_cover_med,
            "m06_continuity_pct": continuity_pct, "m06_payout": payout,
            "m06_cuts": int(cuts), "m06_layer1_pass": bool(layer1_pass),
            "m06_score_pts": score_pts, "m06_hard_pass": bool(hard_pass)}

print(f"M-06 test on {demo}: {compute_m06(demo, results[demo])}")"""))

# ── Cell 12: aggregate across universe ────────────────────────────────────────
cells.append(nbf.v4.new_markdown_cell("""## Step 10 — Apply all metrics to the universe"""))

cells.append(nbf.v4.new_code_cell("""rows = []
for _, row in universe.iterrows():
    ticker, sector = row["ticker"], row["bics_sector"]
    bundle = results.get(ticker, {"fin": None, "cf": None, "bs": None})
    rec = {
        "ticker": ticker,
        "company": row["idBbGlobalCompanyName"],
        "bics_sector": sector,
        "yf_ticker": row["yf_ticker"],
    }
    rec.update(compute_m01(ticker, sector, bundle))
    rec.update(compute_m02(ticker, bundle))
    rec.update(compute_m03(ticker, sector, bundle))
    rec.update(compute_m04(ticker, bundle))
    rec.update(compute_m05(ticker, bundle))
    rec.update(compute_m06(ticker, bundle))
    rows.append(rec)

scores_df = pd.DataFrame(rows)
print(f"Scored {len(scores_df)} companies. Columns: {len(scores_df.columns)}")
scores_df.head()"""))

# ── Cell 13: percentile-rank scoring (0-100) ──────────────────────────────────
cells.append(nbf.v4.new_markdown_cell("""## Step 11 — Score each metric on 0–100 by percentile rank

The composite uses **percentile rank within the scored universe** to translate each raw metric into a 0–100 score. Higher = better for all metrics (we invert M-05 CV and M-04 accruals since lower is better)."""))

cells.append(nbf.v4.new_code_cell("""def percentile_score(s, ascending=True):
    \"\"\"Percentile rank → 0-100. ascending=True means higher raw value = higher score.\"\"\"
    return s.rank(pct=True, ascending=ascending) * 100

scores_df["m01_score"] = percentile_score(scores_df["m01_spread"], ascending=True)
# M-02: average of two signals (each scored separately)
scores_df["m02_score_a"] = percentile_score(scores_df["m02_fcf_ebitda"], ascending=True)
scores_df["m02_score_b"] = percentile_score(scores_df["m02_fcf_ni"], ascending=True)
scores_df["m02_score"]   = scores_df[["m02_score_a", "m02_score_b"]].mean(axis=1)
# M-03: FCCR higher better, Net Debt/EBITDA lower better — average them
scores_df["m03_score_a"] = percentile_score(scores_df["m03_fccr_trailing"], ascending=True)
scores_df["m03_score_b"] = percentile_score(scores_df["m03_netdebt_ebitda"], ascending=False)
scores_df["m03_score"]   = scores_df[["m03_score_a", "m03_score_b"]].mean(axis=1)
# M-04: lower accruals = higher score → ascending=False
scores_df["m04_score"]   = percentile_score(scores_df["m04_sloan_avg"], ascending=False)
# M-05: lower CV = higher score
scores_df["m05_score"]   = percentile_score(scores_df["m05_cv"], ascending=False)
# M-06: already 0-100 from sub-signal scoring
scores_df["m06_score"]   = scores_df["m06_score_pts"]

scores_df[["ticker","m01_score","m02_score","m03_score","m04_score","m05_score","m06_score"]].head(10)"""))

# ── Cell 14: composite + redistribution ───────────────────────────────────────
cells.append(nbf.v4.new_markdown_cell("""## Step 12 — Weighted composite (with graceful degradation)

Composite = Σ ( weight × metric_score ) for the **available** metrics, with weights renormalised when any metric is NaN. Companies with fewer than 3 valid metric scores receive `composite = NaN` and `data_quality_flag = INSUFFICIENT`."""))

cells.append(nbf.v4.new_code_cell("""WEIGHTS = {"m01_score": 0.22, "m02_score": 0.22, "m03_score": 0.18,
           "m04_score": 0.13, "m05_score": 0.13, "m06_score": 0.12}

def weighted_composite(row):
    pairs = [(row[m], w) for m, w in WEIGHTS.items() if pd.notna(row[m])]
    if len(pairs) < 3:
        return np.nan, len(pairs), "INSUFFICIENT"
    total_w = sum(w for _, w in pairs)
    composite = sum(s * w for s, w in pairs) / total_w
    quality = "FULL" if len(pairs) == 6 else "PARTIAL"
    return composite, len(pairs), quality

scores_df[["composite", "metrics_available", "data_quality_flag"]] = scores_df.apply(
    lambda r: pd.Series(weighted_composite(r)), axis=1
)

# Layer-1 hard-exclude flag
scores_df["layer1_excluded"] = ~scores_df["m06_layer1_pass"].fillna(True)

# Hard-floor summary: how many of the 6 hard_pass flags did each company pass?
hp_cols = ["m01_hard_pass","m02_hard_pass","m03_hard_pass",
           "m04_hard_pass","m05_hard_pass","m06_hard_pass"]
scores_df["hard_floors_passed"] = scores_df[hp_cols].sum(axis=1)
scores_df["all_hard_floors_passed"] = scores_df[hp_cols].all(axis=1)

scores_df[["ticker","company","bics_sector","composite",
           "metrics_available","data_quality_flag",
           "hard_floors_passed","layer1_excluded"]].sort_values("composite", ascending=False).head(15)"""))

# ── Cell 15: diagnostics ──────────────────────────────────────────────────────
cells.append(nbf.v4.new_markdown_cell("""## Step 13 — Diagnostics"""))

cells.append(nbf.v4.new_code_cell("""print("=== Data coverage by metric ===")
for m in ["m01","m02","m03","m04","m05","m06"]:
    col = f"{m}_score"
    n = scores_df[col].notna().sum()
    print(f"  {m.upper()}: {n}/{len(scores_df)} ({n/len(scores_df)*100:.0f}%)")

print("\\n=== Hard-floor pass rate ===")
for hp in hp_cols:
    n = scores_df[hp].sum()
    print(f"  {hp:20s}: {n}/{len(scores_df)} ({n/len(scores_df)*100:.0f}%)")

print(f"\\nAll-six hard floors passed: {scores_df['all_hard_floors_passed'].sum()} of {len(scores_df)}")
print(f"Layer-1 excluded (dividend cuts > 2): {scores_df['layer1_excluded'].sum()}")
print(f"Composite NaN (INSUFFICIENT data): {scores_df['data_quality_flag'].eq('INSUFFICIENT').sum()}")
print(f"\\nComposite distribution:")
print(scores_df['composite'].describe())"""))

# ── Cell 16: save ─────────────────────────────────────────────────────────────
cells.append(nbf.v4.new_markdown_cell("""## Step 14 — Save outputs"""))

cells.append(nbf.v4.new_code_cell("""out_path = SCORES_DIR / f"fundamental_quality_{VINTAGE}.csv"
scores_df["data_vintage_fundq"] = VINTAGE
scores_df.to_csv(out_path, index=False)
print(f"Saved: {out_path}")
print(f"Rows: {len(scores_df)}  Columns: {len(scores_df.columns)}")"""))

# ── Cell 17: complete ─────────────────────────────────────────────────────────
cells.append(nbf.v4.new_markdown_cell("""## Notebook complete

**Output:** `outputs/scores/fundamental_quality_YYYY-MM-DD.csv`

**Downstream usage:** the resulting composite score can be incorporated as an additional ranking input in `10_portfolio_construction.ipynb`, either:
- as a **qualitative override layer** (only override decisions flagged at human review), or
- as a **scored input** in the composite formula alongside ESG, Sharpe, Biodiversity, EU (would require re-weighting the composite to make room for a fundamental quality component).

**Decision on integration** is documented in the override log (`Appendix E` of the report). In the current build, the 6-metric framework is reported as Screen B in Section 4.2 of the report and used qualitatively, not as an automated exclusion filter."""))

# ── assemble ──────────────────────────────────────────────────────────────────
nb["cells"] = cells
nb.metadata = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python", "version": "3.11"},
}

os.makedirs(os.path.dirname(NB_PATH), exist_ok=True)
with open(NB_PATH, "w", encoding="utf-8") as f:
    nbf.write(nb, f)

print(f"Wrote {NB_PATH}  ({len(cells)} cells)")
