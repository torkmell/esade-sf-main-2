# Anticipated Q&A — Optimization & Backtesting

*MSc Finance, ESADE — Sustainable Investing assignment.*
*Defense / viva preparation. Each item: the likely question, a short on-the-spot answer, and supporting evidence to cite if pushed.*

---

## A. Method choice

### A1. Why six methods and not just one?

**Short answer.** Because every optimizer's output is conditional on its
assumptions, and any one of those assumptions can fail on a 20-stock
sample. Comparing a representative set makes the assumption-dependence
visible.

**Evidence.** DeMiguel, Garlappi and Uppal (2009) show naive 1/N
diversification beats sample-mean-variance OOS in 11 of 14 datasets —
that result alone forces you to benchmark against equal weight before
trusting any optimizer.

### A2. Why max-Sharpe? Markowitz is decades-old; some literature dismisses it.

**Short answer.** Max-Sharpe is the textbook tangency, and dismissing it
without measuring it would be unscientific. We include it precisely so we
can show *empirically* whether it beats simpler methods on this universe.

**Evidence.** Markowitz (1952); concerns about estimation error come from
Merton (1980) and Michaud (1989) — both addressed in our implementation
via Ledoit-Wolf shrinkage (Ledoit and Wolf, 2004) on the covariance.

### A3. Why min-volatility? Isn't it just a low-vol smart-beta strategy?

**Short answer.** Yes, and intentionally so. Min-volatility sidesteps the
hardest input — expected returns — and exploits a robust, documented
anomaly. It is the "less wrong" cousin of max-Sharpe.

**Evidence.** Merton (1980) on the difficulty of estimating expected
returns; Blitz and van Vliet (2007) and Baker, Bradley and Wurgler
(2011) on the low-volatility anomaly's persistence.

### A4. Why HRP? Is it more than a marketing term?

**Short answer.** HRP solves a different problem than Markowitz. It does
not invert the covariance matrix, so it is robust to the ill-conditioning
that plagues quadratic optimizers on small N. We include it to test
robustness explicitly, not for fashion.

**Evidence.** López de Prado (2016) demonstrates HRP outperforming
inverse-variance, minimum-variance and equal-weighting OOS in Monte Carlo
experiments, citing condition-number issues with the sample covariance.

### A5. Why Black-Litterman if its inputs are subjective?

**Short answer.** Because we want to inject the sustainability signal
*into the optimizer's expected returns*, not just into the universe
filter upstream. BL is the standard machinery for blending an
information-poor prior with informative views.

**Evidence.** Black and Litterman (1992); Idzorek (2005) for the
practical view-construction step; Pedersen, Fitzgibbons and Pomorski
(2021) for the ESG-as-view framing.

### A6. Why include Score-Tilted at all? It is barely an "optimizer".

**Short answer.** Because the IC must be able to reason about the chosen
method. Score-Tilted is the napkin-math version — fully transparent,
trivially defensible, and a useful baseline against the "smarter"
methods.

**Evidence.** Methodological appeal to interpretability — Rudin (2019)
argues against complex black-box models when transparent ones suffice.

### A7. Why not include CVaR / mean-variance with shortfall / Maximum
Diversification / Risk Parity?

**Short answer.** We chose a representative set, not an exhaustive one.
The six methods span: theory-free baseline (1/N), classical mean-variance
(max-Sharpe), variance-only (min-vol), clustering-based (HRP), Bayesian
(BL), and rule-based (Score-Tilted). Adding more would increase
multiple-comparison risk without adding new assumption families.

**Evidence.** Harvey and Liu (2014) caution against extensive
multiple-testing in backtest comparisons; six methods × four criteria is
already at the upper edge of what we can defend.

---

## B. Backtest design

### B1. Why a 3-year estimation window?

**Short answer.** Long enough to estimate a covariance for 20 names
(~756 daily observations vs. 20² / 2 = 200 parameters), short enough to
stay responsive to regime changes. The hyperparameter is exposed in
`config.py` for sensitivity analysis.

**Evidence.** Standard rule of thumb in practitioner literature (Grinold
and Kahn, 2000); also matches the back-of-envelope condition
T >> N(N+1)/2 needed for a non-singular sample covariance.

### B2. Why annual rebalance and not monthly or quarterly?

**Short answer.** Three reasons: (i) the ESG signal is a slow-moving
fundamental, so monthly rebal would chase noise; (ii) annual matches a
typical institutional review cadence and gives interpretable turnover
numbers; (iii) it is configurable, so sensitivity to that choice can be
tested without code changes.

**Evidence.** Bender and Wang (2016) on factor-portfolio rebalance
frequency; SFDR Article 11 reports are also annual, aligning with
institutional reporting cadence.

### B3. How do you know your backtest is not overfit?

