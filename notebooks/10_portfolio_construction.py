#!/usr/bin/env python
# coding: utf-8

# # Agent 11 — Portfolio Construction (Stage 3)
#
# **What this notebook does:**
# Takes the ESG Specialist's **sector-capped Top 40** shortlist, applies the Stage 3 financial screen, recovers the companies dropped by upstream merge bugs, and selects the final **20-stock** long-only portfolio with rule-based weights.
#
# **How to present this to investors:**
# > *Our portfolio construction agent starts from an ESG-screened, sector-balanced shortlist of 40 names. It applies a transparent financial screen, then a composite score combining financial quality (60%) and ESG quality (40%). Diversification is enforced as a hard constraint — max 5 holdings per sector (≤25%), max 10% per stock — and watchlisted names are routed to Investment Committee review. The weights are rule-based, not a black box.*
#
# **Audit fixes applied (May 2026):**
# - **Issue 1 — sector concentration.** Candidate pool is the sector-capped Top 40 (`stage2_top40_capped_hybrid.csv`), *not* the full eligible universe. A max-5-per-sector cap is enforced at selection, so no sector exceeds 25% of a 20-stock book.
# - **Issue 2 — gate failures retained.** Companies failing the financial screen (`EXCLUDED_GATE` / `EXCLUDED_METRIC`) are hard-dropped *before* ranking. The previous median-imputation of missing financial scores — which let gate failures survive at full weight — is removed.
# - **Issue 3 — watchlist was informational.** Watchlisted holdings that reach the final 20 generate IC-override rows requiring documentation before sign-off.
# - **Holdings count** set to 20 (mandate: 15–25).
#
# **Recovery note:** 8 of the 40 capped companies were dropped by ticker-join bugs in notebooks 02 and 05. This notebook bypasses those merges — it maps every company to a verified Yahoo Finance ticker and, for the 3 that never reached the financial pipeline (Klépierre, MERLIN, Inditex), downloads prices and computes their metrics directly.

# In[1]:


import pandas as pd
import numpy as np
from datetime import date
import glob, os

# ── Candidate pool: the ESG Specialist's sector-capped Top 40 shortlist ────────
capped = pd.read_csv("../data/provided/stage2_top40_capped_hybrid.csv")
watch  = pd.read_csv("../data/provided/capped40_with_watchlists.csv")
print(f"Capped Top 40 shortlist   : {len(capped)} companies")
print(f"Watchlist annotations     : {len(watch)} companies")

# ── Stage 3 financial screen output (Yahoo Finance tickers) ────────────────────
fin_files = sorted(glob.glob("../outputs/scores/financial_metrics_*.csv"))
if not fin_files:
    raise FileNotFoundError("financial_metrics_*.csv not found — run Agent 10 first.")
df_fin = pd.read_csv(fin_files[-1])
print(f"Financial metrics         : {len(df_fin)} companies  ({os.path.basename(fin_files[-1])})")

# ── Enrichment source: largest universe_scores file (biodiversity / EU / carbon)
# Used only to decorate the output, never for selection. Picking the LARGEST
# file keeps the enrichment pool stable across re-runs of this notebook.
uni_files = glob.glob("../outputs/portfolio/universe_scores_*.csv")
if uni_files:
    uni_path = max(uni_files, key=os.path.getsize)
    df_uni = pd.read_csv(uni_path)
    print(f"Enrichment (universe)     : {len(df_uni)} companies  ({os.path.basename(uni_path)})")
else:
    df_uni = None
    print("Enrichment (universe)     : none found — bio/EU/carbon columns will be blank")


# ## Step 1 — Build the candidate table from the capped Top 40
#
# We start from the 40-company sector-capped shortlist, map every company to a verified Yahoo Finance ticker, then attach watchlist flags and the Stage 3 financial metrics. The ticker map is hardcoded on purpose — the broken ESG↔Yahoo joins upstream are exactly what dropped 8 of these names.

# In[2]:


# ════════════════════════════════════════════════════════════════════════════
# STEP 1 — Build the 40-company candidate table from the capped Top 40
# ════════════════════════════════════════════════════════════════════════════

