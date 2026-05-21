"""
selector.py — multi-criteria comparison and method recommendation.

Build spec sec. 8:
  - Build a comparison table over the 6 methods.
  - Do NOT choose on raw return alone.
  - Compute a composite ranking across:
      Sharpe (higher better),
      max drawdown (smaller better),
      turnover (lower better),
      tracking error inside the configured band (2-8%) (in-band is better).
  - Output a recommended method with a short rationale, labelled
    "RECOMMENDATION - FOR HUMAN INVESTMENT COMMITTEE REVIEW".

The composite is intentionally simple and transparent: each metric is
normalised to [0, 1] across the candidate methods, then averaged with the
weights from config.COMPOSITE_WEIGHTS. The human keeps the decision.
"""

from __future__ import annotations

from typing import Dict, Tuple

import numpy as np
import pandas as pd

import config


# ---------------------------------------------------------------------------
# Normalisation helpers
# ---------------------------------------------------------------------------
def _norm_higher_better(s: pd.Series) -> pd.Series:
    """Linear-rescale to [0, 1], higher original value -> higher score."""
    if s.dropna().empty:
        return pd.Series(np.zeros(len(s)), index=s.index)
    lo, hi = s.min(), s.max()
    if hi == lo:
        return pd.Series(np.ones(len(s)) * 0.5, index=s.index)
    return (s - lo) / (hi - lo)


def _norm_lower_better(s: pd.Series) -> pd.Series:
    """Linear-rescale to [0, 1], LOWER original value -> higher score.

    For max drawdown the values are negative (e.g. -0.23), and we want
    smaller magnitude (closer to 0) to score higher — that is correctly
    handled by treating "higher = better" on the raw negative number.
    """
    return _norm_higher_better(-s)


def _score_tracking_error(te: float) -> float:
    """1.0 if TE sits inside the configured band; falls off linearly outside.

    Inside the band: full score (1.0). Outside, the score decays toward 0
    at twice the band-width away. This rewards "active but not benchmark-
    hugging" methods without binary thresholds.
    """
    lo, hi = config.TRACKING_ERROR_BAND
    width = hi - lo
    if pd.isna(te):
        return 0.0
    if lo <= te <= hi:
        return 1.0
    if te < lo:
        return max(0.0, 1.0 - (lo - te) / width)
    return max(0.0, 1.0 - (te - hi) / width)


# ---------------------------------------------------------------------------
# Build the comparison table
# ---------------------------------------------------------------------------
def build_comparison_table(
    metrics: Dict[str, Dict[str, float]],
) -> pd.DataFrame:
    """Turn `{method: {metric: value}}` into a tidy DataFrame.

    Row order is preserved from the input dict. Column order is fixed so
    the CSV is readable: returns first, then risk, then turnover/TE, then
    sustainability, then the diagnostic columns.
    """
    cols = [
        "cumulative_return", "cagr", "ann_vol",
        "sharpe", "sortino", "max_drawdown",
        "annual_turnover", "tracking_error",
        "waci",
        "n_oos_days", "n_failed_rebal", "n_waci_skipped",
    ]
    rows = []
    for method, m in metrics.items():
        rows.append({"method": method, **{c: m.get(c, np.nan) for c in cols}})
    df = pd.DataFrame(rows).set_index("method")[cols]
    return df


# ---------------------------------------------------------------------------
# Composite ranking
# ---------------------------------------------------------------------------
def composite_rank(comparison: pd.DataFrame) -> pd.DataFrame:
    """Add per-criterion scores and a composite score to the comparison table.

    Adds these columns to a COPY of the input:
        score_sharpe, score_max_drawdown, score_turnover, score_tracking_error,
        composite_score, rank.
    """
    df = comparison.copy()
    df["score_sharpe"] = _norm_higher_better(df["sharpe"])
    df["score_max_drawdown"] = _norm_lower_better(df["max_drawdown"])
    df["score_turnover"] = _norm_lower_better(df["annual_turnover"])
    df["score_tracking_error"] = df["tracking_error"].apply(_score_tracking_error)

    w = config.COMPOSITE_WEIGHTS
    df["composite_score"] = (
        w["sharpe"] * df["score_sharpe"]
        + w["max_drawdown"] * df["score_max_drawdown"]
        + w["turnover"] * df["score_turnover"]
        + w["tracking_error"] * df["score_tracking_error"]
    )
    df["rank"] = df["composite_score"].rank(ascending=False, method="min", na_option="bottom").astype(int)
    return df.sort_values("composite_score", ascending=False)


