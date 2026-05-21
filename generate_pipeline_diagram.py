"""
Generates a professional pipeline architecture diagram.
Output: outputs/reports/pipeline_diagram.png
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import matplotlib.patheffects as pe
import os

os.makedirs("outputs/reports", exist_ok=True)

# ── Colour palette ────────────────────────────────────────────
C_DARK_BLUE  = "#1F497D"
C_MID_BLUE   = "#2E74B5"
C_LIGHT_BLUE = "#D6E4F0"
C_GREEN      = "#375623"
C_GREEN_LIGHT= "#E2EFDA"
C_ORANGE     = "#7F4000"
C_ORANGE_LT  = "#FCE4D6"
C_PURPLE     = "#3D1F6B"
C_PURPLE_LT  = "#EAE0F5"
C_GREY       = "#595959"
C_GREY_LT    = "#F2F2F2"
C_WHITE      = "#FFFFFF"
C_RED        = "#C00000"
C_TEAL       = "#1F6B5A"
C_TEAL_LT    = "#D9EFE8"

fig, ax = plt.subplots(figsize=(20, 26))
ax.set_xlim(0, 20)
ax.set_ylim(0, 26)
ax.axis('off')
fig.patch.set_facecolor(C_WHITE)

# ── Helper functions ──────────────────────────────────────────
def box(ax, x, y, w, h, label, sublabel="", fc=C_LIGHT_BLUE, ec=C_MID_BLUE,
        text_color=C_DARK_BLUE, fontsize=10, bold=True, radius=0.25):
    rect = FancyBboxPatch((x - w/2, y - h/2), w, h,
                          boxstyle=f"round,pad=0.05,rounding_size={radius}",
                          facecolor=fc, edgecolor=ec, linewidth=1.5, zorder=3)
    ax.add_patch(rect)
    weight = "bold" if bold else "normal"
    if sublabel:
        ax.text(x, y + 0.12, label, ha='center', va='center',
                fontsize=fontsize, fontweight=weight, color=text_color, zorder=4)
        ax.text(x, y - 0.22, sublabel, ha='center', va='center',
                fontsize=fontsize - 1.5, color=text_color, alpha=0.75, zorder=4)
    else:
        ax.text(x, y, label, ha='center', va='center',
                fontsize=fontsize, fontweight=weight, color=text_color, zorder=4)

def arrow(ax, x1, y1, x2, y2, color=C_GREY, lw=1.5, style='->', label=""):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle=style, color=color,
                                lw=lw, connectionstyle="arc3,rad=0.0"),
                zorder=2)
    if label:
        mx, my = (x1+x2)/2, (y1+y2)/2
        ax.text(mx + 0.15, my, label, fontsize=7.5, color=color,
                va='center', style='italic', zorder=5)

def csv_tag(ax, x, y, label):
    rect = FancyBboxPatch((x - 1.1, y - 0.22), 2.2, 0.44,
                          boxstyle="round,pad=0.03,rounding_size=0.12",
                          facecolor=C_GREEN_LIGHT, edgecolor=C_GREEN,
                          linewidth=1.0, zorder=3)
    ax.add_patch(rect)
    ax.text(x, y, label, ha='center', va='center', fontsize=7.5,
            color=C_GREEN, fontweight='bold', zorder=4)

# ═══════════════════════════════════════════════════════════════
# TITLE
# ═══════════════════════════════════════════════════════════════
ax.add_patch(FancyBboxPatch((0.3, 24.5), 19.4, 1.2,
             boxstyle="round,pad=0.1,rounding_size=0.3",
             facecolor=C_DARK_BLUE, edgecolor=C_DARK_BLUE, zorder=3))
ax.text(10, 25.18, "ESADE Sustainable Finance — AI Agent Pipeline",
        ha='center', va='center', fontsize=16, fontweight='bold',
        color=C_WHITE, zorder=4)
ax.text(10, 24.72, "13-Agent Orchestrated Pipeline  ·  run_pipeline.py  ·  ~63 seconds end-to-end",
        ha='center', va='center', fontsize=9.5, color="#CCE0FF", zorder=4)

# ═══════════════════════════════════════════════════════════════
# INPUT DATA
# ═══════════════════════════════════════════════════════════════
ax.text(10, 24.05, "INPUT DATA  (Professor's 4 CSV Files — replaced Friday)",
        ha='center', va='center', fontsize=9, color=C_GREY, style='italic')

input_files = [
    ("equityBicsV2.csv\n(Companies + Identifiers)", 3.2),
    ("esgEnvironmental\nSocial.csv", 7.2),
    ("esgGovernance\nConsolidated.csv", 11.8),
    ("legalEntity\nEuTaxonomy.csv", 16.2),
]
for label, x in input_files:
    box(ax, x, 23.35, 3.4, 0.85, label, fc=C_ORANGE_LT, ec=C_ORANGE,
        text_color=C_ORANGE, fontsize=8, radius=0.15)

# arrows from inputs down to Agent 01
for _, x in input_files:
    arrow(ax, x, 22.92, 10, 22.12, color=C_ORANGE, lw=1.2)

# ═══════════════════════════════════════════════════════════════
# AGENT 01 — Mandate
# ═══════════════════════════════════════════════════════════════
box(ax, 10, 21.75, 6.5, 0.65,
    "Agent 01 — Mandate",
    "Defines investment thesis, ESG weights, exclusion rules",
    fc=C_PURPLE_LT, ec=C_PURPLE, text_color=C_PURPLE, fontsize=9.5)
arrow(ax, 10, 21.42, 10, 21.02, color=C_GREY)
csv_tag(ax, 10, 20.82, "mandate.json")

# ═══════════════════════════════════════════════════════════════
# AGENT 02 — Data Ingestion
# ═══════════════════════════════════════════════════════════════
arrow(ax, 10, 20.6, 10, 20.22, color=C_GREY)
box(ax, 10, 19.88, 6.5, 0.65,
    "Agent 02 — Data Ingestion",
    "Merges 4 CSVs · downloads prices via yfinance · vintage tags",
    fc=C_LIGHT_BLUE, ec=C_MID_BLUE, text_color=C_DARK_BLUE, fontsize=9.5)
arrow(ax, 10, 19.55, 10, 19.15, color=C_GREY)
csv_tag(ax, 10, 18.95, "master_dataset_DATE.csv  (279 companies)")

# ═══════════════════════════════════════════════════════════════
# AGENT 03 — Data Quality
# ═══════════════════════════════════════════════════════════════
arrow(ax, 10, 18.73, 10, 18.35, color=C_GREY)
box(ax, 10, 18.0, 6.5, 0.65,
    "Agent 03 — Data Quality",
    "Missing-value audit · outlier detection · data dictionary",
    fc=C_LIGHT_BLUE, ec=C_MID_BLUE, text_color=C_DARK_BLUE, fontsize=9.5)
arrow(ax, 10, 17.67, 10, 17.27, color=C_GREY)
csv_tag(ax, 10, 17.07, "data_dictionary_DATE.csv  +  outlier_flags_DATE.csv")

# ═══════════════════════════════════════════════════════════════
# PARALLEL BLOCK: Agents 04, 05/06, 07, 08  (feed into Agent 09/10)
# ═══════════════════════════════════════════════════════════════
arrow(ax, 10, 16.85, 10, 16.42, color=C_GREY)

# Parallel label
ax.text(10, 16.25, "Parallel Analysis Agents", ha='center', va='center',
        fontsize=8.5, color=C_GREY, style='italic')

# Draw 4 parallel agents
parallel = [
    (3.0,  "Agent 04\nDoc Intelligence",  "Claude Projects\nRAG extractions",    C_TEAL_LT,   C_TEAL),
    (7.5,  "Agent 05/06\nESG & Climate",  "E, S, G scores\nWACI calculation",     C_LIGHT_BLUE, C_MID_BLUE),
    (12.5, "Agent 07\nBiodiversity",      "ENCORE + WRI\nAqueduct scores",        C_GREEN_LIGHT, C_GREEN),
    (17.0, "Agent 08\nEU Regulation",     "SFDR Article 8\nPAI indicators",       C_ORANGE_LT,  C_ORANGE),
]

# arrows from master dataset to each parallel agent
for x, *_ in parallel:
    arrow(ax, 10, 16.05, x, 15.55, color=C_GREY, lw=1.2)

for x, title, sub, fc, ec in parallel:
    box(ax, x, 15.15, 3.6, 0.75, title, sub,
        fc=fc, ec=ec, text_color=ec, fontsize=9, radius=0.2)

# CSV outputs for parallel agents
parallel_csv = [
    (3.0,  "doc_intel\nTICKER.json"),
    (7.5,  "esg_scores\n_DATE.csv"),
    (12.5, "biodiversity\n_scores.csv"),
    (17.0, "eu_regulation\n_DATE.csv"),
]
for x, label in parallel_csv:
    arrow(ax, x, 14.77, x, 14.42, color=C_GREY, lw=1.0)
    csv_tag(ax, x, 14.22, label)
    arrow(ax, x, 14.02, 10, 13.55, color=C_GREY, lw=1.0)

# ═══════════════════════════════════════════════════════════════
# AGENT 09 — Greenwashing
# ═══════════════════════════════════════════════════════════════
ax.text(10, 13.38, "Outputs merged", ha='center', va='center',
        fontsize=8, color=C_GREY, style='italic')
arrow(ax, 10, 13.22, 10, 12.85, color=C_GREY)
box(ax, 10, 12.5, 6.5, 0.65,
    "Agent 09 — Greenwashing",
    "8-Test framework · RAG JSON imports · exclusion flags",
    fc=C_ORANGE_LT, ec=C_ORANGE, text_color=C_ORANGE, fontsize=9.5)
arrow(ax, 10, 12.17, 10, 11.77, color=C_GREY)
csv_tag(ax, 10, 11.57, "greenwash_TICKER.json  →  watchlist / exclusions")

# ═══════════════════════════════════════════════════════════════
# AGENT 10 — Financial Analysis
# ═══════════════════════════════════════════════════════════════
arrow(ax, 10, 11.35, 10, 10.97, color=C_GREY)
box(ax, 10, 10.62, 6.5, 0.65,
    "Agent 10 — Financial Analysis",
    "Annual return · volatility · Sharpe ratio · max drawdown",
    fc=C_LIGHT_BLUE, ec=C_MID_BLUE, text_color=C_DARK_BLUE, fontsize=9.5)
arrow(ax, 10, 10.29, 10, 9.89, color=C_GREY)
csv_tag(ax, 10, 9.69, "financial_metrics_DATE.csv")

# ═══════════════════════════════════════════════════════════════
# AGENT 11 — Portfolio Construction
# ═══════════════════════════════════════════════════════════════
arrow(ax, 10, 9.47, 10, 9.07, color=C_GREY)
box(ax, 10, 8.72, 8.6, 0.7,
    "Agent 11 — Portfolio Construction (Stage 3)",
    "Capped Top 40 → financial screen → composite (60% Fin / 40% ESG) → max 5 / sector → 20 holdings",
    fc=C_PURPLE_LT, ec=C_PURPLE, text_color=C_PURPLE, fontsize=9.5)
ax.text(3.05, 8.72, "Recovers 8 holdings dropped\nby upstream ticker-join bugs",
        ha='center', va='center', fontsize=7.5, color=C_GREY, style='italic')
arrow(ax, 10, 8.37, 10, 7.99, color=C_GREY)
csv_tag(ax, 10, 7.79, "final_portfolio_DATE.csv  (20 holdings)   +   universe_scores_DATE.csv  (40 ranked, 7 excluded)")

# ═══════════════════════════════════════════════════════════════
# AGENT 12 — Human Review
# ═══════════════════════════════════════════════════════════════
arrow(ax, 10, 7.57, 10, 7.17, color=C_GREY)
box(ax, 10, 6.82, 6.5, 0.65,
    "Agent 12 — Human Review",
    "Override log + IC watchlist sign-off  ·  AI Use Statement",
    fc=C_TEAL_LT, ec=C_TEAL, text_color=C_TEAL, fontsize=9.5)
arrow(ax, 10, 6.49, 10, 6.09, color=C_GREY)
csv_tag(ax, 10, 5.89, "human_overrides_DATE.csv  +  ai_use_statement.txt")

# ═══════════════════════════════════════════════════════════════
# AGENT 13 — Reporting
# ═══════════════════════════════════════════════════════════════
arrow(ax, 10, 5.67, 10, 5.27, color=C_GREY)
box(ax, 10, 4.92, 6.5, 0.65,
    "Agent 13 — Reporting",
    "Portfolio factsheet · ESG comparison chart · risk-return chart",
    fc=C_LIGHT_BLUE, ec=C_MID_BLUE, text_color=C_DARK_BLUE, fontsize=9.5)
arrow(ax, 10, 4.59, 10, 4.19, color=C_GREY)
csv_tag(ax, 10, 3.99, "portfolio_weights.png  +  esg_comparison.png  +  sector_allocation.png")

# ═══════════════════════════════════════════════════════════════
# OUTPUT BOX
# ═══════════════════════════════════════════════════════════════
arrow(ax, 10, 3.77, 10, 3.3, color=C_GREY)
box(ax, 10, 2.92, 12, 0.65,
    "Streamlit Dashboard  (http://localhost:8501)  +  Investment_Mandate_and_Research.docx",
    fc=C_DARK_BLUE, ec=C_DARK_BLUE, text_color=C_WHITE, fontsize=10, radius=0.3)

# ═══════════════════════════════════════════════════════════════
# LEGEND
# ═══════════════════════════════════════════════════════════════
legend_items = [
    (C_PURPLE_LT, C_PURPLE,    "Mandate / Strategy"),
    (C_LIGHT_BLUE, C_MID_BLUE, "Data Pipeline"),
    (C_TEAL_LT,   C_TEAL,     "Intelligence / Review"),
    (C_ORANGE_LT, C_ORANGE,   "Risk / Regulation"),
    (C_GREEN_LIGHT, C_GREEN,  "CSV / JSON Output"),
]
lx, ly = 0.5, 2.2
ax.text(lx, ly + 0.3, "Legend:", fontsize=8.5, color=C_GREY, fontweight='bold')
for i, (fc, ec, label) in enumerate(legend_items):
    bx = lx + i * 3.4
    rect = FancyBboxPatch((bx, ly - 0.28), 0.55, 0.38,
                          boxstyle="round,pad=0.03,rounding_size=0.08",
                          facecolor=fc, edgecolor=ec, linewidth=1.2, zorder=3)
    ax.add_patch(rect)
    ax.text(bx + 0.7, ly - 0.09, label, fontsize=8, color=C_GREY, va='center')

# Footer
ax.text(10, 0.35, "ESADE MSc Finance  ·  Sustainable Finance Group Assignment  ·  Deadline: 22 May 2026",
        ha='center', va='center', fontsize=8.5, color=C_GREY, style='italic')
ax.text(10, 0.1, "Orchestrator: run_pipeline.py (VS Code Ctrl+Shift+B)  ·  All agents communicate via outputs/ CSV files",
        ha='center', va='center', fontsize=8, color=C_GREY)

plt.tight_layout(pad=0.3)
out = "outputs/reports/pipeline_diagram.png"
plt.savefig(out, dpi=180, bbox_inches='tight', facecolor=C_WHITE)
plt.close()
print(f"Saved: {out}")