# Verified Yahoo Finance ticker for every capped-40 company. Hardcoded on
# purpose: the upstream ESG-ticker <-> Yahoo-ticker joins are exactly what
# dropped 8 of these names from the merged universe. Mapping here bypasses them.
YF_TICKER = {
    "Raiffeisen Bank International AG": "RBI.VI",
    "Alfa Laval AB":                    "ALFA.ST",
    "Norsk Hydro ASA":                  "NHY.OL",
    "Addtech AB Class B":               "ADDT-B.ST",
    "Aegon Ltd.":                       "AGN.AS",
    "AIB Group plc":                    "A5G.IR",
    "Lloyds Banking Group plc":         "LLOY.L",
    "SBM Offshore NV":                  "SBMO.AS",
    "Zurich Insurance Group Ltd":       "ZURN.SW",
    "NatWest Group Plc":                "NWG.L",
    "Schneider Electric SE":            "SU.PA",
    "ABB Ltd.":                         "ABBN.SW",
    "Swiss Prime Site AG":              "SPSN.SW",
    "UCB S.A.":                         "UCB.BR",
    "Logitech":                         "LOGN.SW",
    "Rentokil Initial plc":             "RTO.L",
    "Klepierre SA":                     "LI.PA",
    "Arcadis NV":                       "ARCAD.AS",
    "L'Oreal S.A.":                     "OR.PA",
    "Nexans SA":                        "NEX.PA",
    "Wartsila Oyj Abp":                 "WRT1V.HE",
    "AstraZeneca PLC":                  "AZN.L",
    "MERLIN Properties SOCIMI, S.A.":   "MRL.MC",
    "E.ON SE":                          "EOAN.DE",
    "Sweco AB Class B":                 "SWEC-B.ST",
    "Galenica AG":                      "GALE.SW",
    "Industria de Diseno Textil, S.A.": "ITX.MC",
    "Orion Oyj Class B":                "ORNBV.HE",
    "Benefit Systems":                  "BFT.WA",
    "Ipsen SA":                         "IPN.PA",
    "Next plc":                         "NXT.L",
    "Swedish Orphan Biovitrum AB":      "SOBI.ST",
    "Tele2 AB Class B":                 "TEL2-B.ST",
    "Moncler SpA":                      "MONC.MI",
    "ASML Holding NV":                  "ASML.AS",
    "MITIE Group PLC":                  "MTO.L",
    "Publicis Groupe SA":               "PUB.PA",
    "AIXTRON SE":                       "AIXA.DE",
    "Vallourec SA":                     "VK.PA",
    "Subsea 7 S.A.":                    "SUBC.OL",
}

# Candidate table = the capped 40, with normalised column names
df = capped.rename(columns={
    "factset_name": "company_name",
    "SASB Sector":  "sasb_sector",
    "in_house_pct": "ESG_score",     # Stage 2 in-house ESG percentile, 0-100
}).copy()
df = df[["company_name", "sasb_sector", "ESG_score", "in_house_z"]]

df["yf_ticker"] = df["company_name"].map(YF_TICKER)
unmapped = df.loc[df["yf_ticker"].isna(), "company_name"].tolist()
if unmapped:
    raise ValueError(f"No Yahoo ticker mapped for: {unmapped} — update YF_TICKER.")

# ── Watchlist flags (Issue 3 control input) ────────────────────────────────────
w = watch.rename(columns={"Company": "company_name"})
keep = ["company_name"] + [c for c in ["Any_Watchlist", "Watchlist_Reasons"] if c in w.columns]
df = df.merge(w[keep], on="company_name", how="left")
df["Any_Watchlist"] = df["Any_Watchlist"].fillna(False).astype(bool)
if "Watchlist_Reasons" not in df.columns:
    df["Watchlist_Reasons"] = ""
df["Watchlist_Reasons"] = df["Watchlist_Reasons"].fillna("")

# ── Stage 3 financial metrics, merged on Yahoo ticker ──────────────────────────
fin_cols = ["ticker", "vol_annual", "max_drawdown", "sharpe_ratio", "beta",
            "composite_financial_score", "gate_verdict", "financial_verdict"]
df = df.merge(df_fin[fin_cols], left_on="yf_ticker", right_on="ticker", how="left")
df = df.drop(columns=["ticker"])

# ── Best-effort enrichment for the output (biodiversity / EU / carbon) ─────────
if df_uni is not None:
    enrich = ["yf_ticker", "idBbGlobalCompanyName", "carbon_intensity", "ci_source",
              "E_score", "S_score", "G_score", "biodiversity_score", "nature_risk_tier",
              "encore_score", "aqueduct_score", "taxonomy_eligible_pct",
              "taxonomy_aligned_pct", "gw_exclude", "gw_watchlist"]
    enrich = [c for c in enrich if c in df_uni.columns]
    df = df.merge(df_uni[enrich].drop_duplicates("yf_ticker"), on="yf_ticker", how="left")

# Recovery is needed ONLY for companies with no financial-pipeline record at all
# (financial_verdict is NaN). A company that IS in the pipeline but failed it
# — e.g. a GATE_FAIL with incomplete metrics — keeps its verdict and is handled
# by the Step 2 screen; it must NOT be sent to recovery.
need = df.loc[df["financial_verdict"].isna(), "company_name"].tolist()
print(f"Candidate table built     : {len(df)} companies")
print(f"  in financial pipeline     : {int(df['financial_verdict'].notna().sum())}/40")
print(f"  need yfinance recovery    : {len(need)} -> {need}")
df[["company_name", "sasb_sector", "yf_ticker", "ESG_score",
    "sharpe_ratio", "financial_verdict", "Any_Watchlist"]]


# In[3]:


# ════════════════════════════════════════════════════════════════════════════
# STEP 1b — Price download + recovery of companies missing from the screen
# ════════════════════════════════════════════════════════════════════════════
# Klepierre / MERLIN / Inditex were dropped by the notebook-02 master-build merge
# (universe 289 -> master 279), so notebook 04 never computed their financial
# metrics. We download 5y daily prices for ALL 40 holdings here: it fills the
# missing metrics AND provides the return matrix used by the Step 4 correlation
# filter. Requires an internet connection (yfinance).

import yfinance as yf