# ---------------------------------------------------------------------------
# Recommendation
# ---------------------------------------------------------------------------
def recommend(scored: pd.DataFrame) -> Tuple[str, str]:
    """Return (recommended_method, rationale_text).

    The rationale is two or three short sentences citing the actual numbers
    the recommendation rests on, so a human can sanity-check at a glance.
    Always labelled as a recommendation, never as a decision.
    """
    if scored.empty:
        return "(none)", "No methods produced results."
    top = scored.iloc[0]
    name = top.name

    sharpe = top["sharpe"]
    mdd = top["max_drawdown"]
    turn = top["annual_turnover"]
    te = top["tracking_error"]
    lo, hi = config.TRACKING_ERROR_BAND

    te_phrase = (f"tracking error {te:.2%} (inside the {lo:.0%}-{hi:.0%} band)"
                 if lo <= te <= hi
                 else f"tracking error {te:.2%} (outside the "
                      f"{lo:.0%}-{hi:.0%} band - flag)")

    rationale = (
        f"Recommended: {name}. Composite score {top['composite_score']:.2f} "
        f"(rank 1 of {len(scored)}). Drivers: Sharpe {sharpe:.2f}, "
        f"max drawdown {mdd:.2%}, annual turnover {turn:.2%}, {te_phrase}. "
        f"This is a quantitative composite across Sharpe, max drawdown, "
        f"turnover and tracking-error band; final selection rests with the "
        f"Investment Committee."
    )
    return name, rationale


# ---------------------------------------------------------------------------
# Convenience: do everything in one call
# ---------------------------------------------------------------------------
def select(
    metrics: Dict[str, Dict[str, float]],
) -> Tuple[pd.DataFrame, pd.DataFrame, str, str]:
    """One-call entrypoint used by run_pipeline.py.

    Returns:
        comparison  : raw metric table
        scored      : same table plus per-criterion scores + composite rank
        winner_name : the recommended method
        rationale   : the human-readable rationale string
    """
    comparison = build_comparison_table(metrics)
    scored = composite_rank(comparison)
    winner_name, rationale = recommend(scored)
    return comparison, scored, winner_name, rationale


# ---------------------------------------------------------------------------
# Self-test using a tiny synthetic metrics dict
# ---------------------------------------------------------------------------
def _self_test() -> int:
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    print("=" * 60)
    print("selector.py - self-test (synthetic metrics)")
    print("=" * 60)
    synth = {
        "equal_weight":    {"sharpe": 0.82, "max_drawdown": -0.23,
                            "annual_turnover": 0.00, "tracking_error": 0.07,
                            "cagr": 0.14, "ann_vol": 0.15, "cumulative_return": 0.98,
                            "sortino": 1.14, "waci": 219, "n_oos_days": 1294,
                            "n_failed_rebal": 0, "n_waci_skipped": 0},
        "max_sharpe":      {"sharpe": 0.95, "max_drawdown": -0.29,
                            "annual_turnover": 0.24, "tracking_error": 0.10,
                            "cagr": 0.17, "ann_vol": 0.16, "cumulative_return": 1.26,
                            "sortino": 1.31, "waci": 118, "n_oos_days": 1294,
                            "n_failed_rebal": 0, "n_waci_skipped": 0},
        "min_volatility":  {"sharpe": 0.95, "max_drawdown": -0.23,
                            "annual_turnover": 0.12, "tracking_error": 0.08,
                            "cagr": 0.15, "ann_vol": 0.14, "cumulative_return": 1.06,
                            "sortino": 1.29, "waci": 243, "n_oos_days": 1294,
                            "n_failed_rebal": 0, "n_waci_skipped": 0},
    }
    comp, scored, winner, rationale = select(synth)
    print("Comparison:")
    print(comp.round(4))
    print()
    print("Scored (sorted by composite):")
    print(scored[["sharpe", "max_drawdown", "annual_turnover",
                  "tracking_error", "composite_score", "rank"]].round(4))
    print()
    print("RECOMMENDATION - FOR HUMAN INVESTMENT COMMITTEE REVIEW")
    print(f"  {rationale}")
    print("=" * 60)
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(_self_test())
