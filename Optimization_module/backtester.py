"""
backtester.py — the Backtesting Agent.

Walk-forward, out-of-sample backtest. Build spec sec. 7:

  - Estimation window (in-sample): 3 years (~756 trading days).
    Expected returns / covariance are estimated ONLY from this window.
  - Rebalance frequency: annual (configurable via config.REBALANCE_FREQUENCY).
  - At each rebalance date, run a method on the trailing 3-year window,
    get weights, HOLD those weights for the next year, record OOS returns.
  - The estimation window and the performance-measurement window NEVER
    overlap. Reported performance is the stitched-together sequence of
    out-of-sample years only.
  - Run for every method in optimizers.py.

For each method we compute:
  - Cumulative return, CAGR, annualised volatility
  - Sharpe and Sortino
  - Maximum drawdown
  - Annual turnover (sum of |delta weights| at each rebalance)
  - Tracking error vs the benchmark (annualised std of P - B returns)
  - Portfolio WACI (weighted-average carbon intensity, skipping blank rows)

Pure Python / NumPy / pandas. No LLM calls. Deterministic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

import config
import optimizers


# ---------------------------------------------------------------------------
# Rebalance schedule
# ---------------------------------------------------------------------------
def _rebalance_dates(
    index: pd.DatetimeIndex,
    estimation_days: int,
    frequency: str,
) -> List[pd.Timestamp]:
    """Return the list of dates on which the portfolio is re-optimized.

    The first rebalance date is the first trading day on which we have a
    full `estimation_days` of history behind us. Subsequent rebalances are
    spaced by `frequency`. The last rebalance date is the latest one for
    which we can still observe at least one OOS bar.

    `frequency` values supported:
      - "annual"    : every ~252 trading days
      - "quarterly" : every ~63 trading days
      - "monthly"   : every ~21 trading days
    """
    step_map = {
        "annual": 252,
        "quarterly": 63,
        "monthly": 21,
    }
    step = step_map.get(frequency)
    if step is None:
        raise ValueError(f"Unsupported rebalance frequency: {frequency}")

    if len(index) <= estimation_days:
        return []

    dates: List[pd.Timestamp] = []
    i = estimation_days  # first index where we have full history behind us
    while i < len(index) - 1:  # need at least one OOS bar after the rebalance
        dates.append(index[i])
        i += step
    return dates


# ---------------------------------------------------------------------------
# Per-method backtest container
# ---------------------------------------------------------------------------
@dataclass
class BacktestResult:
    """Container for one method's complete backtest output."""
    method: str
    weights_by_date: Dict[pd.Timestamp, Dict[str, float]] = field(default_factory=dict)
    portfolio_returns: pd.Series = field(default_factory=lambda: pd.Series(dtype=float))
    benchmark_returns: pd.Series = field(default_factory=lambda: pd.Series(dtype=float))
    failed_dates: List[pd.Timestamp] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Walk-forward driver — runs ONE method end-to-end
# ---------------------------------------------------------------------------
def backtest_method(
    method: str,
    prices: pd.DataFrame,
    benchmark: pd.Series,
    holdings: pd.DataFrame,
    sector_map: Dict[str, str],
) -> BacktestResult:
    """Walk forward, rebalancing at each scheduled date.

    At rebalance date t:
      1. In-sample window = prices in [t - estimation_days, t).
      2. Run `method` on that window -> weights.
      3. Compute realised daily returns from t up to the NEXT rebalance date
         using the held weights. These are the out-of-sample returns.
      4. Repeat.

    The estimation window stops STRICTLY before t, so no day inside the
    measurement window is used to compute its own weights -> no overlap.
    """
    print(f"  backtest: {method}")
    estimation_days = config.ESTIMATION_WINDOW_DAYS
    daily_rets = prices.pct_change().dropna(how="any")
    bench_rets = benchmark.pct_change().dropna()
    bench_rets = bench_rets.loc[bench_rets.index.intersection(daily_rets.index)]
    daily_rets = daily_rets.loc[bench_rets.index]

    rebal_dates = _rebalance_dates(
        daily_rets.index, estimation_days, config.REBALANCE_FREQUENCY
    )

    result = BacktestResult(method=method)
    pieces_portfolio: List[pd.Series] = []
    pieces_bench: List[pd.Series] = []

    for i, t in enumerate(rebal_dates):
        # 1. In-sample window — strictly before t.
        end_pos = daily_rets.index.get_loc(t)
        start_pos = max(0, end_pos - estimation_days)
        in_sample_prices = prices.iloc[start_pos:end_pos + 1]
        # (We use prices up to and INCLUDING the rebalance day to estimate;
        # daily returns from t+1 onwards are the OOS series.)

        # 2. Optimize.
        weights = optimizers.optimize(
            method, in_sample_prices, holdings, sector_map
        )
        if weights is None:
            result.failed_dates.append(t)
            continue
        result.weights_by_date[t] = weights

        # 3. OOS window — from the day AFTER t up to (but not including) the
        # next rebalance date (or the end of the data, for the last block).
        next_t = rebal_dates[i + 1] if i + 1 < len(rebal_dates) else None
        oos = daily_rets.loc[daily_rets.index > t]
        if next_t is not None:
            oos = oos.loc[oos.index < next_t]
        if oos.empty:
            continue

        # 4. Stitch returns.
        w_vec = np.array([weights.get(c, 0.0) for c in oos.columns])
        port_daily = (oos.values @ w_vec)
        pieces_portfolio.append(pd.Series(port_daily, index=oos.index))
        pieces_bench.append(bench_rets.loc[oos.index])

    if pieces_portfolio:
        result.portfolio_returns = pd.concat(pieces_portfolio).sort_index()
        result.benchmark_returns = pd.concat(pieces_bench).sort_index()

    return result