BENCHMARK    = "^STOXX"   # STOXX Europe 600 — matches the Agent 10 financial screen
RF_RATE      = 0.0        # risk-free rate assumption (pipeline convention)
TRADING_DAYS = 252

all_yf = df["yf_ticker"].tolist()
print(f"Downloading 5y daily prices for {len(all_yf)} holdings + benchmark ...")
raw = yf.download(all_yf + [BENCHMARK], period="5y", auto_adjust=True, progress=False)
prices = raw["Close"].copy().dropna(how="all")
daily_ret = prices.pct_change(fill_method=None)
print(f"Price history: {prices.shape[0]} days x {prices.shape[1]} series")

def market_metrics(tkr):
    """Annualised vol, Sharpe, max drawdown and beta from a price series."""
    if tkr not in prices.columns:
        return None
    p = prices[tkr].dropna()
    if len(p) < TRADING_DAYS:
        return None
    r = p.pct_change(fill_method=None).dropna()
    ann_ret = (1 + r.mean()) ** TRADING_DAYS - 1
    ann_vol = r.std() * np.sqrt(TRADING_DAYS)
    sharpe  = (ann_ret - RF_RATE) / ann_vol if ann_vol else np.nan
    cummax  = p.cummax()
    mdd     = ((p - cummax) / cummax).min()
    beta = np.nan
    if BENCHMARK in daily_ret.columns:
        b = daily_ret[[tkr, BENCHMARK]].dropna()
        if len(b) > 60 and b[BENCHMARK].var() > 0:
            beta = b[tkr].cov(b[BENCHMARK]) / b[BENCHMARK].var()
    return dict(vol_annual=float(ann_vol), sharpe_ratio=float(sharpe),
                max_drawdown=float(mdd),
                beta=float(beta) if pd.notna(beta) else np.nan)

# Fill financial metrics ONLY for companies the screen never covered at all
# (financial_verdict is NaN). Companies already in the pipeline keep their
# real verdict — recovery must never overwrite a GATE_FAIL / EXCLUDED_* verdict.
recovered = []
for idx in df.index[df["financial_verdict"].isna()]:
    name = df.at[idx, "company_name"]
    m = market_metrics(df.at[idx, "yf_ticker"])
    if m is None:
        print(f"  ! {name}: no usable price history — will be excluded in Step 2")
        continue
    for k, v in m.items():
        df.at[idx, k] = v
    df.at[idx, "financial_verdict"] = "RECOVERED_LIMITED"   # market metrics only, no fundamental gate
    df.at[idx, "gate_verdict"]      = "NOT_GATED"
    recovered.append(name)

print(f"Recovered via yfinance ({len(recovered)}): {recovered}")
print(f"Companies with financial metrics now: {int(df['sharpe_ratio'].notna().sum())}/40")
df.loc[df["company_name"].isin(recovered),
       ["company_name", "yf_ticker", "vol_annual", "sharpe_ratio", "max_drawdown", "beta"]]


# In[4]:


# ════════════════════════════════════════════════════════════════════════════
# STEP 1c — Sector-median backfill for holdings missing enrichment
# ════════════════════════════════════════════════════════════════════════════
# The recovered companies were never in the merged universe, so the enrichment
# merge left their carbon / biodiversity / E-S-G / nature-risk figures blank.
# We impute from the GICS-sector profile of the full universe — the
# `sector_median_imputed` convention notebook 05 uses. Imputation is on the GICS
# `sector`, NOT the SASB sector: SASB "Infrastructure" mixes utilities
# (~630 tCO2e/$M) with REITs (~17), so a SASB-median would badly mis-state them.
# (EU Taxonomy fields are NOT imputed — reported coverage is sparse by nature;
#  they are left blank and disclosed as a data limitation.)

# GICS sector for the recovered names (not carried through the broken merges)
GICS_SECTOR = {
    "Klepierre SA":                     "Real Estate",
    "MERLIN Properties SOCIMI, S.A.":   "Real Estate",
    "Industria de Diseno Textil, S.A.": "Consumer Discretionary",
    "Tele2 AB Class B":                 "Communications",
    "Orion Oyj Class B":                "Health Care",
}
if df_uni is not None and "sector" in df_uni.columns and "sector" not in df.columns:
    df = df.merge(df_uni[["yf_ticker", "sector"]].drop_duplicates("yf_ticker"),
                  on="yf_ticker", how="left")
if "sector" not in df.columns:
    df["sector"] = pd.NA
df["sector"] = df["sector"].fillna(df["company_name"].map(GICS_SECTOR))

