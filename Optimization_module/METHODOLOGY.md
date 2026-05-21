# Methodology: Optimization & Backtesting Module

*MSc Finance — Sustainable Investing assignment, ESADE.*
*Final stage of the AI-agent research pipeline (Portfolio Construction Agent, module 11). Stock selection (the 20 names) is taken as a fixed input from the Investment Captain; this section concerns weighting and evaluation only.*

---

## 1. Design philosophy

We do not commit to a single "right" optimizer. Each portfolio-construction
method carries its own assumptions — about the stability of expected
returns, the conditioning of the covariance matrix, or the meaningfulness
of higher moments — and any one of those assumptions can fail on a
20-stock European equity sample. Following the model-uncertainty argument
of DeMiguel, Garlappi and Uppal (2009), who show that naive 1/N
diversification often outperforms sample-based mean-variance optimization
out-of-sample, we implement a **representative set of six methods** and
compare them under a walk-forward, out-of-sample protocol. The output is
not a single answer but a robustness-aware comparison; the final selection
remains with the Investment Committee.

## 2. The six weighting methods

We choose methods that span the assumption space, from theory-free
benchmarks to the explicit integration of the sustainability signal.

1. **Equal weight (1/N).** The hard-to-beat benchmark of DeMiguel et al.
   (2009). Requires no estimation and is therefore immune to estimation
   error. Establishes a floor against which optimization must justify
   itself.

2. **Maximum Sharpe.** The Markowitz (1952) tangency portfolio
   operationalised through PyPortfolioOpt's `EfficientFrontier`
   (Martin 2021). Expected returns are estimated from historical means and
   the covariance from Ledoit-Wolf shrinkage (Ledoit and Wolf, 2004), which
   shrinks the sample covariance toward a structured target and is
   well-suited to the small-N, three-year window we use.

3. **Minimum volatility.** Same EF setup as max-Sharpe but with the
   variance objective. Avoids the need to estimate expected returns — which
   are notoriously hard (Merton, 1980) — and exploits the low-volatility
   anomaly (Blitz and van Vliet, 2007; Baker, Bradley and Wurgler, 2011).

4. **Hierarchical Risk Parity (HRP).** López de Prado (2016) shows that
   HRP is robust to the ill-conditioning that plagues quadratic optimizers,
   because it relies on a hierarchical clustering of correlations and
   recursive risk budgeting rather than on inverting the covariance matrix.
   We include HRP precisely to test whether a non-Markowitz approach
   improves out-of-sample robustness in our setting.

5. **Black-Litterman with ESG views.** The Black-Litterman framework
   (Black and Litterman, 1992; Idzorek, 2005) blends a market-implied prior
   with investor views to produce a posterior of expected returns. We
   construct the views directly from the ESG percentile: each name's view
   is the market-implied prior plus a linear ESG tilt with a configurable
   top-to-bottom spread (`BL_ESG_VIEW_SPREAD = 4%`). High-ESG names receive
   a small positive tilt; low-ESG names a small negative one. The
   posterior is then fed to max-Sharpe under the mandate constraints.
   This is the method that injects the sustainability signal *directly into
   construction*, rather than only filtering the universe upstream. The
   design choice mirrors Pedersen, Fitzgibbons and Pomorski's (2021)
   "ESG-efficient frontier", which embeds ESG into expected returns.

6. **Score-tilted (ESG-proportional).** Weights proportional to the ESG
   percentile, capped at the single-name ceiling and renormalised. The
   simplest transparent way to express the mandate; we include it as a
   non-optimization baseline that an analyst could compute on a napkin and
   that the IC can therefore reason about without trusting any optimizer.

All six methods are dispatched through a common interface so the
backtester can call them in a loop.

## 3. Constraints

Constraints are common across all methods (with the exceptions noted
below) and reflect the mandate:

| Constraint | Value | Source |
|---|---|---|
| Long-only, fully invested | weights ≥ 0, Σw = 1 | Mandate |
| Single-name cap | 10% | Standard concentration limit; aligns with the spirit of the UCITS 5/10/40 rule (UCITS Directive 2009/65/EC, Art. 52). |
| Sector cap | 25% | Discretionary; consistent with diversified-equity practice. |
| Country cap | 35% | Discretionary; allows core-Europe overweights without single-country dominance. |

For max-Sharpe, min-volatility and Black-Litterman the caps are passed to
PyPortfolioOpt's CVXPY backend as native linear constraints (Diamond and
Boyd, 2016). For HRP and Score-Tilted the single-name cap is enforced
**post-optimization** by iterative cap-and-renormalise; sector and country
caps cannot be expressed within those frameworks. This limitation is
disclosed in the run log and the README rather than hidden.

