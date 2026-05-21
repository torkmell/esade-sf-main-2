# Claude Code Build Prompt — Optimization & Backtesting Module
### Scope: assume the 20-stock portfolio is already selected. Build ONLY optimization + backtesting.

> Paste everything below the line into Claude Code as your build instruction.
> Place `sample_holdings_20.csv` in the project folder before you start.

---

## 1. Context

You are building the **final stage** of an AI-agent research pipeline for an MSc Finance
sustainable-investing assignment. **Stock selection is already done** — a human Investment
Captain has chosen the ~20 companies. Your job is ONLY two things:

1. **Optimization** — compute portfolio weights for the given companies using SEVERAL methods.
2. **Backtesting** — test each method out-of-sample and compare them so a human can pick one.

In the pipeline diagram this is the **Portfolio Construction Agent (module 11)**, with two
sub-components — an **Optimization Agent** and a **Backtesting Agent**. Build BOTH as plain,
deterministic Python. **Do NOT use any LLM / AI calls inside this code.** Optimization and
backtesting must be 100% reproducible: same input → same output, every time.

**Do NOT build stock selection, ESG scoring, or any upstream data pipeline.** Those are out of
scope. The 20 companies are a fixed input. Never add or drop a name.

## 2. How you must work (the team has limited coding experience)

- Write clean, **heavily commented** code. Every function gets a plain-English docstring:
  what it does, what goes in, what comes out.
- **Build one file at a time.** After each file, STOP and tell me exactly what command to run
  to test it and what output to expect, before moving on.
- **Inspect the input CSV first.** Open `sample_holdings_20.csv`, print its columns and first
  rows, show me, and confirm the mapping before writing any logic.
- **No silent failures.** If a price download fails or a method is infeasible, log a clear
  message and continue with the rest — never crash the whole run.
- Fix all random seeds. Record every parameter in a run log.
- At the very end produce `VERIFICATION.md` — a non-coder checklist to confirm the run is sane.

## 3. The input file — `sample_holdings_20.csv`

One row per selected company. Columns (confirm exact names by inspecting the file):

| Column | Meaning | Used for |
|---|---|---|
| `ticker` | Yahoo Finance ticker, with exchange suffix (e.g. `IMCD.AS`, `VER.VI`) | downloading prices |
| `company_name` | Human-readable name | display only |
| `country` | Country of listing | country cap |
| `sector` | SASB sector | sector cap |
| `esg_score` | Overall ESG percentile, 0-100 (higher = better) | Black-Litterman views + score-tilt |
| `carbon_intensity` | GHG / EVIC carbon intensity (blank for some rows) | portfolio WACI in the backtest |

**Ticker verification — do this FIRST, it is the most common failure point.** Before any
optimization, write a small step in `data_loader.py` that downloads a short recent price window
for all 20 tickers and reports which ones returned no data. Print that report and PAUSE so I
can fix any bad tickers before the full run. Do not silently proceed with missing tickers.

## 4. Mandate constraints — put these in `config.py`

- Long-only, fully invested: weights ≥ 0, weights sum to 1, no shorting, no leverage.
- **Single-name cap: 10%** (no stock above 0.10).
- **Sector cap: 25%** — applied using the `sector` column in the CSV.
- **Country cap: 35%** — applied using the `country` column in the CSV.
- Benchmark: **STOXX Europe 600**. A free Net-Total-Return series is hard to get — use the best
  free Yahoo Finance proxy (e.g. `^STOXX`) and **document this as a limitation** in the README
  and run log.
- Price history: download **8 years** of daily prices (or the maximum available) via
  `yfinance`, in EUR where possible, and **cache to `data/` so re-runs are reproducible**.

## 5. Project structure

```
optimization_module/
  config.py          # all constraints + parameters in one place
  data_loader.py     # load CSV; verify tickers; download & cache prices; build sector/country maps
  optimizers.py      # OPTIMIZATION AGENT — 6 methods, all via PyPortfolioOpt
  backtester.py      # BACKTESTING AGENT — walk-forward, out-of-sample
  selector.py        # multi-criteria comparison + recommended method
  run_pipeline.py    # orchestrator — runs everything, writes all outputs
  requirements.txt   # pyportfolioopt, yfinance, pandas, numpy, matplotlib
  README.md          # plain-English: what it is, how to run, known limitations
  VERIFICATION.md    # non-coder checklist
  data/              # cached price data
  outputs/           # all results
```

## 6. `optimizers.py` — the Optimization Agent

One function per method. **Every method uses PyPortfolioOpt** and **every method must respect
the single-name cap, sector cap and country cap.** Build these 6 methods:

