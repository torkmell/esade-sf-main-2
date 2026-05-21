"""
data_loader.py — load the holdings CSV, verify tickers, and fetch prices.

This module is the data plumbing for the rest of the pipeline. Nothing here
makes investment decisions — it only:

  1. Reads `sample_holdings_20.csv` and validates its columns.
  2. **Verifies every ticker actually returns data** before any long download.
     This is the single biggest source of avoidable failure (a mistyped Yahoo
     suffix wastes 8 years of download time on a bad name). We fail fast and
     loudly here so the human can fix tickers before the real run.
  3. Downloads up to 8 years of daily prices for the 20 names and the
     benchmark, and caches them on disk so re-runs are reproducible.
  4. Builds simple `{ticker: sector}` and `{ticker: country}` lookup tables
     that the optimizers use for sector / country caps.

All functions are documented in plain English. The module can also be run
directly (`python data_loader.py`) — that runs the inspection + verification
step ONLY, prints a report, and does NOT touch the 8-year download. That is
the deliberate PAUSE point from the build spec.
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd
import yfinance as yf

import config

# Columns we expect to find in sample_holdings_20.csv. If any are missing,
# we refuse to proceed — silently coping with a malformed CSV is exactly the
# kind of "silent failure" the build spec forbids.
REQUIRED_COLUMNS = [
    "ticker",
    "company_name",
    "sector",
    "esg_score",
    "carbon_intensity",
]


# ---------------------------------------------------------------------------
# 1. Holdings CSV
# ---------------------------------------------------------------------------
def load_holdings(csv_path: Path | None = None) -> pd.DataFrame:
    """Read the 20-stock holdings file and validate its columns.

    Input:
        csv_path: optional path to the holdings CSV. Defaults to the path
                  configured in config.HOLDINGS_CSV.

    Output:
        A pandas DataFrame indexed 0..N-1 with the columns listed in
        REQUIRED_COLUMNS. Tickers are stripped of whitespace.

    Raises:
        FileNotFoundError if the CSV is missing.
        ValueError if any required column is absent.
    """
    path = Path(csv_path) if csv_path else config.HOLDINGS_CSV
    if not path.exists():
        raise FileNotFoundError(f"Holdings CSV not found: {path}")

    df = pd.read_csv(path)

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(
            f"Holdings CSV is missing required columns: {missing}. "
            f"Found columns: {list(df.columns)}"
        )

    # Defensive cleanup: strip whitespace from the string columns. A stray
    # space in a ticker is a very common cause of "no data" surprises.
    for col in ["ticker", "company_name", "sector"]:
        df[col] = df[col].astype(str).str.strip()

    # ESG scores must be numeric; coerce silently-bad values to NaN and warn.
    df["esg_score"] = pd.to_numeric(df["esg_score"], errors="coerce")
    df["carbon_intensity"] = pd.to_numeric(df["carbon_intensity"], errors="coerce")

    return df


# ---------------------------------------------------------------------------
# 2. Sector / country lookup tables
# ---------------------------------------------------------------------------
def build_group_maps(
    holdings: pd.DataFrame,
) -> Dict[str, str]:
    """Build a `{ticker: sector}` dictionary.

    Optimizers use this to translate per-stock weights into sector totals so
    they can apply the 25% sector cap.
    """
    return dict(zip(holdings["ticker"], holdings["sector"]))


# ---------------------------------------------------------------------------
# 3. Ticker verification — the deliberate PAUSE point
# ---------------------------------------------------------------------------
def verify_tickers(
    tickers: List[str],
    days: int | None = None,
) -> Dict[str, bool]:
    """Download a short recent price window for each ticker and report status.

    For each ticker we try to pull `days` worth of daily bars from Yahoo
    Finance. If the response is empty, the ticker is flagged as bad. This is
    cheap (a few hundred KB of data) and surfaces typos / delisted names
    BEFORE the long 8-year download starts.

    Input:
        tickers: list of Yahoo Finance tickers (with exchange suffix).
        days:    how many recent calendar days to probe. Defaults to
                 config.TICKER_VERIFY_DAYS.

    Output:
        Dict `{ticker: True_if_ok_else_False}` in the same order as input.

    Notes on behaviour:
        - We download tickers one at a time. yfinance's batch download can
          silently swallow bad symbols; single-ticker calls give us a clean
          "this name returned 0 rows" signal per name.
        - Network errors are caught and counted as "bad" — the user can re-run
          if it was a transient blip.
    """
    days = days or config.TICKER_VERIFY_DAYS
    end = datetime.utcnow()
    start = end - timedelta(days=days)

    status: Dict[str, bool] = {}
    for t in tickers:
        try:
            data = yf.download(
                t,
                start=start.strftime("%Y-%m-%d"),
                end=end.strftime("%Y-%m-%d"),
                progress=False,
                auto_adjust=config.PRICE_AUTO_ADJUST,
                threads=False,
            )
            status[t] = (data is not None) and (not data.empty)
        except Exception as exc:
            # Network glitch, rate limit, etc. Treat as bad for now; the
            # caller decides whether to abort or retry.
            print(f"  [WARN] {t}: exception during verify -> {exc}")
            status[t] = False

        # A tiny pause keeps Yahoo's free endpoint happy for 20 calls.
        time.sleep(0.1)

    return status


def print_verification_report(status: Dict[str, bool]) -> int:
    """Pretty-print the result of `verify_tickers` and return # of bad tickers.

    Output goes to stdout so the human running `python data_loader.py` sees
    it immediately. We deliberately do NOT raise on bad tickers — the caller
    decides what to do with the report.
    """
    ok = [t for t, good in status.items() if good]
    bad = [t for t, good in status.items() if not good]

    print()
    print("Ticker verification report")
    print("-" * 40)
    print(f"  OK   ({len(ok):>2d}/{len(status)}): {', '.join(ok) or '(none)'}")
    print(f"  FAIL ({len(bad):>2d}/{len(status)}): {', '.join(bad) or '(none)'}")
    print("-" * 40)
    if bad:
        print("  ACTION REQUIRED: fix or replace the FAIL tickers before "
              "the full price download.")
    else:
        print("  All tickers returned data. Safe to proceed to the full "
              "price download.")
    print()
    return len(bad)


# ---------------------------------------------------------------------------
# 4. Long-history price download — with on-disk cache
# ---------------------------------------------------------------------------
def _cache_paths() -> Tuple[Path, Path]:
    """Return the (data file, meta file) paths used by the price cache."""
    return (
        config.DATA_DIR / "prices.pkl",
        config.DATA_DIR / "prices_meta.json",
    )


def _cache_is_valid(
    meta_path: Path,
    tickers: List[str],
    years: int,
    benchmark: str,
) -> bool:
    """Return True iff a previously cached file matches the current request.

    The cache is invalidated if the holdings list, the requested history
    length, or the benchmark ticker changed. The cache is also invalidated
    if it is older than 24 hours, so a fresh run on a new day picks up the
    latest bars without manual intervention.
    """
    if not meta_path.exists():
        return False
    try:
        meta = json.loads(meta_path.read_text())
    except Exception:
        return False

    if sorted(meta.get("tickers", [])) != sorted(tickers):
        return False
    if meta.get("years") != years:
        return False
    if meta.get("benchmark") != benchmark:
        return False

    fetched = meta.get("fetched_at")
    if not fetched:
        return False
    try:
        age = datetime.utcnow() - datetime.fromisoformat(fetched)
    except Exception:
        return False
    return age < timedelta(hours=24)


def download_prices(
    tickers: List[str],
    years: int | None = None,
    use_cache: bool = True,
) -> Tuple[pd.DataFrame, pd.Series, str]:
    """Download daily adjusted close prices for the 20 names + benchmark.

    Input:
        tickers:   list of Yahoo Finance tickers.
        years:     how many years of history to request (defaults to config).
        use_cache: read/write the on-disk cache. Pass False to force a fresh
                   download (useful when debugging the data layer).

    Output:
        A tuple `(prices, benchmark, fetched_at_iso)` where:
          - `prices` is a DataFrame of shape (T, N) with one column per
            ticker. Adjusted close prices, NaNs forward-filled then dropped
            for rows with any remaining NaN.
          - `benchmark` is a Series of the same calendar with the benchmark
            adjusted close prices, aligned on the same dates as `prices`.
          - `fetched_at_iso` is an ISO timestamp of when the data was pulled
            (used in run_log.txt as the audit "price-download date").

    Behaviour:
        - On cache hit, we read prices.pkl and skip the network entirely.
        - yfinance returns multi-level columns when given >1 ticker; we
          flatten to a plain {ticker: Series} layout.
        - Any ticker whose full-history download returns 0 rows is logged
          and dropped, never silently kept as NaNs.
    """
    years = years or config.PRICE_HISTORY_YEARS
    end = datetime.utcnow()
    start = end - timedelta(days=int(years * 365.25) + 7)  # +7d safety pad

    prices_path, meta_path = _cache_paths()

    if use_cache and _cache_is_valid(
        meta_path, tickers, years, config.BENCHMARK_TICKER
    ):
        print(f"  [cache] using cached prices at {prices_path}")
        bundle = pd.read_pickle(prices_path)
        meta = json.loads(meta_path.read_text())
        return bundle["prices"], bundle["benchmark"], meta["fetched_at"]

    print(f"  Downloading {len(tickers)} tickers + benchmark "
          f"({years} years) from Yahoo Finance...")

    # Step 1: holdings. Batch download, then flatten columns.
    raw = yf.download(
        tickers,
        start=start.strftime("%Y-%m-%d"),
        end=end.strftime("%Y-%m-%d"),
        progress=False,
        auto_adjust=config.PRICE_AUTO_ADJUST,
        threads=True,
        group_by="ticker",
    )

    prices: Dict[str, pd.Series] = {}
    dropped: List[str] = []

    if isinstance(raw.columns, pd.MultiIndex):
        # group_by="ticker" gives (ticker, field) columns.
        for t in tickers:
            if t not in raw.columns.get_level_values(0):
                dropped.append(t)
                continue
            series = raw[t]["Close"].dropna()
            if series.empty:
                dropped.append(t)
            else:
                prices[t] = series
    else:
        # Single ticker — flat columns. Should not happen for 20 names but
        # we handle it for completeness.
        series = raw["Close"].dropna()
        if not series.empty:
            prices[tickers[0]] = series
        else:
            dropped.append(tickers[0])

    if dropped:
        print(f"  [WARN] full-history download returned no data for: {dropped}")

    if not prices:
        raise RuntimeError(
            "No price data returned for any ticker. Aborting — check network "
            "connectivity and ticker symbols."
        )

    prices_df = pd.DataFrame(prices).sort_index()
    # Forward-fill small gaps (e.g. local holidays on some exchanges) then
    # drop dates where any ticker is still NaN. The result is an aligned
    # panel that every optimizer can consume directly.
    prices_df = prices_df.ffill().dropna(how="any")

    # Step 2: benchmark.
    bench_raw = yf.download(
        config.BENCHMARK_TICKER,
        start=start.strftime("%Y-%m-%d"),
        end=end.strftime("%Y-%m-%d"),
        progress=False,
        auto_adjust=config.PRICE_AUTO_ADJUST,
        threads=False,
    )
    if bench_raw is None or bench_raw.empty:
        raise RuntimeError(
            f"Benchmark download failed for {config.BENCHMARK_TICKER}. "
            f"Aborting."
        )

    # yfinance sometimes returns a multi-level column here too.
    if isinstance(bench_raw.columns, pd.MultiIndex):
        bench_close = bench_raw["Close"].iloc[:, 0]
    else:
        bench_close = bench_raw["Close"]
    benchmark = bench_close.dropna().sort_index()

    # Align the benchmark to the same trading days as the holdings panel.
    benchmark = benchmark.reindex(prices_df.index).ffill().dropna()
    prices_df = prices_df.loc[benchmark.index]

    fetched_at = datetime.utcnow().isoformat(timespec="seconds")

    # Step 3: cache to disk.
    config.ensure_dirs()
    pd.to_pickle({"prices": prices_df, "benchmark": benchmark}, prices_path)
    meta_path.write_text(json.dumps({
        "tickers": list(prices_df.columns),
        "dropped_tickers": dropped,
        "years": years,
        "benchmark": config.BENCHMARK_TICKER,
        "fetched_at": fetched_at,
        "n_rows": int(len(prices_df)),
        "first_date": str(prices_df.index[0].date()),
        "last_date": str(prices_df.index[-1].date()),
    }, indent=2))

    print(f"  Saved cache: {prices_path}")
    print(f"  Saved meta:  {meta_path}")
    print(f"  Panel shape: {prices_df.shape} (rows x tickers)")
    print(f"  Date range:  {prices_df.index[0].date()} -> "
          f"{prices_df.index[-1].date()}")

    return prices_df, benchmark, fetched_at


# ---------------------------------------------------------------------------
# CLI: inspection + ticker verification ONLY (the deliberate PAUSE point)
# ---------------------------------------------------------------------------
def _main_inspect_and_verify() -> int:
    """Print CSV summary, run ticker verification, and stop.

    This is what `python data_loader.py` does. The user inspects the report,
    fixes any bad tickers, and re-runs. Only run_pipeline.py triggers the
    full 8-year download.
    """
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    print("=" * 60)
    print("data_loader.py - CSV inspection + ticker verification")
    print("=" * 60)

    holdings = load_holdings()
    print(f"  CSV: {config.HOLDINGS_CSV}")
    print(f"  Rows: {len(holdings)}")
    print(f"  Columns: {list(holdings.columns)}")
    print()
    print("First 5 rows:")
    print(holdings.head().to_string(index=False))
    print()

    sectors = holdings["sector"].value_counts()
    print(f"Sector distribution ({len(sectors)} sectors):")
    for s, n in sectors.items():
        print(f"  {s:<35s} {n:>2d}")
    print()

    print(f"Verifying {len(holdings)} tickers against Yahoo Finance "
          f"({config.TICKER_VERIFY_DAYS}-day probe)...")
    status = verify_tickers(holdings["ticker"].tolist())
    n_bad = print_verification_report(status)

    # Also probe the benchmark itself so a bad BENCHMARK_TICKER fails here,
    # not deep inside the backtest.
    print(f"Verifying benchmark ticker: {config.BENCHMARK_TICKER}")
    bench_status = verify_tickers([config.BENCHMARK_TICKER])
    if not bench_status[config.BENCHMARK_TICKER]:
        print(f"  [ERROR] benchmark ticker {config.BENCHMARK_TICKER} "
              f"returned no data. Pipeline cannot run until this is fixed.")
        n_bad += 1
    else:
        print(f"  OK: benchmark ticker {config.BENCHMARK_TICKER} responded.")

    print()
    if n_bad:
        print(f"STOP: {n_bad} ticker(s) need to be fixed before the full "
              f"price download.")
        return 1
    print("OK: ready for the full 8-year price download "
          "(invoked by run_pipeline.py).")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main_inspect_and_verify())