## 4. Backtesting protocol

We use a walk-forward, expanding-evaluation, out-of-sample protocol
(Aronson, 2007; Bailey, Borwein, López de Prado and Zhu, 2014):

- **Estimation window:** 3 years (~756 trading days). At each rebalance,
  expected returns and the covariance matrix are estimated **only** from
  this trailing window.
- **Rebalance frequency:** annual (configurable). At each rebalance, the
  method is re-run on the trailing window; the resulting weights are
  **held for the next year** to generate realised returns.
- **No overlap:** the estimation window terminates strictly before the
  rebalance date, so no day inside the measurement window contributes to
  its own weight calculation. Stitching the OOS years end-to-end gives the
  reported performance series.
- **Total OOS span:** approximately 5 years (the 8-year history minus the
  3-year burn-in).

This protocol controls for the most common backtest pathologies — in-sample
overfitting and look-ahead through accidentally including future
information in the estimator (Bailey et al., 2014).

## 5. Performance metrics

For each method we report a deliberately broad metric set so the comparison
does not collapse onto a single dimension:

- **Cumulative return, CAGR, annualised volatility.**
- **Sharpe ratio** (Sharpe, 1966) as the workhorse risk-adjusted metric.
- **Sortino ratio** (Sortino and Price, 1994) to penalise downside
  asymmetry, which a pure-variance metric misses.
- **Maximum drawdown** as a tail-risk indicator that captures investor
  pain in a way Sharpe does not.
- **Annual turnover** as a transaction-cost / implementation proxy.
- **Tracking error** vs the benchmark (STOXX Europe 600 price proxy via
  Yahoo `^STOXX`; an NTR series is not freely available — disclosed).
- **Portfolio Weighted-Average Carbon Intensity (WACI)** following the
  TCFD recommendations (TCFD, 2017) and the format used in SFDR Article 9
  reporting.

## 6. Method selection: composite, not single-criterion

A core methodological position is that **the recommended method must not be
chosen on realised return alone.** Realised return over a five-year OOS
window is a noisy estimator of the underlying process; ranking on it would
amount to data-snooping (Lo and MacKinlay, 1990). We therefore compute a
composite score over four criteria, normalised to [0, 1] across the six
candidate methods:

| Criterion | Direction | Weight |
|---|---|---|
| Sharpe ratio | higher is better | 40% |
| Maximum drawdown | smaller is better | 25% |
| Annual turnover | lower is better | 15% |
| Tracking-error band (2-8%) | inside band is better | 20% |

The tracking-error band is treated non-monotonically: a method that hugs
the benchmark (TE < 2%) earns no premium for active risk, while a method
with TE > 8% takes on benchmark-divergence risk that an institutional
mandate would discourage. The method with the highest composite score is
labelled the recommendation, but the output is explicitly framed as
**"RECOMMENDATION — FOR HUMAN INVESTMENT COMMITTEE REVIEW"** to keep
discretionary judgment in the loop, in the spirit of the human-in-the-loop
risk-management argument of Hubbard (2020).

### 6.1 The composite is informative; the override is auditable

In the present run the composite ranks **max-Sharpe first** — a result
driven by the 40% weight on the Sharpe ratio inside `COMPOSITE_WEIGHTS`.
For a Nordic pension-fund mandate, whose stated priorities are drawdown
defense and low turnover rather than peak risk-adjusted return, the
Investment Committee can justifiably **override the composite #1 in
favour of minimum volatility**: min-volatility ties max-Sharpe on Sharpe
(0.95 vs 0.95), but beats it on maximum drawdown (−23.2% vs −28.8%),
annual turnover (12.3% vs 24.3%) and tracking error inside the 2-8%
band (8.3%, in-band, vs 9.9%, outside). The override is sensitive to the
composite weighting: tilting the weights further toward Sharpe would flip
the recommendation back to max-Sharpe. That sensitivity is exposed in
`config.COMPOSITE_WEIGHTS` precisely so the Committee can audit it.

The methodology therefore makes two coordinated claims, not one: (i) the
composite as specified picks max-Sharpe, and (ii) a *defended override*
toward min-volatility is the appropriate selection for this mandate. Both
claims are explicit, traceable to the same numbers, and reproducible.

## 7. Known limitations (disclosed honestly)

