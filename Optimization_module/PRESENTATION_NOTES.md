# Presentation Talk-Track — Optimization & Backtesting

*MSc Finance, ESADE — Sustainable Investing assignment.*
*One bullet block per slide. Read top-down; each block is what you actually say out loud, not what's printed on the slide.*

---

## Slide 1 — The decision we are NOT trying to make

- The 20-stock universe is already fixed by the Investment Captain. We are
  the **Portfolio Construction Agent** (module 11 of the pipeline).
- We have one job: turn 20 names into 20 weights, defensibly.
- And one explicit non-job: we are not picking the stocks; we are not
  re-scoring the ESG signal.

## Slide 2 — Why we compare six methods instead of picking one

- Every optimizer's output is conditional on its assumptions: stable
  expected returns, a well-conditioned covariance, a sensible market
  proxy. Any one of those can fail on a 20-stock European sample.
- DeMiguel, Garlappi and Uppal (2009) — naive 1/N beats sample-mean-variance
  out-of-sample in 11 of 14 datasets they study. That alone is the
  motivation for benchmarking against equal weight.
- Our methodology is therefore: implement a representative *set* of
  approaches, evaluate them under the same backtest protocol, recommend
  on a composite score.

## Slide 3 — The six methods, mapped to their justification

- **Equal weight (1/N)** — the DeMiguel/Garlappi/Uppal floor.
- **Maximum Sharpe** — Markowitz (1952) tangency. Ledoit-Wolf shrinkage
  for the covariance to control estimation error on 3 years of daily data.
- **Minimum volatility** — avoids estimating expected returns (Merton,
  1980 — they are essentially un-estimable from short samples). Exploits
  the low-volatility anomaly (Blitz and van Vliet, 2007).
- **Hierarchical Risk Parity** — López de Prado (2016). Robust to
  ill-conditioned covariance because it does not invert it.
- **Black-Litterman with ESG views** — Black and Litterman (1992) plus
  Idzorek (2005). ESG percentile is mapped to a small tilt on the
  market-implied prior, then the posterior feeds max-Sharpe. This is the
  only method that injects the sustainability signal directly into
  expected returns, in the spirit of Pedersen, Fitzgibbons and Pomorski
  (2021).
- **Score-tilted** — weights proportional to ESG percentile. The
  napkin-math baseline: transparent and trivially defensible.

## Slide 4 — The constraint set

- Long-only, fully invested.
- Single name ≤ 10%, sector ≤ 25%, country ≤ 35%. The 10% cap is in the
  spirit of the UCITS 5/10/40 rule.
- Two honest caveats: HRP and Score-Tilted enforce the single-name cap
  only — they have no native optimizer to express linear sector / country
  constraints. We disclose this in the CSV of weights and in the README.
- The other four methods route the caps through CVXPY's linear
  constraint engine via PyPortfolioOpt.

## Slide 5 — The backtest protocol

- Walk-forward, expanding evaluation, strictly out-of-sample.
- 3-year estimation window → annual rebalance → hold weights for one
  year → stitch realised OOS years into a single performance series.
- The estimation window terminates *strictly before* the rebalance date,
  so no day inside the measurement window is used to compute its own
  weights. This is the discipline of Bailey, López de Prado et al.
  (2014) against backtest overfitting.

## Slide 6 — Why we do NOT rank on return

- Five years of realised return is a noisy signal. Picking the highest
  is a textbook data-snooping move (Lo and MacKinlay, 1990).
- We compute a composite over four criteria:
  - Sharpe (40%) — risk-adjusted return,
  - Max drawdown (25%) — tail behaviour Sharpe misses,
  - Annual turnover (15%) — implementation cost proxy,
  - Tracking error inside a 2-8% band (20%) — penalises both benchmark-
    hugging and benchmark-divergence.
- Each criterion is normalised to [0, 1] across the six candidates.
- The composite produces a recommendation, never a decision.

## Slide 7 — Sustainability integration

- Two of the six methods embed ESG directly into construction:
  Black-Litterman views and Score-Tilted weights. The remaining four
  inherit ESG only through the upstream universe selection — they ignore
  the within-universe ESG variation.
- This separation lets the Committee see, quantitatively, *what
  embedding ESG into expected returns costs or earns* relative to
  embedding it only at the screening stage.
- Carbon-intensity: portfolio WACI computed per TCFD (2017), reported
  alongside risk/return so the trade-off is visible.

## Slide 8 — Look-ahead bias: disclosed, not hidden

- The 20 names were chosen with today's information. The backtest holds
  those same 20 names in every window, including 2018-2020. That is a
  look-ahead bias on the universe, by construction.
- We do not try to undo it (no point-in-time historical ESG data exists
  to reconstruct prior universes). We frame the output as a *relative*
  comparison of weighting methods — never as a claim of historical alpha.
- The run log carries the verbatim disclosure required for that framing.

## Slide 9 — Result

- Read the table on screen: composite ranks the methods, the winner is
  labelled, the rationale lists the actual drivers (Sharpe X, MDD Y,
  turnover Z, TE W).
- On this run the composite picks **max-Sharpe** — driven by the 40%
  Sharpe weight inside the composite.
- For a Nordic pension-fund mandate, the IC overrides toward **minimum
  volatility**: same Sharpe (0.95 vs 0.95), smaller drawdown (−23.2% vs
  −28.8%), roughly half the turnover (12% vs 24%), tracking error inside
  the 2-8% band (8.3% vs 9.9%). Drawdown defense and low turnover beat
  peak risk-adjusted return for this client; that is the explicit basis
  for the override.
- The framework treats this as a **defended override**, not a
  contradiction: the composite informs, the IC adjudicates, the audit
  trail captures both. Tilting the composite further toward Sharpe
  flips it back — the sensitivity lives in `config.COMPOSITE_WEIGHTS`
  and is itself part of the answer.
- The label on the output: **"RECOMMENDATION — FOR HUMAN INVESTMENT
  COMMITTEE REVIEW."** We deliberately do not call this a decision.

## Slide 10 — What we would do with more time

- Point-in-time ESG history to lift the look-ahead constraint.
- A live total-return benchmark instead of the price-only Yahoo proxy.
- Transaction-cost-aware optimization (Almgren and Chriss, 2001) — we
  report turnover but do not penalise it inside the objective.
- Market-cap-weighted Black-Litterman prior instead of 1/N proxy.

---

## Closing line (use if asked "so what?")

> The methodology's value is not that it picks the winning method. It is
> that, for any chosen method, the Committee can see the assumption it
> rests on, the robustness check it survived, and the limitation it
> inherits. The recommendation is an input to a human decision, not a
> replacement for one.
