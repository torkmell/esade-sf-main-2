"""
calculate_market_metrics_template.py
--------------------------------------
Reads raw price data from /data/financial/raw_prices/ and benchmark data from
/data/financial/raw_benchmark/, then calculates market-based financial metrics.

Outputs:
  /data/financial/calculated_metrics/market_metrics.csv

Metrics calculated:
  - 1Y total return
  - 3Y annualised return
  - 5Y annualised return
  - Annualised volatility (std of log returns * sqrt(252))
  - Maximum drawdown
  - Sharpe ratio (rf = 2.5% ECB proxy, daily excess returns method)
  - Beta vs STOXX Europe 600 (OLS in-house; NOT info['beta'])

Benchmark note:
  NB04 (04_financial_analysis.ipynb) downloads live from yfinance:
    yf.Ticker("^STOXX").history(period="5y")['Close']  (EXW1.DE as fallback)
  This standalone script reads from pre-cached benchmark CSVs instead.
  Ensure cached benchmark was generated from ^STOXX (not EXW1.DE) for
  consistency with NB04 beta calculations.

Dependencies:
  pip install pandas numpy

Run manually only — do NOT execute automatically.
"""

import os
import glob
import numpy as np
import pandas as pd
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

RAW_PRICES_DIR     = os.path.join(ROOT, "data", "financial", "raw_prices")
RAW_BENCHMARK_DIR  = os.path.join(ROOT, "data", "financial", "raw_benchmark")
OUTPUT_DIR         = os.path.join(ROOT, "data", "financial", "calculated_metrics")
os.makedirs(OUTPUT_DIR, exist_ok=True)

TODAY = date.today().isoformat()
RISK_FREE_RATE = 0.025  # 2.5% — ECB deposit facility rate approximation (2024–2025)
                         # Hard-coded per methodology document. Update annually in audit log.
TRADING_DAYS   = 252    # assumption: 252 trading days per year

# Preferred benchmark is ^STOXX (STOXX Europe 600 index direct feed).
# EXW1.DE (ETF proxy) is retained as fallback only.
BENCHMARK_PRIMARY  = "^STOXX"
BENCHMARK_FALLBACK = "EXW1.DE"

# ── Load most recent price file ───────────────────────────────────────────────
price_files = sorted(glob.glob(os.path.join(RAW_PRICES_DIR, "raw_prices_*.csv")))
if not price_files:
    raise FileNotFoundError(
        f"No raw price files found in {RAW_PRICES_DIR}. "
        "Run fetch_price_data_template.py first."
    )
latest_price_file = price_files[-1]
print(f"Loading prices from: {latest_price_file}")
prices = pd.read_csv(latest_price_file, index_col=0, parse_dates=True)
prices = prices.sort_index()

# ── Load most recent benchmark file ──────────────────────────────────────────
bmark_files = sorted(glob.glob(os.path.join(RAW_BENCHMARK_DIR, "benchmark_*.csv")))
if not bmark_files:
    print("WARNING: No benchmark file found. Beta will not be calculated.")
    benchmark = None
else:
    latest_bmark_file = bmark_files[-1]
    print(f"Loading benchmark from: {latest_bmark_file}")
    benchmark = pd.read_csv(latest_bmark_file, index_col=0, parse_dates=True).squeeze()
    benchmark = benchmark.sort_index()

# ── Helper functions ──────────────────────────────────────────────────────────

def total_return(series, years):
    """Annualised return over a given number of years from the end of the series."""
    end = series.last_valid_index()
    trading_days = int(years * TRADING_DAYS)
    start_idx = series.index.get_loc(end) - trading_days
    if start_idx < 0:
        return np.nan  # insufficient history
    start_price = series.iloc[max(start_idx, 0)]
    end_price   = series.iloc[-1]
    if pd.isna(start_price) or pd.isna(end_price) or start_price == 0:
        return np.nan
    raw = (end_price / start_price) - 1
    return ((1 + raw) ** (1 / years)) - 1 if years != 1 else raw

def annualised_vol(series):
    """Annualised standard deviation of log daily returns."""
    log_ret = np.log(series / series.shift(1)).dropna()
    if len(log_ret) < 20:
        return np.nan  # insufficient data
    return log_ret.std() * np.sqrt(TRADING_DAYS)