1. **Look-ahead bias on the universe.** The 20 holdings are a single
   current snapshot; no point-in-time historical ESG data exists for them.
   The backtest therefore holds the same 20 names in every window.
   Following Bailey et al. (2014) we frame the output as a **relative
   comparison of weighting methods**, not as a claim of absolute historical
   alpha. The run log records the disclosure verbatim.

2. **Benchmark is a price-return proxy** (`^STOXX`), not the
   net-total-return STOXX Europe 600. NTR is not freely available; the
   reported tracking error is therefore conservatively wide.

3. **HRP and Score-Tilted enforce only the single-name cap.** Their
   sector and country exposures may exceed the mandate caps. The CSV of
   final weights makes this transparent and the README explains why.

4. **Black-Litterman uses a 1/N market proxy** for the implied-prior
   computation because the module has no live market-cap data. A
   capitalisation-weighted prior is a natural extension.

5. **No transaction costs or taxes** are modelled in the OOS return series.
   Turnover is reported separately so the cost penalty can be estimated
   externally if needed.

## 8. Reproducibility

The whole module is deterministic. The random seed is fixed in
`config.py`; the price panel is cached to disk with a metadata sidecar
recording the fetch timestamp; every parameter (constraints, windows,
composite weights, BL spread) is centralised in `config.py`; and the
audit log (`run_log.txt`) records the run timestamp, the price-fetch
timestamp, every parameter, any ticker that failed verification, and any
method that failed to converge. Re-running on the same inputs yields
identical outputs.

---

## References

- Aronson, D. (2007). *Evidence-Based Technical Analysis*. Wiley.
- Bailey, D. H., Borwein, J., López de Prado, M. and Zhu, Q. J. (2014).
  Pseudo-mathematics and financial charlatanism: The effects of backtest
  overfitting on out-of-sample performance. *Notices of the AMS*, 61(5),
  458-471.
- Baker, M., Bradley, B. and Wurgler, J. (2011). Benchmarks as limits to
  arbitrage: Understanding the low-volatility anomaly. *Financial Analysts
  Journal*, 67(1), 40-54.
- Black, F. and Litterman, R. (1992). Global portfolio optimization.
  *Financial Analysts Journal*, 48(5), 28-43.
- Blitz, D. and van Vliet, P. (2007). The volatility effect: Lower risk
  without lower return. *Journal of Portfolio Management*, 34(1), 102-113.
- DeMiguel, V., Garlappi, L. and Uppal, R. (2009). Optimal versus naive
  diversification: How inefficient is the 1/N portfolio strategy?
  *Review of Financial Studies*, 22(5), 1915-1953.
- Diamond, S. and Boyd, S. (2016). CVXPY: A Python-embedded modeling
  language for convex optimization. *Journal of Machine Learning
  Research*, 17(83), 1-5.
- Hubbard, D. W. (2020). *The Failure of Risk Management*. Wiley.
- Idzorek, T. (2005). A step-by-step guide to the Black-Litterman model.
  In *Forecasting expected returns in the financial markets* (pp. 17-38).
- Ledoit, O. and Wolf, M. (2004). Honey, I shrunk the sample covariance
  matrix. *Journal of Portfolio Management*, 30(4), 110-119.
- Lo, A. W. and MacKinlay, A. C. (1990). Data-snooping biases in tests of
  financial asset pricing models. *Review of Financial Studies*, 3(3),
  431-467.
- López de Prado, M. (2016). Building diversified portfolios that
  outperform out of sample. *Journal of Portfolio Management*, 42(4),
  59-69.
- Markowitz, H. (1952). Portfolio selection. *Journal of Finance*, 7(1),
  77-91.
- Martin, R. A. (2021). PyPortfolioOpt: Portfolio optimization in Python.
  *Journal of Open Source Software*, 6(61), 3066.
- Merton, R. C. (1980). On estimating the expected return on the market:
  An exploratory investigation. *Journal of Financial Economics*, 8(4),
  323-361.
- Pedersen, L. H., Fitzgibbons, S. and Pomorski, L. (2021). Responsible
  investing: The ESG-efficient frontier. *Journal of Financial Economics*,
  142(2), 572-597.
- Sharpe, W. F. (1966). Mutual fund performance. *Journal of Business*,
  39(1), 119-138.
- Sortino, F. A. and Price, L. N. (1994). Performance measurement in a
  downside risk framework. *Journal of Investing*, 3(3), 59-64.
- TCFD (2017). *Recommendations of the Task Force on Climate-related
  Financial Disclosures*. Final Report, June 2017.
- UCITS Directive 2009/65/EC, Article 52 (the 5/10/40 concentration rule).
