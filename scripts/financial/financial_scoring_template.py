"""
financial_scoring_template.py
-------------------------------
Reads the financial_metrics CSV produced by agent10_financial_analysis.ipynb
and generates an enriched scoring summary for portfolio review.

Input:
  /outputs/scores/financial_metrics_{date}.csv   (produced by NB04)

Output:
  /data/financial/calculated_metrics/financial_scores_{date}.csv

Scoring model — four metrics, percentile-ranked:
  M-01 Annualised Volatility  (20%) — inverse percentile; lower vol = higher score
  M-02 Maximum Drawdown       (30%) — inverse percentile; shallower = higher score
  M-03 Sharpe Ratio           (30%) — normal percentile;  higher Sharpe = higher score
  M-04 Beta Band Score        (20%) — band score already computed in NB04

Composite = 0.20 x M01 + 0.30 x M02 + 0.30 x M03 + 0.20 x M04

NaN handling:
  - Percentile ranking uses na_option="keep" — NaN stays NaN in individual scores.
  - Composite uses median imputation for missing metrics (not zero) to avoid
    penalising data gaps as confirmed poor performance.
  - metric_nan_count column tracks completeness per stock.
  - Stocks with financial_verdict == REVIEW_REQUIRED are flagged but NOT excluded.

IMPORTANT: Percentile scores are computed over the PASSED universe only
(excludes hard-excluded stocks from the ranking pool). This prevents excluded
stocks from dilating the percentile distribution of the eligible set upward.

Dependencies:
  pip install pandas numpy

Run manually only.
"""

import os, glob
import numpy as np
import pandas as pd
from datetime import date

ROOT       = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCORES_DIR = os.path.join(ROOT, "outputs", "scores")
OUTPUT_DIR = os.path.join(ROOT, "data", "financial", "calculated_metrics")
os.makedirs(OUTPUT_DIR, exist_ok=True)
TODAY = date.today().isoformat()

# Composite weights — must match NB04
WEIGHTS = {"m01": 0.20, "m02": 0.30, "m03": 0.30, "m04": 0.20}
assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9, "Weights must sum to 1.0"

RF_ANNUAL = 0.025  # documented — matches NB04

# ── Load NB04 output ──────────────────────────────────────────────────────────
fin_files = sorted(glob.glob(os.path.join(SCORES_DIR, "financial_metrics_*.csv")))
if not fin_files:
    raise FileNotFoundError(
        f"No financial_metrics CSV found in {SCORES_DIR}.\n"
        "Run agent10_financial_analysis.ipynb first."
    )

df = pd.read_csv(fin_files[-1])
print(f"Loaded: {fin_files[-1]}  ({len(df)} rows)")

# ── Validate required columns ─────────────────────────────────────────────────
REQUIRED = [
    "ticker", "vol_annual", "max_drawdown", "sharpe_ratio",
    "beta_band_score", "financial_verdict",
]
missing_cols = [c for c in REQUIRED if c not in df.columns]
if missing_cols:
    raise ValueError(
        f"Missing columns in financial_metrics file: {missing_cols}\n"
        "Ensure agent10_financial_analysis.ipynb was run with the 2-stage architecture.\n"
        "Old 5-pillar schema is not compatible with this script."
    )

# ── Percentile ranking helper ─────────────────────────────────────────────────
def pct_rank(series, invert=False):
    ranks = series.rank(pct=True, na_option="keep") * 100
    return (100 - ranks) if invert else ranks

# ── Compute scores on passed universe only ────────────────────────────────────
# Excluded stocks are NOT included in the ranking pool — their presence would
# dilate the percentile distribution of the eligible set upward artificially.
passed_mask  = df["financial_verdict"].isin(["PASSED", "REVIEW_REQUIRED"])
ranked_df    = df[passed_mask].copy()
review_count = (df["financial_verdict"] == "REVIEW_REQUIRED").sum()
passed_count = passed_mask.sum() - review_count

print(f"Ranking universe: {len(ranked_df)} stocks "
      f"(PASSED={passed_count}, REVIEW_REQUIRED={review_count})")

ranked_df["m01_score"] = pct_rank(ranked_df["vol_annual"],    invert=True)
ranked_df["m02_score"] = pct_rank(ranked_df["max_drawdown"],  invert=True)
ranked_df["m03_score"] = pct_rank(ranked_df["sharpe_ratio"],  invert=False)

# M04: beta_band_score already computed in NB04 (0/25/50/75/100/NaN)
ranked_df["m04_score"] = pd.to_numeric(ranked_df["beta_band_score"], errors="coerce")

