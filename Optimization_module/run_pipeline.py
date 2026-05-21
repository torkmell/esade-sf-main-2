"""
run_pipeline.py — orchestrator.

Runs the whole module end-to-end and writes everything required by build
spec sec. 9 into `outputs/`:

  - optimization_weights.csv  : final weight vector of every method.
  - backtest_results.csv      : method-vs-metrics comparison + composite rank.
  - equity_curves.png         : OOS cumulative return of every method + bench.
  - run_log.txt               : audit log with timestamps, parameters, bad
                                tickers, failed methods, the look-ahead
                                disclosure, and WACI-skip count.

The console output at the end mirrors what a human gets to read first.

This script is the SINGLE entry point. Other files have CLI helpers for
debugging (`python data_loader.py`, etc.) but `run_pipeline.py` is what
produces the deliverables.
"""

from __future__ import annotations

import sys
import time
from datetime import datetime
from typing import Dict

import matplotlib

# Use a non-interactive backend so the script works on headless machines /
# CI agents without a display.
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import config           # noqa: E402
import data_loader      # noqa: E402
import optimizers       # noqa: E402
import backtester       # noqa: E402
import selector         # noqa: E402


# ---------------------------------------------------------------------------
# A small in-memory log we flush to run_log.txt at the end
# ---------------------------------------------------------------------------
class RunLog:
    """Accumulates audit lines and writes them to disk on close()."""

    def __init__(self) -> None:
        self.lines = []
        self.t0 = datetime.utcnow()
        self.add(f"Run started (UTC): {self.t0.isoformat(timespec='seconds')}")

    def add(self, line: str = "") -> None:
        self.lines.append(line)
        print(line)

    def section(self, title: str) -> None:
        self.add("")
        self.add("-" * 60)
        self.add(title)
        self.add("-" * 60)

    def close(self, path) -> None:
        self.add("")
        self.add(f"Run finished (UTC): "
                 f"{datetime.utcnow().isoformat(timespec='seconds')} "
                 f"(elapsed {(datetime.utcnow() - self.t0).total_seconds():.1f}s)")
        path.write_text("\n".join(self.lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# Steps
# ---------------------------------------------------------------------------
def step_setup(log: RunLog) -> None:
    """Make sure output / data folders exist; log the parameter set."""
    config.ensure_dirs()
    log.section("Parameters (from config.py)")
    log.add(f"  RANDOM_SEED              = {config.RANDOM_SEED}")
    log.add(f"  MAX_WEIGHT_PER_STOCK     = {config.MAX_WEIGHT_PER_STOCK:.0%}")
    log.add(f"  MAX_WEIGHT_PER_SECTOR    = {config.MAX_WEIGHT_PER_SECTOR:.0%}")
    log.add(f"  PRICE_HISTORY_YEARS      = {config.PRICE_HISTORY_YEARS}")
    log.add(f"  ESTIMATION_WINDOW_YEARS  = {config.ESTIMATION_WINDOW_YEARS} "
            f"({config.ESTIMATION_WINDOW_DAYS} trading days)")
    log.add(f"  REBALANCE_FREQUENCY      = {config.REBALANCE_FREQUENCY}")
    log.add(f"  RISK_FREE_RATE           = {config.RISK_FREE_RATE:.2%}")
    log.add(f"  BENCHMARK                = {config.BENCHMARK_NAME} "
            f"({config.BENCHMARK_TICKER})")
    log.add(f"  TRACKING_ERROR_BAND      = "
            f"{config.TRACKING_ERROR_BAND[0]:.0%}-"
            f"{config.TRACKING_ERROR_BAND[1]:.0%}")
    log.add(f"  COMPOSITE_WEIGHTS        = {config.COMPOSITE_WEIGHTS}")
    log.add(f"  BL_ESG_VIEW_SPREAD       = {config.BL_ESG_VIEW_SPREAD:.2%}")


def step_load_and_verify(log: RunLog):
    """Load CSV, verify tickers, return holdings + group maps."""
    log.section("Holdings CSV + ticker verification")
    holdings = data_loader.load_holdings()
    log.add(f"  CSV: {config.HOLDINGS_CSV}")
    log.add(f"  Rows: {len(holdings)}  Columns: {list(holdings.columns)}")

    status = data_loader.verify_tickers(holdings["ticker"].tolist())
    bad = [t for t, ok in status.items() if not ok]
    log.add(f"  Ticker verify: {len(status) - len(bad)}/{len(status)} OK")
    if bad:
        log.add(f"  Bad tickers: {bad}")
        raise SystemExit(
            f"ABORT: {len(bad)} ticker(s) returned no data. Fix the CSV and "
            f"rerun. Offending: {bad}"
        )

    bench_status = data_loader.verify_tickers([config.BENCHMARK_TICKER])
    if not bench_status[config.BENCHMARK_TICKER]:
        log.add(f"  Benchmark ticker {config.BENCHMARK_TICKER} returned no data.")
        raise SystemExit(
            f"ABORT: benchmark ticker {config.BENCHMARK_TICKER} returned "
            f"no data. Pick a different proxy and rerun."
        )
    log.add(f"  Benchmark {config.BENCHMARK_TICKER}: OK")

    sector_map = data_loader.build_group_maps(holdings)
    return holdings, sector_map


def step_download_prices(log: RunLog, holdings):
    """Pull the full historical panel + benchmark (cache-aware)."""
    log.section("Price download")
    prices, benchmark, fetched_at = data_loader.download_prices(
        holdings["ticker"].tolist()
    )
    log.add(f"  Fetched at (UTC ISO): {fetched_at}")
    log.add(f"  Panel: {prices.shape[0]} rows x {prices.shape[1]} tickers")
    log.add(f"  Range: {prices.index[0].date()} -> {prices.index[-1].date()}")
    log.add(f"  Benchmark series length: {len(benchmark)}")
    return prices, benchmark, fetched_at


def step_final_weights(log: RunLog, prices, holdings, sector_map):
    """Run each method ONCE on the most recent estimation window.

    These are the weights that go into optimization_weights.csv. Reusing the
    most-recent in-sample window gives a single, comparable snapshot per
    method that a human can read directly.
    """
    log.section("Final-snapshot optimization (most recent estimation window)")
    in_sample = prices.tail(config.ESTIMATION_WINDOW_DAYS)
    log.add(f"  Window: {in_sample.index[0].date()} -> "
            f"{in_sample.index[-1].date()} ({len(in_sample)} rows)")

    snapshot: Dict[str, Dict[str, float]] = {}
    for method in optimizers.METHODS:
        w = optimizers.optimize(
            method, in_sample, holdings, sector_map
        )
        if w is None:
            log.add(f"  {method:<18s}: INFEASIBLE")
            continue
        snapshot[method] = w
        wser = pd.Series(w)
        log.add(f"  {method:<18s}: sum={wser.sum():.4f} "
                f"max_name={wser.max():.3%} "
                f"top3={', '.join(f'{t}={v:.2%}' for t, v in wser.nlargest(3).items())}")
    return snapshot


def step_backtest(log: RunLog, prices, benchmark, holdings, sector_map):
    """Walk-forward OOS backtest for every method."""
    log.section("Walk-forward backtest (out-of-sample)")
    results = backtester.run_all(
        prices, benchmark, holdings, sector_map
    )
    for method, res in results.items():
        log.add(f"  {method:<18s}: {len(res.portfolio_returns):>5d} OOS days, "
                f"{len(res.weights_by_date)} rebalances, "
                f"{len(res.failed_dates)} failed")
    return results


def step_metrics_and_recommendation(log: RunLog, results, holdings):
    """Compute per-method metrics, rank, recommend."""
    log.section("Metrics + composite ranking")
    metrics = {m: backtester.compute_metrics(r, holdings)
               for m, r in results.items()}

    # Aggregate WACI-skip count across methods (each method's final weights
    # may skip different names if carbon data is missing).
    waci_skipped = max((m["n_waci_skipped"] for m in metrics.values()),
                       default=0)
    log.add(f"  WACI: names without carbon_intensity skipped = {waci_skipped}")

    comparison, scored, winner, rationale = selector.select(metrics)
    log.add("")
    log.add("RECOMMENDATION - FOR HUMAN INVESTMENT COMMITTEE REVIEW")
    log.add(f"  {rationale}")
    return comparison, scored, winner, rationale


def step_write_outputs(
    log: RunLog,
    snapshot,
    scored,
    results,
    benchmark,
):
    """Write CSVs and PNG into outputs/."""
    log.section("Writing outputs")

    # 1. optimization_weights.csv — methods as columns, tickers as rows.
    weights_df = pd.DataFrame(snapshot).fillna(0.0)
    weights_df.index.name = "ticker"
    weights_path = config.OUTPUTS_DIR / "optimization_weights.csv"
    weights_df.to_csv(weights_path, float_format="%.6f")
    log.add(f"  {weights_path}")

    # 2. backtest_results.csv — the comparison-plus-scores table.
    results_path = config.OUTPUTS_DIR / "backtest_results.csv"
    scored.to_csv(results_path, float_format="%.6f")
    log.add(f"  {results_path}")

    # 3. equity_curves.png — one line per method + benchmark.
    fig_path = config.OUTPUTS_DIR / "equity_curves.png"
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Custom styles to prevent line overlapping (e.g. equal_weight vs score_tilted)
    style_map = {
        "equal_weight":    {"color": "#555555", "linestyle": ":",  "linewidth": 2.5, "alpha": 0.8},
        "hrp":             {"color": "#1f77b4", "linestyle": "-",  "linewidth": 2.0, "alpha": 0.9},
        "score_tilted":    {"color": "#ff7f0e", "linestyle": "-.", "linewidth": 2.0, "alpha": 0.9},
        "max_sharpe":      {"color": "#2ca02c", "linestyle": "--", "linewidth": 1.5, "alpha": 0.7},
        "min_volatility":  {"color": "#d62728", "linestyle": "--", "linewidth": 1.5, "alpha": 0.7},
        "black_litterman": {"color": "#9467bd", "linestyle": "--", "linewidth": 1.5, "alpha": 0.7},
    }
    
    for method, res in results.items():
        if res.portfolio_returns.empty:
            continue
        eq = (1.0 + res.portfolio_returns).cumprod()
        style = style_map.get(method, {"linewidth": 1.5})
        ax.plot(eq.index, eq.values, label=method, **style)
        
    # Benchmark: align to the union of OOS dates we just plotted.
    all_oos = pd.Index([])
    for res in results.values():
        all_oos = all_oos.union(res.portfolio_returns.index)
    if len(all_oos) and not benchmark.empty:
        bench_rets = benchmark.pct_change().dropna()
        bench_rets = bench_rets.loc[bench_rets.index.intersection(all_oos)]
        if not bench_rets.empty:
            bench_eq = (1.0 + bench_rets).cumprod()
            ax.plot(bench_eq.index, bench_eq.values,
                    label=f"Benchmark ({config.BENCHMARK_TICKER})",
                    linewidth=2.0, linestyle="--", color="black")
    ax.set_title("Out-of-sample equity curves (rebased to 1.0)")
    ax.set_xlabel("Date")
    ax.set_ylabel("Growth of 1.00")
    ax.grid(alpha=0.3)
    ax.legend(loc="best", fontsize=9)
    fig.tight_layout()
    fig.savefig(fig_path, dpi=120)
    plt.close(fig)
    log.add(f"  {fig_path}")


def step_lookahead_disclosure(log: RunLog) -> None:
    """Emit the verbatim look-ahead disclosure required by spec sec. 7."""
    log.section("Look-ahead disclosure (verbatim, required by build spec)")
    log.add(f"  {config.LOOKAHEAD_DISCLOSURE}")


# ---------------------------------------------------------------------------
# Console summary helper
# ---------------------------------------------------------------------------
def print_console_summary(scored: pd.DataFrame, winner: str, rationale: str):
    print()
    print("=" * 70)
    print(" FINAL SUMMARY ".center(70, "="))
    print("=" * 70)
    cols = ["sharpe", "max_drawdown", "annual_turnover",
            "tracking_error", "waci", "composite_score", "rank"]
    cols = [c for c in cols if c in scored.columns]
    fmt = scored[cols].copy()
    for c in fmt.columns:
        if c == "rank":
            fmt[c] = fmt[c].astype(int)
        elif c == "waci":
            fmt[c] = fmt[c].map(lambda x: f"{x:.1f}")
        elif c == "composite_score":
            fmt[c] = fmt[c].map(lambda x: f"{x:.3f}")
        else:
            fmt[c] = fmt[c].map(lambda x: f"{x:.2%}" if pd.notna(x) else "n/a")
    print(fmt.to_string())
    print()
    print(f"Recommended method: {winner}")
    print(rationale)
    print("=" * 70)


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    log = RunLog()
    log.add("Optimization & Backtesting pipeline")

    step_setup(log)
    holdings, sector_map = step_load_and_verify(log)
    prices, benchmark, _ = step_download_prices(log, holdings)
    snapshot = step_final_weights(log, prices, holdings, sector_map)
    results = step_backtest(log, prices, benchmark, holdings, sector_map)
    comparison, scored, winner, rationale = step_metrics_and_recommendation(
        log, results, holdings
    )
    step_write_outputs(log, snapshot, scored, results, benchmark)
    step_lookahead_disclosure(log)

    log.close(config.RUN_LOG)
    print_console_summary(scored, winner, rationale)
    print(f"\nAll outputs written to: {config.OUTPUTS_DIR}")
    print(f"Run log: {config.RUN_LOG}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