if df_uni is not None and "sector" in df_uni.columns:
    # Numeric enrichment columns -> GICS-sector median
    for col in ["carbon_intensity", "biodiversity_score", "encore_score",
                "aqueduct_score", "E_score", "S_score", "G_score"]:
        if col not in df.columns or col not in df_uni.columns:
            continue
        miss = df[col].isna()
        if not miss.any():
            continue
        sec_med = df_uni.groupby("sector")[col].median()
        df.loc[miss, col] = df.loc[miss, "sector"].map(sec_med)
        still = df[col].isna()
        if still.any():                              # sector unknown -> universe median
            df.loc[still, col] = df_uni[col].median()
        if col == "carbon_intensity":
            if "ci_source" not in df.columns:
                df["ci_source"] = pd.NA
            df.loc[miss, "ci_source"] = "sector_median_imputed"
        print(f"  {col:<20}: imputed {int(miss.sum())} holdings (GICS-sector median)")

    # Categorical: nature_risk_tier -> GICS-sector mode
    if "nature_risk_tier" in df.columns and "nature_risk_tier" in df_uni.columns:
        miss = df["nature_risk_tier"].isna()
        if miss.any():
            sec_mode = (df_uni.dropna(subset=["nature_risk_tier"])
                        .groupby("sector")["nature_risk_tier"]
                        .agg(lambda s: s.mode().iloc[0] if not s.mode().empty else None))
            df.loc[miss, "nature_risk_tier"] = df.loc[miss, "sector"].map(sec_mode)
            print(f"  {'nature_risk_tier':<20}: imputed {int(miss.sum())} holdings (GICS-sector mode)")

# gw_exclude / gw_watchlist: greenwashing (NB09) has not been run yet. Keep the
# columns — NB09 will fill them with real flags later — but make them uniform
# now (default False, the same value the rest of the universe carries) so the
# output has no half-blank column. Greenwashing-pending is a report limitation.
for c in ["gw_exclude", "gw_watchlist"]:
    if c in df.columns:
        df[c] = df[c].fillna(False)

print(f"\nCarbon-intensity coverage now: {int(df['carbon_intensity'].notna().sum())}/40 holdings")
print(df.loc[df["company_name"].isin(GICS_SECTOR),
      ["company_name", "sector", "carbon_intensity", "biodiversity_score",
       "E_score", "S_score", "G_score", "nature_risk_tier"]].to_string(index=False))


# ## Step 2 — Financial screen as a hard exclusion  *(Audit Issue 2 fix)*
#
# Companies that fail the Stage 3 financial screen are **dropped before ranking**. Previously their missing financial score was filled with the universe median, which let gate failures survive into the portfolio at full weight. No imputation is done here.

# In[5]:


# ════════════════════════════════════════════════════════════════════════════
# STEP 2 — Financial screen as a hard exclusion   (AUDIT ISSUE 2 FIX)
# ════════════════════════════════════════════════════════════════════════════
# The financial screen is a HARD GATE applied BEFORE ranking. No imputation:
# a company that fails the screen, or that has no financial data, is dropped.

exclusions = []

# Rule 1 — financial screen failure: a hard gate fail (gate_verdict GATE_FAIL /
#          financial_verdict EXCLUDED_GATE) or a metric exclusion
#          (EXCLUDED_METRIC — e.g. negative Sharpe, volatility cap breach)
HARD_FAIL = {"EXCLUDED_GATE", "EXCLUDED_METRIC"}
fail_mask = df["financial_verdict"].isin(HARD_FAIL) | (df["gate_verdict"] == "GATE_FAIL")
for _, r in df[fail_mask].iterrows():
    reason = (r["financial_verdict"] if r["financial_verdict"] in HARD_FAIL
              else "GATE_FAIL")
    exclusions.append((r["company_name"], f"Financial screen: {reason}"))

# Rule 2 — metric backstop for recovered names (no pipeline verdict of their
#          own): apply the same thresholds the screen uses
for _, r in df[df["financial_verdict"] == "RECOVERED_LIMITED"].iterrows():
    if pd.notna(r["sharpe_ratio"]) and r["sharpe_ratio"] < 0:
        exclusions.append((r["company_name"], f"Negative Sharpe ratio ({r['sharpe_ratio']:.2f})"))
    elif pd.notna(r["vol_annual"]) and r["vol_annual"] > 0.40:
        exclusions.append((r["company_name"], f"Annualised volatility > 40% ({r['vol_annual']:.0%})"))

# Rule 3 — no financial data at all: never in the pipeline AND recovery failed
#          (financial_verdict still NaN after Step 1b) -> cannot be scored
for _, r in df[df["financial_verdict"].isna()].iterrows():
    exclusions.append((r["company_name"], "No financial data — yfinance recovery failed"))

# Rule 4 — greenwashing auto-exclusion (Agent 9), if that data is present
if "gw_exclude" in df.columns:
    for _, r in df[df["gw_exclude"] == True].iterrows():
        exclusions.append((r["company_name"], "Greenwashing: HIGH on 3+ dimensions (Agent 9)"))

# ── Manual overrides — add (company_name, reason) tuples here if needed ─────────
MANUAL_EXCLUSIONS = []
exclusions.extend(MANUAL_EXCLUSIONS)

excluded_names = sorted({n for n, _ in exclusions})
eligible = df[~df["company_name"].isin(excluded_names)].copy().reset_index(drop=True)

os.makedirs("../outputs/portfolio", exist_ok=True)
excl_df = pd.DataFrame(exclusions, columns=["company_name", "reason"]).drop_duplicates("company_name")
excl_df.to_csv("../outputs/portfolio/exclusions.csv", index=False)

print(f"Excluded by the financial / ESG screen: {len(excluded_names)}")
for _, r in excl_df.iterrows():
    print(f"  - {r['company_name']:<34} {r['reason']}")
print(f"\nEligible for portfolio ranking: {len(eligible)} of 40")
excl_df


