"""
config.py — single source of truth for all parameters.

Every constraint, window, file path, and tunable knob lives here. Other modules
import from this file; they never hard-code these values. Change a number here
and the whole pipeline picks it up on the next run.

The constants are grouped by topic and heavily commented so a non-coder can
read this file and understand exactly what the run is doing.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# 1. Reproducibility
# ---------------------------------------------------------------------------
# Fixed random seed for any stochastic step (none today, but future-proof).
# The whole pipeline is deterministic: same input + same code -> same output.
RANDOM_SEED = 42

# ---------------------------------------------------------------------------
# 2. File paths
# ---------------------------------------------------------------------------
# All paths are resolved relative to the folder this file lives in, so the
# pipeline works no matter where the user invokes it from.
PROJECT_DIR = Path(__file__).resolve().parent

# Input — the human Investment Captain's 20-stock selection.
HOLDINGS_CSV = PROJECT_DIR / "sample_holdings_20.csv"

# Cached price data lives here; re-runs reuse the cache for reproducibility.
DATA_DIR = PROJECT_DIR / "data"

# Every result the pipeline writes lands in this folder.
OUTPUTS_DIR = PROJECT_DIR / "outputs"

# Audit trail (run date, parameters, errors, look-ahead disclosure).
RUN_LOG = OUTPUTS_DIR / "run_log.txt"

# ---------------------------------------------------------------------------
# 3. Mandate constraints (§4 of the build spec)
# ---------------------------------------------------------------------------
# Long-only, fully invested portfolio.
#   weights >= 0, weights sum to 1, no shorting, no leverage.
WEIGHT_MIN = 0.0          # no short positions
WEIGHT_SUM_TARGET = 1.0   # fully invested

# Single-name cap: no stock may exceed 10% of the portfolio.
MAX_WEIGHT_PER_STOCK = 0.10

# Sector cap: no SASB sector may exceed 25% of the portfolio.
# Applied using the `sector` column in the holdings CSV.
MAX_WEIGHT_PER_SECTOR = 0.25

# ---------------------------------------------------------------------------
# 4. Benchmark (§4 of the build spec)
# ---------------------------------------------------------------------------
# The mandate's stated benchmark is STOXX Europe 600 Net-Total-Return.
# A free NTR series is not available on Yahoo Finance, so we proxy with the
# free price-return index "^STOXX". This is a known limitation and is logged
# to run_log.txt and noted in README.md.
BENCHMARK_TICKER = "^STOXX"
BENCHMARK_NAME = "STOXX Europe 600 (price index, Yahoo proxy)"

# ---------------------------------------------------------------------------
# 5. Price-history download (§4 of the build spec)
# ---------------------------------------------------------------------------
# Download the maximum of 8 years of daily prices, in EUR where possible,
# and cache to DATA_DIR. yfinance prices are auto-adjusted (splits/dividends)
# so they are total-return-style on the equity side.
PRICE_HISTORY_YEARS = 8
PRICE_FREQUENCY = "1d"             # daily bars
PRICE_AUTO_ADJUST = True           # adjust for splits/dividends
TRADING_DAYS_PER_YEAR = 252        # annualisation constant for vol/Sharpe etc.

# Short window used by data_loader to verify each ticker actually returns
# data before the long historical download starts. Saves time if a ticker
# is mistyped — fails fast and loudly.
TICKER_VERIFY_DAYS = 30

# ---------------------------------------------------------------------------
# 6. Backtest windows (§7 of the build spec)
# ---------------------------------------------------------------------------
# In-sample / estimation window: how much history we feed the optimizer to
# estimate expected returns and the covariance matrix. 3 years ~ 756 trading
# days. The estimation window and the live measurement window NEVER overlap.
ESTIMATION_WINDOW_YEARS = 3
ESTIMATION_WINDOW_DAYS = ESTIMATION_WINDOW_YEARS * TRADING_DAYS_PER_YEAR

# Rebalance frequency: how often the walk-forward backtest re-runs each
# optimizer and updates weights. Annual by default; exposed here so it can
# be changed without touching backtester.py.
# Valid options: "annual", "quarterly", "monthly".
REBALANCE_FREQUENCY = "annual"

# Risk-free rate used in Sharpe / Black-Litterman. Kept simple and constant
# rather than pulling a live yield series; documented as an assumption.
RISK_FREE_RATE = 0.02   # 2% annual

# ---------------------------------------------------------------------------
# 7. Optimizer-specific parameters (§6 of the build spec)
# ---------------------------------------------------------------------------
# Black-Litterman: how strongly the ESG score moves expected returns away
# from the market-implied prior. We pick a deliberately modest spread so the
# sustainability tilt is meaningful but does not overpower the prior.
# Top ESG name's view = +BL_ESG_VIEW_SPREAD / 2,
# Bottom ESG name's view = -BL_ESG_VIEW_SPREAD / 2, others linearly in between.
BL_ESG_VIEW_SPREAD = 0.04   # 4% top-to-bottom annual excess-return spread
BL_VIEW_CONFIDENCE = 0.50   # tau-style confidence on each ESG view (moderate)

# ---------------------------------------------------------------------------
# 8. Backtest performance / scoring (§7-§8 of the build spec)
# ---------------------------------------------------------------------------
# Tracking-error band used by selector.py when scoring methods. A method
# whose TE sits in this band gets full marks; outside this band it loses
# points. The band reflects an "active but not benchmark-hugging" mandate.
TRACKING_ERROR_BAND = (0.02, 0.08)   # 2% - 8% annualised

# Weights of each criterion in the composite ranking (must sum to 1.0).
# Higher Sharpe is better, smaller max drawdown is better, lower turnover
# is better, tracking error inside the band is better.
COMPOSITE_WEIGHTS = {
    "sharpe":          0.40,
    "max_drawdown":    0.25,
    "turnover":        0.15,
    "tracking_error":  0.20,
}

# ---------------------------------------------------------------------------
# 9. The look-ahead disclosure (§7 of the build spec — required verbatim)
# ---------------------------------------------------------------------------
# This sentence MUST appear, unchanged, in run_log.txt and README.md.
LOOKAHEAD_DISCLOSURE = (
    "This backtest compares weighting methods on a fixed, currently-selected "
    "universe. Because the holdings were chosen with present-day information, "
    "absolute historical performance is subject to look-ahead bias. The valid "
    "output is the RELATIVE comparison of weighting methods, not a claim of "
    "absolute historical alpha."
)


def ensure_dirs() -> None:
    """Create the data/ and outputs/ folders if they don't exist yet.

    Called once at the start of run_pipeline.py. Safe to call repeatedly:
    `mkdir(exist_ok=True)` is a no-op when the folder is already there.
    """
    DATA_DIR.mkdir(exist_ok=True)
    OUTPUTS_DIR.mkdir(exist_ok=True)


if __name__ == "__main__":
    # Running `python config.py` directly prints a one-page summary of the
    # whole configuration. Useful as a sanity check before a real run.
    import sys
    # The Windows default console codepage (cp949 on Korean Windows) cannot
    # encode every Unicode character. Force UTF-8 for our stdout writes so
    # the summary prints cleanly regardless of the host locale.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    print("=" * 60)
    print("Optimization & Backtesting module - configuration summary")
    print("=" * 60)
    print(f"Holdings CSV   : {HOLDINGS_CSV}")
    print(f"Data cache     : {DATA_DIR}")
    print(f"Outputs        : {OUTPUTS_DIR}")
    print()
    print("Constraints:")
    print(f"  Single-name cap : {MAX_WEIGHT_PER_STOCK:.0%}")
    print(f"  Sector cap      : {MAX_WEIGHT_PER_SECTOR:.0%}")
    print(f"  Long-only       : weights in [{WEIGHT_MIN}, {MAX_WEIGHT_PER_STOCK}]")
    print()
    print("Benchmark      :", BENCHMARK_NAME, f"({BENCHMARK_TICKER})")
    print(f"Price history  : {PRICE_HISTORY_YEARS} years, "
          f"{PRICE_FREQUENCY}, auto-adjusted={PRICE_AUTO_ADJUST}")
    print()
    print("Backtest:")
    print(f"  Estimation window : {ESTIMATION_WINDOW_YEARS} years "
          f"({ESTIMATION_WINDOW_DAYS} trading days)")
    print(f"  Rebalance         : {REBALANCE_FREQUENCY}")
    print(f"  Risk-free rate    : {RISK_FREE_RATE:.2%}")
    print()
    print("Composite ranking weights:")
    for k, v in COMPOSITE_WEIGHTS.items():
        print(f"  {k:<16s}: {v:.0%}")
    assert abs(sum(COMPOSITE_WEIGHTS.values()) - 1.0) < 1e-9, \
        "COMPOSITE_WEIGHTS must sum to 1.0"
    print()
    print("Look-ahead disclosure (will appear in run_log.txt & README.md):")
    print(f"  {LOOKAHEAD_DISCLOSURE}")
    print("=" * 60)
    print("OK")