# Composite with median imputation for missing metrics
m01_med = ranked_df["m01_score"].median()
m02_med = ranked_df["m02_score"].median()
m03_med = ranked_df["m03_score"].median()
m04_med = ranked_df["m04_score"].median()

ranked_df["composite_financial_score"] = (
    ranked_df["m01_score"].fillna(m01_med) * WEIGHTS["m01"] +
    ranked_df["m02_score"].fillna(m02_med) * WEIGHTS["m02"] +
    ranked_df["m03_score"].fillna(m03_med) * WEIGHTS["m03"] +
    ranked_df["m04_score"].fillna(m04_med) * WEIGHTS["m04"]
).round(2)

ranked_df["metric_nan_count"] = (
    ranked_df["m01_score"].isna().astype(int) +
    ranked_df["m02_score"].isna().astype(int) +
    ranked_df["m03_score"].isna().astype(int) +
    ranked_df["m04_score"].isna().astype(int)
)

# ── Risk flag ─────────────────────────────────────────────────────────────────
def risk_flag(row):
    vol = row.get("vol_annual")
    sr  = row.get("sharpe_ratio")
    if pd.isna(vol) and pd.isna(sr):
        return "UNKNOWN"
    if (not pd.isna(vol) and vol > 0.35) or (not pd.isna(sr) and sr < 0.2):
        return "HIGH"
    if (not pd.isna(vol) and vol < 0.20) and (not pd.isna(sr) and sr > 0.5):
        return "LOW"
    return "MEDIUM"

ranked_df["financial_risk_flag"] = ranked_df.apply(risk_flag, axis=1)

# ── Data confidence ────────────────────────────────────────────────────────────
def confidence(row):
    if row.get("financial_verdict") == "REVIEW_REQUIRED":
        return "LOW"
    mc = row.get("metric_nan_count", 0)
    if mc == 0:
        return "HIGH"
    if mc <= 1:
        return "MEDIUM"
    return "LOW"

ranked_df["data_confidence"] = ranked_df.apply(confidence, axis=1)

ranked_df["human_review_required"] = (
    (ranked_df["financial_verdict"] == "REVIEW_REQUIRED") |
    (ranked_df["metric_nan_count"]  > 0) |
    (ranked_df["financial_risk_flag"] == "HIGH")
)

ranked_df["calculation_date"]    = TODAY
ranked_df["rf_rate_used"]        = RF_ANNUAL
ranked_df["composite_weights"]   = "M01:0.20 M02:0.30 M03:0.30 M04:0.20"

# ── Output columns ─────────────────────────────────────────────────────────────
output_cols = [
    "ticker", "financial_verdict",
    "vol_annual", "max_drawdown", "sharpe_ratio", "beta",
    # Legacy alias columns — backward compatibility with downstream consumers
    "annual_volatility_pct", "max_drawdown_pct", "beta_vs_benchmark",
    "m01_score", "m02_score", "m03_score", "m04_score",
    "composite_financial_score", "metric_nan_count",
    "m01_vol_flag", "m02_mdd_flag", "m03_sharpe_flag", "m04_beta_flag",
    "financial_risk_flag", "data_confidence", "human_review_required",
    "calculation_date", "rf_rate_used", "composite_weights",
]
output_cols = [c for c in output_cols if c in ranked_df.columns]
out = ranked_df[output_cols]

# ── Save ───────────────────────────────────────────────────────────────────────
out_path = os.path.join(OUTPUT_DIR, f"financial_scores_{TODAY}.csv")
out.to_csv(out_path, index=False)
print(f"\nSaved: {out_path}")
print(f"\nTop 15 by composite score:")
print(out.nlargest(15, "composite_financial_score")[
    ["ticker", "composite_financial_score", "financial_risk_flag", "data_confidence", "financial_verdict"]
].to_string(index=False))

print(f"\nScore distribution:")
print(out["composite_financial_score"].describe().round(2))

print(f"\nRisk flags : {out['financial_risk_flag'].value_counts().to_dict()}")
print(f"Confidence : {out['data_confidence'].value_counts().to_dict()}")
print(f"Human review required: {out['human_review_required'].sum()} of {len(out)} stocks")

print("\nNOTE: Percentile scores are relative to the PASSED universe only (excluded stocks removed from ranking pool).")
print("      REVIEW_REQUIRED stocks are included but flagged for human review.")
print("      Score is a ranking tool, not investment advice. Human review required before any portfolio decision.")
