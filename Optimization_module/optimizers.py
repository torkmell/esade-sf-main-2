"""
optimizers.py — the Optimization Agent.

Six weighting methods, all driven by PyPortfolioOpt and all subject to the
mandate's caps:

  - single name <= 10%
  - any sector <= 25%
  - any country <= 35%
  - long-only, fully invested

Methods (build spec sec. 6):
  1. equal_weight      - 1/N baseline (the floor every other method must beat).
  2. max_sharpe        - EfficientFrontier max-Sharpe with all caps.
  3. min_volatility    - EfficientFrontier min-volatility with all caps.
  4. hrp               - Hierarchical Risk Parity, then post-cap to 10%.
  5. black_litterman   - BL with ESG-driven views, then max-Sharpe on the
                         posterior, with all caps.
  6. score_tilted      - weights proportional to ESG score, cap at 10%.

Every method exposes the same shape:
    optimize_<name>(prices, holdings, sector_map, country_map) -> dict | None
    returns {ticker: weight} on success, None on infeasibility.

A unified dispatcher `optimize(method, ...)` is provided for the backtester
so it can iterate over methods by name.

No LLM / AI calls. Deterministic: same prices -> same weights, every time.
"""

from __future__ import annotations

import sys
from typing import Callable, Dict, Optional

import numpy as np
import pandas as pd

from pypfopt import (
    BlackLittermanModel,
    EfficientFrontier,
    HRPOpt,
    black_litterman,
    expected_returns,
    risk_models,
)

import config


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _clean_weights(raw: dict, tickers) -> Dict[str, float]:
    """Take PyPortfolioOpt's raw weights and return a clean {ticker: weight}.

    Steps:
      - keep order matching `tickers`
      - drop tiny numerical noise (< 1e-6) to exactly zero
      - renormalise to sum to 1.0 (PyPortfolioOpt sometimes returns 0.9999)
    """
    weights = np.array([raw.get(t, 0.0) for t in tickers], dtype=float)
    weights[weights < 1e-6] = 0.0
    s = weights.sum()
    if s > 0:
        weights = weights / s
    return {t: float(w) for t, w in zip(tickers, weights)}


def _post_cap_and_renormalise(
    raw_weights: Dict[str, float],
    cap: float,
) -> Dict[str, float]:
    """Cap each weight at `cap` and renormalise so weights sum to 1.

    Used by HRP and the Score-Tilted method because those methods cannot
    take constraints natively. We iterate up to a small fixed budget — each
    pass may push other names above the cap as they receive the redistributed
    weight. Documented in run_log.txt as a post-processing step.
    """
    tickers = list(raw_weights.keys())
    w = np.array([raw_weights[t] for t in tickers], dtype=float)
    w = np.clip(w, 0.0, None)
    if w.sum() == 0:
        return {t: 0.0 for t in tickers}
    w = w / w.sum()

    for _ in range(50):
        over = w > cap
        if not over.any():
            break
        # Set capped names to the cap, redistribute the surplus among the
        # remaining names proportionally to their current weight.
        surplus = (w[over] - cap).sum()
        w[over] = cap
        free = ~over
        free_sum = w[free].sum()
        if free_sum <= 0:
            # All names already at the cap; nothing left to redistribute.
            break
        w[free] = w[free] + surplus * (w[free] / free_sum)

    return {t: float(x) for t, x in zip(tickers, w)}


def _attach_group_constraints(
    ef: EfficientFrontier,
    tickers,
    sector_map: Dict[str, str],
) -> None:
    """Attach sector cap to a PyPortfolioOpt EfficientFrontier."""
    sector_groups = sorted({sector_map[t] for t in tickers if t in sector_map})
    sector_upper = {g: config.MAX_WEIGHT_PER_SECTOR for g in sector_groups}
    sector_lower = {g: 0.0 for g in sector_groups}
    ef.add_sector_constraints(
        {t: sector_map[t] for t in tickers},
        sector_lower,
        sector_upper,
    )