# ---------------------------------------------------------------------------
# Performance metrics — applied to one BacktestResult
# ---------------------------------------------------------------------------
def _max_drawdown(equity: pd.Series) -> float:
    """Return the maximum peak-to-trough drawdown of an equity curve."""
    if equity.empty:
        return float("nan")
    running_max = equity.cummax()
    dd = equity / running_max - 1.0
    return float(dd.min())


def _annual_turnover(
    weights_by_date: Dict[pd.Timestamp, Dict[str, float]],
    rebalances_per_year: float,
) -> float:
    """Sum of |delta weights| at each rebalance, scaled to per-year.

    Turnover at one rebalance = 0.5 * sum |w_new - w_old| (one-way trading).
    Annual turnover = average per-rebalance turnover * rebalances_per_year.
    """
    if len(weights_by_date) < 2:
        return 0.0
    dates = sorted(weights_by_date)
    deltas = []
    for prev, curr in zip(dates[:-1], dates[1:]):
        keys = set(weights_by_date[prev]) | set(weights_by_date[curr])
        d = sum(abs(weights_by_date[curr].get(k, 0.0)
                    - weights_by_date[prev].get(k, 0.0)) for k in keys)
        deltas.append(0.5 * d)
    avg = float(np.mean(deltas))
    return avg * rebalances_per_year


def _portfolio_waci(
    final_weights: Dict[str, float],
    holdings: pd.DataFrame,
) -> Tuple[float, int]:
    """Weighted-average carbon intensity.

    Skip names whose `carbon_intensity` is BLANK (NaN) in the holdings file,
    renormalise the remaining weights, and compute the weighted average.
    Returns (waci, n_skipped) where n_skipped counts the names dropped for
    missing data only — not names the optimizer chose to weight at zero.
    """
    df = holdings.set_index("ticker")[["carbon_intensity"]].copy()
    df["weight"] = pd.Series(final_weights)
    df["weight"] = df["weight"].fillna(0.0)
    # Count rows where the carbon column is blank AMONG the held names.
    held = df[df["weight"] > 0]
    n_skipped = int(held["carbon_intensity"].isna().sum())
    # Now drop the blank-carbon rows and compute WACI over the rest.
    df = df.dropna(subset=["carbon_intensity"])
    if df["weight"].sum() == 0:
        return float("nan"), n_skipped
    waci = float((df["weight"] * df["carbon_intensity"]).sum() / df["weight"].sum())
    return waci, n_skipped


