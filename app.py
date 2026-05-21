"""
ESADE Sustainable Finance Dashboard
Run with:  venv/Scripts/streamlit.exe run app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import glob
import os
from datetime import date

# ── Page config ───────────────────────────────────────────────
st.set_page_config(
    page_title="ESADE Sustainable Finance",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Colours ───────────────────────────────────────────────────
DARK_BLUE  = "#1F497D"
MID_BLUE   = "#2E74B5"
LIGHT_BLUE = "#D6E4F0"
GREEN      = "#2E7D32"
RED        = "#C62828"
AMBER      = "#F57F17"

# ── CSS ───────────────────────────────────────────────────────
st.markdown(f"""
<style>
    .main-header {{
        background: linear-gradient(135deg, {DARK_BLUE}, {MID_BLUE});
        color: white;
        padding: 1.5rem 2rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
    }}
    .main-header h1 {{ color: white; margin: 0; font-size: 1.8rem; }}
    .main-header p  {{ color: #cce0ff; margin: 0.3rem 0 0 0; font-size: 0.95rem; }}
    .metric-card {{
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        text-align: center;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    }}
    .metric-card .label {{ font-size: 0.78rem; color: #666; font-weight: 500; text-transform: uppercase; letter-spacing: 0.04em; }}
    .metric-card .value {{ font-size: 1.7rem; font-weight: 700; color: {DARK_BLUE}; margin-top: 0.2rem; }}
    .metric-card .sub   {{ font-size: 0.8rem; color: #888; margin-top: 0.15rem; }}
    .section-header {{
        font-size: 1.15rem;
        font-weight: 700;
        color: {DARK_BLUE};
        border-left: 4px solid {MID_BLUE};
        padding-left: 0.7rem;
        margin: 1.5rem 0 0.8rem 0;
    }}
    .tag-green  {{ background:#e8f5e9; color:#2e7d32; padding:2px 8px; border-radius:4px; font-size:0.78rem; font-weight:600; }}
    .tag-red    {{ background:#ffebee; color:#c62828; padding:2px 8px; border-radius:4px; font-size:0.78rem; font-weight:600; }}
    .tag-amber  {{ background:#fff8e1; color:#f57f17; padding:2px 8px; border-radius:4px; font-size:0.78rem; font-weight:600; }}
    .tag-blue   {{ background:{LIGHT_BLUE}; color:{DARK_BLUE}; padding:2px 8px; border-radius:4px; font-size:0.78rem; font-weight:600; }}
    div[data-testid="stDataFrame"] {{ border-radius: 8px; overflow: hidden; }}
</style>
""", unsafe_allow_html=True)


# ── Data loaders (always pick latest file) ────────────────────
@st.cache_data(ttl=60)
def load_latest(pattern):
    files = sorted(glob.glob(pattern))
    if not files:
        return None
    return pd.read_csv(files[-1])

@st.cache_data(ttl=60)
def load_mandate():
    p = "outputs/scores/mandate.json"
    if not os.path.exists(p):
        return {}
    with open(p) as f:
        return json.load(f)

@st.cache_data(ttl=60)
def load_optimization():
    p_results = "Optimization_module/outputs/backtest_results.csv"
    if os.path.exists(p_results):
        try:
            return pd.read_csv(p_results)
        except Exception:
            return None
    return None

def load_all():
    portfolio  = load_latest("outputs/portfolio/final_portfolio_*.csv")
    universe   = load_latest("outputs/portfolio/universe_scores_*.csv")
    exclusions = load_latest("outputs/portfolio/exclusions.csv")
    esg        = load_latest("outputs/scores/esg_scores_*.csv")
    financial  = load_latest("outputs/scores/financial_metrics_*.csv")
    bio        = load_latest("outputs/scores/biodiversity_scores_*.csv")
    master     = load_latest("outputs/scores/master_dataset_*.csv")
    mandate    = load_mandate()
    return portfolio, universe, exclusions, esg, financial, bio, master, mandate


# ── Sidebar navigation ────────────────────────────────────────
st.sidebar.markdown(f"""
<div style='background:{DARK_BLUE}; padding:1rem; border-radius:8px; margin-bottom:1rem;'>
    <div style='color:white; font-weight:700; font-size:1.05rem;'>🌱 ESADE SF</div>
    <div style='color:#cce0ff; font-size:0.78rem;'>Sustainable Finance Pipeline</div>
</div>
""", unsafe_allow_html=True)

page = st.sidebar.radio(
    "Navigate",
    ["🏠 Overview", "📊 Portfolio Holdings", "🌱 ESG Scores",
     "📈 Risk & Returns", "⚙️ Portfolio Optimization", "🌍 Climate & Biodiversity",
     "⚠️ Greenwashing", "🚫 Exclusions", "📋 Mandate"],
    label_visibility="collapsed"
)

st.sidebar.markdown("---")
st.sidebar.caption(f"Data as of: {date.today().strftime('%d %b %Y')}")
st.sidebar.caption("Mock data — replace Friday with real sources")

# ── Load data ─────────────────────────────────────────────────
portfolio, universe, exclusions, esg, financial, bio, master, mandate = load_all()


# ══════════════════════════════════════════════════════════════
#  PAGE 1 — OVERVIEW
# ══════════════════════════════════════════════════════════════
if page == "🏠 Overview":

    st.markdown(f"""
    <div class='main-header'>
        <h1>🌱 ESADE Sustainable Finance Portfolio</h1>
        <p>AI-powered ESG investment pipeline · European Equity Universe · Long-Only</p>
    </div>
    """, unsafe_allow_html=True)

    # Key metrics row
    if portfolio is not None:
        c1, c2, c3, c4, c5 = st.columns(5)
        wt_esg   = (portfolio['ESG_score'] * portfolio['weight']).sum()
        wt_sh    = (portfolio['sharpe_ratio'] * portfolio['weight']).sum()
        avg_ret  = (portfolio['annual_return_pct'] * portfolio['weight']).sum()
        avg_vol  = (portfolio['annual_volatility_pct'] * portfolio['weight']).sum()
        n_stocks = len(portfolio)

        for col, label, value, sub in [
            (c1, "Holdings",           f"{n_stocks}",          "stocks selected"),
            (c2, "Weighted ESG",       f"{wt_esg:.1f}/100",    "composite score"),
            (c3, "Weighted Sharpe",    f"{wt_sh:.2f}",         "risk-adjusted return"),
            (c4, "Wtd Annual Return",  f"{avg_ret:.1f}%",      "5-year average"),
            (c5, "Wtd Volatility",     f"{avg_vol:.1f}%",      "annual std dev"),
        ]:
            with col:
                st.markdown(f"""
                <div class='metric-card'>
                    <div class='label'>{label}</div>
                    <div class='value'>{value}</div>
                    <div class='sub'>{sub}</div>
                </div>""", unsafe_allow_html=True)

    st.markdown("")

    col_left, col_right = st.columns([1, 1])

    # Portfolio weights donut chart
    with col_left:
        st.markdown("<div class='section-header'>Portfolio Weights</div>", unsafe_allow_html=True)
        if portfolio is not None:
            fig = px.pie(
                portfolio,
                names="ticker",
                values="weight",
                hole=0.45,
                color_discrete_sequence=px.colors.sequential.Blues_r,
            )
            fig.update_traces(textposition='outside', textinfo='label+percent')
            fig.update_layout(
                margin=dict(l=20, r=20, t=20, b=20),
                showlegend=False,
                height=380,
            )
            st.plotly_chart(fig, use_container_width=True)

    # ESG vs Sharpe scatter
    with col_right:
        st.markdown("<div class='section-header'>ESG Score vs Sharpe Ratio</div>", unsafe_allow_html=True)
        if portfolio is not None:
            fig2 = px.scatter(
                portfolio,
                x="ESG_score",
                y="sharpe_ratio",
                size="weight",
                text="ticker",
                color="ESG_score",
                color_continuous_scale="Blues",
                size_max=40,
                labels={"ESG_score": "ESG Score", "sharpe_ratio": "Sharpe Ratio", "weight": "Portfolio Weight"},
            )
            fig2.update_traces(textposition='top center', textfont_size=9)
            fig2.update_layout(
                margin=dict(l=20, r=20, t=20, b=20),
                height=380,
                coloraxis_showscale=False,
            )
            st.plotly_chart(fig2, use_container_width=True)

    # Investment thesis
    if mandate:
        st.markdown("<div class='section-header'>Investment Thesis</div>", unsafe_allow_html=True)
        st.info(mandate.get("investment_thesis", "—"))

    # Sector breakdown
    if portfolio is not None and master is not None:
        st.markdown("<div class='section-header'>Sector Breakdown</div>", unsafe_allow_html=True)
        merged = portfolio.merge(master[['ticker','bics_sector','companyName']], on='ticker', how='left')
        sector_w = merged.groupby('bics_sector')['weight'].sum().reset_index()
        sector_w.columns = ['Sector', 'Weight']
        sector_w['Weight %'] = (sector_w['Weight'] * 100).round(1)
        fig3 = px.bar(
            sector_w.sort_values('Weight %', ascending=True),
            x='Weight %', y='Sector', orientation='h',
            color='Weight %', color_continuous_scale='Blues',
            text='Weight %',
        )
        fig3.update_traces(texttemplate='%{text}%', textposition='outside')
        fig3.update_layout(margin=dict(l=20, r=20, t=10, b=20), height=320, coloraxis_showscale=False)
        st.plotly_chart(fig3, use_container_width=True)


# ══════════════════════════════════════════════════════════════
#  PAGE 2 — PORTFOLIO HOLDINGS
# ══════════════════════════════════════════════════════════════
elif page == "📊 Portfolio Holdings":

    st.markdown("<h2 style='color:#1F497D'>📊 Portfolio Holdings</h2>", unsafe_allow_html=True)

    if portfolio is not None and master is not None:
        merged = portfolio.merge(
            master[['ticker','companyName','bics_sector','country']],
            on='ticker', how='left'
        )

        # Sort options
        sort_col = st.selectbox(
            "Sort by",
            ["weight", "ESG_score", "sharpe_ratio", "annual_return_pct", "composite_score"],
            format_func=lambda x: {
                "weight": "Portfolio Weight",
                "ESG_score": "ESG Score",
                "sharpe_ratio": "Sharpe Ratio",
                "annual_return_pct": "Annual Return %",
                "composite_score": "Composite Score",
            }.get(x, x)
        )

        merged = merged.sort_values(sort_col, ascending=False).reset_index(drop=True)
        merged['Rank'] = range(1, len(merged)+1)
        merged['Weight %'] = (merged['weight'] * 100).round(2)

        display_cols = {
            'Rank': 'Rank',
            'ticker': 'Ticker',
            'companyName': 'Company',
            'bics_sector': 'Sector',
            'country': 'Country',
            'Weight %': 'Weight %',
            'ESG_score': 'ESG Score',
            'E_score': 'E',
            'S_score': 'S',
            'G_score': 'G',
            'sharpe_ratio': 'Sharpe',
            'annual_return_pct': 'Return %',
            'annual_volatility_pct': 'Volatility %',
            'max_drawdown_pct': 'Max DD %',
        }

        display = merged[[c for c in display_cols if c in merged.columns]].rename(columns=display_cols)

        # Round numerics
        for col in ['ESG Score', 'E', 'S', 'G', 'Sharpe', 'Return %', 'Volatility %', 'Max DD %', 'Weight %']:
            if col in display.columns:
                display[col] = display[col].round(2)

        st.dataframe(
            display,
            use_container_width=True,
            hide_index=True,
            height=600,
        )

        # ESG pillars chart
        st.markdown("<div class='section-header'>E / S / G Breakdown per Holding</div>", unsafe_allow_html=True)
        melt = merged[['ticker','E_score','S_score','G_score']].melt(id_vars='ticker', var_name='Pillar', value_name='Score')
        melt['Pillar'] = melt['Pillar'].map({'E_score':'Environmental','S_score':'Social','G_score':'Governance'})
        fig = px.bar(
            melt, x='ticker', y='Score', color='Pillar',
            barmode='group',
            color_discrete_map={'Environmental':'#2E74B5','Social':'#70AD47','Governance':'#ED7D31'},
            labels={'ticker':'', 'Score':'Score (0–100)'}
        )
        fig.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=380, legend_title='')
        st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════════════════
#  PAGE 3 — ESG SCORES
# ══════════════════════════════════════════════════════════════
elif page == "🌱 ESG Scores":

    st.markdown("<h2 style='color:#1F497D'>🌱 ESG Scores — Full Universe</h2>", unsafe_allow_html=True)

    if esg is not None:
        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown("<div class='section-header'>ESG Score — All 57 Companies</div>", unsafe_allow_html=True)
            # Colour bars by inclusion
            in_port = set(portfolio['ticker'].tolist()) if portfolio is not None else set()
            esg_sorted = esg.sort_values('ESG_score', ascending=True).copy()
            esg_sorted['Status'] = esg_sorted['ticker'].apply(
                lambda t: 'In Portfolio' if t in in_port else 'Excluded'
            )
            fig = px.bar(
                esg_sorted, x='ESG_score', y='ticker', orientation='h',
                color='Status',
                color_discrete_map={'In Portfolio': MID_BLUE, 'Excluded': '#BDBDBD'},
                labels={'ESG_score': 'ESG Score (0–100)', 'ticker': ''},
                height=900,
            )
            fig.update_layout(margin=dict(l=20, r=20, t=10, b=20), legend_title='')
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("<div class='section-header'>Score Distribution</div>", unsafe_allow_html=True)
            fig2 = px.histogram(
                esg, x='ESG_score', nbins=15,
                color_discrete_sequence=[MID_BLUE],
                labels={'ESG_score': 'ESG Score'},
            )
            fig2.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=280)
            st.plotly_chart(fig2, use_container_width=True)

            st.markdown("<div class='section-header'>Pillar Averages</div>", unsafe_allow_html=True)
            pillar_data = pd.DataFrame({
                'Pillar': ['Environmental (40%)', 'Social (30%)', 'Governance (30%)'],
                'Universe Avg': [esg['E_score'].mean(), esg['S_score'].mean(), esg['G_score'].mean()],
            })
            if portfolio is not None:
                port_esg = esg[esg['ticker'].isin(in_port)]
                pillar_data['Portfolio Avg'] = [
                    port_esg['E_score'].mean(), port_esg['S_score'].mean(), port_esg['G_score'].mean()
                ]
            fig3 = px.bar(
                pillar_data.melt(id_vars='Pillar', var_name='Group', value_name='Score'),
                x='Score', y='Pillar', color='Group', barmode='group', orientation='h',
                color_discrete_map={'Universe Avg': '#BDBDBD', 'Portfolio Avg': MID_BLUE},
                labels={'Score': 'Avg Score', 'Pillar': ''},
            )
            fig3.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=230, legend_title='')
            st.plotly_chart(fig3, use_container_width=True)

            # Stats table
            st.markdown("<div class='section-header'>Statistics</div>", unsafe_allow_html=True)
            stats = esg['ESG_score'].describe().round(1)
            st.dataframe(
                stats.rename("ESG Score").to_frame(),
                use_container_width=True,
            )


# ══════════════════════════════════════════════════════════════
#  PAGE 4 — RISK & RETURNS
# ══════════════════════════════════════════════════════════════
elif page == "📈 Risk & Returns":

    st.markdown("<h2 style='color:#1F497D'>📈 Risk & Returns</h2>", unsafe_allow_html=True)

    if financial is not None:
        in_port = set(portfolio['ticker'].tolist()) if portfolio is not None else set()
        fin = financial.copy()
        fin['Status'] = fin['ticker'].apply(lambda t: 'In Portfolio' if t in in_port else 'Excluded')

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("<div class='section-header'>Risk–Return Scatter</div>", unsafe_allow_html=True)
            fig = px.scatter(
                fin, x='annual_volatility_pct', y='annual_return_pct',
                color='Status', text='ticker',
                color_discrete_map={'In Portfolio': MID_BLUE, 'Excluded': '#BDBDBD'},
                labels={
                    'annual_volatility_pct': 'Volatility % (annual)',
                    'annual_return_pct': 'Return % (annual)',
                },
                size_max=12,
            )
            fig.update_traces(textposition='top center', textfont_size=8)
            fig.update_layout(margin=dict(l=20, r=20, t=10, b=20), height=400, legend_title='')
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("<div class='section-header'>Sharpe Ratio — Portfolio Holdings</div>", unsafe_allow_html=True)
            port_fin = fin[fin['Status']=='In Portfolio'].sort_values('sharpe_ratio', ascending=True)
            fig2 = px.bar(
                port_fin, x='sharpe_ratio', y='ticker', orientation='h',
                color='sharpe_ratio', color_continuous_scale='Blues',
                labels={'sharpe_ratio': 'Sharpe Ratio', 'ticker': ''},
            )
            fig2.update_layout(margin=dict(l=20, r=20, t=10, b=20), height=400, coloraxis_showscale=False)
            st.plotly_chart(fig2, use_container_width=True)

        # Max drawdown
        st.markdown("<div class='section-header'>Maximum Drawdown — Portfolio Holdings</div>", unsafe_allow_html=True)
        port_dd = fin[fin['Status']=='In Portfolio'].sort_values('max_drawdown_pct')
        fig3 = px.bar(
            port_dd, x='ticker', y='max_drawdown_pct',
            color='max_drawdown_pct', color_continuous_scale='Reds_r',
            labels={'max_drawdown_pct': 'Max Drawdown %', 'ticker': ''},
            text='max_drawdown_pct',
        )
        fig3.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig3.update_layout(margin=dict(l=20, r=20, t=10, b=30), height=320, coloraxis_showscale=False)
        st.plotly_chart(fig3, use_container_width=True)

        # Summary table
        st.markdown("<div class='section-header'>Full Metrics Table</div>", unsafe_allow_html=True)
        tbl = fin[fin['Status']=='In Portfolio'][
            ['ticker','annual_return_pct','annual_volatility_pct','sharpe_ratio','max_drawdown_pct']
        ].sort_values('sharpe_ratio', ascending=False).round(3)
        tbl.columns = ['Ticker','Return %','Volatility %','Sharpe','Max DD %']
        st.dataframe(tbl, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════
#  PAGE 4.5 — PORTFOLIO OPTIMIZATION
# ══════════════════════════════════════════════════════════════
elif page == "⚙️ Portfolio Optimization":

    st.markdown("<h2 style='color:#1F497D'>⚙️ Portfolio Optimization & Backtest</h2>", unsafe_allow_html=True)
    st.markdown("최적화 솔버와 머신러닝 모델을 활용한 기법별 최종 가중치 배분 성과를 비교하고 제약 조건을 검증합니다.")

    opt_df = load_optimization()

    col1, col2 = st.columns([6, 5])

    with col1:
        st.markdown("<div class='section-header'>최적화 기법별 성과 지표 비교 (Ranked)</div>", unsafe_allow_html=True)
        if opt_df is not None:
            display_df = opt_df.copy()
            rename_dict = {
                "method": "기법 (Method)",
                "sharpe": "샤프 비율 (Sharpe)",
                "max_drawdown": "최대 낙폭 (Max DD)",
                "annual_turnover": "연간 회전율 (Turnover)",
                "tracking_error": "추적 오차 (TE)",
                "waci": "탄소 강도 (WACI)",
                "composite_score": "종합 점수",
                "rank": "순위"
            }
            display_df = display_df.rename(columns=rename_dict)
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.warning("최적화 결과 데이터를 찾을 수 없습니다. Optimization_module을 먼저 실행해 주세요.")

        st.markdown("<div class='section-header'>포트폴리오 제약 조건 & 기법 평가</div>", unsafe_allow_html=True)
        st.markdown("""
        *   **Equal Weight (동일 가중)**: 20개 종목에 동일하게 5%씩 균등 배분 (성공, 종합 1위)
        *   **HRP (계층적 리스크 패리티)**: 머신러닝 클러스터링을 활용해 변동성을 안정적으로 분산 (성공, 종합 2위)
        *   **Score Tilted (ESG 틸팅 가중)**: ESG 점수를 가중치에 가산 틸팅 (성공, 종합 3위)
        *   **Max Sharpe / Min Volatility / Black-Litterman**: 포트폴리오 가이드라인 제약조건(단일 종목 최대 10%, 동일 섹터 최대 25% 한도) 충돌로 인해 솔버 해 없음 (**Infeasible** 처리)
        """)

    with col2:
        st.markdown("<div class='section-header'>OOS 누적 자산 성장 곡선 (Equity Curves)</div>", unsafe_allow_html=True)
        curve_path = "Optimization_module/outputs/equity_curves.png"
        if os.path.exists(curve_path):
            st.image(curve_path, caption="Out-of-Sample Performance Comparison (5Y)", use_container_width=True)
        else:
            st.info("OOS 백테스트 자산곡선 차트 이미지가 아직 생성되지 않았습니다.")


# ══════════════════════════════════════════════════════════════
#  PAGE 5 — CLIMATE & BIODIVERSITY
# ══════════════════════════════════════════════════════════════
elif page == "🌍 Climate & Biodiversity":

    st.markdown("<h2 style='color:#1F497D'>🌍 Climate & Biodiversity</h2>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    # Carbon intensity (WACI proxy)
    with col1:
        st.markdown("<div class='section-header'>Carbon Intensity (tCO₂e per €M Revenue)</div>", unsafe_allow_html=True)
        if master is not None and portfolio is not None:
            in_port = set(portfolio['ticker'].tolist())
            ci = master[master['ticker'].isin(in_port)][['ticker','carbon_intensity_tco2e_per_eur_m_revenue']].dropna()
            ci = ci.sort_values('carbon_intensity_tco2e_per_eur_m_revenue', ascending=True)
            ci.columns = ['Ticker','Carbon Intensity']
            fig = px.bar(
                ci, x='Carbon Intensity', y='Ticker', orientation='h',
                color='Carbon Intensity', color_continuous_scale='RdYlGn_r',
                labels={'Carbon Intensity': 'tCO₂e / €M Revenue'},
            )
            fig.update_layout(margin=dict(l=20, r=20, t=10, b=20), height=450, coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)

    # Biodiversity
    with col2:
        st.markdown("<div class='section-header'>Nature Risk Score (ENCORE + WRI Aqueduct)</div>", unsafe_allow_html=True)
        if bio is not None and portfolio is not None:
            bio_port = bio[bio['ticker'].isin(in_port)].copy() if 'ticker' in bio.columns else None
            if bio_port is not None and 'nature_risk_score' in bio_port.columns:
                bio_port = bio_port.sort_values('nature_risk_score', ascending=True)
                color_col = 'nature_risk_score'
                fig2 = px.bar(
                    bio_port, x=color_col, y='ticker', orientation='h',
                    color=color_col, color_continuous_scale='YlOrRd',
                    labels={color_col: 'Nature Risk Score (0–100)', 'ticker': ''},
                )
                fig2.update_layout(margin=dict(l=20, r=20, t=10, b=20), height=450, coloraxis_showscale=False)
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("Biodiversity scores not yet available — re-run Agent 07.")

    # Renewable energy
    st.markdown("<div class='section-header'>Renewable Energy % — Portfolio Holdings</div>", unsafe_allow_html=True)
    if master is not None and portfolio is not None:
        re = master[master['ticker'].isin(in_port)][['ticker','renewable_energy_pct']].dropna()
        re = re.sort_values('renewable_energy_pct', ascending=True)
        fig3 = px.bar(
            re, x='renewable_energy_pct', y='ticker', orientation='h',
            color='renewable_energy_pct', color_continuous_scale='Greens',
            labels={'renewable_energy_pct': 'Renewable Energy %', 'ticker': ''},
            text='renewable_energy_pct',
        )
        fig3.update_traces(texttemplate='%{text:.0f}%', textposition='outside')
        fig3.update_layout(margin=dict(l=20, r=20, t=10, b=20), height=380, coloraxis_showscale=False)
        st.plotly_chart(fig3, use_container_width=True)


# ══════════════════════════════════════════════════════════════
#  PAGE 6 — GREENWASHING
# ══════════════════════════════════════════════════════════════
elif page == "⚠️ Greenwashing":

    st.markdown("<h2 style='color:#1F497D'>⚠️ Greenwashing Risk Assessment</h2>", unsafe_allow_html=True)

    st.info(
        "Greenwashing scores are generated by the RAG Operator via Claude Projects using the 8-Test framework. "
        "JSON files land in `outputs/rag/greenwash_TICKER.json`. "
        "Results below will populate automatically once the RAG analysis is complete."
    )

    # Check if any greenwash JSONs exist
    gw_files = glob.glob("outputs/rag/greenwash_*.json")

    if gw_files:
        records = []
        for fp in gw_files:
            ticker = os.path.basename(fp).replace("greenwash_","").replace(".json","")
            with open(fp) as f:
                data = json.load(f)
            row = {"ticker": ticker}
            for dim in ["specificity","metric","baseline","target","time_horizon","scope","verification","consistency"]:
                row[dim] = data.get(dim, {}).get("rating", "MISSING")
            row["high_count"] = sum(1 for d in row if row.get(d)=="HIGH")
            records.append(row)

        gw_df = pd.DataFrame(records)

        def colour_rating(val):
            c = {"LOW":"background-color:#e8f5e9","MED":"background-color:#fff8e1",
                 "HIGH":"background-color:#ffebee","MISSING":"background-color:#f5f5f5"}.get(val,"")
            return c

        st.dataframe(
            gw_df.style.map(colour_rating, subset=[c for c in gw_df.columns if c not in ['ticker','high_count']]),
            use_container_width=True,
            hide_index=True,
        )

    else:
        # Show framework explanation instead
        st.markdown("<div class='section-header'>8-Test Greenwashing Framework</div>", unsafe_allow_html=True)
        dims = [
            ("1. Specificity",    "Are claims specific and unambiguous?",        "Vague language like 'green' or 'sustainable'"),
            ("2. Metric",         "Is there a supporting number?",               "No numeric backing"),
            ("3. Baseline",       "What is the comparison reference?",           "Missing or cherry-picked baseline"),
            ("4. Target",         "What is the stated endpoint?",                "Non-binding or absent target"),
            ("5. Time Horizon",   "By when will it be achieved?",                "2050+ with no interim milestones"),
            ("6. Scope",          "Which division / asset does it cover?",       "Ambiguous or partial coverage"),
            ("7. Verification",   "Is there external assurance?",               "Self-reported only"),
            ("8. Consistency",    "Does capex/lobbying match the claims?",       "Contradiction between actions and words"),
        ]
        rows = []
        for name, question, red_flag in dims:
            rows.append({"Dimension": name, "Question": question, "Red Flag": red_flag})
        df_dims = pd.DataFrame(rows)
        st.dataframe(df_dims, use_container_width=True, hide_index=True, height=320)

        st.markdown("<div class='section-header'>How to Generate Greenwashing Scores</div>", unsafe_allow_html=True)
        st.code("""
# For each company, run this prompt in Claude Projects:
# (Agent 09 notebook prints the full prompt when executed)

\"You are an ESG forensic analyst. For [COMPANY], analyse the most recent
sustainability report and assess each of the 8 greenwashing dimensions.
For each dimension provide:
(a) direct quote with page number
(b) numerical value or factual statement
(c) red-flag rating (LOW / MED / HIGH / MISSING)
(d) one-two sentences of reasoning.
Output as JSON with 8 fields.\"

# Save output to: outputs/rag/greenwash_TICKER.json
""", language="text")


# ══════════════════════════════════════════════════════════════
#  PAGE 7 — EXCLUSIONS
# ══════════════════════════════════════════════════════════════
elif page == "🚫 Exclusions":

    st.markdown("<h2 style='color:#1F497D'>🚫 Excluded Companies</h2>", unsafe_allow_html=True)

    if exclusions is not None and master is not None:
        excl_full = exclusions.merge(
            master[['ticker','companyName','bics_sector','country']],
            on='ticker', how='left'
        )

        # Categorise reason
        def categorise(r):
            r = str(r).lower()
            if 'esg' in r:      return 'ESG Floor'
            if 'sharpe' in r:   return 'Negative Sharpe'
            if 'greenwash' in r: return 'Greenwashing'
            return 'Other'

        excl_full['Category'] = excl_full['reason'].apply(categorise)

        col1, col2 = st.columns([1, 2])

        with col1:
            st.markdown("<div class='section-header'>Exclusion Reasons</div>", unsafe_allow_html=True)
            cat_counts = excl_full['Category'].value_counts().reset_index()
            cat_counts.columns = ['Reason', 'Count']
            fig = px.pie(
                cat_counts, names='Reason', values='Count', hole=0.4,
                color_discrete_map={
                    'ESG Floor': RED,
                    'Negative Sharpe': AMBER,
                    'Greenwashing': '#7B1FA2',
                    'Other': '#757575',
                },
            )
            fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=280)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("<div class='section-header'>Excluded Companies Detail</div>", unsafe_allow_html=True)
            display = excl_full[['ticker','companyName','bics_sector','country','reason','Category']].copy()
            display.columns = ['Ticker','Company','Sector','Country','Reason','Category']
            st.dataframe(display, use_container_width=True, hide_index=True, height=280)

        # ESG scores of excluded companies
        if esg is not None:
            st.markdown("<div class='section-header'>ESG Scores of Excluded Companies</div>", unsafe_allow_html=True)
            excl_esg = esg[esg['ticker'].isin(exclusions['ticker'])].copy()
            excl_esg = excl_esg.sort_values('ESG_score')
            fig2 = px.bar(
                excl_esg, x='ticker', y='ESG_score',
                color='ESG_score', color_continuous_scale='Reds_r',
                labels={'ESG_score': 'ESG Score (0–100)', 'ticker': ''},
                text='ESG_score',
            )
            fig2.update_traces(texttemplate='%{text:.1f}', textposition='outside')
            fig2.update_layout(margin=dict(l=20, r=20, t=10, b=20), height=340, coloraxis_showscale=False)
            st.plotly_chart(fig2, use_container_width=True)
    else:
        st.warning("Exclusions data not found. Run Agent 11 (Portfolio Construction) first.")


# ══════════════════════════════════════════════════════════════
#  PAGE 8 — MANDATE
# ══════════════════════════════════════════════════════════════
elif page == "📋 Mandate":

    st.markdown("<h2 style='color:#1F497D'>📋 Investment Mandate</h2>", unsafe_allow_html=True)

    if mandate:
        c1, c2 = st.columns(2)

        with c1:
            st.markdown("<div class='section-header'>Fund Details</div>", unsafe_allow_html=True)
            items = {
                "Fund Name":       mandate.get("fund_name","—"),
                "Universe":        mandate.get("universe","—"),
                "Benchmark":       mandate.get("benchmark","—"),
                "Data Vintage":    mandate.get("vintage","—"),
            }
            for k, v in items.items():
                st.markdown(f"**{k}:** {v}")

            st.markdown("<div class='section-header'>Composite Score Weights</div>", unsafe_allow_html=True)
            w = mandate.get("composite_score_weights", {})
            if w:
                fig = px.pie(
                    values=list(w.values()),
                    names=[k.replace('_weight','').upper() for k in w.keys()],
                    color_discrete_sequence=[MID_BLUE, DARK_BLUE],
                    hole=0.4,
                )
                fig.update_layout(margin=dict(l=10,r=10,t=10,b=10), height=230)
                st.plotly_chart(fig, use_container_width=True)

        with c2:
            st.markdown("<div class='section-header'>ESG Pillar Weights</div>", unsafe_allow_html=True)
            pw = mandate.get("esg_pillar_weights", {})
            if pw:
                fig2 = px.bar(
                    x=list(pw.keys()),
                    y=[v*100 for v in pw.values()],
                    color=list(pw.keys()),
                    color_discrete_map={"E":"#2E74B5","S":"#70AD47","G":"#ED7D31"},
                    labels={'x':'Pillar','y':'Weight (%)'},
                    text=[f"{v*100:.0f}%" for v in pw.values()],
                )
                fig2.update_traces(textposition='outside')
                fig2.update_layout(margin=dict(l=10,r=10,t=10,b=10), height=230, showlegend=False)
                st.plotly_chart(fig2, use_container_width=True)

            st.markdown("<div class='section-header'>Hard Exclusion Rules</div>", unsafe_allow_html=True)
            for rule in mandate.get("hard_exclusions", []):
                st.markdown(f"🚫 {rule}")

            st.markdown("<div class='section-header'>Watchlist Triggers</div>", unsafe_allow_html=True)
            for rule in mandate.get("watchlist_triggers", []):
                st.markdown(f"⚠️ {rule}")

        st.markdown("<div class='section-header'>Investment Thesis</div>", unsafe_allow_html=True)
        st.info(mandate.get("investment_thesis","—"))

        st.markdown("<div class='section-header'>Required Metrics</div>", unsafe_allow_html=True)
        metrics = mandate.get("required_metrics", [])
        cols = st.columns(3)
        for i, m in enumerate(metrics):
            with cols[i % 3]:
                st.markdown(f"✅ {m}")

    else:
        st.warning("Mandate not found. Run Agent 01 first.")
