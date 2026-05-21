# Verification checklist — non-coder

Use this list to sanity-check a run **without reading any code.** Open the
files in `outputs/` and answer each question. If anything is "no", flag it
to whoever is on the technical side.

---

## 1. The run actually finished

Open `outputs/run_log.txt`. Scroll to the bottom.

- [ ] There is a line that says `Run finished (UTC): ...` with a timestamp.
- [ ] The elapsed time is reasonable (typically 10-120 seconds).
- [ ] There is NO Python traceback / `Error` / `Exception` in the log.

## 2. The right input was used

In `run_log.txt`, near the top:

- [ ] The line `CSV: ...sample_holdings_20.csv` shows the holdings file.
- [ ] `Rows: 20` — exactly 20 holdings were read in.
- [ ] `Ticker verify: 20/20 OK` — every ticker returned data.
- [ ] `Benchmark ^STOXX: OK` — the benchmark also responded.

## 3. The parameters match the mandate

Same file, "Parameters" section near the top:

- [ ] `MAX_WEIGHT_PER_STOCK     = 10%`
- [ ] `MAX_WEIGHT_PER_SECTOR    = 25%`
- [ ] `MAX_WEIGHT_PER_COUNTRY   = 35%`
- [ ] `ESTIMATION_WINDOW_YEARS  = 3 (756 trading days)`
- [ ] `REBALANCE_FREQUENCY      = annual`
- [ ] `BENCHMARK                = STOXX Europe 600 ... (^STOXX)`

## 4. The price download is fresh and audited

Same file, "Price download" section:

- [ ] `Fetched at (UTC ISO): ...` shows a recent timestamp — this is the
  audit trail required by the mandate.
- [ ] The panel covers roughly 8 years of trading days (~2000+ rows).
- [ ] The date range ends close to today.

## 5. The weights are well-formed

Open `outputs/optimization_weights.csv`. There are 20 rows (one per ticker)
and 6 method columns: `equal_weight, max_sharpe, min_volatility, hrp,
black_litterman, score_tilted`.

For **every column**, check:

- [ ] All weights are between 0 and 0.10 (no number above 0.10).
- [ ] No negative weights.
- [ ] The column sums to ~1.0 (allow a tiny rounding error like 0.9999).

The fastest way is to put each column into a spreadsheet and run
`=SUM(...)` and `=MAX(...)`.

## 6. The caps are respected — sectors and countries

For methods 2, 3, and 5 (`max_sharpe`, `min_volatility`, `black_litterman`):

- [ ] Sum of weights inside any one **sector** ≤ 25%.
- [ ] Sum of weights inside any one **country** ≤ 35%.

For methods 4 and 6 (`hrp`, `score_tilted`):

- The single-name 10% cap is enforced.
- The sector / country caps are **NOT** enforced (these methods have no
  native optimizer for them). The README explains this; sector/country
  totals in those two columns may exceed the cap.

## 7. The backtest produced a comparison table

Open `outputs/backtest_results.csv`.

- [ ] There is exactly **one row per method** (6 rows total).
- [ ] The columns include Sharpe, max drawdown, annual turnover, tracking
  error, WACI, composite score, and rank.
- [ ] The `rank` column has values 1 through 6 — every method got a rank.
- [ ] `n_oos_days` is similar across methods (a few hundred to ~1300).
- [ ] `n_failed_rebal` is 0 (or 1-2 at most) for every method.

## 8. The equity-curves chart exists and looks reasonable

Open `outputs/equity_curves.png`.

- [ ] Seven lines: six method lines plus the benchmark (dashed black).
- [ ] All lines start near 1.0 on the left edge.
- [ ] No line goes flat / vertical / off the chart — these would signal
  data problems.
- [ ] The benchmark line is identifiable as the dashed black line.

## 9. The recommendation is labelled clearly

Same file, "RECOMMENDATION" section:

- [ ] The text contains `RECOMMENDATION - FOR HUMAN INVESTMENT COMMITTEE
  REVIEW`.
- [ ] The recommended method is named.
- [ ] The rationale lists the actual Sharpe, max drawdown, turnover, and
  tracking error of that method.

## 10. The look-ahead disclosure is recorded verbatim

Same file, "Look-ahead disclosure" section:

- [ ] The exact sentence below appears, unchanged, in `run_log.txt`:

> This backtest compares weighting methods on a fixed, currently-selected
> universe. Because the holdings were chosen with present-day information,
> absolute historical performance is subject to look-ahead bias. The valid
> output is the RELATIVE comparison of weighting methods, not a claim of
> absolute historical alpha.

## 11. WACI accounting is honest

Same file, "Metrics + composite ranking" section:

- [ ] There is a line `WACI: names without carbon_intensity skipped = N`.
- [ ] If `N > 0`, the CSV genuinely had blank carbon-intensity values for
  N rows — confirm by opening `sample_holdings_20.csv` and counting blanks.

---

If every box is ticked, the run is mechanically sane. The Investment
Committee can then judge **which method to pick** — that decision is theirs,
not the code's.