def compute_metrics(
    result: BacktestResult,
    holdings: pd.DataFrame,
) -> Dict[str, float]:
    """Distil a BacktestResult into the comparison-table metrics.

    Output dict keys (match the column list in build spec sec. 7):
      cumulative_return, cagr, ann_vol, sharpe, sortino, max_drawdown,
      annual_turnover, tracking_error, waci, n_oos_days, n_failed_rebal,
      n_waci_skipped.
    """
    p = result.portfolio_returns
    b = result.benchmark_returns
    if p.empty:
        return {
            "cumulative_return": float("nan"),
            "cagr": float("nan"),
            "ann_vol": float("nan"),
            "sharpe": float("nan"),
            "sortino": float("nan"),
            "max_drawdown": float("nan"),
            "annual_turnover": float("nan"),
            "tracking_error": float("nan"),
            "waci": float("nan"),
            "n_oos_days": 0,
            "n_failed_rebal": len(result.failed_dates),
            "n_waci_skipped": 0,
        }

    ann = config.TRADING_DAYS_PER_YEAR
    rf_daily = config.RISK_FREE_RATE / ann

    equity = (1.0 + p).cumprod()
    cumret = float(equity.iloc[-1] - 1.0)
    cagr = float(equity.iloc[-1] ** (ann / len(p)) - 1.0)
    ann_vol = float(p.std() * np.sqrt(ann))
    excess = p - rf_daily
    sharpe = float(excess.mean() / p.std() * np.sqrt(ann)) if p.std() > 0 else float("nan")
    downside = p[p < 0]
    sortino = (float(excess.mean() / downside.std() * np.sqrt(ann))
               if not downside.empty and downside.std() > 0 else float("nan"))
    mdd = _max_drawdown(equity)

    rebal_per_year = {"annual": 1, "quarterly": 4, "monthly": 12}[
        config.REBALANCE_FREQUENCY
    ]
    turnover = _annual_turnover(result.weights_by_date, rebal_per_year)

    # Tracking error: annualised stdev of (portfolio - benchmark) daily.
    aligned = pd.concat([p, b], axis=1, keys=["p", "b"]).dropna()
    te = float((aligned["p"] - aligned["b"]).std() * np.sqrt(ann))

    # WACI uses the FINAL weights (last rebalance), per build spec.
    last_date = max(result.weights_by_date)
    waci, n_skipped = _portfolio_waci(result.weights_by_date[last_date], holdings)

    return {
        "cumulative_return": cumret,
        "cagr": cagr,
        "ann_vol": ann_vol,
        "sharpe": sharpe,
        "sortino": sortino,
        "max_drawdown": mdd,
        "annual_turnover": turnover,
        "tracking_error": te,
        "waci": waci,
        "n_oos_days": int(len(p)),
        "n_failed_rebal": len(result.failed_dates),
        "n_waci_skipped": n_skipped,
    }


# ---------------------------------------------------------------------------
# Top-level: run ALL methods, return a tidy dict-of-results
# ---------------------------------------------------------------------------
def run_all(
    prices: pd.DataFrame,
    benchmark: pd.Series,
    holdings: pd.DataFrame,
    sector_map: Dict[str, str],
    methods: Optional[List[str]] = None,
) -> Dict[str, BacktestResult]:
    """Run the walk-forward backtest for every method in optimizers.METHODS.

    Returns `{method_name: BacktestResult}`. Failures inside a single method
    do not stop the others — each is independent.
    """
    methods = methods or list(optimizers.METHODS)
    results: Dict[str, BacktestResult] = {}
    for m in methods:
        try:
            results[m] = backtest_method(
                m, prices, benchmark, holdings, sector_map
            )
        except Exception as exc:
            print(f"  [WARN] backtest_method('{m}') crashed: {exc}")
            results[m] = BacktestResult(method=m)
    return results


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
def _self_test() -> int:
    """`python backtester.py` runs the full multi-method backtest end-to-end.

    Prints a compact metrics table. Does not write any files — that's the
    job of run_pipeline.py.
    """
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    import data_loader
    print("=" * 70)
    print("backtester.py - self-test")
    print("=" * 70)

    holdings = data_loader.load_holdings()
    sector_map = data_loader.build_group_maps(holdings)
    prices, bench, fetched = data_loader.download_prices(
        holdings["ticker"].tolist()
    )
    print(f"  Prices: {prices.shape[0]} days, {prices.shape[1]} tickers, "
          f"fetched at {fetched}")
    print(f"  Estimation window: {config.ESTIMATION_WINDOW_YEARS}y, "
          f"rebalance: {config.REBALANCE_FREQUENCY}")
    print()

    results = run_all(prices, bench, holdings, sector_map)

    print()
    print(f"{'method':<18s}  {'cumret':>8s}  {'cagr':>7s}  {'vol':>7s}  "
          f"{'sharpe':>7s}  {'sortino':>7s}  {'maxdd':>7s}  "
          f"{'turn':>6s}  {'te':>6s}  {'waci':>8s}  {'days':>5s}  fail")
    print("-" * 110)
    for m, res in results.items():
        met = compute_metrics(res, holdings)
        print(f"{m:<18s}  "
              f"{met['cumulative_return']:>7.2%}  "
              f"{met['cagr']:>6.2%}  "
              f"{met['ann_vol']:>6.2%}  "
              f"{met['sharpe']:>7.2f}  "
              f"{met['sortino']:>7.2f}  "
              f"{met['max_drawdown']:>7.2%}  "
              f"{met['annual_turnover']:>5.2%}  "
              f"{met['tracking_error']:>5.2%}  "
              f"{met['waci']:>8.1f}  "
              f"{met['n_oos_days']:>5d}  "
              f"{met['n_failed_rebal']:>3d}")
    print("=" * 70)
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(_self_test())