**Short answer.** The protocol enforces a strict no-overlap between
estimation and measurement windows. Every parameter we tune is set
*before* the backtest runs and is reported in the run log. We do not
re-tune after seeing OOS results.

**Evidence.** Bailey, Borwein, López de Prado and Zhu (2014) — the
explicit anti-overfitting protocol we follow.

### B4. Have you tested sensitivity to the rebalance date offset?

**Short answer.** Not in this build. It is a documented next step. The
ESG signal is slow-moving so we expect modest sensitivity, but the
"date-of-month" choice is a known source of backtest variance.

### B5. Why STOXX Europe 600 as the benchmark, and why the price proxy?

**Short answer.** STOXX 600 is the standard pan-European broad-market
benchmark and the mandate's stated reference. We use Yahoo's `^STOXX`
price index because a free Net-Total-Return series is not available.
The tracking error we report is therefore conservatively wide; we flag
this in the run log and the README.

---

## C. Constraints

### C1. Where do the 10% / 25% / 35% caps come from?

**Short answer.** The single-name 10% cap aligns with the spirit of the
UCITS 5/10/40 rule on issuer concentration; sector and country caps
are mandate-level discretionary settings that prevent dominant
exposures without being so tight as to force benchmark-hugging.

**Evidence.** UCITS Directive 2009/65/EC, Article 52.

### C2. Why doesn't HRP enforce the sector and country caps?

**Short answer.** HRP's optimization is hierarchical recursion through a
correlation-based cluster tree; it has no linear-constraint hook for
arbitrary groupings. We could iteratively rebalance after the fact, but
that would no longer be HRP. We disclose the limitation in the run log
and the README, rather than relabel a kludge as HRP.

**Evidence.** López de Prado (2016) — the original paper, no constraint
extension proposed.

### C3. What happens if all caps cannot be satisfied jointly?

**Short answer.** The optimizer raises an infeasibility error, which we
catch, log, and the method is recorded as "INFEASIBLE" for that
rebalance — it does not pollute the comparison silently. On the present
universe the constraints are easily feasible.

---

## D. Sustainability integration

### D1. ESG percentile is a noisy, vendor-specific score. Why trust it
as a view?

**Short answer.** We do not "trust" it; we use it with deliberately
modest magnitude (`BL_ESG_VIEW_SPREAD = 4%` top-to-bottom) and disclose
the sensitivity. The architecture lets the IC reduce that spread to zero
and observe the BL portfolio converge to the market-implied prior.

**Evidence.** Berg, Kölbel and Rigobon (2022) on ESG-rating divergence
across providers — informs our use of modest tilts and percentile (not
absolute) inputs.

### D2. Why are most methods agnostic to the ESG signal?

**Short answer.** Because the sustainability filter is upstream (the
universe is already ESG-screened). Re-injecting ESG into every method
would be double-counting. BL and Score-Tilted exist as the two methods
that consciously *do* embed ESG into construction, so the Committee can
quantify the value-add of doing so versus only screening.

### D3. Is carbon intensity (WACI) part of the optimization objective?

**Short answer.** No, it is reported as a portfolio characteristic, not
optimized over. The mandate does not specify a WACI target; introducing
one is a natural extension. The current setup lets the IC see
realized WACI across methods and decide whether to add the constraint.

**Evidence.** TCFD (2017) WACI definition; SFDR Article 9 reporting
template.

---

## E. Limitations and honesty

### E1. Look-ahead bias — how bad is it?

**Short answer.** Bad in absolute terms: the 20 names were chosen with
today's information, so any backtest of those names back to 2018 is
upward-biased on absolute return. We frame the output as *relative*
comparison only, and the verbatim disclosure is recorded in `run_log.txt`
and the README.

**Evidence.** Bailey et al. (2014) on look-ahead and survivorship bias
as the dominant sources of backtest inflation.

### E2. Why didn't you fix the look-ahead?

**Short answer.** It is unfixable here. No point-in-time historical ESG
data exists for these vendors, and reconstructing the prior universes
would require redoing the whole upstream selection pipeline at every
window — out of scope for this module. The honest move is to disclose,
not fake a correction.

### E3. What is the most serious limitation you could fix in a week?

**Short answer.** Replace the 1/N market proxy in the Black-Litterman
prior with capitalisation weights. That is well-defined and would
materially improve the BL output's interpretability.

### E4. Could the recommendation flip with different parameters?

**Short answer.** Yes, by design. The composite weights, the TE band,
and the BL spread are all in `config.py` for exactly that reason. The
methodology is *robust* in that all assumptions are explicit, not in
the (impossible) sense that no choice matters.

---

## F. Implementation / engineering

### F1. Why PyPortfolioOpt over rolling your own?

**Short answer.** PyPortfolioOpt's max-Sharpe / min-vol / BL / HRP are
peer-reviewed, well-tested, and wrap CVXPY for the optimization itself.
Re-implementing them in-thesis would invite bugs without educational
value, and the time was better spent on the backtest protocol and the
composite ranking.

