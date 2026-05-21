# Optimization & Backtesting Module

This is the **final stage** of the AI-agent research pipeline. The Investment
Captain has already picked the ~20 companies. This module does **only two
things**:

1. **Optimization** — compute portfolio weights for the given companies
   using six different methods.
2. **Backtesting** — run a walk-forward, out-of-sample backtest of each
   method on 8 years of history, so a human can compare them and pick one.

The whole module is plain, deterministic Python. **No LLM calls.** Same
input + same code → same output, every time.

---

## What you get when you run it

Everything lands in `outputs/`:

| File | What it is |
|---|---|
| `optimization_weights.csv` | The final-snapshot weight vector of every method, side by side. |
| `backtest_results.csv` | The method-vs-metrics table plus the composite ranking. |
| `equity_curves.png` | Cumulative out-of-sample return of each method + the benchmark. |
| `run_log.txt` | Audit log: run timestamp, price-fetch timestamp, every parameter, any bad tickers, any failed methods, the look-ahead disclosure, and the WACI-skip count. |

Console also prints a one-page summary at the end. The orchestrator labels
the recommendation as `RECOMMENDATION - FOR HUMAN INVESTMENT COMMITTEE
REVIEW`. **The code recommends; the human decides.**

---

## How to run it

```powershell
# 1. Create a Python 3.11 virtual environment (one-time):
py -3.11 -m venv .venv

# 2. Install dependencies:
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# 3. (Optional) Inspect the CSV + verify tickers BEFORE the long download:
.\.venv\Scripts\python.exe data_loader.py

# 4. Run the full pipeline:
.\.venv\Scripts\python.exe run_pipeline.py
```

End-to-end runtime on a cached panel is under 10 seconds; the first run
spends a minute or two pulling 8 years of daily prices from Yahoo Finance.

---

## Constraints (`config.py`)

All constraints live in `config.py`. Change them there; every module picks
the change up on the next run.

- Long-only, fully invested: weights ≥ 0, sum to 1, no shorting, no leverage.
- **Single-name cap: 10%** — no stock above 0.10.
- **Sector cap: 25%** — using the `sector` column in the holdings CSV.
- **Country cap: 35%** — using the `country` column in the holdings CSV.
- **Estimation window: 3 years** (~756 trading days) — what each optimizer
  sees as in-sample at each rebalance.
- **Rebalance frequency: annual** (configurable).
- **Risk-free rate: 2%** annual.

---

## The six methods

| # | Method | What it does | Constraint handling |
|---|---|---|---|
| 1 | `equal_weight` | 1/N in every name. Baseline. | All caps trivially satisfied at 1/N = 5%. |
| 2 | `max_sharpe` | EfficientFrontier max-Sharpe via PyPortfolioOpt. | 10% / 25% / 35% caps applied as native CVXPY constraints. |
| 3 | `min_volatility` | EfficientFrontier min-vol. | Same constraint set as max_sharpe. |
| 4 | `hrp` | Hierarchical Risk Parity (`HRPOpt`). | Single-name cap applied **post-optimization** by iterative cap-and-renormalise. **Sector / country caps NOT enforced** — HRP has no native constraint hooks. Documented in `run_log.txt`. |
| 5 | `black_litterman` | Black-Litterman with ESG-driven views: high ESG → small positive tilt to prior, low ESG → small negative tilt. Then max-Sharpe on the posterior. | All caps native. The view spread is `BL_ESG_VIEW_SPREAD` in `config.py` (4% top-to-bottom by default). |
| 6 | `score_tilted` | Weights proportional to ESG score. | Single-name cap by post-cap-and-renormalise; sector / country caps not enforced (no native optimizer). |

---

## The backtest (`backtester.py`)

Walk-forward, out-of-sample. At each rebalance date:

1. **In-sample window** = the trailing 3 years (strictly before the rebalance date).
2. Run each method on the in-sample window → get weights.
3. **Hold** those weights until the next rebalance date.
4. Record the realised daily returns over the holding period — those are the **out-of-sample** returns.

The estimation window and the measurement window **never overlap**.
Reported performance is the stitched-together sequence of OOS years only.

Per-method metrics:

- cumulative return, CAGR, annualised volatility
- **Sharpe** and **Sortino**
- **max drawdown**
- **annual turnover** (sum of |Δw| at each rebalance, scaled per year)
- **tracking error vs the benchmark** (annualised std of P − B)
- **portfolio WACI** (weighted-average carbon intensity, skipping any
  names with blank carbon data — `run_log.txt` records how many were skipped)

---

## How the recommendation is made (`selector.py`)

Do **not** choose on raw return alone. The selector computes a composite
score across:

| Criterion | Direction | Default weight |
|---|---|---|
| Sharpe | higher is better | 40% |
| max drawdown | smaller magnitude is better | 25% |
| annual turnover | lower is better | 15% |
| tracking-error band (2-8%) | inside band is better | 20% |

Each criterion is normalised to [0, 1] across the six methods and combined.
The output labels the winner as a **recommendation**, not a decision.

---

## Known limitations (read this before quoting results)

1. **Look-ahead bias.** The 20 holdings are a single current snapshot — no
   point-in-time historical ESG / membership data exists for them. The
   backtest therefore holds the **same 20 names** in every window. This
   makes absolute historical performance subject to look-ahead bias. The
   valid output is the **relative** comparison of methods, not a claim of
   absolute historical alpha. The verbatim disclosure is in `run_log.txt`:

   > This backtest compares weighting methods on a fixed, currently-selected
   > universe. Because the holdings were chosen with present-day information,
   > absolute historical performance is subject to look-ahead bias. The
   > valid output is the RELATIVE comparison of weighting methods, not a
   > claim of absolute historical alpha.

2. **Benchmark is a price-only proxy.** A free Net-Total-Return STOXX
   Europe 600 series is not available; the module uses Yahoo's free
   `^STOXX` (price return). Tracking error vs an NTR benchmark would be a
   bit lower than reported.

3. **HRP and Score-Tilted enforce only the single-name cap.** They have
   no native optimizer in which to express sector and country caps. Those
   methods' sector / country exposures may exceed the caps; this is
   transparent in `outputs/optimization_weights.csv` and logged.

4. **Black-Litterman market-implied prior uses a 1/N market proxy** since
   this module has no live market-cap data. Documented limitation.

5. **Single CSV holding fix during build.** `KESB.HE` is not a valid Yahoo
   ticker; it was changed to `KESKOB.HE` (Kesko Class B Helsinki) after
   verification failed for the original symbol.

---

## File layout

```
optimization_module/
  config.py          - all constraints + parameters in one place
  data_loader.py     - load CSV, verify tickers, download & cache prices
  optimizers.py      - the 6 weighting methods (PyPortfolioOpt)
  backtester.py      - walk-forward, out-of-sample backtest
  selector.py        - multi-criteria comparison + recommended method
  run_pipeline.py    - orchestrator (the script you run)
  requirements.txt   - pinned dependency versions
  README.md          - this file
  VERIFICATION.md    - non-coder checklist for sanity-checking a run
  sample_holdings_20.csv - the 20-stock selection (input)
  data/              - cached price data (created on first run)
  outputs/           - results (created on first run)
```

Every module also has a `__main__` self-test you can run standalone for
debugging:

```powershell
.\.venv\Scripts\python.exe config.py        # print all parameters
.\.venv\Scripts\python.exe data_loader.py   # inspect CSV + verify tickers
.\.venv\Scripts\python.exe optimizers.py    # run each method once
.\.venv\Scripts\python.exe backtester.py    # full backtest, no file writes
.\.venv\Scripts\python.exe selector.py      # composite ranking on synthetic data
```