def max_drawdown(series):
    """Maximum peak-to-trough percentage decline."""
    if series.dropna().empty:
        return np.nan
    roll_max = series.cummax()
    drawdown = (series - roll_max) / roll_max
    return drawdown.min()

def sharpe(series):
    """Sharpe ratio via daily excess returns, annualised.
    rf_daily = 2.5% / 252. Formula: (mean(excess) / std(excess)) × sqrt(252).
    Numerically more stable than the annual-return / annual-vol method."""
    log_ret = np.log(series / series.shift(1)).dropna()
    if len(log_ret) < 20:
        return np.nan
    rf_daily = RISK_FREE_RATE / TRADING_DAYS
    excess   = log_ret - rf_daily
    if excess.std() == 0:
        return np.nan
    return (excess.mean() / excess.std()) * np.sqrt(TRADING_DAYS)

def beta_vs_benchmark(series, bmark):
    """Beta: cov(stock_returns, benchmark_returns) / var(benchmark_returns)."""
    if bmark is None:
        return np.nan
    aligned = pd.concat([series, bmark], axis=1, join="inner").dropna()
    if len(aligned) < 20:
        return np.nan
    s_ret = np.log(aligned.iloc[:, 0] / aligned.iloc[:, 0].shift(1)).dropna()
    b_ret = np.log(aligned.iloc[:, 1] / aligned.iloc[:, 1].shift(1)).dropna()
    s_ret, b_ret = s_ret.align(b_ret, join="inner")
    if b_ret.var() == 0:
        return np.nan
    return np.cov(s_ret, b_ret)[0, 1] / b_ret.var()

# ── Calculate metrics for each ticker ─────────────────────────────────────────
records = []
insufficient = []

for ticker in prices.columns:
    s = prices[ticker].dropna()

    if len(s) < 756:  # G1 threshold: <3 years (~756 trading days) = insufficient for all metrics
        print(f"  FLAGGED: {ticker} — only {len(s)} rows (< 756 / 3yr threshold). Metrics will be partial.")
        insufficient.append(ticker)

    r1  = total_return(s, 1)
    r3  = total_return(s, 3)
    r5  = total_return(s, 5)
    vol = annualised_vol(s)
    mdd = max_drawdown(s)
    sr  = sharpe(s)
    bt  = beta_vs_benchmark(s, benchmark)

    records.append({
        "ticker":                   ticker,
        "return_1y_pct":            round(r1 * 100, 2)  if not pd.isna(r1)  else None,
        "return_3y_ann_pct":        round(r3 * 100, 2)  if not pd.isna(r3)  else None,
        "return_5y_ann_pct":        round(r5 * 100, 2)  if not pd.isna(r5)  else None,
        "annualized_volatility_pct":round(vol * 100, 2) if not pd.isna(vol) else None,
        "max_drawdown_pct":         round(mdd * 100, 2) if not pd.isna(mdd) else None,
        "sharpe_ratio":             round(sr, 3)        if not pd.isna(sr)  else None,
        "beta_vs_benchmark":        round(bt, 3)        if not pd.isna(bt)  else None,
        "data_sufficiency_flag":    "INSUFFICIENT" if ticker in insufficient else "OK",
        "price_source":             os.path.basename(latest_price_file),
        "benchmark_source":         os.path.basename(bmark_files[-1]) if bmark_files else "NONE",
        "calculation_date":         TODAY,
        "risk_free_rate_assumption": RISK_FREE_RATE,
        "trading_days_assumption":   TRADING_DAYS,
    })
    print(f"  {ticker}: 1Y={records[-1]['return_1y_pct']}%  vol={records[-1]['annualized_volatility_pct']}%  Sharpe={records[-1]['sharpe_ratio']}  beta={records[-1]['beta_vs_benchmark']}")

# ── Save output ───────────────────────────────────────────────────────────────
out = pd.DataFrame(records)
out_path = os.path.join(OUTPUT_DIR, f"market_metrics_{TODAY}.csv")
out.to_csv(out_path, index=False)
print(f"\nSaved: {out_path}")

if insufficient:
    print(f"\nFlagged (insufficient history): {insufficient}")
    print("These tickers will have partial or null metrics. Document in audit log.")

print("\nNext step: run financial_scoring_template.py to combine with fundamentals.")
print("Audit trail: log this run in data/financial/financial_audit_log.csv")