**Evidence.** Martin (2021), *JOSS* paper for PyPortfolioOpt; Diamond
and Boyd (2016) for CVXPY.

### F2. Is the pipeline deterministic? Reproducible?

**Short answer.** Yes. The random seed is fixed, the price panel is
cached with metadata, and every parameter is centralised. Re-running on
the same inputs gives bit-identical outputs except for the price-fetch
timestamp.

### F3. Why use AI agents for the upstream stages but not for
optimization?

**Short answer.** Stock selection involves judgment over heterogeneous
qualitative inputs (controversies, reports, sector trends) where LLMs
add value. Portfolio construction is a closed-form mathematical problem
where determinism, auditability and reproducibility matter more than
flexibility. Using an LLM here would degrade trust without improving
output.

**Evidence.** Methodological argument from Rudin (2019) on interpretable
models in high-stakes decisions; institutional preference for
deterministic risk processes.

---

## G. Killer / curve-ball questions

### G1. "What if the IC just wants you to pick one?"

**Answer.** I would frame it as a **defended override of the composite
#1**, not as a free pick. The composite ranks **max-Sharpe** first
because Sharpe carries 40% of the weight inside `COMPOSITE_WEIGHTS`. For
a Nordic pension-fund mandate, whose priorities are drawdown defense and
low turnover rather than peak risk-adjusted return, the Investment
Committee can justifiably override toward **minimum volatility**:
min-volatility ties max-Sharpe on Sharpe (0.95), and beats it on
maximum drawdown (−23.2% vs −28.8%), annual turnover (12.3% vs 24.3%)
and tracking-error-in-band (8.3% in-band vs 9.9% outside). The override
is sensitive to the composite weighting: tilting it further toward
Sharpe flips the recommendation back to max-Sharpe. That sensitivity is
exposed in `config.COMPOSITE_WEIGHTS` precisely so the override is
auditable — same numbers as the methodology, two coordinated claims,
not a hidden disagreement.

**What this answer is NOT.** It is *not* "min-volatility beats 1/N, so
we pick min-volatility." Max-Sharpe also beats 1/N. The 1/N comparison
is a **baseline-pass** check — it answers "did complexity earn its
keep?" — not a tiebreaker between two methods that have both already
passed it. The genuine basis for choosing min-volatility over
max-Sharpe here is the mandate, not the 1/N baseline.

### G2. "Your composite weights are arbitrary."

**Answer.** They are *judgment-based*, not arbitrary. Each weight is
defensible (Sharpe is the standard risk-adjusted metric; max DD captures
tail risk Sharpe misses; turnover is a cost proxy; TE band reflects an
active-but-bounded mandate) and the weights are exposed in `config.py`
so the IC can run sensitivity analysis. If the question is "would the
ranking change under different weights?" — yes, sometimes, and that is a
finding, not a bug.

### G3. "How is this different from just plotting six equity curves?"

**Answer.** The equity curves are one output among many. The contribution
is (i) a disciplined OOS protocol that prevents look-ahead overfitting,
(ii) a multi-criteria composite that prevents return-snooping, and (iii)
explicit disclosure of constraint violations, parameter assumptions and
the universe look-ahead. The curves are the evidence; the framework is
the methodology.

### G4. "Why should the Investment Committee trust you?"

**Answer.** Trust is not the right frame. The framework is auditable: every
parameter is in `config.py`, every step is in `run_log.txt`, every
optimizer's code is short enough to read, and every limitation is
disclosed in the README. The Committee does not need to trust me — they
need to inspect the artefacts and decide whether the methodology is
sound. That is the design.

---

## References (additions beyond the methodology document)

- Almgren, R. and Chriss, N. (2001). Optimal execution of portfolio
  transactions. *Journal of Risk*, 3, 5-40.
- Bender, J. and Wang, T. (2016). Can the whole be more than the sum of
  the parts? Bottom-up versus top-down multifactor portfolio
  construction. *Journal of Portfolio Management*, 42(5), 39-50.
- Berg, F., Kölbel, J. F. and Rigobon, R. (2022). Aggregate confusion:
  The divergence of ESG ratings. *Review of Finance*, 26(6), 1315-1344.
- Grinold, R. and Kahn, R. (2000). *Active Portfolio Management*. McGraw-Hill.
- Harvey, C. R. and Liu, Y. (2014). Backtesting. *Journal of Portfolio
  Management*, 42(1), 13-28.
- Michaud, R. (1989). The Markowitz optimization enigma: Is "optimized"
  optimal? *Financial Analysts Journal*, 45(1), 31-42.
- Rudin, C. (2019). Stop explaining black-box models for high-stakes
  decisions and use interpretable models instead. *Nature Machine
  Intelligence*, 1(5), 206-215.