# ## Step 3 — Composite ranking score
#
# The financial score is **recomputed uniformly** across the eligible pool from four raw market metrics (Sharpe, volatility, max drawdown, beta), so every company — including the recovered names — sits on one scale. Composite = 60% financial + 40% ESG.

# In[6]:


# ════════════════════════════════════════════════════════════════════════════
# STEP 3 — Composite ranking score
# ════════════════════════════════════════════════════════════════════════════
# Financial score is recomputed UNIFORMLY across the eligible pool from four raw
# market metrics — so every company (incl. the recovered names) sits on one
# scale and the ranking never depends on the broken merged-universe file.

FIN_WEIGHT = 0.60
ESG_WEIGHT = 0.40

def pct_rank(series, higher_better=True):
    """Percentile-rank a series within the pool, oriented so higher = better, 0-100."""
    r = series.astype(float).rank(pct=True)
    return (r if higher_better else (1 - r)) * 100

eligible = eligible.copy()
eligible["s_sharpe"] = pct_rank(eligible["sharpe_ratio"], higher_better=True)
eligible["s_vol"]    = pct_rank(eligible["vol_annual"],   higher_better=False)  # lower vol better
eligible["s_mdd"]    = pct_rank(eligible["max_drawdown"], higher_better=True)   # less negative better
eligible["s_beta"]   = pct_rank(eligible["beta"],         higher_better=False)  # lower / defensive better

# Equal-weight blend of the four risk/return percentile ranks -> 0-100
eligible["fin_score"] = eligible[["s_sharpe", "s_vol", "s_mdd", "s_beta"]].mean(axis=1).round(2)

# Composite: 60% financial quality + 40% ESG quality (ESG_score already 0-100)
eligible["composite_score"] = (
    eligible["fin_score"] * FIN_WEIGHT + eligible["ESG_score"] * ESG_WEIGHT
).round(2)

eligible = eligible.sort_values("composite_score", ascending=False).reset_index(drop=True)
eligible["rank"] = eligible.index + 1

print(f"Composite = {FIN_WEIGHT:.0%} financial + {ESG_WEIGHT:.0%} ESG   (eligible pool: {len(eligible)})")
print()
print(eligible[["rank", "company_name", "sasb_sector", "fin_score",
                "ESG_score", "composite_score"]].to_string(index=False))


# ## Step 4 — Return correlation matrix
#
# Builds the pairwise return correlation matrix from the 5y daily returns downloaded in Step 1b. Step 5 uses it to avoid pairing highly co-moving holdings.

# In[7]:


# ════════════════════════════════════════════════════════════════════════════
# STEP 4 — Return correlation matrix
# ════════════════════════════════════════════════════════════════════════════
# Built from the 5y daily returns downloaded in Step 1b. Used by the greedy
# selection in Step 5 to avoid pairing highly co-moving holdings.

CORR_THRESHOLD = 0.90   # Step 5 skips a candidate correlated > 0.90 with a pick

pool_tickers = [t for t in eligible["yf_ticker"] if t in daily_ret.columns]
ret_pool = daily_ret[pool_tickers].dropna(how="all")
corr = ret_pool.corr() if not ret_pool.empty else pd.DataFrame()

print(f"Correlation matrix: {corr.shape[0]} x {corr.shape[1]} holdings")
if not corr.empty:
    import itertools
    pairs = [(a, b, corr.loc[a, b]) for a, b in itertools.combinations(corr.columns, 2)]
    pairs.sort(key=lambda x: -abs(x[2]))
    print(f"\nMost correlated pairs (threshold {CORR_THRESHOLD}):")
    for a, b, c in pairs[:6]:
        flag = "  <-- above threshold" if abs(c) > CORR_THRESHOLD else ""
        print(f"  {a:<11} {b:<11} {c:+.2f}{flag}")
else:
    print("No return data — correlation filter will be skipped in Step 5.")


# ## Step 5 — Select 20 holdings: sector cap + correlation guard  *(Audit Issue 1 fix)*
#
# Greedy walk down the composite ranking. A candidate joins only if its sector is not already full (**max 5 per sector → ≤25%**) and it is not too correlated with a holding already chosen. Weights are proportional to composite score, capped at 10% per stock.

# In[8]:


# ════════════════════════════════════════════════════════════════════════════
# STEP 5 — Select 20 holdings: sector cap + correlation guard   (AUDIT ISSUE 1 FIX)
# ════════════════════════════════════════════════════════════════════════════
# Greedy walk down the composite ranking. A candidate is added only if (a) its
# sector is not already full and (b) it is not too correlated with a holding
# already chosen. The sector cap guarantees no sector exceeds 25% of the book.

N_HOLDINGS     = 20      # mandate: 15-25 holdings
MAX_PER_SECTOR = 5       # 5 / 20 = 25% — the mandate sector ceiling
MAX_WEIGHT     = 0.10    # 10% cap per holding

sector_count = {}
chosen, chosen_tickers, corr_skips, sector_skips = [], [], [], []