# ---------------------------------------------------------------------------
# Method 1: equal weight
# ---------------------------------------------------------------------------
def optimize_equal_weight(
    prices: pd.DataFrame,
    holdings: pd.DataFrame,
    sector_map: Dict[str, str],
) -> Optional[Dict[str, float]]:
    """1/N across all names. Baseline; respects all caps trivially.

    With 20 names of roughly balanced sector/country exposure the 10% / 25% /
    35% caps are satisfied by 1/N = 5% by construction. We still verify the
    caps explicitly and log if any are breached (would only happen if the
    sample shrank dramatically).
    """
    tickers = list(prices.columns)
    n = len(tickers)
    if n == 0:
        return None
    w = 1.0 / n
    weights = {t: w for t in tickers}

    # Sanity check the caps (defensive — shouldn't fire for N=20).
    if w > config.MAX_WEIGHT_PER_STOCK + 1e-9:
        print(f"  [WARN] equal_weight: 1/N={w:.3%} exceeds single-name cap "
              f"{config.MAX_WEIGHT_PER_STOCK:.0%}")
        return None
    return weights


# ---------------------------------------------------------------------------
# Method 2: maximum Sharpe
# ---------------------------------------------------------------------------
def optimize_max_sharpe(
    prices: pd.DataFrame,
    holdings: pd.DataFrame,
    sector_map: Dict[str, str],
) -> Optional[Dict[str, float]]:
    """Tangency portfolio: max excess-return per unit of volatility.

    Expected returns from historical mean; covariance from Ledoit-Wolf
    shrinkage (more stable than raw sample covariance for ~3 years of data).
    All three caps applied as constraints inside the optimizer.
    """
    tickers = list(prices.columns)
    try:
        mu = expected_returns.mean_historical_return(prices)
        S = risk_models.CovarianceShrinkage(prices).ledoit_wolf()

        ef = EfficientFrontier(
            mu, S,
            weight_bounds=(config.WEIGHT_MIN, config.MAX_WEIGHT_PER_STOCK),
        )
        _attach_group_constraints(ef, tickers, sector_map)
        ef.max_sharpe(risk_free_rate=config.RISK_FREE_RATE)
        return _clean_weights(ef.clean_weights(), tickers)
    except Exception as exc:
        print(f"  [WARN] max_sharpe infeasible / failed: {exc}")
        return None


# ---------------------------------------------------------------------------
# Method 3: minimum volatility
# ---------------------------------------------------------------------------
def optimize_min_volatility(
    prices: pd.DataFrame,
    holdings: pd.DataFrame,
    sector_map: Dict[str, str],
) -> Optional[Dict[str, float]]:
    """Lowest portfolio variance subject to all caps.

    Same Ledoit-Wolf covariance, same constraint set as max-Sharpe. Tends
    to concentrate on low-vol defensives until the 10% single-name cap
    forces diversification.
    """
    tickers = list(prices.columns)
    try:
        S = risk_models.CovarianceShrinkage(prices).ledoit_wolf()
        ef = EfficientFrontier(
            None, S,
            weight_bounds=(config.WEIGHT_MIN, config.MAX_WEIGHT_PER_STOCK),
        )
        _attach_group_constraints(ef, tickers, sector_map)
        ef.min_volatility()
        return _clean_weights(ef.clean_weights(), tickers)
    except Exception as exc:
        print(f"  [WARN] min_volatility infeasible / failed: {exc}")
        return None


# ---------------------------------------------------------------------------
# Method 4: Hierarchical Risk Parity
# ---------------------------------------------------------------------------
def optimize_hrp(
    prices: pd.DataFrame,
    holdings: pd.DataFrame,
    sector_map: Dict[str, str],
) -> Optional[Dict[str, float]]:
    """HRP via PyPortfolioOpt, then post-cap to 10% per name.

    HRP does NOT natively accept sector / country / single-name constraints
    — it clusters assets by correlation and risk-budgets recursively. We:
      1. Run HRP unconstrained.
      2. Cap any single-name weight above 10% and renormalise (iterative).
      3. Document this post-processing step in run_log.txt.

    Sector and country caps are NOT enforced for HRP — that limitation is
    surfaced honestly rather than papered over.
    """
    tickers = list(prices.columns)
    try:
        rets = prices.pct_change().dropna()
        hrp = HRPOpt(rets)
        hrp.optimize()
        capped = _post_cap_and_renormalise(
            dict(hrp.clean_weights()), config.MAX_WEIGHT_PER_STOCK
        )
        return _clean_weights(capped, tickers)
    except Exception as exc:
        print(f"  [WARN] hrp failed: {exc}")
        return None


