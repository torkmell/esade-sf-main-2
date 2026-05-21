"""
fetch_price_data_template.py
----------------------------
Downloads historical daily adjusted close prices for portfolio tickers and
the benchmark, then saves them as timestamped CSVs under:

  /data/financial/raw_prices/
  /data/financial/raw_benchmark/

Dependencies:
  pip install yfinance pandas

Run manually only — do NOT execute automatically.
"""

import os
import pandas as pd
from datetime import date

# ── Install check ──────────────────────────────────────────────────────────────
try:
    import yfinance as yf
except ImportError:
    raise ImportError(
        "yfinance is not installed. Run: pip install yfinance"
    )

# ── Configuration ──────────────────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

TICKER_CSV = os.path.join(ROOT, "data", "financial", "financial_data_tracker.csv")

RAW_PRICES_DIR   = os.path.join(ROOT, "data", "financial", "raw_prices")
RAW_BENCHMARK_DIR = os.path.join(ROOT, "data", "financial", "raw_benchmark")

PRICE_START = "2020-01-01"
PRICE_END   = "2025-01-01"

BENCHMARK_TICKER = "EXW1.DE"  # iShares STOXX Europe 600 ETF — proxy for STOXX 600

TODAY = date.today().isoformat()

os.makedirs(RAW_PRICES_DIR, exist_ok=True)
os.makedirs(RAW_BENCHMARK_DIR, exist_ok=True)

# ── Load tickers from tracker ─────────────────────────────────────────────────
tracker = pd.read_csv(TICKER_CSV)

# Column in tracker that holds Yahoo Finance tickers — update if column name changes
# The tracker CSV has a "ticker" column (Bloomberg) but yfinance needs Yahoo tickers.
# Yahoo tickers are stored in the financial_agent_outputs.csv or can be read from
# final_portfolio_2026-05-14.csv. For now, load from portfolio output.
PORTFOLIO_CSV = os.path.join(ROOT, "outputs", "portfolio", "final_portfolio_2026-05-14.csv")
portfolio = pd.read_csv(PORTFOLIO_CSV)

# Map bloomberg ticker -> yahoo ticker
ticker_map = dict(zip(portfolio["ticker"], portfolio["yf_ticker"]))

yf_tickers = [v for v in ticker_map.values() if pd.notna(v) and v != ""]
print(f"Downloading prices for {len(yf_tickers)} tickers: {yf_tickers}")

# ── Download portfolio prices ─────────────────────────────────────────────────
failed = []
prices_list = []

for yf_ticker in yf_tickers:
    try:
        data = yf.download(
            yf_ticker,
            start=PRICE_START,
            end=PRICE_END,
            auto_adjust=True,
            progress=False,
        )["Close"]

        if data.empty:
            print(f"  WARNING: No data returned for {yf_ticker}")
            failed.append(yf_ticker)
            continue

        # Rename column to yf_ticker for clarity
        data = data.rename(yf_ticker)
        prices_list.append(data)
        print(f"  OK: {yf_ticker} — {len(data)} rows")

    except Exception as e:
        print(f"  ERROR: {yf_ticker} — {e}")
        failed.append(yf_ticker)

if prices_list:
    prices = pd.concat(prices_list, axis=1)
    out_path = os.path.join(RAW_PRICES_DIR, f"raw_prices_{TODAY}.csv")
    prices.to_csv(out_path)
    print(f"\nSaved: {out_path}")
    print(f"Shape: {prices.shape}")

if failed:
    print(f"\nFailed tickers ({len(failed)}): {failed}")
    print("Check ticker symbols against Yahoo Finance — they may have changed.")

# ── Download benchmark ────────────────────────────────────────────────────────
print(f"\nDownloading benchmark: {BENCHMARK_TICKER}")
try:
    bmark = yf.download(
        BENCHMARK_TICKER,
        start=PRICE_START,
        end=PRICE_END,
        auto_adjust=True,
        progress=False,
    )["Close"]

    bmark_path = os.path.join(RAW_BENCHMARK_DIR, f"benchmark_{BENCHMARK_TICKER}_{TODAY}.csv")
    bmark.to_csv(bmark_path)
    print(f"Saved: {bmark_path} — {len(bmark)} rows")

except Exception as e:
    print(f"ERROR downloading benchmark: {e}")

print("\nDone. Review downloaded files before running calculate_market_metrics_template.py.")
print("Audit trail: log this run in data/financial/financial_audit_log.csv")