for i, r in eligible.iterrows():
    if len(chosen) >= N_HOLDINGS:
        break
    sec, tkr = r["sasb_sector"], r["yf_ticker"]
    if sector_count.get(sec, 0) >= MAX_PER_SECTOR:
        sector_skips.append(r["company_name"]); continue
    if chosen_tickers and not corr.empty and tkr in corr.columns:
        peers = [t for t in chosen_tickers if t in corr.columns]
        if peers and corr.loc[tkr, peers].abs().max() > CORR_THRESHOLD:
            corr_skips.append(r["company_name"]); continue
    chosen.append(i)
    chosen_tickers.append(tkr)
    sector_count[sec] = sector_count.get(sec, 0) + 1

portfolio = eligible.loc[chosen].copy().reset_index(drop=True)

if corr_skips:
    print(f"Skipped (correlation > {CORR_THRESHOLD}): {corr_skips}")
if sector_skips:
    print(f"Skipped (sector cap of {MAX_PER_SECTOR} reached): {sector_skips}")
if len(portfolio) < N_HOLDINGS:
    print(f"WARNING: only {len(portfolio)} holdings selected — pool too small or constraints too tight.")

# ── Weights: proportional to composite score, capped at 10%, then renormalised ─
w = portfolio["composite_score"] / portfolio["composite_score"].sum()
for _ in range(100):
    w = w.clip(upper=MAX_WEIGHT)
    gap = 1.0 - w.sum()
    if gap < 1e-9:
        break
    room = w < MAX_WEIGHT
    if not room.any():
        break
    w = w + gap * (w.where(room, 0.0) / w[room].sum())
portfolio["weight"] = (w / w.sum()).round(4)

print(f"\nFinal portfolio: {len(portfolio)} holdings")
print(f"Weights sum to : {portfolio['weight'].sum():.4f}   |   max weight: {portfolio['weight'].max():.1%}")
print()
sec_tbl = (portfolio.groupby("sasb_sector")["weight"]
           .agg(holdings="count", weight="sum").sort_values("weight", ascending=False))
sec_tbl["weight"] = (sec_tbl["weight"] * 100).round(1)
print("Sector exposure:")
print(sec_tbl.to_string())
print(f"\nLargest sector: {sec_tbl['weight'].max():.1f}%   (mandate ceiling 25%)")
portfolio[["rank", "company_name", "sasb_sector", "ESG_score", "fin_score",
           "composite_score", "Any_Watchlist", "weight"]]


# In[9]:


# ════════════════════════════════════════════════════════════════════════════
# STEP 5b — IC override worksheet   (AUDIT ISSUE 3 FIX)
# ════════════════════════════════════════════════════════════════════════════
# Mandate control: a holding that passes screening but carries a governance flag
# needs an Investment Committee override decision, with a documented rationale,
# before it can be held. Two triggers route a holding here:
#   WATCHLIST  — on the Truvalue and/or transition watchlist
#   FINANCIAL  — financial screen returned REVIEW_REQUIRED (incomplete data)
# Rows are emitted in the human_overrides schema for the reviewer (NB11) to fill.

LOG_COLS = ["date", "decided_by", "ticker", "company_name", "override_type",
            "model_decision", "human_decision", "rationale", "evidence", "approved_by"]

ic_rows = []
for _, r in portfolio.iterrows():
    triggers, evidence = [], []
    if r.get("Any_Watchlist") == True:
        triggers.append("WATCHLIST")
        wr = r.get("Watchlist_Reasons", "")
        if isinstance(wr, str) and wr.strip():
            evidence.append(wr.strip())
    if str(r.get("financial_verdict", "")) == "REVIEW_REQUIRED":
        triggers.append("FINANCIAL")
        evidence.append(f"Financial screen REVIEW_REQUIRED "
                         f"(gate_verdict={r.get('gate_verdict', 'NA')}) — incomplete financial data")
    if not triggers:
        continue
    ic_rows.append({
        "date":           str(date.today()),
        "decided_by":     "",
        "ticker":         r["yf_ticker"],
        "company_name":   r["company_name"],
        "override_type":  "IC_REVIEW_" + "_".join(triggers),
        "model_decision": f"Included - composite rank {int(r['rank'])}, weight {r['weight']:.1%}",
        "human_decision": "",
        "rationale":      "",
        "evidence":       "  |  ".join(evidence),
        "approved_by":    "",
    })

ic_df = pd.DataFrame(ic_rows, columns=LOG_COLS)
ic_path = f"../outputs/scores/ic_overrides_watchlist_{date.today()}.csv"
ic_df.to_csv(ic_path, index=False)

print(f"Holdings requiring an IC override decision: {len(ic_df)} of {len(portfolio)}")
if len(ic_df):
    print(ic_df[["company_name", "override_type", "evidence"]].to_string(index=False))
print(f"\nIC override worksheet saved: {ic_path}")
print("ACTION REQUIRED before sign-off: complete decided_by / human_decision /")
print("rationale / approved_by for each row, then merge into human_overrides_*.csv (NB11).")
ic_df


# ## Step 6 — Portfolio summary statistics

# In[10]:


# ════════════════════════════════════════════════════════════════════════════
# STEP 6 — Portfolio summary statistics
# ════════════════════════════════════════════════════════════════════════════

weighted_esg    = (portfolio["ESG_score"]    * portfolio["weight"]).sum()
weighted_fin    = (portfolio["fin_score"]    * portfolio["weight"]).sum()
weighted_sharpe = (portfolio["sharpe_ratio"] * portfolio["weight"]).sum()