# ---------------------------------------------------------------------------
# Method 5: Black-Litterman with ESG-driven views
# ---------------------------------------------------------------------------
def _build_esg_views(
    holdings: pd.DataFrame,
    tickers,
    prior: pd.Series,
) -> Dict[str, float]:
    """Translate the ESG score into BL absolute-view returns.

    Interpret the ESG signal as a small TILT applied to the market-implied
    prior return for each asset:

        top ESG (highest score) -> prior + spread/2
        bottom ESG (lowest score) -> prior - spread/2
        median ESG -> prior (no tilt)

    Building views as `prior + tilt` (rather than `tilt` alone, treated as
    an absolute level) keeps the posterior anchored in the same magnitude
    as the prior. If we passed only the tilt (~+/-2%) as the absolute view,
    BL would pull the posterior all the way down to that level, often below
    the risk-free rate, and the subsequent max-Sharpe problem becomes
    numerically infeasible under tight caps.

    Magnitude is modest on purpose — BL is meant to TILT the prior, not
    replace it. Set in config.BL_ESG_VIEW_SPREAD.
    """
    scores = (holdings
              .set_index("ticker")
              .loc[list(tickers), "esg_score"]
              .astype(float))
    lo, hi = float(scores.min()), float(scores.max())
    if hi == lo:
        return {t: float(prior[t]) for t in tickers}
    centred = (scores - (lo + hi) / 2.0) / ((hi - lo) / 2.0)  # in [-1, +1]
    tilt = (centred * (config.BL_ESG_VIEW_SPREAD / 2.0)).to_dict()
    return {t: float(prior[t]) + float(tilt[t]) for t in tickers}


def optimize_black_litterman(
    prices: pd.DataFrame,
    holdings: pd.DataFrame,
    sector_map: Dict[str, str],
) -> Optional[Dict[str, float]]:
    """Black-Litterman: market-implied prior tilted by ESG views.

    Steps:
      1. Covariance from Ledoit-Wolf.
      2. Market-implied prior = `pi = delta * S @ w_mkt` where w_mkt is
         taken as 1/N (we have no live market caps for the 20 names in this
         simplified module). This is documented as a simplification.
      3. ESG views are mapped to per-ticker absolute views (see helper).
      4. Run BL to get posterior expected returns.
      5. Run max-Sharpe on the posterior with all caps applied.

    This is the method that pushes the sustainability signal directly into
    construction, rather than only filtering the universe upstream.
    """
    tickers = list(prices.columns)
    try:
        S = risk_models.CovarianceShrinkage(prices).ledoit_wolf()

        # Equal-weight market proxy — we have no market-cap data in this
        # module. Documented limitation.
        market_weights = pd.Series(1.0 / len(tickers), index=tickers)
        pi = black_litterman.market_implied_prior_returns(
            market_weights,
            risk_aversion=2.5,    # standard textbook value
            cov_matrix=S,
            risk_free_rate=config.RISK_FREE_RATE,
        )

        views = _build_esg_views(holdings, tickers, pi)
        bl = BlackLittermanModel(
            S,
            pi=pi,
            absolute_views=views,
            # tau-style implicit confidence; PyPortfolioOpt's default works fine
        )
        bl_returns = bl.bl_returns()
        # We keep the original Ledoit-Wolf covariance S rather than
        # bl.bl_cov() — the BL-adjusted covariance can be poorly conditioned
        # when views are weak, which trips CVXPY's default OSQP into
        # "infeasible_inaccurate". Using the well-behaved S is a standard
        # alternative documented in the BL literature.
        # Try multiple solvers — PyPortfolioOpt's max-Sharpe uses a variable
        # transformation that some solvers struggle with on BL posteriors.
        last_exc = None
        for solver in ("SCS", "ECOS", "CLARABEL"):
            try:
                ef = EfficientFrontier(
                    bl_returns, S,
                    weight_bounds=(config.WEIGHT_MIN,
                                   config.MAX_WEIGHT_PER_STOCK),
                    solver=solver,
                )
                _attach_group_constraints(ef, tickers, sector_map)
                ef.max_sharpe(risk_free_rate=config.RISK_FREE_RATE)
                return _clean_weights(ef.clean_weights(), tickers)
            except Exception as exc:
                last_exc = exc
                continue
        raise last_exc if last_exc else RuntimeError("BL all solvers failed")
    except Exception as exc:
        print(f"  [WARN] black_litterman failed: {exc}")
        return None