1. **Equal weight** — 1/N in each name. Baseline; the method every other method must beat.
2. **Maximum Sharpe** — PyPortfolioOpt `EfficientFrontier`, `weight_bounds=(0, 0.10)`; apply
   sector caps and country caps with `add_sector_constraints` (call it once for sectors and
   once treating country as a "sector"-style group).
3. **Minimum volatility** — same `EfficientFrontier` setup, `min_volatility()`.
4. **Hierarchical Risk Parity (HRP)** — `HRPOpt`. HRP cannot take sector/country constraints
   natively; after optimizing, cap any weight above 10% and renormalize, then **document this
   post-processing step** in comments and the run log.
5. **Black-Litterman** — `BlackLittermanModel`. Build the "views" from `esg_score`: map a
   higher ESG score to a small positive expected-excess-return view and a lower score to a
   small negative view (keep the magnitude modest, e.g. a few percent spread top-to-bottom).
   Then run `max_sharpe()` on the Black-Litterman posterior returns. Comment this clearly — it
   is the method that feeds the sustainability signal directly into construction.
6. **Score-tilted** — weights proportional to `esg_score`, then capped at 10% and renormalized.
   Simple, transparent, mandate-aligned.

Each method: input = price/return history for the in-sample window + the constraint set + the
holdings table; output = a dict `{ticker: weight}` plus the method name. If a method is
infeasible under the caps, catch the error, log it clearly, return `None`, and continue.

## 7. `backtester.py` — the Backtesting Agent

Implement a **walk-forward, out-of-sample** backtest. This is what prevents overfitting — build
it exactly as described:

- **Estimation window (in-sample): 3 years** (~756 trading days). Expected returns and the
  covariance matrix are estimated ONLY from this window.
- **Rebalance frequency: annual** (expose it as a `config.py` parameter so it can be changed).
- **Procedure:** at each rebalance date, take the trailing 3-year window → run a method → get
  weights → **hold those weights for the next 1 year** → record that out-of-sample year's
  realised returns. Then roll the window forward and repeat to the end of the data.
- The estimation window and the performance-measurement window must **never overlap.** Reported
  performance is the stitched-together sequence of out-of-sample years only.
- Run this for every method in `optimizers.py`.

**Look-ahead bias — required handling.** The 20 companies and their ESG scores are a single
current snapshot; no point-in-time historical ESG data exists, so the backtest holds the SAME
20 names across all windows. This is a known limitation — do NOT try to fix it, but handle it
honestly: write into `run_log.txt` and `README.md` this exact sentence — *"This backtest
compares weighting methods on a fixed, currently-selected universe. Because the holdings were
chosen with present-day information, absolute historical performance is subject to look-ahead
bias. The valid output is the RELATIVE comparison of weighting methods, not a claim of absolute
historical alpha."* Frame every result as "which weighting method is most robust", never "this
portfolio would have returned X%".

For each method, compute over the full out-of-sample period:
- Cumulative return, CAGR, annualised volatility
- **Sharpe ratio** and **Sortino ratio**
- **Maximum drawdown**
- **Annual turnover** (sum of absolute weight changes at each rebalance)
- **Tracking error vs the benchmark** (annualised std of portfolio-minus-benchmark returns)
- **Portfolio WACI** — weighted-average of `carbon_intensity` using final weights; skip names
  with blank carbon data and note in the log how many were skipped.

## 8. `selector.py` — comparison and recommendation

- Build a comparison table: rows = the 6 methods, columns = all metrics from section 7.
- **Do NOT choose the winner on raw return alone.** Compute a composite ranking across: Sharpe
  (higher better), maximum drawdown (smaller better), turnover (lower better), and whether
  tracking error sits inside a sensible band (e.g. 2-8%).
- Output a recommended method WITH a short written rationale, but label the output
  `RECOMMENDATION — FOR HUMAN INVESTMENT COMMITTEE REVIEW`. The code recommends; the human
  decides. This is deliberate and must stay in the output.

## 9. Outputs — write all into `outputs/`

- `optimization_weights.csv` — every method's full weight vector, side by side.
- `backtest_results.csv` — the method-vs-metrics comparison table.
- `equity_curves.png` — cumulative out-of-sample return of each method vs the benchmark.
- `run_log.txt` — audit log: run date/time, price-download date, all parameters (estimation
  window, rebalance frequency, all cap values), any tickers with no data, any methods that
  failed and why, the look-ahead limitation sentence, and how many names lacked carbon data.
- A clear printed summary in the console at the end of `run_pipeline.py`.

## 10. Final step

After everything runs end to end, write `VERIFICATION.md`: a short, plain-English checklist a
team member who cannot read code can use to confirm the run is sensible. For example: every
weight is between 0% and 10%; each method's weights sum to ~100%; no sector exceeds 25%; no
country exceeds 35%; the comparison table has one row per method; the run log records a price-
download date and the look-ahead limitation. Keep it concrete and non-technical.