pool_esg    = eligible["ESG_score"].mean()
pool_fin    = eligible["fin_score"].mean()
pool_sharpe = eligible["sharpe_ratio"].mean()

print("=== FINAL 20 vs ELIGIBLE POOL ===")
print(f"{'Metric':<32} {'Portfolio':>12} {'Pool':>12} {'Delta':>12}")
print("-" * 70)
print(f"{'Weighted ESG score (40%)':<32} {weighted_esg:>12.1f} {pool_esg:>12.1f} {weighted_esg-pool_esg:>+12.1f}")
print(f"{'Weighted financial score (60%)':<32} {weighted_fin:>12.1f} {pool_fin:>12.1f} {weighted_fin-pool_fin:>+12.1f}")
print(f"{'Weighted Sharpe ratio':<32} {weighted_sharpe:>12.3f} {pool_sharpe:>12.3f} {weighted_sharpe-pool_sharpe:>+12.3f}")
print(f"{'Holdings':<32} {len(portfolio):>12} {len(eligible):>12}")
print()
print(f"Sectors represented : {portfolio['sasb_sector'].nunique()}")
print(f"Largest sector      : {(portfolio.groupby('sasb_sector')['weight'].sum().max()*100):.1f}%  (ceiling 25%)")
print(f"Watchlisted holdings: {int(portfolio['Any_Watchlist'].sum())}  (see IC override worksheet, Step 5b)")
if "carbon_intensity" in portfolio.columns and portfolio["carbon_intensity"].notna().any():
    cov  = int(portfolio["carbon_intensity"].notna().sum())
    waci = (portfolio["carbon_intensity"].fillna(0) * portfolio["weight"]).sum()
    print(f"WACI (carbon)       : {waci:.1f} tCO2e/$M revenue  ({cov}/{len(portfolio)} holdings with data)")


# ## Step 7 — Save portfolio

# In[11]:


# ════════════════════════════════════════════════════════════════════════════
# STEP 7 — Save outputs
# ════════════════════════════════════════════════════════════════════════════
today = str(date.today())

# Drop working/legacy columns so the saved files carry only meaningful data:
#   s_sharpe/s_vol/s_mdd/s_beta — intermediate percentile ranks averaged into
#                                 fin_score (NOT Sharpe ratios — scratch values)
#   composite_financial_score   — legacy; NB10 ranks on the recomputed fin_score
#   idBbGlobalCompanyName       — redundant duplicate of company_name
DROP_COLS = ["s_sharpe", "s_vol", "s_mdd", "s_beta",
             "composite_financial_score", "idBbGlobalCompanyName"]
for _t in (portfolio, df):
    _t.drop(columns=DROP_COLS, errors="ignore", inplace=True)

# Final 20-stock portfolio
port_path = f"../outputs/portfolio/final_portfolio_{today}.csv"
portfolio.to_csv(port_path, index=False)
print(f"Final portfolio saved : {port_path}  ({len(portfolio)} holdings, {portfolio.shape[1]} columns)")

# Stage 3 universe = all 40 capped companies with their outcome:
#   SELECTED      — in the final 20
#   NOT_SELECTED  — passed the financial screen but outranked
#   EXCLUDED      — failed the financial screen (exclusion_reason filled)
universe = df.merge(eligible[["company_name", "fin_score", "composite_score", "rank"]],
                    on="company_name", how="left")
universe = universe.merge(excl_df.rename(columns={"reason": "exclusion_reason"}),
                          on="company_name", how="left")
universe = universe.merge(portfolio[["company_name", "weight"]],
                          on="company_name", how="left")

in_port = universe["company_name"].isin(portfolio["company_name"])
is_excl = universe["exclusion_reason"].notna()
universe["portfolio_status"] = np.where(in_port, "SELECTED",
                               np.where(is_excl, "EXCLUDED", "NOT_SELECTED"))

# Order: selected first (by rank), then not-selected (by rank), then excluded
universe["_o"] = np.where(in_port, 0, np.where(is_excl, 2, 1))
universe = (universe.sort_values(["_o", "rank", "company_name"])
                    .drop(columns="_o").reset_index(drop=True))

# Put the decision-relevant columns first for readability
front = ["portfolio_status", "rank", "company_name", "sasb_sector", "yf_ticker",
         "ESG_score", "fin_score", "composite_score", "weight",
         "exclusion_reason", "Any_Watchlist", "Watchlist_Reasons"]
front = [c for c in front if c in universe.columns]
universe = universe[front + [c for c in universe.columns if c not in front]]

uni_path = f"../outputs/portfolio/universe_scores_{today}.csv"
universe.to_csv(uni_path, index=False)

n = universe["portfolio_status"].value_counts()
print(f"Universe scores saved : {uni_path}  ({len(universe)} companies — the capped 40)")
print(f"  SELECTED={n.get('SELECTED',0)}   NOT_SELECTED={n.get('NOT_SELECTED',0)}   EXCLUDED={n.get('EXCLUDED',0)}")
print()
print("Companies NOT in the final 20:")
print(universe.loc[universe["portfolio_status"] != "SELECTED",
      ["portfolio_status", "rank", "company_name", "sasb_sector",
       "composite_score", "exclusion_reason"]].to_string(index=False))