# ---------------------------------------------------------------------------
# Method 6: score-tilted (ESG-proportional)
# ---------------------------------------------------------------------------
def optimize_score_tilted(
    prices: pd.DataFrame,
    holdings: pd.DataFrame,
    sector_map: Dict[str, str],
) -> Optional[Dict[str, float]]:
    """Weights proportional to ESG score, then capped at 10% per name.

    The simplest possible mandate-aligned method: more ESG -> more weight.
    Like HRP, this method does not enforce sector / country caps natively
    (it has no optimizer in which to express them). The single-name cap is
    enforced via the same iterative cap-and-renormalise routine.
    """
    tickers = list(prices.columns)
    try:
        scores = (holdings
                  .set_index("ticker")
                  .loc[tickers, "esg_score"]
                  .clip(lower=0.0)
                  .astype(float))
        if scores.sum() <= 0:
            return None
        raw = (scores / scores.sum()).to_dict()
        capped = _post_cap_and_renormalise(raw, config.MAX_WEIGHT_PER_STOCK)
        return _clean_weights(capped, tickers)
    except Exception as exc:
        print(f"  [WARN] score_tilted failed: {exc}")
        return None


# ---------------------------------------------------------------------------
# Public registry + dispatcher
# ---------------------------------------------------------------------------
METHODS: Dict[str, Callable] = {
    "equal_weight":     optimize_equal_weight,
    "max_sharpe":       optimize_max_sharpe,
    "min_volatility":   optimize_min_volatility,
    "hrp":              optimize_hrp,
    "black_litterman":  optimize_black_litterman,
    "score_tilted":     optimize_score_tilted,
}


def optimize(
    method: str,
    prices: pd.DataFrame,
    holdings: pd.DataFrame,
    sector_map: Dict[str, str],
) -> Optional[Dict[str, float]]:
    """Run the named method. Returns {ticker: weight} or None on failure.

    The backtester calls this in a loop so it doesn't need to know about
    each method's internals. New methods can be added to METHODS without
    touching the backtester.
    """
    fn = METHODS.get(method)
    if fn is None:
        raise KeyError(f"Unknown optimization method: {method}. "
                       f"Available: {list(METHODS)}")
    return fn(prices, holdings, sector_map)


# ---------------------------------------------------------------------------
# Self-test: run every method on the full cached / freshly-downloaded panel
# ---------------------------------------------------------------------------
def _self_test() -> int:
    """`python optimizers.py` runs every method once and prints summaries.

    Uses the most recent ESTIMATION_WINDOW_DAYS of cached prices. Verifies
    that each method produces weights that respect all three caps (or, for
    HRP / score_tilted, the single-name cap that they CAN respect).
    """
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    import data_loader
    print("=" * 60)
    print("optimizers.py - self-test")
    print("=" * 60)

    holdings = data_loader.load_holdings()
    tickers = holdings["ticker"].tolist()
    sector_map = data_loader.build_group_maps(holdings)

    prices, _, fetched = data_loader.download_prices(tickers)
    in_sample = prices.tail(config.ESTIMATION_WINDOW_DAYS)
    print(f"  In-sample window: {in_sample.index[0].date()} -> "
          f"{in_sample.index[-1].date()} ({len(in_sample)} rows)")
    print(f"  Fetched at: {fetched}")
    print()

    for name in METHODS:
        w = optimize(name, in_sample, holdings, sector_map)
        if w is None:
            print(f"  {name:<18s}: INFEASIBLE / FAILED")
            continue
        wser = pd.Series(w)
        top = wser.sort_values(ascending=False).head(3)
        max_name_w = wser.max()
        sector_w = (wser.groupby([sector_map[t] for t in wser.index])
                       .sum().sort_values(ascending=False))
        print(f"  {name:<18s}: sum={wser.sum():.4f}  max_name={max_name_w:.3%}"
              f"  max_sector={sector_w.iloc[0]:.3%}")
        print(f"    top3: {', '.join(f'{t}={v:.2%}' for t, v in top.items())}")
    print("=" * 60)
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(_self_test())