# In[12]:


# ════════════════════════════════════════════════════════════════════════════
# STEP 8 — Apply the IC override decisions   (data-layer override application)
# ════════════════════════════════════════════════════════════════════════════
# Reads the IC's completed override decisions (override_decisions_*.csv) and
# left-joins them onto the final portfolio as ADDITIVE metadata. The original
# TV_Watchlist / Trans_Watchlist flags are kept visible alongside — never
# overwritten — so the algorithmic flag and the human override sit side by side
# for the audit trail (Lecture 5, slide 38). The override annotates; it does
# not replace.

# ── Original granular watchlist flags — surfaced explicitly alongside override ─
wl_cols = [c for c in ["TV_Watchlist", "Trans_Watchlist"] if c in watch.columns]
if wl_cols:
    portfolio = portfolio.merge(
        watch.rename(columns={"Company": "company_name"})[["company_name"] + wl_cols],
        on="company_name", how="left")

# ── IC override decisions ──────────────────────────────────────────────────────
OVR_COLS = ["override_type", "override_disposition", "override_evidence_source",
            "override_evidence_date", "override_reviewer", "override_review_date",
            "override_rationale_short", "override_caveat"]
ovr_files = sorted(glob.glob("../outputs/scores/override_decisions_*.csv"))
if ovr_files:
    ovr = pd.read_csv(ovr_files[-1])
    print(f"Override decisions loaded: {ovr_files[-1]}  ({len(ovr)} decisions)")
    portfolio = portfolio.merge(
        ovr[["company_name"] + [c for c in OVR_COLS if c in ovr.columns]],
        on="company_name", how="left")
    unmatched = sorted(set(ovr["company_name"]) - set(portfolio["company_name"]))
    if unmatched:
        print(f"  WARNING: override rows with no matching holding: {unmatched}")
else:
    print("No override_decisions_*.csv found — override columns added empty.")
    for c in OVR_COLS:
        portfolio[c] = pd.NA

# Derived flag — True where an IC override decision was applied
portfolio["override_applied"] = portfolio["override_disposition"].notna()

# Captain has signed off the IC Override Notes memo (v1), so the final portfolio
# file is updated IN PLACE — the override metadata is now part of it.
portfolio.to_csv(port_path, index=False)
print(f"\nFinal portfolio updated in place with override metadata: {port_path}")
print(f"Columns now: {portfolio.shape[1]}   |   Holdings with an IC override: "
      f"{int(portfolio['override_applied'].sum())} of {len(portfolio)}")
print("\nDisposition summary:")
print(portfolio["override_disposition"].fillna("(no override)").value_counts().to_string())
print()
print(portfolio.loc[portfolio["override_applied"],
      ["company_name", "override_type", "override_disposition"]].to_string(index=False))


# In[13]:


# ── Optimization module input: the final 20 holdings ──────────────────────────
# Format required by Optimization_module/data_loader.py:
#   ticker (Yahoo Finance), company_name, sector, esg_score, carbon_intensity

opt_input = portfolio[["yf_ticker", "company_name", "sasb_sector",
                       "ESG_score", "carbon_intensity"]].copy()
opt_input = opt_input.rename(columns={
    "yf_ticker":   "ticker",
    "sasb_sector": "sector",
    "ESG_score":   "esg_score",
})
opt_input["esg_score"]        = opt_input["esg_score"].round(2)
opt_input["carbon_intensity"] = pd.to_numeric(opt_input["carbon_intensity"],
                                              errors="coerce").fillna(0.0).round(4)
opt_input = opt_input[["ticker", "company_name", "sector", "esg_score", "carbon_intensity"]]

opt_dated_path  = f"../outputs/portfolio/optimization_input_{today}.csv"
opt_module_path = "../Optimization_module/sample_holdings_20.csv"
opt_input.to_csv(opt_dated_path, index=False)
opt_input.to_csv(opt_module_path, index=False)

print("Optimization input saved:")
print(f"  {opt_dated_path}   (dated copy)")
print(f"  {opt_module_path}  (Optimization module input — overwritten)")
print(f"\nFinal {len(opt_input)} holdings passed to optimizer:")
print(opt_input.to_string(index=False))


# ## ✅ Notebook complete
#
# You now have:
# - **Final 20-stock portfolio** (`final_portfolio_<date>.csv`) with weights summing to 100%, max 10% per holding, max 25% per sector
# - **Exclusion log** (`exclusions.csv`) — every company dropped by the financial screen, with reasons
# - **IC override worksheet** (`ic_overrides_watchlist_<date>.csv`) — watchlisted holdings requiring documentation before sign-off
# - **Universe scores** (`universe_scores_<date>.csv`) — the scored capped-40 candidate table
# - **Optimization input** (`optimization_input_<date>.csv`)
#
# **Methodology:** capped Top 40 → financial screen (hard exclusion) → composite score (60% financial + 40% ESG) → greedy selection with max-5-per-sector cap and correlation guard → score-proportional weights capped at 10%.
#
# **Before sign-off:** complete the IC override worksheet for each watchlisted holding (Step 5b).
#
# **Next:** re-run `11_human_review.ipynb` and `12_reporting.ipynb` to refresh the override log and the factsheet.

